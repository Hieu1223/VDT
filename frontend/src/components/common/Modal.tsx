import React from "react";
import { X } from "lucide-react";
import "@/components/common/Modal.css";

interface ModalProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  testId?: string;
}

export function Modal({ title, onClose, children, testId }: ModalProps) {
  return (
    <div className="modal-overlay" data-testid={testId ? `${testId}-overlay` : undefined} onClick={onClose}>
      <div className="modal-card card" onClick={(e) => e.stopPropagation()} data-testid={testId}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="btn btn-ghost btn-sm modal-close-button" data-testid={testId ? `${testId}-close-button` : "modal-close-button"} onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}
