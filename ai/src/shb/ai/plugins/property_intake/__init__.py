"""property_intake plugin — extract & auto-fill "Nhập thông tin" (Màn 1).

Uploads (PDF text/scan, DOCX) are parsed, classified, and field-extracted into a
form-ready structure with per-field grounding (source + confidence + status),
mirroring the PAA mockup's "Nhập thông tin" tab.

Pipeline (PR2–PR4): ingest -> extract -> verify -> merge -> validate -> assemble.

* An LLM classifier routes each document to one of four text extractors — Sổ
  đỏ/hồng (GCN), Tờ khai LPTB, Biên bản bàn giao, Thông báo thuế đất — each with
  its own schema/prompt (PR3).
* Group-A guarantees: mandatory grounding, null-instead-of-guess, verbatim value
  + typed code normalizers (PR3).
* An LLM-judge **verifier** re-checks each value against its evidence (#5), a
  **merge** step reconciles across documents by source priority and flags
  conflicts as ``mau_thuan``, **validators** run rule/arithmetic cross-checks
  (feature 4), and **confidence tiering** decides the final cell status (#9) —
  all PR4.

Later PRs add vision OCR for scans and DB persistence.
"""
