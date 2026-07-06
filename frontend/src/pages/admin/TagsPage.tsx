import React, { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { tagsApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { Tag } from "@/types";
import "@/pages/admin/Admin.css";

export default function TagsPage() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [color, setColor] = useState("#003BFF");
  const [error, setError] = useState("");

  const load = () => tagsApi.list().then(({ data }) => setTags(data));

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await tagsApi.create(name.trim(), color);
      setName("");
      await load();
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not create tag.");
    }
  };

  const handleDelete = async (id: string) => {
    await tagsApi.remove(id);
    await load();
  };

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="tags-page">
      <div className="page-header">
        <div>
          <h1>Tags</h1>
          <p className="text-muted">Manage the master tag list used across tickets.</p>
        </div>
      </div>

      {error && <div className="form-error" data-testid="tags-error-message">{error}</div>}

      <form className="card tags-create-form" onSubmit={handleCreate} data-testid="tags-create-form">
        <input className="input" placeholder="Tag name" value={name} data-testid="tags-name-input" onChange={(e) => setName(e.target.value)} required />
        <input type="color" value={color} data-testid="tags-color-input" onChange={(e) => setColor(e.target.value)} />
        <button type="submit" className="btn btn-primary" data-testid="tags-create-submit-button">Add tag</button>
      </form>

      {tags.length === 0 ? (
        <EmptyState title="No tags yet" testId="tags-empty" />
      ) : (
        <div className="tags-grid">
          {tags.map((t) => (
            <div key={t.id} className="tags-chip-card card" data-testid={`tags-chip-${t.id}`}>
              <span className="tag-chip" style={{ background: `${t.color}22`, color: t.color }}>{t.name}</span>
              <button className="btn btn-ghost btn-sm" data-testid={`tags-delete-${t.id}`} onClick={() => handleDelete(t.id)}>
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
