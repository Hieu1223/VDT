"""Enumerations shared across all backend modules."""
from enum import Enum


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    TECHNICIAN_HUMAN = "technician_human"
    TECHNICIAN_VIRTUAL = "technician_virtual"
    ADMIN = "admin"


TECHNICIAN_ROLES = {UserRole.TECHNICIAN_HUMAN, UserRole.TECHNICIAN_VIRTUAL}


class UserStatus(str, Enum):
    PENDING_ACTIVATION = "pending_activation"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class TicketStatus(str, Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    CLOSED = "closed"


OPEN_TICKET_STATUSES = {
    TicketStatus.NEW,
    TicketStatus.ASSIGNED,
    TicketStatus.IN_PROGRESS,
    TicketStatus.ESCALATED,
}


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class Level(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"


class RequestType(str, Enum):
    ESCALATION = "escalation"
    REASSIGNMENT = "reassignment"


class EventDomain(str, Enum):
    USER = "user"
    TICKET = "ticket"
    MESSAGE = "message"
    ESCALATION = "escalation"
    REASSIGN = "reassign"
    SLA = "sla"
    CSAT = "csat"
    TAG = "tag"
    LOCK = "lock"
    ASSIGNMENT = "assignment"


class EventType(str, Enum):
    USER_REGISTERED = "USER_REGISTERED"
    USER_ACTIVATED = "USER_ACTIVATED"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    USER_ONLINE = "USER_ONLINE"
    USER_OFFLINE = "USER_OFFLINE"

    TICKET_CREATED = "TICKET_CREATED"
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    TICKET_STATUS_CHANGED = "TICKET_STATUS_CHANGED"
    TICKET_RESOLVED = "TICKET_RESOLVED"
    TICKET_REJECTED = "TICKET_REJECTED"

    TAG_ADDED = "TAG_ADDED"
    TAG_REMOVED = "TAG_REMOVED"

    LOCK_ACQUIRED = "LOCK_ACQUIRED"
    LOCK_REFRESHED = "LOCK_REFRESHED"
    LOCK_RELEASED = "LOCK_RELEASED"
    LOCK_EXPIRED = "LOCK_EXPIRED"

    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_EDITED = "MESSAGE_EDITED"
    MESSAGE_DELETED = "MESSAGE_DELETED"

    ESCALATION_REQUESTED = "ESCALATION_REQUESTED"
    ESCALATION_APPROVED = "ESCALATION_APPROVED"
    ESCALATION_REJECTED = "ESCALATION_REJECTED"
    ESCALATION_RETURNED = "ESCALATION_RETURNED"

    REASSIGN_REQUESTED = "REASSIGN_REQUESTED"
    REASSIGN_APPROVED = "REASSIGN_APPROVED"
    REASSIGN_REJECTED = "REASSIGN_REJECTED"
    REASSIGN_RETURNED = "REASSIGN_RETURNED"

    SLA_NEAR_BREACH_FIRST_RESPONSE = "SLA_NEAR_BREACH_FIRST_RESPONSE"
    SLA_BREACHED_FIRST_RESPONSE = "SLA_BREACHED_FIRST_RESPONSE"
    SLA_NEAR_BREACH_RESOLVE = "SLA_NEAR_BREACH_RESOLVE"
    SLA_BREACHED_RESOLVE = "SLA_BREACHED_RESOLVE"

    CSAT_REQUESTED = "CSAT_REQUESTED"
    CSAT_SUBMITTED = "CSAT_SUBMITTED"


class NotificationType(str, Enum):
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    NEW_MESSAGE = "new_message"
    ESCALATION_UPDATE = "escalation_update"
    REASSIGN_UPDATE = "reassign_update"
    SLA_ALERT = "sla_alert"
    CSAT_REQUEST = "csat_request"
    USER_LIFECYCLE = "user_lifecycle"
