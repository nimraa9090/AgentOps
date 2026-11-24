"""
Verification script for Phase 2.1 — Step 2: Agent Repository & Database Indexing.
Tests:
- Index initialization & idempotency
- Create agent
- Duplicate name rejection
- Read agent by ID & safe invalid ID handling
- Update agent with partial fields
- Pagination & status filtering
- Delete agent & record cleanup
"""

import sys
import logging
from bson import ObjectId

from app.database import get_database, close_database_connection
from app.models.agent import AgentCreate, AgentUpdate, AgentStatus
from app.repositories.agent_repository import (
    AgentRepository,
    DuplicateAgentNameError,
    init_agent_indexes,
)

# Suppress verbose pymongo logs during test output
logging.basicConfig(level=logging.WARNING)

def run_tests():
    print("=" * 60)
    print("RUNNING PHASE 2.1 STEP 2 REPOSITORY & INDEX VERIFICATION")
    print("=" * 60)

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

    test_agent_name = "Test-Subsea-Probe-Temp"
    test_agent_id = None

    try:
        repo = AgentRepository(db)

        # ----------------------------------------------------
        # 1. TEST INDEX INITIALIZATION & IDEMPOTENCY
        # ----------------------------------------------------
        print("\n--- Test 1: Index Initialization & Idempotency ---")
        indexes_first_run = init_agent_indexes(db)
        print(f" Indexes created/verified: {indexes_first_run}")
        assert_test(
            "idx_agents_name_unique" in indexes_first_run,
            "Index: idx_agents_name_unique created",
        )
        assert_test(
            "idx_agents_status" in indexes_first_run,
            "Index: idx_agents_status created",
        )
        assert_test(
            "idx_agents_created_at" in indexes_first_run,
            "Index: idx_agents_created_at created",
        )

        # Idempotency check: run again
        indexes_second_run = init_agent_indexes(db)
        assert_test(
            indexes_first_run == indexes_second_run,
            "Index Idempotency: Second run produces identical indexes without error",
        )

        # Ensure any leftover test record from prior runs is purged
        repo.collection.delete_many({"name": test_agent_name})

        # ----------------------------------------------------
        # 2. TEST CREATE AGENT
        # ----------------------------------------------------
        print("\n--- Test 2: Create Agent Operation ---")
        agent_in = AgentCreate(
            name=test_agent_name,
            role="Subsea Telemetry Probe",
            model="GPT-4o mini",
            operationalDepthMeters=3800,
            temperature=0.4,
            currentTask="Measuring abyssal thermocline gradient",
        )
        created = repo.create_agent(agent_in)
        test_agent_id = created.id

        assert_test(created.id is not None, "Create: Returned document has an id")
        assert_test(ObjectId.is_valid(created.id), "Create: ID is a valid ObjectId hex string")
        assert_test(created.name == test_agent_name, "Create: Agent name matches input")
        assert_test(created.codenamed_depth == "Bathypelagic (3800m)", "Create: Codenamed depth auto-computed")
        assert_test(created.memory_usage_mb == 0.0, "Create: Memory usage defaults to 0.0")
        assert_test(created.success_rate_percent == 100.0, "Create: Success rate defaults to 100.0")

        # ----------------------------------------------------
        # 3. TEST UNIQUE INDEX (DUPLICATE NAME REJECTION)
        # ----------------------------------------------------
        print("\n--- Test 3: Unique Name Constraint ---")
        try:
            duplicate_agent = AgentCreate(
                name=test_agent_name,
                role="Another Probe",
                model="Claude 3.5 Haiku",
            )
            repo.create_agent(duplicate_agent)
            assert_test(False, "Duplicate Name: Should have raised DuplicateAgentNameError")
        except DuplicateAgentNameError:
            assert_test(True, "Duplicate Name: DuplicateAgentNameError raised successfully")

        # ----------------------------------------------------
        # 4. TEST READ AGENT (get_agent_by_id)
        # ----------------------------------------------------
        print("\n--- Test 4: Read Agent By ID ---")
        fetched = repo.get_agent_by_id(test_agent_id)
        assert_test(fetched is not None, "Read: Document successfully retrieved by ID")
        assert_test(fetched.id == test_agent_id, "Read: ID matches created record")
        assert_test(fetched.name == test_agent_name, "Read: Name matches created record")

        # Non-existent valid ObjectId
        missing = repo.get_agent_by_id("000000000000000000000000")
        assert_test(missing is None, "Read: Non-existent ObjectId returns None safely")

        # Malformed / invalid string ID
        invalid_query = repo.get_agent_by_id("not-an-object-id-12345")
        assert_test(invalid_query is None, "Read: Malformed string ID returns None safely")

        # ----------------------------------------------------
        # 5. TEST UPDATE AGENT (update_agent)
        # ----------------------------------------------------
        print("\n--- Test 5: Update Agent Operation ---")
        update_payload = AgentUpdate(
            status=AgentStatus.COMPUTING,
            currentTask="Analyzing acoustic bathymetry ping",
            memoryUsageMb=342.5,
        )
        updated = repo.update_agent(test_agent_id, update_payload)
        assert_test(updated is not None, "Update: Updated document returned")
        assert_test(updated.status == AgentStatus.COMPUTING, "Update: Status changed to 'computing'")
        assert_test(updated.current_task == "Analyzing acoustic bathymetry ping", "Update: Task updated")
        assert_test(updated.memory_usage_mb == 342.5, "Update: Memory updated to 342.5 MB")
        assert_test(updated.name == test_agent_name, "Update: Unmodified fields preserved")

        # ----------------------------------------------------
        # 6. TEST PAGINATION & FILTERING (get_all_agents)
        # ----------------------------------------------------
        print("\n--- Test 6: Pagination & Status Filtering ---")
        agents_page_1, total = repo.get_all_agents(skip=0, limit=10)
        assert_test(total >= 1, f"Pagination: Total documents count >= 1 (got {total})")
        assert_test(any(a.id == test_agent_id for a in agents_page_1), "Pagination: Test agent present in page 1")

        # Filter by status = computing
        computing_agents, comp_total = repo.get_all_agents(skip=0, limit=10, status=AgentStatus.COMPUTING)
        assert_test(any(a.id == test_agent_id for a in computing_agents), "Filter: Found test agent when filtering by 'computing'")

        # Filter by status = degraded (should NOT match our computing test agent)
        degraded_agents, deg_total = repo.get_all_agents(skip=0, limit=10, status=AgentStatus.DEGRADED)
        assert_test(not any(a.id == test_agent_id for a in degraded_agents), "Filter: Test agent absent when filtering by 'degraded'")

        # High skip beyond results
        empty_page, _ = repo.get_all_agents(skip=10000, limit=10)
        assert_test(len(empty_page) == 0, "Pagination: Large skip offset returns empty list")

        # ----------------------------------------------------
        # 7. TEST DELETE AGENT & CLEANUP
        # ----------------------------------------------------
        print("\n--- Test 7: Delete Agent Operation & Cleanup ---")
        delete_success = repo.delete_agent(test_agent_id)
        assert_test(delete_success is True, "Delete: Agent successfully deleted")

        # Verify record no longer exists
        post_delete_fetch = repo.get_agent_by_id(test_agent_id)
        assert_test(post_delete_fetch is None, "Delete: Querying deleted ID returns None")

        # Deleting again should return False
        delete_again = repo.delete_agent(test_agent_id)
        assert_test(delete_again is False, "Delete: Deleting already removed record returns False")

    finally:
        # Guarantee cleanup in case any test asserted early
        if test_agent_id:
            repo.collection.delete_many({"name": test_agent_name})
            print(f"\n[CLEANUP] Purged any remaining test records with name '{test_agent_name}'.")

        close_database_connection()

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
