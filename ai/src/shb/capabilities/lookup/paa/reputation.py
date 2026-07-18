"""``reputation`` adapter — dư luận/tâm linh. Confidence luôn thấp theo thiết kế
(docs/ARCHITECTURE.md §6.1: "conf thấp, chỉ cảnh báo") — never used to reject
a case, only surfaced as a flag for human review.
"""

from __future__ import annotations

from shb.capabilities.lookup.base import LookupAdapter
from shb.db.models_paa import LookupCategory


class ReputationAdapter(LookupAdapter):
    """Đọc ``lookup_finding`` category='stigma_reputation' cho 1 case."""

    key = "reputation"
    label = "Danh tiếng / tâm linh"
    category = LookupCategory.STIGMA_REPUTATION
