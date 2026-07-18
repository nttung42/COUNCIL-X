import type { AppraisalCaseFull } from '../types';
import { fixtureCase } from '../mocks/fixtureCase';

// Điểm nối API thật khi backend sẵn sàng. Hiện tại chưa có API (frontend đi trước),
// nên mọi hàm ở đây trả về dữ liệu tĩnh từ src/mocks/fixtureCase.ts.
//
// Khi backend xong, người phụ trách API chỉ cần:
//   1. Set VITE_API_BASE_URL trong .env (xem .env.example).
//   2. Thay phần "TODO: gọi API thật" bên dưới bằng fetch(`${API_BASE_URL}/cases/${caseId}`)
//      trả về JSON đúng shape AppraisalCaseFull (src/types.ts).
//   3. src/state/caseStore.ts import getCase() từ đây thay vì import fixtureCase trực tiếp —
//      phần còn lại của UI không cần đổi vì đã lập trình theo type, không theo dữ liệu tĩnh.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export function isApiConfigured(): boolean {
  return Boolean(API_BASE_URL);
}

export async function getCase(caseId: string): Promise<AppraisalCaseFull> {
  if (!isApiConfigured()) {
    return JSON.parse(JSON.stringify(fixtureCase)) as AppraisalCaseFull;
  }

  // TODO: gọi API thật khi backend sẵn sàng.
  const res = await fetch(`${API_BASE_URL}/cases/${caseId}`);
  if (!res.ok) throw new Error(`Không tải được hồ sơ ${caseId}: HTTP ${res.status}`);
  return (await res.json()) as AppraisalCaseFull;
}
