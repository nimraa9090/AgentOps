"""
Verification script for Phase 2.1 — Step 1: Models Foundation & Agent Schemas.
Tests valid data, invalid data, defaults, ObjectId handling, and frontend AgentInfo compatibility.
"""

import sys
import json
from datetime import datetime
from bson import ObjectId
from pydantic import ValidationError

from app.models import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentInDB,
    AgentStatus,
    OperationalDepth,
    compute_codenamed_depth,
)


def run_tests():
    print("=" * 60)
    print("RUNNING PHASE 2.1 STEP 1 MODEL VERIFICATION TESTS")
    print("=" * 60)
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

    # ----------------------------------------------------
    # TEST 1: Valid Agent Creation & Defaults
    # ----------------------------------------------------
    print("\n--- Test 1: Valid Agent Data & Defaults ---")
    try:
        agent_in = AgentCreate(
            name="Kraken-Router",
            role="Central Orchestrator",
            model="Claude 3.7 Sonnet",
            operationalDepthMeters=10920,
        )
        assert_test(agent_in.name == "Kraken-Router", "AgentCreate: Name matches")
        assert_test(agent_in.status == AgentStatus.IDLE, "AgentCreate: Status defaults to 'idle'")
        assert_test(agent_in.current_task == "Standby", "AgentCreate: Current task defaults to 'Standby'")
        assert_test(agent_in.codenamed_depth == "Hadopelagic (10920m)", "AgentCreate: Codenamed depth auto-computed")
        assert_test(agent_in.temperature == 0.7, "AgentCreate: Temperature defaults to 0.7")
        assert_test(agent_in.max_tokens == 4096, "AgentCreate: Max tokens defaults to 4096")
    except Exception as e:
        assert_test(False, "Valid Agent Creation", str(e))

    # ----------------------------------------------------
    # TEST 2: Invalid Data Rejection
    # ----------------------------------------------------
    print("\n--- Test 2: Invalid Data Rejection ---")
    
    # 2a: Name too short / whitespace
    try:
        AgentCreate(name=" ", role="Tester", model="GPT-4o")
        assert_test(False, "Invalid Name: Pure whitespace should fail")
    except ValidationError:
        assert_test(True, "Invalid Name: Pure whitespace rejected")

    # 2b: Invalid Status
    try:
        AgentCreate(name="Valid Agent", role="Tester", model="GPT-4o", status="sleeping")
        assert_test(False, "Invalid Status: 'sleeping' should fail")
    except ValidationError:
        assert_test(True, "Invalid Status: Non-existent enum value rejected")

    # 2c: Temperature out of range (> 2.0)
    try:
        AgentCreate(name="Valid Agent", role="Tester", model="GPT-4o", temperature=2.5)
        assert_test(False, "Invalid Temperature: 2.5 should fail")
    except ValidationError:
        assert_test(True, "Invalid Temperature: > 2.0 rejected")

    # 2d: Operational depth out of range (> 11,500m)
    try:
        AgentCreate(name="Valid Agent", role="Tester", model="GPT-4o", operationalDepthMeters=15000)
        assert_test(False, "Invalid Depth: 15,000m should fail")
    except ValidationError:
        assert_test(True, "Invalid Depth: > 11,500m rejected")

    # ----------------------------------------------------
    # TEST 3: Partial AgentUpdate Validation
    # ----------------------------------------------------
    print("\n--- Test 3: AgentUpdate Validation ---")
    try:
        update_data = AgentUpdate(
            status=AgentStatus.COMPUTING,
            currentTask="Refactoring microservices",
            memoryUsageMb=512.5,
        )
        assert_test(update_data.status == AgentStatus.COMPUTING, "AgentUpdate: Status updated to 'computing'")
        assert_test(update_data.current_task == "Refactoring microservices", "AgentUpdate: Task updated via camelCase alias")
        assert_test(update_data.memory_usage_mb == 512.5, "AgentUpdate: Memory updated")
        assert_test(update_data.name is None, "AgentUpdate: Unspecified fields are None")
    except Exception as e:
        assert_test(False, "AgentUpdate Validation", str(e))

    # ----------------------------------------------------
    # TEST 4: MongoDB ObjectId Serialization
    # ----------------------------------------------------
    print("\n--- Test 4: MongoDB ObjectId Serialization ---")
    fake_mongo_id = ObjectId("654a1b2c3d4e5f6a7b8c9d0e")
    raw_mongo_doc = {
        "_id": fake_mongo_id,
        "name": "Nautilus-CodeSynth",
        "role": "Code Synthesis & AST Verification",
        "model": "GPT-4o",
        "status": "computing",
        "codenamedDepth": "Abyssopelagic (6,200m)",
        "currentTask": "Refactoring microservice GraphQL resolvers",
        "operationalDepthMeters": 6240,
        "memoryUsageMb": 1140.0,
        "tokensProcessed": 1240900,
        "avgLatencyMs": 910.0,
        "successRatePercent": 99.1,
        "uptimeHours": 198.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    try:
        agent_resp = AgentResponse.model_validate(raw_mongo_doc)
        assert_test(agent_resp.id == str(fake_mongo_id), "ObjectId: _id mapped to string id")
        assert_test(isinstance(agent_resp.id, str), "ObjectId: id is Python str instance")

        dumped_dict = agent_resp.model_dump(by_alias=True)
        assert_test("id" in dumped_dict, "Serialized Dict: Contains 'id' key")
        assert_test("_id" not in dumped_dict, "Serialized Dict: Does NOT expose raw '_id' key")
        assert_test(dumped_dict["id"] == "654a1b2c3d4e5f6a7b8c9d0e", "Serialized Dict: ID matches ObjectId string")

        dumped_json = agent_resp.model_dump_json(by_alias=True)
        parsed_json = json.loads(dumped_json)
        assert_test(parsed_json["id"] == "654a1b2c3d4e5f6a7b8c9d0e", "JSON Output: 'id' serialized correctly in JSON")
    except Exception as e:
        assert_test(False, "ObjectId Serialization", str(e))

    # ----------------------------------------------------
    # TEST 5: Exact Frontend AgentInfo Compatibility
    # ----------------------------------------------------
    print("\n--- Test 5: Frontend AgentInfo Compatibility ---")
    # From frontend/lib/mock-data.ts (agt-001)
    frontend_mock_agent = {
        "id": "agt-001",
        "name": "Kraken-Router v2.4",
        "codenamedDepth": "Hadopelagic (10,900m)",
        "role": "Central Orchestrator & Task Decomposer",
        "model": "Claude 3.7 Sonnet (Hybrid Reasoning)",
        "status": "active",
        "currentTask": "Decomposing high-level user objective into 14 subsea parallel execution steps",
        "operationalDepthMeters": 10920,
        "memoryUsageMb": 824,
        "tokensProcessed": 842100,
        "avgLatencyMs": 640,
        "successRatePercent": 99.8,
        "uptimeHours": 342,
    }

    try:
        validated_agent = AgentResponse.model_validate(frontend_mock_agent)
        serialized_for_frontend = validated_agent.model_dump(by_alias=True)

        required_frontend_keys = [
            "id",
            "name",
            "codenamedDepth",
            "role",
            "model",
            "status",
            "currentTask",
            "operationalDepthMeters",
            "memoryUsageMb",
            "tokensProcessed",
            "avgLatencyMs",
            "successRatePercent",
            "uptimeHours",
        ]

        all_keys_present = True
        for key in required_frontend_keys:
            if key not in serialized_for_frontend:
                print(f"Missing required frontend key: {key}")
                all_keys_present = False
            else:
                # Check types match frontend expectations
                val = serialized_for_frontend[key]
                expected_type = type(frontend_mock_agent[key])
                if not isinstance(val, (expected_type, float, int)):
                    print(f"Type mismatch for {key}: expected {expected_type}, got {type(val)}")
                    all_keys_present = False

        assert_test(all_keys_present, "Frontend Compatibility: All 13 AgentInfo fields present with matching types")
        assert_test(serialized_for_frontend["status"] == "active", "Frontend Compatibility: Status is 'active'")
        assert_test(serialized_for_frontend["codenamedDepth"] == "Hadopelagic (10,900m)", "Frontend Compatibility: codenamedDepth matches")
    except Exception as e:
        assert_test(False, "Frontend AgentInfo Compatibility", str(e))

    # ----------------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------------
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {total_passed} Passed, {total_failed} Failed")
    print("=" * 60)
    
    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
