"""
Comprehensive route testing suite for Phase 2.1 — Step 3: Agent CRUD API Routes.
Verifies all 5 endpoints, status codes (201, 200, 204, 404, 409, 422),
pagination, filtering, ObjectId serialization, and cleans up all test records.
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


async def run_route_tests():
    print("=" * 65)
    print("RUNNING PHASE 2.1 STEP 3: AGENT CRUD API ROUTE TESTS")
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

    test_agent_1 = "Nautilus-Route-Test-1"
    test_agent_2 = "Nautilus-Route-Test-2"
    agent_1_id = None
    agent_2_id = None

    db = get_database()
    if db is None:
        print("[FATAL] Could not connect to MongoDB Atlas.")
        sys.exit(1)

    # Clean up any leftover test data
    db["agents"].delete_many({"name": {"$in": [test_agent_1, test_agent_2]}})

    async with lifespan(app):
        # ----------------------------------------------------
        # 1. TEST EXISTING HEALTH ENDPOINTS
        # ----------------------------------------------------
        print("\n--- Test 1: Preserving Health Endpoints ---")
        status_code, _, body = await make_request("GET", "/api/v1/health")
        assert_test(status_code == 200, "GET /api/v1/health returns 200 OK")
        assert_test(body.get("status") == "healthy", "Application health status is 'healthy'")

        status_code, _, body = await make_request("GET", "/api/v1/health/database")
        assert_test(status_code == 200, "GET /api/v1/health/database returns 200 OK")
        assert_test(body.get("status") == "connected", "Database health status is 'connected'")

        # ----------------------------------------------------
        # 2. TEST POST /api/v1/agents (CREATE)
        # ----------------------------------------------------
        print("\n--- Test 2: POST /api/v1/agents (Create Agent) ---")
        create_payload_1 = {
            "name": test_agent_1,
            "role": "Autonomous Deep-Sea Navigator",
            "model": "Claude 3.7 Sonnet",
            "operationalDepthMeters": 6000,
            "currentTask": "Navigating abyssal trench",
            "temperature": 0.5,
            "max_tokens": 8192,
        }
        status_code, _, body = await make_request("POST", "/api/v1/agents", create_payload_1)
        assert_test(status_code == 201, "POST /api/v1/agents returns 201 Created")
        assert_test(isinstance(body, dict), "Response body is a JSON object")
        assert_test("id" in body and ObjectId.is_valid(body["id"]), "Response 'id' is a valid stringified ObjectId")
        assert_test("_id" not in body, "Response does NOT leak raw MongoDB '_id'")
        assert_test(body.get("name") == test_agent_1, "Agent name matches payload")
        assert_test(body.get("status") == "idle", "Default status is 'idle'")
        assert_test(body.get("codenamedDepth") == "Abyssopelagic (6000m)", "Auto-computed codenamedDepth matches")
        assert_test(body.get("operationalDepthMeters") == 6000, "operationalDepthMeters serialized correctly")
        assert_test(body.get("memoryUsageMb") == 0.0, "memoryUsageMb defaults to 0.0")
        assert_test(body.get("successRatePercent") == 100.0, "successRatePercent defaults to 100.0")

        agent_1_id = body.get("id")

        # Create Agent 2 for pagination & conflict testing
        create_payload_2 = {
            "name": test_agent_2,
            "role": "Subsea Sonar Array",
            "model": "GPT-4o",
            "operationalDepthMeters": 2000,
        }
        status_code, _, body2 = await make_request("POST", "/api/v1/agents", create_payload_2)
        assert_test(status_code == 201, "POST /api/v1/agents (second agent) returns 201 Created")
        agent_2_id = body2.get("id")

        # ----------------------------------------------------
        # 3. TEST 409 CONFLICT (DUPLICATE NAME)
        # ----------------------------------------------------
        print("\n--- Test 3: POST /api/v1/agents (Duplicate Name Conflict) ---")
        status_code, _, body = await make_request("POST", "/api/v1/agents", create_payload_1)
        assert_test(status_code == 409, "POST with duplicate name returns 409 Conflict")
        assert_test("already exists" in body.get("detail", ""), "409 detail explains duplicate name")

        # ----------------------------------------------------
        # 4. TEST 422 UNPROCESSABLE ENTITY (INVALID INPUT)
        # ----------------------------------------------------
        print("\n--- Test 4: POST /api/v1/agents (Invalid Request Payload) ---")
        invalid_payload = {
            "name": "",  # Empty string rejected by validator
            "role": "Tester",
            "model": "GPT-4o",
            "temperature": 5.0,  # Out of bounds (> 2.0)
        }
        status_code, _, body = await make_request("POST", "/api/v1/agents", invalid_payload)
        assert_test(status_code == 422, "POST with invalid payload returns 422 Unprocessable Entity")
        assert_test("detail" in body, "422 response includes validation details")

        # ----------------------------------------------------
        # 5. TEST GET /api/v1/agents/{agent_id} (GET BY ID)
        # ----------------------------------------------------
        print("\n--- Test 5: GET /api/v1/agents/{agent_id} ---")
        status_code, _, body = await make_request("GET", f"/api/v1/agents/{agent_1_id}")
        assert_test(status_code == 200, "GET /api/v1/agents/{id} returns 200 OK")
        assert_test(body.get("id") == agent_1_id, "Retrieved ID matches requested ID")
        assert_test(body.get("name") == test_agent_1, "Retrieved agent name matches")
        assert_test(body.get("role") == "Autonomous Deep-Sea Navigator", "Retrieved agent role matches")

        # Missing Agent ID (valid ObjectId format)
        status_code, _, body = await make_request("GET", "/api/v1/agents/000000000000000000000000")
        assert_test(status_code == 404, "GET non-existent ObjectId returns 404 Not Found")

        # Missing Agent ID (malformed string)
        status_code, _, body = await make_request("GET", "/api/v1/agents/unknown-slug-or-id")
        assert_test(status_code == 404, "GET malformed ID returns 404 Not Found")

        # ----------------------------------------------------
        # 6. TEST PATCH /api/v1/agents/{agent_id} (UPDATE)
        # ----------------------------------------------------
        print("\n--- Test 6: PATCH /api/v1/agents/{agent_id} (Partial Update) ---")
        patch_payload = {
            "status": "computing",
            "currentTask": "Computing acoustic trajectory through trench",
            "memoryUsageMb": 512.5,
        }
        status_code, _, body = await make_request("PATCH", f"/api/v1/agents/{agent_1_id}", patch_payload)
        assert_test(status_code == 200, "PATCH returns 200 OK")
        assert_test(body.get("status") == "computing", "Status updated to 'computing'")
        assert_test(body.get("currentTask") == "Computing acoustic trajectory through trench", "currentTask updated")
        assert_test(body.get("memoryUsageMb") == 512.5, "memoryUsageMb updated to 512.5")
        assert_test(body.get("name") == test_agent_1, "Unmodified fields remain intact")

        # Conflict on renaming to existing agent's name
        conflict_patch = {"name": test_agent_2}
        status_code, _, body = await make_request("PATCH", f"/api/v1/agents/{agent_1_id}", conflict_patch)
        assert_test(status_code == 409, "PATCH with conflicting name returns 409 Conflict")

        # PATCH non-existent agent
        status_code, _, body = await make_request("PATCH", "/api/v1/agents/000000000000000000000000", {"status": "active"})
        assert_test(status_code == 404, "PATCH non-existent agent returns 404 Not Found")

        # ----------------------------------------------------
        # 7. TEST GET /api/v1/agents (PAGINATION & FILTERING)
        # ----------------------------------------------------
        print("\n--- Test 7: GET /api/v1/agents (Pagination & Filtering) ---")
        status_code, headers, body = await make_request("GET", "/api/v1/agents?limit=1&skip=0")
        assert_test(status_code == 200, "GET /api/v1/agents returns 200 OK")
        assert_test(isinstance(body, list), "GET /api/v1/agents returns a JSON list")
        assert_test(len(body) == 1, "Limit=1 restricts returned items to 1")
        assert_test("x-total-count" in headers, "Response includes 'X-Total-Count' header")
        total_count = int(headers.get("x-total-count", 0))
        assert_test(total_count >= 2, f"X-Total-Count reflects total records (got {total_count})")

        # Filter by status=computing (Agent 1 was updated to computing)
        status_code, headers, body = await make_request("GET", "/api/v1/agents?status=computing")
        assert_test(status_code == 200, "Filtering by status=computing returns 200 OK")
        assert_test(any(a["id"] == agent_1_id for a in body), "Agent 1 present in status=computing query")

        # Filter by status=degraded (Neither agent is degraded)
        status_code, headers, body = await make_request("GET", "/api/v1/agents?status=degraded")
        assert_test(status_code == 200, "Filtering by status=degraded returns 200 OK")
        assert_test(not any(a["id"] in [agent_1_id, agent_2_id] for a in body), "Test agents absent in status=degraded query")

        # ----------------------------------------------------
        # 8. TEST DELETE /api/v1/agents/{agent_id}
        # ----------------------------------------------------
        print("\n--- Test 8: DELETE /api/v1/agents/{agent_id} ---")
        status_code, _, body = await make_request("DELETE", f"/api/v1/agents/{agent_1_id}")
        assert_test(status_code == 204, "DELETE /api/v1/agents/{id} returns 204 No Content")

        # Verify agent 1 is gone
        status_code, _, _ = await make_request("GET", f"/api/v1/agents/{agent_1_id}")
        assert_test(status_code == 404, "Querying deleted agent returns 404 Not Found")

        # Delete again returns 404
        status_code, _, _ = await make_request("DELETE", f"/api/v1/agents/{agent_1_id}")
        assert_test(status_code == 404, "Deleting already deleted agent returns 404 Not Found")

        # Delete agent 2
        status_code, _, _ = await make_request("DELETE", f"/api/v1/agents/{agent_2_id}")
        assert_test(status_code == 204, "Deleting second agent returns 204 No Content")

        # ----------------------------------------------------
        # 9. FINAL CLEANUP VERIFICATION (INSIDE LIFESPAN)
        # ----------------------------------------------------
        db["agents"].delete_many({"name": {"$in": [test_agent_1, test_agent_2]}})
        remaining = db["agents"].count_documents({"name": {"$in": [test_agent_1, test_agent_2]}})
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
    asyncio.run(run_route_tests())
