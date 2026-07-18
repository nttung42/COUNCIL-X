# Collateral Appraisal Platform — implementation plan

## Mục tiêu

Mở rộng MVP thẩm định Bất động sản thành nền tảng thẩm định tài sản bảo đảm toàn diện, gồm 4 phân hệ ngang hàng:

- Bất động sản
- Động sản
- Giấy tờ có giá
- Quyền tài sản

Giữ nguyên lõi MVP BĐS hiện có, thêm các màn điều hướng và workspace mock cho 3 phân hệ còn lại. Không đưa Approval/Disbursement/Portfolio Monitoring vào primary UX.

## Route chính

```text
/                                      Tổng quan
/appraisals                            Hồ sơ thẩm định
/appraisals/:caseId                    Chi tiết hồ sơ
/asset-domains                         Phân hệ tài sản
/asset-domains/real-estate/:caseId     Workspace Bất động sản MVP
/asset-domains/movable-assets/:caseId  Workspace Động sản
/asset-domains/valuable-papers/:caseId Workspace Giấy tờ có giá
/asset-domains/property-rights/:caseId Workspace Quyền tài sản
/evidence                              Evidence Center
/reports                               Report Center
```

Legacy routes `/cases/...` giữ để không vỡ demo cũ.

## Reuse từ MVP

- Design tokens: `apps/frontend/src/theme/tokens.css`
- Common UI: `apps/frontend/src/components/common/ui.tsx`
- BĐS workspace: `apps/frontend/src/features/collateral-appraisal/`
- Info panels: `apps/frontend/src/components/InfoPanel/`
- Store/API BĐS: `apps/frontend/src/state/caseStore.ts`
- BĐS fixture: `apps/frontend/src/mocks/fixtureCase.ts`

## Files thêm

- `apps/frontend/src/app/layout/PlatformNav.tsx`
- `apps/frontend/src/app/layout/PlatformPageLayout.tsx`
- `apps/frontend/src/features/collateral-platform/CollateralHomePage.tsx`
- `apps/frontend/src/features/collateral-platform/AppraisalCaseListPage.tsx`
- `apps/frontend/src/features/collateral-platform/AppraisalCaseDetailPage.tsx`
- `apps/frontend/src/features/collateral-platform/AssetDomainHubPage.tsx`
- `apps/frontend/src/features/collateral-platform/EvidenceCenterPage.tsx`
- `apps/frontend/src/features/collateral-platform/ReportCenterPage.tsx`
- `apps/frontend/src/features/asset-domains/GenericAssetDomainWorkspace.tsx`
- `apps/frontend/src/mocks/assetDomainCases.ts`

## Verification

- `npm run build`
- `npm run lint`
- Manual navigation across all new routes.
