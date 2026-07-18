"""property_intake plugin — extract & auto-fill "Nhập thông tin" (Màn 1).

Uploads (PDF text/scan, DOCX) are parsed, classified, and field-extracted into a
form-ready structure with per-field grounding (source + confidence + status),
mirroring the PAA mockup's "Nhập thông tin" tab.

PR2 scope: end-to-end skeleton for the Sổ đỏ / Sổ hồng (GCN) document type over
text-based PDFs. Later PRs add the other document types, vision OCR for scans,
cross-document reconciliation, and DB persistence.
"""
