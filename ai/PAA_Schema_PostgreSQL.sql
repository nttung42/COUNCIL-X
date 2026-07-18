-- =====================================================================================
-- PAA (Property Appraisal Agent) — Schema dữ liệu PostgreSQL
-- SHB — Vietnam AI Innovation Challenge 2026
--
-- File này định nghĩa toàn bộ bảng dữ liệu cần thiết để vận hành 5 màn của mockup:
--   Màn 1  Nhập thông tin       -> case_borrower, property_legal_info, property_physical_info,
--                                   loan_info, attached_document
--   Màn 2  Kết quả tra cứu      -> market_comparable, lookup_finding (7 nguồn tra cứu)
--   Màn 3  Định giá             -> valuation_result, valuation_method, valuation_confidence_factor
--   Màn 4  Rủi ro               -> risk_assessment_result, risk_group, risk_flag, risk_ltv_policy_band
--   Màn 5  Dashboard            -> dashboard_step_summary, agent_trace_event, exported_report
--   Chung (mọi màn)             -> appraisal_case, case_step_progress, case_edit_log, chat_message
--
-- Quy ước:
--   - case_id dạng "REQ-2026-0001" là khoá tự nhiên của 1 hồ sơ thẩm định (appraisal_case).
--   - Mọi bảng con dùng UUID làm khoá chính, tham chiếu case_id (FK, ON DELETE CASCADE).
--   - Tiền VND lưu dạng BIGINT (đơn vị: đồng) để tránh sai số dấu phẩy động.
--   - Điểm số / % lưu SMALLINT có CHECK 0-100.
--   - "raw_findings" (dữ liệu tra cứu thô dạng bullet) lưu TEXT[] — đủ dùng cho quy mô 1 hồ sơ,
--     có thể tách bảng con nếu sau này cần tìm kiếm/lọc theo từng dòng.
-- =====================================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto; -- cho gen_random_uuid()

CREATE SCHEMA IF NOT EXISTS paa;
SET search_path TO paa, public;

-- =====================================================================================
-- ENUM TYPES DÙNG CHUNG
-- =====================================================================================

-- Trạng thái hồ sơ — khớp badge màu ở "Lịch sử hồ sơ" (sidebar)
CREATE TYPE case_status AS ENUM ('dang_xu_ly', 'hoan_tat', 'huy');

-- Trạng thái từng bước (subtab) — khoá/mở khoá/đang xác nhận theo đúng cơ chế "Xác nhận & Tiếp theo"
CREATE TYPE step_status AS ENUM ('locked', 'unlocked', 'confirmed');

-- Mức độ nghiêm trọng dùng chung cho risk_flag / risk_assessment_result.risk_label
-- (khớp 4 mức màu CSS: good / warning / serious / critical)
CREATE TYPE severity_level AS ENUM ('thap', 'trung_binh', 'cao', 'nghiem_trong');

-- Trạng thái xác thực của 1 flag/finding
CREATE TYPE verification_status AS ENUM ('da_xac_thuc', 'chua_xac_thuc');

-- Nguồn của 1 chỉnh sửa: sửa trực tiếp trên form hay nhờ PAA sửa qua chat
CREATE TYPE edit_source AS ENUM ('ui_form', 'chat');

-- Trạng thái 1 chỉnh sửa trong luồng "pending -> confirmed" (xanh dương -> xanh lá)
CREATE TYPE edit_status AS ENUM ('pending', 'confirmed');

-- Vai trò người gửi tin nhắn trong khung chat
CREATE TYPE chat_role AS ENUM ('user', 'agent', 'status');

-- Nhóm tài liệu đính kèm (màn 1 — Nguồn tài liệu đính kèm)
CREATE TYPE document_category AS ENUM ('so_do_so_hong', 'cmnd_cccd', 'hop_dong', 'anh_hien_trang', 'khac');

-- 7 nguồn tra cứu của Research Agent (đúng theo PAA_KienTruc_HighLevel.md)
CREATE TYPE lookup_category AS ENUM (
  'market_price', 'planning_zoning', 'legal_status',
  'neighborhood_amenity', 'environmental_risk', 'liquidity_stat', 'stigma_reputation'
);

-- Badge trạng thái hiển thị trên mỗi lookup-detail card ở màn Kết quả tra cứu
CREATE TYPE lookup_badge AS ENUM ('da_xac_thuc', 'luu_y', 'chua_xac_thuc');

-- 3 phương pháp định giá (Valuation Agent)
CREATE TYPE valuation_method_key AS ENUM ('sales_comparison', 'hedonic_ml', 'cost_approach');

-- 5 yếu tố cấu thành độ tin cậy định giá (màn 3)
CREATE TYPE confidence_factor_key AS ENUM (
  'comp_quantity_quality', 'method_consensus', 'legal_planning_completeness',
  'market_volatility', 'comp_similarity'
);

-- 5 nhóm rủi ro cấu thành điểm rủi ro tài sản (màn 4)
CREATE TYPE risk_group_key AS ENUM ('legal', 'liquidity', 'price_volatility', 'physical_environment', 'reputation');

-- =====================================================================================
-- BẢNG GỐC: 1 HỒ SƠ THẨM ĐỊNH (dùng chung cho mọi màn + sidebar "Lịch sử hồ sơ")
-- =====================================================================================

CREATE TABLE appraisal_case (
  case_id         TEXT PRIMARY KEY,                 -- vd. 'REQ-2026-0001'
  status          case_status NOT NULL DEFAULT 'dang_xu_ly',
  current_step    SMALLINT NOT NULL DEFAULT 1 CHECK (current_step BETWEEN 1 AND 5),
  requested_by    TEXT,                              -- thẩm định viên / chuyên viên tín dụng phụ trách
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE appraisal_case IS 'Hồ sơ thẩm định gốc — mỗi dòng tương ứng 1 mục trong "Lịch sử hồ sơ" ở sidebar.';

-- Trạng thái mở khoá/xác nhận của từng subtab (1..5) — cơ chế "phải Xác nhận màn trước mới mở màn sau"
CREATE TABLE case_step_progress (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id       TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  step_number   SMALLINT NOT NULL CHECK (step_number BETWEEN 1 AND 5),
  status        step_status NOT NULL DEFAULT 'locked',
  unlocked_at   TIMESTAMPTZ,
  confirmed_at  TIMESTAMPTZ,
  UNIQUE (case_id, step_number)
);
COMMENT ON TABLE case_step_progress IS 'Trạng thái khoá/mở/xác nhận của 5 subtab — dùng để hiển thị icon 🔒 và chặn nhảy tab khi chưa xác nhận bước trước.';

-- =====================================================================================
-- MÀN 1 — NHẬP THÔNG TIN
-- =====================================================================================

-- A. Thông tin bên vay / chủ sở hữu
CREATE TABLE case_borrower (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id               TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  full_name             TEXT NOT NULL,
  national_id           TEXT NOT NULL,               -- Số CMND/CCCD
  phone_number          TEXT,
  relationship_to_asset TEXT,                         -- vd. 'Chủ sở hữu đứng tên trên GCN'
  is_primary            BOOLEAN NOT NULL DEFAULT true, -- cho phép nhiều đồng sở hữu trong tương lai
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_case_borrower_case_id ON case_borrower(case_id);

-- B. Thông tin pháp lý tài sản
CREATE TABLE property_legal_info (
  case_id                  TEXT PRIMARY KEY REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  certificate_type         TEXT NOT NULL,   -- vd. 'Sổ hồng (QSDĐ & QSH nhà ở)'
  certificate_number       TEXT NOT NULL,
  issue_date               DATE,
  issuing_authority        TEXT,            -- vd. 'Sở TN&MT TP'
  land_plot_number         TEXT,            -- Số thửa
  map_sheet_number         TEXT,            -- Số tờ bản đồ
  land_use_purpose         TEXT,            -- vd. 'Đất ở tại đô thị (ODT)'
  use_term                 TEXT,            -- 'Lâu dài' hoặc ngày hết hạn
  ownership_form           TEXT,            -- vd. 'Sở hữu riêng'
  current_mortgage_status  TEXT             -- vd. 'Chưa thế chấp tại TCTD nào'
);

-- C. Vị trí & đặc điểm tài sản
CREATE TABLE property_physical_info (
  case_id                 TEXT PRIMARY KEY REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  address                 TEXT NOT NULL,             -- địa chỉ đầy đủ hiển thị ở header chat + sidebar
  ward                    TEXT,
  district                TEXT,
  city                    TEXT,
  latitude                NUMERIC(9,6),
  longitude               NUMERIC(9,6),
  property_type           TEXT NOT NULL,             -- vd. 'Nhà phố (nhà trong hẻm)'
  land_area_sqm           NUMERIC(8,2) NOT NULL,
  floor_area_sqm          NUMERIC(8,2),
  num_floors_desc         TEXT,                       -- vd. '2 tầng + sân thượng' (giữ text tự do như mockup)
  frontage_m              NUMERIC(5,2),
  depth_m                 NUMERIC(5,2),
  construction_year       SMALLINT,
  structure_material      TEXT,                       -- vd. 'Bê tông cốt thép, tường gạch'
  house_direction         TEXT,                       -- vd. 'Đông Nam'
  road_type_desc          TEXT,                       -- vd. 'Hẻm bê tông, rộng 3.5m, ô tô vào được'
  alley_width_m           NUMERIC(4,2),
  current_usage_status    TEXT                        -- vd. 'Đang ở, không cho thuê'
);

-- D. Thông tin khoản vay
CREATE TABLE loan_info (
  case_id            TEXT PRIMARY KEY REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  loan_amount_vnd    BIGINT NOT NULL,
  loan_purpose       TEXT,             -- vd. 'Thế chấp vay vốn'
  loan_term_years    SMALLINT
);

-- Nguồn tài liệu đính kèm (upload) — chỉ hiển thị ở màn 1
CREATE TABLE attached_document (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id        TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  file_name      TEXT NOT NULL,
  file_type      TEXT NOT NULL,        -- 'pdf' | 'jpg' | 'png'
  file_size_kb   INTEGER,
  doc_category   document_category NOT NULL DEFAULT 'khac',
  uploaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_attached_document_case_id ON attached_document(case_id);

-- =====================================================================================
-- MÀN 2 — KẾT QUẢ TRA CỨU (Research Agent, 7 tool)
-- =====================================================================================

-- Bảng "Giao dịch so sánh khu vực" (nguồn: market_price_lookup)
CREATE TABLE market_comparable (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id             TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  comp_address        TEXT NOT NULL,
  distance_km         NUMERIC(4,2),
  area_sqm            NUMERIC(8,2),
  transaction_date    DATE,
  price_per_sqm_vnd   BIGINT NOT NULL,
  display_order       SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX idx_market_comparable_case_id ON market_comparable(case_id);

-- 6 lookup-detail card (Quy hoạch / Pháp lý / Tiện ích / Môi trường / Thanh khoản / Dư luận)
-- + có thể thêm 1 dòng category='market_price' để lưu đoạn "Nhận định của PAA" dưới bảng so sánh giá.
CREATE TABLE lookup_finding (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id           TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  category          lookup_category NOT NULL,
  tool_name         TEXT NOT NULL,          -- vd. 'planning_zoning_lookup' — khớp tên tool trong kiến trúc
  status_badge      lookup_badge NOT NULL DEFAULT 'chua_xac_thuc',
  title             TEXT NOT NULL,          -- vd. 'Quy hoạch', 'Pháp lý'...
  raw_findings      TEXT[] NOT NULL DEFAULT '{}',   -- các gạch đầu dòng "Dữ liệu tra cứu được"
  inference_text    TEXT,                   -- "💡 Nhận định của PAA"
  source_label      TEXT,                   -- vd. 'Cổng thông tin quy hoạch đô thị'
  confidence_pct    SMALLINT CHECK (confidence_pct BETWEEN 0 AND 100),
  UNIQUE (case_id, category)
);
CREATE INDEX idx_lookup_finding_case_id ON lookup_finding(case_id);
COMMENT ON TABLE lookup_finding IS '7 nguồn tra cứu của Research Agent — mỗi category tương ứng 1 lookup-detail card ở màn Kết quả tra cứu.';

-- =====================================================================================
-- MÀN 3 — ĐỊNH GIÁ (Valuation Agent)
-- =====================================================================================

CREATE TABLE valuation_result (
  case_id                    TEXT PRIMARY KEY REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  proposed_value_vnd         BIGINT NOT NULL,
  value_range_low_vnd        BIGINT NOT NULL,
  value_range_high_vnd       BIGINT NOT NULL,
  price_per_sqm_vnd          BIGINT,
  confidence_pct             SMALLINT NOT NULL CHECK (confidence_pct BETWEEN 0 AND 100),
  comparable_count           SMALLINT,               -- số giao dịch dùng để định giá
  price_index_period         TEXT,                    -- vd. '2026-Q2'
  price_index_value          NUMERIC(6,2),            -- vd. 118.3
  price_index_base           NUMERIC(6,2) DEFAULT 100,
  confidence_inference_text  TEXT,                    -- nhận định PAA ở khối "Cấu thành độ tin cậy tổng"
  computed_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Chuỗi chỉ số giá theo thời gian (sparkline ở màn 3)
CREATE TABLE valuation_price_index_point (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id      TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  period_label TEXT NOT NULL,          -- vd. '2024-Q1'
  index_value  NUMERIC(6,2) NOT NULL,
  display_order SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX idx_valuation_price_index_point_case_id ON valuation_price_index_point(case_id);

-- 3 phương pháp định giá + bảng "Quy đổi giá trị đề xuất — trọng số kết hợp"
CREATE TABLE valuation_method (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id                TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  method_key             valuation_method_key NOT NULL,
  estimated_value_vnd    BIGINT NOT NULL,
  weight_pct             SMALLINT NOT NULL CHECK (weight_pct BETWEEN 0 AND 100),
  contribution_value_vnd BIGINT,                 -- estimated_value_vnd * weight_pct / 100 (denormalized để hiển thị nhanh)
  method_confidence_pct  SMALLINT CHECK (method_confidence_pct BETWEEN 0 AND 100),
  inputs                 TEXT[] NOT NULL DEFAULT '{}',  -- "Dữ liệu đầu vào" dạng bullet
  inference_text         TEXT,
  source_label           TEXT,
  UNIQUE (case_id, method_key)
);
CREATE INDEX idx_valuation_method_case_id ON valuation_method(case_id);

-- 5 yếu tố cấu thành độ tin cậy định giá (khối "Cấu thành độ tin cậy tổng")
CREATE TABLE valuation_confidence_factor (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id      TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  factor_key   confidence_factor_key NOT NULL,
  label        TEXT NOT NULL,
  weight_pct   SMALLINT NOT NULL CHECK (weight_pct BETWEEN 0 AND 100),
  score        SMALLINT NOT NULL CHECK (score BETWEEN 0 AND 100),
  UNIQUE (case_id, factor_key)
);
CREATE INDEX idx_valuation_confidence_factor_case_id ON valuation_confidence_factor(case_id);

-- =====================================================================================
-- MÀN 4 — RỦI RO (Risk Assessment Agent)
-- =====================================================================================

CREATE TABLE risk_assessment_result (
  case_id             TEXT PRIMARY KEY REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  risk_score          SMALLINT NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
  risk_label          severity_level NOT NULL,
  ltv_proposed_pct    SMALLINT NOT NULL CHECK (ltv_proposed_pct BETWEEN 0 AND 100),
  risk_inference_text TEXT,           -- nhận định PAA ở khối "Quy đổi điểm rủi ro tổng"
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Bảng cấu hình khung LTV theo điểm rủi ro (dữ liệu tĩnh, KHÔNG gắn theo case — dùng chung toàn hệ thống)
CREATE TABLE risk_ltv_policy_band (
  id           SMALLINT PRIMARY KEY,
  min_score    SMALLINT NOT NULL,
  max_score    SMALLINT,              -- NULL = không giới hạn trên (band '>60')
  max_ltv_pct  SMALLINT NOT NULL,
  label        TEXT NOT NULL
);
COMMENT ON TABLE risk_ltv_policy_band IS 'Cấu hình chính sách LTV theo điểm rủi ro tài sản — seed sẵn 4 khung như mockup, chỉnh qua bảng này khi chính sách thay đổi, không cần sửa code.';
INSERT INTO risk_ltv_policy_band (id, min_score, max_score, max_ltv_pct, label) VALUES
  (1, 0,  20,   75, '0–20 điểm → tối đa 75%'),
  (2, 21, 40,   65, '21–40 điểm → tối đa 65%'),
  (3, 41, 60,   55, '41–60 điểm → tối đa 55%'),
  (4, 61, NULL, 45, '>60 điểm → tối đa 45% hoặc cần thẩm định lại');

-- 5 nhóm rủi ro cấu thành (Pháp lý / Thanh khoản / Biến động giá / Vật lý-môi trường / Danh tiếng-tâm linh)
CREATE TABLE risk_group (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id         TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  group_key       risk_group_key NOT NULL,
  label           TEXT NOT NULL,
  weight_pct      SMALLINT NOT NULL CHECK (weight_pct BETWEEN 0 AND 100),
  score           SMALLINT NOT NULL CHECK (score BETWEEN 0 AND 100),
  raw_findings    TEXT[] NOT NULL DEFAULT '{}',
  inference_text  TEXT,
  source_label    TEXT,
  tool_name       TEXT,               -- vd. 'legal_status_lookup' — nhóm rủi ro nào lấy dữ liệu từ tool nào
  UNIQUE (case_id, group_key)
);
CREATE INDEX idx_risk_group_case_id ON risk_group(case_id);

-- "Flags cần lưu ý" (danh sách cảnh báo rút gọn hiển thị cuối màn 4)
CREATE TABLE risk_flag (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id            TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  severity           severity_level NOT NULL,
  title              TEXT NOT NULL,          -- vd. 'Danh tiếng / tâm linh'
  description        TEXT,
  confidence_pct     SMALLINT CHECK (confidence_pct BETWEEN 0 AND 100),
  verified_status    verification_status NOT NULL DEFAULT 'chua_xac_thuc',
  linked_risk_group  UUID REFERENCES risk_group(id) ON DELETE SET NULL,
  display_order      SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX idx_risk_flag_case_id ON risk_flag(case_id);

-- =====================================================================================
-- MÀN 5 — DASHBOARD
-- =====================================================================================

-- "Tổng hợp theo từng bước" — 4 dòng tóm tắt, mỗi dòng có thể bấm "Xem lại" nhảy về đúng subtab
CREATE TABLE dashboard_step_summary (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id       TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  step_number   SMALLINT NOT NULL CHECK (step_number BETWEEN 1 AND 4),
  title         TEXT NOT NULL,
  summary_text  TEXT NOT NULL,
  UNIQUE (case_id, step_number)
);
COMMENT ON TABLE dashboard_step_summary IS 'Có thể sinh động (denormalize lại từ property_physical_info / valuation_result / risk_assessment_result) mỗi khi vào Dashboard, thay vì lưu tĩnh — bảng này phù hợp nếu muốn "đóng băng" nội dung tóm tắt tại thời điểm hoàn tất.';

-- "Trace thực thi PAA" — timeline agent trace (đúng yêu cầu "dashboard hiển thị agent trace")
CREATE TABLE agent_trace_event (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id         TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  seconds_offset  NUMERIC(6,2) NOT NULL,     -- vd. 1.4  (hiển thị dạng "t+1.4s")
  actor           TEXT NOT NULL,             -- vd. 'Research Agent', 'Valuation Agent', 'Planner Agent'
  title           TEXT NOT NULL,             -- vd. 'Bộ máy định giá hoàn tất'
  description     TEXT,
  event_order     SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX idx_agent_trace_event_case_id ON agent_trace_event(case_id);

-- Lịch sử các lần "Xuất báo cáo thẩm định"
CREATE TABLE exported_report (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id         TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  file_name       TEXT NOT NULL,             -- vd. 'BienBan_ThamDinh_REQ-2026-0001.html'
  format          TEXT NOT NULL DEFAULT 'html',
  generated_by    TEXT,                       -- thẩm định viên bấm nút xuất
  generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_exported_report_case_id ON exported_report(case_id);

-- =====================================================================================
-- DÙNG CHUNG MỌI MÀN — luồng "sửa qua form/chat -> chờ xác nhận -> xác nhận" + lịch sử chat
-- =====================================================================================

-- Nhật ký chỉnh sửa: mỗi lần user sửa 1 trường (qua form contenteditable hoặc qua chat),
-- 1 dòng pending được tạo; khi bấm "Xác nhận & Tiếp theo" ở đúng tab đó, dòng chuyển 'confirmed'.
CREATE TABLE case_edit_log (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id          TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  step_number      SMALLINT NOT NULL CHECK (step_number BETWEEN 1 AND 5),
  target_table     TEXT NOT NULL,      -- vd. 'property_physical_info'
  target_field     TEXT NOT NULL,      -- vd. 'land_area_sqm'
  old_value        TEXT,
  new_value        TEXT,
  edit_source      edit_source NOT NULL,
  status           edit_status NOT NULL DEFAULT 'pending',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  confirmed_at     TIMESTAMPTZ
);
CREATE INDEX idx_case_edit_log_case_id ON case_edit_log(case_id);
CREATE INDEX idx_case_edit_log_case_status ON case_edit_log(case_id, status);
COMMENT ON TABLE case_edit_log IS 'Audit trail cho cơ chế highlight xanh dương (pending) -> xanh lá (confirmed) ở mọi màn 1-4. target_table/target_field trỏ tới đúng cột đã bị sửa để phục vụ truy vết.';

-- Toàn bộ tin nhắn trong khung chat (30% bên trái) — phục vụ replay hội thoại + audit
CREATE TABLE chat_message (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id             TEXT NOT NULL REFERENCES appraisal_case(case_id) ON DELETE CASCADE,
  role                chat_role NOT NULL,
  message_text        TEXT NOT NULL,
  related_edit_log_id UUID REFERENCES case_edit_log(id) ON DELETE SET NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_chat_message_case_id ON chat_message(case_id, created_at);

-- =====================================================================================
-- TRIGGER: tự cập nhật appraisal_case.updated_at khi có thay đổi ở các bảng 1:1 chính
-- =====================================================================================

CREATE OR REPLACE FUNCTION paa.touch_case_updated_at() RETURNS TRIGGER AS $$
BEGIN
  UPDATE paa.appraisal_case SET updated_at = now() WHERE case_id = NEW.case_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_touch_case_on_physical_info
  AFTER INSERT OR UPDATE ON property_physical_info
  FOR EACH ROW EXECUTE FUNCTION paa.touch_case_updated_at();

CREATE TRIGGER trg_touch_case_on_valuation
  AFTER INSERT OR UPDATE ON valuation_result
  FOR EACH ROW EXECUTE FUNCTION paa.touch_case_updated_at();

CREATE TRIGGER trg_touch_case_on_risk
  AFTER INSERT OR UPDATE ON risk_assessment_result
  FOR EACH ROW EXECUTE FUNCTION paa.touch_case_updated_at();

-- =====================================================================================
-- VIEW TIỆN DỤNG: danh sách "Lịch sử hồ sơ" hiển thị ở sidebar
-- =====================================================================================

CREATE OR REPLACE VIEW v_case_history AS
SELECT
  c.case_id,
  p.address,
  c.status,
  c.updated_at
FROM appraisal_case c
LEFT JOIN property_physical_info p ON p.case_id = c.case_id
ORDER BY c.updated_at DESC;

-- =====================================================================================
-- VIEW TIỆN DỤNG: 4 thẻ KPI tổng quan ở đầu màn Dashboard (không cần lưu trùng dữ liệu)
-- =====================================================================================

CREATE OR REPLACE VIEW v_dashboard_kpi AS
SELECT
  v.case_id,
  v.proposed_value_vnd,
  v.value_range_low_vnd,
  v.value_range_high_vnd,
  v.confidence_pct        AS valuation_confidence_pct,
  r.risk_score,
  r.risk_label,
  r.ltv_proposed_pct
FROM valuation_result v
JOIN risk_assessment_result r ON r.case_id = v.case_id;
