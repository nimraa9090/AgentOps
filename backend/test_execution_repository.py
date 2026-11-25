"""
Verification test suite for Phase 2.3 — Step 2: Execution Repository & Database Indexing.
Tests:
- Index creation & idempotency
- Create execution with initial pending state and parameters
- Retrieve execution by ID & safe invalid ID handling
- Update execution state (transitions to RUNNING and COMPLETED, adding steps, updating timestamps)
- Pagination, workflow_id filtering, and status filtering
- Delete execution & complete record cleanup
"""

import sys
import logging
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from app.database import get_database, close_database_connection
from app.models.common import now_utc
from app.models.execution import (
    ExecutionCreate,
    ExecutionResponse,
    ExecutionStatus,
    ExecutionStep,
    ExecutionUpdate,
)
from app.repositories.execution_repository import (
    ExecutionRepository,
    init_execution_indexes,
)

# Suppress verbose pymongo logs during test output
logging.basicConfig(level=logging.WARNING)


def run_tests():
    print("=" * 65)
    print("RUNNING PHASE 2.3 STEP 2: EXECUTION REPOSITORY & INDEX TESTS")
    print("=" * 65)

    db = get_database()
    if db is None:
        print("[FATAL] Could not connect to MongoDB Atlas.")
        sys.exit(1)

    print(f"Connected to database: '{db.name}'")
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

    test_wf_id_1 = "wf-exec-test-alpha"
    test_wf_id_2 = "wf-exec-test-beta"
    exec_1_id = None
    exec_2_id = None
    exec_3_id = None

    try:
        repo = ExecutionRepository(db)

        # ----------------------------------------------------
        # 1. TEST INDEX INITIALIZATION & IDEMPOTENCY
        # ----------------------------------------------------
        print("\n--- Test 1: Index Initialization & Idempotency ---")
        indexes_run_1 = init_execution_indexes(db)
        print(f" Indexes created/verified: {indexes_run_1}")
        assert_test(
            "idx_executions_workflow_id" in indexes_run_1,
            "Index: idx_executions_workflow_id created",
        )
        assert_test(
            "idx_executions_status" in indexes_run_1,
            "Index: idx_executions_status created",
        )
        assert_test(
            "idx_executions_created_at" in indexes_run_1,
            "Index: idx_executions_created_at created",
        )
        assert_test(
            "idx_executions_workflow_created_at" in indexes_run_1,
            "Compound Index: idx_executions_workflow_created_at created",
        )

        # Idempotency check: second run should not fail or duplicate
        indexes_run_2 = init_execution_indexes(db)
        assert_test(
            indexes_run_1 == indexes_run_2,
            "Index Idempotency: Second run produces identical indexes without error",
        )

        # Purge any leftovers from previous aborted test runs
        repo.collection.delete_many({"workflowId": {"$in": [test_wf_id_1, test_wf_id_2]}})

        # ----------------------------------------------------
        # 2. TEST CREATE EXECUTION
        # ----------------------------------------------------
        print("\n--- Test 2: Create Execution Operation ---")
        create_payload_1 = ExecutionCreate(
            workflowId=test_wf_id_1,
            parameters={"targetDepthMeters": 10920, "sensorPack": "abyssal-sonar"},
        )
        created_1 = repo.create_execution(create_payload_1)
        exec_1_id = created_1.id

        assert_test(created_1.id is not None, "Create: Returned document has an id")
        assert_test(ObjectId.is_valid(created_1.id), "Create: ID is a valid ObjectId hex string")
        assert_test(created_1.workflow_id == test_wf_id_1, "Create: workflow_id matches input")
        assert_test(created_1.status == ExecutionStatus.PENDING, "Create: Status initialized to 'pending'")
        assert_test(created_1.steps == [], "Create: Steps initialized to empty list")
        assert_test(created_1.started_at is None, "Create: started_at is initially None")
        assert_test(created_1.completed_at is None, "Create: completed_at is initially None")
        assert_test(created_1.parameters == {"targetDepthMeters": 10920, "sensorPack": "abyssal-sonar"}, "Create: parameters stored")
        assert_test(created_1.created_at is not None, "Create: created_at timestamp generated")
        assert_test(created_1.updated_at is not None, "Create: updated_at timestamp generated")

        # Create second execution under workflow 2
        create_payload_2 = ExecutionCreate(
            workflow_id=test_wf_id_2,
            parameters={"telemetryRelay": True},
        )
        created_2 = repo.create_execution(create_payload_2)
        exec_2_id = created_2.id
        assert_test(created_2.id is not None, "Create: Second execution created successfully")

        # Create third execution under workflow 1
        create_payload_3 = ExecutionCreate(
            workflow_id=test_wf_id_1,
            parameters={"passNumber": 2},
        )
        created_3 = repo.create_execution(create_payload_3)
        exec_3_id = created_3.id
        assert_test(created_3.id is not None, "Create: Third execution created successfully")

        # ----------------------------------------------------
        # 3. TEST READ EXECUTION (get_execution_by_id)
        # ----------------------------------------------------
        print("\n--- Test 3: Read Execution By ID ---")
        fetched = repo.get_execution_by_id(exec_1_id)
        assert_test(fetched is not None, "Read: Document successfully retrieved by ID")
        assert_test(fetched.id == exec_1_id, "Read: ID matches created record")
        assert_test(fetched.workflow_id == test_wf_id_1, "Read: workflow_id matches created record")

        # Non-existent valid ObjectId
        missing = repo.get_execution_by_id("000000000000000000000000")
        assert_test(missing is None, "Read: Non-existent ObjectId returns None safely")

        # Malformed / invalid string ID
        invalid_query = repo.get_execution_by_id("invalid-id-xyz-not-an-id")
        assert_test(invalid_query is None, "Read: Malformed string ID returns None safely")

        # ----------------------------------------------------
        # 4. TEST UPDATE EXECUTION (State Transitions & Step Results)
        # ----------------------------------------------------
        print("\n--- Test 4: Update Execution Operation ---")
        start_time = now_utc()
        
        # Transition to RUNNING
        update_to_running = ExecutionUpdate(
            status=ExecutionStatus.RUNNING,
            startedAt=start_time,
        )
        updated_running = repo.update_execution(exec_1_id, update_to_running)
        assert_test(updated_running is not None, "Update: Updated document returned")
        assert_test(updated_running.status == ExecutionStatus.RUNNING, "Update: Status changed to 'running'")
        assert_test(updated_running.started_at is not None, "Update: started_at recorded")
        assert_test(updated_running.updated_at >= created_1.updated_at, "Update: updated_at advanced")

        # Record step completion and transition to COMPLETED
        step1 = ExecutionStep(
            stepId="step-sonar-01",
            name="Sonar Sweep",
            agentId="agt-kraken-01",
            order=0,
            status=ExecutionStatus.COMPLETED,
            startedAt=start_time,
            completedAt=start_time + timedelta(seconds=15),
            outputData={"depthDetectedMeters": 10920, "temperatureC": 1.8},
        )
        finish_time = start_time + timedelta(seconds=20)
        update_to_completed = ExecutionUpdate(
            status=ExecutionStatus.COMPLETED,
            completedAt=finish_time,
            steps=[step1],
        )
        updated_completed = repo.update_execution(exec_1_id, update_to_completed)
        assert_test(updated_completed.status == ExecutionStatus.COMPLETED, "Update: Status changed to 'completed'")
        assert_test(len(updated_completed.steps) == 1, "Update: Step result recorded in execution")
        assert_test(updated_completed.steps[0].output_data["depthDetectedMeters"] == 10920, "Update: Step outputData stored correctly")
        assert_test(updated_completed.completed_at is not None, "Update: completed_at recorded")

        # Updating non-existent execution
        non_existent_update = repo.update_execution("000000000000000000000000", ExecutionUpdate(status=ExecutionStatus.CANCELLED))
        assert_test(non_existent_update is None, "Update: Updating non-existent execution returns None")

        # ----------------------------------------------------
        # 5. TEST PAGINATION & FILTERING (get_all_executions)
        # ----------------------------------------------------
        print("\n--- Test 5: Pagination & Filtering ---")
        # Pagination limit=2
        page_1, total = repo.get_all_executions(skip=0, limit=2)
        assert_test(total >= 3, f"Pagination: Total documents count >= 3 (got {total})")
        assert_test(len(page_1) == 2, "Pagination: Limit=2 returns exactly 2 items")

        # Filter by workflow_id = test_wf_id_1 (2 executions created under wf 1)
        wf_1_execs, wf_1_total = repo.get_all_executions(skip=0, limit=10, workflow_id=test_wf_id_1)
        assert_test(wf_1_total == 2, f"Filter by workflowId: Exactly 2 executions match wf 1 (got {wf_1_total})")
        assert_test(all(e.workflow_id == test_wf_id_1 for e in wf_1_execs), "Filter by workflowId: All items have workflowId=test_wf_id_1")

        # Filter by workflow_id = test_wf_id_2 (1 execution created under wf 2)
        wf_2_execs, wf_2_total = repo.get_all_executions(skip=0, limit=10, workflow_id=test_wf_id_2)
        assert_test(wf_2_total == 1, f"Filter by workflowId: Exactly 1 execution matches wf 2 (got {wf_2_total})")
        assert_test(wf_2_execs[0].workflow_id == test_wf_id_2, "Filter by workflowId: Item has workflowId=test_wf_id_2")

        # Filter by status = COMPLETED (exec_1 was updated to completed)
        completed_execs, comp_total = repo.get_all_executions(skip=0, limit=10, status=ExecutionStatus.COMPLETED)
        assert_test(any(e.id == exec_1_id for e in completed_execs), "Filter by status: Completed query contains exec_1")

        # Filter by status = FAILED (none of the test executions are failed)
        failed_execs, _ = repo.get_all_executions(skip=0, limit=10, status=ExecutionStatus.FAILED)
        assert_test(not any(e.id in [exec_1_id, exec_2_id, exec_3_id] for e in failed_execs), "Filter by status: Test executions absent in status='failed'")

        # High skip offset
        empty_page, _ = repo.get_all_executions(skip=10000, limit=10)
        assert_test(len(empty_page) == 0, "Pagination: Large skip offset returns empty list")

        # ----------------------------------------------------
        # 6. TEST DELETE EXECUTION & CLEANUP
        # ----------------------------------------------------
        print("\n--- Test 6: Delete Execution Operation & Cleanup ---")
        deleted_1 = repo.delete_execution(exec_1_id)
        assert_test(deleted_1 is True, "Delete: Execution 1 successfully deleted")

        # Verify record no longer exists
        post_delete_fetch = repo.get_execution_by_id(exec_1_id)
        assert_test(post_delete_fetch is None, "Delete: Querying deleted ID returns None")

        # Deleting again should return False
        deleted_again = repo.delete_execution(exec_1_id)
        assert_test(deleted_again is False, "Delete: Deleting already removed record returns False")

        # Delete remaining test executions
        deleted_2 = repo.delete_execution(exec_2_id)
        deleted_3 = repo.delete_execution(exec_3_id)
        assert_test(deleted_2 is True and deleted_3 is True, "Delete: Remaining test executions deleted")

        # Final purge check
        repo.collection.delete_many({"workflowId": {"$in": [test_wf_id_1, test_wf_id_2]}})
        remaining = repo.collection.count_documents({"workflowId": {"$in": [test_wf_id_1, test_wf_id_2]}})
        assert_test(remaining == 0, "Cleanup: Zero lingering test records in database")

    finally:
        # Guarantee cleanup in case any assertion threw early
        if exec_1_id or exec_2_id or exec_3_id:
            repo.collection.delete_many({"workflowId": {"$in": [test_wf_id_1, test_wf_id_2]}})
            print("\n[CLEANUP] Purged any remaining test records.")

        close_database_connection()

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
