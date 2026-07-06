import React, { useState } from "react";
import { Send } from "lucide-react";
import ReplyPreview from "@/components/chat/ReplyPreview";
import AttachmentUploader from "@/components/chat/AttachmentUploader";
import type { Attachment, Message } from "@/types";
import "@/components/chat/Chat.css";

interface Props {
  ticketId: string;
  replyTo: Message | null;
  onClearReply: () => void;
  onSend: (content: string, replyToId: string | null, attachments: Attachment[]) => Promise<void>;
  disabled?: boolean;
  disabledReason?: string;
}

export default function Composer({ ticketId, replyTo, onClearReply, onSend, disabled, disabledReason }: Props) {
  const [content, setContent] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!content.trim() && attachments.length === 0) return;
    setSending(true);
    try {
      await onSend(content.trim(), replyTo?.id || null, attachments);
      setContent("");
      setAttachments([]);
      onClearReply();
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="composer" data-testid="chat-composer">
      {replyTo && <ReplyPreview preview={{ id: replyTo.id, sender_username: replyTo.sender_username, content: replyTo.content }} onClear={onClearReply} />}
      {disabled ? (
        <p className="composer-disabled-note" data-testid="composer-disabled-note">{disabledReason || "You cannot send messages here."}</p>
      ) : (
        <>
          <textarea
            className="textarea composer-input"
            placeholder="Type a message..."
            value={content}
            data-testid="composer-input"
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <div className="composer-actions">
            <AttachmentUploader ticketId={ticketId} attachments={attachments} onChange={setAttachments} />
            <button className="btn btn-primary btn-sm" data-testid="composer-send-button" onClick={handleSend} disabled={sending}>
              <Send size={14} /> Send
            </button>
          </div>
        </>
      )}
    </div>
  );
}
