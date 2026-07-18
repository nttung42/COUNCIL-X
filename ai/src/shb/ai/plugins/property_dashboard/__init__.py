"""property_dashboard plugin — Dashboard tổng hợp (Màn 5).

Given a ``case_id``, aggregates Màn 1–4 into the sign-off dashboard: the KPI
tiles, a deterministic lending verdict + max loan (``shb.capabilities.dashboard.synthesis``),
the 4 "Tổng hợp theo từng bước" summaries (LLM-worded via the narrator, fail-safe
to templates), the agent trace timeline and the case-history sidebar. Numbers and
the decision are 100% deterministic — the LLM only rewords prose. Async → SSE.
"""
