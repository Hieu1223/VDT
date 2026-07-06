export type UserRole = "employee" | "technician_human" | "technician_virtual" | "admin";
export type UserStatus = "pending_activation" | "active" | "suspended" | "deactivated";
export type TicketStatus = "new" | "assigned" | "in_progress" | "escalated" | "resolved" | "rejected" | "closed";
export type Priority = "P1" | "P2" | "P3" | "P4";
export type Level = "high" | "medium" | "low";
export type RequestStatus = "pending" | "approved" | "rejected" | "returned";
export type RequestType = "escalation" | "reassignment";

export interface User {
  id: string;
  username: string;
  full_name: string;
  email?: string | null;
  role: UserRole;
  status: UserStatus;
  online: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
  ws_connected?: boolean;
}

export interface SlaBlock {
  first_response_due_at?: string | null;
  resolve_due_at?: string | null;
  first_responded_at?: string | null;
  resolved_at?: string | null;
  first_response_breached: boolean;
  resolve_breached: boolean;
  first_response_near_breach: boolean;
  resolve_near_breach: boolean;
}

export interface LockBlock {
  locked_by?: string | null;
  locked_by_username?: string | null;
  locked_at?: string | null;
  expires_at?: string | null;
}

export interface Ticket {
  id: string;
  subject: string;
  description: string;
  category: string;
  impact: Level;
  urgency: Level;
  priority: Priority;
  status: TicketStatus;
  requester_id: string;
  requester_username: string;
  assignee_id?: string | null;
  assignee_username?: string | null;
  tags: string[];
  sla?: SlaBlock | null;
  lock?: LockBlock | null;
  resolution_note?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  filename: string;
  url: string;
  content_type: string;
  size: number;
}

export interface ReplyPreview {
  id: string;
  sender_username: string;
  content: string;
}

export interface Message {
  id: string;
  ticket_id: string;
  sender_id: string;
  sender_username: string;
  sender_role: UserRole;
  content: string;
  attachments: Attachment[];
  reply_to_message_id?: string | null;
  reply_preview?: ReplyPreview | null;
  edited_at?: string | null;
  deleted_at?: string | null;
  created_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  ticket_id?: string | null;
  read_at?: string | null;
  dispatched: boolean;
  created_at: string;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface EscalationRequest {
  id: string;
  type: RequestType;
  ticket_id: string;
  requested_by: string;
  requested_by_username: string;
  reason: string;
  target_technician_id?: string | null;
  status: RequestStatus;
  reviewed_by?: string | null;
  review_note?: string | null;
  created_at: string;
  reviewed_at?: string | null;
}

export interface CsatSurvey {
  id: string;
  ticket_id: string;
  technician_id: string;
  technician_username?: string;
  requester_id: string;
  requester_username?: string;
  ticket_subject?: string;
  rating?: number | null;
  comment?: string | null;
  status: "pending" | "submitted";
  created_at: string;
  submitted_at?: string | null;
}

export interface BusinessCalendar {
  business_days: number[];
  start_hour: number;
  start_minute: number;
  end_hour: number;
  end_minute: number;
  holidays: string[];
}

export interface TimelineEvent {
  id: string;
  domain: string;
  event_type: string;
  routing_key: string;
  payload: Record<string, any>;
  actor_id?: string | null;
  ticket_id?: string | null;
  created_at: string;
}
