# Contract — SSE streaming tiến độ job (toàn platform)

> **Trạng thái:** v1 — áp cho **mọi AI service async** (property_intake, property_lookup, và các function sau).
> **Mục đích:** FE nhận tiến độ **real-time** cho tác vụ nặng, thay cho polling (hết bị proxy/timeout ngắt).

## Luồng chuẩn (mọi function AI)

```
1) POST /api/v1/services/{service_id}/run     (header X-API-Key, body {input})
      → 200 { "job_id": "...", "status": "pending" }
2) Mở SSE: GET /api/v1/jobs/{job_id}/stream?api_key=<key>
      → nhận snapshot → progress... → done (kèm result)  → server tự đóng
```

FE **không cần poll** `/jobs/{id}` nữa (vẫn giữ endpoint đó để tra cứu khi cần).

## Endpoint SSE

```
GET /api/v1/jobs/{job_id}/stream
Content-Type: text/event-stream
```

**Auth:** trình duyệt `EventSource` không set được header → truyền key qua **query `?api_key=<key>`**.
Nếu FE dùng `fetch`+ReadableStream thì có thể dùng header `X-API-Key`. Chỉ đọc được job của chính user (403 nếu khác chủ, 404 nếu không tồn tại).

## Các sự kiện (SSE events)

| event | Khi nào | data |
|---|---|---|
| `snapshot` | ngay khi kết nối | `{ "status", "progress" }` — trạng thái hiện tại (phòng khi nối trễ) |
| `progress` | mỗi bước node của pipeline | `{ "progress": 0..100 }` |
| `status` | khi job chuyển `running` | `{ "status": "running" }` |
| `done` | job xong | `{ "status": "completed", "result": <OutputSchema của service> }` → **đóng** |
| `error` | job lỗi | `{ "status": "failed", "error": "..." }` → **đóng** |
| `:` (comment) | ~15s idle | heartbeat giữ kết nối qua proxy |

Mốc `progress` của **property_intake** theo 6 node: `30` ingest · `55` extract · `70` verify · `82` merge · `92` validate · `100` assemble.

## Ví dụ dòng SSE thật (property_intake)

```
event: snapshot
data: {"status": "running", "progress": 0}

: heartbeat

event: progress
data: {"progress": 30}
event: progress
data: {"progress": 55}
...
event: progress
data: {"progress": 100}

event: done
data: {"status": "completed", "result": { ... PropertyIntakeOutput ... }}
```

## FE — dùng EventSource

```js
const res = await fetch(`/api/v1/services/property_intake/run`, {
  method: "POST",
  headers: { "X-API-Key": key, "Content-Type": "application/json" },
  body: JSON.stringify({ input: { file_ids, case_id } }),
});
const { job_id } = await res.json();

const es = new EventSource(`/api/v1/jobs/${job_id}/stream?api_key=${key}`);
es.addEventListener("progress", (e) => setProgress(JSON.parse(e.data).progress));
es.addEventListener("done", (e) => { render(JSON.parse(e.data).result); es.close(); });
es.addEventListener("error", (e) => { /* job lỗi hoặc mất kết nối */ es.close(); });
```

> `EventSource` **tự reconnect** khi rớt mạng; khi nối lại nhận `snapshot` để đồng bộ, và nếu job đã xong sẽ nhận `done` ngay.

## Test tay bằng curl

```bash
curl -N "http://localhost:8888/api/v1/jobs/<job_id>/stream?api_key=<key>"
# -N = không buffer, in stream real-time tới khi 'done' rồi đóng
```

## Kiến trúc (tham khảo)

Worker (Celery) publish sự kiện lên **Redis pub/sub** (`job-events:{job_id}`) mỗi khi tiến độ/ trạng thái đổi; endpoint SSE subscribe kênh đó và relay ra FE — API process stream được tiến độ do **process worker khác** sinh ra, không cần chạm DB liên tục. Xem `services/event_bus.py`, `api/v1/endpoints/jobs.py`.
