"""property_risk plugin — Rủi ro tài sản (Màn 4).

Given a ``case_id``, scores the 5 weighted asset-risk groups (pháp lý, thanh
khoản, biến động giá, vật lý-môi trường, danh tiếng) from Màn 1+2+3 via
``shb.capabilities.risk.engine``, producing the asset risk score, the proposed
LTV (from the policy bands), and the flags. 100% deterministic (no LLM) — the
score drives the LTV decision. Async → streams progress over SSE.
"""
