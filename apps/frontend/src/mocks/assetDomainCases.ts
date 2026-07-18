import { CASE_ID } from './fixtureCase';

export type AssetDomainId = 'real_estate' | 'movable_assets' | 'valuable_papers' | 'property_rights';
export type AssetCaseStatus = 'not_started' | 'processing' | 'waiting_for_data' | 'waiting_for_review' | 'completed' | 'blocked' | 'inconclusive';
export type AssetRiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type FindingTone = 'good' | 'warning' | 'serious' | 'critical';

export interface AssetMetric {
  label: string;
  value: string;
  sub: string;
  tone?: string;
}

export interface AssetFinding {
  id: string;
  title: string;
  tone: FindingTone;
  description: string;
  evidence: string;
  rule: string;
  action: string;
  confidence: string;
  humanStatus: 'pending' | 'confirmed' | 'rejected';
}

export interface AssetEvidence {
  id: string;
  title: string;
  source: string;
  confidence: string;
  usedIn: string;
  status: 'Chờ xác nhận' | 'Đã xác nhận' | 'Cần bổ sung';
}

export interface CollateralCaseSummary {
  caseId: string;
  domainId: AssetDomainId;
  domainLabel: string;
  assetSubtype: string;
  assetName: string;
  owner: string;
  location: string;
  status: AssetCaseStatus;
  riskLevel: AssetRiskLevel;
  confidencePct: number;
  valueLabel: string;
  nextAction: string;
  findingsCount: number;
  blockerCount: number;
  evidenceCoveragePct: number;
}

export interface AssetDomainConfig {
  domainId: AssetDomainId;
  routeId: 'realEstateAppraisal' | 'movableAssetsAppraisal' | 'valuablePapersAppraisal' | 'propertyRightsAppraisal';
  label: string;
  subtitle: string;
  statusLabel: string;
  caseId: string;
  assetName: string;
  assetSubtype: string;
  owner: string;
  steps: string[];
  metrics: AssetMetric[];
  findings: AssetFinding[];
  evidence: AssetEvidence[];
  calculation: {
    title: string;
    columns: string[];
    rows: string[][];
  };
  reportSections: string[];
}

export const STATUS_LABEL: Record<AssetCaseStatus, string> = {
  not_started: 'Chưa bắt đầu',
  processing: 'Đang xử lý',
  waiting_for_data: 'Chờ dữ liệu',
  waiting_for_review: 'Chờ human review',
  completed: 'Hoàn tất',
  blocked: 'Blocked',
  inconclusive: 'Không kết luận được',
};

export const RISK_LABEL: Record<AssetRiskLevel, string> = {
  low: 'Thấp',
  medium: 'Trung bình',
  high: 'Cao',
  critical: 'Nghiêm trọng',
};

export const RISK_TONE: Record<AssetRiskLevel, FindingTone> = {
  low: 'good',
  medium: 'warning',
  high: 'serious',
  critical: 'critical',
};

export const collateralCases: CollateralCaseSummary[] = [
  {
    caseId: CASE_ID,
    domainId: 'real_estate',
    domainLabel: 'Bất động sản',
    assetSubtype: 'Nhà phố',
    assetName: 'Nhà phố hẻm 45 Nguyễn Văn A',
    owner: 'Nguyễn Văn A',
    location: 'Phường B, Quận C',
    status: 'waiting_for_review',
    riskLevel: 'medium',
    confidencePct: 78,
    valueLabel: '4.85 tỷ',
    nextAction: 'Xác nhận kết quả định giá BĐS',
    findingsCount: 3,
    blockerCount: 0,
    evidenceCoveragePct: 87,
  },
  {
    caseId: 'MV-2026-0002',
    domainId: 'movable_assets',
    domainLabel: 'Động sản',
    assetSubtype: 'Xe tải',
    assetName: 'Xe tải Hino 8 tấn',
    owner: 'Công ty TNHH ABC Logistics',
    location: 'Kho Bình Tân, TP.HCM',
    status: 'waiting_for_data',
    riskLevel: 'high',
    confidencePct: 72,
    valueLabel: '780 triệu',
    nextAction: 'Bổ sung ảnh số khung/số máy',
    findingsCount: 2,
    blockerCount: 1,
    evidenceCoveragePct: 64,
  },
  {
    caseId: 'SEC-2026-0001',
    domainId: 'valuable_papers',
    domainLabel: 'Giấy tờ có giá',
    assetSubtype: 'Trái phiếu',
    assetName: 'Trái phiếu XYZ2028',
    owner: 'Công ty TNHH ABC',
    location: 'Lưu ký VSDC',
    status: 'processing',
    riskLevel: 'medium',
    confidencePct: 81,
    valueLabel: '7.7 tỷ',
    nextAction: 'Rà soát haircut thanh khoản',
    findingsCount: 2,
    blockerCount: 0,
    evidenceCoveragePct: 79,
  },
  {
    caseId: 'PR-2026-0001',
    domainId: 'property_rights',
    domainLabel: 'Quyền tài sản',
    assetSubtype: 'Quyền đòi nợ',
    assetName: 'Quyền đòi nợ HĐ-2026-15',
    owner: 'Công ty TNHH ABC',
    location: 'Hợp đồng thương mại nội địa',
    status: 'waiting_for_review',
    riskLevel: 'high',
    confidencePct: 68,
    valueLabel: '8.6 tỷ',
    nextAction: 'Xác nhận loại trừ khoản quá hạn >90 ngày',
    findingsCount: 3,
    blockerCount: 1,
    evidenceCoveragePct: 71,
  },
];

export const assetDomainConfigs: Record<Exclude<AssetDomainId, 'real_estate'>, AssetDomainConfig> = {
  movable_assets: {
    domainId: 'movable_assets',
    routeId: 'movableAssetsAppraisal',
    label: 'Động sản',
    subtitle: 'Xe, máy móc thiết bị, hàng tồn kho và tài sản hữu hình có thể di chuyển.',
    statusLabel: 'Đã cấu hình khung thẩm định',
    caseId: 'MV-2026-0002',
    assetName: 'Xe tải Hino 8 tấn',
    assetSubtype: 'Phương tiện vận tải',
    owner: 'Công ty TNHH ABC Logistics',
    steps: ['Nhận diện tài sản', 'Quyền sở hữu & hạn chế', 'Tình trạng tài sản', 'Giá thị trường', 'Khấu hao', 'Thanh khoản & định giá', 'Báo cáo'],
    metrics: [
      { label: 'Giá trị thị trường', value: '780 triệu', sub: 'Theo dữ liệu xe tương đồng' },
      { label: 'Giá trị thanh lý', value: '620 triệu', sub: 'Sau haircut thanh khoản', tone: 'var(--warning)' },
      { label: 'Haircut đề xuất', value: '25%', sub: 'Tình trạng + thanh khoản' },
      { label: 'Confidence', value: '72%', sub: 'Cần xác minh serial', tone: 'var(--warning)' },
    ],
    findings: [
      {
        id: 'mv-serial',
        title: 'Serial cần xác minh lại',
        tone: 'critical',
        description: 'Ảnh số khung hiện trường chưa đủ nét để khớp chắc chắn với hồ sơ đăng ký.',
        evidence: 'Giấy đăng ký xe.pdf; ảnh số khung hiện trường',
        rule: 'Serial/số khung/số máy phải khớp hồ sơ sở hữu trước khi nhận bảo đảm.',
        action: 'Yêu cầu chụp lại số khung/số máy và cán bộ thực địa xác nhận.',
        confidence: 'Medium · image quality low',
        humanStatus: 'pending',
      },
      {
        id: 'mv-depreciation',
        title: 'Khấu hao vận hành cao hơn chuẩn',
        tone: 'warning',
        description: 'Xe chạy 190.000km, cao hơn trung vị cùng đời xe khoảng 22%.',
        evidence: 'Odometer photo; maintenance log',
        rule: 'Tăng haircut nếu mức sử dụng vượt ngưỡng nhóm tài sản.',
        action: 'Áp dụng haircut bổ sung 5% hoặc yêu cầu biên bản bảo dưỡng gần nhất.',
        confidence: 'High · odometer visible',
        humanStatus: 'pending',
      },
    ],
    evidence: [
      { id: 'mv-ev-1', title: 'Giấy đăng ký xe', source: 'dang-ky-xe.pdf', confidence: '92%', usedIn: 'Quyền sở hữu', status: 'Đã xác nhận' },
      { id: 'mv-ev-2', title: 'Ảnh số khung', source: 'anh-so-khung.jpg', confidence: '54%', usedIn: 'Nhận diện tài sản', status: 'Cần bổ sung' },
      { id: 'mv-ev-3', title: 'Bảng giá xe tương đồng', source: 'market_vehicle_lookup', confidence: '76%', usedIn: 'Định giá', status: 'Chờ xác nhận' },
    ],
    calculation: {
      title: 'Khấu hao và giá trị bảo đảm',
      columns: ['Yếu tố', 'Tỷ lệ', 'Lý do', 'Human edit'],
      rows: [
        ['Hao mòn vật lý', '12%', 'Tuổi xe và km vận hành', 'No'],
        ['Lỗi thời kỹ thuật', '4%', 'Đời xe cũ hơn chuẩn thị trường', 'No'],
        ['Thanh khoản', '9%', 'Thời gian bán dự kiến 75 ngày', 'Pending'],
      ],
    },
    reportSections: ['Hồ sơ tài sản', 'Quyền sở hữu', 'Tình trạng', 'Dữ liệu thị trường', 'Khấu hao', 'Thanh khoản', 'Giá trị', 'Evidence', 'Giới hạn'],
  },
  valuable_papers: {
    domainId: 'valuable_papers',
    routeId: 'valuablePapersAppraisal',
    label: 'Giấy tờ có giá',
    subtitle: 'Trái phiếu, cổ phiếu, chứng chỉ tiền gửi, kỳ phiếu và công cụ đủ điều kiện nhận bảo đảm.',
    statusLabel: 'Đã cấu hình khung thẩm định',
    caseId: 'SEC-2026-0001',
    assetName: 'Trái phiếu XYZ2028',
    assetSubtype: 'Trái phiếu doanh nghiệp',
    owner: 'Công ty TNHH ABC',
    steps: ['Hồ sơ công cụ', 'Quyền sở hữu & xác thực', 'Rủi ro tổ chức phát hành', 'Khả năng giao dịch', 'Định giá', 'Haircut', 'Báo cáo'],
    metrics: [
      { label: 'Mệnh giá', value: '10 tỷ', sub: '100.000 trái phiếu' },
      { label: 'Giá thị trường', value: '9.4 tỷ', sub: 'Marked-to-market' },
      { label: 'Haircut tổng', value: '18%', sub: 'Issuer + liquidity + tenor', tone: 'var(--warning)' },
      { label: 'Giá trị bảo đảm', value: '7.7 tỷ', sub: 'Sau haircut' },
    ],
    findings: [
      {
        id: 'sec-liquidity',
        title: 'Thanh khoản thấp',
        tone: 'warning',
        description: 'Khối lượng giao dịch trung bình thấp, bid–ask spread cao hơn nhóm tham chiếu.',
        evidence: 'Market data feed; exchange snapshot',
        rule: 'Tăng haircut thanh khoản nếu số ngày bán dự kiến > 10 ngày giao dịch.',
        action: 'Áp dụng haircut thanh khoản 8% và theo dõi lại khi thị trường biến động.',
        confidence: 'High · direct market feed',
        humanStatus: 'pending',
      },
      {
        id: 'sec-issuer',
        title: 'Issuer có cảnh báo outlook',
        tone: 'serious',
        description: 'Tổ chức phát hành bị chuyển triển vọng từ ổn định sang tiêu cực trong kỳ gần nhất.',
        evidence: 'Rating agency bulletin',
        rule: 'Cảnh báo nếu outlook bị hạ trong 12 tháng gần nhất.',
        action: 'Yêu cầu Risk xác nhận mức haircut tín dụng.',
        confidence: 'Medium · depends on latest rating feed',
        humanStatus: 'pending',
      },
    ],
    evidence: [
      { id: 'sec-ev-1', title: 'Xác nhận lưu ký', source: 'vsdc-confirmation.pdf', confidence: '95%', usedIn: 'Quyền sở hữu', status: 'Đã xác nhận' },
      { id: 'sec-ev-2', title: 'Bảng giá thị trường', source: 'market_price_feed', confidence: '88%', usedIn: 'Định giá', status: 'Chờ xác nhận' },
      { id: 'sec-ev-3', title: 'Rating issuer', source: 'rating-bulletin.pdf', confidence: '80%', usedIn: 'Issuer risk', status: 'Chờ xác nhận' },
    ],
    calculation: {
      title: 'Haircut và giá trị bảo đảm',
      columns: ['Haircut', 'Tỷ lệ', 'Căn cứ', 'Trạng thái'],
      rows: [
        ['Rủi ro tín dụng', '6%', 'Issuer outlook negative', 'Review needed'],
        ['Rủi ro thị trường', '3%', 'Biến động giá 30 ngày', 'Pass'],
        ['Thanh khoản', '8%', 'Bid–ask spread cao', 'Review needed'],
        ['Kỳ hạn', '1%', 'Đáo hạn 2028', 'Pass'],
      ],
    },
    reportSections: ['Hồ sơ giấy tờ', 'Quyền sở hữu', 'Rủi ro tổ chức phát hành', 'Khả năng giao dịch', 'Định giá', 'Haircut', 'Evidence', 'Giới hạn'],
  },
  property_rights: {
    domainId: 'property_rights',
    routeId: 'propertyRightsAppraisal',
    label: 'Quyền tài sản',
    subtitle: 'Quyền đòi nợ, khoản phải thu, quyền phát sinh từ hợp đồng và tài sản hình thành trong tương lai.',
    statusLabel: 'Đã cấu hình khung thẩm định',
    caseId: 'PR-2026-0001',
    assetName: 'Quyền đòi nợ HĐ-2026-15',
    assetSubtype: 'Khoản phải thu thương mại',
    owner: 'Công ty TNHH ABC',
    steps: ['Hồ sơ quyền & hợp đồng', 'Khả năng thực thi pháp lý', 'Bên có nghĩa vụ', 'Dòng tiền & thu hồi', 'Tiến độ', 'Định giá kịch bản', 'Điều kiện theo dõi', 'Báo cáo'],
    metrics: [
      { label: 'Giá trị hợp đồng', value: '12 tỷ', sub: 'Theo hợp đồng cơ sở' },
      { label: 'Thu hồi ròng', value: '8.6 tỷ', sub: 'Sau aging/dilution' },
      { label: 'Haircut', value: '30%', sub: 'Pháp lý + collection risk', tone: 'var(--warning)' },
      { label: 'Confidence', value: '68%', sub: 'Cần xác nhận công nợ', tone: 'var(--warning)' },
    ],
    findings: [
      {
        id: 'pr-aging',
        title: '20% khoản phải thu quá hạn trên 90 ngày',
        tone: 'critical',
        description: 'Aging report cho thấy nhóm nợ quá hạn kéo dài, làm giảm khả năng thu hồi thực tế.',
        evidence: 'Aging report Q2/2026; đối chiếu công nợ',
        rule: 'Loại hoặc haircut mạnh khoản phải thu quá hạn >90 ngày.',
        action: 'Loại khỏi giá trị bảo đảm hoặc tăng haircut collection risk.',
        confidence: 'High · aging report complete',
        humanStatus: 'pending',
      },
      {
        id: 'pr-transfer',
        title: 'Điều khoản chuyển giao cần chấp thuận',
        tone: 'warning',
        description: 'Hợp đồng cơ sở yêu cầu bên có nghĩa vụ chấp thuận khi chuyển giao quyền đòi nợ.',
        evidence: 'Hợp đồng HĐ-2026-15 điều 12.3',
        rule: 'Cần đủ chấp thuận trước khi nhận bảo đảm quyền phát sinh từ hợp đồng.',
        action: 'Yêu cầu bổ sung văn bản chấp thuận của bên có nghĩa vụ.',
        confidence: 'Medium · legal review pending',
        humanStatus: 'pending',
      },
    ],
    evidence: [
      { id: 'pr-ev-1', title: 'Hợp đồng cơ sở', source: 'hd-2026-15.pdf', confidence: '90%', usedIn: 'Hồ sơ quyền', status: 'Chờ xác nhận' },
      { id: 'pr-ev-2', title: 'Aging report', source: 'aging-q2-2026.xlsx', confidence: '86%', usedIn: 'Dòng tiền & thu hồi', status: 'Chờ xác nhận' },
      { id: 'pr-ev-3', title: 'Xác nhận công nợ', source: 'xac-nhan-cong-no.pdf', confidence: '62%', usedIn: 'Bên có nghĩa vụ', status: 'Cần bổ sung' },
    ],
    calculation: {
      title: 'Định giá theo kịch bản',
      columns: ['Scenario', 'Xác suất', 'Giá trị', 'Giả định'],
      rows: [
        ['Base', '55%', '9.8 tỷ', 'Thu đúng lịch phần chưa quá hạn'],
        ['Downside', '30%', '7.4 tỷ', 'Gia hạn 60 ngày, dilution tăng'],
        ['Stress', '15%', '4.9 tỷ', 'Bên có nghĩa vụ chậm thanh toán kéo dài'],
      ],
    },
    reportSections: ['Hồ sơ quyền', 'Khả năng thực thi', 'Đánh giá đối tác', 'Dòng tiền', 'Tiến độ', 'Định giá theo kịch bản', 'Điều kiện theo dõi', 'Evidence', 'Giới hạn'],
  },
};

export const allAssetDomainConfigs: AssetDomainConfig[] = [
  {
    domainId: 'real_estate',
    routeId: 'realEstateAppraisal',
    label: 'Bất động sản',
    subtitle: 'Nhà đất, căn hộ, đất ở và tài sản gắn liền với đất.',
    statusLabel: 'Đang vận hành',
    caseId: CASE_ID,
    assetName: 'Nhà phố hẻm 45 Nguyễn Văn A',
    assetSubtype: 'Nhà phố',
    owner: 'Nguyễn Văn A',
    steps: ['Dữ liệu tài sản', 'Pháp lý & thị trường', 'Định giá', 'Rủi ro & LTV', 'Báo cáo & evidence'],
    metrics: [
      { label: 'Giá trị đề xuất', value: '4.85 tỷ', sub: 'Khoảng 4.55–5.10 tỷ' },
      { label: 'Confidence', value: '78%', sub: '5 giao dịch so sánh' },
      { label: 'Risk score', value: '34/100', sub: 'Trung bình', tone: 'var(--warning)' },
      { label: 'LTV đề xuất', value: '65%', sub: 'Theo risk band' },
    ],
    findings: [],
    evidence: [],
    calculation: { title: 'Tính giá trị đề xuất', columns: ['Phương pháp', 'Giá trị', 'Trọng số'], rows: [['So sánh trực tiếp', '4.90 tỷ', '50%'], ['Hedonic ML', '4.80 tỷ', '30%'], ['Chi phí', '4.75 tỷ', '20%']] },
    reportSections: ['Property profile', 'Legal status', 'Comparable', 'Valuation', 'Risk', 'LTV', 'Evidence'],
  },
  ...Object.values(assetDomainConfigs),
];

export function findCollateralCase(caseId: string): CollateralCaseSummary {
  return collateralCases.find((item) => item.caseId === caseId) ?? collateralCases[0];
}

export function findDomainByCase(caseId: string): AssetDomainConfig {
  const summary = findCollateralCase(caseId);
  if (summary.domainId === 'real_estate') return allAssetDomainConfigs[0];
  return assetDomainConfigs[summary.domainId];
}
