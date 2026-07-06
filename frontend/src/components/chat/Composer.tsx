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
  const [sending, setSending] = useState(false);

  const handleSendText = async () => {
    if (!content.trim()) return;
    setSending(true);
    try {
      await onSend(content.trim(), replyTo?.id || null, []);
      setContent("");
      onClearReply();
    } finally {
      setSending(false);
    }
  };

  const handleSendFiles = async (attachments: Attachment[]) => {
    await onSend("", replyTo?.id || null, attachments);
    onClearReply();
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
                handleSendText();
              }
            }}
          />
          <div className="composer-actions">
            <AttachmentUploader ticketId={ticketId} onSendFiles={handleSendFiles} disabled={sending} />
            <button className="btn btn-primary btn-sm" data-testid="composer-send-button" onClick={handleSendText} disabled={sending || !content.trim()}>
              <Send size={14} /> Send
            </button>
          </div>
        </>
      )}
    </div>
  );
}
