/* ============================================================================
   Fixture — 1 case mẫu đúng shape GET /api/cases/{id} (contracts §3).
   Số liệu bám sát PAA_Mockup_SHB.html + backend/app/mockdata/README.md:
   địa chỉ "Hẻm 45 Nguyễn Văn A", định giá 4.85 tỷ (78%), risk 34/100 (MEDIUM),
   LTV 65%, flag stigma (tin đồn 2019, verified=false) + flag môi trường (ngập 2022–2023).

   Dùng khi VITE_USE_FIXTURE=true để phát triển/test UI độc lập, KHÔNG chờ backend.
   Không xoá khi tích hợp API thật — giữ để test/Storybook (theo skill paa-frontend-impl).
   ============================================================================ */
import type { AppraisalReport, CaseListItem, StepUpdateEvent } from '../types'

export const FIXTURE_CASE_ID = 'fixture-0001'

export const fixtureCaseList: CaseListItem[] = [
  { case_id: 'fixture-0001', address: 'Hẻm 45 Nguyễn Văn A, Q.C', status: 'processing', updated_at: '2026-07-18T10:00:00Z' },
  { case_id: 'fixture-0002', address: '12 Trần Văn B, Q.7', status: 'completed', updated_at: '2026-07-17T09:00:00Z' },
  { case_id: 'fixture-0003', address: 'Chung cư Sunview, Q.Bình Thạnh', status: 'completed', updated_at: '2026-07-15T09:00:00Z' },
  { case_id: 'fixture-0004', address: 'Đất nền Long Thành, Đồng Nai', status: 'completed', updated_at: '2026-07-11T09:00:00Z' },
  { case_id: 'fixture-0005', address: '34 Lê Văn C, Q.10', status: 'cancelled', updated_at: '2026-07-04T09:00:00Z' },
]

export const fixtureCase: AppraisalReport = {
  case_id: FIXTURE_CASE_ID,
  request_id: 'REQ-2026-0001',
  status: 'completed',
  subject_property: {
    address: 'Hẻm 45 Nguyễn Văn A, Phường B, Quận C',
    lat: 10.7756,
    long: 106.7019,
    area_m2: 62,
    property_type: 'nha_pho',
    legal_status_claimed: 'so_hong',
  },
  loan_context: {
    requested_amount: 3200000000,
    purpose: 'the_chap_vay_von',
  },
  lookup_result: {
    market_price: {
      tool_name: 'market_price_lookup',
      status: 'ok',
      confidence: 0.82,
      source_type: 'mock',
      data: {
        price_index_period: '2026-Q2',
        price_index: [
          { period: '2024-Q1', index: 100.0 },
          { period: '2024-Q3', index: 103.1 },
          { period: '2025-Q1', index: 106.2 },
          { period: '2025-Q3', index: 110.4 },
          { period: '2025-Q4', index: 114.8 },
          { period: '2026-Q1', index: 116.9 },
          { period: '2026-Q2', index: 118.3 },
        ],
        comparables: [
          { transaction_id: 'TXN-000121', address: 'Hẻm 40 Nguyễn Văn A', distance_from_subject_km: 0.3, area_m2: 58, transaction_date: '2025-11-01', price_per_m2: 76600000, source_type: 'mock', confidence: 0.8 },
          { transaction_id: 'TXN-000122', address: 'Đường Nguyễn Văn A', distance_from_subject_km: 0.6, area_m2: 65, transaction_date: '2025-09-01', price_per_m2: 79200000, source_type: 'mock', confidence: 0.78 },
          { transaction_id: 'TXN-000123', address: 'Hẻm 12 Trần Văn B', distance_from_subject_km: 0.8, area_m2: 60, transaction_date: '2025-06-01', price_per_m2: 88100000, source_type: 'mock', confidence: 0.72 },
          { transaction_id: 'TXN-000124', address: 'Hẻm 45 (kế bên)', distance_from_subject_km: 0.1, area_m2: 64, transaction_date: '2026-02-01', price_per_m2: 98400000, source_type: 'mock', confidence: 0.9 },
          { transaction_id: 'TXN-000125', address: 'Đường Lê Văn C', distance_from_subject_km: 1.1, area_m2: 70, transaction_date: '2026-01-01', price_per_m2: 95000000, source_type: 'mock', confidence: 0.85 },
        ],
      },
    },
    planning_zoning: {
      tool_name: 'planning_zoning_lookup', status: 'ok', confidence: 0.85, source_type: 'mock',
      data: { zoning_status: 'Không quy hoạch treo. Lộ giới dự kiến mở rộng theo QH 2024.', is_planned_overlay: false, road_widening_plan: 'QH 2024' },
    },
    legal_status: {
      tool_name: 'legal_status_lookup', status: 'ok', confidence: 0.95, source_type: 'mock',
      data: { legal_status: 'Sổ hồng chính chủ, không tranh chấp, không thế chấp nơi khác.', has_dispute: false, mortgaged_elsewhere: false },
    },
    neighborhood_amenity: {
      tool_name: 'neighborhood_amenity_lookup', status: 'ok', confidence: 0.8, source_type: 'mock',
      data: {
        amenities: [
          { type: 'school', name: 'Trường tiểu học', distance_m: 300 },
          { type: 'market', name: 'Chợ', distance_m: 450 },
          { type: 'bus', name: 'Trạm bus', distance_m: 200 },
          { type: 'hospital', name: 'BV quận', distance_m: 1200 },
        ],
      },
    },
    environmental_risk: {
      tool_name: 'environmental_risk_lookup', status: 'ok', confidence: 0.7, source_type: 'mock',
      data: { flood_risk: 'Thấp', landslide_risk: 'Không', pollution_risk: 'Thấp', notes: 'Từng ngập nhẹ mùa mưa 2022–2023 (mức thấp).' },
    },
    liquidity_stat: {
      tool_name: 'liquidity_stat_lookup', status: 'ok', confidence: 0.75, source_type: 'mock',
      data: { avg_days_on_market: 45, success_rate_pct: 82 },
    },
    stigma_reputation: {
      tool_name: 'stigma_reputation_lookup', status: 'partial', confidence: 0.3, source_type: 'unverified_rumor',
      warning: 'Tin đồn chưa kiểm chứng — chỉ mang tính cảnh báo tham khảo, không dùng để từ chối hồ sơ.',
      data: { rumors: [{ detail: 'Tin đồn dân cư chưa xác thực về sự việc năm 2019.', year: 2019, verified: false }] },
    },
  },
  valuation: {
    estimated_value: 4850000000,
    value_range: { low: 4550000000, high: 5100000000 },
    value_per_m2: 97000000,
    confidence_score: 0.78,
    methodology_breakdown: {
      comparable_approach: 4900000000,
      hedonic_model: 4800000000,
      cost_approach: 4750000000,
    },
    comparables_used: 6,
    time_adjustment_index_period: '2026-Q2',
    price_index_series: [
      { period: '2024-Q1', index: 100.0 },
      { period: '2024-Q3', index: 103.1 },
      { period: '2025-Q1', index: 106.2 },
      { period: '2025-Q3', index: 110.4 },
      { period: '2025-Q4', index: 114.8 },
      { period: '2026-Q1', index: 116.9 },
      { period: '2026-Q2', index: 118.3 },
    ],
    adjustment_notes: [
      'Quy đổi giá giao dịch về kỳ 2026-Q2 theo chỉ số giá khu vực (gốc 100).',
      'Loại 1 giao dịch ngoài bán kính 1.1km khỏi blend so sánh trực tiếp.',
    ],
  },
  asset_risk: {
    asset_risk_score: 34,
    risk_tier: 'MEDIUM',
    recommended_ltv_cap: 0.65,
    risk_group_scores: {
      legal: 15,
      liquidity: 30,
      price_volatility: 55,
      physical_environmental: 30,
      reputation_stigma: 60,
    },
    flags: [
      { type: 'legal', severity: 'low', detail: 'Sổ hồng hợp lệ, không tranh chấp ghi nhận.', confidence: 0.95, verified: true },
      { type: 'stigma', severity: 'medium', detail: 'Tin đồn dân cư chưa xác thực về sự việc 2019 — cần xác minh thực địa.', confidence: 0.35, verified: false, action: 'Khảo sát thực địa xác minh tin đồn' },
      { type: 'environmental', severity: 'low', detail: 'Khu vực từng ngập nhẹ 2022–2023 — khuyến nghị mua bảo hiểm tài sản.', confidence: 0.7, verified: true, action: 'Mua bảo hiểm tài sản' },
    ],
    recommended_conditions: [
      'Xác minh thực địa tin đồn dân cư trước khi phê duyệt.',
      'Mua bảo hiểm tài sản do khu vực từng ngập nhẹ.',
    ],
  },
  checklist: [
    { item_id: 'CHK-1', text: 'Xác thực sổ hồng qua hệ thống nội bộ', is_checked: true, related_flag_type: 'legal' },
    { item_id: 'CHK-2', text: 'Đối chiếu quy hoạch khu vực', is_checked: true, related_flag_type: null },
    { item_id: 'CHK-3', text: 'Khảo sát thực địa xác minh tin đồn dân cư (2019)', is_checked: false, related_flag_type: 'stigma' },
    { item_id: 'CHK-4', text: 'Mua bảo hiểm tài sản do khu vực từng ngập nhẹ', is_checked: false, related_flag_type: 'environmental' },
    { item_id: 'CHK-5', text: 'Chụp ảnh hiện trạng công trình', is_checked: false, related_flag_type: null },
  ],
  draft_report: {
    sections: {
      property_info: 'Hẻm 45 Nguyễn Văn A, 62m² · Sổ hồng chính chủ.',
      valuation: '4.85 tỷ (4.55–5.10 tỷ), độ tin cậy 78%.',
      risk_and_ltv: 'Điểm rủi ro tài sản 34/100 (Trung bình) — LTV đề xuất 65%.',
    },
    signature_block: '☐ Chữ ký thẩm định viên      ☐ Xác nhận chuyên viên tín dụng',
  },
  requires_human_verification: true,
  trace_id: 'TRACE-8891',
  trace_events: [
    { step_name: 'Hệ thống tiếp nhận yêu cầu', component: 'planner', t_offset_seconds: 0.0, output_summary: 'Từ hệ thống điều phối chung (Planner Agent)' },
    { step_name: '7 nguồn tra cứu chạy song song', component: 'research_agent', t_offset_seconds: 1.2, output_summary: 'Giá thị trường, quy hoạch, pháp lý, tiện ích, dư luận, môi trường, thanh khoản...' },
    { step_name: 'Bộ máy định giá hoàn tất', component: 'valuation_agent', t_offset_seconds: 1.4, output_summary: 'Giá trị ước tính: 4.85 tỷ' },
    { step_name: 'Bộ máy chấm điểm rủi ro hoàn tất', component: 'risk_agent', t_offset_seconds: 1.6, output_summary: 'Điểm rủi ro tài sản: 34/100 · Trung bình' },
    { step_name: 'Copilot sinh nháp biên bản', component: 'advisory_agent', t_offset_seconds: 2.3, output_summary: 'Cần thẩm định viên xác minh thêm: Có' },
  ],
}

/* Kịch bản SSE mô phỏng — apiClient phát lại tuần tự khi USE_FIXTURE, để test đồng bộ
   chat ↔ info panel (FR-011) mà không cần backend. */
export const fixtureStepUpdates: StepUpdateEvent[] = [
  { step_name: 'Tiếp nhận yêu cầu', active_tab: 1, chat_message: 'Đã nhận yêu cầu. Đang tra cứu dữ liệu khu vực (giao dịch so sánh, quy hoạch, pháp lý, dư luận...).' },
  { step_name: 'Tra cứu song song', active_tab: 2, chat_message: '⏳ Đang gọi 7 adapter tra cứu song song…', status: 'processing' },
  { step_name: 'Đã có kết quả tra cứu', active_tab: 2, chat_message: 'Đã có kết quả tra cứu — xem tab Kết quả tra cứu. Phát hiện 1 điểm cần lưu ý (tin đồn khu vực, chưa xác thực).' },
  { step_name: 'Định giá hoàn tất', active_tab: 3, chat_message: 'Định giá đề xuất 4.85 tỷ, độ tin cậy 78% — xem tab Định giá.' },
  { step_name: 'Chấm điểm rủi ro hoàn tất', active_tab: 4, chat_message: 'Điểm rủi ro BĐS 34/100 (Trung bình), LTV đề xuất 65% — xem tab Rủi ro.', status: 'completed' },
]
