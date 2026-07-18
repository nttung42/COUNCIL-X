"""``environment`` adapter — ngập lụt, ô nhiễm; ảnh hưởng nhóm rủi ro vật lý-môi trường."""

from __future__ import annotations

from shb.capabilities.lookup.base import LookupAdapter
from shb.db.models_paa import LookupCategory


class EnvironmentAdapter(LookupAdapter):
    """Đọc ``lookup_finding`` category='environmental_risk' cho 1 case."""

    key = "environment"
    label = "Môi trường"
    category = LookupCategory.ENVIRONMENTAL_RISK
