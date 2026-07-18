"""property_lookup plugin — Kết quả tra cứu (Màn 2).

Given a ``case_id``, reads the 7 pre-populated lookup findings (giá thị trường,
quy hoạch, pháp lý, tiện ích, môi trường, thanh khoản, dư luận) + the comparable
transactions from the DB (via ``shb.capabilities.lookup``) and returns them in the
frontend's Màn 2 shape. Synchronous (DB read only) — no Celery job.
"""
