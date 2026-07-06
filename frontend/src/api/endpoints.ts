import { apiClient } from "@/api/client";
import type {
  BusinessCalendar, CsatSurvey, EscalationRequest, Message, Notification, Paginated, Tag, Ticket, TimelineEvent, User,
} from "@/types";

// ---- Auth ----
export const authApi = {
  register: (payload: { username: string; password: string; full_name: string; email?: string; role: string }) =>
    apiClient.post<User>("/auth/register", payload),
  login: (username: string, password: string) => apiClient.post("/auth/login", { username, password }),
  me: () => apiClient.get<User>("/auth/me"),
  logout: () => apiClient.post("/auth/logout"),
};

// ---- Users ----
export const usersApi = {
  updateProfile: (payload: Partial<{ full_name: string; email: string }>) =>
    apiClient.patch<User>("/users/me", payload),
  changePassword: (current_password: string, new_password: string) =>
    apiClient.post("/users/me/change-password", { current_password, new_password }),
  heartbeat: () => apiClient.post("/users/me/heartbeat"),
  technicians: () => apiClient.get<User[]>("/users/technicians"),
  adminList: (params?: { role?: string; status?: string; search?: string; online?: boolean; date_from?: string; date_to?: string; page?: number; page_size?: number }) =>
    apiClient.get<Paginated<User>>("/users", { params }),
  adminCreate: (payload: { username: string; password: string; full_name: string; email?: string; role: string }) =>
    apiClient.post<User>("/users", payload),
  adminUpdateStatus: (userId: string, status: string) => apiClient.patch<User>(`/users/${userId}/status`, { status }),
};

// ---- Tickets ----
export const ticketsApi = {
  create: (payload: { subject: string; description: string; category: string; impact: string; urgency: string }) =>
    apiClient.post<Ticket>("/tickets", payload),
  mine: (params?: { tag?: string; date_from?: string; date_to?: string }) => apiClient.get<Ticket[]>("/tickets", { params }),
  queue: (params?: { tag?: string; date_from?: string; date_to?: string; sla_min_pct?: number }) =>
    apiClient.get<Ticket[]>("/tickets/queue", { params }),
  all: (params?: { status?: string; priority?: string; assignee_id?: string; search?: string; tag?: string; date_from?: string; date_to?: string; sla_min_pct?: number; page?: number; page_size?: number }) =>
    apiClient.get<Paginated<Ticket>>("/tickets/all", { params }),
  get: (id: string) => apiClient.get<Ticket>(`/tickets/${id}`),
  resolve: (id: string, resolution_note: string) => apiClient.post<Ticket>(`/tickets/${id}/resolve`, { resolution_note }),
  reject: (id: string, rejection_reason: string) => apiClient.post<Ticket>(`/tickets/${id}/reject`, { rejection_reason }),
  priorityMatrix: () => apiClient.get("/tickets/config/priority-matrix"),
  updatePriorityMatrix: (impact: string, urgency: string, priority: string) =>
    apiClient.patch(`/tickets/config/priority-matrix/${impact}/${urgency}`, { priority }),
  slaPolicies: () => apiClient.get("/tickets/config/sla-policies"),
  updateSlaPolicy: (priority: string, payload: { first_response_minutes: number; resolve_minutes: number }) =>
    apiClient.patch(`/tickets/config/sla-policies/${priority}`, payload),
};

// ---- Business calendar ----
export const calendarApi = {
  get: () => apiClient.get<BusinessCalendar>("/calendar"),
  update: (payload: BusinessCalendar) => apiClient.put<BusinessCalendar>("/calendar", payload),
};

// ---- Locks ----
export const locksApi = {
  acquire: (ticketId: string) => apiClient.post<Ticket>(`/tickets/${ticketId}/lock`),
  refresh: (ticketId: string) => apiClient.post<Ticket>(`/tickets/${ticketId}/lock/refresh`),
  release: (ticketId: string) => apiClient.delete<Ticket>(`/tickets/${ticketId}/lock`),
  forceRelease: (ticketId: string) => apiClient.post<Ticket>(`/tickets/${ticketId}/lock/force-release`),
};

// ---- Messages ----
export const messagesApi = {
  list: (ticketId: string) => apiClient.get<Message[]>(`/tickets/${ticketId}/messages`),
  send: (ticketId: string, payload: { content: string; reply_to_message_id?: string | null; attachments?: any[] }) =>
    apiClient.post<Message>(`/tickets/${ticketId}/messages`, payload),
  upload: (ticketId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.post(`/tickets/${ticketId}/messages/upload`, form, { headers: { "Content-Type": "multipart/form-data" } });
  },
  edit: (ticketId: string, messageId: string, content: string) =>
    apiClient.patch<Message>(`/tickets/${ticketId}/messages/${messageId}`, { content }),
  remove: (ticketId: string, messageId: string) => apiClient.delete<Message>(`/tickets/${ticketId}/messages/${messageId}`),
};

// ---- Tags ----
export const tagsApi = {
  list: () => apiClient.get<Tag[]>("/tags"),
  create: (name: string, color: string) => apiClient.post<Tag>("/tags", { name, color }),
  remove: (tagId: string) => apiClient.delete(`/tags/${tagId}`),
  attach: (ticketId: string, tag: string) => apiClient.post<Ticket>(`/tickets/${ticketId}/tags`, { tag }),
  detach: (ticketId: string, tag: string) => apiClient.delete<Ticket>(`/tickets/${ticketId}/tags/${tag}`),
};

// ---- Escalation / Reassignment ----
export const escalationApi = {
  escalate: (ticketId: string, reason: string, suggested_target_id?: string) =>
    apiClient.post(`/tickets/${ticketId}/escalate`, { reason, suggested_target_id }),
  reassignRequest: (ticketId: string, reason: string, target_technician_id: string) =>
    apiClient.post(`/tickets/${ticketId}/reassign-request`, { reason, target_technician_id }),
  mine: () => apiClient.get<EscalationRequest[]>("/requests/mine"),
  pending: () => apiClient.get<EscalationRequest[]>("/requests/pending"),
  approve: (requestId: string, target_technician_id?: string, note?: string) =>
    apiClient.post(`/requests/${requestId}/approve`, { target_technician_id, note }),
  reject: (requestId: string, note?: string) => apiClient.post(`/requests/${requestId}/reject`, { note }),
  returnToRequester: (requestId: string, note?: string) => apiClient.post(`/requests/${requestId}/return`, { note }),
};

// ---- Assignment config ----
export const assignmentApi = {
  getConfig: () => apiClient.get<{ active_algorithm: string; available_algorithms: string[] }>("/assignment/config"),
  setConfig: (algorithm: string) => apiClient.put("/assignment/config", { algorithm }),
};

// ---- Notifications ----
export const notificationsApi = {
  list: () => apiClient.get<Notification[]>("/notifications"),
  markRead: (id: string) => apiClient.post(`/notifications/${id}/read`),
  markAllRead: () => apiClient.post("/notifications/read-all"),
};

// ---- CSAT ----
export const csatApi = {
  get: (ticketId: string) => apiClient.get<CsatSurvey>(`/csat/${ticketId}`),
  submit: (ticketId: string, rating: number, comment?: string) =>
    apiClient.post<CsatSurvey>(`/csat/${ticketId}`, { rating, comment }),
  adminList: (params?: { status?: string; rating_min?: number; rating_max?: number; technician_id?: string; date_from?: string; date_to?: string; page?: number; page_size?: number }) =>
    apiClient.get<Paginated<CsatSurvey>>("/csat", { params }),
};

// ---- Filters ----
export const filtersApi = {
  ticketOptions: () => apiClient.get("/filters/tickets"),
};

// ---- Admin suite ----
export const kanbanApi = { board: () => apiClient.get<Record<string, any[]>>("/kanban/board") };
export const timelineApi = { list: (params?: { ticket_id?: string; limit?: number }) => apiClient.get<TimelineEvent[]>("/timeline", { params }) };
export const monitorApi = {
  users: () => apiClient.get<User[]>("/monitor/users"),
  tickets: () => apiClient.get("/monitor/tickets"),
};
