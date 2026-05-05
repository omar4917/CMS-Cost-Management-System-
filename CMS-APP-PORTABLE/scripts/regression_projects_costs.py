"""
Basic regression smoke tests for Projects + Costs.

Usage:
  python scripts/regression_projects_costs.py --db cms_db_test
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(SCRIPT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def _configure_db(db_name):
    if db_name:
        os.environ["DB_NAME"] = db_name

    import importlib

    db = importlib.import_module("core.database")
    if db_name:
        db.DB_CONFIG["database"] = db_name
        db.reset_connection_cache()
    return db


def main():
    parser = argparse.ArgumentParser(description="Regression checks for Projects + Costs.")
    parser.add_argument("--db", help="Database name to target (overrides DB_NAME).")
    parser.add_argument("--keep", action="store_true", help="Keep test rows after run.")
    args = parser.parse_args()

    db_name = args.db or os.getenv("CMS_TEST_DB") or os.getenv("DB_NAME")
    db = _configure_db(db_name)

    from core.projects_service import fetch_projects, project_snapshot

    project_id = None
    test_tag = f"REG-{uuid.uuid4().hex[:8]}"
    project_name = f"Regression Project {test_tag}"

    try:
        project_id = db.execute_query(
            """
            INSERT INTO projects (name, location, status, total_budget, progress, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (project_name, "Test Location", "active", 1000000, 10),
            fetch=False,
        )
        if not project_id:
            raise RuntimeError("Failed to insert test project.")

        cost_rows = [
            (project_id, f"Cost A {test_tag}", 1000, 0, 0),
            (project_id, f"Cost B {test_tag}", 0, 2000, 0),
            (project_id, f"Cost C {test_tag}", 0, 0, 3000),
        ]
        for project_id, label, cost_amount, actual_amount, estimated_amount in cost_rows:
            db.execute_query(
                """
                INSERT INTO cost_items (project_id, cost_detail, cost_amount, actual_amount, estimated_amount, cost_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURDATE(), NOW(), NOW())
                """,
                (project_id, label, cost_amount, actual_amount, estimated_amount),
                fetch=False,
            )

        snapshot = project_snapshot(project_id, project_name)
        expected_costs = 6000
        actual_costs = float(snapshot.get("costs") or 0)
        if abs(actual_costs - expected_costs) > 0.01:
            raise RuntimeError(f"Cost snapshot mismatch: expected {expected_costs}, got {actual_costs}.")

        matches = fetch_projects(search=test_tag)
        if not any(row.get("id") == project_id for row in matches or []):
            raise RuntimeError("Search did not return the test project.")

        print("Regression checks passed.")
        return 0
    except Exception as exc:
        print(f"Regression checks failed: {exc}")
        return 1
    finally:
        if args.keep or not project_id:
            return
        try:
            db.execute_query("DELETE FROM cost_items WHERE project_id=%s", (project_id,), fetch=False)
            db.execute_query("DELETE FROM projects WHERE id=%s", (project_id,), fetch=False)
        except Exception as exc:
            print(f"Cleanup failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
