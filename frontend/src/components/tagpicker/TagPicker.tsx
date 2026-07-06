import React, { useState } from "react";
import { Plus, X } from "lucide-react";
import type { Tag } from "@/types";
import "@/components/tagpicker/TagPicker.css";

interface Props {
  tags: string[];
  availableTags: Tag[];
  onAttach: (tag: string) => Promise<void> | void;
  onDetach: (tag: string) => Promise<void> | void;
  readOnly?: boolean;
}

export default function TagPicker({ tags, availableTags, onAttach, onDetach, readOnly }: Props) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");

  const suggestions = availableTags.filter((t) => !tags.includes(t.name) && t.name.includes(value.toLowerCase()));

  const submit = async (name: string) => {
    if (!name.trim()) return;
    await onAttach(name.trim());
    setValue("");
    setOpen(false);
  };

  return (
    <div className="tag-picker" data-testid="tag-picker">
      {tags.map((tag) => (
        <span key={tag} className="tag-chip" data-testid={`tag-chip-${tag}`}>
          {tag}
          {!readOnly && (
            <button type="button" aria-label={`remove-${tag}`} onClick={() => onDetach(tag)} data-testid={`tag-remove-${tag}`}>
              <X size={12} />
            </button>
          )}
        </span>
      ))}
      {!readOnly && (
        <div className="tag-picker-add">
          {open ? (
            <div className="tag-picker-dropdown">
              <input
                autoFocus
                className="input"
                placeholder="Tag name..."
                value={value}
                data-testid="tag-picker-input"
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit(value)}
              />
              {suggestions.length > 0 && (
                <ul className="tag-picker-suggestions">
                  {suggestions.slice(0, 6).map((s) => (
                    <li key={s.id}>
                      <button type="button" data-testid={`tag-suggestion-${s.name}`} onClick={() => submit(s.name)}>{s.name}</button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <button type="button" className="tag-picker-trigger" data-testid="tag-picker-open-button" onClick={() => setOpen(true)}>
              <Plus size={12} /> Add tag
            </button>
          )}
        </div>
      )}
    </div>
  );
}
