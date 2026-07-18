import { useRef } from 'react';
import type { Tab1Field, Tab1SectionKey } from '../../types';
import { getEditStatus, useCaseStore } from '../../state/caseStore';
import { Card, EditedBadge, SourceChip } from '../common/ui';
import { getSourceChip, TAB1_STATUS_TOOLTIP } from '../../utils/tab1Field';

const DV_LINES = ['t', 'm', '', 's', '', 'm', '', 's', 'm', '', 's', '', 'm', 's', '', 'm', '', 's'];

function dvTier(conf: number): 'high' | 'mid' | 'low' {
  if (conf >= 85) return 'high';
  if (conf >= 60) return 'mid';
  return 'low';
}

function FormField({ field }: { field: Tab1Field }) {
  const status = useCaseStore((s) => getEditStatus(s.pendingEdits, s.confirmedKeys, 1, field.key));
  const docPages = useCaseStore((s) => s.caseData.docPages);
  const editTab1Field = useCaseStore((s) => s.editTab1Field);
  const jumpToSource = useCaseStore((s) => s.jumpToSource);

  const chip = getSourceChip(field, docPages);

  return (
    <div className={'field' + (status === 'pending' ? ' pending-edit' : status === 'confirmed' ? ' edited' : '')}>
      <label title={TAB1_STATUS_TOOLTIP[field.status]}>
        {field.label}
        <EditedBadge status={status} />
      </label>
      <input
        className="fake-input"
        value={field.value}
        onChange={(e) => editTab1Field(field.key, e.target.value)}
      />
      {chip && (
        <div className="field-meta">
          <SourceChip
            label={chip.label}
            warn={chip.warn}
            tooltip={field.sourceSnippet}
            onClick={() => jumpToSource(field.sourceDocKey ?? '', field.key)}
          />
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
  const apiMode = useCaseStore((s) => s.apiMode);
  const isUploading = useCaseStore((s) => s.isUploading);
  const isExtracting = useCaseStore((s) => s.isExtracting);
  const extractionProgress = useCaseStore((s) => s.extractionProgress);
  const uploadRealFiles = useCaseStore((s) => s.uploadRealFiles);
  const runExtraction = useCaseStore((s) => s.runExtraction);
  const fillSampleData = useCaseStore((s) => s.fillSampleData);
  const extractionWarnings = useCaseStore((s) => s.extractionWarnings);

  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleDropzoneClick() {
    if (apiMode) fileInputRef.current?.click();
    else addMockUpload();
  }

  function handleFilesSelected(fileList: FileList | null) {
    if (!fileList || !fileList.length) return;
    void uploadRealFiles(Array.from(fileList));
  }

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
            {apiMode && (
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.jpg,.jpeg,.png"
                style={{ display: 'none' }}
                onChange={(e) => {
                  handleFilesSelected(e.target.files);
                  e.target.value = '';
                }}
              />
            )}
            <div className="dropzone" onClick={handleDropzoneClick} style={isUploading ? { opacity: 0.6, pointerEvents: 'none' } : undefined}>
              <div className="dz-icon">{isUploading ? '⏳' : '📤'}</div>
              <div className="dz-text">
                {isUploading ? (
                  'Đang tải lên…'
                ) : (
                  <>
                    Kéo thả tệp vào đây hoặc <span>chọn tệp để tải lên</span>
                  </>
                )}
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
            {apiMode && (
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button
                  type="button"
                  className="primary-btn"
                  style={{ flex: 1 }}
                  disabled={!documents.length || isExtracting}
                  onClick={() => void runExtraction()}
                >
                  {isExtracting ? `⏳ PAA đang trích xuất dữ liệu… ${extractionProgress ?? 0}%` : '🔎 Yêu cầu PAA trích xuất dữ liệu'}
                </button>
                <button
                  type="button"
                  className="footer-back-btn"
                  title="Điền nhanh dữ liệu giả để test giao diện, không phải dữ liệu thật"
                  onClick={fillSampleData}
                >
                  🎲 Điền dữ liệu mẫu
                </button>
              </div>
            )}
            {extractionWarnings.length > 0 && (
              <div
                style={{
                  marginTop: 12,
                  background: 'var(--warning-tint)',
                  border: '1px solid rgba(250,178,25,0.4)',
                  borderRadius: 8,
                  padding: '9px 11px',
                }}
              >
                <div style={{ fontSize: 10.5, fontWeight: 700, color: '#8a6100', marginBottom: 4 }}>
                  ⚠ {extractionWarnings.length} cảnh báo từ lần trích xuất gần nhất
                </div>
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: 11.5, color: 'var(--ink)', lineHeight: 1.55 }}>
                  {extractionWarnings.map((w, i) => (
                    // eslint-disable-next-line react/no-array-index-key
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

function DocViewerCard() {
  const docPages = useCaseStore((s) => s.caseData.docPages);
  const tab1Fields = useCaseStore((s) => s.caseData.tab1Fields);
  const dvCurrentKey = useCaseStore((s) => s.dvCurrentKey);
  const dvPulseBoxId = useCaseStore((s) => s.dvPulseBoxId);
  const dvPulseToken = useCaseStore((s) => s.dvPulseToken);
  const dvHintOverride = useCaseStore((s) => s.dvHintOverride);
  const setDvCurrent = useCaseStore((s) => s.setDvCurrent);

  if (!docPages.length) {
    return (
      <Card className="doc-viewer-card">
        <div className="dv-toolbar">
          <div className="dv-title">🗂️ Tài liệu &amp; vùng trích xuất</div>
        </div>
        <div className="dv-hint">Chưa có tài liệu nào được xử lý — tải tài liệu lên ở khối phía trên để bắt đầu.</div>
      </Card>
    );
  }

  const doc = docPages.find((d) => d.key === dvCurrentKey) ?? docPages[0];
  const boxes = tab1Fields.filter((f) => f.sourceDocKey === doc.key && f.bbox);

  return (
    <Card className="doc-viewer-card">
      <div className="dv-toolbar">
        <div className="dv-title">🗂️ Tài liệu &amp; vùng trích xuất</div>
        <div className="dv-files">
          {docPages.map((page) => (
            <span
              key={page.key}
              className={'dv-file' + (page.key === dvCurrentKey ? ' active' : '')}
              onClick={() => setDvCurrent(page.key)}
            >
              {page.label}
            </span>
          ))}
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
          {boxes.map((f) => {
            const isPulsing = f.key === dvPulseBoxId;
            const conf = f.confidencePct ?? 0;
            return (
              <div
                key={isPulsing ? `${f.key}-${dvPulseToken}` : f.key}
                className={'dv-box ' + dvTier(conf) + (isPulsing ? ' pulse' : '')}
                style={{ top: `${f.bbox!.top}%`, left: `${f.bbox!.left}%`, width: `${f.bbox!.w}%`, height: `${f.bbox!.h}%` }}
              >
                <span className="dv-conf">{conf}%</span>
                <span className="dv-tip">
                  <b>{f.label}</b>
                  <br />
                  {f.value}
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

const SECTION_TITLE: Record<Tab1SectionKey, string> = {
  A: 'A. Thông tin bên vay / chủ sở hữu',
  B: 'B. Thông tin pháp lý tài sản',
  C: 'C. Vị trí & đặc điểm tài sản',
  D: 'D. Thông tin khoản vay',
};

function FormSection({ section, fields }: { section: Tab1SectionKey; fields: Tab1Field[] }) {
  if (!fields.length) return null;
  return (
    <Card className="form-section">
      <div className="section-h">{SECTION_TITLE[section]}</div>
      <div className="grid c2">
        {fields.map((f) => (
          <FormField key={f.key} field={f} />
        ))}
      </div>
    </Card>
  );
}

export function Tab1Input() {
  const tab1Fields = useCaseStore((s) => s.caseData.tab1Fields);
  const apiMode = useCaseStore((s) => s.apiMode);

  const bySection = (section: Tab1SectionKey) => tab1Fields.filter((f) => f.section === section);

  return (
    <>
      <DataSourceAccordion />
      <DocViewerCard />

      <p className="extract-caption">
        <span>🔎</span>
        <span>
          Trường có chip <b>📄 nguồn</b> là PAA trích được <b>trực tiếp từ tài liệu</b> — bấm chip để đối chiếu vùng
          gốc. Trường không có nguồn (SĐT, khoản vay...) cứ <b>gõ tay trực tiếp</b> vào ô; PAA{' '}
          <b>không tự suy đoán</b> những trường này.
          {apiMode && ' Có thể gõ tay toàn bộ form ngay, hoặc tải tài liệu lên rồi bấm "Yêu cầu PAA trích xuất dữ liệu" để PAA tự điền giúp.'}
        </span>
      </p>

      <FormSection section="A" fields={bySection('A')} />
      <FormSection section="B" fields={bySection('B')} />
      <FormSection section="C" fields={bySection('C')} />
      <FormSection section="D" fields={bySection('D')} />
    </>
  );
}
