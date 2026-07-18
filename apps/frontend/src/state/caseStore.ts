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

// Store trung tâm cho toàn bộ workspace thẩm định — chuyển thể hành vi từ khối <script>
// trong ai/PAA_Mockup_SHB_8.html (khoá/mở tab, luồng "sửa -> chờ xác nhận -> xác nhận",
// kịch bản chat demo) sang state React. caseData là dữ liệu 1 hồ sơ; khi API thật sẵn sàng,
// thay initial state của caseData bằng dữ liệu load từ src/services/apiClient.ts.

export type EditStatusFlag = 'none' | 'pending' | 'confirmed';

const STEP_NUMBERS: StepNumber[] = [1, 2, 3, 4, 5];

function cloneFixture(): AppraisalCaseFull {
  return JSON.parse(JSON.stringify(fixtureCase)) as AppraisalCaseFull;
}

function wait(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

let idSeq = 0;
function nextId(prefix: string) {
  idSeq += 1;
  return `${prefix}-${idSeq}`;
}

const TAB1_SECTIONS = ['borrower', 'legal', 'physical', 'loan'] as const;
export type Tab1Section = (typeof TAB1_SECTIONS)[number];

function buildFieldBaseline(caseData: AppraisalCaseFull): Record<string, string> {
  const baseline: Record<string, string> = {};
  TAB1_SECTIONS.forEach((section) => {
    const obj = caseData[section] as unknown as Record<string, unknown>;
    Object.entries(obj).forEach(([field, cf]) => {
      if (cf && typeof cf === 'object' && 'value' in (cf as Record<string, unknown>)) {
        baseline[`${section}.${field}`] = (cf as { value: string }).value;
      }
    });
  });
  return baseline;
}

function readFieldValue(caseData: AppraisalCaseFull, key: string): string {
  const [section, field] = key.split('.') as [Tab1Section, string];
  const obj = caseData[section] as unknown as Record<string, { value: string }>;
  return obj[field]?.value ?? '';
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

  dvCurrentKey: string;
  dvPulseBoxId: string | null;
  dvPulseToken: number;
  dvHintOverride: string | null;

  markPending: (screen: StepNumber, key: string) => void;
  confirmScreen: (screen: StepNumber) => void;
  editTab1Field: (section: Tab1Section, field: string, value: string) => void;
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
  addMockUpload: () => void;
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

  editTab1Field: (section, field, value) => {
    const key = `${section}.${field}`;
    set((s) => {
      const sectionObj = s.caseData[section] as unknown as Record<string, { value: string; source?: unknown }>;
      const updatedSection = { ...sectionObj, [field]: { ...sectionObj[field], value } };
      const caseData = { ...s.caseData, [section]: updatedSection } as AppraisalCaseFull;

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
        get().editTab1Field('physical', 'landAreaSqm', '65 m²');
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
        text: 'Đã ghi nhận. Đây là bản demo tĩnh — trong hệ thống thật, PAA sẽ điều phối các agent chuyên trách để xử lý yêu cầu này.',
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
      { type: 'status', text: `📄 Đã xuất báo cáo: BienBan_ThamDinh_${s.caseData.caseId}.html`, delay: 400 },
    ]);
  },

  toggleDs: () => set((s) => ({ dsOpen: !s.dsOpen })),

  addMockUpload: () => {
    const s = get();
    const item = mockUploadPool[s.mockFileIdx % mockUploadPool.length];
    const doc: AttachedDocument = { id: nextId('doc'), uploadedAtLabel: 'vừa xong', ...item };
    set((state) => ({ documents: [...state.documents, doc], mockFileIdx: state.mockFileIdx + 1 }));
  },

  removeUpload: (id) => set((s) => ({ documents: s.documents.filter((d) => d.id !== id) })),

  setDvCurrent: (key) => set({ dvCurrentKey: key, dvPulseBoxId: null, dvHintOverride: null }),

  jumpToSource: (docKey, boxId) => {
    if (!docKey || docKey === 'suy-luan') {
      set({ dvHintOverride: 'Trường này do PAA suy luận hoặc nhập tay — không có vùng nguồn trực tiếp trên tài liệu.' });
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
