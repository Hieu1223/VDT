"""
End-to-end backend tests for the Helpdesk/ITSM platform.
Covers: auth, ticket lifecycle + auto-assignment, locks, chat/upload,
resolve + CSAT, reject, tags, escalation/reassignment review flows,
admin config, kanban, timeline, monitor.
"""
import io
import time
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fall back to reading frontend/.env directly if not exported in this shell
    BASE_URL = "http://localhost:8001"

API = f"{BASE_URL}/api"

CREDS = {
    "admin": ("admin", "Admin@12345"),
    "tech": ("tech.human", "Tech@12345"),
    "vtech": ("tech.virtual", "VTech@12345"),
    "employee": ("employee.demo", "Employee@12345"),
}


def login(username, password):
    r = requests.post(f"{API}/auth/login", json={"username": username, "password": password})
    return r


@pytest.fixture(scope="session")
def tokens():
    toks = {}
    for role, (u, p) in CREDS.items():
        r = login(u, p)
        assert r.status_code == 200, f"login failed for {role}: {r.text}"
        data = r.json()
        assert "access_token" in data
        assert data["user"]["role"] or data["user"].get("role") is not None
        toks[role] = data["access_token"]
    return toks


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestAuth:
    def test_login_success_all_roles(self, tokens):
        assert set(tokens.keys()) == {"admin", "tech", "vtech", "employee"}

    def test_login_invalid_password(self):
        r = login("admin", "WrongPass123")
        assert r.status_code == 401

    def test_login_unknown_user(self):
        r = login("no_such_user", "x")
        assert r.status_code == 401

    def test_me_endpoint(self, tokens):
        r = requests.get(f"{API}/auth/me", headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200
        assert r.json()["username"] == "admin"
        assert r.json()["role"] == "admin"

    def test_register_pending_then_blocked_login(self):
        import uuid
        uname = f"TEST_reg_{uuid.uuid4().hex[:8]}"
        r = requests.post(f"{API}/auth/register", json={
            "username": uname, "password": "TestPass@123", "full_name": "Test Reg",
            "email": f"{uname}@test.com", "role": "employee",
        })
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "pending_activation"
        # login should be forbidden while pending
        r2 = login(uname, "TestPass@123")
        assert r2.status_code == 403
        return uname


class TestAdminUserManagement:
    def test_admin_create_user_direct(self, tokens):
        import uuid
        uname = f"TEST_vtech_{uuid.uuid4().hex[:6]}"
        payload = {
            "username": uname, "password": "TestPass@123", "full_name": "Test VTech",
            "email": f"{uname}@test.com", "role": "technician_virtual",
        }
        r = requests.post(f"{API}/users", json=payload, headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["username"] == uname.lower()
        assert data["status"] == "active"  # admin-created users should be active immediately

    def test_admin_activate_pending_user(self, tokens):
        import uuid
        uname = f"TEST_pending_{uuid.uuid4().hex[:6]}"
        reg = requests.post(f"{API}/auth/register", json={
            "username": uname, "password": "TestPass@123", "full_name": "Pending User",
            "email": f"{uname}@test.com", "role": "employee",
        })
        user_id = reg.json()["id"]
        r = requests.patch(f"{API}/users/{user_id}/status", json={"status": "active"}, headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "active"
        # now login should succeed
        r2 = login(uname, "TestPass@123")
        assert r2.status_code == 200

    def test_admin_suspend_and_deactivate(self, tokens):
        import uuid
        uname = f"TEST_susp_{uuid.uuid4().hex[:6]}"
        payload = {
            "username": uname, "password": "TestPass@123", "full_name": "Susp User",
            "email": f"{uname}@test.com", "role": "employee",
        }
        r = requests.post(f"{API}/users", json=payload, headers=auth_headers(tokens["admin"]))
        user_id = r.json()["id"]

        r2 = requests.patch(f"{API}/users/{user_id}/status", json={"status": "suspended"}, headers=auth_headers(tokens["admin"]))
        assert r2.status_code == 200
        assert r2.json()["status"] == "suspended"
        assert login(uname, "TestPass@123").status_code == 403

        r3 = requests.patch(f"{API}/users/{user_id}/status", json={"status": "deactivated"}, headers=auth_headers(tokens["admin"]))
        assert r3.status_code == 200
        assert r3.json()["status"] == "deactivated"

    def test_non_admin_cannot_list_users(self, tokens):
        r = requests.get(f"{API}/users", headers=auth_headers(tokens["employee"]))
        assert r.status_code == 403


class TestTicketLifecycle:
    def test_create_ticket_priority_and_autoassign(self, tokens):
        payload = {
            "subject": "TEST_ticket priority check",
            "description": "Cannot access email - urgent issue",
            "category": "software",
            "impact": "high",
            "urgency": "high",
        }
        r = requests.post(f"{API}/tickets", json=payload, headers=auth_headers(tokens["employee"]))
        assert r.status_code == 200, r.text
        ticket = r.json()
        assert ticket["subject"] == payload["subject"]
        assert ticket["priority"] in ("P1", "P2", "P3", "P4", "critical", "high", "medium", "low")
        ticket_id = ticket["id"]

        # verify persisted
        get_r = requests.get(f"{API}/tickets/{ticket_id}", headers=auth_headers(tokens["employee"]))
        assert get_r.status_code == 200
        assert get_r.json()["id"] == ticket_id

        # wait for RabbitMQ auto-assignment pipeline
        assignee = None
        for _ in range(15):
            time.sleep(1)
            check = requests.get(f"{API}/tickets/{ticket_id}", headers=auth_headers(tokens["employee"])).json()
            if check.get("assignee_id"):
                assignee = check
                break
        assert assignee is not None, "Ticket was not auto-assigned within 15s"
        assert assignee["status"] in ("assigned", "in_progress")
        return ticket_id

    def test_employee_ticket_appears_in_my_tickets(self, tokens):
        r = requests.get(f"{API}/tickets", headers=auth_headers(tokens["employee"]))
        assert r.status_code == 200
        tickets = r.json()
        assert isinstance(tickets, list)
        assert any(t["subject"].startswith("TEST_") for t in tickets)

    def test_employee_cannot_create_ticket_role_blocked_for_technician(self, tokens):
        r = requests.post(f"{API}/tickets", json={
            "subject": "should fail", "description": "x", "category": "software",
            "impact": "low", "urgency": "low",
        }, headers=auth_headers(tokens["tech"]))
        assert r.status_code == 403

    def test_technician_queue_visible(self, tokens):
        r = requests.get(f"{API}/tickets/queue", headers=auth_headers(tokens["tech"]))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_employee_cannot_access_queue(self, tokens):
        r = requests.get(f"{API}/tickets/queue", headers=auth_headers(tokens["employee"]))
        assert r.status_code == 403


@pytest.fixture(scope="module")
def created_ticket(tokens_module):
    payload = {
        "subject": "TEST_lifecycle ticket",
        "description": "Full lifecycle test ticket",
        "category": "hardware",
        "impact": "medium",
        "urgency": "medium",
    }
    r = requests.post(f"{API}/tickets", json=payload, headers=auth_headers(tokens_module["employee"]))
    assert r.status_code == 200
    ticket = r.json()
    ticket_id = ticket["id"]
    # wait for assignment
    for _ in range(15):
        time.sleep(1)
        check = requests.get(f"{API}/tickets/{ticket_id}", headers=auth_headers(tokens_module["employee"])).json()
        if check.get("assignee_id"):
            return check
    pytest.skip("ticket not auto-assigned in time")


@pytest.fixture(scope="module")
def tokens_module():
    toks = {}
    for role, (u, p) in CREDS.items():
        r = login(u, p)
        toks[role] = r.json()["access_token"]
    return toks


class TestLocksMessagesResolveCsat:
    def test_lock_acquire_and_conflict(self, tokens_module, created_ticket):
        ticket_id = created_ticket["id"]
        r1 = requests.post(f"{API}/tickets/{ticket_id}/lock", headers=auth_headers(tokens_module["tech"]))
        assert r1.status_code == 200, r1.text

        # admin trying to acquire should see conflict (locked by tech)
        r2 = requests.post(f"{API}/tickets/{ticket_id}/lock", headers=auth_headers(tokens_module["admin"]))
        assert r2.status_code == 409, f"expected lock conflict, got {r2.status_code}: {r2.text}"

    def test_send_message_and_attachment(self, tokens_module, created_ticket):
        ticket_id = created_ticket["id"]
        r = requests.post(f"{API}/tickets/{ticket_id}/messages", json={"content": "TEST first response"},
                           headers=auth_headers(tokens_module["tech"]))
        assert r.status_code == 200, r.text
        assert r.json()["content"] == "TEST first response"

        files = {"file": ("test_upload.txt", io.BytesIO(b"hello world attachment"), "text/plain")}
        up = requests.post(f"{API}/tickets/{ticket_id}/messages/upload", files=files, headers=auth_headers(tokens_module["tech"]))
        assert up.status_code == 200, up.text
        upload_data = up.json()
        assert "url" in upload_data or "file_url" in upload_data

    def test_resolve_ticket_creates_csat(self, tokens_module, created_ticket):
        ticket_id = created_ticket["id"]
        r = requests.post(f"{API}/tickets/{ticket_id}/resolve", json={"resolution_note": "TEST fixed the issue"},
                           headers=auth_headers(tokens_module["tech"]))
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "resolved"

        csat = requests.get(f"{API}/csat/{ticket_id}", headers=auth_headers(tokens_module["employee"]))
        assert csat.status_code == 200, csat.text

    def test_csat_submit_and_block_resubmit(self, tokens_module, created_ticket):
        ticket_id = created_ticket["id"]
        r1 = requests.post(f"{API}/csat/{ticket_id}", json={"rating": 5, "comment": "TEST great support"},
                            headers=auth_headers(tokens_module["employee"]))
        assert r1.status_code == 200, r1.text
        r2 = requests.post(f"{API}/csat/{ticket_id}", json={"rating": 3, "comment": "TEST resubmit"},
                            headers=auth_headers(tokens_module["employee"]))
        assert r2.status_code in (400, 409), f"expected resubmission block, got {r2.status_code}"


class TestRejectAndTags:
    @pytest.fixture(scope="class")
    def open_ticket(self, tokens_module):
        r = requests.post(f"{API}/tickets", json={
            "subject": "TEST_reject ticket", "description": "for rejection", "category": "software",
            "impact": "low", "urgency": "low",
        }, headers=auth_headers(tokens_module["employee"]))
        ticket_id = r.json()["id"]
        for _ in range(15):
            time.sleep(1)
            check = requests.get(f"{API}/tickets/{ticket_id}", headers=auth_headers(tokens_module["employee"])).json()
            if check.get("assignee_id"):
                return check
        pytest.skip("ticket not auto-assigned in time")

    def test_reject_ticket(self, tokens_module, open_ticket):
        ticket_id = open_ticket["id"]
        r = requests.post(f"{API}/tickets/{ticket_id}/reject", json={"rejection_reason": "TEST not a valid issue"},
                           headers=auth_headers(tokens_module["tech"]))
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "rejected"

    def test_tags_create_attach_remove(self, tokens_module, open_ticket):
        ticket_id = open_ticket["id"]
        import uuid
        tag_name = f"TEST_tag_{uuid.uuid4().hex[:6]}"
        create = requests.post(f"{API}/tags", json={"name": tag_name}, headers=auth_headers(tokens_module["admin"]))
        assert create.status_code == 200, create.text
        tag_id = create.json()["id"]

        attach = requests.post(f"{API}/tickets/{ticket_id}/tags", json={"tag": tag_name}, headers=auth_headers(tokens_module["tech"]))
        assert attach.status_code == 200, attach.text
        assert tag_name.lower() in attach.json().get("tags", [])

        remove = requests.delete(f"{API}/tickets/{ticket_id}/tags/{tag_name}", headers=auth_headers(tokens_module["tech"]))
        assert remove.status_code in (200, 204), remove.text

        delete_tag = requests.delete(f"{API}/tags/{tag_id}", headers=auth_headers(tokens_module["admin"]))
        assert delete_tag.status_code in (200, 204), delete_tag.text


class TestEscalationReassignment:
    @pytest.fixture(scope="class")
    def assigned_ticket(self, tokens_module):
        r = requests.post(f"{API}/tickets", json={
            "subject": "TEST_escalation ticket", "description": "for escalation", "category": "network",
            "impact": "high", "urgency": "medium",
        }, headers=auth_headers(tokens_module["employee"]))
        ticket_id = r.json()["id"]
        for _ in range(15):
            time.sleep(1)
            check = requests.get(f"{API}/tickets/{ticket_id}", headers=auth_headers(tokens_module["employee"])).json()
            if check.get("assignee_id"):
                return check
        pytest.skip("ticket not auto-assigned in time")

    def test_escalate_flow(self, tokens_module, assigned_ticket):
        ticket_id = assigned_ticket["id"]
        assignee_id = assigned_ticket["assignee_id"]
        # resolve which known credential currently holds the assignment (round_robin
        # cycles across all active technicians, which may include ones created by earlier tests)
        actor_token = None
        actor_role = None
        for role_key in ("tech", "vtech", "admin"):
            me = requests.get(f"{API}/auth/me", headers=auth_headers(tokens_module[role_key])).json()
            if me["id"] == assignee_id:
                actor_token = tokens_module[role_key]
                actor_role = me["role"]
                break
        if not actor_token:
            pytest.skip(f"Ticket auto-assigned to a technician ({assignee_id}) outside known test credentials; "
                        f"likely due to round-robin including technicians created by earlier test classes")
        r = requests.post(f"{API}/tickets/{ticket_id}/escalate", json={"reason": "TEST needs senior help"},
                           headers=auth_headers(actor_token))
        assert r.status_code == 200, r.text
        ticket = requests.get(f"{API}/tickets/{ticket_id}", headers=auth_headers(actor_token)).json()
        if actor_role == "technician_virtual":
            assert ticket["status"] == "assigned"
            assert ticket["assignee_id"] is not None
            assert ticket["assignee_id"] != assignee_id
            assert ticket.get("request_pending") is not True

            mine = requests.get(f"{API}/requests/mine", headers=auth_headers(actor_token))
            assert mine.status_code == 200
            my_req = [m for m in mine.json() if m["ticket_id"] == ticket_id]
            assert len(my_req) == 1
            assert my_req[0]["status"] == "approved"
        else:
            assert ticket["status"] != "escalated"
            assert ticket.get("request_pending") is True

            pending = requests.get(f"{API}/requests/pending", headers=auth_headers(tokens_module["admin"]))
            assert pending.status_code == 200
            matches = [p for p in pending.json() if p["ticket_id"] == ticket_id]
            assert len(matches) == 1
            request_id = matches[0]["id"]

            vtech_id_r = requests.get(f"{API}/users?role=technician_virtual", headers=auth_headers(tokens_module["admin"]))
            target_id = None
            vtech_items = vtech_id_r.json().get("items", []) if vtech_id_r.status_code == 200 else []
            candidates = [u for u in vtech_items if u["id"] != assignee_id]
            if candidates:
                target_id = candidates[0]["id"]
            else:
                tech_r = requests.get(f"{API}/users?role=technician_human", headers=auth_headers(tokens_module["admin"]))
                candidates = [u for u in tech_r.json().get("items", []) if u["id"] != assignee_id]
                target_id = candidates[0]["id"]

            approve = requests.post(f"{API}/requests/{request_id}/approve", json={"target_technician_id": target_id, "note": "TEST approved"},
                                     headers=auth_headers(tokens_module["admin"]))
            assert approve.status_code == 200, approve.text

            ticket2 = requests.get(f"{API}/tickets/{ticket_id}", headers=auth_headers(tokens_module["admin"])).json()
            assert ticket2["status"] == "assigned"
            assert ticket2["assignee_id"] == target_id

            mine = requests.get(f"{API}/requests/mine", headers=auth_headers(actor_token))
            assert mine.status_code == 200
            my_req = [m for m in mine.json() if m["id"] == request_id]
            assert len(my_req) == 1
            assert my_req[0]["status"] == "approved"


class TestAdminConfigKanbanTimelineMonitor:
    def test_get_and_switch_algorithm(self, tokens_module):
        r = requests.get(f"{API}/assignment/config", headers=auth_headers(tokens_module["admin"]))
        assert r.status_code == 200, r.text
        current = r.json()
        assert "active_algorithm" in current

        new_algo = "least_busy" if current.get("active_algorithm") == "round_robin" else "round_robin"
        upd = requests.put(f"{API}/assignment/config", json={"algorithm": new_algo}, headers=auth_headers(tokens_module["admin"]))
        assert upd.status_code == 200, upd.text

        check = requests.get(f"{API}/assignment/config", headers=auth_headers(tokens_module["admin"]))
        assert check.json().get("active_algorithm") == new_algo

        # revert
        requests.put(f"{API}/assignment/config", json={"algorithm": current.get("active_algorithm")}, headers=auth_headers(tokens_module["admin"]))

    def test_sla_policy_edit_persists(self, tokens_module):
        r = requests.get(f"{API}/tickets/config/sla-policies", headers=auth_headers(tokens_module["admin"]))
        assert r.status_code == 200
        policies = r.json()
        assert len(policies) > 0
        p = policies[0]
        new_val = p["resolve_minutes"] + 1
        upd = requests.patch(f"{API}/tickets/config/sla-policies/{p['priority']}",
                              json={"first_response_minutes": p["first_response_minutes"], "resolve_minutes": new_val},
                              headers=auth_headers(tokens_module["admin"]))
        assert upd.status_code == 200, upd.text
        check = requests.get(f"{API}/tickets/config/sla-policies", headers=auth_headers(tokens_module["admin"]))
        updated = [x for x in check.json() if x["priority"] == p["priority"]][0]
        assert updated["resolve_minutes"] == new_val
        # revert
        requests.patch(f"{API}/tickets/config/sla-policies/{p['priority']}",
                        json={"first_response_minutes": p["first_response_minutes"], "resolve_minutes": p["resolve_minutes"]},
                        headers=auth_headers(tokens_module["admin"]))

    def test_kanban_columns(self, tokens_module):
        r = requests.get(f"{API}/kanban/board", headers=auth_headers(tokens_module["admin"]))
        assert r.status_code == 200, r.text

    def test_timeline_events(self, tokens_module):
        r = requests.get(f"{API}/timeline", headers=auth_headers(tokens_module["admin"]))
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_monitor_users_and_tickets(self, tokens_module):
        r = requests.get(f"{API}/monitor/users", headers=auth_headers(tokens_module["admin"]))
        assert r.status_code == 200, r.text
        r2 = requests.get(f"{API}/monitor/tickets", headers=auth_headers(tokens_module["admin"]))
        assert r2.status_code == 200, r2.text

    def test_non_admin_blocked_from_admin_routes(self, tokens_module):
        r = requests.get(f"{API}/monitor/users", headers=auth_headers(tokens_module["employee"]))
        assert r.status_code == 403
        r2 = requests.get(f"{API}/kanban/board", headers=auth_headers(tokens_module["tech"]))
        assert r2.status_code == 403
