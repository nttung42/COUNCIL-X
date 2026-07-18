import type { CaseField } from '../../types';
import { getEditStatus, Tab1Section, useCaseStore } from '../../state/caseStore';
import { Card, EditedBadge, SourceChip } from '../common/ui';

const DV_ORDER = ['so-hong', 'to-khai', 'bien-ban', 'tb-thue'];
const DV_LINES = ['t', 'm', '', 's', '', 'm', '', 's', 'm', '', 's', '', 'm', 's', '', 'm', '', 's'];

function dvTier(conf: number): 'high' | 'mid' | 'low' {
  if (conf >= 85) return 'high';
  if (conf >= 60) return 'mid';
  return 'low';
}

function FormField({ section, field, label, cf }: { section: Tab1Section; field: string; label: string; cf: CaseField }) {
  const key = `${section}.${field}`;
  const status = useCaseStore((s) => getEditStatus(s.pendingEdits, s.confirmedKeys, 1, key));
  const editTab1Field = useCaseStore((s) => s.editTab1Field);
  const jumpToSource = useCaseStore((s) => s.jumpToSource);

  return (
    <div className={'field' + (status === 'pending' ? ' pending-edit' : status === 'confirmed' ? ' edited' : '')}>
      <label>
        {label}
        <EditedBadge status={status} />
      </label>
      <input
        className="fake-input"
        value={cf.value}
        onChange={(e) => editTab1Field(section, field, e.target.value)}
      />
      {cf.source && (
        <div className="field-meta">
          <SourceChip source={cf.source} onClick={() => jumpToSource(cf.source!.docKey, cf.source!.boxId)} />
        </div>
      )}
    </div>
  );
}

function DataSourceAccordion() {
  const dsOpen = useCaseStore((s) => s.dsOpen);
  const toggleDs = useCaseStore((s) => s.toggleDs);
  const documents = useCaseStore((s) => s.documents);
  const addMockUpload = useCaseStore((s) => s.addMockUpload);
  const removeUpload = useCaseStore((s) => s.removeUpload);

  return (
    <div className="ds-persistent" style={{ padding: '0 0 12px' }}>
      <Card>
        <div className={'ds-header' + (dsOpen ? ' open' : '')} onClick={toggleDs}>
          <div className="ds-icon">📎</div>
          <div>
            <div className="ds-title">Nguồn tài liệu đính kèm</div>
            <div className="ds-sub">{documents.length ? `${documents.length} tệp đã tải lên` : 'Chưa có tài liệu nào được tải lên'}</div>
          </div>
          <span className="ds-chevron">▾</span>
        </div>
        {dsOpen && (
          <div className="ds-body">
            <div className="dropzone" onClick={addMockUpload}>
              <div className="dz-icon">📤</div>
              <div className="dz-text">
                Kéo thả tệp vào đây hoặc <span>chọn tệp để tải lên</span>
              </div>
              <div className="dz-hint">
                Hỗ trợ PDF, JPG, PNG · tối đa 20MB/tệp — ví dụ: sổ đỏ/sổ hồng, CMND/CCCD, hợp đồng, ảnh hiện trạng...
              </div>
            </div>
            <div className="upload-list">
              {documents.length === 0 ? (
                <div className="upload-empty">Chưa có tệp nào được tải lên.</div>
              ) : (
                documents.map((doc) => (
                  <div className="upload-row" key={doc.id}>
                    <div className="upload-ic">{doc.icon}</div>
                    <div className="upload-info">
                      <div className="upload-name">{doc.fileName}</div>
                      <div className="upload-status">✓ Đã tải lên · {doc.uploadedAtLabel}</div>
                    </div>
                    <button type="button" className="upload-remove" title="Xoá tệp" onClick={() => removeUpload(doc.id)}>
                      ✕
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function DocViewerCard() {
  const docPages = useCaseStore((s) => s.caseData.docPages);
  const dvCurrentKey = useCaseStore((s) => s.dvCurrentKey);
  const dvPulseBoxId = useCaseStore((s) => s.dvPulseBoxId);
  const dvPulseToken = useCaseStore((s) => s.dvPulseToken);
  const dvHintOverride = useCaseStore((s) => s.dvHintOverride);
  const setDvCurrent = useCaseStore((s) => s.setDvCurrent);

  const doc = docPages.find((d) => d.key === dvCurrentKey) ?? docPages[0];

  return (
    <Card className="doc-viewer-card">
      <div className="dv-toolbar">
        <div className="dv-title">🗂️ Tài liệu &amp; vùng trích xuất</div>
        <div className="dv-files">
          {DV_ORDER.filter((k) => docPages.some((d) => d.key === k)).map((k) => {
            const page = docPages.find((d) => d.key === k)!;
            return (
              <span
                key={k}
                className={'dv-file' + (k === dvCurrentKey ? ' active' : '')}
                onClick={() => setDvCurrent(k)}
              >
                {page.label}
              </span>
            );
          })}
        </div>
      </div>
      <div className="dv-stage">
        <div className={'dv-page' + (doc.scan ? ' scan' : '')}>
          <div className="dv-watermark">SHB</div>
          <div className="dv-lines">
            {DV_LINES.map((c, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <div key={i} className={'ln' + (c ? ' ' + c : '')} />
            ))}
          </div>
          {doc.boxes.map((b) => {
            const isPulsing = b.id === dvPulseBoxId;
            return (
              <div
                key={isPulsing ? `${doc.key}-${b.id}-${dvPulseToken}` : `${doc.key}-${b.id}`}
                className={'dv-box ' + dvTier(b.conf) + (isPulsing ? ' pulse' : '')}
                style={{ top: `${b.top}%`, left: `${b.left}%`, width: `${b.w}%`, height: `${b.h}%` }}
              >
                <span className="dv-conf">{b.conf}%</span>
                <span className="dv-tip">
                  <b>{b.field}</b>
                  <br />
                  {b.value}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="dv-hint">
        {dvHintOverride ?? (
          <>
            Ô màu = vùng PAA trích xuất được, kèm <b>% độ tin cậy</b> ngay trên tài liệu. Di chuột vào ô để xem trường
            + giá trị. Bấm chip <b>📄 nguồn</b> ở mỗi trường bên dưới để nhảy tới đúng vùng.
          </>
        )}
      </div>
    </Card>
  );
}

export function Tab1Input() {
  const borrower = useCaseStore((s) => s.caseData.borrower);
  const legal = useCaseStore((s) => s.caseData.legal);
  const physical = useCaseStore((s) => s.caseData.physical);
  const loan = useCaseStore((s) => s.caseData.loan);

  return (
    <>
      <DataSourceAccordion />
      <DocViewerCard />

      <p className="extract-caption">
        <span>🔎</span>
        <span>
          Mỗi trường bên dưới chỉ điền khi trích được <b>trực tiếp từ tài liệu</b> — bấm chip <b>📄 nguồn</b> để đối
          chiếu vùng gốc. Trường không có nguồn (SĐT, khoản vay) để nhập tay; PAA <b>không suy đoán</b>.
        </span>
      </p>

      <Card className="form-section">
        <div className="section-h">A. Thông tin bên vay / chủ sở hữu</div>
        <div className="grid c2">
          <FormField section="borrower" field="fullName" label="Họ và tên" cf={borrower.fullName} />
          <FormField section="borrower" field="nationalId" label="Số CMND/CCCD" cf={borrower.nationalId} />
          <FormField section="borrower" field="phoneNumber" label="Số điện thoại" cf={borrower.phoneNumber} />
          <FormField
            section="borrower"
            field="relationshipToAsset"
            label="Mối quan hệ với tài sản"
            cf={borrower.relationshipToAsset}
          />
        </div>
      </Card>

      <Card className="form-section">
        <div className="section-h">
          B. Thông tin pháp lý tài sản
          <span
            className="qmark"
            data-why="Các trường này đối chiếu trực tiếp với dữ liệu trên Giấy chứng nhận quyền sử dụng đất / quyền sở hữu nhà (sổ đỏ/sổ hồng)."
          >
            ?
          </span>
        </div>
        <div className="grid c2">
          <FormField section="legal" field="certificateType" label="Loại giấy chứng nhận" cf={legal.certificateType} />
          <FormField section="legal" field="certificateNumber" label="Số giấy chứng nhận" cf={legal.certificateNumber} />
          <FormField section="legal" field="issueDateAuthority" label="Ngày cấp / Cơ quan cấp" cf={legal.issueDateAuthority} />
          <FormField section="legal" field="landPlotMapSheet" label="Số thửa / Số tờ bản đồ" cf={legal.landPlotMapSheet} />
          <FormField section="legal" field="landUsePurpose" label="Mục đích sử dụng đất" cf={legal.landUsePurpose} />
          <FormField section="legal" field="useTerm" label="Thời hạn sử dụng" cf={legal.useTerm} />
          <FormField section="legal" field="ownershipForm" label="Hình thức sở hữu" cf={legal.ownershipForm} />
          <FormField
            section="legal"
            field="currentMortgageStatus"
            label="Tình trạng thế chấp hiện tại"
            cf={legal.currentMortgageStatus}
          />
        </div>
      </Card>

      <Card className="form-section">
        <div className="section-h">C. Vị trí &amp; đặc điểm tài sản</div>
        <div className="grid c2">
          <FormField section="physical" field="address" label="Địa chỉ" cf={physical.address} />
          <FormField section="physical" field="propertyType" label="Loại BĐS" cf={physical.propertyType} />
          <FormField section="physical" field="landAreaSqm" label="Diện tích đất" cf={physical.landAreaSqm} />
          <FormField section="physical" field="floorAreaSqm" label="Diện tích sàn xây dựng" cf={physical.floorAreaSqm} />
          <FormField section="physical" field="frontageDepth" label="Kích thước mặt tiền × chiều sâu" cf={physical.frontageDepth} />
          <FormField section="physical" field="numFloorsDesc" label="Số tầng" cf={physical.numFloorsDesc} />
          <FormField section="physical" field="constructionYear" label="Năm xây dựng" cf={physical.constructionYear} />
          <FormField section="physical" field="structureMaterial" label="Kết cấu / vật liệu" cf={physical.structureMaterial} />
          <FormField section="physical" field="houseDirection" label="Hướng nhà" cf={physical.houseDirection} />
          <FormField section="physical" field="roadTypeDesc" label="Loại đường / độ rộng hẻm" cf={physical.roadTypeDesc} />
          <FormField section="physical" field="currentUsageStatus" label="Tình trạng sử dụng hiện tại" cf={physical.currentUsageStatus} />
        </div>
      </Card>

      <Card className="form-section">
        <div className="section-h">D. Thông tin khoản vay</div>
        <div className="grid c2">
          <FormField section="loan" field="loanAmountVnd" label="Số tiền vay" cf={loan.loanAmountVnd} />
          <FormField section="loan" field="loanPurpose" label="Mục đích vay" cf={loan.loanPurpose} />
          <FormField section="loan" field="loanTermYears" label="Thời hạn vay" cf={loan.loanTermYears} />
        </div>
      </Card>
    </>
  );
}
