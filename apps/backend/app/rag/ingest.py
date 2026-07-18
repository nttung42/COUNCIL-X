"""Ingest kb_documents/*.md vào bảng KbChunk (Postgres + pgvector).

Chạy 1 lần: `python -m app.rag.ingest` (từ thư mục `backend/`).

Đặc điểm:
- Parse frontmatter YAML đơn giản (doc_type, property_type, title) — không cần
  thư viện ngoài.
- Chunk theo heading cấp 1–2 (`#` / `##`): mỗi heading + nội dung dưới nó = 1 chunk.
  (06-case-cu dùng `#` cho mỗi case; 01-quy-trinh dùng `##` cho mỗi bước — cả hai
  đều tách đúng thành từng chunk có ý nghĩa.)
- Idempotent: xoá chunk cũ của cùng `source_doc` trước khi insert lại.

Các hàm chunking (`parse_frontmatter`, `chunk_markdown`, `build_chunks`) là hàm
THUẦN, không đụng DB/embedding — có thể test offline để đếm số chunk.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Thư mục chứa 6 tài liệu nguồn RAG.
KB_DIR = Path(__file__).resolve().parents[1] / "mockdata" / "kb_documents"

# Heading cấp 1 hoặc 2 bắt đầu 1 chunk mới.
_HEADING_RE = re.compile(r"^(#{1,2})\s+\S", re.MULTILINE)


@dataclass
class Chunk:
    source_doc: str
    chunk_text: str
    metadata: dict = field(default_factory=dict)


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Tách frontmatter YAML (dạng `---\\n...\\n---`) khỏi body.

    Parser thủ công đủ cho frontmatter phẳng `key: value`. Nếu file thiếu
    frontmatter, trả về ({}, raw) và caller sẽ dùng default.
    """
    text = raw.lstrip("﻿")  # bỏ BOM nếu có
    if not text.startswith("---"):
        return {}, raw
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    _, front, body = parts
    meta: dict = {}
    for line in front.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("'\"")
    return meta, body.lstrip("\n")


def chunk_markdown(body: str) -> list[str]:
    """Chia body thành các chunk theo heading cấp 1–2.

    - Phần preamble (nếu có) trước heading đầu tiên được gộp vào chunk đầu.
    - Dòng phân cách `---` đơn lẻ bị loại bỏ khỏi chunk text.
    - Bỏ qua chunk rỗng.
    """
    matches = list(_HEADING_RE.finditer(body))
    if not matches:
        cleaned = _clean(body)
        return [cleaned] if cleaned else []

    chunks: list[str] = []

    # Preamble trước heading đầu tiên -> gộp vào chunk đầu.
    first_start = matches[0].start()
    preamble = _clean(body[:first_start])

    bounds = [m.start() for m in matches] + [len(body)]
    for i in range(len(matches)):
        segment = body[bounds[i] : bounds[i + 1]]
        cleaned = _clean(segment)
        if i == 0 and preamble:
            cleaned = f"{preamble}\n\n{cleaned}".strip()
        if cleaned:
            chunks.append(cleaned)
    return chunks


def _clean(segment: str) -> str:
    """Bỏ dòng phân cách `---` đơn lẻ và whitespace thừa."""
    lines = [ln for ln in segment.splitlines() if ln.strip() != "---"]
    return "\n".join(lines).strip()


def build_chunks(path: Path) -> list[Chunk]:
    """Đọc 1 file .md -> danh sách Chunk kèm metadata (chưa embedding)."""
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)

    # Default hợp lý nếu frontmatter thiếu field (không raise để không chặn ingest).
    doc_type = meta.get("doc_type") or "khac"
    property_type = meta.get("property_type") or "all"

    metadata = {"doc_type": doc_type, "property_type": property_type}
    if meta.get("title"):
        metadata["title"] = meta["title"]

    return [
        Chunk(source_doc=path.name, chunk_text=text, metadata=dict(metadata))
        for text in chunk_markdown(body)
    ]


def build_all_chunks(kb_dir: Path = KB_DIR) -> list[Chunk]:
    """Gom chunk của toàn bộ *.md trong kb_dir (dùng cho ingest & self-test)."""
    all_chunks: list[Chunk] = []
    for path in sorted(kb_dir.glob("*.md")):
        try:
            all_chunks.extend(build_chunks(path))
        except Exception as exc:  # noqa: BLE001 - 1 file lỗi không chặn toàn bộ
            print(f"[warn] Bỏ qua {path.name}: {exc}", file=sys.stderr)
    return all_chunks


def ingest(kb_dir: Path = KB_DIR) -> int:
    """Nạp toàn bộ kb_documents vào bảng KbChunk. Trả về số chunk đã insert.

    Cần `.env` thật (embedding endpoint) + Postgres/pgvector đang chạy.
    """
    # Import "nặng" đặt trong hàm để self-test chunking không cần DB/SDK.
    from sqlalchemy import delete, text

    from app.db.session import Base, SessionLocal, engine
    from app.models.kb_chunk import KbChunk
    from app.rag.embedder import embed_texts

    # Đảm bảo extension pgvector + bảng tồn tại.
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)

    chunks = build_all_chunks(kb_dir)
    if not chunks:
        print("[warn] Không tìm thấy chunk nào để ingest.", file=sys.stderr)
        return 0

    embeddings = embed_texts([c.chunk_text for c in chunks])

    inserted = 0
    with SessionLocal() as session:
        # Idempotent: xoá chunk cũ của các source_doc sắp nạp lại.
        source_docs = {c.source_doc for c in chunks}
        session.execute(
            delete(KbChunk).where(KbChunk.source_doc.in_(source_docs))
        )
        for chunk, emb in zip(chunks, embeddings):
            session.add(
                KbChunk(
                    source_doc=chunk.source_doc,
                    chunk_text=chunk.chunk_text,
                    embedding=emb,
                    metadata_json=chunk.metadata,
                )
            )
            inserted += 1
        session.commit()

    print(f"[ok] Đã ingest {inserted} chunk từ {len(source_docs)} tài liệu.")
    return inserted


def _self_test() -> None:
    """In số chunk theo từng file (offline, không cần DB/embedding)."""
    # Console Windows mặc định cp1252 không in được tiếng Việt -> ép UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        pass
    total = 0
    for path in sorted(KB_DIR.glob("*.md")):
        chunks = build_chunks(path)
        meta = chunks[0].metadata if chunks else {}
        print(
            f"{path.name:40s} -> {len(chunks):2d} chunk "
            f"(doc_type={meta.get('doc_type')}, property_type={meta.get('property_type')})"
        )
        total += len(chunks)
    print(f"TỔNG: {total} chunk từ {len(list(KB_DIR.glob('*.md')))} tài liệu")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        _self_test()
    else:
        ingest()
