"""``zoning`` adapter — tình trạng quy hoạch, lộ giới (conf ~0.85 theo thiết kế)."""

from __future__ import annotations

from shb.capabilities.lookup.base import LookupAdapter
from shb.db.models_paa import LookupCategory


class ZoningAdapter(LookupAdapter):
    """Đọc ``lookup_finding`` category='planning_zoning' cho 1 case."""

    key = "zoning"
    label = "Quy hoạch"
    category = LookupCategory.PLANNING_ZONING
