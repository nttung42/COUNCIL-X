/* Error boundary — 1 component lỗi không làm sập toàn app (Error Handling). */
import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  label?: string
}
interface State {
  hasError: boolean
  message?: string
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(err: Error): State {
    return { hasError: true, message: err.message }
  }

  componentDidCatch(err: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('[PAA UI error]', this.props.label, err, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="state-msg error">
          Không hiển thị được {this.props.label ?? 'phần này'}.
          <br />
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{this.state.message}</span>
        </div>
      )
    }
    return this.props.children
  }
}
