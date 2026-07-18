"""planning_zoning_lookup — tra cứu quy hoạch, lộ giới, quy hoạch treo.

Tool spec: SHB_ThamDinhBDS_DesignDoc_2.md §8.
Input : address, cadastral_id
Output: envelope (data-model.md §5) với
        ``data = {zoning_status, is_planned_overlay, road_widening_plan}``.
Nguồn: ``mockdata/zoning.json`` (join theo ``cadastral_id`` nếu có, hoặc theo
``address_id`` suy ra từ ``address``).
"""

from __future__ import annotations

from typing import Optional

from ._mockdata_utils import envelope, find_address_id, load_mock

TOOL_NAME = "planning_zoning_lookup"


def planning_zoning_lookup(
    address: Optional[str] = None,
    cadastral_id: Optional[str] = None,
) -> dict:
    """Tra cứu tình trạng quy hoạch của thửa đất.

    Không tìm thấy -> ``status="partial"`` với payload trung tính (không raise).
    """
    records = load_mock("zoning.json").get("zoning_records", [])

    record = None
    if cadastral_id:
        record = next((r for r in records if r.get("cadastral_id") == cadastral_id), None)
    if record is None:
        address_id = find_address_id(address=address)
        if address_id:
            record = next((r for r in records if r.get("address_id") == address_id), None)

    if record is None:
        return envelope(
            TOOL_NAME, "partial", 0.25,
            {"zoning_status": None, "is_planned_overlay": False, "road_widening_plan": None},
            warning=(
                "Không tìm thấy hồ sơ quy hoạch cho địa chỉ/mã thửa đã cho — "
                "cần thẩm định viên tra cứu cổng thông tin quy hoạch địa phương."
            ),
        )

    data = {
        "zoning_status": record.get("zoning_status"),
        "is_planned_overlay": bool(record.get("is_planned_overlay", False)),
        "road_widening_plan": record.get("road_widening_plan"),
    }
    return envelope(TOOL_NAME, "ok", record.get("confidence", 0.8), data)
