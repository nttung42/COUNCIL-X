import { create } from 'zustand';
import type { AppraisalCaseFull, AttachedDocument, ChatMessage, ChatRole, StepNumber } from '../types';
import { fixtureCase, mockUploadPool } from '../mocks/fixtureCase';
import {
  APPRAISAL_STEP_MSG,
  ChatStep,
  ChipFlow,
  DEMO_EDIT_REPLIES,
  DEMO_FLOWS,
  DemoEditKey,
  LOADING_TEXT,
  NEXT_USER_MSG,
  matchDemoEdit,
} from '../mocks/chatScripts';
import { downloadStandaloneReport } from '../utils/exportReport';
import { isApiConfigured, runPropertyIntake, runPropertyLookup, runPropertyValuation, uploadFile } from '../services/apiClient';
import { mapPropertyIntakeOutput } from '../utils/mapPropertyIntake';
import { mapPropertyLookupOutput } from '../utils/mapPropertyLookup';
import { mapPropertyValuationOutput } from '../utils/mapPropertyValuation';

// Store trung tâm cho toàn bộ workspace thẩm định — chuyển thể hành vi từ khối <script>
// trong ai/PAA_Mockup_SHB_8.html (khoá/mở tab, luồng "sửa -> chờ xác nhận -> xác nhận",
// kịch bản chat demo) sang state React. caseData là dữ liệu 1 hồ sơ; khi API thật sẵn sàng,
// thay initial state của caseData bằng dữ liệu load từ src/services/apiClient.ts.

export type EditStatusFlag = 'none' | 'pending' | 'confirmed';

const STEP_NUMBERS: StepNumber[] = [1, 2, 3, 4, 5];

function cloneFixture(): AppraisalCaseFull {
  const clone = JSON.parse(JSON.stringify(fixtureCase)) as AppraisalCaseFull;
  // Ở apiMode, màn "Nhập thông tin" vẫn hiện ĐỦ bộ trường như mockup (cùng key/section/label với
  // fixture) để thẩm định viên luôn gõ tay được ngay cả khi chưa/không trích xuất tài liệu nào —
  // chỉ xoá giá trị + nguồn trích xuất (dữ liệu demo), không xoá cả danh sách trường. Khi bấm
  // "Yêu cầu PAA trích xuất dữ liệu" (runExtraction), kết quả thật được GỘP vào đúng trường theo
  // key thay vì thay thế toàn bộ. Các màn 2-5 vẫn dùng dữ liệu mẫu vì ai/ backend chưa có endpoint
  // cho lookup/valuation/risk/dashboard.
  if (isApiConfigured()) {
    clone.tab1Fields = clone.tab1Fields.map((f) => ({
      ...f,
      value: '',
      status: 'nhap_tay',
      confidencePct: null,
      sourceDocKey: null,
      sourceSnippet: null,
      bbox: null,
    }));
    clone.docPages = [];
  }
  return clone;
}

function mergeByKey<T extends { key: string }>(base: T[], updates: T[]): T[] {
  const map = new Map(base.map((item) => [item.key, item]));
  updates.forEach((item) => map.set(item.key, item));
  return Array.from(map.values());
}

function wait(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

let idSeq = 0;
function nextId(prefix: string) {
  idSeq += 1;
  return `${prefix}-${idSeq}`;
}

function buildFieldBaseline(caseData: AppraisalCaseFull): Record<string, string> {
  const baseline: Record<string, string> = {};
  caseData.tab1Fields.forEach((f) => {
    baseline[f.key] = f.value;
  });
  return baseline;
}

function readFieldValue(caseData: AppraisalCaseFull, key: string): string {
  return caseData.tab1Fields.find((f) => f.key === key)?.value ?? '';
}

function upsertDashboardSummary(caseData: AppraisalCaseFull, stepNumber: 2 | 3, summaryText: string): AppraisalCaseFull {
  const dashboardSteps = caseData.dashboardSteps.map((step) =>
    step.stepNumber === stepNumber ? { ...step, summaryText } : step,
  );
  return { ...caseData, dashboardSteps };
}

function emptyPerStep<T>(fill: () => T): Record<StepNumber, T> {
  const out = {} as Record<StepNumber, T>;
  STEP_NUMBERS.forEach((n) => {
    out[n] = fill();
  });
  return out;
}

export function getEditStatus(
  pendingEdits: Record<StepNumber, string[]>,
  confirmedKeys: Set<string>,
  screen: StepNumber,
  key: string,
): EditStatusFlag {
  if (pendingEdits[screen]?.includes(key)) return 'pending';
  if (confirmedKeys.has(key)) return 'confirmed';
  return 'none';
}

interface CaseStoreState {
  caseData: AppraisalCaseFull;
  fieldBaseline: Record<string, string>;

  activeTab: StepNumber;
  visitedTabs: Record<StepNumber, boolean>;
  unlockedTabs: Record<StepNumber, boolean>;
  isLoadingTab: boolean;
  isCaseFinalized: boolean;

  pendingEdits: Record<StepNumber, string[]>;
  confirmedKeys: Set<string>;
  appraisalMsgShown: Partial<Record<StepNumber, boolean>>;

  chatStarted: boolean;
  chatMessages: ChatMessage[];
  isTyping: boolean;

  documents: AttachedDocument[];
  mockFileIdx: number;
  dsOpen: boolean;

  /** true khi VITE_API_BASE_URL được cấu hình — màn Nhập thông tin dùng upload/trích xuất thật thay vì demo. */
  apiMode: boolean;
  isUploading: boolean;
  isExtracting: boolean;
  extractionProgress: number | null;
  /** Cảnh báo từ lần trích xuất gần nhất (vd. loại tài liệu chưa hỗ trợ) — hiện thành banner riêng, không chỉ chìm trong chat. */
  extractionWarnings: string[];
  isRunningLookup: boolean;
  lookupProgress: number | null;
  lookupWarnings: string[];
  isRunningValuation: boolean;
  valuationProgress: number | null;
  valuationWarnings: string[];

  dvCurrentKey: string;
  dvPulseBoxId: string | null;
  dvPulseToken: number;
  dvHintOverride: string | null;

  markPending: (screen: StepNumber, key: string) => void;
  confirmScreen: (screen: StepNumber) => void;
  editTab1Field: (key: string, value: string) => void;
  applyDemoEdit: (key: DemoEditKey) => void;

  pushMessage: (role: ChatRole, html: string) => void;
  runSteps: (steps: ChatStep[]) => Promise<void>;
  showAppraisalStepThen: (n: StepNumber) => Promise<void>;

  switchTab: (n: StepNumber) => void;
  goBack: () => void;
  confirmAndNext: () => Promise<void>;
  finalizeCase: () => void;

  selectChip: (flow: ChipFlow) => Promise<void>;
  sendFreeText: (text: string) => Promise<void>;
  exportReport: () => Promise<void>;

  toggleDs: () => void;
  fillSampleData: () => void;
  addMockUpload: () => void;
  uploadRealFiles: (files: File[]) => Promise<void>;
  runExtraction: () => Promise<void>;
  runLookup: () => Promise<void>;
  runValuation: () => Promise<void>;
  removeUpload: (id: string) => void;

  setDvCurrent: (key: string) => void;
  jumpToSource: (docKey: string, boxId?: string) => void;
  clearPulse: () => void;
}

const initialCaseData = cloneFixture();

export const useCaseStore = create<CaseStoreState>()((set, get) => ({
  caseData: initialCaseData,
  fieldBaseline: buildFieldBaseline(initialCaseData),

  activeTab: 1,
  visitedTabs: { 1: true, 2: false, 3: false, 4: false, 5: false },
  unlockedTabs: { 1: true, 2: false, 3: false, 4: false, 5: false },
  isLoadingTab: false,
  isCaseFinalized: false,

  pendingEdits: emptyPerStep<string[]>(() => []),
  confirmedKeys: new Set<string>(),
  appraisalMsgShown: {},

  chatStarted: false,
  chatMessages: [],
  isTyping: false,

  documents: [],
  mockFileIdx: 0,
  dsOpen: false,

  apiMode: isApiConfigured(),
  isUploading: false,
  isExtracting: false,
  extractionProgress: null,
  extractionWarnings: [],
  isRunningLookup: false,
  lookupProgress: null,
  lookupWarnings: [],
  isRunningValuation: false,
  valuationProgress: null,
  valuationWarnings: [],

  dvCurrentKey: 'so-hong',
  dvPulseBoxId: null,
  dvPulseToken: 0,
  dvHintOverride: null,

  markPending: (screen, key) => {
    set((s) => {
      if (s.pendingEdits[screen].includes(key)) return {};
      return { pendingEdits: { ...s.pendingEdits, [screen]: [...s.pendingEdits[screen], key] } };
    });
  },

  confirmScreen: (screen) => {
    set((s) => {
      const keys = s.pendingEdits[screen];
      if (!keys.length) return {};
      const confirmedKeys = new Set(s.confirmedKeys);
      keys.forEach((k) => confirmedKeys.add(k));
      let fieldBaseline = s.fieldBaseline;
      if (screen === 1) {
        fieldBaseline = { ...s.fieldBaseline };
        keys.forEach((k) => {
          fieldBaseline[k] = readFieldValue(s.caseData, k);
        });
      }
      return { confirmedKeys, fieldBaseline, pendingEdits: { ...s.pendingEdits, [screen]: [] } };
    });
  },

  editTab1Field: (key, value) => {
    set((s) => {
      const tab1Fields = s.caseData.tab1Fields.map((f) => (f.key === key ? { ...f, value } : f));
      const caseData = { ...s.caseData, tab1Fields };

      const baseline = s.fieldBaseline[key] ?? '';
      const already = s.pendingEdits[1];
      let pending1 = already;
      if (value.trim() !== baseline.trim()) {
        if (!already.includes(key)) pending1 = [...already, key];
      } else if (already.includes(key)) {
        pending1 = already.filter((k) => k !== key);
      }
      return { caseData, pendingEdits: { ...s.pendingEdits, 1: pending1 } };
    });
  },

  applyDemoEdit: (key) => {
    switch (key) {
      case 'area':
        get().editTab1Field('land_area_sqm', '65 m²');
        break;
      case 'environment': {
        set((s) => ({
          caseData: {
            ...s.caseData,
            lookupFindings: s.caseData.lookupFindings.map((f) =>
              f.id === 'lc-environment'
                ? {
                    ...f,
                    statusBadge: 'da_xac_thuc',
                    inferenceText:
                      'Đã xác minh lại theo phản hồi của bạn: hệ thống thoát nước khu vực được cải tạo từ 2024, không còn ghi nhận ngập.',
                    sourceLabel: 'Xác minh thủ công theo phản hồi thẩm định viên',
                    confidencePct: 95,
                  }
                : f,
            ),
          },
        }));
        get().markPending(2, 'lookup.lc-environment');
        break;
      }
      case 'valuation': {
        set((s) => ({
          caseData: {
            ...s.caseData,
            valuation: {
              ...s.caseData.valuation,
              proposedValueLabel: '5.05 tỷ',
              valueRangeLabel: '4.75–5.30 tỷ (đã điều chỉnh)',
            },
          },
        }));
        get().markPending(3, 'valuation.tile');
        break;
      }
      case 'reputation': {
        set((s) => ({
          caseData: {
            ...s.caseData,
            risk: { ...s.caseData.risk, riskScore: 27 },
            riskGroups: s.caseData.riskGroups.map((g) =>
              g.groupKey === 'reputation'
                ? {
                    ...g,
                    score: 20,
                    inferenceText:
                      'Đã xác minh thực địa theo phản hồi của bạn — không phát hiện dấu hiệu bất thường. Điểm rủi ro nhóm này giảm xuống mức thấp, độ tin cậy nguồn tăng lên nhờ xác minh trực tiếp.',
                    sourceLabel: 'Xác minh thủ công theo phản hồi thẩm định viên',
                  }
                : g,
            ),
            riskFlags: s.caseData.riskFlags.map((f) =>
              f.id === 'reputation'
                ? {
                    ...f,
                    severity: 'thap',
                    description: 'Đã xác minh thực địa theo phản hồi của bạn — không phát hiện dấu hiệu bất thường.',
                    confidencePct: 90,
                    verifiedStatus: 'da_xac_thuc',
                  }
                : f,
            ),
          },
        }));
        get().markPending(4, 'risk.group.reputation');
        get().markPending(4, 'risk.flag.reputation');
        break;
      }
      default:
        break;
    }
  },

  pushMessage: (role, html) => {
    set((s) => ({ chatMessages: [...s.chatMessages, { id: nextId('msg'), role, html }] }));
  },

  runSteps: async (steps) => {
    for (const step of steps) {
      if (step.type === 'user') {
        get().pushMessage('user', step.text);
        // eslint-disable-next-line no-await-in-loop
        await wait(350);
        continue;
      }
      set({ isTyping: true });
      // eslint-disable-next-line no-await-in-loop
      await wait(step.delay ?? 900);
      set({ isTyping: false });
      get().pushMessage(step.type === 'status' ? 'status' : 'agent', step.text);
      if (step.applyKey) get().applyDemoEdit(step.applyKey);
      // eslint-disable-next-line no-await-in-loop
      await wait(450);
    }
  },

  showAppraisalStepThen: async (n) => {
    const msg = APPRAISAL_STEP_MSG[n];
    if (!msg || get().appraisalMsgShown[n]) return;
    set((s) => ({ appraisalMsgShown: { ...s.appraisalMsgShown, [n]: true }, chatStarted: true }));
    await get().runSteps([{ type: 'agent', text: msg, delay: 700 }]);
  },

  switchTab: (n) => {
    const s = get();
    if (!s.unlockedTabs[n]) return;
    if (s.visitedTabs[n]) {
      set({ activeTab: n });
      return;
    }
    set({ isLoadingTab: true });
    setTimeout(() => {
      set((state) => ({ visitedTabs: { ...state.visitedTabs, [n]: true }, isLoadingTab: false, activeTab: n }));
      void get().showAppraisalStepThen(n);
    }, 750);
  },

  goBack: () => {
    const cur = get().activeTab;
    if (cur > 1) get().switchTab((cur - 1) as StepNumber);
  },

  confirmAndNext: async () => {
    const cur = get().activeTab;
    get().confirmScreen(cur);
    set({ chatStarted: true });
    if (cur === 5) {
      get().finalizeCase();
      return;
    }
    const target = (cur + 1) as StepNumber;
    set((s) => ({ unlockedTabs: { ...s.unlockedTabs, [target]: true } }));
    const steps: ChatStep[] = [];
    const nextUserMsg = NEXT_USER_MSG[cur];
    if (nextUserMsg) steps.push({ type: 'user', text: nextUserMsg });
    steps.push({ type: 'status', text: '⏳ ' + (LOADING_TEXT[target] ?? 'Đang xử lý…'), delay: 500 });
    await get().runSteps(steps);
    if (cur === 1) await get().runLookup();
    if (cur === 2) await get().runValuation();
    get().switchTab(target);
  },

  finalizeCase: () => {
    set((s) => ({ isCaseFinalized: true, caseData: { ...s.caseData, status: 'hoan_tat' } }));
  },

  selectChip: async (flow) => {
    set({ chatStarted: true, chatMessages: [] });
    await get().runSteps(DEMO_FLOWS[flow]);
  },

  sendFreeText: async (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    set({ chatStarted: true });
    const key = matchDemoEdit(trimmed);
    const steps: ChatStep[] = [{ type: 'user', text: trimmed }];
    if (key) {
      steps.push({ type: 'agent', text: DEMO_EDIT_REPLIES[key], delay: 900, applyKey: key });
    } else {
      steps.push({
        type: 'agent',
        text: 'Đã ghi nhận. Trong hệ thống thật, yêu cầu này được chuyển tới luồng xử lý thẩm định phù hợp.',
        delay: 900,
      });
    }
    await get().runSteps(steps);
  },

  exportReport: async () => {
    const s = get();
    downloadStandaloneReport(s.caseData);
    set({ chatStarted: true });
    await get().runSteps([
      { type: 'status', text: `Đã xuất báo cáo: BienBan_ThamDinh_${s.caseData.caseId}.html`, delay: 400 },
    ]);
  },

  toggleDs: () => set((s) => ({ dsOpen: !s.dsOpen })),

  fillSampleData: () => {
    set((s) => {
      const sampleByKey = new Map(fixtureCase.tab1Fields.map((f) => [f.key, f.value]));
      const tab1Fields = s.caseData.tab1Fields.map((f) => {
        const sampleValue = sampleByKey.get(f.key);
        return sampleValue !== undefined ? { ...f, value: sampleValue } : f;
      });
      const pending1 = tab1Fields
        .filter((f) => f.value.trim() !== (s.fieldBaseline[f.key] ?? '').trim())
        .map((f) => f.key);
      return {
        caseData: { ...s.caseData, tab1Fields },
        pendingEdits: { ...s.pendingEdits, 1: pending1 },
      };
    });
  },

  addMockUpload: () => {
    const s = get();
    const item = mockUploadPool[s.mockFileIdx % mockUploadPool.length];
    const doc: AttachedDocument = { id: nextId('doc'), uploadedAtLabel: 'vừa xong', ...item };
    set((state) => ({ documents: [...state.documents, doc], mockFileIdx: state.mockFileIdx + 1 }));
  },

  uploadRealFiles: async (files) => {
    if (!files.length) return;
    set({ isUploading: true });
    try {
      for (const file of files) {
        // eslint-disable-next-line no-await-in-loop
        const uploaded = await uploadFile(file);
        const isPdf = uploaded.content_type.includes('pdf');
        const isImage = uploaded.content_type.startsWith('image/');
        const doc: AttachedDocument = {
          id: uploaded.id,
          fileName: uploaded.original_name,
          icon: isPdf ? 'PDF' : isImage ? 'IMG' : 'DOC',
          docCategory: 'khac',
          uploadedAtLabel: 'vừa xong',
        };
        set((s) => ({ documents: [...s.documents, doc] }));
      }
    } catch (err) {
      set({ chatStarted: true });
      get().pushMessage('status', `Tải tệp lên thất bại: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      set({ isUploading: false });
    }
  },

  runExtraction: async () => {
    const s = get();
    if (!s.apiMode || s.isExtracting || !s.documents.length) return;
    set({ isExtracting: true, chatStarted: true, extractionProgress: 0, extractionWarnings: [] });
    try {
      const output = await runPropertyIntake(
        s.documents.map((d) => d.id),
        s.caseData.caseId,
        (progress) => set({ extractionProgress: progress }),
      );
      const { tab1Fields: extractedFields, docPages: extractedPages } = mapPropertyIntakeOutput(output);

      set((state) => {
        // Gộp theo key: trường trích xuất được ghi đè đúng ô tương ứng trong bộ trường mockup;
        // trường lạ (key backend trả về không khớp danh sách mẫu) vẫn được thêm vào cuối, không mất dữ liệu.
        const tab1Fields = mergeByKey(state.caseData.tab1Fields, extractedFields);
        const docPages = mergeByKey(state.caseData.docPages, extractedPages);
        return {
          caseData: { ...state.caseData, tab1Fields, docPages },
          fieldBaseline: buildFieldBaseline({ ...state.caseData, tab1Fields }),
          pendingEdits: { ...state.pendingEdits, 1: [] },
          dvCurrentKey: docPages[0]?.key ?? state.dvCurrentKey,
          extractionWarnings: output.warnings ?? [],
        };
      });
      get().pushMessage(
        'status',
        `Đã trích xuất ${extractedFields.length} trường từ ${extractedPages.length} tài liệu.` +
          (output.warnings?.length ? ` Có ${output.warnings.length} cảnh báo — xem chi tiết ở khối tài liệu.` : ''),
      );
    } catch (err) {
      get().pushMessage('status', `Trích xuất dữ liệu thất bại: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      set({ isExtracting: false, extractionProgress: null });
    }
  },

  runLookup: async () => {
    const s = get();
    if (!s.apiMode || s.isRunningLookup) return;
    set({ isRunningLookup: true, lookupProgress: 0, lookupWarnings: [] });
    try {
      const output = await runPropertyLookup(s.caseData.caseId, (progress) => set({ lookupProgress: progress }));
      const mapped = mapPropertyLookupOutput(output);
      set((state) => {
        const caseData = upsertDashboardSummary(
          {
            ...state.caseData,
            marketComparables: mapped.marketComparables,
            marketInferenceText: mapped.marketInferenceText,
            lookupFindings: mapped.lookupFindings,
          },
          2,
          `${mapped.lookupFindings.length} nguồn tra cứu hoàn tất · ${mapped.marketComparables.length} giao dịch so sánh.`,
        );
        return { caseData, lookupWarnings: mapped.warnings };
      });
      get().pushMessage(
        'status',
        `Đã cập nhật kết quả tra cứu từ backend: ${mapped.lookupFindings.length} nguồn, ${mapped.marketComparables.length} giao dịch so sánh.` +
          (mapped.warnings.length ? ` Có ${mapped.warnings.length} cảnh báo.` : ''),
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      set({ lookupWarnings: [`Không lấy được dữ liệu tra cứu thật: ${message}`] });
      get().pushMessage('status', `Không lấy được dữ liệu tra cứu thật, đang giữ dữ liệu demo. ${message}`);
    } finally {
      set({ isRunningLookup: false, lookupProgress: null });
    }
  },

  runValuation: async () => {
    const s = get();
    if (!s.apiMode || s.isRunningValuation) return;
    set({ isRunningValuation: true, valuationProgress: 0, valuationWarnings: [] });
    try {
      const output = await runPropertyValuation(s.caseData.caseId, (progress) => set({ valuationProgress: progress }));
      const mapped = mapPropertyValuationOutput(output);
      if (!mapped.ok) {
        set({ valuationWarnings: mapped.warnings });
        get().pushMessage('status', `Backend chưa trả được định giá, đang giữ dữ liệu demo. ${mapped.warnings.join(' ')}`);
        return;
      }
      set((state) => {
        const caseData = upsertDashboardSummary(
          {
            ...state.caseData,
            valuation: mapped.valuation,
            priceIndexSeries: mapped.priceIndexSeries,
            valuationMethods: mapped.valuationMethods,
            valuationWeightedInferenceText: mapped.valuationWeightedInferenceText,
            confidenceFactors: mapped.confidenceFactors,
            confidenceInferenceText: mapped.confidenceInferenceText,
          },
          3,
          `${mapped.valuation.proposedValueLabel} (${mapped.valuation.valueRangeLabel}) · độ tin cậy ${mapped.valuation.confidencePct}%, kết hợp ${mapped.valuationMethods.length} phương pháp.`,
        );
        return { caseData, valuationWarnings: mapped.warnings };
      });
      get().pushMessage(
        'status',
        `Đã cập nhật định giá từ backend: ${mapped.valuation.proposedValueLabel}, độ tin cậy ${mapped.valuation.confidencePct}%.` +
          (mapped.warnings.length ? ` Có ${mapped.warnings.length} cảnh báo.` : ''),
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      set({ valuationWarnings: [`Không lấy được định giá thật: ${message}`] });
      get().pushMessage('status', `Không lấy được định giá thật, đang giữ dữ liệu demo. ${message}`);
    } finally {
      set({ isRunningValuation: false, valuationProgress: null });
    }
  },

  removeUpload: (id) => set((s) => ({ documents: s.documents.filter((d) => d.id !== id) })),

  setDvCurrent: (key) => set({ dvCurrentKey: key, dvPulseBoxId: null, dvHintOverride: null }),

  jumpToSource: (docKey, boxId) => {
    if (!docKey || docKey === 'suy-luan') {
      set({ dvHintOverride: 'Trường này được suy luận hoặc nhập tay — không có vùng nguồn trực tiếp trên tài liệu.' });
      return;
    }
    set((s) => ({
      dvCurrentKey: docKey,
      dvPulseBoxId: boxId ?? null,
      dvPulseToken: s.dvPulseToken + 1,
      dvHintOverride: null,
    }));
  },

  clearPulse: () => set({ dvPulseBoxId: null }),
}));
