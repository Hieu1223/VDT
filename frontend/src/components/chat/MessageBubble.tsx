import React, { useState } from "react";
import { CornerUpLeft, Paperclip, Pencil, Trash2 } from "lucide-react";
import type { Message } from "@/types";
import ReplyPreview from "@/components/chat/ReplyPreview";
import "@/components/chat/Chat.css";

interface Props {
  message: Message;
  isMine: boolean;
  onReply: (message: Message) => void;
  onEdit: (message: Message, content: string) => Promise<void>;
  onDelete: (message: Message) => Promise<void>;
}

export default function MessageBubble({ message, isMine, onReply, onEdit, onDelete }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(message.content);

  const isDeleted = !!message.deleted_at;

  const saveEdit = async () => {
    if (draft.trim() && draft !== message.content) {
      await onEdit(message, draft.trim());
    }
    setEditing(false);
  };

  return (
    <div className={`message-bubble-row ${isMine ? "message-bubble-row-mine" : ""} fade-in`} data-testid={`message-bubble-${message.id}`}>
      <div className={`message-bubble ${isMine ? "message-bubble-mine" : "message-bubble-other"}`}>
        {!isMine && <span className="message-bubble-sender">{message.sender_username}</span>}
        {message.reply_preview && <ReplyPreview preview={message.reply_preview} />}

        {editing ? (
          <div className="message-bubble-edit">
            <textarea className="textarea" value={draft} onChange={(e) => setDraft(e.target.value)} data-testid={`message-edit-input-${message.id}`} />
            <div className="message-bubble-edit-actions">
              <button className="btn btn-secondary btn-sm" onClick={() => setEditing(false)} data-testid={`message-edit-cancel-${message.id}`}>Cancel</button>
              <button className="btn btn-primary btn-sm" onClick={saveEdit} data-testid={`message-edit-save-${message.id}`}>Save</button>
            </div>
          </div>
        ) : (
          <p className="message-bubble-content">{message.content}</p>
        )}

        {!isDeleted && message.attachments.length > 0 && (
          <div className="message-bubble-attachments">
            {message.attachments.map((a) => (
              <a key={a.url} href={a.url} target="_blank" rel="noopener noreferrer" className="message-bubble-attachment" data-testid={`message-attachment-${message.id}`}>
                <Paperclip size={14} /> {a.filename}
              </a>
            ))}
          </div>
        )}

        <div className="message-bubble-footer">
          <span className="message-bubble-time">
            {new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            {message.edited_at && !isDeleted && " · edited"}
          </span>
          {!isDeleted && !editing && (
            <div className="message-bubble-actions">
              <button type="button" data-testid={`message-reply-button-${message.id}`} onClick={() => onReply(message)} title="Reply">
                <CornerUpLeft size={14} />
              </button>
              {isMine && (
                <>
                  <button type="button" data-testid={`message-edit-button-${message.id}`} onClick={() => setEditing(true)} title="Edit">
                    <Pencil size={14} />
                  </button>
                  <button type="button" data-testid={`message-delete-button-${message.id}`} onClick={() => onDelete(message)} title="Delete">
                    <Trash2 size={14} />
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
