import React, { useRef, useState } from "react";
import { Paperclip, X } from "lucide-react";
import { messagesApi } from "@/api/endpoints";
import type { Attachment } from "@/types";
import "@/components/chat/Chat.css";

interface Props {
  ticketId: string;
  attachments: Attachment[];
  onChange: (attachments: Attachment[]) => void;
}

export default function AttachmentUploader({ ticketId, attachments, onChange }: Props) {
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
      onChange([...attachments, ...uploaded]);
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
        disabled={uploading}
      >
        <Paperclip size={16} /> {uploading ? "Uploading..." : "Attach"}
      </button>
      {attachments.length > 0 && (
        <div className="attachment-uploader-list">
          {attachments.map((a, idx) => (
            <span key={a.url} className="attachment-chip" data-testid={`attachment-pending-${idx}`}>
              {a.filename}
              <button type="button" onClick={() => onChange(attachments.filter((x) => x.url !== a.url))} data-testid={`attachment-remove-${idx}`}>
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
