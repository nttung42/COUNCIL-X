<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/001-property-appraisal-agent/plan.md`
<!-- SPECKIT END -->

## Harness: PAA MVP Build (5 agent song song)

**Mục tiêu:** code hoá `specs/001-property-appraisal-agent/tasks.md` bằng 5 agent chuyên trách
(Lookup Tools, Valuation & Risk, Advisory & RAG, Frontend chạy song song Wave 1; Orchestrator & API
chạy Wave 2 sau khi 3 agent backend Wave 1 xong).

**Trigger:** khi yêu cầu build/triển khai/implement PAA, hoặc build lại/sửa 1 phần cụ thể (lookup
tools, valuation, risk, RAG, orchestrator, API, frontend) của PAA MVP, dùng skill
`paa-build-orchestrator`. Câu hỏi đơn thuần về kiến trúc/spec thì trả lời trực tiếp, không cần
trigger skill.

**Thay đổi:**
| Ngày | Thay đổi | Đối tượng | Lý do |
|---|---|---|---|
| 2026-07-18 | Khởi tạo harness: 5 agent + 5 skill impl + 1 orchestrator skill | `.claude/agents/paa-*.md`, `.claude/skills/paa-*` | Yêu cầu ban đầu: phân task tasks.md ra nhiều agent chạy song song qua Agent tool |
