"""stigma_reputation_lookup — tra cứu tin đồn/dư luận tiêu cực, yếu tố tâm linh.

Tool spec: SHB_ThamDinhBDS_DesignDoc_2.md §8.
Input : address
Output: envelope (data-model.md §5) với
        ``data = {rumors: [{detail, year, confidence, verified: false}]}``.
Nguồn: ``mockdata/address_profiles.json`` -> field ``stigma_factors``.

RÀNG BUỘC CỨNG (Nguyên tắc III — Stigma Data Isolation):
- ``verified`` của MỌI rumor LUÔN bị ép ``False``, bất kể mock data ghi gì.
- ``source_type`` giữ "mock", confidence thấp; dữ liệu này chỉ để tạo flag
  cảnh báo xác minh thực địa, KHÔNG phải căn cứ từ chối tín dụng.
"""

from __future__ import annotations

import re
from typing import Optional

from ._mockdata_utils import envelope, find_address_id, load_mock

TOOL_NAME = "stigma_reputation_lookup"


def stigma_reputation_lookup(address: Optional[str] = None) -> dict:
    """Tra cứu hồ sơ dư luận/tin đồn của địa chỉ.

    - Địa chỉ có hồ sơ, có tin đồn -> ``status="ok"``, mỗi rumor ``verified=False``.
    - Địa chỉ có hồ sơ, không tin đồn -> ``status="ok"``, ``rumors=[]``.
    - Không tìm thấy hồ sơ -> ``status="partial"``, ``rumors=[]``.
    """
    profiles = load_mock("address_profiles.json").get("profiles", [])
    address_id = find_address_id(address=address)
    profile = None
    if address_id:
        profile = next((p for p in profiles if p.get("address_id") == address_id), None)

    if profile is None:
        return envelope(
            TOOL_NAME, "partial", 0.2, {"rumors": []},
            warning=(
                "Không tìm thấy hồ sơ dư luận cho địa chỉ đã cho — "
                "chưa có dữ liệu tin đồn, cần khảo sát thực địa nếu nghi ngờ."
            ),
        )

    rumors = []
    for factor in profile.get("stigma_factors", []):
        rumors.append(
            {
                "type": factor.get("type"),
                "detail": factor.get("detail"),
                "year": _extract_year(factor.get("detail", "")),
                "confidence": factor.get("confidence", 0.3),
                # RÀNG BUỘC CỨNG: luôn False, không đọc từ mock data.
                "verified": False,
            }
        )

    if not rumors:
        # Không có tin đồn là kết quả hợp lệ, đầy đủ.
        return envelope(TOOL_NAME, "ok", 0.6, {"rumors": []},
                        warning="Không ghi nhận tin đồn/yếu tố tâm linh cho địa chỉ này.")

    # Confidence thấp có chủ đích (Nguyên tắc III) — trung bình confidence tin đồn.
    conf = sum(r["confidence"] for r in rumors) / len(rumors)
    return envelope(
        TOOL_NAME, "ok", conf, {"rumors": rumors},
        warning=(
            "Dữ liệu tin đồn/dư luận CHƯA được xác minh (verified=false) — chỉ dùng "
            "để tạo cảnh báo xác minh thực địa, không phải căn cứ từ chối tín dụng."
        ),
    )


def _extract_year(text: str) -> Optional[int]:
    """Trích năm (19xx/20xx) đầu tiên trong chuỗi mô tả tin đồn."""
    m = re.search(r"\b(19|20)\d{2}\b", text or "")
    return int(m.group(0)) if m else None
