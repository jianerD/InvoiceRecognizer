import os
import sys
import argparse
import json
from pathlib import Path
from invoice_core.recognizer import InvoiceRecognizer, InvoiceType
from invoice_core.storage import StagingManager, InvoiceOrganizer


def cmd_recognize(args):
    print(f"正在识别发票目录: {args.input}")
    print(f"输出目录: {args.output}")

    recognizer = InvoiceRecognizer()
    results = recognizer.recognize_directory(args.input, args.output)

    print(f"\n识别完成! 共处理 {len(results)} 个文件")
    print("\n识别结果统计:")

    stats = recognizer.get_statistics()
    for inv_type, data in stats.items():
        print(f"  {inv_type}: {data['count']} 张, 金额: {data['amount']:.2f} 元")

    if args.json:
        json_path = os.path.join(args.output, "recognition_result.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in results], f, ensure_ascii=False, indent=2)
        print(f"\n识别结果已保存到: {json_path}")

    return 0


def cmd_staging(args):
    staging = StagingManager(args.base_dir if args.base_dir else "data")

    if args.action == "list":
        invoices = staging.get_invoices()
        print(f"暂存区共有 {len(invoices)} 张发票:\n")

        if args.type:
            invoices = [inv for inv in invoices if inv.type == args.type]

        for inv in invoices:
            amount_str = f"{inv.amount:.2f}" if inv.amount else "未知"
            print(f"  [{inv.type}] {inv.date or '未知日期'} | {amount_str}元 | {inv.filename}")

        print(f"\n总计: {len(invoices)} 张")

        stats = staging.get_statistics()
        print(f"总金额: {stats['total_amount']:.2f} 元")

    elif args.action == "add":
        if not args.input:
            print("错误: 请指定要导入的发票目录 (--input)")
            return 1

        print(f"正在从 {args.input} 导入发票到暂存区...")

        recognizer = InvoiceRecognizer()
        results = recognizer.recognize_directory(args.input)

        staging.add_invoices(results)
        print(f"已导入 {len(results)} 张发票到暂存区")

    elif args.action == "clear":
        confirm = input("确定要清空暂存区吗? (y/n): ")
        if confirm.lower() == 'y':
            staging.clear_staging()
            print("暂存区已清空")
        else:
            print("操作取消")

    elif args.action == "remove":
        if not args.filename:
            print("错误: 请指定要删除的文件名 (--filename)")
            return 1

        if staging.remove_invoice(args.filename):
            print(f"已删除: {args.filename}")
        else:
            print(f"文件不存在: {args.filename}")

    elif args.action == "export":
        export_path = args.output or "staging_export.json"
        staging.export_json(export_path)
        print(f"已导出到: {export_path}")

    return 0


def cmd_organize(args):
    staging = StagingManager(args.base_dir if args.base_dir else "data")
    organizer = InvoiceOrganizer(staging)

    if args.action == "range":
        if not args.start or not args.end:
            print("错误: 请指定开始和结束日期 (--start, --end)")
            return 1

        print(f"正在整理 {args.start} 至 {args.end} 的发票...")

        result = organizer.organize_by_date_range(args.start, args.end)

        if result["success"]:
            print(f"\n整理完成!")
            print(f"目标目录: {result['target_dir']}")
            print(f"发票数量: {result['invoice_count']}")
            print(f"统计报告: {result['report']}")
        else:
            print(f"整理失败: {result['message']}")

    elif args.action == "match":
        if not args.start or not args.end:
            print("错误: 请指定日期区间 (--start, --end)")
            return 1

        result = organizer.auto_match_invoices(args.start, args.end)

        print(f"\n自动匹配完成!")
        print(f"匹配到的配对数: {result['total_pairs']}")
        print(f"涉及的发票数: {result['matched_invoices']}")

        for i, pair in enumerate(result['pairs'], 1):
            print(f"\n配对 {i}:")
            print(f"  发票1: {pair['invoice1'].type} - {pair['invoice1'].filename}")
            print(f"  发票2: {pair['invoice2'].type} - {pair['invoice2'].filename}")
            print(f"  匹配金额: {pair['matched_amount']:.2f} 元")

    return 0


def cmd_report(args):
    staging = StagingManager(args.base_dir if args.base_dir else "data")

    stats = staging.get_statistics()

    print("=" * 50)
    print("发票统计报告")
    print("=" * 50)
    print(f"总发票数: {stats['total_count']} 张")
    print(f"总金额: {stats['total_amount']:.2f} 元")
    print()

    for inv_type, data in stats['by_type'].items():
        print(f"【{inv_type}】")
        print(f"  数量: {data['count']} 张")
        print(f"  金额: {data['amount']:.2f} 元")
        print()

    if args.json:
        json_path = args.output or "report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"报告已保存到: {json_path}")

    if args.excel:
        try:
            import pandas as pd
            data_list = []
            for inv in staging.get_invoices():
                data_list.append({
                    "类型": inv.type,
                    "日期": inv.date,
                    "金额": inv.amount,
                    "文件名": inv.filename,
                    "备注": inv.notes
                })

            df = pd.DataFrame(data_list)
            excel_path = args.output or "report.xlsx"
            df.to_excel(excel_path, index=False)
            print(f"Excel报告已保存到: {excel_path}")
        except ImportError:
            print("错误: 需要安装 pandas 和 openpyxl 才能导出Excel")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="发票识别工具 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 识别发票
  python -m invoice_cli recognize --input ./invoices --output ./output

  # 查看暂存区
  python -m invoice_cli staging list

  # 添加发票到暂存区
  python -m invoice_cli staging add --input ./invoices

  # 按区间整理发票
  python -m invoice_cli organize range --start 2026-01-01 --end 2026-01-31

  # 查看统计报告
  python -m invoice_cli report
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    parser_recognize = subparsers.add_parser("recognize", help="识别发票")
    parser_recognize.add_argument("--input", "-i", required=True, help="输入目录")
    parser_recognize.add_argument("--output", "-o", required=True, help="输出目录")
    parser_recognize.add_argument("--json", action="store_true", help="保存JSON结果")

    parser_staging = subparsers.add_parser("staging", help="暂存区管理")
    parser_staging.add_argument("--action", choices=["list", "add", "clear", "remove", "export"],
                               default="list", help="操作类型")
    parser_staging.add_argument("--input", help="输入目录 (add命令用)")
    parser_staging.add_argument("--filename", help="文件名 (remove命令用)")
    parser_staging.add_argument("--output", help="输出文件 (export命令用)")
    parser_staging.add_argument("--type", help="发票类型过滤")
    parser_staging.add_argument("--base-dir", help="数据目录")

    parser_organize = subparsers.add_parser("organize", help="整理发票")
    parser_organize.add_argument("--action", choices=["range", "match"],
                                 default="range", help="操作类型")
    parser_organize.add_argument("--start", help="开始日期 (YYYY-MM-DD)")
    parser_organize.add_argument("--end", help="结束日期 (YYYY-MM-DD)")
    parser_organize.add_argument("--base-dir", help="数据目录")

    parser_report = subparsers.add_parser("report", help="查看统计报告")
    parser_report.add_argument("--json", action="store_true", help="导出JSON")
    parser_report.add_argument("--excel", action="store_true", help="导出Excel")
    parser_report.add_argument("--output", help="输出文件路径")
    parser_report.add_argument("--base-dir", help="数据目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "recognize":
        return cmd_recognize(args)
    elif args.command == "staging":
        return cmd_staging(args)
    elif args.command == "organize":
        return cmd_organize(args)
    elif args.command == "report":
        return cmd_report(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
