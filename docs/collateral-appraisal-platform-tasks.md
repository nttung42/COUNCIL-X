# Collateral Appraisal Platform — tasks

## Done in current implementation pass

- [x] Add platform mock data for 4 asset domains.
- [x] Add PlatformNav and PlatformPageLayout.
- [x] Add Home dashboard.
- [x] Add collateral appraisal case list.
- [x] Add generic case detail.
- [x] Add asset domain hub with 4 equal domains.
- [x] Add generic workspace for movable assets, valuable papers, property rights.
- [x] Add Evidence Center.
- [x] Add Report Center.
- [x] Remap primary routes to Collateral Appraisal Platform.
- [x] Keep legacy credit workflow routes as hidden compatibility routes.
- [x] Keep Bất động sản MVP workspace intact.
- [x] Rename BĐS stage labels toward asset-appraisal wording.
- [x] Add platform CSS using existing SHB design tokens.

## Verify

- [x] `npm run build` — pass.
- [ ] `npm run lint` — blocked: frontend repo has no ESLint config, so ESLint exits before checking files.
- [ ] Open `/`
- [ ] Open `/appraisals`
- [ ] Open `/appraisals/REQ-2026-0001`
- [ ] Open `/asset-domains`
- [ ] Open `/asset-domains/real-estate/REQ-2026-0001`
- [ ] Open `/asset-domains/movable-assets/MV-2026-0002`
- [ ] Open `/asset-domains/valuable-papers/SEC-2026-0001`
- [ ] Open `/asset-domains/property-rights/PR-2026-0001`
- [ ] Open `/evidence`
- [ ] Open `/reports`

## Later cleanup

- [ ] Extract `DataSourceAccordion` and `DocViewerCard` from `Tab1Input.tsx` if Evidence Center needs live document viewer.
- [ ] Convert generic asset domain mock config into backend contract after APIs exist.
- [ ] Add reason-required modal for Edit/Reject human review actions.
- [ ] Add real search/filter state for Appraisal list and Evidence Center.
