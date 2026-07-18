"""Wires the 7 PAA lookup adapters into a shared :class:`AdapterRegistry`.
Analogous to ``shb.ai.plugins.registry`` but for lookup adapters, per
docs/ARCHITECTURE.md §6.1 ("Adapter cũng đăng ký qua một AdapterRegistry").
"""

from __future__ import annotations

from functools import lru_cache

from shb.capabilities.lookup.base import AdapterRegistry
from shb.capabilities.lookup.paa.amenities import AmenitiesAdapter
from shb.capabilities.lookup.paa.comparable_sales import ComparableSalesAdapter
from shb.capabilities.lookup.paa.environment import EnvironmentAdapter
from shb.capabilities.lookup.paa.legal import LegalAdapter
from shb.capabilities.lookup.paa.liquidity import LiquidityAdapter
from shb.capabilities.lookup.paa.reputation import ReputationAdapter
from shb.capabilities.lookup.paa.zoning import ZoningAdapter

_ADAPTER_CLASSES = (
    ComparableSalesAdapter,
    ZoningAdapter,
    LegalAdapter,
    AmenitiesAdapter,
    EnvironmentAdapter,
    LiquidityAdapter,
    ReputationAdapter,
)


@lru_cache(maxsize=1)
def get_lookup_registry() -> AdapterRegistry:
    """Get the global PAA lookup adapter registry (built once, cached).

    Usage in a LangGraph lookup node::

        registry = get_lookup_registry()
        results = await registry.run_all(case_id, session)  # fan-out, 7 adapters
    """
    registry = AdapterRegistry()
    for adapter_cls in _ADAPTER_CLASSES:
        registry.register(adapter_cls())
    return registry
