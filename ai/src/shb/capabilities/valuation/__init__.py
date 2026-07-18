"""SQL-backed read tools for the Định giá (valuation) screen / Valuation Engine
(docs/ARCHITECTURE.md §6.2). Plain async functions over an ``AsyncSession`` —
call directly from a graph node, or wrap as a LangChain ``@tool``.
"""
