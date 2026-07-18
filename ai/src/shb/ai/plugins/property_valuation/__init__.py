"""property_valuation plugin — Định giá (Màn 3).

Given a ``case_id``, computes a transparent valuation (3 methods + weighted blend
+ 5-factor confidence) from the Màn 1 subject and Màn 2 comparables via
``shb.capabilities.valuation.engine``. The only subjective input is a bounded
(±5%) LLM adjustment for hướng nhà/phong thủy, kept separate for audit. Async →
streams progress over SSE.
"""
