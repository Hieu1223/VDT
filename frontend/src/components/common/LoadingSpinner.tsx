import React from "react";

export default function LoadingSpinner({ fullPage = false }: { fullPage?: boolean }) {
  if (fullPage) {
    return (
      <div className="loading-page" data-testid="loading-spinner-fullpage">
        <div className="loading-spinner" />
      </div>
    );
  }
  return <div className="loading-spinner" data-testid="loading-spinner" />;
}
