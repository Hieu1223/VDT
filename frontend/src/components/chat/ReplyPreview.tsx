import React from "react";
import { X } from "lucide-react";
import type { ReplyPreview as ReplyPreviewType } from "@/types";
import "@/components/chat/Chat.css";

export default function ReplyPreview({ preview, onClear }: { preview: ReplyPreviewType; onClear?: () => void }) {
  return (
    <div className="reply-preview" data-testid="reply-preview">
      <div className="reply-preview-bar" />
      <div className="reply-preview-body">
        <span className="reply-preview-sender">{preview.sender_username}</span>
        <span className="reply-preview-content">{preview.content}</span>
      </div>
      {onClear && (
        <button type="button" data-testid="reply-preview-clear-button" onClick={onClear}>
          <X size={14} />
        </button>
      )}
    </div>
  );
}
