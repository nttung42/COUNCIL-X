#!/usr/bin/env python
"""mock_planner.py — smoke test / demo PAA chạy ĐỘC LẬP (không cần Planner Agent thật).

Gọi đúng luồng của ``contracts/appraisal-api.md``:
  (1) POST /api/appraisal-requests  -> 202 {case_id}
  (2) poll GET /api/cases/{id}       -> chờ status=completed (hoặc subscribe SSE)
  (3) in ra AppraisalReport JSON đầy đủ.

Hai chế độ:
  - IN-PROCESS (mặc định): nạp ASGI app trong tiến trình qua httpx.ASGITransport —
    KHÔNG cần chạy uvicorn, KHÔNG cần Postgres (store "memory"). Đủ chứng minh wiring
    pipeline Research→Valuation→Risk→Advisory đúng.
  - SERVER: ``--server-url http://localhost:8000`` gọi backend đang chạy thật.

Ví dụ (quickstart.md Kịch bản 1):
  python scripts/mock_planner.py --address "Hẻm 45 Nguyễn Văn A, Phường B, Quận C" \
    --area-m2 62 --property-type nha_pho --legal-status so_hong \
    --requested-amount 3200000000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Cho phép ``import app...`` khi chạy từ repo root: thêm backend/ vào sys.path.
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Store mặc định memory (không cần Postgres cho smoke test in-process).
os.environ.setdefault("STORE_BACKEND", "memory")

# Console Windows (cp1252) không in được tiếng Việt -> ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass


def build_payload(args) -> dict:
    return {
        "request_id": args.request_id or f"REQ-{int(time.time())}",
        "subject_property": {
            "address": args.address,
            "lat": args.lat,
            "long": args.long,
            "area_m2": args.area_m2,
            "property_type": args.property_type,
            "legal_status_claimed": args.legal_status,
        },
        "loan_context": {
            "requested_amount": args.requested_amount,
            "purpose": args.purpose,
        },
    }


async def run(args) -> int:
    import httpx

    if args.server_url:
        client_kwargs = {"base_url": args.server_url.rstrip("/")}
        mode = f"SERVER {args.server_url}"
    else:
        from app.main import app  # noqa: WPS433

        transport = httpx.ASGITransport(app=app)
        client_kwargs = {"transport": transport, "base_url": "http://paa.local"}
        mode = "IN-PROCESS (ASGI, store=memory)"

    payload = build_payload(args)
    print(f"== PAA mock_planner — chế độ {mode} ==")
    print(f"POST /api/appraisal-requests  request_id={payload['request_id']}")

    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=30.0, **client_kwargs) as client:
        resp = await client.post("/api/appraisal-requests", json=payload)
        if resp.status_code != 202:
            print(f"!! Tạo request thất bại: HTTP {resp.status_code}\n{resp.text}")
            return 1
        case_id = resp.json()["case_id"]
        print(f"   -> 202 case_id={case_id} status=processing")

        # (2) poll tới khi hoàn tất (hoặc timeout).
        deadline = t0 + args.timeout
        case = None
        while time.monotonic() < deadline:
            g = await client.get(f"/api/cases/{case_id}")
            case = g.json()
            if case.get("status") in ("completed", "cancelled"):
                break
            await asyncio.sleep(0.25)

        elapsed = time.monotonic() - t0
        print(f"   -> status={case.get('status')} sau {elapsed:.2f}s\n")

    # (3) in report + kiểm tra nhanh các kỳ vọng quickstart.
    print(json.dumps(case, ensure_ascii=False, indent=2))
    _summarize(case, elapsed)
    return 0 if case.get("status") == "completed" else 2


def _summarize(case: dict, elapsed: float) -> None:
    val = case.get("valuation") or {}
    risk = case.get("asset_risk") or {}
    checklist = case.get("checklist") or []
    stigma_items = [c for c in checklist if c.get("related_flag_type") == "stigma"]
    print("\n" + "=" * 60)
    print("KIỂM TRA NHANH (đối chiếu quickstart.md Kịch bản 1):")
    print(f"  thời gian pipeline           : {elapsed:.2f}s  (<15s? {'OK' if elapsed < 15 else 'CHẬM'})")
    print(f"  valuation.estimated_value    : {val.get('estimated_value')}")
    print(f"  valuation.confidence_score   : {val.get('confidence_score')}")
    print(f"  valuation.comparables_used   : {val.get('comparables_used')}")
    print(f"  asset_risk.asset_risk_score  : {risk.get('asset_risk_score')}")
    print(f"  asset_risk.risk_tier         : {risk.get('risk_tier')}")
    print(f"  asset_risk.recommended_ltv   : {risk.get('recommended_ltv_cap')}")
    print(f"  checklist items              : {len(checklist)}")
    print(f"  mục xác minh tin đồn (stigma) : {len(stigma_items)} "
          f"({'OK' if stigma_items else 'THIẾU'})")
    print(f"  requires_human_verification  : {case.get('requires_human_verification')}")
    print(f"  trace_events                 : {len(case.get('trace_events') or [])} bước")
    print("=" * 60)


def main() -> int:
    p = argparse.ArgumentParser(description="PAA mock Planner smoke test")
    p.add_argument("--address", default="Hẻm 45 Nguyễn Văn A, Phường B, Quận C")
    p.add_argument("--lat", type=float, default=10.7756)
    p.add_argument("--long", type=float, default=106.7019)
    p.add_argument("--area-m2", dest="area_m2", type=float, default=62)
    p.add_argument("--property-type", dest="property_type", default="nha_pho")
    p.add_argument("--legal-status", dest="legal_status", default="so_hong")
    p.add_argument("--requested-amount", dest="requested_amount", type=int, default=3_200_000_000)
    p.add_argument("--purpose", default="the_chap_vay_von")
    p.add_argument("--request-id", dest="request_id", default=None)
    p.add_argument("--server-url", dest="server_url", default=None,
                   help="Nếu đặt, gọi backend đang chạy thật thay vì in-process.")
    p.add_argument("--timeout", type=float, default=15.0)
    args = p.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
