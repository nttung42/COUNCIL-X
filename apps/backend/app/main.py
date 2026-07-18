"""FastAPI app PAA — lắp ráp router + error handler + CORS.

Chạy: ``uvicorn app.main:app --reload`` (backend tại http://localhost:8000).

Store backend chọn qua ``settings.store_backend`` ("memory" mặc định — chạy ngay
không cần Postgres; "sql" cần Postgres + tạo bảng). Khi dùng "sql", startup gọi
``Base.metadata.create_all`` để tạo bảng case_sessions/trace_events (KbChunk cần
pgvector -> nên nạp qua ``python -m app.rag.ingest``).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import appraisal, cases, chat
from app.config import settings
from app.errors import install_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    if (getattr(settings, "store_backend", "memory") or "memory").lower() == "sql":
        try:
            import app.models  # noqa: F401 - đăng ký CaseSession/TraceEvent/KbChunk
            from app.db.session import Base, engine

            # Chỉ tạo bảng case/trace; KbChunk (pgvector) nạp riêng qua ingest.
            from app.models.case_session import CaseSession
            from app.models.trace_event import TraceEvent

            Base.metadata.create_all(
                engine, tables=[CaseSession.__table__, TraceEvent.__table__]
            )
        except Exception as exc:  # noqa: BLE001 - không chặn khởi động nếu DB chưa sẵn
            print(f"[PAA] Cảnh báo: không tạo được bảng SQL ({exc}). "
                  "Kiểm tra DATABASE_URL / Postgres.")
    yield


app = FastAPI(title="PAA — Property Appraisal Agent API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

install_error_handlers(app)

app.include_router(appraisal.router)
app.include_router(cases.router)
app.include_router(chat.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "store_backend": getattr(settings, "store_backend", "memory")}
