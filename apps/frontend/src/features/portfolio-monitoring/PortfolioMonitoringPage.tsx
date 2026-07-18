import { WorkflowPageLayout } from '../../app/layout/AppLayout';
import { navigate } from '../../app/routes';
import { DEMO_CASE_ID } from '../../app/workflowSteps';
import { Card, StatTile } from '../../components/common/ui';

const alerts = [
  {
    tone: 'critical',
    name: 'Cty DEF',
    text: 'Dư nợ 8 tỷ · Sụt số dư tài khoản 70% trong 30 ngày.',
    evidence: 'Core Banking transaction monitoring · 17/07/2026',
    rule: 'Critical nếu số dư tài khoản giảm > 60% trong 30 ngày.',
    action: 'Giao RM kiểm tra dòng tiền và cập nhật kế hoạch thu nợ.',
  },
  {
    tone: 'warning',
    name: 'Cty ABC',
    text: 'Dư nợ 3.5 tỷ · Trễ kỳ trả lãi 5 ngày; nhắc nhở tự động đã gửi.',
    evidence: 'Lịch trả nợ · EWS 15/07/2026',
    rule: 'Warn nếu trễ lãi > 3 ngày.',
    action: 'Theo dõi phản hồi khách hàng trong 48 giờ.',
  },
  {
    tone: 'warning',
    name: 'Cty GHI',
    text: 'Dư nợ 12 tỷ · Ngành thép biến động mạnh; xem xét tái thẩm định.',
    evidence: 'Industry signal feed · EWS 12/07/2026',
    rule: 'Warn nếu ngành có volatility index vượt ngưỡng nội bộ.',
    action: 'Xem xét tái thẩm định theo ngành.',
  },
];

export function PortfolioMonitoringPage() {
  return (
    <WorkflowPageLayout defaultPane="info">
      <div className="info-pane" style={{ flex: 1 }}>
        <div className="review-banner"><span className="ic">⚡</span>Giám sát danh mục — Tháng 07/2026 · 3 cảnh báo cần xử lý.</div>
        <div className="info-content">
          <div className="process-summary">
            <div>
              <b>Monitoring complete</b>
              <span>4 signals checked · 3 alerts</span>
            </div>
            <details>
              <summary>View checks</summary>
              <div className="flow-progress">
                {['Cash-flow signal checked', 'Repayment schedule checked', 'Industry signal checked', 'Dashboard aggregated'].map((step) => (
                  <div key={step} className="flow-step done"><span className="flow-ic">✓</span>{step}</div>
                ))}
              </div>
            </details>
          </div>

          <Card>
            <div className="subtab-bar portfolio-tabs">
              <button type="button" className="subtab-btn active">Tất cả <span className="n">3</span></button>
              <button type="button" className="subtab-btn">Cảnh báo sớm <span className="n">2</span></button>
              <button type="button" className="subtab-btn">Quá hạn <span className="n">1</span></button>
              <button type="button" className="subtab-btn">Cần hành động <span className="n">3</span></button>
            </div>
            <div className="section-h">Cảnh báo sớm</div>
            {alerts.map((alert) => (
              <div key={alert.name} className="flag-row">
                <span className={`badge ${alert.tone}`}><span className="dot" />{alert.tone === 'critical' ? 'Cao' : 'Trung bình'}</span>
                <div>
                  <b>{alert.name}</b>
                  <p>{alert.text}</p>
                  <div className="evidence-grid">
                    <span><b>Evidence</b>{alert.evidence}</span>
                    <span><b>Rule</b>{alert.rule}</span>
                    <span><b>Action</b>{alert.action}</span>
                  </div>
                </div>
                <div className="ews-actions">
                  <button type="button" className="footer-back-btn">Xem chi tiết</button>
                  <button type="button" className="footer-back-btn">Giao việc RM</button>
                  <button type="button" className="primary-btn" onClick={() => navigate('financialReview', { caseId: DEMO_CASE_ID })}>Tái thẩm định →</button>
                </div>
              </div>
            ))}
          </Card>

          <div className="grid c4 portfolio-summary">
            <StatTile label="Tổng dư nợ danh mục" value="186 tỷ" sub="42 khách hàng đang giám sát" />
            <StatTile label="Cảnh báo đỏ" value={<span style={{ color: 'var(--danger)' }}>1</span>} sub="Cần hành động ngay" />
            <StatTile label="Cảnh báo vàng" value={<span style={{ color: 'var(--warning)' }}>2</span>} sub="Theo dõi sát" />
            <StatTile label="Nhắc nhở tự động" value="14" sub="Trong tháng 07/2026" />
          </div>
        </div>
        <div className="info-footer">
          <div className="footer-hint">Danh mục đã quét xong; có thể giao việc hoặc tái thẩm định hồ sơ rủi ro.</div>
          <div className="footer-btns">
            <button type="button" className="footer-back-btn" onClick={() => navigate('loanDisbursement', { caseId: DEMO_CASE_ID })}>← Về hỗ trợ tín dụng</button>
            <button type="button" className="primary-btn">Quét lại danh mục</button>
          </div>
        </div>
      </div>
    </WorkflowPageLayout>
  );
}
