import React from "react";

interface State {
  hasError: boolean;
  message?: string;
}

export default class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="empty-state" data-testid="error-boundary-fallback">
          <h2>Something went wrong</h2>
          <p className="text-muted">{this.state.message || "Please refresh the page and try again."}</p>
          <button className="btn btn-primary" data-testid="error-boundary-reload-button" onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
