"""
Test suite for Phase 2.3 — Step 1: Execution Models & Schemas.
Tests valid creation, defaults, optional fields, invalid workflow IDs, negative order,
status validation, timestamp sequence validation, updates, and MongoDB ObjectId serialization.
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pydantic import ValidationError

from app.models import (
    ExecutionBase,
    ExecutionCreate,
    ExecutionInDB,
    ExecutionResponse,
    ExecutionStatus,
    ExecutionStep,
    ExecutionUpdate,
)


def run_tests():
    print("=" * 65)
    print("RUNNING PHASE 2.3 STEP 1: EXECUTION MODEL VERIFICATION TESTS")
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
    # TEST 1: ExecutionCreate Valid & Defaults
    # ----------------------------------------------------
    print("\n--- Test 1: ExecutionCreate Valid & Defaults ---")
    try:
        exec_create = ExecutionCreate(workflowId="wf-trench-001")
        assert_test(exec_create.workflow_id == "wf-trench-001", "ExecutionCreate: workflow_id matches via alias")
        assert_test(exec_create.parameters is None, "ExecutionCreate: parameters defaults to None")

        # With parameters
        exec_create_with_params = ExecutionCreate(
            workflow_id="wf-trench-002",
            parameters={"depthTargetMeters": 10500, "sensorMode": "passive"},
        )
        assert_test(exec_create_with_params.parameters == {"depthTargetMeters": 10500, "sensorMode": "passive"}, "ExecutionCreate: parameters populated")
    except Exception as e:
        assert_test(False, "ExecutionCreate Valid & Defaults", str(e))

    # ----------------------------------------------------
    # TEST 2: ExecutionStep Valid & Defaults
    # ----------------------------------------------------
    print("\n--- Test 2: ExecutionStep Valid & Defaults ---")
    try:
        now = datetime.now(timezone.utc)
        step = ExecutionStep(
            stepId="step-01",
            name="Initialize Sonar Sweep",
            order=0,
        )
        assert_test(step.step_id == "step-01", "ExecutionStep: step_id matches via alias")
        assert_test(step.name == "Initialize Sonar Sweep", "ExecutionStep: name matches")
        assert_test(step.order == 0, "ExecutionStep: order=0 accepted")
        assert_test(step.status == ExecutionStatus.PENDING, "ExecutionStep: status defaults to 'pending'")
        assert_test(step.agent_id is None, "ExecutionStep: agent_id defaults to None")
        assert_test(step.started_at is None, "ExecutionStep: started_at defaults to None")
        assert_test(step.completed_at is None, "ExecutionStep: completed_at defaults to None")
        assert_test(step.input_data is None, "ExecutionStep: input_data defaults to None")
        assert_test(step.output_data is None, "ExecutionStep: output_data defaults to None")
        assert_test(step.error is None, "ExecutionStep: error defaults to None")

        # Fully populated step
        finished_step = ExecutionStep(
            stepId="step-02",
            name="Acoustic Ranging Ping",
            agentId="agt-kraken-01",
            order=1,
            status=ExecutionStatus.COMPLETED,
            startedAt=now,
            completedAt=now + timedelta(seconds=12),
            inputData={"pingStrengthWatts": 250},
            outputData={"echoDetected": True, "depthMeters": 9840},
        )
        assert_test(finished_step.status == ExecutionStatus.COMPLETED, "ExecutionStep: status 'completed'")
        assert_test(finished_step.agent_id == "agt-kraken-01", "ExecutionStep: agent_id matches via alias")
        assert_test(finished_step.output_data["depthMeters"] == 9840, "ExecutionStep: output_data preserved")
    except Exception as e:
        assert_test(False, "ExecutionStep Valid & Defaults", str(e))

    # ----------------------------------------------------
    # TEST 3: Validation Constraints (IDs, Names, Orders)
    # ----------------------------------------------------
    print("\n--- Test 3: Validation Constraints ---")
    # Empty workflow_id
    try:
        ExecutionCreate(workflow_id="")
        assert_test(False, "ExecutionCreate: empty workflow_id should fail")
    except ValidationError:
        assert_test(True, "ExecutionCreate: empty workflow_id rejected")

    # Whitespace workflow_id
    try:
        ExecutionCreate(workflow_id="   ")
        assert_test(False, "ExecutionCreate: whitespace workflow_id should fail")
    except ValidationError:
        assert_test(True, "ExecutionCreate: whitespace workflow_id rejected")

    # Negative step order
    try:
        ExecutionStep(step_id="s1", name="Step A", order=-1)
        assert_test(False, "ExecutionStep: order=-1 should fail")
    except ValidationError:
        assert_test(True, "ExecutionStep: order=-1 rejected")

    # Empty step_id
    try:
        ExecutionStep(step_id="", name="Step A", order=0)
        assert_test(False, "ExecutionStep: empty step_id should fail")
    except ValidationError:
        assert_test(True, "ExecutionStep: empty step_id rejected")

    # Empty step name
    try:
        ExecutionStep(step_id="s1", name="", order=0)
        assert_test(False, "ExecutionStep: empty step name should fail")
    except ValidationError:
        assert_test(True, "ExecutionStep: empty step name rejected")

    # ----------------------------------------------------
    # TEST 4: ExecutionStatus Enum Validation
    # ----------------------------------------------------
    print("\n--- Test 4: ExecutionStatus Enum Validation ---")
    required_statuses = ["pending", "running", "completed", "failed", "cancelled"]
    for s in required_statuses:
        status_enum = ExecutionStatus(s)
        assert_test(status_enum.value == s, f"ExecutionStatus: '{s}' is a valid enum value")

    # Invalid status strings
    for bad_status in ["paused", "draft", "unknown", ""]:
        try:
            ExecutionBase(workflow_id="wf-001", status=bad_status)
            assert_test(False, f"ExecutionStatus: '{bad_status}' should fail")
        except ValidationError:
            assert_test(True, f"ExecutionStatus: '{bad_status}' rejected by validator")

    # ----------------------------------------------------
    # TEST 5: Timestamp Sequence Validation
    # ----------------------------------------------------
    print("\n--- Test 5: Timestamp Sequence Validation ---")
    start_time = datetime.now(timezone.utc)
    early_completion = start_time - timedelta(minutes=5)

    # Step: completed_at earlier than started_at
    try:
        ExecutionStep(
            step_id="step-time",
            name="Time Check",
            order=0,
            started_at=start_time,
            completed_at=early_completion,
        )
        assert_test(False, "ExecutionStep: completed_at < started_at should fail")
    except ValidationError:
        assert_test(True, "ExecutionStep: completed_at < started_at rejected")

    # ExecutionBase: completed_at earlier than started_at
    try:
        ExecutionBase(
            workflow_id="wf-001",
            started_at=start_time,
            completed_at=early_completion,
        )
        assert_test(False, "ExecutionBase: completed_at < started_at should fail")
    except ValidationError:
        assert_test(True, "ExecutionBase: completed_at < started_at rejected")

    # Valid chronological timestamps
    try:
        valid_exec = ExecutionBase(
            workflow_id="wf-001",
            started_at=start_time,
            completed_at=start_time + timedelta(seconds=45),
        )
        assert_test(valid_exec.completed_at > valid_exec.started_at, "ExecutionBase: valid timestamps accepted")
    except Exception as e:
        assert_test(False, "ExecutionBase: valid timestamps", str(e))

    # ----------------------------------------------------
    # TEST 6: ExecutionUpdate (Partial State Updates)
    # ----------------------------------------------------
    print("\n--- Test 6: ExecutionUpdate (Partial Updates) ---")
    try:
        # Transition to running
        update_to_running = ExecutionUpdate(
            status=ExecutionStatus.RUNNING,
            startedAt=start_time,
        )
        assert_test(update_to_running.status == ExecutionStatus.RUNNING, "ExecutionUpdate: status updated to 'running'")
        assert_test(update_to_running.started_at == start_time, "ExecutionUpdate: started_at updated")
        assert_test(update_to_running.completed_at is None, "ExecutionUpdate: unset completed_at is None")
        assert_test(update_to_running.error is None, "ExecutionUpdate: unset error is None")

        # Transition to failed with error
        update_failed = ExecutionUpdate(
            status=ExecutionStatus.FAILED,
            completedAt=start_time + timedelta(seconds=10),
            error="Subsea communications packet timed out at 10,920m",
        )
        assert_test(update_failed.status == ExecutionStatus.FAILED, "ExecutionUpdate: status updated to 'failed'")
        assert_test(update_failed.error == "Subsea communications packet timed out at 10,920m", "ExecutionUpdate: error recorded")
    except Exception as e:
        assert_test(False, "ExecutionUpdate Validation", str(e))

    # ----------------------------------------------------
    # TEST 7: Serialization & MongoDB ObjectId Mapping
    # ----------------------------------------------------
    print("\n--- Test 7: Serialization & MongoDB ObjectId Mapping ---")
    fake_mongo_id = ObjectId("654a1b2c3d4e5f6a7b8c9d0e")
    now_ts = datetime.now(timezone.utc)

    raw_mongo_doc = {
        "_id": fake_mongo_id,
        "workflowId": "654a1b2c3d4e5f6a7b8c9d01",
        "status": "completed",
        "startedAt": now_ts,
        "completedAt": now_ts + timedelta(minutes=2),
        "steps": [
            {
                "stepId": "s-1",
                "name": "Bathymetric Ping",
                "agentId": "agt-001",
                "order": 0,
                "status": "completed",
                "startedAt": now_ts,
                "completedAt": now_ts + timedelta(minutes=2),
                "outputData": {"depth": 10920},
            }
        ],
        "parameters": {"environment": "abyssal"},
        "created_at": now_ts,
        "updated_at": now_ts + timedelta(minutes=2),
    }

    try:
        response = ExecutionResponse.model_validate(raw_mongo_doc)
        assert_test(response.id == str(fake_mongo_id), "ExecutionResponse: _id mapped to string 'id'")
        assert_test(isinstance(response.id, str), "ExecutionResponse: 'id' is Python str instance")
        assert_test(response.workflow_id == "654a1b2c3d4e5f6a7b8c9d01", "ExecutionResponse: workflow_id matches")
        assert_test(response.status == ExecutionStatus.COMPLETED, "ExecutionResponse: status is 'completed'")
        assert_test(len(response.steps) == 1, "ExecutionResponse: steps preserved")
        assert_test(response.steps[0].output_data == {"depth": 10920}, "ExecutionResponse: step outputData preserved")

        # Dict serialization with camelCase aliases
        dumped_dict = response.model_dump(by_alias=True)
        assert_test("id" in dumped_dict, "Serialized Dict: Contains 'id' key")
        assert_test("_id" not in dumped_dict, "Serialized Dict: Does NOT expose raw '_id'")
        assert_test(dumped_dict["id"] == "654a1b2c3d4e5f6a7b8c9d0e", "Serialized Dict: ID matches ObjectId string")
        assert_test("workflowId" in dumped_dict, "Serialized Dict: workflowId serialized as camelCase")
        assert_test("startedAt" in dumped_dict, "Serialized Dict: startedAt serialized as camelCase")
        assert_test("completedAt" in dumped_dict, "Serialized Dict: completedAt serialized as camelCase")
        assert_test("stepId" in dumped_dict["steps"][0], "Serialized Dict: stepId serialized as camelCase")

        # JSON string serialization
        dumped_json = response.model_dump_json(by_alias=True)
        parsed_json = json.loads(dumped_json)
        assert_test(parsed_json["id"] == "654a1b2c3d4e5f6a7b8c9d0e", "JSON Output: ID matches ObjectId string")
        assert_test(parsed_json["status"] == "completed", "JSON Output: status serialized as string")
        assert_test("_id" not in parsed_json, "JSON Output: Does NOT contain '_id'")
    except Exception as e:
        assert_test(False, "Serialization & ObjectId Mapping", str(e))

    # ----------------------------------------------------
    # TEST 8: ExecutionInDB Model
    # ----------------------------------------------------
    print("\n--- Test 8: ExecutionInDB Model ---")
    try:
        in_db = ExecutionInDB(
            id="exec-001",
            workflowId="wf-001",
            status=ExecutionStatus.PENDING,
        )
        assert_test(in_db.id == "exec-001", "ExecutionInDB: id matches")
        assert_test(in_db.workflow_id == "wf-001", "ExecutionInDB: workflow_id matches")
        assert_test(in_db.status == ExecutionStatus.PENDING, "ExecutionInDB: status is 'pending'")
        assert_test(in_db.created_at is not None, "ExecutionInDB: created_at timestamp generated")
        assert_test(in_db.updated_at is not None, "ExecutionInDB: updated_at timestamp generated")
    except Exception as e:
        assert_test(False, "ExecutionInDB Validation", str(e))

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
