"""PAA agents (Google ADK / async orchestration).

- ``research_agent``  : ParallelAgent (7 lookup chạy SONG SONG — SC-001).
- ``valuation_agent`` : gọi ``calculate_valuation``.
- ``risk_agent``      : gọi ``calculate_asset_risk_score``.
- ``advisory_agent``  : gọi ``query_knowledge_base`` + ``generate_report_draft``.

Xem docstring từng module + ``model.py`` cho chiến lược wiring ADK/fallback.
"""

from app.agents.advisory_agent import AdvisoryAgent, advisory_agent
from app.agents.research_agent import ResearchAgent, research_agent
from app.agents.risk_agent import RiskAgent, risk_agent
from app.agents.valuation_agent import ValuationAgent, valuation_agent

__all__ = [
    "ResearchAgent", "research_agent",
    "ValuationAgent", "valuation_agent",
    "RiskAgent", "risk_agent",
    "AdvisoryAgent", "advisory_agent",
]
