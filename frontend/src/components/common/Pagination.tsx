import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  testId?: string;
}

export function Pagination({ page, pageSize, total, onPageChange, testId }: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (total === 0) return null;
  return (
    <div className="pagination-bar" data-testid={testId}>
      <span className="text-muted pagination-summary">
        {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} of {total}
      </span>
      <div className="pagination-controls">
        <button className="btn btn-secondary btn-sm" data-testid={testId ? `${testId}-prev-button` : undefined} disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          <ChevronLeft size={16} />
        </button>
        <span className="pagination-page-indicator" data-testid={testId ? `${testId}-page-indicator` : undefined}>Page {page} of {totalPages}</span>
        <button className="btn btn-secondary btn-sm" data-testid={testId ? `${testId}-next-button` : undefined} disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
