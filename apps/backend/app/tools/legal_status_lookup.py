"""legal_status_lookup — tra cứu tình trạng pháp lý, tranh chấp, thế chấp.

Tool spec: SHB_ThamDinhBDS_DesignDoc_2.md §8.
Input : address, owner_id
Output: envelope (data-model.md §5) với
        ``data = {legal_status, has_dispute, mortgaged_elsewhere, notes}``.
Nguồn: ``mockdata/legal_records.json`` (join theo ``address_id`` suy ra từ
``address``). ``owner_id`` được nhận theo tool spec nhưng mock data không có
khoá owner_id để join — chỉ dùng address_id; xem ghi chú trong báo cáo.
"""

from __future__ import annotations

from typing import Optional

from ._mockdata_utils import envelope, find_address_id, load_mock

TOOL_NAME = "legal_status_lookup"


def legal_status_lookup(
    address: Optional[str] = None,
    owner_id: Optional[str] = None,
) -> dict:
    """Tra cứu tình trạng pháp lý của tài sản.

    Không tìm thấy -> ``status="partial"`` với payload trung tính (không raise).
    """
    records = load_mock("legal_records.json").get("legal_records", [])

    address_id = find_address_id(address=address)
    record = None
    if address_id:
        record = next((r for r in records if r.get("address_id") == address_id), None)

    if record is None:
        return envelope(
            TOOL_NAME, "partial", 0.25,
            {
                "legal_status": None,
                "has_dispute": False,
                "mortgaged_elsewhere": False,
                "notes": None,
            },
            warning=(
                "Không tìm thấy hồ sơ pháp lý cho địa chỉ đã cho — cần thẩm định "
                "viên đối chiếu văn phòng đăng ký đất đai/CIC."
            ),
        )

    data = {
        "legal_status": record.get("legal_status"),
        "has_dispute": bool(record.get("has_dispute", False)),
        "mortgaged_elsewhere": bool(record.get("mortgaged_elsewhere", False)),
        "notes": record.get("notes"),
    }
    return envelope(TOOL_NAME, "ok", record.get("confidence", 0.85), data)
