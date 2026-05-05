"""
Project data access + aggregate helpers for the desktop app.
Keeps SQL and deletion logic out of view code.
"""

from __future__ import annotations

from typing import Iterable

from core.database import execute_query
from core.recycle_bin import recycle_and_delete, recycle_and_delete_many


def fetch_projects(search: str | None = None, status: str | None = None, purpose: str | None = None):
    query = "SELECT * FROM projects WHERE 1=1"
    params: list[object] = []

    if search:
        query += (
            " AND (name LIKE %s OR location LIKE %s OR description LIKE %s "
            "OR property_type LIKE %s OR property_for LIKE %s OR construction_status LIKE %s)"
        )
        like = f"%{search}%"
        params.extend([like, like, like, like, like, like])

    if status and status != "All Statuses":
        query += " AND status=%s"
        params.append(status)

    if purpose and purpose != "All Listings":
        query += " AND LOWER(COALESCE(property_for, ''))=%s"
        params.append(str(purpose).lower())

    query += " ORDER BY created_at DESC, id DESC"
    return execute_query(query, params)


def fetch_project(project_id: int):
    rows = execute_query("SELECT * FROM projects WHERE id=%s", (project_id,))
    return rows[0] if rows else None


def project_metrics(projects):
    total = len(projects or [])
    active = sum(1 for p in (projects or []) if str(p.get("status", "")).lower() == "active")
    budget = sum(float(p.get("total_budget") or 0) for p in (projects or []))
    avg_progress = 0
    if total:
        avg_progress = sum(float(p.get("progress") or 0) for p in projects) / total
    return {
        "total": total,
        "active": active,
        "budget": budget,
        "avg_progress": avg_progress,
    }


def project_snapshot(project_id: int, project_name: str | None = None):
    investments = execute_query(
        "SELECT COALESCE(SUM(amount),0) AS total FROM investments WHERE project_id=%s AND status='confirmed'",
        (project_id,),
    )[0]["total"]

    collections = execute_query(
        "SELECT COALESCE(SUM(CASE WHEN paid_amount > 0 THEN paid_amount ELSE amount END),0) AS total "
        "FROM payment_schedules WHERE project_id=%s AND status='paid'",
        (project_id,),
    )[0]["total"]

    costs = execute_query(
        """
        SELECT COALESCE(SUM(
            CASE
                WHEN cost_amount IS NOT NULL AND cost_amount <> 0 THEN cost_amount
                WHEN actual_amount IS NOT NULL AND actual_amount <> 0 THEN actual_amount
                WHEN estimated_amount IS NOT NULL AND estimated_amount <> 0 THEN estimated_amount
                ELSE 0
            END
        ), 0) AS total
        FROM cost_items
        WHERE project_id=%s
        """,
        (project_id,),
    )[0]["total"]

    if not costs and project_name:
        costs = execute_query(
            """
            SELECT COALESCE(SUM(
                CASE
                    WHEN cost_amount IS NOT NULL AND cost_amount <> 0 THEN cost_amount
                    WHEN actual_amount IS NOT NULL AND actual_amount <> 0 THEN actual_amount
                    WHEN estimated_amount IS NOT NULL AND estimated_amount <> 0 THEN estimated_amount
                    ELSE 0
                END
            ), 0) AS total
            FROM cost_items
            WHERE (project_id IS NULL OR project_id=0) AND cost_head_project=%s
            """,
            (project_name,),
        )[0]["total"]

    contractors = execute_query(
        "SELECT COALESCE(SUM(amount),0) AS total FROM contractor_payments "
        "WHERE project_id=%s AND status IN ('paid','approved','completed')",
        (project_id,),
    )[0]["total"]

    return {
        "investments": investments,
        "collections": collections,
        "costs": costs,
        "contractors": contractors,
    }


def bulk_delete_projects(project_ids: Iterable[int], *, deleted_by: int | None = None):
    ids = sorted({int(x) for x in project_ids if x is not None})
    if not ids:
        return 0

    placeholders = ",".join(["%s"] * len(ids))
    for table, column in [
        ("cost_items", "project_id"),
        ("investments", "project_id"),
        ("payment_schedules", "project_id"),
        ("contractor_payments", "project_id"),
        ("cash_transactions", "project_id"),
    ]:
        try:
            rows = execute_query(f"SELECT id FROM `{table}` WHERE `{column}` IN ({placeholders})", tuple(ids)) or []
            dep_ids = [int(r.get("id")) for r in rows if r.get("id") is not None]
            if dep_ids:
                recycle_and_delete_many(
                    table,
                    dep_ids,
                    deleted_by=deleted_by,
                    reason="Bulk delete projects",
                )
        except Exception:
            # Some deployments may not have all tables/columns.
            pass

    return recycle_and_delete_many(
        "projects",
        ids,
        deleted_by=deleted_by,
        reason="Bulk delete projects",
    )


def delete_project(project_id: int, *, deleted_by: int | None = None):
    return bulk_delete_projects([project_id], deleted_by=deleted_by)
