---
name: paa-frontend-impl
description: "Mapping chi tiết từng section của PAA_Mockup_SHB.html sang component React, cách tổ chức state đồng bộ chat/info panel qua SSE, và cách dùng fixture để test UI độc lập trước khi backend sẵn sàng. Dùng khi viết code cho frontend/src/**."
---

# Implement PAA Frontend theo Mockup

## Mapping HTML mockup → component (dòng tham chiếu trong `PAA_Mockup_SHB.html`)

| Mockup section | Component | Ghi chú |
|---|---|---|
| `.sidebar` (dòng ~250-287) | `Sidebar.tsx` | copy nguyên cấu trúc `.sb-brand`, `.new-req-btn`, `.history-list`; dot màu theo status: `good`=hoàn tất, `warning`=đang xử lý, `text-muted`=huỷ |
| `.chat-pane` (dòng ~298-315) | `ChatPane.tsx` | 3 loại message: `.msg.agent`, `.msg.user`, `.msg.status` (dashed border, in nghiêng) — giữ đúng 3 style này khi render message theo `role` |
| `.subtab-bar` + `.info-screen` (dòng ~319-487) | `SubtabBar.tsx` + 6 `Tab*.tsx` | mỗi `.info-screen` = 1 component riêng, `SubtabBar` chỉ quản lý active tab index |
| Screen 1 form (dòng ~331-344) | `Tab1Input.tsx` | field: address, property_type, area_m2, legal_status_claimed, requested_amount, purpose |
| Screen 2 lookup (dòng ~347-385) | `Tab2Lookup.tsx` | bảng giao dịch so sánh + 6 `.lookup-card`; badge `good`=đã xác thực, `warning`=lưu ý/chưa xác thực — map trực tiếp từ `source_type`/`verified` |
| Screen 3 valuation (dòng ~388-414) | `Tab3Valuation.tsx` | 4 `.stat-tile`, `.barchart` 3 phương pháp, sparkline SVG (copy logic `drawSpark()` dòng ~519-536 sang `useEffect`) |
| Screen 4 risk (dòng ~417-446) | `Tab4Risk.tsx` | 2 `.meter-wrap` (risk score, LTV), `.barchart` 5 nhóm rủi ro, `.flag-row` list |
| Screen 5 checklist (dòng ~449-471) | `Tab5Checklist.tsx` | `.check-item` toggle logic (dòng ~510-518) — gọi API PATCH thay vì chỉ toggle class cục bộ |
| Screen 6 dashboard (dòng ~474-485) | `Tab6Dashboard.tsx` | `.timeline`/`.tl-item` — map từ mảng `trace_events` |
| CSS `:root` tokens (dòng ~8-39) | `theme/tokens.css` | copy nguyên xi mọi biến `--navy-*`, `--orange-*`, `--good/warning/serious/critical` |

## State đồng bộ Chat ↔ Info Panel (FR-011)

```ts
// state/caseStore.ts
type CaseState = {
  caseId: string | null
  activeTab: 1|2|3|4|5|6
  chatMessages: {role: 'user'|'agent'|'status', content: string}[]
  caseData: AppraisalReport | null   // shape theo contracts/appraisal-api.md §3
}
```

- Mở SSE (`GET /api/cases/{id}/stream`) ngay sau khi tạo case; mỗi `step_update` event:
  append 1 message vào `chatMessages` (dùng `chat_message` field từ event) VÀ set `activeTab` từ
  `active_tab` field — người dùng vẫn bấm tay đổi tab được sau đó (không khoá lại activeTab).
- Khi chọn case khác từ Sidebar: đóng SSE cũ, gọi `GET /api/cases/{id}` để load state đầy đủ, mở
  SSE mới nếu `status="processing"`.

## Test UI độc lập bằng fixture (không chờ backend thật)

Tạo `frontend/src/mocks/fixtureCase.ts` chứa 1 object mẫu đúng shape response
`GET /api/cases/{id}` (dùng số liệu trong `contracts/appraisal-api.md` §3 và
`backend/app/mockdata/README.md` — địa chỉ "Hẻm 45 Nguyễn Văn A", định giá 4.85 tỷ, risk 34/100).
Trong `apiClient.ts`, thêm 1 flag `USE_FIXTURE` (đọc từ biến môi trường Vite
`VITE_USE_FIXTURE=true`) để trả fixture thay vì gọi fetch thật khi đang phát triển UI song song với
backend — xoá/tắt flag này khi tích hợp với API thật ở bước cuối, không xoá code fixture (giữ để
dùng lại cho Storybook/test sau này nếu cần).

## Nguyên tắc hiển thị dữ liệu (Nguyên tắc II/III/VI)

- Mọi ô số liệu định giá/rủi ro: bọc trong 1 wrapper hiển thị kèm `<span class="qmark"
  data-why="...">?</span>` (pattern có sẵn trong mockup) ghi rõ nguồn + độ tin cậy — không render
  số trần trụi.
- Tab2Lookup: render `stigma_factors`/nhóm tin đồn trong 1 card RIÊNG BIỆT với badge màu
  `warning` + text "Chưa xác thực", không gộp chung UI với card pháp lý/quy hoạch (badge `good`
  + "Đã xác thực").
- `App.tsx`: thêm 1 banner cố định (không có nút đóng) nội dung disclaimer dữ liệu mô phỏng, đặt
  ngay dưới header, hiển thị trên mọi tab.
