"""``amenities`` adapter — trường/chợ/bus/bệnh viện quanh khu."""

from __future__ import annotations

from shb.capabilities.lookup.base import LookupAdapter
from shb.db.models_paa import LookupCategory


class AmenitiesAdapter(LookupAdapter):
    """Đọc ``lookup_finding`` category='neighborhood_amenity' cho 1 case."""

    key = "amenities"
    label = "Tiện ích xung quanh"
    category = LookupCategory.NEIGHBORHOOD_AMENITY
