---
name: paa-advisory-rag-impl
description: "Cách implement RAG pipeline (embedder, ingest, query_knowledge_base) và generate_report_draft của PAA — chunking strategy, cấu trúc bảng pgvector, template biên bản thẩm định. Dùng khi viết code cho backend/app/rag/*.py và backend/app/tools/{query_knowledge_base,generate_report_draft}.py."
---

# Implement PAA RAG & Advisory Tooling

## embedder.py

```python
from openai import OpenAI
from app.config import settings  # đã có sẵn từ Foundational phase

client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

def embed_text(text: str) -> list[float]:
    resp = client.embeddings.create(model=settings.embedding_model, input=text)
    return resp.data[0].embedding
```

Không hardcode `base_url`/`api_key`/model — luôn qua `settings` (Nguyên tắc constitution về
tech stack). Nếu `settings.embedding_model` chưa set trong `.env.example`, thêm dòng
`EMBEDDING_MODEL=text-embedding-3-small` (hoặc placeholder tương đương) vào `.env.example` — không
sửa các dòng khác đã có.

## ingest.py — chunking strategy

- Đọc từng file `backend/app/mockdata/kb_documents/*.md`, parse frontmatter YAML (`doc_type`,
  `property_type`, `title`) bằng `python-frontmatter` hoặc parser thủ công đơn giản (split theo
  `---`).
- Chunk theo heading `##` (mỗi heading + nội dung dưới nó là 1 chunk) — với 6 tài liệu hiện có,
  chunk theo heading là đủ, không cần sliding window phức tạp.
- Với mỗi chunk: gọi `embed_text`, lưu vào bảng `KbChunk` (`source_doc`, `chunk_text`, `embedding`,
  `metadata_json={"doc_type":..., "property_type":...}`).
- Script chạy 1 lần (`python -m app.rag.ingest`), idempotent — nếu chạy lại, xoá chunk cũ của cùng
  `source_doc` trước khi insert lại (tránh trùng lặp khi demo chạy nhiều lần).

## query_knowledge_base.py

```python
def query_knowledge_base(query: str, property_type: str | None = None, top_k: int = 3) -> list[dict]:
    """Trả về [{source_doc, chunk_text, score}], luôn kèm source_doc để làm citation (FR-010)."""
```

- Tính embedding của `query`, dùng pgvector `<->` (cosine/L2 distance) để lấy top-K chunk gần nhất.
- Nếu `property_type` được truyền: ưu tiên lọc `metadata_json->>'property_type'` khớp hoặc
  `doc_type='quy_trinh'`/`'quy_dinh'` (áp dụng mọi loại tài sản) trước khi tính khoảng cách.
- Luôn trả `source_doc` (tên file) trong mỗi kết quả — Advisory Agent/Chat endpoint dùng field này
  làm citation hiển thị cho thẩm định viên.

## generate_report_draft.py — template biên bản

Sinh `AppraisalReportDraft` (data-model.md §9) với 3 section markdown:

```python
sections = {
  "property_info": f"**Địa chỉ**: {subject_property.address}\n**Diện tích**: {subject_property.area_m2} m²\n**Pháp lý khai báo**: {subject_property.legal_status_claimed}",
  "valuation": f"Giá trị đề xuất: {valuation_result.estimated_value:,} VNĐ ({valuation_result.value_range.low:,}–{valuation_result.value_range.high:,}), độ tin cậy {valuation_result.confidence_score:.0%}.",
  "risk_and_ltv": f"Điểm rủi ro tài sản: {risk_result.asset_risk_score}/100 ({risk_result.risk_tier}). LTV đề xuất: {risk_result.recommended_ltv_cap:.0%}.",
}
signature_block = "☐ Chữ ký thẩm định viên    ☐ Xác nhận chuyên viên tín dụng"
```

Dùng `kb_checklist` (kết quả từ `query_knowledge_base` với checklist theo `property_type`) để chèn
thêm các mục cần xác minh vào cuối `risk_and_ltv` nếu có flag rủi ro — KHÔNG được tự thêm nội dung
kết luận "đã duyệt"/"từ chối" vào bất kỳ section nào (Nguyên tắc I — đây luôn là bản nháp chờ người
ký).
