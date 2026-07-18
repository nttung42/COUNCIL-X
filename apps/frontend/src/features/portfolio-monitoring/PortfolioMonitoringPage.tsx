import { WorkflowPageLayout } from '../../app/layout/AppLayout';
import { navigate } from '../../app/routes';
import { DEMO_CASE_ID } from '../../app/workflowSteps';
import { Card, StatTile } from '../../components/common/ui';

const alerts = [
  { tone: 'critical', name: 'Cty DEF', text: 'Dư nợ 8 tỷ · Sụt số dư tài khoản 70% trong 30 ngày.', meta: 'EWS phát hiện 17/07/2026 · Core Banking transaction monitoring' },
  { tone: 'warning', name: 'Cty ABC', text: 'Dư nợ 3.5 tỷ · Trễ kỳ trả lãi 5 ngày; nhắc nhở tự động đã gửi.', meta: 'EWS phát hiện 15/07/2026 · Lịch trả nợ' },
  { tone: 'warning', name: 'Cty GHI', text: 'Dư nợ 12 tỷ · Ngành thép biến động mạnh; xem xét tái thẩm định.', meta: 'EWS phát hiện 12/07/2026 · Tín hiệu ngành' },
];

export function PortfolioMonitoringPage() {
  return (
    <WorkflowPageLayout defaultPane="info">
      <div className="info-pane" style={{ flex: 1 }}>
        <div className="review-banner"><span className="ic">⚡</span>Giám sát danh mục — Tháng 07/2026 · EWS phát hiện 3 cảnh báo cần chú ý.</div>
        <div className="info-content">
          <div className="flow-progress">
            {['Tín hiệu dòng tiền', 'Lịch trả nợ', 'Tín hiệu ngành & thị trường', 'Tổng hợp dashboard'].map((step, index) => (
              <div key={step} className="flow-step done"><span className="flow-ic">{index + 1}</span>{step}</div>
            ))}
          </div>

          <Card>
            <div className="subtab-bar portfolio-tabs">
              <button type="button" className="subtab-btn active">Tất cả <span className="n">3</span></button>
              <button type="button" className="subtab-btn">Cảnh báo sớm <span className="n">2</span></button>
              <button type="button" className="subtab-btn">Quá hạn <span className="n">1</span></button>
              <button type="button" className="subtab-btn">Cần hành động <span className="n">3</span></button>
            </div>
            <div className="section-h">Cảnh báo sớm AI phát hiện</div>
            {alerts.map((alert) => (
              <div key={alert.name} className="flag-row">
                <span className={`badge ${alert.tone}`}><span className="dot" />{alert.tone === 'critical' ? 'Cao' : 'Trung bình'}</span>
                <div style={{ flex: 1 }}>
                  <b>{alert.name}</b>
                  <p>{alert.text}</p>
                  <div className="meta">{alert.meta}</div>
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
            <StatTile label="Cảnh báo đỏ" value={<span style={{ color: 'var(--critical)' }}>1</span>} sub="Cần hành động ngay" />
            <StatTile label="Cảnh báo vàng" value={<span style={{ color: '#8a6100' }}>2</span>} sub="Theo dõi sát" />
            <StatTile label="Nhắc nhở tự động" value="14" sub="Trong tháng 07/2026" />
          </div>
        </div>
        <div className="info-footer">
          <div className="footer-hint">Danh mục đã quét xong; có thể giao việc hoặc tái thẩm định hồ sơ rủi ro.</div>
          <div className="footer-btns">
            <button type="button" className="footer-back-btn" onClick={() => navigate('loanDisbursement', { caseId: DEMO_CASE_ID })}>↩ Về hỗ trợ tín dụng</button>
            <button type="button" className="primary-btn">Quét lại danh mục</button>
          </div>
        </div>
      </div>
    </WorkflowPageLayout>
  );
}
