import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class InvoiceType:
    TRAIN = "火车票"
    DIDI = "滴滴电子发票"
    DIDI_REIMBURSE = "滴滴行程报销单"
    RESTAURANT = "餐饮发票"
    TOLL = "通行发票"
    CAR_RENTAL = "车辆租赁"
    FLIGHT = "机票"
    FLIGHT_ITINERARY = "机票行程单"
    PHONE_BILL = "话费"
    HOTEL = "酒店发票"
    EXPRESS = "快递发票"
    OTHER = "其他"


class InvoiceInfo:
    def __init__(self):
        self.original_filename = ""
        self.filename = ""
        self.filepath = ""
        self.type = InvoiceType.OTHER
        self.date = None
        self.amount = None
        self.is_refund = False
        self.from_station = None
        self.to_station = None
        self.merchant = None
        self.notes = ""
        self.didi_time_start = None
        self.didi_time_end = None
        self.flight_number = None
        self.flight_from = None
        self.flight_to = None
        self.hotel_name = None
        self.checkin_date = None
        self.checkout_date = None
        self.express_company = None
        self.phone_provider = None
        self.raw_text = ""
        self.confidence = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_filename": self.original_filename,
            "filename": self.filename,
            "filepath": self.filepath,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "is_refund": self.is_refund,
            "from_station": self.from_station,
            "to_station": self.to_station,
            "merchant": self.merchant,
            "notes": self.notes,
            "didi_time_start": self.didi_time_start,
            "didi_time_end": self.didi_time_end,
            "flight_number": self.flight_number,
            "flight_from": self.flight_from,
            "flight_to": self.flight_to,
            "hotel_name": self.hotel_name,
            "checkin_date": self.checkin_date,
            "checkout_date": self.checkout_date,
            "express_company": self.express_company,
            "phone_provider": self.phone_provider,
            "confidence": self.confidence
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class InvoiceRecognizer:
    STATION_KEYWORDS = [
        "合肥南", "上海南", "北京南", "杭州东", "南京南", "广州南", "深圳北",
        "福州南", "厦门北", "长沙南", "武汉", "西安北", "成都东", "重庆北",
        "合肥西", "蚌埠南", "常州北", "义乌", "徐州东", "淮北", "三明",
        "南平", "南平市", "三明北", "杭州西", "上海虹桥", "北京首都"
    ]

    FLIGHT_COMPANIES = [
        "国航", "东航", "南航", "海航", "川航", "厦航", "深航",
        "山航", "津航", "祥鹏", "华夏", "春秋", "吉祥"
    ]

    EXPRESS_COMPANIES = [
        "顺丰", "中通", "圆通", "韵达", "申通", "极兔", "邮政",
        "德邦", "京东", "UPS", "DHL", "FedEx"
    ]

    PHONE_PROVIDERS = ["移动", "联通", "电信"]

    def __init__(self):
        self.results: List[InvoiceInfo] = []

    def recognize_file(self, filepath: str) -> InvoiceInfo:
        filename = os.path.basename(filepath)
        info = InvoiceInfo()
        info.original_filename = filename
        info.filename = filename
        info.filepath = filepath

        self._detect_type_from_filename(filename, info)

        if filename.lower().endswith('.pdf') and PDFPLUMBER_AVAILABLE:
            text = self._extract_text_from_pdf(filepath)
            if text:
                info.raw_text = text
                self._enhance_from_text(text, info)

        if not info.date:
            info.date = self._extract_date_from_filename(filename)

        if not info.amount:
            info.amount = self._extract_amount_from_filename(filename)

        info.filename = self._generate_new_filename(info)
        return info

    def _detect_type_from_filename(self, filename: str, info: InvoiceInfo):
        info.is_refund = "退票" in filename or "【退票】" in filename or "[退票]" in filename

        if "站_到_" in filename or ("站" in filename and "_到_" in filename):
            info.type = InvoiceType.TRAIN
            self._extract_train_info(filename, info)
        elif "餐饮" in filename:
            info.type = InvoiceType.RESTAURANT
            self._extract_restaurant_info(filename, info)
        elif "行程报销单" in filename:
            info.type = InvoiceType.DIDI_REIMBURSE
            self._extract_didi_info(filename, info)
        elif "电子发票" in filename or "滴滴" in filename:
            info.type = InvoiceType.DIDI
            self._extract_didi_info(filename, info)
        elif "通行" in filename or "高速" in filename:
            info.type = InvoiceType.TOLL
            self._extract_toll_info(filename, info)
        elif "租车" in filename or "商务租车" in filename:
            info.type = InvoiceType.CAR_RENTAL
        elif "登机" in filename or "机票" in filename:
            info.type = InvoiceType.FLIGHT_ITINERARY
            self._extract_flight_info(filename, info)
        elif "话费" in filename or any(p in filename for p in self.PHONE_PROVIDERS):
            info.type = InvoiceType.PHONE_BILL
            self._extract_phone_info(filename, info)
        elif "酒店" in filename or "住宿" in filename or "宾馆" in filename:
            info.type = InvoiceType.HOTEL
            self._extract_hotel_info(filename, info)
        elif any(c in filename for c in self.EXPRESS_COMPANIES):
            info.type = InvoiceType.EXPRESS
            self._extract_express_info(filename, info)

        if info.is_refund:
            info.notes = "退票"

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            if PDFPLUMBER_AVAILABLE:
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
        except Exception:
            pass
        return ""

    def _enhance_from_text(self, text: str, info: InvoiceInfo):
        amount = self._find_amount_from_text(text)
        if amount and (not info.amount or amount > info.amount):
            info.amount = amount
            info.confidence = min(info.confidence + 0.3, 1.0)

        if not info.date:
            date = self._find_date_from_text(text)
            if date:
                info.date = date

        if info.type == InvoiceType.TRAIN:
            self._detect_train_from_text(text, info)
        elif info.type == InvoiceType.DIDI_REIMBURSE:
            self._detect_didi_times(text, info)
        elif info.type == InvoiceType.FLIGHT_ITINERARY:
            self._detect_flight_from_text(text, info)
        elif info.type == InvoiceType.PHONE_BILL:
            self._detect_phone_from_text(text, info)
        elif info.type == InvoiceType.HOTEL:
            self._detect_hotel_from_text(text, info)

    def _detect_train_from_text(self, text: str, info: InvoiceInfo):
        text_clean = text.replace('\n', ' ').replace('站 站', '站')

        for station in self.STATION_KEYWORDS:
            if station in text_clean:
                info.confidence = min(info.confidence + 0.2, 1.0)
                break

        if '退票' in text or '作废' in text:
            info.is_refund = True
            info.notes = "退票"

    def _detect_didi_times(self, text: str, info: InvoiceInfo):
        patterns = [
            r'行程起止日期[：:]\s*(\d{4}-\d{2}-\d{2})\s*[至到-]\s*(\d{4}-\d{2}-\d{2})',
            r'(\d{4}-\d{2}-\d{2})\s*[至到-]\s*(\d{4}-\d{2}-\d{2})',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                info.didi_time_start = matches[0][0]
                info.didi_time_end = matches[0][1]
                if not info.date:
                    info.date = matches[0][0]
                break

    def _detect_flight_from_text(self, text: str, info: InvoiceInfo):
        for company in self.FLIGHT_COMPANIES:
            if company in text:
                info.flight_number = company
                break

        dates = self._find_date_from_text(text)
        if dates:
            info.date = dates

    def _detect_phone_from_text(self, text: str, info: InvoiceInfo):
        for provider in self.PHONE_PROVIDERS:
            if provider in text:
                info.phone_provider = provider
                break

    def _detect_hotel_from_text(self, text: str, info: InvoiceInfo):
        patterns = [
            r'入住[：:]\s*(\d{4}-\d{2}-\d{2})',
            r'离店[：:]\s*(\d{4}-\d{2}-\d{2})',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                if '入住' in pattern:
                    info.checkin_date = matches[0][0]
                elif '离店' in pattern:
                    info.checkout_date = matches[0][0]
                break

    def _extract_train_info(self, filename: str, info: InvoiceInfo):
        patterns = [
            r'([^站_]+站)_到_([^_]+站)_([\d.]+)_(\d{4}-\d{2}-\d{2})',
            r'([^站_]+站)_到_([^_]+站)_(\d+\.?\d*)_(\d{4})-(\d{2})-(\d{2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                info.from_station = match.group(1)
                info.to_station = match.group(2)
                info.amount = float(match.group(3))
                if len(match.groups()) >= 4:
                    info.date = match.group(4) if '-' in match.group(4) else f"{match.group(4)}-{match.group(5)}-{match.group(6)}"
                break

    def _extract_restaurant_info(self, filename: str, info: InvoiceInfo):
        parts = filename.split('_')
        for part in parts:
            amount_match = re.search(r'(\d+\.\d{2})', part)
            if amount_match and float(amount_match.group(1)) > 10:
                info.amount = float(amount_match.group(1))
                break
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info.date = date_match.group(1)
        if len(parts) >= 2:
            info.merchant = parts[1]

    def _extract_didi_info(self, filename: str, info: InvoiceInfo):
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info.date = date_match.group(1)
        amount_match = re.search(r'(\d+\.\d{2})', filename)
        if amount_match:
            info.amount = float(amount_match.group(1))

    def _extract_toll_info(self, filename: str, info: InvoiceInfo):
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info.date = date_match.group(1)
        amount_match = re.search(r'(\d+\.\d{2})', filename)
        if amount_match:
            info.amount = float(amount_match.group(1))

    def _extract_flight_info(self, filename: str, info: InvoiceInfo):
        for company in self.FLIGHT_COMPANIES:
            if company in filename:
                info.flight_number = company
                break

        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info.date = date_match.group(1)

        amount_match = re.search(r'(\d+\.\d{2})', filename)
        if amount_match:
            info.amount = float(amount_match.group(1))

    def _extract_phone_info(self, filename: str, info: InvoiceInfo):
        for provider in self.PHONE_PROVIDERS:
            if provider in filename:
                info.phone_provider = provider
                break

        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info.date = date_match.group(1)

        amount_match = re.search(r'(\d+\.\d{2})', filename)
        if amount_match:
            info.amount = float(amount_match.group(1))

    def _extract_hotel_info(self, filename: str, info: InvoiceInfo):
        parts = filename.split('_')
        if len(parts) >= 2:
            info.hotel_name = parts[1]

        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info.date = date_match.group(1)

        amount_match = re.search(r'(\d+\.\d{2})', filename)
        if amount_match:
            info.amount = float(amount_match.group(1))

    def _extract_express_info(self, filename: str, info: InvoiceInfo):
        for company in self.EXPRESS_COMPANIES:
            if company in filename:
                info.express_company = company
                break

        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            info.date = date_match.group(1)

        amount_match = re.search(r'(\d+\.\d{2})', filename)
        if amount_match:
            info.amount = float(amount_match.group(1))

    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if match:
            return match.group(1)
        return None

    def _extract_amount_from_filename(self, filename: str) -> Optional[float]:
        match = re.search(r'(\d+\.\d{2})', filename)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        return None

    def _find_amount_from_text(self, text: str) -> Optional[float]:
        patterns = [
            r'￥\s*(\d+\.?\d*)',
            r'¥\s*(\d+\.?\d*)',
            r'价税合计[：:]\s*[￥¥]?\s*(\d+\.?\d*)',
            r'金额[：:]\s*[￥¥]?\s*(\d+\.?\d*)',
            r'实付[：:]\s*[￥¥]?\s*(\d+\.?\d*)',
            r'票价[：:]\s*[￥¥]?\s*(\d+\.?\d*)',
            r'票款[：:]\s*(\d+\.?\d*)',
            r'运费[：:]\s*(\d+\.?\d*)',
            r'保费[：:]\s*(\d+\.?\d*)',
        ]

        amounts = []
        for pattern in patterns:
            amounts += re.findall(pattern, text)

        valid_amounts = []
        for a in amounts:
            try:
                clean_a = a.replace(',', '').strip()
                val = float(clean_a)
                if 1 <= val <= 100000:
                    valid_amounts.append(val)
            except:
                pass

        if valid_amounts:
            return max(valid_amounts)

        simpler = re.findall(r'(\d+\.\d{2})', text)
        for s in simpler:
            try:
                val = float(s)
                if 1 <= val <= 100000:
                    valid_amounts.append(val)
            except:
                pass

        if valid_amounts:
            return max(valid_amounts)
        return None

    def _find_date_from_text(self, text: str) -> Optional[str]:
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

    def _generate_new_filename(self, info: InvoiceInfo) -> str:
        ext = ".pdf"
        if info.type == InvoiceType.TRAIN:
            refund_tag = "_退票" if info.is_refund else ""
            return f"火车票_{info.date}_{info.from_station}_到_{info.to_station}_{info.amount}{refund_tag}{ext}"
        elif info.type == InvoiceType.DIDI:
            return f"滴滴_{info.date}_{info.amount}{ext}"
        elif info.type == InvoiceType.DIDI_REIMBURSE:
            return f"滴滴行程报销单_{info.date}_{info.amount}{ext}"
        elif info.type == InvoiceType.RESTAURANT:
            merchant = info.merchant or "未知"
            return f"餐饮_{merchant[:10]}_{info.amount}_{info.date}{ext}"
        elif info.type == InvoiceType.TOLL:
            return f"通行发票_{info.date}_{info.amount}{ext}"
        elif info.type == InvoiceType.PHONE_BILL:
            provider = info.phone_provider or "话费"
            return f"{provider}发票_{info.date}_{info.amount}{ext}"
        elif info.type == InvoiceType.FLIGHT_ITINERARY:
            return f"机票行程单_{info.date}_{info.amount}{ext}"
        elif info.type == InvoiceType.HOTEL:
            hotel = info.hotel_name or "酒店"
            return f"酒店_{hotel[:10]}_{info.date}_{info.amount}{ext}"
        elif info.type == InvoiceType.EXPRESS:
            company = info.express_company or "快递"
            return f"{company}发票_{info.date}_{info.amount}{ext}"
        else:
            date_str = info.date or "未知日期"
            amount_str = str(info.amount) if info.amount else "未知金额"
            return f"{info.type}_{date_str}_{amount_str}{ext}"

    def recognize_directory(self, input_dir: str, output_dir: str = None) -> List[InvoiceInfo]:
        self.results = []

        if not os.path.exists(input_dir):
            return self.results

        for root, dirs, files in os.walk(input_dir):
            if "staging" in root or "processed" in root:
                continue

            for filename in files:
                if not filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    continue

                filepath = os.path.join(root, filename)
                try:
                    info = self.recognize_file(filepath)
                    self.results.append(info)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

        return self.results

    def get_by_type(self, invoice_type: str) -> List[InvoiceInfo]:
        return [r for r in self.results if r.type == invoice_type]

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        stats = {}
        for info in self.results:
            if info.type not in stats:
                stats[info.type] = {"count": 0, "amount": 0.0}
            stats[info.type]["count"] += 1
            if info.amount:
                stats[info.type]["amount"] += info.amount
        return stats
