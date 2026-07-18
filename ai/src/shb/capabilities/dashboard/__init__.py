"""SQL-backed read tools for the Dashboard screen. Reimplements the two
convenience views from ``PAA_Schema_PostgreSQL.sql`` (``v_case_history``,
``v_dashboard_kpi``) as plain parametrized queries — portable to SQLite
(tests) and directly callable as agent/report tools without a DB view object.
"""
