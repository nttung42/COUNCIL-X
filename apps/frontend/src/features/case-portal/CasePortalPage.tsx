import { href } from '../../app/routes';
import { APPRAISAL_CASE_ID, DEMO_CASE_ID, workflowSteps } from '../../app/workflowSteps';

export function CasePortalPage() {
  return (
    <div className="portal-body">
      <div className="portal-topbar">
        <img className="mark" src="/logo.png" alt="SHB" />
        <div className="ptitle">
          Hệ thống Thẩm định Tín dụng AI
          <small>Digital Credit Appraisal Suite — chọn vai trò để vào đúng màn hình làm việc</small>
        </div>
      </div>

      <div className="portal-hero">
        <h1>Chọn nghiệp vụ để bắt đầu</h1>
        <p>
          Mỗi màn hình tương ứng một bước xử lý hồ sơ. Tên URL, route, page và component dùng ngôn ngữ nghiệp vụ;
          không dùng tên phase. Màn <b>Định giá tài sản bảo đảm</b> dùng implementation React hiện có.
        </p>
      </div>

      <div className="portal-wrap">
        <div className="portal-section-title">Luồng xử lý 1 hồ sơ tín dụng</div>
        <div className="pipeline-strip">
          {workflowSteps.map((step, index) => (
            <span key={step.routeId} className="pipeline-item-wrap">
              {index > 0 && <span className="arrow">→</span>}
              <a href={href(step.routeId, step.caseId ? { caseId: step.caseId } : undefined)}>{step.shortLabel} · {step.label}</a>
            </span>
          ))}
        </div>

        <div className="portal-section-title">Hồ sơ demo đang có</div>
        <div className="case-grid">
          <div className="case-card">
            <div className="cc-head"><span className="cc-name">Cty TNHH ABC</span><span className="cc-code">{DEMO_CASE_ID}</span></div>
            <div className="cc-desc">Vay bổ sung vốn lưu động 5 tỷ · 24 tháng. Dùng cho intake, screening, financial, legal, underwriting, approval, disbursement, monitoring.</div>
            <div className="cc-stage"><span className="dot-mark warning" />Đang xử lý · <a href={href('caseIntake', { caseId: DEMO_CASE_ID })}>Mở hồ sơ →</a></div>
          </div>
          <div className="case-card">
            <div className="cc-head"><span className="cc-name">Nguyễn Văn A</span><span className="cc-code">{APPRAISAL_CASE_ID}</span></div>
            <div className="cc-desc">Thế chấp vay vốn 3.2 tỷ · nhà phố Q.C. Hồ sơ demo cho Định giá tài sản bảo đảm.</div>
            <div className="cc-stage"><span className="dot-mark good" />Đã hoàn tất định giá · <a href={href('collateralAppraisal', { caseId: APPRAISAL_CASE_ID })}>Mở hồ sơ TSBĐ →</a></div>
          </div>
        </div>

        <div className="portal-section-title">Vào theo vai trò</div>
        <div className="role-grid">
          {workflowSteps.map((step) => (
            <a key={step.routeId} className={'role-card' + (step.routeId === 'collateralAppraisal' ? ' mvp' : '')} href={href(step.routeId, step.caseId ? { caseId: step.caseId } : undefined)}>
              <div className="rc-top">
                <div className="rc-ic">{step.icon}</div>
                <div>
                  <div className="rc-name">{step.role}</div>
                  <div className="rc-phase">{step.label}</div>
                </div>
              </div>
              <div className="rc-desc">Vào màn hình {step.label.toLowerCase()} cho hồ sơ demo.</div>
              <div className="rc-foot"><span className="rc-ai">Assistant</span><span className="rc-go">Vào màn hình →</span></div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
