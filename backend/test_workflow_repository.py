"""
Verification test suite for Phase 2.2 — Step 2: Workflow Repository & Database Indexing.
Tests:
- Index creation & idempotency
- Create workflow with sequential and parallel steps
- Duplicate name rejection
- Read workflow by ID & safe invalid ID handling
- Update workflow with partial fields & duplicate name prevention
- Pagination & status filtering
- Delete workflow & complete record cleanup
"""

import sys
import logging
from bson import ObjectId

from app.database import get_database, close_database_connection
from app.models.workflow import (
    WorkflowCreate,
    WorkflowStep,
    WorkflowStatus,
    WorkflowUpdate,
)
from app.repositories.workflow_repository import (
    WorkflowRepository,
    DuplicateWorkflowNameError,
    init_workflow_indexes,
)

# Suppress verbose pymongo logs during test output
logging.basicConfig(level=logging.WARNING)


def run_tests():
    print("=" * 65)
    print("RUNNING PHASE 2.2 STEP 2: WORKFLOW REPOSITORY & INDEX TESTS")
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

    test_wf_name_1 = "Test-Seafloor-Mapping-Temp-1"
    test_wf_name_2 = "Test-Acoustic-Relay-Temp-2"
    wf_1_id = None
    wf_2_id = None

    try:
        repo = WorkflowRepository(db)

        # ----------------------------------------------------
        # 1. TEST INDEX INITIALIZATION & IDEMPOTENCY
        # ----------------------------------------------------
        print("\n--- Test 1: Index Initialization & Idempotency ---")
        indexes_run_1 = init_workflow_indexes(db)
        print(f" Indexes created/verified: {indexes_run_1}")
        assert_test(
            "idx_workflows_name_unique" in indexes_run_1,
            "Index: idx_workflows_name_unique created",
        )
        assert_test(
            "idx_workflows_status" in indexes_run_1,
            "Index: idx_workflows_status created",
        )
        assert_test(
            "idx_workflows_created_at" in indexes_run_1,
            "Index: idx_workflows_created_at created",
        )

        # Idempotency check: running a second time should not fail or duplicate
        indexes_run_2 = init_workflow_indexes(db)
        assert_test(
            indexes_run_1 == indexes_run_2,
            "Index Idempotency: Second run produces identical indexes without error",
        )

        # Purge any leftovers from previous aborted test runs
        repo.collection.delete_many({"name": {"$in": [test_wf_name_1, test_wf_name_2]}})

        # ----------------------------------------------------
        # 2. TEST CREATE WORKFLOW (Sequential & Parallel Steps)
        # ----------------------------------------------------
        print("\n--- Test 2: Create Workflow Operation ---")
        # Notice: step-1a and step-1b share order=1, representing parallel execution
        steps_input = [
            WorkflowStep(
                stepId="step-0",
                name="Sonar Calibration",
                order=0,
                config={"frequencyKhz": 12.0},
            ),
            WorkflowStep(
                stepId="step-1a",
                name="Bathymetric Grid Ping",
                order=1,
            ),
            WorkflowStep(
                stepId="step-1b",
                name="Hydrothermal Vent Sensor Ping",
                order=1,  # Identical order index for concurrent execution tier
            ),
        ]

        wf_in = WorkflowCreate(
            name=test_wf_name_1,
            description="Deep trench acoustic and thermal survey",
            status=WorkflowStatus.DRAFT,
            steps=steps_input,
        )
        created = repo.create_workflow(wf_in)
        wf_1_id = created.id

        assert_test(created.id is not None, "Create: Returned document has an id")
        assert_test(ObjectId.is_valid(created.id), "Create: ID is a valid ObjectId hex string")
        assert_test(created.name == test_wf_name_1, "Create: Workflow name matches input")
        assert_test(created.status == WorkflowStatus.DRAFT, "Create: Status is 'draft'")
        assert_test(len(created.steps) == 3, "Create: 3 steps stored correctly")
        assert_test(created.steps[1].order == 1 and created.steps[2].order == 1, "Create: Parallel steps with order=1 preserved")
        assert_test(created.created_at is not None, "Create: created_at timestamp generated")
        assert_test(created.updated_at is not None, "Create: updated_at timestamp generated")

        # Create second workflow for pagination and conflict tests
        wf_in_2 = WorkflowCreate(
            name=test_wf_name_2,
            description="Autonomous buoy communication relay",
            status=WorkflowStatus.PAUSED,
        )
        created_2 = repo.create_workflow(wf_in_2)
        wf_2_id = created_2.id
        assert_test(created_2.id is not None, "Create: Second workflow created successfully")

        # ----------------------------------------------------
        # 3. TEST UNIQUE NAME CONSTRAINT (DUPLICATE NAME REJECTION)
        # ----------------------------------------------------
        print("\n--- Test 3: Unique Name Constraint ---")
        try:
            duplicate_wf = WorkflowCreate(
                name=test_wf_name_1,
                description="Duplicate attempt",
            )
            repo.create_workflow(duplicate_wf)
            assert_test(False, "Duplicate Name: Should have raised DuplicateWorkflowNameError")
        except DuplicateWorkflowNameError:
            assert_test(True, "Duplicate Name: DuplicateWorkflowNameError raised successfully")

        # ----------------------------------------------------
        # 4. TEST READ WORKFLOW (get_workflow_by_id)
        # ----------------------------------------------------
        print("\n--- Test 4: Read Workflow By ID ---")
        fetched = repo.get_workflow_by_id(wf_1_id)
        assert_test(fetched is not None, "Read: Document successfully retrieved by ID")
        assert_test(fetched.id == wf_1_id, "Read: ID matches created record")
        assert_test(fetched.name == test_wf_name_1, "Read: Name matches created record")
        assert_test(len(fetched.steps) == 3, "Read: All 3 steps retrieved")

        # Non-existent valid ObjectId
        missing = repo.get_workflow_by_id("000000000000000000000000")
        assert_test(missing is None, "Read: Non-existent ObjectId returns None safely")

        # Malformed / invalid string ID
        invalid_query = repo.get_workflow_by_id("invalid-id-xyz")
        assert_test(invalid_query is None, "Read: Malformed string ID returns None safely")

        # ----------------------------------------------------
        # 5. TEST UPDATE WORKFLOW (update_workflow)
        # ----------------------------------------------------
        print("\n--- Test 5: Update Workflow Operation ---")
        update_payload = WorkflowUpdate(
            status=WorkflowStatus.ACTIVE,
            description="Activated abyssal survey mission",
        )
        updated = repo.update_workflow(wf_1_id, update_payload)
        assert_test(updated is not None, "Update: Updated document returned")
        assert_test(updated.status == WorkflowStatus.ACTIVE, "Update: Status changed to 'active'")
        assert_test(updated.description == "Activated abyssal survey mission", "Update: Description updated")
        assert_test(updated.name == test_wf_name_1, "Update: Unmodified name preserved")
        assert_test(len(updated.steps) == 3, "Update: Steps preserved when unset in update")

        # Conflict on renaming to existing workflow name
        try:
            conflict_update = WorkflowUpdate(name=test_wf_name_2)
            repo.update_workflow(wf_1_id, conflict_update)
            assert_test(False, "Update Conflict: Should raise DuplicateWorkflowNameError")
        except DuplicateWorkflowNameError:
            assert_test(True, "Update Conflict: DuplicateWorkflowNameError raised on name collision")

        # Updating non-existent workflow
        non_existent_update = repo.update_workflow("000000000000000000000000", WorkflowUpdate(status=WorkflowStatus.COMPLETED))
        assert_test(non_existent_update is None, "Update: Updating non-existent workflow returns None")

        # ----------------------------------------------------
        # 6. TEST PAGINATION & FILTERING (get_all_workflows)
        # ----------------------------------------------------
        print("\n--- Test 6: Pagination & Status Filtering ---")
        page_1, total = repo.get_all_workflows(skip=0, limit=1)
        assert_test(total >= 2, f"Pagination: Total documents count >= 2 (got {total})")
        assert_test(len(page_1) == 1, "Pagination: Limit=1 returns exactly 1 item")

        # Filter by status = active (wf_1 was updated to active)
        active_wfs, active_total = repo.get_all_workflows(skip=0, limit=10, status=WorkflowStatus.ACTIVE)
        assert_test(any(w.id == wf_1_id for w in active_wfs), "Filter: Found wf_1 when filtering by status='active'")

        # Filter by status = failed (neither test workflow is failed)
        failed_wfs, _ = repo.get_all_workflows(skip=0, limit=10, status=WorkflowStatus.FAILED)
        assert_test(not any(w.id in [wf_1_id, wf_2_id] for w in failed_wfs), "Filter: Test workflows absent in status='failed'")

        # High skip beyond results
        empty_page, _ = repo.get_all_workflows(skip=10000, limit=10)
        assert_test(len(empty_page) == 0, "Pagination: Large skip offset returns empty list")

        # ----------------------------------------------------
        # 7. TEST DELETE WORKFLOW & CLEANUP
        # ----------------------------------------------------
        print("\n--- Test 7: Delete Workflow Operation & Cleanup ---")
        deleted_1 = repo.delete_workflow(wf_1_id)
        assert_test(deleted_1 is True, "Delete: Workflow 1 successfully deleted")

        # Verify record no longer exists
        post_delete_fetch = repo.get_workflow_by_id(wf_1_id)
        assert_test(post_delete_fetch is None, "Delete: Querying deleted ID returns None")

        # Deleting again should return False
        deleted_again = repo.delete_workflow(wf_1_id)
        assert_test(deleted_again is False, "Delete: Deleting already removed record returns False")

        # Delete workflow 2
        deleted_2 = repo.delete_workflow(wf_2_id)
        assert_test(deleted_2 is True, "Delete: Workflow 2 successfully deleted")

        # Final purge & confirmation
        repo.collection.delete_many({"name": {"$in": [test_wf_name_1, test_wf_name_2]}})
        remaining = repo.collection.count_documents({"name": {"$in": [test_wf_name_1, test_wf_name_2]}})
        assert_test(remaining == 0, "Cleanup: Zero lingering test records in database")

    finally:
        # Guarantee cleanup in case any assertion threw early
        if wf_1_id or wf_2_id:
            repo.collection.delete_many({"name": {"$in": [test_wf_name_1, test_wf_name_2]}})
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
