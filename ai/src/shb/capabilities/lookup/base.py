"""Lookup Adapter framework — SQL-backed "tools" the PAA agent graph fans out to
for the 7 Research Agent findings (Màn 2 — Kết quả tra cứu). Makes concrete the
``LookupAdapter`` Protocol sketched in docs/ARCHITECTURE.md §6.1 against the
PAA schema's ``lookup_finding`` / ``market_comparable`` tables.

Each adapter reads pre-populated data (seeded via ``gen_seed_data.py`` for
demo cases, or written by a real research pipeline later — the interface does
not change, per the architecture doc's "cắm data thật" note). Nothing here
calls an LLM; these are pure data-access tools.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.db.models_paa import LookupCategory, LookupFinding


def _num(value: Decimal | float | None) -> float | None:
    """Convert a Decimal (Numeric column) to float for JSON-friendly tool output."""
    if value is None:
        return None
    return float(value) if isinstance(value, Decimal) else value


class AdapterResult(BaseModel):
    """Return shape of a single lookup adapter call — matches ARCHITECTURE.md §6.1
    ``AdapterResult`` (``data``, ``confidence``, ``source``, ``verified``), plus
    ``status_badge`` to drive the mockup's 3-color badge directly.
    """

    adapter_key: str
    data: dict
    confidence: float = Field(ge=0.0, le=1.0)
    source: str | None = None
    verified: bool = False
    status_badge: str | None = None  # 'da_xac_thuc' | 'luu_y' | 'chua_xac_thuc'


class LookupAdapter:
    """Base class for one of the 7 PAA lookup adapters.

    Subclasses set ``key`` / ``label`` / ``category``. The default
    :meth:`lookup` reads the single matching row from ``lookup_finding``
    (``UNIQUE(case_id, category)`` — see ``models_paa.LookupFinding``).
    Subclasses that need extra tables (``comparable_sales`` also reads
    ``market_comparable``) override :meth:`lookup` and reuse
    :meth:`_load_finding` / :meth:`_to_result` for the common part.
    """

    key: str
    label: str
    category: LookupCategory

    async def _load_finding(self, case_id: str, session: AsyncSession) -> LookupFinding | None:
        stmt = select(LookupFinding).where(
            LookupFinding.case_id == case_id, LookupFinding.category == self.category
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    def _to_result(self, finding: LookupFinding | None) -> AdapterResult:
        if finding is None:
            # No research data yet for this case/category — unverified, zero confidence.
            return AdapterResult(
                adapter_key=self.key,
                data={"raw_findings": [], "inference": None},
                confidence=0.0,
                source=None,
                verified=False,
                status_badge="chua_xac_thuc",
            )
        return AdapterResult(
            adapter_key=self.key,
            data={
                "title": finding.title,
                "raw_findings": list(finding.raw_findings or []),
                "inference": finding.inference_text,
            },
            confidence=(finding.confidence_pct or 0) / 100.0,
            source=finding.source_label,
            verified=finding.status_badge.value == "da_xac_thuc",
            status_badge=finding.status_badge.value,
        )

    async def lookup(self, case_id: str, session: AsyncSession) -> AdapterResult:
        """Fetch this adapter's finding for one case. Override for extra tables."""
        finding = await self._load_finding(case_id, session)
        return self._to_result(finding)


class AdapterRegistry:
    """Registry of lookup adapters — analogous to ``AIServiceRegistry``
    (``shb.ai.plugins.registry``) but for lookup adapters, per
    docs/ARCHITECTURE.md §6.1's "Adapter cũng đăng ký qua một AdapterRegistry".
    """

    def __init__(self) -> None:
        self._adapters: dict[str, LookupAdapter] = {}

    def register(self, adapter: LookupAdapter) -> None:
        """Register an adapter instance. Raises if ``adapter.key`` is already taken."""
        if adapter.key in self._adapters:
            raise ValueError(f"Lookup adapter '{adapter.key}' already registered")
        self._adapters[adapter.key] = adapter

    def get(self, key: str) -> LookupAdapter | None:
        """Get one adapter by key (e.g. ``'reputation'``)."""
        return self._adapters.get(key)

    def list_adapters(self) -> list[LookupAdapter]:
        """List all registered adapters (for the ``adapter_keys`` catalog)."""
        return list(self._adapters.values())

    async def run_all(self, case_id: str, session: AsyncSession) -> list[AdapterResult]:
        """Fan out all 7 adapters concurrently for one case.

        Matches the "fan-out song song" lookup node in the PAA graph
        (docs/ARCHITECTURE.md §5.2) — this is the function that node calls.
        """
        return list(
            await asyncio.gather(
                *(adapter.lookup(case_id, session) for adapter in self._adapters.values())
            )
        )
