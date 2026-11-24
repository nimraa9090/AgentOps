"""
Comprehensive route testing suite for Phase 2.2 — Step 3: Workflow CRUD API Routes.
Verifies all 5 endpoints, status codes (201, 200, 204, 404, 409, 422),
pagination, filtering, X-Total-Count, ObjectId serialization, operational health & agents routes,
and cleans up all test records.
"""

import asyncio
import json
import sys
from bson import ObjectId

from app.main import app, lifespan
from app.database import get_database, close_database_connection


async def make_request(method: str, path: str, body: dict = None):
    """
    Direct in-memory ASGI request dispatcher without requiring external HTTP servers or ports.
    """
    path_only, _, qs = path.partition("?")
    body_bytes = json.dumps(body).encode("utf-8") if body is not None else b""
    headers = [
        (b"host", b"localhost"),
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body_bytes)).encode("ascii")),
    ]

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path_only,
        "raw_path": path_only.encode("ascii"),
        "query_string": qs.encode("ascii"),
        "root_path": "",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 80),
    }

    response_messages = []

    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    async def send(message):
        response_messages.append(message)

    await app(scope, receive, send)

    status_code = None
    resp_headers = {}
    resp_body = b""

    for msg in response_messages:
        if msg["type"] == "http.response.start":
            status_code = msg["status"]
            resp_headers = {
                k.decode("ascii").lower(): v.decode("ascii")
                for k, v in msg.get("headers", [])
            }
        elif msg["type"] == "http.response.body":
            resp_body += msg.get("body", b"")

    try:
        data = json.loads(resp_body.decode("utf-8")) if resp_body else None
    except Exception:
        data = resp_body.decode("utf-8")

    return status_code, resp_headers, data


async def run_workflow_route_tests():
    print("=" * 65)
    print("RUNNING PHASE 2.2 STEP 3: WORKFLOW CRUD API ROUTE TESTS")
    print("=" * 65)

    total_passed = 0
    total_failed = 0

    def assert_test(condition: bool, test_name: str, details: str = ""):
        nonlocal total_passed, total_failed
        if condition:
            print(f" [PASS] {test_name}")
            total_passed += 1
        else:
            print(f" [FAIL] {test_name} - {details}")
            total_failed += 1

    test_wf_1 = "Route-Trench-Mapping-Flow-1"
    test_wf_2 = "Route-Trench-Mapping-Flow-2"
    wf_1_id = None
    wf_2_id = None

    db = get_database()
    if db is None:
        print("[FATAL] Could not connect to MongoDB Atlas.")
        sys.exit(1)

    # Clean up any leftover test data
    db["workflows"].delete_many({"name": {"$in": [test_wf_1, test_wf_2]}})

    async with lifespan(app):
        # ----------------------------------------------------
        # 1. VERIFY EXISTING HEALTH & AGENTS ROUTES REMAIN WORKING
        # ----------------------------------------------------
        print("\n--- Test 1: Preserving Health & Agent Endpoints ---")
        status_code, _, body = await make_request("GET", "/api/v1/health")
        assert_test(status_code == 200, "GET /api/v1/health returns 200 OK")
        assert_test(body.get("status") == "healthy", "Application health status is 'healthy'")

        status_code, _, body = await make_request("GET", "/api/v1/health/database")
        assert_test(status_code == 200, "GET /api/v1/health/database returns 200 OK")
        assert_test(body.get("status") == "connected", "Database health status is 'connected'")

        status_code, _, body = await make_request("GET", "/api/v1/agents")
        assert_test(status_code == 200, "GET /api/v1/agents returns 200 OK (Agents API intact)")
        assert_test(isinstance(body, list), "Agents list returns JSON list")

        # ----------------------------------------------------
        # 2. TEST POST /api/v1/workflows (CREATE)
        # ----------------------------------------------------
        print("\n--- Test 2: POST /api/v1/workflows (Create Workflow) ---")
        create_payload_1 = {
            "name": test_wf_1,
            "description": "Deep autonomous survey flow across Marianas trench",
            "status": "draft",
            "steps": [
                {
                    "stepId": "s-1",
                    "name": "Sonar Sweep Calibration",
                    "description": "Initialize multi-beam echo sounder",
                    "order": 0,
                    "config": {"frequencyKhz": 12.0},
                },
                {
                    "stepId": "s-2",
                    "name": "Hydrothermal Sensor Scan",
                    "order": 1,
                },
            ],
        }
        status_code, _, body = await make_request("POST", "/api/v1/workflows", create_payload_1)
        assert_test(status_code == 201, "POST /api/v1/workflows returns 201 Created")
        assert_test(isinstance(body, dict), "Response body is a JSON object")
        assert_test("id" in body and ObjectId.is_valid(body["id"]), "Response 'id' is a valid stringified ObjectId")
        assert_test("_id" not in body, "Response does NOT leak raw MongoDB '_id'")
        assert_test(body.get("name") == test_wf_1, "Workflow name matches payload")
        assert_test(body.get("status") == "draft", "Default status is 'draft'")
        assert_test(len(body.get("steps", [])) == 2, "Workflow contains 2 steps")
        assert_test(body["steps"][0]["stepId"] == "s-1", "Step fields use camelCase alias")
        assert_test("created_at" in body and "updated_at" in body, "Timestamps present in response")

        wf_1_id = body.get("id")

        # Create Workflow 2 for pagination & conflict testing
        create_payload_2 = {
            "name": test_wf_2,
            "description": "Relay communications buoy mesh",
            "status": "paused",
            "steps": [],
        }
        status_code, _, body2 = await make_request("POST", "/api/v1/workflows", create_payload_2)
        assert_test(status_code == 201, "POST /api/v1/workflows (second workflow) returns 201 Created")
        wf_2_id = body2.get("id")

        # ----------------------------------------------------
        # 3. TEST 409 CONFLICT (DUPLICATE NAME)
        # ----------------------------------------------------
        print("\n--- Test 3: POST /api/v1/workflows (Duplicate Name Conflict) ---")
        status_code, _, body = await make_request("POST", "/api/v1/workflows", create_payload_1)
        assert_test(status_code == 409, "POST with duplicate name returns 409 Conflict")
        assert_test("already exists" in body.get("detail", ""), "409 detail explains duplicate name")

        # ----------------------------------------------------
        # 4. TEST 422 UNPROCESSABLE ENTITY (INVALID INPUT)
        # ----------------------------------------------------
        print("\n--- Test 4: POST /api/v1/workflows (Invalid Request Payload) ---")
        # Empty workflow name
        status_code, _, body = await make_request("POST", "/api/v1/workflows", {"name": "   "})
        assert_test(status_code == 422, "POST with whitespace name returns 422 Unprocessable Entity")

        # Negative step order
        bad_step_payload = {
            "name": "Invalid Step Order Flow",
            "steps": [{"stepId": "bad-1", "name": "Step A", "order": -1}],
        }
        status_code, _, body = await make_request("POST", "/api/v1/workflows", bad_step_payload)
        assert_test(status_code == 422, "POST with negative step order returns 422 Unprocessable Entity")

        # Duplicate step IDs
        dup_step_payload = {
            "name": "Dup Step ID Flow",
            "steps": [
                {"stepId": "same-id", "name": "Step A", "order": 0},
                {"stepId": "same-id", "name": "Step B", "order": 1},
            ],
        }
        status_code, _, body = await make_request("POST", "/api/v1/workflows", dup_step_payload)
        assert_test(status_code == 422, "POST with duplicate step IDs returns 422 Unprocessable Entity")

        # Invalid status
        bad_status_payload = {"name": "Bad Status Flow", "status": "flying"}
        status_code, _, body = await make_request("POST", "/api/v1/workflows", bad_status_payload)
        assert_test(status_code == 422, "POST with invalid status returns 422 Unprocessable Entity")

        # ----------------------------------------------------
        # 5. TEST GET /api/v1/workflows/{workflow_id} (GET BY ID)
        # ----------------------------------------------------
        print("\n--- Test 5: GET /api/v1/workflows/{workflow_id} ---")
        status_code, _, body = await make_request("GET", f"/api/v1/workflows/{wf_1_id}")
        assert_test(status_code == 200, "GET /api/v1/workflows/{id} returns 200 OK")
        assert_test(body.get("id") == wf_1_id, "Retrieved ID matches requested ID")
        assert_test(body.get("name") == test_wf_1, "Retrieved workflow name matches")
        assert_test(len(body.get("steps", [])) == 2, "Retrieved workflow steps preserved")

        # Missing Workflow ID (valid ObjectId format)
        status_code, _, body = await make_request("GET", "/api/v1/workflows/000000000000000000000000")
        assert_test(status_code == 404, "GET non-existent ObjectId returns 404 Not Found")

        # Missing Workflow ID (malformed string)
        status_code, _, body = await make_request("GET", "/api/v1/workflows/unknown-slug-or-id")
        assert_test(status_code == 404, "GET malformed ID returns 404 Not Found")

        # ----------------------------------------------------
        # 6. TEST PATCH /api/v1/workflows/{workflow_id} (PARTIAL UPDATE)
        # ----------------------------------------------------
        print("\n--- Test 6: PATCH /api/v1/workflows/{workflow_id} (Partial Update) ---")
        patch_payload = {
            "status": "active",
            "description": "Activated trench survey mission pipeline",
        }
        status_code, _, body = await make_request("PATCH", f"/api/v1/workflows/{wf_1_id}", patch_payload)
        assert_test(status_code == 200, "PATCH returns 200 OK")
        assert_test(body.get("status") == "active", "Status updated to 'active'")
        assert_test(body.get("description") == "Activated trench survey mission pipeline", "Description updated")
        assert_test(body.get("name") == test_wf_1, "Unmodified name preserved")
        assert_test(len(body.get("steps", [])) == 2, "Unmodified steps preserved")

        # Conflict on renaming to existing workflow's name
        conflict_patch = {"name": test_wf_2}
        status_code, _, body = await make_request("PATCH", f"/api/v1/workflows/{wf_1_id}", conflict_patch)
        assert_test(status_code == 409, "PATCH with conflicting name returns 409 Conflict")

        # PATCH non-existent workflow
        status_code, _, body = await make_request("PATCH", "/api/v1/workflows/000000000000000000000000", {"status": "active"})
        assert_test(status_code == 404, "PATCH non-existent workflow returns 404 Not Found")

        # PATCH with invalid whitespace name
        status_code, _, body = await make_request("PATCH", f"/api/v1/workflows/{wf_1_id}", {"name": "   "})
        assert_test(status_code == 422, "PATCH with whitespace name returns 422 Unprocessable Entity")

        # ----------------------------------------------------
        # 7. TEST GET /api/v1/workflows (PAGINATION & FILTERING)
        # ----------------------------------------------------
        print("\n--- Test 7: GET /api/v1/workflows (Pagination & Filtering) ---")
        status_code, headers, body = await make_request("GET", "/api/v1/workflows?limit=1&skip=0")
        assert_test(status_code == 200, "GET /api/v1/workflows returns 200 OK")
        assert_test(isinstance(body, list), "GET /api/v1/workflows returns a JSON list")
        assert_test(len(body) == 1, "Limit=1 restricts returned items to 1")
        assert_test("x-total-count" in headers, "Response includes 'X-Total-Count' header")
        total_count = int(headers.get("x-total-count", 0))
        assert_test(total_count >= 2, f"X-Total-Count reflects total records (got {total_count})")

        # Filter by status=active (Workflow 1 was updated to active)
        status_code, headers, body = await make_request("GET", "/api/v1/workflows?status=active")
        assert_test(status_code == 200, "Filtering by status=active returns 200 OK")
        assert_test(any(w["id"] == wf_1_id for w in body), "Workflow 1 present in status=active query")

        # Filter by status=failed (Neither workflow is failed)
        status_code, headers, body = await make_request("GET", "/api/v1/workflows?status=failed")
        assert_test(status_code == 200, "Filtering by status=failed returns 200 OK")
        assert_test(not any(w["id"] in [wf_1_id, wf_2_id] for w in body), "Test workflows absent in status=failed query")

        # High skip offset
        status_code, _, body = await make_request("GET", "/api/v1/workflows?skip=1000")
        assert_test(len(body) == 0, "High skip offset returns empty list")

        # ----------------------------------------------------
        # 8. TEST DELETE /api/v1/workflows/{workflow_id}
        # ----------------------------------------------------
        print("\n--- Test 8: DELETE /api/v1/workflows/{workflow_id} ---")
        status_code, _, body = await make_request("DELETE", f"/api/v1/workflows/{wf_1_id}")
        assert_test(status_code == 204, "DELETE /api/v1/workflows/{id} returns 204 No Content")

        # Verify workflow 1 is gone
        status_code, _, _ = await make_request("GET", f"/api/v1/workflows/{wf_1_id}")
        assert_test(status_code == 404, "Querying deleted workflow returns 404 Not Found")

        # Delete again returns 404
        status_code, _, _ = await make_request("DELETE", f"/api/v1/workflows/{wf_1_id}")
        assert_test(status_code == 404, "Deleting already deleted workflow returns 404 Not Found")

        # Delete workflow 2
        status_code, _, _ = await make_request("DELETE", f"/api/v1/workflows/{wf_2_id}")
        assert_test(status_code == 204, "Deleting second workflow returns 204 No Content")

        # ----------------------------------------------------
        # 9. FINAL CLEANUP VERIFICATION (INSIDE LIFESPAN)
        # ----------------------------------------------------
        db["workflows"].delete_many({"name": {"$in": [test_wf_1, test_wf_2]}})
        remaining = db["workflows"].count_documents({"name": {"$in": [test_wf_1, test_wf_2]}})
        assert_test(remaining == 0, "Cleanup: Zero lingering test records in database")

    # ----------------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------------
    print("\n" + "=" * 65)
    print(f"TEST SUMMARY: {total_passed} Passed, {total_failed} Failed")
    print("=" * 65)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_workflow_route_tests())
