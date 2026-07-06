import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, ArrowUpRight, RefreshCw, Unlock } from "lucide-react";
import { escalationApi, locksApi, tagsApi, ticketsApi, usersApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { useNotifications } from "@/context/NotificationContext";
import StatusStepper from "@/components/badges/StatusStepper";
import PriorityBadge from "@/components/badges/PriorityBadge";
import LockBadge from "@/components/badges/LockBadge";
import TagPicker from "@/components/tagpicker/TagPicker";
import ChatRoom from "@/components/chat/ChatRoom";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { Tag, Ticket, User } from "@/types";
import "@/pages/tickets/Tickets.css";

const TECHNICIAN_ROLES = ["technician_human", "technician_virtual"];
const OPEN_STATUSES = ["new", "assigned", "in_progress", "escalated"];

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { notifications } = useNotifications();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [technicians, setTechnicians] = useState<User[]>([]);
  const [resolveNote, setResolveNote] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [escalateReason, setEscalateReason] = useState("");
  const [reassignReason, setReassignReason] = useState("");
  const [reassignTarget, setReassignTarget] = useState("");
  const [showResolve, setShowResolve] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const [showEscalate, setShowEscalate] = useState(false);
  const [showReassign, setShowReassign] = useState(false);

  const isTechnicianOrAdmin = !!user && (TECHNICIAN_ROLES.includes(user.role) || user.role === "admin");
  const isOpen = !!ticket && OPEN_STATUSES.includes(ticket.status);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const { data } = await ticketsApi.get(id);
      setTicket(data);
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Ticket not found.");
    }
  }, [id]);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  useEffect(() => {
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, [load]);

  useEffect(() => {
    if (isTechnicianOrAdmin) {
      tagsApi.list().then(({ data }) => setAvailableTags(data)).catch(() => {});
      usersApi.technicians().then(({ data }) => setTechnicians(data)).catch(() => {});
    }
  }, [isTechnicianOrAdmin]);

  useEffect(() => {
    const relevant = notifications.find((n) => n.ticket_id === id);
    if (relevant) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notifications, id]);

  useEffect(() => {
    if (!id || !isTechnicianOrAdmin || !isOpen) return;
    locksApi.acquire(id).then(({ data }) => setTicket(data)).catch(() => {});
    const heartbeat = setInterval(() => {
      locksApi.refresh(id).then(({ data }) => setTicket(data)).catch(() => {});
    }, 90000);
    return () => {
      clearInterval(heartbeat);
      locksApi.release(id).catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, isTechnicianOrAdmin, isOpen]);

  const holdsLock = ticket?.lock?.locked_by === user?.id;
  const lockedByOther = !!ticket?.lock?.locked_by && !holdsLock;
  const canManage = isTechnicianOrAdmin && !lockedByOther;
  const isAssignee = ticket?.assignee_id === user?.id;

  const runAction = async (fn: () => Promise<any>) => {
    setActionError("");
    try {
      await fn();
      await load();
    } catch (err: any) {
      setActionError(formatApiError(err?.response?.data?.detail) || "Action failed.");
    }
  };

  if (loading) return <LoadingSpinner fullPage />;
  if (error || !ticket) {
    return (
      <div className="page">
        <div className="form-error" data-testid="ticket-detail-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="page ticket-detail-page" data-testid="ticket-detail-page">
      <div className="page-header">
        <div>
          <span className="text-muted label">Ticket #{ticket.id.slice(0, 8)}</span>
          <h1>{ticket.subject}</h1>
        </div>
        <div className="ticket-detail-badges">
          <PriorityBadge priority={ticket.priority} />
          {isTechnicianOrAdmin && <LockBadge lock={ticket.lock} currentUserId={user?.id} />}
        </div>
      </div>

      {actionError && <div className="form-error" data-testid="ticket-detail-action-error">{actionError}</div>}

      <StatusStepper status={ticket.status} />

      <div className="ticket-detail-grid">
        <div className="ticket-detail-main card">
          <h3>Description</h3>
          <p className="ticket-detail-description">{ticket.description}</p>

          <div className="ticket-detail-meta">
            <div><span className="label">Category</span><p>{ticket.category}</p></div>
            <div><span className="label">Requester</span><p>{ticket.requester_username}</p></div>
            <div><span className="label">Assignee</span><p>{ticket.assignee_username || "Unassigned"}</p></div>
          </div>

          <div className="ticket-detail-tags">
            <span className="label">Tags</span>
            <TagPicker
              tags={ticket.tags}
              availableTags={availableTags}
              readOnly={!isTechnicianOrAdmin}
              onAttach={(tag) => runAction(() => tagsApi.attach(ticket.id, tag))}
              onDetach={(tag) => runAction(() => tagsApi.detach(ticket.id, tag))}
            />
          </div>

          {ticket.resolution_note && (
            <div className="ticket-detail-note ticket-detail-note-success">
              <strong>Resolution:</strong> {ticket.resolution_note}
            </div>
          )}
          {ticket.rejection_reason && (
            <div className="ticket-detail-note ticket-detail-note-danger">
              <strong>Rejection reason:</strong> {ticket.rejection_reason}
            </div>
          )}

          {ticket.status === "resolved" && user?.role === "employee" && (
            <Link to={`/csat/${ticket.id}`} className="btn btn-primary" data-testid="ticket-detail-csat-link">
              Rate your experience
            </Link>
          )}

          {isTechnicianOrAdmin && isOpen && (
            <div className="ticket-detail-actions">
              {lockedByOther && (
                <p className="text-muted ticket-lock-warning" data-testid="ticket-locked-warning">
                  <AlertTriangle size={14} /> Locked by {ticket.lock?.locked_by_username}. {user?.role === "admin" && "You can force-release below."}
                </p>
              )}
              {user?.role === "admin" && lockedByOther && (
                <button className="btn btn-secondary btn-sm" data-testid="ticket-force-release-lock-button" onClick={() => runAction(() => locksApi.forceRelease(ticket.id))}>
                  <Unlock size={14} /> Force release lock
                </button>
              )}

              {canManage && (
                <div className="ticket-action-group">
                  <button className="btn btn-primary btn-sm" data-testid="ticket-open-resolve-button" onClick={() => setShowResolve((s) => !s)}>Resolve</button>
                  <button className="btn btn-danger btn-sm" data-testid="ticket-open-reject-button" onClick={() => setShowReject((s) => !s)}>Reject</button>
                  {isAssignee && (
                    <>
                      <button className="btn btn-secondary btn-sm" data-testid="ticket-open-escalate-button" onClick={() => setShowEscalate((s) => !s)}>
                        <ArrowUpRight size={14} /> Escalate
                      </button>
                      <button className="btn btn-secondary btn-sm" data-testid="ticket-open-reassign-button" onClick={() => setShowReassign((s) => !s)}>
                        <RefreshCw size={14} /> Request Reassignment
                      </button>
                    </>
                  )}
                </div>
              )}

              {showResolve && canManage && (
                <div className="ticket-inline-form">
                  <textarea className="textarea" placeholder="Resolution note..." value={resolveNote} data-testid="ticket-resolve-note-input" onChange={(e) => setResolveNote(e.target.value)} />
                  <button className="btn btn-primary btn-sm" data-testid="ticket-confirm-resolve-button" onClick={() => runAction(() => ticketsApi.resolve(ticket.id, resolveNote))}>Confirm resolve</button>
                </div>
              )}
              {showReject && canManage && (
                <div className="ticket-inline-form">
                  <textarea className="textarea" placeholder="Rejection reason..." value={rejectReason} data-testid="ticket-reject-reason-input" onChange={(e) => setRejectReason(e.target.value)} />
                  <button className="btn btn-danger btn-sm" data-testid="ticket-confirm-reject-button" onClick={() => runAction(() => ticketsApi.reject(ticket.id, rejectReason))}>Confirm reject</button>
                </div>
              )}
              {showEscalate && canManage && (
                <div className="ticket-inline-form">
                  <textarea className="textarea" placeholder="Why does this need escalation?" value={escalateReason} data-testid="ticket-escalate-reason-input" onChange={(e) => setEscalateReason(e.target.value)} />
                  <button className="btn btn-secondary btn-sm" data-testid="ticket-confirm-escalate-button" onClick={() => runAction(() => escalationApi.escalate(ticket.id, escalateReason))}>Submit escalation</button>
                </div>
              )}
              {showReassign && canManage && (
                <div className="ticket-inline-form">
                  <textarea className="textarea" placeholder="Why reassign this ticket?" value={reassignReason} data-testid="ticket-reassign-reason-input" onChange={(e) => setReassignReason(e.target.value)} />
                  <select className="select" value={reassignTarget} data-testid="ticket-reassign-target-select" onChange={(e) => setReassignTarget(e.target.value)}>
                    <option value="">Select technician...</option>
                    {technicians.filter((t) => t.id !== user?.id).map((t) => (
                      <option key={t.id} value={t.id}>{t.full_name} ({t.username})</option>
                    ))}
                  </select>
                  <button className="btn btn-secondary btn-sm" data-testid="ticket-confirm-reassign-button" disabled={!reassignTarget} onClick={() => runAction(() => escalationApi.reassignRequest(ticket.id, reassignReason, reassignTarget))}>Submit reassignment request</button>
                </div>
              )}
            </div>
          )}
        </div>

        {isTechnicianOrAdmin && ticket.sla && (
          <div className="ticket-detail-sla card">
            <h3>SLA</h3>
            <SlaRow label="First response due" value={ticket.sla.first_response_due_at} breached={ticket.sla.first_response_breached} near={ticket.sla.first_response_near_breach} met={!!ticket.sla.first_responded_at} />
            <SlaRow label="Resolve due" value={ticket.sla.resolve_due_at} breached={ticket.sla.resolve_breached} near={ticket.sla.resolve_near_breach} met={!!ticket.sla.resolved_at} />
          </div>
        )}
      </div>

      <div className="ticket-detail-chat">
        <h3>Conversation</h3>
        <ChatRoom
          ticketId={ticket.id}
          canPost={isOpen ? (user?.role === "employee" ? ticket.requester_id === user.id : isTechnicianOrAdmin) : false}
          disabledReason={!isOpen ? "This ticket is closed and no longer accepting messages." : undefined}
        />
      </div>
    </div>
  );
}

function SlaRow({ label, value, breached, near, met }: { label: string; value?: string | null; breached: boolean; near: boolean; met: boolean }) {
  let cls = "sla-row-ok";
  if (breached) cls = "sla-row-breach";
  else if (near) cls = "sla-row-warning";
  else if (met) cls = "sla-row-met";

  return (
    <div className={`sla-row ${cls}`} data-testid={`sla-row-${label.replace(/\s+/g, "-").toLowerCase()}`}>
      <span className="label">{label}</span>
      <span>{value ? new Date(value).toLocaleString() : "-"}</span>
      {breached && <span className="sla-row-flag">Breached</span>}
      {!breached && near && <span className="sla-row-flag">Near breach</span>}
      {met && !breached && <span className="sla-row-flag sla-row-flag-ok">Met</span>}
    </div>
  );
}
