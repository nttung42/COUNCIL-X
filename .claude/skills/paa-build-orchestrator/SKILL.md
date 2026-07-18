---
name: paa-build-orchestrator
description: "Điều phối 5 agent chuyên trách để build song song MVP Property Appraisal Agent (PAA) cho SHB — Lookup Tools, Valuation & Risk, Advisory & RAG, Frontend (Wave 1, song song), Orchestrator & API (Wave 2, sau khi Wave 1 backend xong). Dùng khi user nói 'build PAA', 'triển khai PAA', 'chạy các agent PAA song song', 'implement tasks.md của PAA', hoặc yêu cầu tiếp tục/build lại/sửa 1 phần của PAA MVP (vd. 'sửa lại lookup tools', 'build lại frontend', 'chạy tiếp orchestrator sau khi 3 agent kia xong')."
---

# PAA Build Orchestrator

Điều phối việc code hoá `specs/001-property-appraisal-agent/tasks.md` bằng 5 agent chuyên trách,
chạy qua **Agent tool ở chế độ sub-agent** (không dùng TeamCreate) — vì toàn bộ hợp đồng giao tiếp
giữa các module đã được chuẩn hoá đầy đủ bằng file trước khi bắt đầu (`data-model.md`,
`contracts/appraisal-api.md`, `tasks.md`), nên không cần hội thoại real-time giữa các agent; mỗi
agent chỉ cần đọc đúng tài liệu và trả file đúng vị trí.

## Thực thi mô hình: Sub-agent, 2 wave (fan-out → 1 phụ thuộc)

## Cấu hình agent

| Agent | subagent_type | Skill | Output chính |
|---|---|---|---|
| `paa-lookup-tools` | custom (`.claude/agents/paa-lookup-tools.md`) | `paa-lookup-tools-impl` | `backend/app/tools/{7 file lookup}.py` |
| `paa-valuation-risk` | custom | `paa-valuation-risk-impl` | `backend/app/tools/calculate_valuation.py`, `calculate_asset_risk_score.py` |
| `paa-advisory-rag` | custom | `paa-advisory-rag-impl` | `backend/app/rag/*.py`, `backend/app/tools/query_knowledge_base.py`, `generate_report_draft.py` |
| `paa-frontend` | custom | `paa-frontend-impl` | `frontend/src/**` |
| `paa-orchestrator-api` | custom | `paa-orchestrator-api-impl` | `backend/app/agents/*.py`, `orchestrator/*.py`, `api/*.py` |

## Workflow

### Phase 0: Kiểm tra tiền đề & xác định chế độ chạy

1. Xác nhận `specs/001-property-appraisal-agent/{spec,plan,data-model,tasks}.md` và
   `contracts/appraisal-api.md` tồn tại — đây là input bắt buộc cho mọi agent. Nếu thiếu, DỪNG và
   báo người dùng cần chạy speckit trước (`/speckit-specify` → `/speckit-plan` → `/speckit-tasks`).
2. Kiểm tra `backend/app/mockdata/*.json` + `kb_documents/*.md` tồn tại — nếu thiếu, ưu tiên tạo
   mock data trước (đây là Foundational phase, chặn mọi agent Wave 1 theo constitution Development
   Workflow).
3. Xác định chế độ chạy dựa trên trạng thái hiện có của `backend/`/`frontend/`:
   - **Chưa có file nào ở `backend/app/tools/`, `frontend/src/`** → build lần đầu, chạy Phase 1→4
     đầy đủ.
   - **Đã có 1 phần file (vd. đã chạy Wave 1 nhưng chưa chạy Wave 2)** → chỉ chạy phần còn thiếu;
     đọc file đã có để agent kế tiếp dùng làm input thật thay vì giả định.
   - **User yêu cầu sửa/build lại 1 agent cụ thể** (vd. "sửa lại lookup tools") → chỉ gọi lại đúng
     agent đó, truyền thêm vào prompt đường dẫn file cũ để agent đọc và cải thiện thay vì viết lại
     từ đầu.

### Phase 1: Wave 1 — 4 agent chạy song song (Lookup Tools, Valuation & Risk, Advisory & RAG, Frontend)

Gọi 4 lần `Agent` tool trong CÙNG 1 message (để chạy song song thật), mỗi lần:
- `subagent_type`: tên agent tương ứng ở bảng trên
- `model`: kế thừa model phiên hiện tại trừ khi người dùng yêu cầu khác (không cần ép `opus` — đây
  là task code hoá theo spec đã có sẵn rất chi tiết, không phải nghiên cứu mở, model hiện tại của
  phiên là đủ)
- `run_in_background: true`
- `prompt`: tối thiểu phải nêu rõ (a) đường dẫn `specs/001-property-appraisal-agent/` để agent tự
  đọc spec/plan/data-model/tasks/contracts liên quan, (b) nhắc lại phạm vi file CHỈ thuộc agent đó
  (tránh đụng file agent khác), (c) nếu là lần chạy lại: đường dẫn file cũ cần đọc trước khi sửa.

Ví dụ 1 lời gọi (lặp lại tương tự cho 3 agent còn lại trong cùng message):

```
Agent({
  description: "Implement 7 PAA lookup tools",
  subagent_type: "paa-lookup-tools",
  run_in_background: true,
  prompt: "Đọc specs/001-property-appraisal-agent/{spec,plan,data-model,tasks}.md và
    backend/app/mockdata/README.md, sau đó implement đầy đủ 7 lookup tool theo đúng phạm vi và
    nguyên tắc đã định nghĩa trong agent/skill của bạn. Báo cáo lại danh sách file đã tạo và mọi
    giả định đã đưa ra."
})
```

**Không** chờ agent Frontend hoàn tất mới chuyển Phase 2 — Frontend độc lập hoàn toàn, có thể tiếp
tục chạy song song hoặc hoàn tất trước/sau Wave 2 tuỳ tốc độ, không ảnh hưởng dependency.

### Phase 2: Wave 2 — Orchestrator & API (chờ 3 agent backend Wave 1)

1. Chờ kết quả (không phải Frontend) của `paa-lookup-tools`, `paa-valuation-risk`,
   `paa-advisory-rag` — 3 agent này tạo ra các file mà `paa-orchestrator-api` cần import.
2. Đọc báo cáo cuối của cả 3 agent (đặc biệt mọi "giả định"/"sai khác chữ ký hàm" họ đã nêu).
3. Gọi `Agent` với `subagent_type: "paa-orchestrator-api"`, `run_in_background: false` (cần kết quả
   ngay để báo cáo lại người dùng), prompt bao gồm tóm tắt các giả định/sai khác đã thu thập ở bước
   2 để agent này không phải tự dò lại từ đầu.

### Phase 3: Kiểm tra tích hợp (nhẹ, không phải QA đầy đủ)

1. Xác nhận toàn bộ file trong bảng "Cấu hình agent" đã tồn tại đúng vị trí (`ls`/`Glob` nhanh).
2. Nếu có, chạy thử `scripts/mock_planner.py` theo `quickstart.md` Kịch bản 1 — nếu lỗi do thiếu
   `.env` thật (LLM/DB chưa cấu hình), ghi rõ đây là bước cần người dùng tự hoàn tất, không coi là
   lỗi của agent.
3. Báo cáo tổng hợp cho người dùng: agent nào xong, file nào đã tạo, vấn đề/giả định nào cần người
   dùng xác nhận thêm, và bước tiếp theo (`docker compose up`, điền `.env`, chạy quickstart.md).

## Data flow

```
[paa-lookup-tools]  ─┐
[paa-valuation-risk] ─┼─► (files) ─► [paa-orchestrator-api] ─► báo cáo tích hợp
[paa-advisory-rag]   ─┘
[paa-frontend]       ────────────────────────────────────────► (độc lập, không chặn)
```

## Error Handling

- 1 agent Wave 1 thất bại/timeout: thử lại 1 lần. Nếu vẫn lỗi, vẫn tiến hành Wave 2 với các agent
  Wave 1 còn lại đã xong, ghi rõ trong báo cáo cuối "phần X chưa implement, agent
  paa-orchestrator-api sẽ gặp lỗi import — cần chạy lại agent [tên] trước khi build đầy đủ".
- Quá nửa agent Wave 1 thất bại: dừng lại, báo người dùng trước khi tự ý chạy Wave 2 (Wave 2 sẽ vô
  nghĩa nếu thiếu quá nhiều input).
- Timeout: dùng kết quả đã có, không tự đoán nội dung file agent chưa kịp trả.

## Test Scenarios

**Luồng bình thường**: (1) Phase 0 xác nhận đủ spec + mock data → (2) Phase 1 gọi 4 agent song song
trong 1 message → (3) 3 agent backend báo hoàn tất → (4) Phase 2 gọi `paa-orchestrator-api` →
(5) Phase 3 xác nhận đủ file + chạy thử mock_planner.py → (6) báo cáo "PAA MVP build xong, cần điền
.env thật để chạy full pipeline".

**Luồng lỗi**: agent `paa-valuation-risk` timeout ở Wave 1 → thử lại 1 lần → vẫn lỗi → vẫn gọi
`paa-orchestrator-api` với 2/3 input backend, kèm cảnh báo rõ trong prompt "calculate_valuation.py
và calculate_asset_risk_score.py CHƯA có, hãy tạo stub tạm hoặc bỏ qua wiring phần đó, ghi rõ trong
report" → báo cáo cuối liệt kê rõ phần còn thiếu cần chạy lại `paa-valuation-risk` riêng.
