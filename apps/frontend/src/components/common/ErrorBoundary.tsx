import { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('PAA workspace crashed:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
            color: '#151A2E',
            padding: 24,
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 32 }}>⚠️</div>
          <div style={{ fontWeight: 700, fontSize: 15 }}>PAA Workspace gặp lỗi không mong muốn.</div>
          <div style={{ fontSize: 12.5, color: '#5B6478', maxWidth: 420 }}>{this.state.error.message}</div>
          <button
            type="button"
            onClick={() => window.location.reload()}
            style={{
              background: '#C24E0E',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '9px 16px',
              fontSize: 12.5,
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Tải lại trang
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
