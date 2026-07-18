import { WorkflowNav } from '../../app/layout/WorkflowNav';
import { href } from '../../app/routes';
import { APPRAISAL_CASE_ID, DEMO_CASE_ID, workflowSteps } from '../../app/workflowSteps';

export function CasePortalPage() {
  return (
    <div className="page-shell portal-shell">
      <WorkflowNav />
      <main className="portal-body">
        <section className="portal-hero">
          <h1>Cổng điều phối thẩm định tín dụng</h1>
          <p>
            Mở nhanh hồ sơ demo, đi theo vai trò nghiệp vụ hoặc xem toàn bộ luồng xử lý trước khi vào màn hình làm việc.
          </p>
        </section>

        <div className="portal-wrap">
          <div className="grid c3 portal-stats">
            <div className="card stat-tile">
              <div className="label">Luồng xử lý</div>
              <div className="value">{workflowSteps.length}</div>
              <div className="sub">bước nghiệp vụ</div>
            </div>
            <div className="card stat-tile">
              <div className="label">Hồ sơ demo</div>
              <div className="value">2</div>
              <div className="sub">doanh nghiệp và cá nhân</div>
            </div>
            <div className="card stat-tile">
              <div className="label">Kịch bản</div>
              <div className="value">1</div>
              <div className="sub">luồng end-to-end</div>
            </div>
          </div>

          <div className="portal-section-title">Luồng xử lý 1 hồ sơ tín dụng</div>
          <div className="pipeline-strip">
            {workflowSteps.map((step, index) => (
              <span key={step.routeId} className="pipeline-item-wrap">
                {index > 0 && <span className="arrow">→</span>}
                <a href={href(step.routeId, step.caseId ? { caseId: step.caseId } : undefined)}>
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  {step.label}
                  <small>{step.role}</small>
                </a>
              </span>
            ))}
          </div>

          <div className="portal-section-title">Hồ sơ demo đang có</div>
          <div className="case-grid">
            <a className="case-card" href={href('caseIntake', { caseId: DEMO_CASE_ID })} aria-label="Mở hồ sơ Cty TNHH ABC">
              <div className="cc-head">
                <span className="cc-name">Cty TNHH ABC</span>
                <span className="cc-code">{DEMO_CASE_ID}</span>
              </div>
              <div className="cc-desc">
                Vay bổ sung vốn lưu động 5 tỷ · 24 tháng. Dùng cho tiếp nhận, sàng lọc, thẩm định, phê duyệt, giải ngân và giám sát.
              </div>
              <div className="cc-stage">
                <span className="badge warning"><span className="dot" />Đang xử lý</span>
                <span className="rc-go">Mở luồng tiếp nhận →</span>
              </div>
            </a>
            <a className="case-card" href={href('collateralAppraisal', { caseId: APPRAISAL_CASE_ID })} aria-label="Mở hồ sơ Nguyễn Văn A">
              <div className="cc-head">
                <span className="cc-name">Nguyễn Văn A</span>
                <span className="cc-code">{APPRAISAL_CASE_ID}</span>
              </div>
              <div className="cc-desc">Thế chấp vay vốn 3.2 tỷ · nhà phố Q.C. Hồ sơ demo cho nghiệp vụ định giá tài sản bảo đảm.</div>
              <div className="cc-stage">
                <span className="badge good"><span className="dot" />Đã hoàn tất định giá</span>
                <span className="rc-go">Mở định giá TSBĐ →</span>
              </div>
            </a>
          </div>

          <div className="portal-section-title">Vào theo vai trò</div>
          <div className="role-grid">
            {workflowSteps.map((step) => (
              <a key={step.routeId} className={'role-card' + (step.routeId === 'collateralAppraisal' ? ' mvp' : '')} href={href(step.routeId, step.caseId ? { caseId: step.caseId } : undefined)}>
                <div className="rc-top">
                  <div className="rc-ic">{step.icon}</div>
                  <div>
                    <div className="rc-name">{step.label}</div>
                    <div className="rc-phase">{step.role}</div>
                  </div>
                </div>
                <div className="rc-desc">Vào màn hình {step.label.toLowerCase()} cho hồ sơ demo.</div>
                <div className="rc-foot"><span className="rc-ai">Trợ lý {step.label.toLowerCase()}</span><span className="rc-go">Vào màn hình nghiệp vụ →</span></div>
              </a>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
