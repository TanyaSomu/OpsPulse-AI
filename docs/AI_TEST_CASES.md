# OpsPulse AI — AI-Generated Test Cases Specification

## 1. Overview & AI Testing Strategy

This test suite was generated for **OpsPulse AI** using the AI-assisted testing workflow. OpsPulse AI is a full-stack incident management and service reliability platform built with FastAPI, PostgreSQL, and React.

### Tooling Configuration
- **AI Testing Framework**: TestSprite CLI (`@testsprite/testsprite-cli` v0.14.0) with Antigravity agent verification skills installed (`.agents/skills/testsprite-verify`).
- **Cloud Execution Note**: TestSprite cloud verification requires `TESTSPRITE_API_KEY`. In local execution, test cases are executed deterministically using **pytest** (backend API, state machine, and database persistence) and **Playwright** (frontend browser E2E flows).
- **Test Database Isolation**: Database tests run with transactional rollback or dedicated session boundaries without mutating baseline seed data.

---

## 2. Test Case Summary Matrix

| ID | Module | Scenario Group | Scenario Description | Priority | Automation Target |
|---|---|---|---|---|---|
| `TC-AUTH-01` | Auth | Positive | Valid credentials authenticate and return JWT token | P1 | `backend/app/tests/test_auth_ai.py` |
| `TC-AUTH-02` | Auth | Negative | Invalid password rejected with HTTP 401 | P1 | `backend/app/tests/test_auth_ai.py` |
| `TC-AUTH-03` | Auth | Negative | Non-existent user email rejected with HTTP 401 | P2 | `backend/app/tests/test_auth_ai.py` |
| `TC-AUTH-04` | Auth | Boundary | Empty string and whitespace login credentials rejected | P2 | `backend/app/tests/test_auth_ai.py` |
| `TC-AUTH-05` | Auth | Security | Expired or malformed bearer token rejected with HTTP 401 | P1 | `backend/app/tests/test_auth_ai.py` |
| `TC-AUTH-06` | Auth | Positive / E2E | Browser login form submits and redirects to dashboard | P1 | `frontend/e2e/auth.spec.ts` |
| `TC-ALRT-01` | Alerts | Positive | Webhook ingests alert and triggers new incident | P1 | `backend/app/tests/test_alerts_ai.py` |
| `TC-ALRT-02` | Alerts | Negative | Alert with non-existent service rejected with HTTP 404 | P2 | `backend/app/tests/test_alerts_ai.py` |
| `TC-ALRT-03` | Alerts | Negative | Alert with invalid severity level rejected with HTTP 422 | P2 | `backend/app/tests/test_alerts_ai.py` |
| `TC-ALRT-04` | Alerts | Boundary | Alert with missing required payload fields rejected | P2 | `backend/app/tests/test_alerts_ai.py` |
| `TC-ALRT-05` | Alerts | Integration | Identical alert within 15-minute window is deduplicated | P1 | `backend/app/tests/test_alerts_ai.py` |
| `TC-ALRT-06` | Alerts | Integration / E2E | Webhook alert simulated from UI appears in incoming alerts list | P2 | `frontend/e2e/alerts.spec.ts` |
| `TC-INCD-01` | Incidents | Positive | Create incident with initial `TRIGGERED` status and SLA deadline | P1 | `backend/app/tests/test_incidents_ai.py` |
| `TC-INCD-02` | Incidents | Positive | Retrieve existing incident details with correlated alert records | P1 | `backend/app/tests/test_incidents_ai.py` |
| `TC-INCD-03` | Incidents | Positive | Acknowledge incident moves status to `ACKNOWLEDGED` and clears SLA breach | P1 | `backend/app/tests/test_incidents_ai.py` |
| `TC-INCD-04` | Incidents | Positive | Mitigate incident transitions status to `MITIGATED` and logs note | P2 | `backend/app/tests/test_incidents_ai.py` |
| `TC-INCD-05` | Incidents | Positive | Resolve incident transitions status to `RESOLVED` and sets `resolved_at` | P1 | `backend/app/tests/test_incidents_ai.py` |
| `TC-INCD-06` | Incidents | Negative | Invalid state transition (`RESOLVED` → `ACKNOWLEDGED`) rejected HTTP 400 | P1 | `backend/app/tests/test_incidents_ai.py` |
| `TC-INCD-07` | Incidents | Integration | Incident status changes create immutable `IncidentEvent` audit rows | P1 | `backend/app/tests/test_incidents_ai.py` |
| `TC-INCD-08` | Incidents | Positive / E2E | Responder clicks Acknowledge button in UI and status updates | P1 | `frontend/e2e/incidents.spec.ts` |
| `TC-ESCL-01` | Escalation | Positive | Admin creates escalation policy with ordered rules | P2 | `backend/app/tests/test_escalation_ai.py` |
| `TC-ESCL-02` | Escalation | Negative | Escalation policy with duplicate or negative rule tiers rejected | P2 | `backend/app/tests/test_escalation_ai.py` |
| `TC-ESCL-03` | Escalation | Integration | Expired SLA deadline automatically advances responder to tier 2 | P1 | `backend/app/tests/test_escalation_ai.py` |
| `TC-ESCL-04` | Escalation | Regression | Already `RESOLVED` incident is never escalated even if deadline expired | P1 | `backend/app/tests/test_escalation_ai.py` |
| `TC-ESCL-05` | Escalation | Positive | Manual SLA check endpoint evaluates expired deadlines | P2 | `backend/app/tests/test_escalation_ai.py` |
| `TC-SRVC-01` | Services | Positive | Admin registers new monitored service with valid slug | P2 | `backend/app/tests/test_services_ai.py` |
| `TC-SRVC-02` | Services | Negative | Service registration with duplicate name rejected with HTTP 400 | P2 | `backend/app/tests/test_services_ai.py` |
| `TC-SRVC-03` | Services | Positive | Update service operational health status (`HEALTHY` → `DEGRADED`) | P2 | `backend/app/tests/test_services_ai.py` |
| `TC-SRVC-04` | Services | Security | Non-admin user cannot register or modify a service | P1 | `backend/app/tests/test_services_ai.py` |
| `TC-SRVC-05` | Services | Positive / E2E | Monitored services catalog renders with health status badges | P2 | `frontend/e2e/services.spec.ts` |
| `TC-DASH-01` | Dashboard | Positive | Dashboard data API computes exact active and critical incident counts | P1 | `backend/app/tests/test_dashboard_ai.py` |
| `TC-DASH-02` | Dashboard | Integration | Resolving an incident decrements active incident count in dashboard | P1 | `backend/app/tests/test_dashboard_ai.py` |
| `TC-DASH-03` | Dashboard | Boundary | Dashboard handles services with zero historical incidents gracefully | P3 | `backend/app/tests/test_dashboard_ai.py` |
| `TC-DASH-04` | Dashboard | Positive / E2E | Dashboard page loads KPI cards with valid numerical metrics | P1 | `frontend/e2e/dashboard.spec.ts` |
| `TC-SECU-01` | Security | Security | Unauthenticated request to protected endpoints returns HTTP 401 | P1 | `backend/app/tests/test_security_ai.py` |
| `TC-SECU-02` | Security | Security | SQL injection patterns in search query handled safely via ORM | P1 | `backend/app/tests/test_security_ai.py` |
| `TC-SECU-03` | Security | Security | Cross-site scripting (XSS) payload in incident title sanitized | P1 | `backend/app/tests/test_security_ai.py` |
| `TC-SECU-04` | Security | Negative | Accessing non-existent UUID returns HTTP 404 with structured error | P2 | `backend/app/tests/test_security_ai.py` |
| `TC-SECU-05` | Security | Security | Responder role cannot delete services or reassign admin permissions | P1 | `backend/app/tests/test_security_ai.py` |

---

## 3. Detailed Test Case Specifications

### Module A: Authentication

#### TC-AUTH-01: Successful Login with Valid Credentials
- **Scenario Group**: Positive
- **Preconditions**: User `admin@opspulse.local` exists in database with password `admin123`.
- **Input Data**: `{ "username": "admin@opspulse.local", "password": "admin123" }`
- **Execution Steps**:
  1. Send `POST /api/v1/auth/login` with application/x-www-form-urlencoded or JSON credentials.
  2. Inspect response status code and JSON body.
- **Expected Result**: HTTP 200 OK, `access_token` JWT string present, `token_type` is `"bearer"`.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_auth_ai.py::test_login_success`)

#### TC-AUTH-02: Login Rejection with Incorrect Password
- **Scenario Group**: Negative
- **Preconditions**: User `admin@opspulse.local` exists.
- **Input Data**: `{ "username": "admin@opspulse.local", "password": "wrongpassword" }`
- **Execution Steps**:
  1. Send `POST /api/v1/auth/login`.
- **Expected Result**: HTTP 401 Unauthorized, detail message indicating invalid credentials.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_auth_ai.py::test_login_invalid_password`)

#### TC-AUTH-03: Login Rejection with Unregistered Email
- **Scenario Group**: Negative
- **Preconditions**: None.
- **Input Data**: `{ "username": "nobody@opspulse.local", "password": "admin123" }`
- **Execution Steps**:
  1. Send `POST /api/v1/auth/login`.
- **Expected Result**: HTTP 401 Unauthorized.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_auth_ai.py::test_login_unregistered_email`)

#### TC-AUTH-04: Login Validation on Empty Input
- **Scenario Group**: Boundary
- **Preconditions**: None.
- **Input Data**: `{ "username": "", "password": "" }`
- **Execution Steps**:
  1. Send `POST /api/v1/auth/login`.
- **Expected Result**: HTTP 400 Bad Request or HTTP 422 Unprocessable Entity.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_auth_ai.py::test_login_empty_fields`)

#### TC-AUTH-05: Expired or Malformed Bearer Token Rejection
- **Scenario Group**: Security
- **Preconditions**: None.
- **Input Data**: Header `Authorization: Bearer invalid.token.payload`
- **Execution Steps**:
  1. Send `GET /api/v1/auth/me` with malformed token.
- **Expected Result**: HTTP 401 Unauthorized, token rejection without leaking stack trace.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_auth_ai.py::test_invalid_token_rejected`)

#### TC-AUTH-06: Browser Login and Session Redirect
- **Scenario Group**: Positive / E2E
- **Preconditions**: Frontend running on Vite and backend on port 8000.
- **Input Data**: Email `admin@opspulse.local`, Password `admin123`
- **Execution Steps**:
  1. Navigate to `/login`.
  2. Fill `[data-testid="input-login-email"]` and `[data-testid="input-login-password"]`.
  3. Click `[data-testid="btn-login-submit"]`.
- **Expected Result**: Browser navigates to `/`, displaying the Service Reliability Dashboard.
- **Priority**: P1 (Critical)
- **Automation Method**: Playwright E2E (`frontend/e2e/auth.spec.ts`)

---

### Module B: Alert Management & Deduplication

#### TC-ALRT-01: Valid Webhook Alert Ingestion Creates Incident
- **Scenario Group**: Positive
- **Preconditions**: Service `"Order Processing Pipeline"` exists.
- **Input Data**:
  ```json
  {
    "service_name": "Order Processing Pipeline",
    "title": "CPU threshold exceeded 95%",
    "severity": "CRITICAL",
    "source": "Prometheus"
  }
  ```
- **Execution Steps**:
  1. Send `POST /api/v1/alerts/webhook`.
- **Expected Result**: HTTP 200/201, `is_new_incident: true`, `incident_number` returned, status `TRIGGERED`.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_alerts_ai.py::test_webhook_creates_new_incident`)

#### TC-ALRT-02: Alert Ingestion with Non-Existent Service Rejected
- **Scenario Group**: Negative
- **Preconditions**: None.
- **Input Data**: `{ "service_name": "NonExistentServiceXYZ", "title": "Alert" }`
- **Execution Steps**:
  1. Send `POST /api/v1/alerts/webhook`.
- **Expected Result**: HTTP 404 Not Found, error stating service was not found.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_alerts_ai.py::test_webhook_unknown_service_rejected`)

#### TC-ALRT-03: Alert Ingestion with Invalid Severity Level
- **Scenario Group**: Negative
- **Preconditions**: Service exists.
- **Input Data**: `{ "service_name": "Order Processing Pipeline", "title": "Test", "severity": "EXTREME_EMERGENCY" }`
- **Execution Steps**:
  1. Send `POST /api/v1/alerts/webhook`.
- **Expected Result**: HTTP 422 Unprocessable Entity (enum validation failure).
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_alerts_ai.py::test_webhook_invalid_severity_rejected`)

#### TC-ALRT-04: Alert Ingestion with Missing Required Title
- **Scenario Group**: Boundary
- **Preconditions**: Service exists.
- **Input Data**: `{ "service_name": "Order Processing Pipeline" }`
- **Execution Steps**:
  1. Send `POST /api/v1/alerts/webhook`.
- **Expected Result**: HTTP 422 Unprocessable Entity.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_alerts_ai.py::test_webhook_missing_required_fields`)

#### TC-ALRT-05: Duplicate Alert Within 15 Minutes Is Correlated
- **Scenario Group**: Integration
- **Preconditions**: Active incident exists for service with title `"Latency spike on replica 1"`.
- **Input Data**: Identical payload sent twice within 2 minutes.
- **Execution Steps**:
  1. Send first alert payload. Record returned `incident_number`.
  2. Send second identical alert payload.
- **Expected Result**: Second response has `is_new_incident: false`, same `incident_number`, alert count incremented.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_alerts_ai.py::test_duplicate_alert_correlated`)

#### TC-ALRT-06: Webhook Simulation from UI Console
- **Scenario Group**: Integration / E2E
- **Preconditions**: User logged into UI.
- **Execution Steps**:
  1. Click `[data-testid="btn-simulate-alert"]`.
  2. Fill `[data-testid="input-alert-title"]` with `"E2E Simulated Alert"`.
  3. Click `[data-testid="btn-submit-simulate-alert"]`.
- **Expected Result**: Modal displays success confirmation; new incident appears in incident list.
- **Priority**: P2 (High)
- **Automation Method**: Playwright E2E (`frontend/e2e/alerts.spec.ts`)

---

### Module C: Incident Management & Lifecycle State Machine

#### TC-INCD-01: Manual Incident Declaration
- **Scenario Group**: Positive
- **Preconditions**: Service exists.
- **Input Data**: `{ "service_id": "<uuid>", "title": "Memory leak detected", "severity": "HIGH" }`
- **Execution Steps**:
  1. Send `POST /api/v1/incidents` with responder auth token.
- **Expected Result**: HTTP 201 Created, status is `TRIGGERED`, `ack_deadline` computed.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_incidents_ai.py::test_create_incident`)

#### TC-INCD-02: Incident Detail Retrieval with Timeline
- **Scenario Group**: Positive
- **Preconditions**: Incident exists.
- **Execution Steps**:
  1. Send `GET /api/v1/incidents/<incident_id>`.
- **Expected Result**: HTTP 200 OK, returns incident entity, correlated alerts array, and timeline events array.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_incidents_ai.py::test_get_incident_detail`)

#### TC-INCD-03: Incident Acknowledgement Lifecycle Transition
- **Scenario Group**: Positive
- **Preconditions**: Incident in `TRIGGERED` status.
- **Execution Steps**:
  1. Send `POST /api/v1/incidents/<incident_id>/acknowledge`.
- **Expected Result**: HTTP 200 OK, status changes to `ACKNOWLEDGED`, `acknowledged_at` timestamp recorded.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_incidents_ai.py::test_acknowledge_incident`)

#### TC-INCD-04: Incident Mitigation
- **Scenario Group**: Positive
- **Preconditions**: Incident in `ACKNOWLEDGED` status.
- **Input Data**: `{ "note": "Traffic shifted to secondary cluster" }`
- **Execution Steps**:
  1. Send `POST /api/v1/incidents/<incident_id>/mitigate`.
- **Expected Result**: HTTP 200 OK, status changes to `MITIGATED`.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_incidents_ai.py::test_mitigate_incident`)

#### TC-INCD-05: Incident Resolution
- **Scenario Group**: Positive
- **Preconditions**: Incident in `MITIGATED` or `ACKNOWLEDGED` status.
- **Input Data**: `{ "note": "Root cause patch deployed" }`
- **Execution Steps**:
  1. Send `POST /api/v1/incidents/<incident_id>/resolve`.
- **Expected Result**: HTTP 200 OK, status changes to `RESOLVED`, `resolved_at` set.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_incidents_ai.py::test_resolve_incident`)

#### TC-INCD-06: Invalid State Machine Transition Rejected
- **Scenario Group**: Negative
- **Preconditions**: Incident in `RESOLVED` status.
- **Execution Steps**:
  1. Send `POST /api/v1/incidents/<incident_id>/acknowledge`.
- **Expected Result**: HTTP 400 Bad Request with explanatory error message (`"Cannot acknowledge an already resolved incident"`).
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_incidents_ai.py::test_invalid_transition_rejected`)

#### TC-INCD-07: Incident State Changes Create Audit Timeline Events
- **Scenario Group**: Integration
- **Preconditions**: New incident created.
- **Execution Steps**:
  1. Transition incident through Acknowledge -> Mitigate -> Resolve.
  2. Query `IncidentEvent` rows for incident.
- **Expected Result**: 4 distinct event records (`TRIGGERED`, `ACKNOWLEDGED`, `MITIGATED`, `RESOLVED`) persisted in PostgreSQL.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_incidents_ai.py::test_timeline_events_recorded`)

#### TC-INCD-08: Browser Acknowledge and Resolve Actions
- **Scenario Group**: Positive / E2E
- **Preconditions**: Active incident displayed on UI.
- **Execution Steps**:
  1. Open incident detail page `/incidents/<id>`.
  2. Click `[data-testid="btn-action-acknowledge"]`.
  3. Verify status badge updates to `ACKNOWLEDGED`.
- **Expected Result**: Status badge changes without full page reload.
- **Priority**: P1 (Critical)
- **Automation Method**: Playwright E2E (`frontend/e2e/incidents.spec.ts`)

---

### Module D: Escalation Policies & SLA Engine

#### TC-ESCL-01: Escalation Policy Creation
- **Scenario Group**: Positive
- **Preconditions**: Admin auth token.
- **Input Data**: Policy name, 300s timeout, Tier 1 and Tier 2 user IDs.
- **Execution Steps**:
  1. Send `POST /api/v1/escalation-policies`.
- **Expected Result**: HTTP 201 Created with ordered rule tiers.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_escalation_ai.py::test_create_policy`)

#### TC-ESCL-02: Escalation Policy Rejects Empty Rules
- **Scenario Group**: Negative
- **Preconditions**: Admin auth token.
- **Input Data**: `{ "name": "Broken Policy", "rules": [] }`
- **Execution Steps**:
  1. Send `POST /api/v1/escalation-policies`.
- **Expected Result**: HTTP 400 Bad Request or HTTP 422 Unprocessable Entity.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_escalation_ai.py::test_create_policy_empty_rules_rejected`)

#### TC-ESCL-03: SLA Breach Advances Escalation Tier
- **Scenario Group**: Integration
- **Preconditions**: Incident in `TRIGGERED` status with expired `ack_deadline`.
- **Execution Steps**:
  1. Trigger escalation cycle (`check_and_escalate_incidents(db)`).
- **Expected Result**: Incident `current_escalation_level` advances from 1 to 2; assigned responder updates; new notification logged.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_escalation_ai.py::test_sla_breach_advances_tier`)

#### TC-ESCL-04: Resolved Incidents Excluded from Escalation
- **Scenario Group**: Regression
- **Preconditions**: Incident in `RESOLVED` status with past `ack_deadline`.
- **Execution Steps**:
  1. Trigger escalation evaluation.
- **Expected Result**: Incident escalation level does NOT advance; status remains `RESOLVED`.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_escalation_ai.py::test_resolved_incident_not_escalated`)

#### TC-ESCL-05: Manual SLA Check API Evaluation
- **Scenario Group**: Positive
- **Preconditions**: Authenticated user.
- **Execution Steps**:
  1. Send `POST /api/v1/escalation-policies/check-sla`.
- **Expected Result**: HTTP 200 OK with summary dictionary containing `checked_at` and `escalated_count`.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_escalation_ai.py::test_check_sla_endpoint`)

---

### Module E: Services Catalog & Routing

#### TC-SRVC-01: Service Registration
- **Scenario Group**: Positive
- **Preconditions**: Admin auth token.
- **Input Data**: `{ "name": "Billing Webhook Consumer", "owner_team": "Payments", "environment": "production" }`
- **Execution Steps**:
  1. Send `POST /api/v1/services`.
- **Expected Result**: HTTP 201 Created, auto-generated slug `billing-webhook-consumer`, initial status `HEALTHY`.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_services_ai.py::test_create_service`)

#### TC-SRVC-02: Duplicate Service Name Rejection
- **Scenario Group**: Negative
- **Preconditions**: Service `"Payment Gateway API"` already exists.
- **Input Data**: `{ "name": "Payment Gateway API", "owner_team": "Core" }`
- **Execution Steps**:
  1. Send `POST /api/v1/services`.
- **Expected Result**: HTTP 400 Bad Request (`"Service with this name already exists"`).
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_services_ai.py::test_duplicate_service_rejected`)

#### TC-SRVC-03: Update Service Health Status
- **Scenario Group**: Positive
- **Preconditions**: Existing service.
- **Input Data**: `{ "health_status": "DEGRADED" }`
- **Execution Steps**:
  1. Send `PUT /api/v1/services/<id>`.
- **Expected Result**: HTTP 200 OK, `health_status` updated to `DEGRADED`.
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_services_ai.py::test_update_service_health`)

#### TC-SRVC-04: Non-Admin Forbidden to Register Service
- **Scenario Group**: Security
- **Preconditions**: Responder auth token (non-admin).
- **Execution Steps**:
  1. Send `POST /api/v1/services`.
- **Expected Result**: HTTP 403 Forbidden (`"Administrator role required"`).
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_services_ai.py::test_non_admin_cannot_create_service`)

#### TC-SRVC-05: Services Catalog Renders in UI
- **Scenario Group**: Positive / E2E
- **Preconditions**: Logged in user.
- **Execution Steps**:
  1. Navigate to `/services`.
  2. Inspect `[data-testid="services-grid"]`.
- **Expected Result**: Grid displays service cards with health badges.
- **Priority**: P2 (High)
- **Automation Method**: Playwright E2E (`frontend/e2e/services.spec.ts`)

---

### Module F: Reliability Dashboard & Telemetry

#### TC-DASH-01: Dashboard KPI Accuracy
- **Scenario Group**: Positive
- **Preconditions**: Database populated with seed records.
- **Execution Steps**:
  1. Send `GET /api/v1/dashboard/data`.
- **Expected Result**: HTTP 200 OK, `summary.active_incidents` equals SQL count of active incidents (`TRIGGERED` + `ACKNOWLEDGED`).
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_dashboard_ai.py::test_dashboard_kpi_counts`)

#### TC-DASH-02: Incident Resolution Updates Dashboard Metrics
- **Scenario Group**: Integration
- **Preconditions**: Active incident exists.
- **Execution Steps**:
  1. Fetch dashboard active count $N$.
  2. Resolve active incident.
  3. Fetch dashboard active count again.
- **Expected Result**: New active count is $N - 1$.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_dashboard_ai.py::test_dashboard_count_decrements_on_resolve`)

#### TC-DASH-03: Service Health Breakdown
- **Scenario Group**: Boundary
- **Preconditions**: Monitored services exist.
- **Execution Steps**:
  1. Send `GET /api/v1/dashboard/data`.
- **Expected Result**: `service_health` list contains all active services with correct health status.
- **Priority**: P3 (Medium)
- **Automation Method**: Pytest API (`test_dashboard_ai.py::test_service_health_summary`)

#### TC-DASH-04: Dashboard UI Metric Cards Render
- **Scenario Group**: Positive / E2E
- **Preconditions**: User logged into UI.
- **Execution Steps**:
  1. Navigate to `/`.
  2. Verify visibility of `[data-testid="stat-active-incidents"]` and `[data-testid="stat-critical-incidents"]`.
- **Expected Result**: All 6 metric cards display positive integers.
- **Priority**: P1 (Critical)
- **Automation Method**: Playwright E2E (`frontend/e2e/dashboard.spec.ts`)

---

### Module G: Security, RBAC & Boundary Checks

#### TC-SECU-01: Unauthenticated Protected Endpoint Rejection
- **Scenario Group**: Security
- **Preconditions**: None.
- **Execution Steps**:
  1. Send `GET /api/v1/incidents` without Authorization header.
- **Expected Result**: HTTP 401 Unauthorized.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_security_ai.py::test_unauthenticated_request_rejected`)

#### TC-SECU-02: SQL Injection Attack Resilience
- **Scenario Group**: Security
- **Input Data**: Search query `"' OR '1'='1' -- "`
- **Execution Steps**:
  1. Send `GET /api/v1/incidents?search=%27%20OR%20%271%27=%271%27%20--` with auth.
- **Expected Result**: HTTP 200 OK with 0 results matching string literally, without database syntax error or leak.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_security_ai.py::test_sql_injection_resilience`)

#### TC-SECU-03: Cross-Site Scripting (XSS) Sanitization
- **Scenario Group**: Security
- **Input Data**: Incident title `"<script>alert('xss')</script>"`
- **Execution Steps**:
  1. Create incident with XSS title.
  2. Retrieve incident via API.
- **Expected Result**: Stored safely as text; React frontend renders safely without script execution.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_security_ai.py::test_xss_title_handling`)

#### TC-SECU-04: Non-Existent Entity UUID Rejection
- **Scenario Group**: Negative
- **Input Data**: `00000000-0000-0000-0000-000000000000`
- **Execution Steps**:
  1. Send `GET /api/v1/incidents/00000000-0000-0000-0000-000000000000`.
- **Expected Result**: HTTP 404 Not Found (`"Incident not found"`).
- **Priority**: P2 (High)
- **Automation Method**: Pytest API (`test_security_ai.py::test_non_existent_uuid_returns_404`)

#### TC-SECU-05: RBAC Authorization Boundaries
- **Scenario Group**: Security
- **Preconditions**: Responder role user.
- **Execution Steps**:
  1. Responder attempts `POST /api/v1/users` to create a new user.
- **Expected Result**: HTTP 403 Forbidden.
- **Priority**: P1 (Critical)
- **Automation Method**: Pytest API (`test_security_ai.py::test_responder_cannot_create_users`)

---

## 4. Incomplete or Out-of-Scope Features Identified

1. **Live Third-Party Webhook Delivery (PagerDuty / Slack / Twilio SMS)**:
   - *Status*: Abstracted in application design.
   - *Behavior*: Outgoing notifications are recorded in PostgreSQL table `notifications` rather than calling live external APIs.
   - *Testing Scope*: Tests assert database notification creation and audit trail recording.
2. **Multi-Organization Tenant Isolation**:
   - *Status*: Core schemas support `organization_id`, but current single-tenant demo scope utilizes the default seed organization.
   - *Testing Scope*: Tests validate single-organization operations and role boundaries.
