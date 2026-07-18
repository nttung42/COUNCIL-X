export function LandingPage() {
  return (
    <main className="landing-page" aria-labelledby="landing-title">
      <header className="landing-nav">
        <a className="landing-brand" href="/" aria-label="Credit AI home">
          <img className="brand-logo" src="/logo.png" alt="SHB" />
          <span>
            Credit AI
            <small>Digital appraisal suite</small>
          </span>
        </a>
        <a className="landing-login-btn" href="/cases">
          Đăng nhập
        </a>
      </header>

      <section className="landing-hero">
        <div className="landing-copy">
          <div className="eyebrow">SME Credit Appraisal Platform</div>
          <h1 id="landing-title">Thẩm định tín dụng nhanh hơn, nhất quán hơn, có dấu vết hơn.</h1>
          <p>
            Bộ công cụ AI hỗ trợ tiếp nhận hồ sơ, sàng lọc điều kiện, thẩm định tài chính/pháp lý, định giá tài sản bảo đảm,
            phê duyệt, giải ngân và giám sát sau vay.
          </p>
          <div className="landing-actions">
            <a className="primary-btn landing-cta" href="/cases">
              Đăng nhập để vào hệ thống
            </a>
            <a className="landing-secondary" href="/cases/REQ-2026-00458/intake">
              Xem hồ sơ demo
            </a>
          </div>
        </div>

        <div className="landing-card" aria-label="Tóm tắt nền tảng">
          <div className="landing-card-head">
            <span>Live case</span>
            <strong>REQ-2026-00458</strong>
          </div>
          <div className="landing-score">
            <span>Readiness score</span>
            <strong>82%</strong>
          </div>
          <div className="landing-progress"><span /></div>
          <div className="landing-checklist">
            <span>✓ Hồ sơ đã số hoá</span>
            <span>✓ Dữ liệu tài chính đã đối chiếu</span>
            <span>✓ Cảnh báo pháp lý đã gắn nguồn</span>
            <span>• Chờ phản biện tín dụng</span>
          </div>
        </div>
      </section>
    </main>
  );
}
