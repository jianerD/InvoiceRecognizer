import os
import re
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class InvoiceProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("发票识别与整理工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        self.input_dir = "data"
        self.output_dir = os.path.join(self.input_dir, "processed")
        self.results = []
        self.train_tickets = []
        self.use_pdf_extract = tk.BooleanVar(value=True)

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="发票识别与整理工具", font=("微软雅黑", 18, "bold"))
        title_label.pack(pady=10)

        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)

        ttk.Label(settings_frame, text="发票目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_var = tk.StringVar(value=self.input_dir)
        ttk.Entry(settings_frame, textvariable=self.input_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(settings_frame, text="浏览", command=self.browse_input).grid(row=0, column=2, pady=5)

        ttk.Label(settings_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value=self.output_dir)
        ttk.Entry(settings_frame, textvariable=self.output_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(settings_frame, text="浏览", command=self.browse_output).grid(row=1, column=2, pady=5)

        if PDFPLUMBER_AVAILABLE:
            self.pdf_check = ttk.Checkbutton(settings_frame, text="从PDF文本提取金额（推荐）", variable=self.use_pdf_extract)
        else:
            self.pdf_check = ttk.Checkbutton(settings_frame, text="从PDF文本提取（需安装pdfplumber）", state=tk.DISABLED)
        self.pdf_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.process_btn = ttk.Button(btn_frame, text="开始识别", command=self.process_invoices, style="Accent.TButton")
        self.process_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="查看识别结果", command=self.show_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="查看火车票列表", command=self.show_train_tickets).pack(side=tk.LEFT, padx=5)

        self.organize_frame = ttk.LabelFrame(main_frame, text="整理功能", padding="10")
        self.organize_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(self.organize_frame, text="选择整理方式:", font=("微软雅黑", 12)).pack(anchor=tk.W, pady=5)

        organize_btn_frame = ttk.Frame(self.organize_frame)
        organize_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(organize_btn_frame, text="按火车票区间整理发票", command=self.organize_by_date_range).pack(side=tk.LEFT, padx=5)

        self.result_text = tk.Text(self.organize_frame, height=20, wrap=tk.WORD, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=10)

        scrollbar = ttk.Scrollbar(self.result_text, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)

        self.status_label = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=5)

    def browse_input(self):
        directory = filedialog.askdirectory(initialdir=self.input_var.get())
        if directory:
            self.input_var.set(directory)
            self.output_dir = os.path.join(directory, "processed")
            self.output_var.set(self.output_dir)

    def browse_output(self):
        directory = filedialog.askdirectory(initialdir=self.output_var.get())
        if directory:
            self.output_var.set(directory)

    def log(self, message):
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.see(tk.END)
        self.root.update()

    def set_status(self, status):
        self.status_label.config(text=status)
        self.root.update()

    def extract_text_from_pdf(self, pdf_path):
        try:
            if PDFPLUMBER_AVAILABLE:
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
            return ""
        except Exception as e:
            return ""

    def find_amount_from_text(self, text):
        amounts = []

        patterns = [
            r'￥\s*(\d+\.?\d*)',
            r'¥\s*(\d+\.?\d*)',
            r'价税合计[：:]\s*[￥¥]?\s*(\d+\.?\d*)',
            r'金额[：:]\s*[￥¥]?\s*(\d+\.?\d*)',
            r'实付[：:]\s*[￥¥]?\s*(\d+\.?\d*)',
            r'票价[：:]\s*[￥¥]?\s*(\d+\.?\d*)',
            r'票款[：:]\s*(\d+\.?\d*)',
        ]

        for pattern in patterns:
            amounts += re.findall(pattern, text)

        valid_amounts = []
        for a in amounts:
            try:
                clean_a = a.replace(',', '').strip()
                val = float(clean_a)
                if 1 <= val <= 10000:
                    valid_amounts.append(val)
            except:
                pass

        if valid_amounts:
            return max(valid_amounts)
        
        simpler = re.findall(r'(\d+\.\d{2})', text)
        for s in simpler:
            try:
                val = float(s)
                if 1 <= val <= 10000:
                    valid_amounts.append(val)
            except:
                pass
        
        if valid_amounts:
            return max(valid_amounts)
        return None

    def find_date_from_text(self, text):
        patterns = [
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?',
            r'(\d{4})(\d{2})(\d{2})',
        ]

        for pattern in patterns:
            dates = re.findall(pattern, text)
            for d in dates:
                try:
                    year = int(d[0])
                    month = int(d[1])
                    day = int(d[2])
                    if 2020 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                        return f"{year}-{month:02d}-{day:02d}"
                except:
                    pass
        return None

    def find_didi_time_from_text(self, text):
        import re
        time_patterns = [
            r'行程起止日期[：:]\s*(\d{4}-\d{2}-\d{2})\s*[至到-]\s*(\d{4}-\d{2}-\d{2})',
            r'(\d{4}-\d{2}-\d{2})\s*[至到-]\s*(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}:\d{2})\s*[至到-]\s*(\d{1,2}:\d{2})',
            r'(\d{1,2})年(\d{1,2})月(\d{1,2})日.*?(\d{1,2})年(\d{1,2})月(\d{1,2})日',
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None

    def extract_invoice_info(self, filename, relative_path=None):
        info = {
            "original_filename": filename,
            "type": "其他",
            "date": None,
            "amount": None,
            "is_refund": False,
            "from_station": None,
            "to_station": None,
            "merchant": None,
            "notes": "",
            "didi_time_start": None,
            "didi_time_end": None
        }

        info["is_refund"] = "退票" in filename or "【退票】" in filename or "[退票]" in filename

        if "站_到_" in filename or ("站" in filename and "_到_" in filename):
            info["type"] = "火车票"
            self._extract_train_ticket_info(filename, info)
        elif "餐饮" in filename:
            info["type"] = "餐饮发票"
            self._extract_restaurant_info(filename, info)
        elif "行程报销单" in filename:
            info["type"] = "滴滴行程报销单"
            self._extract_didi_info(filename, info)
        elif "电子发票" in filename or "滴滴" in filename:
            info["type"] = "滴滴电子发票"
            self._extract_didi_info(filename, info)
        elif "通行" in filename or "高速" in filename:
            info["type"] = "通行发票"
            self._extract_toll_info(filename, info)
        elif "租车" in filename or "商务租车" in filename:
            info["type"] = "车辆租赁"
        elif "登机" in filename or "机票" in filename:
            info["type"] = "机票"
        elif "话费" in filename or "移动" in filename or "联通" in filename or "电信" in filename:
            info["type"] = "话费"
        elif "行程报销单" in filename:
            info["type"] = "行程报销单"

        if not info["date"]:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if date_match:
                info["date"] = date_match.group(1)

        if info["is_refund"]:
            info["notes"] = "退票"

        return info

    def detect_train_ticket_from_text(self, text):
        text_clean = text.replace('\n', ' ').replace('站 站', '站')
        
        train_patterns = [
            r'([^\s]+站)\s+[GDCKZTY]\d+\s+([^\s]+站)',
            r'(合肥南|上海南|北京南|杭州东|南京南|广州南|深圳北|福州南|厦门北|长沙南|武汉|西安北|成都东|重庆北|合肥西|蚌埠南|常州北|义乌|徐州东|淮北|三明|南平)[站]*\s*[GDCKZTY]\d+\s*(合肥南|上海南|北京南|杭州东|南京南|广州南|深圳北|福州南|厦门北|长沙南|武汉|西安北|成都东|重庆北|合肥西|蚌埠南|常州北|义乌|徐州东|淮北|三明|南平)[站]*',
            r'出发站[：:]\s*([^县市区]+站)',
            r'到达站[：:]\s*([^县市区]+站)',
        ]
        
        result = {}
        for pattern in train_patterns:
            match = re.search(pattern, text_clean)
            if match:
                if len(match.groups()) >= 2:
                    result['出发站'] = match.group(1)
                    result['到达站'] = match.group(2)
                    break
                else:
                    key = pattern.split('[')[0].strip()
                    result[key] = match.group(1)
        
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日\s+\d{1,2}:\d{2}开',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'乘车日期[：:]\s*(\d{4})-(\d{1,2})-(\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                result['year'] = match.group(1)
                result['month'] = match.group(2)
                result['day'] = match.group(3)
                break
        
        return result

    def _extract_train_ticket_info(self, filename, info):
        pattern = r'([^站_]+站)_到_([^_]+站)_([\d.]+)_(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern, filename)
        if match:
            info["from_station"] = match.group(1)
            info["to_station"] = match.group(2)
            info["amount"] = float(match.group(3))
            info["date"] = match.group(4)
        else:
            pattern2 = r'([^站_]+站)_到_([^_]+站)_(\d+\.?\d*)_(\d{4})-(\d{2})-(\d{2})'
            match2 = re.search(pattern2, filename)
            if match2:
                info["from_station"] = match2.group(1)
                info["to_station"] = match2.group(2)
                info["amount"] = float(match2.group(3))
                info["date"] = f"{match2.group(4)}-{match2.group(5)}-{match2.group(6)}"
            else:
                pattern3 = r'([^站_]+站)_到_([^_]+站)_(\d+\.)(\d{4})-(\d{2})-(\d{2})'
                match3 = re.search(pattern3, filename)
                if match3:
                    info["from_station"] = match3.group(1)
                    info["to_station"] = match3.group(2)
                    info["amount"] = float(match3.group(3) + match3.group(4))
                    info["date"] = f"{match3.group(4)}-{match3.group(5)}-{match3.group(6)}"

    def _extract_restaurant_info(self, filename, info):
        parts = filename.split('_')
        for part in parts:
            amount_match = re.search(r'(\d+\.\d{2})', part)
            if amount_match and float(amount_match.group(1)) > 10:
                info["amount"] = float(amount_match.group(1))
                break
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info["date"] = date_match.group(1)
        if len(parts) >= 2:
            info["merchant"] = parts[1]

    def _extract_didi_info(self, filename, info):
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info["date"] = date_match.group(1)
        amount_match = re.search(r'(\d+\.\d{2})', filename)
        if amount_match:
            info["amount"] = float(amount_match.group(1))

    def _extract_toll_info(self, filename, info):
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info["date"] = date_match.group(1)
        amount_match = re.search(r'(\d+\.\d{2})', filename)
        if amount_match:
            info["amount"] = float(amount_match.group(1))

    def process_invoices(self):
        self.input_dir = self.input_var.get()
        self.output_dir = self.output_var.get()

        if not os.path.exists(self.input_dir):
            messagebox.showerror("错误", "发票目录不存在")
            return

        os.makedirs(self.output_dir, exist_ok=True)

        self.results = []
        self.train_tickets = []
        self.result_text.delete(1.0, tk.END)

        self.log("=" * 60)
        self.log("开始识别发票文件")
        self.log(f"输入目录: {self.input_dir}")
        self.log(f"输出目录: {self.output_dir}")
        self.log("=" * 60)

        self.set_status("正在识别...")

        count = 0
        didi_reimburse_dates = {}
        
        for root, dirs, files in os.walk(self.input_dir):
            if "processed" in root:
                continue
            for filename in files:
                if not filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    continue

                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, self.input_dir)
                info = self.extract_invoice_info(filename, relative_path)

                if self.use_pdf_extract.get() and filename.lower().endswith('.pdf'):
                    self.log(f"  提取PDF: {filename}")
                    pdf_text = self.extract_text_from_pdf(file_path)

                    if pdf_text:
                        pdf_amount = self.find_amount_from_text(pdf_text)
                        if pdf_amount and (not info["amount"] or pdf_amount > info["amount"]):
                            self.log(f"    PDF金额: {pdf_amount}")
                            info["amount"] = pdf_amount

                        didi_times = None
                        if info["type"] == "滴滴行程报销单":
                            didi_times = self.find_didi_time_from_text(pdf_text)
                            if didi_times and len(didi_times) >= 2 and '-' in str(didi_times[0]):
                                trip_date = didi_times[0]
                                info["didi_time_start"] = didi_times[0]
                                info["didi_time_end"] = didi_times[1]
                                info["date"] = trip_date
                                if pdf_amount:
                                    amount_key = round(pdf_amount, 2)
                                    if amount_key not in didi_reimburse_dates:
                                        didi_reimburse_dates[amount_key] = trip_date
                                    elif trip_date < didi_reimburse_dates[amount_key]:
                                        didi_reimburse_dates[amount_key] = trip_date
                                self.log(f"    行程日期: {trip_date} (至 {didi_times[1]})")
                            else:
                                pdf_date = self.find_date_from_text(pdf_text)
                                if pdf_date:
                                    info["date"] = pdf_date
                                    self.log(f"    行程报销单日期: {pdf_date}")
                        else:
                            pdf_date = self.find_date_from_text(pdf_text)
                            if pdf_date and not info["date"]:
                                self.log(f"    PDF日期: {pdf_date}")
                                info["date"] = pdf_date

                        if info["type"] in ["滴滴电子发票", "滴滴行程报销单"]:
                            didi_times = self.find_didi_time_from_text(pdf_text)
                            if didi_times:
                                if len(didi_times) == 2:
                                    if '-' in didi_times[0]:
                                        info["didi_time_start"] = didi_times[0]
                                        info["didi_time_end"] = didi_times[1]
                                    else:
                                        info["didi_time_start"] = f"{didi_times[0]}:00"
                                        info["didi_time_end"] = f"{didi_times[1]}:00"
                                elif len(didi_times) == 6:
                                    info["didi_time_start"] = f"{didi_times[0]}-{int(didi_times[1]):02d}-{int(didi_times[2]):02d}"
                                    info["didi_time_end"] = f"{didi_times[3]}-{int(didi_times[4]):02d}-{int(didi_times[5]):02d}"

                        if info["type"] == "其他" or not info["type"]:
                            train_info = self.detect_train_ticket_from_text(pdf_text)
                            if train_info and ('出发站' in train_info or '发站' in train_info or '乘车站' in train_info or '到达站' in train_info):
                                info["type"] = "火车票"
                                if '出发站' in train_info:
                                    info["from_station"] = train_info['出发站']
                                elif '发站' in train_info:
                                    info["from_station"] = train_info['发站']
                                elif '乘车站' in train_info:
                                    info["from_station"] = train_info['乘车站']
                                
                                if '到达站' in train_info:
                                    info["to_station"] = train_info['到达站']
                                elif '到站' in train_info:
                                    info["to_station"] = train_info['到站']
                                elif '下车站' in train_info:
                                    info["to_station"] = train_info['下车站']
                                
                                if 'year' in train_info and 'month' in train_info and 'day' in train_info:
                                    info["date"] = f"{train_info['year']}-{int(train_info['month']):02d}-{int(train_info['day']):02d}"
                                
                                if '退票' in pdf_text or '作废' in pdf_text:
                                    info["is_refund"] = True
                                    info["notes"] = "退票"
                                
                                self.log(f"    识别为火车票: {info['from_station']} → {info['to_station']}")
                    else:
                        self.log(f"    无法提取文本")

                new_filename = self._generate_new_filename(info)
                info["new_filename"] = new_filename

                dest_path = os.path.join(self.output_dir, new_filename)
                if not os.path.exists(dest_path):
                    try:
                        shutil.copy2(file_path, dest_path)
                    except Exception as e:
                        self.log(f"警告: 无法复制 {filename}: {str(e)}")
                        continue
                else:
                    base, ext = os.path.splitext(new_filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        new_filename = f"{base}_{counter}{ext}"
                        dest_path = os.path.join(self.output_dir, new_filename)
                        counter += 1
                    try:
                        shutil.copy2(file_path, dest_path)
                        info["new_filename"] = new_filename
                    except Exception as e:
                        self.log(f"警告: 无法复制 {filename}: {str(e)}")
                        continue

                self.results.append(info)
                if info["type"] == "火车票":
                    self.train_tickets.append(info)
                count += 1

        for info in self.results:
            if info["type"] == "滴滴电子发票" and info["amount"]:
                amount_key = round(info["amount"], 2)
                if amount_key in didi_reimburse_dates:
                    info["date"] = didi_reimburse_dates[amount_key]
                    self.log(f"  更新滴滴电子发票日期: {info['original_filename']} -> {info['date']}")

        self.log(f"\n识别完成！共处理 {count} 个文件")
        self.log(f"  - 火车票: {len(self.train_tickets)} 张")
        self.log(f"  - 餐饮发票: {len([r for r in self.results if r['type'] == '餐饮发票'])} 张")
        self.log(f"  - 滴滴电子发票: {len([r for r in self.results if r['type'] == '滴滴电子发票'])} 张")

        self.set_status("识别完成")

    def _generate_new_filename(self, info):
        ext = ".pdf"
        if info["type"] == "火车票":
            refund_tag = "_退票" if info["is_refund"] else ""
            return f"火车票_{info['date']}_{info['from_station']}_到_{info['to_station']}_{info['amount']}{refund_tag}{ext}"
        elif info["type"] == "餐饮发票":
            merchant = info.get("merchant", "未知")[:10]
            return f"餐饮_{merchant}_{info['amount']}_{info['date']}{ext}"
        elif info["type"] == "滴滴电子发票":
            return f"滴滴_{info['date']}_{info['amount']}{ext}"
        else:
            date_str = info["date"] or "未知日期"
            amount_str = str(info["amount"]) if info["amount"] else "未知金额"
            return f"{info['type']}_{date_str}_{amount_str}{ext}"

    def show_results(self):
        self.result_text.delete(1.0, tk.END)
        self.log("=" * 60)
        self.log("识别结果详情")
        self.log("=" * 60)

        type_groups = {}
        for r in self.results:
            t = r["type"]
            if t not in type_groups:
                type_groups[t] = []
            type_groups[t].append(r)

        for in_type, items in type_groups.items():
            self.log(f"\n【{in_type}】- 共 {len(items)} 张")
            self.log("-" * 40)
            for item in items:
                refund = " [退票]" if item["is_refund"] else ""
                amount = f"{item['amount']:.2f}" if item["amount"] else "未知"
                date = item["date"] or "未知日期"
                self.log(f"  {date} | {amount}元 | {item['original_filename'][:35]}")

    def show_train_tickets(self):
        if not self.train_tickets:
            messagebox.showinfo("提示", "没有识别到火车票")
            return

        sorted_tickets = sorted(self.train_tickets, key=lambda x: (x["date"] or "", x["amount"] or 0))

        self.result_text.delete(1.0, tk.END)
        self.log("=" * 60)
        self.log("火车票列表（按日期排序）")
        self.log("=" * 60)
        self.log(f"{'序号':<4} {'日期':<12} {'出发站':<10} {'到达站':<10} {'金额':<10} {'状态':<8}")
        self.log("-" * 60)

        for i, ticket in enumerate(sorted_tickets, 1):
            refund = "退票" if ticket["is_refund"] else "正常"
            self.log(f"{i:<4} {ticket['date']:<12} {(ticket['from_station'] or '-')[:10]:<10} "
                    f"{(ticket['to_station'] or '-')[:10]:<10} {ticket['amount']:<10.2f} {refund:<8}")

    def generate_report(self, folder_path, start_date, end_date):
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append(f"发票统计报告")
        report_lines.append(f"时间区间: {start_date} 至 {end_date}")
        report_lines.append("=" * 60)
        report_lines.append("")

        type_groups = {}
        total_amount = 0
        files = os.listdir(folder_path)

        for f in files:
            f_path = os.path.join(folder_path, f)
            if os.path.isdir(f_path):
                subfiles = os.listdir(f_path)
                for sf in subfiles:
                    if sf.endswith('.pdf'):
                        if "滴滴" in sf:
                            t = "滴滴出行"
                        elif "餐饮" in sf:
                            t = "餐饮"
                        elif "火车票" in sf:
                            t = "火车票"
                        elif "通行" in sf:
                            t = "通行"
                        elif "车辆租赁" in sf or "租车" in sf:
                            t = "车辆租赁"
                        elif "话费" in sf or "移动" in sf or "联通" in sf or "电信" in sf:
                            t = "话费"
                        else:
                            t = "其他"
                        if t not in type_groups:
                            type_groups[t] = {"count": 0, "amount": 0, "files": []}
                        type_groups[t]["count"] += 1
                        try:
                            amount_match = re.search(r'_(\d+\.?\d*)\.pdf', sf)
                            if amount_match:
                                amount = float(amount_match.group(1))
                                type_groups[t]["amount"] += amount
                                total_amount += amount
                        except:
                            pass
                        type_groups[t]["files"].append(sf)
            elif f.endswith('.pdf'):
                if "餐饮" in f:
                    t = "餐饮"
                elif "火车票" in f:
                    t = "火车票"
                elif "滴滴" in f:
                    t = "滴滴出行"
                elif "通行" in f:
                    t = "通行"
                elif "车辆租赁" in f or "租车" in f:
                    t = "车辆租赁"
                elif "话费" in f or "移动" in f or "联通" in f or "电信" in f:
                    t = "话费"
                else:
                    t = f.split('_')[0] if '_' in f else "其他"
                if t not in type_groups:
                    type_groups[t] = {"count": 0, "amount": 0, "files": []}
                type_groups[t]["count"] += 1
                try:
                    parts = f.replace('.pdf', '').split('_')
                    for part in reversed(parts):
                        try:
                            amount = float(part)
                            if amount > 0:
                                type_groups[t]["amount"] += amount
                                total_amount += amount
                                break
                        except:
                            continue
                except:
                    pass
                type_groups[t]["files"].append(f)

        for t, data in type_groups.items():
            report_lines.append(f"【{t}】")
            report_lines.append(f"  数量: {data['count']} 张")
            report_lines.append(f"  金额: {data['amount']:.2f} 元")
            report_lines.append("")

        report_lines.append("=" * 60)
        report_lines.append(f"总计: {sum(d['count'] for d in type_groups.values())} 张, {total_amount:.2f} 元")
        report_lines.append("=" * 60)

        report_content = "\n".join(report_lines)
        report_path = os.path.join(folder_path, "统计报告.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        self.log(f"已生成统计报告: {report_path}")

    def organize_by_date_range(self):
        if not self.train_tickets:
            messagebox.showinfo("提示", "没有火车票可整理")
            return

        sorted_tickets = sorted(self.train_tickets, key=lambda x: (x["date"] or "", x.get("from_station", "")))

        dialog = tk.Toplevel(self.root)
        dialog.title("按火车票区间整理发票")
        dialog.geometry("700x600")
        dialog.transient(self.root)

        ttk.Label(dialog, text="选择火车票区间：先选开始火车票，再选结束火车票", font=("微软雅黑", 11)).pack(pady=10)

        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(list_frame, font=("Consolas", 10), yscrollcommand=scrollbar.set, selectmode=tk.MULTIPLE)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for i, ticket in enumerate(sorted_tickets):
            refund = " [退票]" if ticket["is_refund"] else ""
            display = f"{i+1}. {ticket['date']} | {ticket['from_station']} → {ticket['to_station']} | {ticket['amount']:.2f}元{refund}"
            listbox.insert(tk.END, display)

        info_label = ttk.Label(dialog, text="请选择2张火车票（开始和结束）", foreground="blue")
        info_label.pack(pady=5)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        def do_organize():
            selection = listbox.curselection()
            if len(selection) != 2:
                messagebox.showwarning("警告", "请选择2张火车票（开始和结束）")
                return

            start_idx, end_idx = sorted(selection)
            start_ticket = sorted_tickets[start_idx]
            end_ticket = sorted_tickets[end_idx]

            start_date = start_ticket["date"]
            end_date = end_ticket["date"]

            if not start_date or not end_date:
                messagebox.showerror("错误", "火车票日期信息不完整")
                return

            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
            except:
                messagebox.showerror("错误", "日期格式错误")
                return

            if start > end:
                messagebox.showwarning("警告", "开始日期不能晚于结束日期")
                return

            folder_name = f"{start_date}_至_{end_date}"
            target_dir = os.path.join(self.output_dir, folder_name)
            os.makedirs(target_dir, exist_ok=True)

            count = 0

            for ticket in sorted_tickets:
                if not ticket["date"]:
                    continue
                try:
                    ticket_date = datetime.strptime(ticket["date"], '%Y-%m-%d')
                    if start <= ticket_date <= end:
                        src = os.path.join(self.output_dir, ticket["new_filename"])
                        if os.path.exists(src):
                            dst = os.path.join(target_dir, ticket["new_filename"])
                            shutil.move(src, dst)
                            count += 1
                            self.log(f"  移动火车票: {ticket['new_filename']}")
                except:
                    pass

            didi_pairs = {}
            for item in self.results:
                if item["type"] not in ["滴滴电子发票", "滴滴行程报销单"]:
                    continue
                if not item["date"]:
                    continue
                try:
                    item_date = datetime.strptime(item["date"], '%Y-%m-%d')
                    if not (start <= item_date <= end):
                        continue
                except:
                    continue

                if item["amount"] is None:
                    continue

                amount_key = round(item["amount"], 2)
                if amount_key not in didi_pairs:
                    didi_pairs[amount_key] = {"电子发票": None, "行程报销单": None}

                if item["type"] == "滴滴电子发票":
                    didi_pairs[amount_key]["电子发票"] = item
                elif item["type"] == "滴滴行程报销单":
                    didi_pairs[amount_key]["行程报销单"] = item

            for amount, pair in didi_pairs.items():
                if pair["电子发票"] and pair["行程报销单"]:
                    didi_folder = f"滴滴_{start_date}_至_{end_date}_金额{amount}"
                    didi_dir = os.path.join(target_dir, didi_folder)
                    os.makedirs(didi_dir, exist_ok=True)

                    for item in [pair["电子发票"], pair["行程报销单"]]:
                        src = os.path.join(self.output_dir, item["new_filename"])
                        if os.path.exists(src):
                            dst = os.path.join(didi_dir, item["new_filename"])
                            shutil.move(src, dst)
                            count += 1
                            self.log(f"  移动滴滴: {item['new_filename']}")
                else:
                    if pair["电子发票"]:
                        item = pair["电子发票"]
                        src = os.path.join(self.output_dir, item["new_filename"])
                        if os.path.exists(src):
                            dst = os.path.join(target_dir, item["new_filename"])
                            shutil.move(src, dst)
                            count += 1
                            self.log(f"  移动滴滴(未配对): {item['new_filename']}")
                    if pair["行程报销单"]:
                        item = pair["行程报销单"]
                        src = os.path.join(self.output_dir, item["new_filename"])
                        if os.path.exists(src):
                            dst = os.path.join(target_dir, item["new_filename"])
                            shutil.move(src, dst)
                            count += 1
                            self.log(f"  移动滴滴(未配对): {item['new_filename']}")

            for item in self.results:
                if item["type"] in ["火车票", "滴滴电子发票", "滴滴行程报销单"]:
                    continue
                if not item["date"]:
                    continue
                try:
                    item_date = datetime.strptime(item["date"], '%Y-%m-%d')
                    if start <= item_date <= end:
                        src = os.path.join(self.output_dir, item["new_filename"])
                        if os.path.exists(src):
                            dst = os.path.join(target_dir, item["new_filename"])
                            shutil.move(src, dst)
                            count += 1
                            self.log(f"  移动: {item['new_filename']}")
                except:
                    pass

            self.generate_report(target_dir, start_date, end_date)

            dialog.destroy()
            messagebox.showinfo("完成", f"已将 {count} 张发票整理到 '{folder_name}' 文件夹\n滴滴发票已按金额配对\n已生成统计报告")

        ttk.Button(btn_frame, text="确认整理", command=do_organize).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)



def main():
    root = tk.Tk()
    app = InvoiceProcessorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
