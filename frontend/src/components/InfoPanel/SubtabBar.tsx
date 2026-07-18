/* SubtabBar — 6 tab pill. Chỉ quản lý active tab index (mockup .subtab-bar). */
import { actions, useCaseStore, type TabIndex } from '../../state/caseStore'

const TABS: { n: TabIndex; label: string }[] = [
  { n: 1, label: 'Nhập thông tin' },
  { n: 2, label: 'Kết quả tra cứu' },
  { n: 3, label: 'Định giá' },
  { n: 4, label: 'Rủi ro' },
  { n: 5, label: 'Checklist' },
  { n: 6, label: 'Dashboard' },
]

export function SubtabBar() {
  const { activeTab } = useCaseStore()
  return (
    <div className="subtab-bar">
      {TABS.map((t) => (
        <button
          key={t.n}
          className={`subtab-btn${activeTab === t.n ? ' active' : ''}`}
          onClick={() => actions.setActiveTab(t.n)}
        >
          <span className="n">{t.n}</span>
          {t.label}
        </button>
      ))}
    </div>
  )
}
