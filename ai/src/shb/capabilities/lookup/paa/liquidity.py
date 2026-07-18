"""``liquidity`` adapter — ngày bán trung bình, tỷ lệ thành công; ảnh hưởng rủi ro thanh khoản."""

from __future__ import annotations

from shb.capabilities.lookup.base import LookupAdapter
from shb.db.models_paa import LookupCategory


class LiquidityAdapter(LookupAdapter):
    """Đọc ``lookup_finding`` category='liquidity_stat' cho 1 case."""

    key = "liquidity"
    label = "Thanh khoản"
    category = LookupCategory.LIQUIDITY_STAT
