"""environmental_risk_lookup — tra cứu rủi ro ngập úng, sạt lở, ô nhiễm.

Tool spec: SHB_ThamDinhBDS_DesignDoc_2.md §8.
Input : lat, long
Output: envelope (data-model.md §5) với
        ``data = {flood_risk, landslide_risk, pollution_risk, notes}``.
Nguồn: ``mockdata/environmental_risk.json`` (join theo ``address_id`` là điểm
gần nhất với (lat, long) trong ``address_profiles.json``).
"""

from __future__ import annotations

from typing import Optional

from ._mockdata_utils import envelope, find_address_id, load_mock

TOOL_NAME = "environmental_risk_lookup"


def environmental_risk_lookup(
    lat: Optional[float] = None,
    long: Optional[float] = None,
) -> dict:
    """Tra cứu rủi ro môi trường quanh 1 toạ độ.

    - Thiếu ``lat``/``long`` -> ``status="error"``.
    - Không có bản ghi gần toạ độ -> ``status="partial"`` payload trung tính.
    """
    if not _is_num(lat) or not _is_num(long):
        return envelope(
            TOOL_NAME, "error", 0.0,
            _neutral(),
            warning="Thiếu toạ độ lat/long — không thể tra cứu rủi ro môi trường theo khu vực.",
        )

    records = load_mock("environmental_risk.json").get("environmental_records", [])
    address_id = find_address_id(lat=lat, long=long)
    record = None
    if address_id:
        record = next((r for r in records if r.get("address_id") == address_id), None)

    if record is None:
        return envelope(
            TOOL_NAME, "partial", 0.25, _neutral(),
            warning=(
                f"Không tìm thấy dữ liệu rủi ro môi trường gần toạ độ ({lat}, {long}) "
                "— cần thẩm định viên đối chiếu dữ liệu khí tượng thuỷ văn/cảnh báo thiên tai."
            ),
        )

    data = {
        "flood_risk": record.get("flood_risk"),
        "landslide_risk": record.get("landslide_risk"),
        "pollution_risk": record.get("pollution_risk"),
        "notes": record.get("notes"),
    }
    return envelope(TOOL_NAME, "ok", record.get("confidence", 0.75), data)


def _neutral() -> dict:
    return {
        "flood_risk": "unknown",
        "landslide_risk": "unknown",
        "pollution_risk": "unknown",
        "notes": None,
    }


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)
