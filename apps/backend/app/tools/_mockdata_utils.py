"""Tiện ích dùng chung cho 7 lookup adapter của PAA Research Agent.

Gom các thao tác lặp lại giữa các tool:
- Nạp (và cache) các file JSON mock trong ``backend/app/mockdata``.
- Dựng ``Lookup Tool Output Envelope`` chuẩn (data-model.md §5).
- So khớp ``address`` / toạ độ đầu vào -> ``address_id`` trong mock data
  (``_find_address_id``) — dùng chung cho 5 tool join theo ``address_id``
  (zoning / legal / amenity / stigma / environmental).
- Trích ``ward`` từ chuỗi địa chỉ, tính khoảng cách Haversine, quy đổi
  ngày giao dịch -> kỳ quý (``YYYY-Qn``) cho ``market_price_lookup``.

Toàn bộ dữ liệu là MOCK (Nguyên tắc VI). ``source_type`` luôn là ``"mock"``.
"""

from __future__ import annotations

import json
import math
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

# backend/app/mockdata (module này nằm trong backend/app/tools)
MOCKDATA_DIR = Path(__file__).resolve().parent.parent / "mockdata"

SOURCE_TYPE_MOCK = "mock"

# Bán kính mặc định (km) khi caller không truyền radius_km. Chọn 2km — đủ bao
# các giao dịch/POI quanh khu vực flagship trong mock data (README §Khu vực mẫu).
DEFAULT_RADIUS_KM = 2.0

# Ngưỡng similarity tối thiểu để coi 2 chuỗi địa chỉ là cùng 1 địa chỉ.
# Chọn 0.78: đủ cao để loại địa chỉ lạ (phần đuôi ", Phường ..., Quận ..." chung
# khiến ratio nền ~0.67), vẫn nhận biến thể bỏ dấu của địa chỉ thật (~0.84) và
# khớp tuyệt đối (1.0). Địa chỉ không có trong mock -> None -> tool trả "partial".
_ADDRESS_MATCH_THRESHOLD = 0.78
# Khoảng cách tối đa (km) để coi 1 toạ độ khớp với 1 address_id.
_COORD_MATCH_MAX_KM = 3.0


# --------------------------------------------------------------------------- #
# Nạp mock data (có cache)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def load_mock(filename: str) -> dict:
    """Đọc 1 file JSON trong thư mục mockdata, cache theo tên file.

    Trả về ``{}`` nếu file thiếu/không parse được, để tool tự xử lý thành
    ``status="partial"`` thay vì raise và làm sập pipeline (Nguyên tắc IV).
    """
    path = MOCKDATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


# --------------------------------------------------------------------------- #
# Envelope chuẩn (data-model.md §5)
# --------------------------------------------------------------------------- #
def envelope(
    tool_name: str,
    status: str,
    confidence: float,
    data: dict,
    warning: Optional[str] = None,
) -> dict:
    """Dựng envelope chuẩn cho mọi lookup tool.

    Fields cố định: ``tool_name``, ``status`` (ok|partial|error),
    ``confidence`` [0,1], ``source_type`` (luôn "mock" trong MVP),
    ``data`` (payload riêng), ``warning`` (str khi status != ok).
    """
    return {
        "tool_name": tool_name,
        "status": status,
        "confidence": round(_clamp01(confidence), 4),
        "source_type": SOURCE_TYPE_MOCK,
        "data": data,
        "warning": warning,
    }


def _clamp01(value: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value))


def avg_confidence(items: list, default: float = 0.3) -> float:
    """Trung bình field ``confidence`` của 1 danh sách dict; ``default`` nếu rỗng."""
    vals = [i.get("confidence") for i in items if isinstance(i, dict) and i.get("confidence") is not None]
    if not vals:
        return default
    return sum(vals) / len(vals)


# --------------------------------------------------------------------------- #
# Toạ độ & khoảng cách
# --------------------------------------------------------------------------- #
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Khoảng cách Haversine (km) giữa 2 điểm lat/long."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# --------------------------------------------------------------------------- #
# Trích ward từ địa chỉ ("... Phường B, Quận C")
# --------------------------------------------------------------------------- #
def ward_from_address(address: Optional[str]) -> Optional[str]:
    """Suy ra khoá ``ward`` (dạng "Phường X, Quận Y") từ chuỗi địa chỉ.

    Khớp với khoá trong ``price_index.json`` / ``liquidity_stats.json``.
    Trả ``None`` nếu không tách được.
    """
    if not address:
        return None
    parts = [p.strip() for p in address.split(",")]
    phuong = quan = None
    for part in parts:
        if phuong is None:
            m = re.search(r"(Phường|Phuong|P\.)\s.*", part)
            if m:
                phuong = m.group(0).strip()
        if quan is None:
            m = re.search(r"(Quận|Quan|Q\.)\s?.*", part)
            if m:
                quan = m.group(0).strip()
    if phuong and quan:
        return f"{phuong}, {quan}"
    return None


# --------------------------------------------------------------------------- #
# So khớp address / toạ độ -> address_id
# --------------------------------------------------------------------------- #
def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


@lru_cache(maxsize=None)
def _address_index() -> tuple:
    """Danh sách (address_id, address, lat, long) từ address_profiles.json.

    ``address_profiles.json`` là nguồn duy nhất có đủ address_id + toạ độ cho
    mọi địa chỉ demo, nên dùng làm bảng tra cứu chung cho helper này.
    """
    profiles = load_mock("address_profiles.json").get("profiles", [])
    rows = []
    for p in profiles:
        rows.append(
            (
                p.get("address_id"),
                p.get("address", ""),
                p.get("lat"),
                p.get("long"),
            )
        )
    return tuple(rows)


def known_address_ids() -> set:
    return {row[0] for row in _address_index() if row[0]}


def find_address_id(
    address: Optional[str] = None,
    lat: Optional[float] = None,
    long: Optional[float] = None,
) -> Optional[str]:
    """Suy ra ``address_id`` từ ``address`` (so khớp chuỗi gần đúng) hoặc từ
    toạ độ (điểm gần nhất trong ``address_profiles.json``).

    Thứ tự ưu tiên:
      1. ``address`` trùng thẳng 1 ``address_id`` đã biết (caller truyền id).
      2. So khớp chuỗi địa chỉ gần đúng (SequenceMatcher, ngưỡng 0.5) +
         ưu tiên quan hệ substring.
      3. Toạ độ gần nhất (Haversine) trong bán kính <= 3km.
    Trả ``None`` nếu không match — tool gọi sẽ set ``status="partial"``.
    """
    rows = _address_index()

    # (1) caller truyền thẳng address_id
    if address and address.strip() in known_address_ids():
        return address.strip()

    # (2) so khớp chuỗi
    if address:
        target = _normalize(address)
        best_id, best_score = None, 0.0
        for aid, addr, _lat, _long in rows:
            if not addr:
                continue
            cand = _normalize(addr)
            score = SequenceMatcher(None, target, cand).ratio()
            # thưởng cho quan hệ chứa nhau (địa chỉ con nằm trong địa chỉ mock)
            if cand in target or target in cand:
                score = max(score, 0.85)
            if score > best_score:
                best_id, best_score = aid, score
        if best_id and best_score >= _ADDRESS_MATCH_THRESHOLD:
            return best_id

    # (3) toạ độ gần nhất
    if _is_number(lat) and _is_number(long):
        best_id, best_km = None, float("inf")
        for aid, _addr, plat, plong in rows:
            if not (_is_number(plat) and _is_number(plong)):
                continue
            km = haversine_km(lat, long, plat, plong)
            if km < best_km:
                best_id, best_km = aid, km
        if best_id is not None and best_km <= _COORD_MATCH_MAX_KM:
            return best_id

    return None


# --------------------------------------------------------------------------- #
# Kỳ quý & quy đổi giá theo chỉ số (market_price_lookup)
# --------------------------------------------------------------------------- #
def period_from_date(date_str: str) -> Optional[str]:
    """``"2025-11-10"`` -> ``"2025-Q4"``. Trả ``None`` nếu parse thất bại."""
    if not date_str:
        return None
    m = re.match(r"(\d{4})-(\d{2})-\d{2}", date_str)
    if not m:
        return None
    year, month = int(m.group(1)), int(m.group(2))
    quarter = (month - 1) // 3 + 1
    return f"{year}-Q{quarter}"


def find_series(ward: Optional[str], property_segment: Optional[str]) -> Optional[dict]:
    """Tìm bản ghi PriceIndexSeries khớp ward + property_segment."""
    if not ward or not property_segment:
        return None
    for rec in load_mock("price_index.json").get("series", []):
        if rec.get("ward") == ward and rec.get("property_segment") == property_segment:
            return rec
    return None


def latest_period(series_rec: dict) -> Optional[str]:
    points = series_rec.get("series", []) if series_rec else []
    periods = [p.get("period") for p in points if p.get("period")]
    return max(periods) if periods else None  # "YYYY-Qn" sort đúng theo thứ tự


def index_at(series_rec: dict, period: str) -> Optional[float]:
    """Giá trị index tại 1 kỳ; nếu thiếu -> lấy kỳ gần nhất <= period,
    hoặc kỳ biên nếu period nằm ngoài dải."""
    points = series_rec.get("series", []) if series_rec else []
    d = {p.get("period"): p.get("index") for p in points if p.get("period")}
    if not d:
        return None
    if period in d:
        return d[period]
    ordered = sorted(d)
    if period < ordered[0]:
        return d[ordered[0]]
    if period > ordered[-1]:
        return d[ordered[-1]]
    le = [p for p in ordered if p <= period]
    return d[le[-1]] if le else d[ordered[0]]
