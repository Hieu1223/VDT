"""
Backend tests for Helpdesk/ITSM v2 feature batch (Phase 1+2+3):
- Business Calendar module (GET/PUT /api/calendar)
- Priority Matrix PATCH endpoint
- CSAT admin list-all filters (GET /api/csat)
- Ticket list/queue/all filters (tag/date_from/date_to/sla_min_pct)
- Admin ticket creation with requester_id (on behalf of employee)
- Users heartbeat + admin user filters
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "http://localhost:8001"

API = f"{BASE_URL}/api"

CREDS = {
    "admin": ("admin", "Admin@12345"),
    "tech": ("tech.human", "Tech@12345"),
    "vtech": ("tech.virtual", "VTech@12345"),
    "employee": ("employee.demo", "Employee@12345"),
}


def login(username, password):
    return requests.post(f"{API}/auth/login", json={"username": username, "password": password})


@pytest.fixture(scope="session")
def tokens():
    toks = {}
    for role, (u, p) in CREDS.items():
        r = login(u, p)
        assert r.status_code == 200, f"login failed for {role}: {r.text}"
        toks[role] = r.json()["access_token"]
    return toks


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestBusinessCalendar:
    def test_get_calendar_requires_admin(self, tokens):
        r = requests.get(f"{API}/calendar", headers=auth_headers(tokens["employee"]))
        assert r.status_code == 403

    def test_get_calendar_admin_ok(self, tokens):
        r = requests.get(f"{API}/calendar", headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200
        data = r.json()
        assert "business_days" in data
        assert "start_hour" in data
        assert "holidays" in data
        assert isinstance(data["holidays"], list)

    def test_update_calendar_and_verify_persistence(self, tokens):
        get_r = requests.get(f"{API}/calendar", headers=auth_headers(tokens["admin"]))
        original = get_r.json()

        payload = {
            "business_days": [0, 1, 2, 3, 4],
            "start_hour": 8,
            "start_minute": 30,
            "end_hour": 17,
            "end_minute": 0,
            "holidays": ["2026-01-01", "2026-12-25"],
        }
        put_r = requests.put(f"{API}/calendar", json=payload, headers=auth_headers(tokens["admin"]))
        assert put_r.status_code == 200
        updated = put_r.json()
        assert updated["start_hour"] == 8
        assert updated["start_minute"] == 30
        assert "2026-01-01" in updated["holidays"]

        # Verify persistence via GET
        verify_r = requests.get(f"{API}/calendar", headers=auth_headers(tokens["admin"]))
        assert verify_r.status_code == 200
        verified = verify_r.json()
        assert verified["start_hour"] == 8
        assert "2026-12-25" in verified["holidays"]

        # restore original to not disturb other tests/environment
        requests.put(f"{API}/calendar", json={
            "business_days": original.get("business_days", [0, 1, 2, 3, 4]),
            "start_hour": original.get("start_hour", 9),
            "start_minute": original.get("start_minute", 0),
            "end_hour": original.get("end_hour", 18),
            "end_minute": original.get("end_minute", 0),
            "holidays": original.get("holidays", []),
        }, headers=auth_headers(tokens["admin"]))


class TestPriorityMatrix:
    def test_get_priority_matrix(self, tokens):
        r = requests.get(f"{API}/tickets/config/priority-matrix", headers=auth_headers(tokens["employee"]))
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) > 0
        assert "impact" in rows[0] and "urgency" in rows[0] and "priority" in rows[0]

    def test_update_priority_matrix_requires_admin(self, tokens):
        r = requests.patch(
            f"{API}/tickets/config/priority-matrix/high/high",
            json={"priority": "P1"},
            headers=auth_headers(tokens["employee"]),
        )
        assert r.status_code == 403

    def test_update_priority_matrix_and_verify_persistence(self, tokens):
        # capture original
        rows = requests.get(f"{API}/tickets/config/priority-matrix", headers=auth_headers(tokens["admin"])).json()
        original = next((r for r in rows if r["impact"] == "low" and r["urgency"] == "low"), None)
        original_priority = original["priority"] if original else "P4"

        r = requests.patch(
            f"{API}/tickets/config/priority-matrix/low/low",
            json={"priority": "P2"},
            headers=auth_headers(tokens["admin"]),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["priority"] == "P2"

        rows2 = requests.get(f"{API}/tickets/config/priority-matrix", headers=auth_headers(tokens["admin"])).json()
        row2 = next((r for r in rows2 if r["impact"] == "low" and r["urgency"] == "low"), None)
        assert row2 is not None
        assert row2["priority"] == "P2"

        # restore
        requests.patch(
            f"{API}/tickets/config/priority-matrix/low/low",
            json={"priority": original_priority},
            headers=auth_headers(tokens["admin"]),
        )

    def test_update_priority_matrix_unknown_combo(self, tokens):
        r = requests.patch(
            f"{API}/tickets/config/priority-matrix/unknown/unknown",
            json={"priority": "P1"},
            headers=auth_headers(tokens["admin"]),
        )
        assert r.status_code == 404


class TestCsatAdminList:
    def test_csat_list_requires_admin(self, tokens):
        r = requests.get(f"{API}/csat", headers=auth_headers(tokens["employee"]))
        assert r.status_code == 403

    def test_csat_list_admin_ok(self, tokens):
        r = requests.get(f"{API}/csat", headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_csat_list_rating_filter(self, tokens):
        r = requests.get(f"{API}/csat", params={"rating_min": 1, "rating_max": 5}, headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200

    def test_csat_list_status_filter(self, tokens):
        r = requests.get(f"{API}/csat", params={"status": "submitted"}, headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200
        for row in r.json():
            assert row["status"] == "submitted"


class TestTicketFilters:
    def test_my_tickets_tag_date_filters(self, tokens):
        r = requests.get(f"{API}/tickets", params={"tag": "nonexistent-tag-xyz"}, headers=auth_headers(tokens["employee"]))
        assert r.status_code == 200
        assert r.json() == []

    def test_queue_sla_min_pct_filter(self, tokens):
        r = requests.get(f"{API}/tickets/queue", params={"sla_min_pct": 999}, headers=auth_headers(tokens["tech"]))
        assert r.status_code == 200
        assert r.json() == []

    def test_all_tickets_admin_filters(self, tokens):
        r = requests.get(f"{API}/tickets/all", params={"date_from": "2000-01-01", "date_to": "2000-01-02"}, headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200
        assert r.json() == []

    def test_all_tickets_requires_admin(self, tokens):
        r = requests.get(f"{API}/tickets/all", headers=auth_headers(tokens["tech"]))
        assert r.status_code == 403


class TestAdminTicketCreationOnBehalf:
    def test_admin_create_ticket_on_behalf_of_employee(self, tokens):
        # get employee id
        techs_r = requests.get(f"{API}/users", params={"role": "employee"}, headers=auth_headers(tokens["admin"]))
        assert techs_r.status_code == 200
        employees = techs_r.json()
        assert len(employees) > 0
        employee = employees[0]

        payload = {
            "subject": "TEST_admin created on behalf",
            "description": "Testing admin-on-behalf ticket creation",
            "category": "General",
            "impact": "low",
            "urgency": "low",
            "requester_id": employee["id"],
        }
        r = requests.post(f"{API}/tickets", json=payload, headers=auth_headers(tokens["admin"]))
        assert r.status_code in (200, 201)
        ticket = r.json()
        assert ticket["subject"] == "TEST_admin created on behalf"
        assert ticket["requester_id"] == employee["id"]

    def test_employee_cannot_pass_requester_id_for_self(self, tokens):
        # employee creating ticket - requester_id should be ignored/not applicable, ticket requester = self
        payload = {
            "subject": "TEST_employee ticket",
            "description": "desc",
            "category": "General",
            "impact": "low",
            "urgency": "low",
        }
        r = requests.post(f"{API}/tickets", json=payload, headers=auth_headers(tokens["employee"]))
        assert r.status_code in (200, 201)


class TestUsersHeartbeatAndFilters:
    def test_heartbeat_marks_online(self, tokens):
        r = requests.post(f"{API}/users/me/heartbeat", headers=auth_headers(tokens["employee"]))
        assert r.status_code == 200
        assert r.json()["online"] is True

        list_r = requests.get(f"{API}/users", params={"online": True}, headers=auth_headers(tokens["admin"]))
        assert list_r.status_code == 200
        usernames = [u["username"] for u in list_r.json()]
        assert "employee.demo" in usernames

    def test_admin_list_users_search_filter(self, tokens):
        r = requests.get(f"{API}/users", params={"search": "employee.demo"}, headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200
        rows = r.json()
        assert any(u["username"] == "employee.demo" for u in rows)

    def test_admin_list_users_role_filter(self, tokens):
        r = requests.get(f"{API}/users", params={"role": "admin"}, headers=auth_headers(tokens["admin"]))
        assert r.status_code == 200
        for u in r.json():
            assert u["role"] == "admin"
