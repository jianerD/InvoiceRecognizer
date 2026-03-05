import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Any
from .recognizer import InvoiceInfo, InvoiceRecognizer, InvoiceType


class StagingManager:
    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.staging_dir = os.path.join(base_dir, "staging")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.metadata_file = os.path.join(self.staging_dir, "metadata.json")

        os.makedirs(self.staging_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

        self.invoices: List[InvoiceInfo] = []
        self.load_metadata()

    def load_metadata(self):
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.invoices = [self._dict_to_invoice(d) for d in data.get('invoices', [])]
            except Exception as e:
                print(f"Failed to load metadata: {e}")
                self.invoices = []

    def save_metadata(self):
        try:
            data = {
                'invoices': [self._invoice_to_dict(inv) for inv in self.invoices],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save metadata: {e}")

    def _invoice_to_dict(self, info: InvoiceInfo) -> Dict[str, Any]:
        return info.to_dict()

    def _dict_to_invoice(self, d: Dict[str, Any]) -> InvoiceInfo:
        info = InvoiceInfo()
        info.original_filename = d.get('original_filename', '')
        info.filename = d.get('filename', '')
        info.filepath = d.get('filepath', '')
        info.type = d.get('type', InvoiceType.OTHER)
        info.date = d.get('date')
        info.amount = d.get('amount')
        info.is_refund = d.get('is_refund', False)
        info.from_station = d.get('from_station')
        info.to_station = d.get('to_station')
        info.merchant = d.get('merchant')
        info.notes = d.get('notes', '')
        info.didi_time_start = d.get('didi_time_start')
        info.didi_time_end = d.get('didi_time_end')
        info.flight_number = d.get('flight_number')
        info.flight_from = d.get('flight_from')
        info.flight_to = d.get('flight_to')
        info.hotel_name = d.get('hotel_name')
        info.checkin_date = d.get('checkin_date')
        info.checkout_date = d.get('checkout_date')
        info.express_company = d.get('express_company')
        info.phone_provider = d.get('phone_provider')
        info.confidence = d.get('confidence', 0.0)
        return info

    def add_invoices(self, invoices: List[InvoiceInfo]):
        for info in invoices:
            staging_path = os.path.join(self.staging_dir, info.filename)
            if os.path.exists(info.filepath):
                shutil.copy2(info.filepath, staging_path)
                info.filepath = staging_path
                self.invoices.append(info)
        self.save_metadata()

    def remove_invoice(self, filename: str) -> bool:
        for i, inv in enumerate(self.invoices):
            if inv.filename == filename or inv.original_filename == filename:
                filepath = os.path.join(self.staging_dir, inv.filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                self.invoices.pop(i)
                self.save_metadata()
                return True
        return False

    def get_invoices(self) -> List[InvoiceInfo]:
        return self.invoices

    def get_invoices_by_type(self, invoice_type: str) -> List[InvoiceInfo]:
        return [inv for inv in self.invoices if inv.type == invoice_type]

    def get_invoices_by_date_range(self, start_date: str, end_date: str) -> List[InvoiceInfo]:
        result = []
        for inv in self.invoices:
            if inv.date and start_date <= inv.date <= end_date:
                result.append(inv)
        return result

    def clear_staging(self):
        for inv in self.invoices:
            filepath = os.path.join(self.staging_dir, inv.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        self.invoices = []
        self.save_metadata()

    def move_to_processed(self, invoices: List[InvoiceInfo], target_folder: str = None) -> str:
        if target_folder is None:
            target_folder = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        target_dir = os.path.join(self.processed_dir, target_folder)
        os.makedirs(target_dir, exist_ok=True)

        for inv in self.invoices:
            if inv in invoices:
                src = os.path.join(self.staging_dir, inv.filename)
                dst = os.path.join(target_dir, inv.filename)
                if os.path.exists(src):
                    shutil.move(src, dst)
                    self.invoices.remove(inv)

        self.save_metadata()
        return target_dir

    def export_json(self, filepath: str):
        data = {
            'invoices': [inv.to_dict() for inv in self.invoices],
            'total_count': len(self.invoices),
            'exported_at': datetime.now().isoformat()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        stats = {}
        total_amount = 0

        for inv in self.invoices:
            if inv.type not in stats:
                stats[inv.type] = {"count": 0, "amount": 0.0}
            stats[inv.type]["count"] += 1
            if inv.amount:
                stats[inv.type]["amount"] += inv.amount
                total_amount += inv.amount

        return {
            "total_count": len(self.invoices),
            "total_amount": total_amount,
            "by_type": stats
        }


class InvoiceOrganizer:
    def __init__(self, staging_manager: StagingManager):
        self.staging = staging_manager

    def organize_by_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        invoices = self.staging.get_invoices_by_date_range(start_date, end_date)

        if not invoices:
            return {"success": False, "message": "指定日期区间内没有发票"}

        target_folder = f"{start_date}_至_{end_date}"
        target_dir = self.staging.move_to_processed(invoices, target_folder)

        stats = self._calculate_stats(invoices)

        report = self._generate_report(invoices, start_date, end_date, target_dir)

        return {
            "success": True,
            "target_dir": target_dir,
            "invoice_count": len(invoices),
            "stats": stats,
            "report": report
        }

    def match_didi_invoices(self, invoices: List[InvoiceInfo]) -> List[Dict[str, Any]]:
        didi_invoices = [inv for inv in invoices if inv.type in [InvoiceType.DIDI, InvoiceType.DIDI_REIMBURSE]]

        pairs = []
        for i, inv1 in enumerate(didi_invoices):
            for inv2 in didi_invoices[i+1:]:
                if inv1.type != inv2.type and inv1.amount and inv2.amount:
                    if abs(inv1.amount - inv2.amount) < 0.01:
                        pairs.append({
                            "invoice1": inv1,
                            "invoice2": inv2,
                            "matched_amount": inv1.amount
                        })

        return pairs

    def auto_match_invoices(self, start_date: str, end_date: str) -> Dict[str, Any]:
        invoices = self.staging.get_invoices_by_date_range(start_date, end_date)

        pairs = self.match_didi_invoices(invoices)

        matched_invoices = []
        for pair in pairs:
            matched_invoices.append(pair["invoice1"])
            matched_invoices.append(pair["invoice2"])

        return {
            "total_pairs": len(pairs),
            "pairs": pairs,
            "matched_invoices": len(matched_invoices)
        }

    def _calculate_stats(self, invoices: List[InvoiceInfo]) -> Dict[str, Any]:
        stats = {}
        total_amount = 0

        for inv in invoices:
            if inv.type not in stats:
                stats[inv.type] = {"count": 0, "amount": 0.0}
            stats[inv.type]["count"] += 1
            if inv.amount:
                stats[inv.type]["amount"] += inv.amount
                total_amount += inv.amount

        return {
            "by_type": stats,
            "total_count": len(invoices),
            "total_amount": total_amount
        }

    def _generate_report(self, invoices: List[InvoiceInfo], start_date: str, end_date: str, target_dir: str) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("发票统计报告")
        lines.append(f"时间区间: {start_date} 至 {end_date}")
        lines.append("=" * 60)
        lines.append("")

        stats = self._calculate_stats(invoices)

        for inv_type, data in stats["by_type"].items():
            lines.append(f"【{inv_type}】")
            lines.append(f"  数量: {data['count']} 张")
            lines.append(f"  金额: {data['amount']:.2f} 元")
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"总计: {stats['total_count']} 张, {stats['total_amount']:.2f} 元")
        lines.append("=" * 60)

        report_content = "\n".join(lines)
        report_path = os.path.join(target_dir, "统计报告.txt")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_path
