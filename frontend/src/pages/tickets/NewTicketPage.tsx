import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ticketsApi, usersApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import type { User } from "@/types";
import "@/pages/tickets/Tickets.css";

export default function NewTicketPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [form, setForm] = useState({ subject: "", description: "", category: "hardware", impact: "medium", urgency: "medium", requester_id: "" });
  const [employees, setEmployees] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      usersApi.adminList({ role: "employee", status: "active" }).then(({ data }) => setEmployees(data)).catch(() => {});
    }
  }, [isAdmin]);

  const update = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const payload: any = { ...form };
      if (!isAdmin || !payload.requester_id) delete payload.requester_id;
      const { data } = await ticketsApi.create(payload);
      navigate(`/tickets/${data.id}`);
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not create ticket.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page" data-testid="new-ticket-page">
      <div className="page-header">
        <div>
          <h1>New Ticket</h1>
          <p className="text-muted">{isAdmin ? "Create a ticket on behalf of an employee." : "Describe your issue and we'll route it to the right technician."}</p>
        </div>
      </div>

      {error && <div className="form-error" data-testid="new-ticket-error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="card new-ticket-form" data-testid="new-ticket-form">
        {isAdmin && (
          <div className="field">
            <label className="label" htmlFor="ticket-requester">Requester</label>
            <select id="ticket-requester" className="select" data-testid="new-ticket-requester-select" value={form.requester_id} onChange={(e) => update("requester_id", e.target.value)} required>
              <option value="">Select employee...</option>
              {employees.map((emp) => <option key={emp.id} value={emp.id}>{emp.full_name} ({emp.username})</option>)}
            </select>
          </div>
        )}
        <div className="field">
          <label className="label" htmlFor="ticket-subject">Subject</label>
          <input id="ticket-subject" className="input" data-testid="new-ticket-subject-input" value={form.subject} onChange={(e) => update("subject", e.target.value)} required minLength={3} />
        </div>
        <div className="field">
          <label className="label" htmlFor="ticket-description">Description</label>
          <textarea id="ticket-description" className="textarea" data-testid="new-ticket-description-input" value={form.description} onChange={(e) => update("description", e.target.value)} required minLength={3} />
        </div>
        <div className="new-ticket-form-row">
          <div className="field">
            <label className="label" htmlFor="ticket-category">Category</label>
            <select id="ticket-category" className="select" data-testid="new-ticket-category-select" value={form.category} onChange={(e) => update("category", e.target.value)}>
              <option value="hardware">Hardware</option>
              <option value="software">Software</option>
              <option value="network">Network</option>
              <option value="access">Access / Permissions</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="field">
            <label className="label" htmlFor="ticket-impact">Impact</label>
            <select id="ticket-impact" className="select" data-testid="new-ticket-impact-select" value={form.impact} onChange={(e) => update("impact", e.target.value)}>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="field">
            <label className="label" htmlFor="ticket-urgency">Urgency</label>
            <select id="ticket-urgency" className="select" data-testid="new-ticket-urgency-select" value={form.urgency} onChange={(e) => update("urgency", e.target.value)}>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
        <button type="submit" className="btn btn-primary" data-testid="new-ticket-submit-button" disabled={submitting}>
          {submitting ? "Submitting..." : "Submit Ticket"}
        </button>
      </form>
    </div>
  );
}
