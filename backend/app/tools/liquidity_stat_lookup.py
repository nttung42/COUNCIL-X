"""liquidity_stat_lookup — tra cứu thống kê thanh khoản khu vực.

Một trong 7 lookup tool của PAA Research Agent (data-model.md §5). (Tool này
không nằm trong danh sách YAML §8 design doc nhưng là 1 trong 7 nguồn tra cứu
song song — xem sơ đồ §Research Agent design doc.)

Input : address hoặc ward, property_type
Output: envelope (data-model.md §5) với
        ``data = {avg_days_on_market, success_rate_pct}``.
Nguồn: ``mockdata/liquidity_stats.json`` (join theo ``ward`` + ``property_segment``).
Nếu chỉ có ``address``, ward được suy ra bằng ``ward_from_address``.
"""

from __future__ import annotations

from typing import Optional

from ._mockdata_utils import envelope, load_mock, ward_from_address

TOOL_NAME = "liquidity_stat_lookup"


def liquidity_stat_lookup(
    address: Optional[str] = None,
    ward: Optional[str] = None,
    property_type: str = "nha_pho",
) -> dict:
    """Tra cứu thời gian bán trung bình & tỷ lệ giao dịch thành công khu vực.

    ``ward`` ưu tiên nếu truyền; nếu không, suy từ ``address``.
    ``property_type`` mặc định ``"nha_pho"`` (loại tài sản ưu tiên của MVP).
    Không tìm thấy -> ``status="partial"`` payload trung tính (null).
    """
    resolved_ward = ward or ward_from_address(address)

    if not resolved_ward:
        return envelope(
            TOOL_NAME, "partial", 0.2,
            {"avg_days_on_market": None, "success_rate_pct": None},
            warning=(
                "Không xác định được phường/quận từ input — không thể tra cứu thống kê "
                "thanh khoản. Cần cung cấp 'ward' hoặc địa chỉ có 'Phường ..., Quận ...'."
            ),
        )

    records = load_mock("liquidity_stats.json").get("liquidity_records", [])
    record = next(
        (
            r for r in records
            if r.get("ward") == resolved_ward and r.get("property_segment") == property_type
        ),
        None,
    )

    if record is None:
        return envelope(
            TOOL_NAME, "partial", 0.25,
            {"avg_days_on_market": None, "success_rate_pct": None},
            warning=(
                f"Không có thống kê thanh khoản cho '{resolved_ward}' / loại "
                f"'{property_type}' — cần thẩm định viên tham chiếu dữ liệu sàn giao dịch."
            ),
        )

    data = {
        "avg_days_on_market": record.get("avg_days_on_market"),
        "success_rate_pct": record.get("success_rate_pct"),
    }
    return envelope(TOOL_NAME, "ok", record.get("confidence", 0.8), data)
