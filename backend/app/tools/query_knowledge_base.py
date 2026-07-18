"""query_knowledge_base — RAG similarity search trên bảng KbChunk.

Luôn trả `source_doc` cho MỌI kết quả để làm citation (FR-010, Nguyên tắc II) —
không bao giờ trả câu trả lời không có nguồn.

Chữ ký hàm GIỮ ỔN ĐỊNH cho agent Orchestrator & API import.
"""

from __future__ import annotations

from typing import Optional


def query_knowledge_base(
    query: str,
    property_type: Optional[str] = None,
    top_k: int = 3,
) -> list[dict]:
    """Tìm top-K chunk gần nhất với `query` trong knowledge base.

    Args:
        query: câu hỏi/nội dung cần tra cứu.
        property_type: nếu truyền (`nha_pho`/`dat_nen`/`chung_cu`/`bds_thuong_mai`),
            ưu tiên chunk khớp property_type đó HOẶC tài liệu áp dụng-mọi-loại
            (`property_type='all'`, hoặc doc_type `quy_trinh`/`quy_dinh`).
        top_k: số kết quả trả về.

    Returns:
        Danh sách dict, mỗi phần tử:
        ``{"source_doc", "chunk_text", "score", "doc_type", "property_type"}``.
        `source_doc` LUÔN có mặt (citation). Danh sách rỗng nếu KB chưa ingest.

    Raises:
        RuntimeError: khi embedding endpoint/DB chưa cấu hình được (bọc lỗi rõ ràng).
    """
    # Import "nặng" trong hàm để giữ module import được khi chưa có SDK/DB.
    from sqlalchemy import or_, select

    from app.db.session import SessionLocal
    from app.models.kb_chunk import KbChunk
    from app.rag.embedder import embed_text

    query_embedding = embed_text(query)

    try:
        with SessionLocal() as session:
            distance = KbChunk.embedding.cosine_distance(query_embedding).label(
                "distance"
            )
            stmt = select(KbChunk, distance)

            if property_type:
                pt = KbChunk.metadata_json["property_type"].astext
                dt = KbChunk.metadata_json["doc_type"].astext
                stmt = stmt.where(
                    or_(
                        pt == property_type,
                        pt == "all",
                        dt.in_(["quy_trinh", "quy_dinh"]),
                    )
                )

            stmt = stmt.order_by(distance).limit(top_k)

            results: list[dict] = []
            for chunk, dist in session.execute(stmt).all():
                meta = chunk.metadata_json or {}
                results.append(
                    {
                        "source_doc": chunk.source_doc,  # citation bắt buộc
                        "chunk_text": chunk.chunk_text,
                        # cosine_distance ∈ [0,2]; score ∈ [-1,1], càng cao càng gần.
                        "score": round(1.0 - float(dist), 4),
                        "doc_type": meta.get("doc_type"),
                        "property_type": meta.get("property_type"),
                    }
                )
            return results
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "query_knowledge_base thất bại khi truy vấn pgvector. Đảm bảo đã chạy "
            f"`python -m app.rag.ingest` và Postgres/pgvector đang chạy. Chi tiết: {exc}"
        ) from exc
