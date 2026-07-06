import React, { useRef, useState } from "react";
import { Paperclip } from "lucide-react";
import { messagesApi } from "@/api/endpoints";
import type { Attachment } from "@/types";
import "@/components/chat/Chat.css";

interface Props {
  ticketId: string;
  onSendFiles: (attachments: Attachment[]) => Promise<void>;
  disabled?: boolean;
}

/** Messenger-style file sharing: picking a file immediately uploads it and
 * sends it as its own message (no separate "attach, then type, then send"
 * step). Images/videos render inline in the chat; anything else renders as
 * a downloadable file chip - see MessageBubble. */
export default function AttachmentUploader({ ticketId, onSendFiles, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      const uploaded: Attachment[] = [];
      for (const file of Array.from(files)) {
        const { data } = await messagesApi.upload(ticketId, file);
        uploaded.push(data);
      }
      await onSendFiles(uploaded);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className="attachment-uploader">
      <input
        ref={inputRef}
        type="file"
        multiple
        hidden
        data-testid="attachment-file-input"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        data-testid="attachment-upload-trigger-button"
        onClick={() => inputRef.current?.click()}
        disabled={uploading || disabled}
        title="Send a file"
      >
        <Paperclip size={16} /> {uploading ? "Sending..." : ""}
      </button>
    </div>
  );
}
