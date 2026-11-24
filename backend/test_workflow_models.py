"""
Test suite for Phase 2.2 — Step 1: Workflow Models & Schemas.
Tests valid creation, defaults, optional fields, invalid names, negative step order,
status validation, partial updates, and MongoDB ObjectId serialization.
"""

import json
import sys
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import ValidationError

from app.models import (
    WorkflowBase,
    WorkflowCreate,
    WorkflowInDB,
    WorkflowResponse,
    WorkflowStatus,
    WorkflowStep,
    WorkflowUpdate,
)


def run_tests():
    print("=" * 65)
    print("RUNNING PHASE 2.2 STEP 1: WORKFLOW MODEL VERIFICATION TESTS")
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

    # ----------------------------------------------------
    # TEST 1: Valid Workflow Creation & Default Values
    # ----------------------------------------------------
    print("\n--- Test 1: Valid Workflow Creation & Defaults ---")
    try:
        wf = WorkflowCreate(name="Abyssal Trench Mapping Pipeline")
        assert_test(wf.name == "Abyssal Trench Mapping Pipeline", "WorkflowCreate: Name matches")
        assert_test(wf.description is None, "WorkflowCreate: Description defaults to None")
        assert_test(wf.status == WorkflowStatus.DRAFT, "WorkflowCreate: Status defaults to 'draft'")
        assert_test(wf.steps == [], "WorkflowCreate: Steps defaults to empty list")
    except Exception as e:
        assert_test(False, "Valid Workflow Creation", str(e))

    # ----------------------------------------------------
    # TEST 2: Workflow Steps & Optional Fields
    # ----------------------------------------------------
    print("\n--- Test 2: Workflow Steps & Optional Fields ---")
    try:
        step1 = WorkflowStep(
            stepId="step-01",
            name="Sonar Pulse Sweep",
            description="High frequency bathymetric ping",
            agentId="agt-001",
            order=0,
            config={"frequencyKhz": 12.5, "sampleRate": 44100},
        )
        assert_test(step1.step_id == "step-01", "WorkflowStep: step_id matches via alias")
        assert_test(step1.name == "Sonar Pulse Sweep", "WorkflowStep: Name matches")
        assert_test(step1.description == "High frequency bathymetric ping", "WorkflowStep: Description matches")
        assert_test(step1.agent_id == "agt-001", "WorkflowStep: agent_id matches via alias")
        assert_test(step1.order == 0, "WorkflowStep: Order 0 accepted")
        assert_test(step1.config == {"frequencyKhz": 12.5, "sampleRate": 44100}, "WorkflowStep: Config dict matches")

        # Step with minimal fields
        step2 = WorkflowStep(
            step_id="step-02",
            name="Telemetry Routing",
            order=1,
        )
        assert_test(step2.description is None, "WorkflowStep: Description is optional (None)")
        assert_test(step2.agent_id is None, "WorkflowStep: agent_id is optional (None)")
        assert_test(step2.config is None, "WorkflowStep: config is optional (None)")

        # Workflow with steps included
        wf_with_steps = WorkflowCreate(
            name="Seafloor Scanning Flow",
            description="Autonomous multi-step scanning sequence",
            status=WorkflowStatus.ACTIVE,
            steps=[step1, step2],
        )
        assert_test(len(wf_with_steps.steps) == 2, "WorkflowCreate: Contains 2 steps")
        assert_test(wf_with_steps.status == WorkflowStatus.ACTIVE, "WorkflowCreate: Explicit status 'active'")
        assert_test(wf_with_steps.description == "Autonomous multi-step scanning sequence", "WorkflowCreate: Description matches")
    except Exception as e:
        assert_test(False, "Workflow Steps & Optional Fields", str(e))

    # ----------------------------------------------------
    # TEST 3: Negative Step Order Rejection
    # ----------------------------------------------------
    print("\n--- Test 3: Negative Step Order Validation ---")
    try:
        WorkflowStep(step_id="s1", name="Invalid Step", order=-1)
        assert_test(False, "Negative Order: order=-1 should fail")
    except ValidationError:
        assert_test(True, "Negative Order: order=-1 rejected by validator")

    try:
        WorkflowStep(step_id="s1", name="Invalid Step", order=-99)
        assert_test(False, "Negative Order: order=-99 should fail")
    except ValidationError:
        assert_test(True, "Negative Order: order=-99 rejected by validator")

    # ----------------------------------------------------
    # TEST 4: Name Validation (Empty / Whitespace / Too Short)
    # ----------------------------------------------------
    print("\n--- Test 4: Name Validation ---")
    # Empty workflow name
    try:
        WorkflowCreate(name="")
        assert_test(False, "Empty Name: '' should fail")
    except ValidationError:
        assert_test(True, "Empty Name: '' rejected")

    # Pure whitespace workflow name
    try:
        WorkflowCreate(name="   ")
        assert_test(False, "Whitespace Name: '   ' should fail")
    except ValidationError:
        assert_test(True, "Whitespace Name: '   ' rejected")

    # Name too short (< 2 chars)
    try:
        WorkflowCreate(name="X")
        assert_test(False, "Short Name: 'X' should fail")
    except ValidationError:
        assert_test(True, "Short Name: 'X' rejected")

    # Empty step name
    try:
        WorkflowStep(step_id="s1", name="", order=0)
        assert_test(False, "Empty Step Name: '' should fail")
    except ValidationError:
        assert_test(True, "Empty Step Name: '' rejected")

    # Pure whitespace step name
    try:
        WorkflowStep(step_id="s1", name="   ", order=0)
        assert_test(False, "Whitespace Step Name: '   ' should fail")
    except ValidationError:
        assert_test(True, "Whitespace Step Name: '   ' rejected")

    # Empty step_id
    try:
        WorkflowStep(step_id="", name="Valid Step", order=0)
        assert_test(False, "Empty step_id: '' should fail")
    except ValidationError:
        assert_test(True, "Empty step_id: '' rejected")

    # ----------------------------------------------------
    # TEST 5: Unique Step ID Validation
    # ----------------------------------------------------
    print("\n--- Test 5: Unique Step ID Validation ---")
    try:
        WorkflowCreate(
            name="Duplicate Steps Flow",
            steps=[
                WorkflowStep(step_id="dup-step", name="Step A", order=0),
                WorkflowStep(step_id="dup-step", name="Step B", order=1),
            ],
        )
        assert_test(False, "Duplicate Step IDs: Should fail validation")
    except ValidationError:
        assert_test(True, "Duplicate Step IDs: Rejected with validation error")

    # ----------------------------------------------------
    # TEST 6: WorkflowStatus Enum Validation
    # ----------------------------------------------------
    print("\n--- Test 6: WorkflowStatus Enum Validation ---")
    valid_statuses = ["draft", "active", "paused", "completed", "failed"]
    for s in valid_statuses:
        status_enum = WorkflowStatus(s)
        assert_test(status_enum.value == s, f"WorkflowStatus: '{s}' is a valid enum value")

    # Invalid status strings
    for bad_status in ["running", "cancelled", "unknown", ""]:
        try:
            WorkflowCreate(name="Status Test", status=bad_status)
            assert_test(False, f"Invalid Status: '{bad_status}' should fail")
        except ValidationError:
            assert_test(True, f"Invalid Status: '{bad_status}' rejected by validator")

    # ----------------------------------------------------
    # TEST 7: WorkflowUpdate (Partial Updates)
    # ----------------------------------------------------
    print("\n--- Test 7: WorkflowUpdate (Partial Updates) ---")
    try:
        # Status only update
        update_status = WorkflowUpdate(status=WorkflowStatus.PAUSED)
        assert_test(update_status.status == WorkflowStatus.PAUSED, "WorkflowUpdate: Status updated to 'paused'")
        assert_test(update_status.name is None, "WorkflowUpdate: Unset name is None")
        assert_test(update_status.description is None, "WorkflowUpdate: Unset description is None")
        assert_test(update_status.steps is None, "WorkflowUpdate: Unset steps is None")

        # Name and description update
        update_info = WorkflowUpdate(
            name="Renamed Workflow",
            description="New description",
        )
        assert_test(update_info.name == "Renamed Workflow", "WorkflowUpdate: Name updated")
        assert_test(update_info.description == "New description", "WorkflowUpdate: Description updated")
        assert_test(update_info.status is None, "WorkflowUpdate: Status remains None")

        # Steps update
        new_steps = [
            WorkflowStep(step_id="step-new", name="Updated Step", order=0),
        ]
        update_steps = WorkflowUpdate(steps=new_steps)
        assert_test(len(update_steps.steps) == 1, "WorkflowUpdate: Steps updated")

        # Invalid whitespace name in update
        try:
            WorkflowUpdate(name="   ")
            assert_test(False, "WorkflowUpdate: Whitespace name should fail")
        except ValidationError:
            assert_test(True, "WorkflowUpdate: Whitespace name rejected")

        # Duplicate step IDs in update
        try:
            WorkflowUpdate(steps=[
                WorkflowStep(step_id="same-id", name="S1", order=0),
                WorkflowStep(step_id="same-id", name="S2", order=1),
            ])
            assert_test(False, "WorkflowUpdate: Duplicate step IDs should fail")
        except ValidationError:
            assert_test(True, "WorkflowUpdate: Duplicate step IDs rejected")
    except Exception as e:
        assert_test(False, "WorkflowUpdate Validation", str(e))

    # ----------------------------------------------------
    # TEST 8: Serialization & MongoDB ObjectId Mapping
    # ----------------------------------------------------
    print("\n--- Test 8: Serialization & MongoDB ObjectId Mapping ---")
    fake_mongo_id = ObjectId("654a1b2c3d4e5f6a7b8c9d0e")
    now = datetime.now(timezone.utc)
    raw_mongo_doc = {
        "_id": fake_mongo_id,
        "name": "Abyssal Sonar Swarm Pipeline",
        "description": "Deep ocean autonomous survey",
        "status": "active",
        "steps": [
            {
                "stepId": "s-1",
                "name": "Ping Seafloor",
                "description": "Send acoustic ping",
                "agentId": "agt-001",
                "order": 0,
                "config": {"powerWatts": 500},
            }
        ],
        "created_at": now,
        "updated_at": now,
    }

    try:
        response = WorkflowResponse.model_validate(raw_mongo_doc)
        assert_test(response.id == str(fake_mongo_id), "WorkflowResponse: _id mapped to string 'id'")
        assert_test(isinstance(response.id, str), "WorkflowResponse: 'id' is Python str instance")
        assert_test(response.name == "Abyssal Sonar Swarm Pipeline", "WorkflowResponse: Name matches")
        assert_test(response.status == WorkflowStatus.ACTIVE, "WorkflowResponse: Status matches")
        assert_test(len(response.steps) == 1, "WorkflowResponse: Steps list preserved")
        assert_test(response.steps[0].step_id == "s-1", "WorkflowResponse: Step attributes preserved")

        # Serialization to dictionary
        dumped_dict = response.model_dump(by_alias=True)
        assert_test("id" in dumped_dict, "Serialized Dict: Contains 'id' key")
        assert_test("_id" not in dumped_dict, "Serialized Dict: Does NOT expose raw '_id'")
        assert_test(dumped_dict["id"] == "654a1b2c3d4e5f6a7b8c9d0e", "Serialized Dict: ID matches ObjectId string")
        assert_test(dumped_dict["steps"][0]["stepId"] == "s-1", "Serialized Dict: Step fields use camelCase aliases")

        # JSON serialization
        dumped_json = response.model_dump_json(by_alias=True)
        parsed_json = json.loads(dumped_json)
        assert_test("id" in parsed_json, "JSON Output: Contains 'id' key")
        assert_test("_id" not in parsed_json, "JSON Output: Does NOT contain '_id'")
        assert_test(parsed_json["id"] == "654a1b2c3d4e5f6a7b8c9d0e", "JSON Output: ID matches ObjectId string")
        assert_test(parsed_json["status"] == "active", "JSON Output: Status serialized as string")
    except Exception as e:
        assert_test(False, "Serialization & ObjectId Mapping", str(e))

    # ----------------------------------------------------
    # TEST 9: WorkflowInDB Model
    # ----------------------------------------------------
    print("\n--- Test 9: WorkflowInDB Model ---")
    try:
        in_db = WorkflowInDB(
            id="wf-001",
            name="In-DB Workflow",
            status=WorkflowStatus.COMPLETED,
            steps=[WorkflowStep(step_id="step-0", name="Initial", order=0)],
        )
        assert_test(in_db.id == "wf-001", "WorkflowInDB: id matches")
        assert_test(in_db.status == WorkflowStatus.COMPLETED, "WorkflowInDB: Status is 'completed'")
        assert_test(in_db.created_at is not None, "WorkflowInDB: created_at timestamp generated")
        assert_test(in_db.updated_at is not None, "WorkflowInDB: updated_at timestamp generated")
    except Exception as e:
        assert_test(False, "WorkflowInDB Validation", str(e))

    # ----------------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------------
    print("\n" + "=" * 65)
    print(f"TEST SUMMARY: {total_passed} Passed, {total_failed} Failed")
    print("=" * 65)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
