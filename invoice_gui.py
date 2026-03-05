import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from invoice_core.recognizer import InvoiceRecognizer, InvoiceType
from invoice_core.storage import StagingManager, InvoiceOrganizer


class ModernInvoiceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("发票识别工具 V2.0")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)

        self.staging = StagingManager("data")
        self.recognizer = InvoiceRecognizer()
        self.organizer = InvoiceOrganizer(self.staging)

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('微软雅黑', 24, 'bold'), foreground='#2c3e50')
        style.configure('Accent.TButton', font=('微软雅黑', 11), padding=10)
        style.configure('List.TTreeview', font=('Consolas', 10), rowheight=28)

    def setup_ui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(main_container, bg='#3498db', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="发票识别工具 V2.0",
                              font=('微软雅黑', 22, 'bold'), bg='#3498db', fg='white')
        title_label.pack(side=tk.LEFT, padx=20, pady=20)

        nav_frame = tk.Frame(main_container, bg='#2c3e50', width=180)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y)
        nav_frame.pack_propagate(False)

        self.create_nav_buttons(nav_frame)

        content_frame = ttk.Frame(main_container, padding=15)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.content_frame = content_frame
        self.show_dashboard()

    def create_nav_buttons(self, parent):
        nav_buttons = [
            ("仪表盘", self.show_dashboard),
            ("发票识别", self.show_recognize),
            ("暂存区", self.show_staging),
            ("发票整理", self.show_organize),
            ("统计报告", self.show_report),
        ]
        for text, command in nav_buttons:
            btn = tk.Button(parent, text=text, font=('微软雅黑', 12),
                          bg='#34495e', fg='white', activebackground='#3498db',
                          activeforeground='white', bd=0, pady=15,
                          cursor='hand2', command=command)
            btn.pack(fill=tk.X, pady=1)

    def show_dashboard(self):
        self.clear_content()
        title = ttk.Label(self.content_frame, text="仪表盘", style='Title.TLabel')
        title.pack(anchor=tk.W, pady=(0, 20))
        stats = self.staging.get_statistics()
        stats_frame = ttk.Frame(self.content_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        cards = [
            ("总发票数", f"{stats['total_count']}", "#3498db"),
            ("总金额", f"¥{stats['total_amount']:.2f}", "#2ecc71"),
            ("发票类型", f"{len(stats['by_type'])}", "#9b59b6"),
            ("火车票", f"{stats['by_type'].get('火车票', {}).get('count', 0)}", "#e67e22"),
        ]
        for i, (label, value, color) in enumerate(cards):
            card = self.create_stat_card(stats_frame, label, value, color)
            card.grid(row=0, column=i, padx=10, sticky='ew')
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)
        self.create_type_distribution(stats['by_type'])

    def create_stat_card(self, parent, label, value, color):
        frame = tk.Frame(parent, bg=color, padx=20, pady=20)
        card_bg = tk.Frame(frame, bg=color, padx=15, pady=15)
        card_bg.pack()
        tk.Label(card_bg, text=value, font=('微软雅黑', 24, 'bold'),
                bg=color, fg='white').pack()
        tk.Label(card_bg, text=label, font=('微软雅黑', 11),
                bg=color, fg='#ecf0f1').pack()
        return frame

    def create_type_distribution(self, type_stats):
        dist_frame = ttk.LabelFrame(self.content_frame, text="发票类型分布", padding=15)
        dist_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        if not type_stats:
            ttk.Label(dist_frame, text="暂无数据").pack()
            return
        tree = ttk.Treeview(dist_frame, columns=('类型', '数量', '金额'), show='headings',
                           style='List.TTreeview')
        tree.heading('类型', text='类型')
        tree.heading('数量', text='数量')
        tree.heading('金额', text='金额')
        tree.column('类型', width=150)
        tree.column('数量', width=100)
        tree.column('金额', width=150)
        scrollbar = ttk.Scrollbar(dist_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for inv_type, data in type_stats.items():
            tree.insert('', tk.END, values=(inv_type, data['count'], f"¥{data['amount']:.2f}"))

    def show_recognize(self):
        self.clear_content()
        title = ttk.Label(self.content_frame, text="发票识别", style='Title.TLabel')
        title.pack(anchor=tk.W, pady=(0, 20))
        settings_frame = ttk.LabelFrame(self.content_frame, text="识别设置", padding=15)
        settings_frame.pack(fill=tk.X, pady=10)
        ttk.Label(settings_frame, text="发票目录:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.input_var = tk.StringVar(value="data")
        ttk.Entry(settings_frame, textvariable=self.input_var, width=40).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(settings_frame, text="浏览", command=self.browse_input).grid(row=0, column=2, pady=10)
        ttk.Label(settings_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.output_var = tk.StringVar(value="data/processed")
        ttk.Entry(settings_frame, textvariable=self.output_var, width=40).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(settings_frame, text="浏览", command=self.browse_output).grid(row=1, column=2, pady=10)
        mode_frame = ttk.LabelFrame(self.content_frame, text="识别模式", padding=15)
        mode_frame.pack(fill=tk.X, pady=10)
        self.recognize_mode = tk.StringVar(value="direct")
        ttk.Radiobutton(mode_frame, text="直接识别", variable=self.recognize_mode,
                       value="direct").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="导入暂存区", variable=self.recognize_mode,
                       value="staging").pack(side=tk.LEFT, padx=10)
        btn_frame = ttk.Frame(self.content_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        ttk.Button(btn_frame, text="开始识别", style='Accent.TButton',
                  command=self.do_recognize).pack(side=tk.LEFT, padx=5)
        self.result_text = tk.Text(self.content_frame, height=15, font=('Consolas', 10))
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=10)

    def show_staging(self):
        self.clear_content()
        title = ttk.Label(self.content_frame, text="暂存区管理", style='Title.TLabel')
        title.pack(anchor=tk.W, pady=(0, 20))
        btn_frame = ttk.Frame(self.content_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="导入行程发票", command=self.import_trip_invoices).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="补充其他发票", command=self.supplement_invoices).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空暂存区", command=self.clear_staging).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="刷新", command=self.show_staging).pack(side=tk.LEFT, padx=5)
        tree_frame = ttk.Frame(self.content_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        columns = ('类型', '日期', '金额', '文件名')
        self.staging_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                         style='List.TTreeview')
        for col in columns:
            self.staging_tree.heading(col, text=col)
            self.staging_tree.column(col, width=150)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.staging_tree.yview)
        self.staging_tree.configure(yscrollcommand=scrollbar.set)
        self.staging_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.refresh_staging_tree()

    def refresh_staging_tree(self):
        for item in self.staging_tree.get_children():
            self.staging_tree.delete(item)
        for inv in self.staging.get_invoices():
            amount_str = f"¥{inv.amount:.2f}" if inv.amount else "未知"
            self.staging_tree.insert('', tk.END, values=(
                inv.type, inv.date or "未知", amount_str, inv.filename
            ))

    def show_organize(self):
        self.clear_content()
        title = ttk.Label(self.content_frame, text="发票整理", style='Title.TLabel')
        title.pack(anchor=tk.W, pady=(0, 20))
        range_frame = ttk.LabelFrame(self.content_frame, text="按日期区间整理", padding=15)
        range_frame.pack(fill=tk.X, pady=10)
        ttk.Label(range_frame, text="开始日期:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.start_date_var = tk.StringVar()
        ttk.Entry(range_frame, textvariable=self.start_date_var, width=20).grid(row=0, column=1, padx=10, pady=10)
        ttk.Label(range_frame, text="结束日期:").grid(row=0, column=2, sticky=tk.W, pady=10)
        self.end_date_var = tk.StringVar()
        ttk.Entry(range_frame, textvariable=self.end_date_var, width=20).grid(row=0, column=3, padx=10, pady=10)
        ttk.Button(range_frame, text="开始整理", command=self.do_organize).grid(row=0, column=4, padx=20, pady=10)
        match_frame = ttk.LabelFrame(self.content_frame, text="滴滴发票自动匹配", padding=15)
        match_frame.pack(fill=tk.X, pady=10)
        ttk.Label(match_frame, text="根据日期和金额自动匹配电子发票和行程报销单").pack()
        ttk.Button(match_frame, text="自动匹配", command=self.do_match).pack(pady=10)

    def show_report(self):
        self.clear_content()
        title = ttk.Label(self.content_frame, text="统计报告", style='Title.TLabel')
        title.pack(anchor=tk.W, pady=(0, 20))
        btn_frame = ttk.Frame(self.content_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="刷新", command=self.show_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出JSON", command=self.export_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出Excel", command=self.export_excel).pack(side=tk.LEFT, padx=5)
        stats = self.staging.get_statistics()
        report_frame = ttk.LabelFrame(self.content_frame, text="统计详情", padding=15)
        report_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        text = tk.Text(report_frame, font=('Consolas', 11), bg='#f8f9fa')
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, "=" * 50 + "\n")
        text.insert(tk.END, "发票统计报告\n")
        text.insert(tk.END, "=" * 50 + "\n\n")
        text.insert(tk.END, f"总发票数: {stats['total_count']} 张\n")
        text.insert(tk.END, f"总金额: ¥{stats['total_amount']:.2f} 元\n\n")
        for inv_type, data in stats['by_type'].items():
            text.insert(tk.END, f"【{inv_type}】\n")
            text.insert(tk.END, f"  数量: {data['count']} 张\n")
            text.insert(tk.END, f"  金额: ¥{data['amount']:.2f} 元\n\n")

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def browse_input(self):
        directory = filedialog.askdirectory(initialdir=self.input_var.get())
        if directory:
            self.input_var.set(directory)

    def browse_output(self):
        directory = filedialog.askdirectory(initialdir=self.output_var.get())
        if directory:
            self.output_var.set(directory)

    def do_recognize(self):
        input_dir = self.input_var.get()
        output_dir = self.output_var.get()
        if not os.path.exists(input_dir):
            messagebox.showerror("错误", "发票目录不存在")
            return
        os.makedirs(output_dir, exist_ok=True)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"正在识别发票目录: {input_dir}\n")
        self.result_text.insert(tk.END, "=" * 50 + "\n")
        results = self.recognizer.recognize_directory(input_dir)
        if self.recognize_mode.get() == "staging":
            self.staging.add_invoices(results)
            self.result_text.insert(tk.END, f"已导入 {len(results)} 张发票到暂存区\n")
        else:
            import shutil
            for info in results:
                if os.path.exists(info.filepath):
                    dst = os.path.join(output_dir, info.filename)
                    shutil.copy2(info.filepath, dst)
            self.result_text.insert(tk.END, f"已识别并复制 {len(results)} 张发票到 {output_dir}\n")
        self.result_text.insert(tk.END, "\n识别统计:\n")
        stats = self.recognizer.get_statistics()
        for inv_type, data in stats.items():
            self.result_text.insert(tk.END, f"  {inv_type}: {data['count']} 张, ¥{data['amount']:.2f}\n")
        messagebox.showinfo("完成", f"识别完成，共处理 {len(results)} 个文件")

    def import_trip_invoices(self):
        directory = filedialog.askdirectory(title="选择行程发票目录")
        if not directory:
            return
        trip_types = [InvoiceType.TRAIN, InvoiceType.FLIGHT_ITINERARY]
        results = self.recognizer.recognize_directory(directory)
        trip_invoices = [r for r in results if r.type in trip_types]
        self.staging.add_invoices(trip_invoices)
        messagebox.showinfo("完成", f"已导入 {len(trip_invoices)} 张行程发票到暂存区")
        self.refresh_staging_tree()

    def supplement_invoices(self):
        directory = filedialog.askdirectory(title="选择发票目录")
        if not directory:
            return
        results = self.recognizer.recognize_directory(directory)
        self.staging.add_invoices(results)
        messagebox.showinfo("完成", f"已补充 {len(results)} 张发票到暂存区")
        self.refresh_staging_tree()

    def clear_staging(self):
        if messagebox.askyesno("确认", "确定要清空暂存区吗？"):
            self.staging.clear_staging()
            messagebox.showinfo("完成", "暂存区已清空")
            self.refresh_staging_tree()

    def do_organize(self):
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        if not start_date or not end_date:
            messagebox.showerror("错误", "请输入开始和结束日期")
            return
        result = self.organizer.organize_by_date_range(start_date, end_date)
        if result["success"]:
            messagebox.showinfo("完成", f"整理完成！\n发票数量: {result['invoice_count']}\n目标目录: {result['target_dir']}")
            self.show_staging()
        else:
            messagebox.showerror("错误", result["message"])

    def do_match(self):
        start_date = self.start_date_var.get() or "2024-01-01"
        end_date = self.end_date_var.get() or "2026-12-31"
        result = self.organizer.auto_match_invoices(start_date, end_date)
        messagebox.showinfo("匹配完成", f"匹配到 {result['total_pairs']} 对发票\n涉及 {result['matched_invoices']} 张发票")

    def export_json(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                               filetypes=[("JSON文件", "*.json")])
        if filepath:
            self.staging.export_json(filepath)
            messagebox.showinfo("完成", f"已导出到: {filepath}")

    def export_excel(self):
        try:
            import pandas as pd
            filepath = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                   filetypes=[("Excel文件", "*.xlsx")])
            if filepath:
                data_list = []
                for inv in self.staging.get_invoices():
                    data_list.append({
                        "类型": inv.type,
                        "日期": inv.date,
                        "金额": inv.amount,
                        "文件名": inv.filename,
                        "备注": inv.notes
                    })
                df = pd.DataFrame(data_list)
                df.to_excel(filepath, index=False)
                messagebox.showinfo("完成", f"已导出到: {filepath}")
        except ImportError:
            messagebox.showerror("错误", "需要安装 pandas 和 openpyxl 才能导出Excel")


def main():
    root = tk.Tk()
    app = ModernInvoiceGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
