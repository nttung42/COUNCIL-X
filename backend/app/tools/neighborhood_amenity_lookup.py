"""neighborhood_amenity_lookup — tra cứu tiện ích/hạ tầng xung quanh.

Tool spec: SHB_ThamDinhBDS_DesignDoc_2.md §8.
Input : lat, long, radius_km
Output: envelope (data-model.md §5) với ``data = {amenities: [{type, name, distance_m}]}``.
Nguồn: ``mockdata/amenities.json`` (join theo ``address_id`` là điểm gần nhất
với (lat, long) trong ``address_profiles.json``). Lọc POI có
``distance_m <= radius_km * 1000``.
"""

from __future__ import annotations

from typing import Optional

from ._mockdata_utils import (
    DEFAULT_RADIUS_KM,
    envelope,
    find_address_id,
    load_mock,
)

TOOL_NAME = "neighborhood_amenity_lookup"


def neighborhood_amenity_lookup(
    lat: Optional[float] = None,
    long: Optional[float] = None,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> dict:
    """Tra cứu POI/tiện ích trong bán kính quanh 1 toạ độ.

    - Thiếu ``lat``/``long`` -> ``status="error"``.
    - Không có bản ghi gần toạ độ -> ``status="partial"``, ``amenities=[]``.
    """
    if not _is_num(lat) or not _is_num(long):
        return envelope(
            TOOL_NAME, "error", 0.0, {"amenities": []},
            warning="Thiếu toạ độ lat/long — không thể tra cứu tiện ích quanh khu vực.",
        )
    if not _is_num(radius_km) or radius_km <= 0:
        radius_km = DEFAULT_RADIUS_KM

    records = load_mock("amenities.json").get("amenity_records", [])
    address_id = find_address_id(lat=lat, long=long)
    record = None
    if address_id:
        record = next((r for r in records if r.get("address_id") == address_id), None)

    if record is None:
        return envelope(
            TOOL_NAME, "partial", 0.25, {"amenities": []},
            warning=(
                f"Không tìm thấy dữ liệu tiện ích gần toạ độ ({lat}, {long}) "
                "— cần thẩm định viên bổ sung khảo sát thực địa."
            ),
        )

    radius_m = radius_km * 1000.0
    amenities = [
        {"type": a.get("type"), "name": a.get("name"), "distance_m": a.get("distance_m")}
        for a in record.get("amenities", [])
        if not _is_num(a.get("distance_m")) or a.get("distance_m") <= radius_m
    ]

    warning = None
    if not amenities:
        warning = (
            f"Có hồ sơ khu vực nhưng không tiện ích nào nằm trong bán kính {radius_km}km."
        )
    status = "ok" if amenities else "partial"
    conf = record.get("confidence", 0.8) if amenities else 0.3
    return envelope(TOOL_NAME, status, conf, {"amenities": amenities}, warning=warning)


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)
