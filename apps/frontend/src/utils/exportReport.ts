import type { AppraisalCaseFull } from '../types';
import { SEVERITY_LABEL } from './severity';

// Sinh nội dung HTML của biên bản thẩm định từ dữ liệu hồ sơ hiện có, y hệt buildReportHtml()
// trong ai/PAA_Mockup_SHB_8.html — không cần backend, tải trực tiếp về máy dưới dạng .html.
export function buildReportHtml(caseData: AppraisalCaseFull): string {
  const address = caseData.physical.address.value;
  const area = caseData.physical.landAreaSqm.value;
  const bdsType = caseData.physical.propertyType.value;

  const { valuation, risk } = caseData;
  const riskLabel = SEVERITY_LABEL[risk.riskLabel].toUpperCase();
  const today = new Date().toLocaleDateString('vi-VN');

  return (
    '<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">' +
    '<title>Bien ban tham dinh - ' +
    caseData.caseId +
    '</title>' +
    '<style>' +
    'body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#151A2E;max-width:760px;margin:32px auto;padding:0 20px;line-height:1.6;}' +
    '.hd{display:flex;align-items:center;gap:12px;border-bottom:3px solid #1E2F66;padding-bottom:14px;margin-bottom:20px;}' +
    '.hd .mark{width:38px;height:38px;border-radius:9px;background:#F2701C;color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;}' +
    '.hd h1{font-size:16px;margin:0;color:#1E2F66;}' +
    '.hd .sub{font-size:11.5px;color:#5B6478;margin-top:2px;}' +
    'h2{font-size:13px;color:#1E2F66;border-left:3px solid #C24E0E;padding-left:8px;margin:22px 0 8px;}' +
    'table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:6px;}' +
    'td,th{padding:6px 8px;border-bottom:1px solid #ECE9E3;text-align:left;}' +
    'th{color:#5B6478;font-weight:700;font-size:10.5px;text-transform:uppercase;}' +
    '.kpi{display:flex;gap:14px;flex-wrap:wrap;margin-top:8px;}' +
    '.kpi div{background:#F1F3FA;border-radius:10px;padding:10px 14px;min-width:130px;}' +
    '.kpi .l{font-size:10.5px;color:#5B6478;}' +
    '.kpi .v{font-size:17px;font-weight:700;color:#1E2F66;}' +
    '.note{background:#FEF1E7;border-radius:8px;padding:10px 12px;font-size:12px;color:#151A2E;margin-top:8px;}' +
    '.sig{margin-top:32px;padding-top:14px;border-top:1px dashed #ECE9E3;font-size:11.5px;color:#5B6478;}' +
    '.ft{margin-top:26px;font-size:10.5px;color:#8A93A8;}' +
    '</style></head><body>' +
    '<div class="hd"><div class="mark">SHB</div><div><h1>BIÊN BẢN THẨM ĐỊNH TÀI SẢN BẢO ĐẢM</h1>' +
    '<div class="sub">Mã hồ sơ ' +
    caseData.caseId +
    ' · Xuất báo cáo ngày ' +
    today +
    '</div></div></div>' +
    '<h2>I. Thông tin tài sản</h2>' +
    '<table><tr><td style="width:32%;color:#5B6478;">Địa chỉ</td><td>' +
    address +
    '</td></tr>' +
    '<tr><td style="color:#5B6478;">Loại BĐS</td><td>' +
    bdsType +
    '</td></tr>' +
    '<tr><td style="color:#5B6478;">Diện tích đất</td><td>' +
    area +
    '</td></tr></table>' +
    '<h2>II. Kết quả tra cứu khu vực</h2>' +
    '<p style="font-size:12.5px;">7 nguồn tra cứu (giá thị trường, quy hoạch, pháp lý, tiện ích, môi trường, thanh khoản, dư luận) đã hoàn tất. Phát hiện 1 điểm cần lưu ý: tin đồn dân cư khu vực liên quan sự việc 2019, độ tin cậy nguồn tin thấp (30%) — khuyến nghị xác minh thực địa.</p>' +
    '<h2>III. Định giá</h2>' +
    '<div class="kpi"><div><div class="l">Giá trị đề xuất</div><div class="v">' +
    valuation.proposedValueLabel +
    '</div></div>' +
    '<div><div class="l">Khoảng tin cậy</div><div class="v" style="font-size:13px;">' +
    valuation.valueRangeLabel +
    '</div></div>' +
    '<div><div class="l">Độ tin cậy</div><div class="v">' +
    valuation.confidencePct +
    '%</div></div></div>' +
    '<p style="font-size:12.5px;">Kết hợp 3 phương pháp: so sánh trực tiếp (50%), hedonic/ML (30%), chi phí xây dựng (20%).</p>' +
    '<h2>IV. Đánh giá rủi ro &amp; LTV</h2>' +
    '<div class="kpi"><div><div class="l">Điểm rủi ro tài sản</div><div class="v">' +
    risk.riskScore +
    '/100</div></div>' +
    '<div><div class="l">Xếp loại</div><div class="v" style="font-size:13px;">' +
    riskLabel +
    '</div></div>' +
    '<div><div class="l">LTV đề xuất</div><div class="v">' +
    risk.ltvProposedPct +
    '%</div></div></div>' +
    '<p style="font-size:12.5px;">5 nhóm rủi ro cấu thành: Pháp lý (30%), Thanh khoản (25%), Biến động giá (20%), Vật lý/môi trường (15%), Danh tiếng/tâm linh (10%).</p>' +
    '<h2>V. Khuyến nghị</h2>' +
    '<div class="note">Cần thẩm định viên xác minh thực địa tin đồn dân cư (2019) trước khi hoàn tất hồ sơ chính thức. Khuyến nghị khách hàng mua bảo hiểm tài sản do khu vực từng ghi nhận ngập nhẹ cục bộ 2022–2023.</div>' +
    '<div class="sig">☐ Chữ ký thẩm định viên &nbsp;&nbsp;&nbsp;&nbsp; ☐ Xác nhận chuyên viên tín dụng</div>' +
    '<div class="ft">Báo cáo được PAA (Property Appraisal Agent) tạo tự động từ dữ liệu đã tra cứu, định giá và đánh giá rủi ro trong phiên làm việc — thẩm định viên rà soát và xác nhận trước khi sử dụng chính thức.</div>' +
    '</body></html>'
  );
}

export function downloadStandaloneReport(caseData: AppraisalCaseFull): void {
  const html = buildReportHtml(caseData);
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `BienBan_ThamDinh_${caseData.caseId}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
