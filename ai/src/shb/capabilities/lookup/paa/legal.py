"""``legal`` adapter — tình trạng sổ, tranh chấp, thế chấp (conf ~0.95 theo thiết kế)."""

from __future__ import annotations

from shb.capabilities.lookup.base import LookupAdapter
from shb.db.models_paa import LookupCategory


class LegalAdapter(LookupAdapter):
    """Đọc ``lookup_finding`` category='legal_status' cho 1 case."""

    key = "legal"
    label = "Pháp lý"
    category = LookupCategory.LEGAL_STATUS
