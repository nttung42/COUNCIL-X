"""Capability building blocks (L4) — reusable SQL-backed "tools" agent graph
nodes call, per docs/ARCHITECTURE.md §6: lookup adapters, valuation/risk
read-queries, dashboard aggregates. Framework-agnostic (plain async functions
over an ``AsyncSession``) so they can be wrapped as LangChain/LangGraph tools,
called directly from FastAPI endpoints, or unit-tested in isolation.
"""
