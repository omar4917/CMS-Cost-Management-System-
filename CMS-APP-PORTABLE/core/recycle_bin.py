"""
Recycle Bin helpers.

We store deleted rows as JSON in the `recycle_bin` table, then hard-delete them
from their source tables. This enables restores and auditability without
requiring soft-delete columns everywhere.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from core.database import get_connection, get_table_columns


def _json_default(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        # Preserve exact value; MySQL DECIMAL accepts strings.
        return str(value)
    return str(value)


def _to_json(payload: Any) -> str:
    return json.dumps(payload, default=_json_default, ensure_ascii=True)


def recycle_and_delete(
    table_name: str,
    entity_id: int,
    *,
    pk_column: str = "id",
    deleted_by: int | None = None,
    reason: str | None = None,
) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM `{table_name}` WHERE `{pk_column}`=%s LIMIT 1", (entity_id,))
        row = cursor.fetchone()
        if not row:
            return False

        cursor.execute(
            "INSERT INTO `recycle_bin` (`entity_table`, `entity_id`, `payload`, `reason`, `deleted_by`) "
            "VALUES (%s, %s, %s, %s, %s)",
            (table_name, entity_id, _to_json(row), reason, deleted_by),
        )
        cursor.execute(f"DELETE FROM `{table_name}` WHERE `{pk_column}`=%s", (entity_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def recycle_and_delete_many(
    table_name: str,
    entity_ids: Iterable[int],
    *,
    pk_column: str = "id",
    deleted_by: int | None = None,
    reason: str | None = None,
    chunk_size: int = 500,
) -> int:
    ids = [int(x) for x in entity_ids if x is not None]
    if not ids:
        return 0

    total_deleted = 0
    for offset in range(0, len(ids), chunk_size):
        batch = ids[offset : offset + chunk_size]
        placeholders = ",".join(["%s"] * len(batch))

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"SELECT * FROM `{table_name}` WHERE `{pk_column}` IN ({placeholders})",
                tuple(batch),
            )
            rows = cursor.fetchall() or []
            if not rows:
                conn.commit()
                continue

            payload_rows = [
                (table_name, int(r.get(pk_column) if isinstance(r, dict) else r[0]), _to_json(r), reason, deleted_by)
                for r in rows
            ]
            cursor.executemany(
                "INSERT INTO `recycle_bin` (`entity_table`, `entity_id`, `payload`, `reason`, `deleted_by`) "
                "VALUES (%s, %s, %s, %s, %s)",
                payload_rows,
            )
            cursor.execute(
                f"DELETE FROM `{table_name}` WHERE `{pk_column}` IN ({placeholders})",
                tuple(batch),
            )
            total_deleted += cursor.rowcount or 0
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    return total_deleted


def restore_recycle_entry(recycle_id: int, *, restored_by: int | None = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM `recycle_bin` WHERE `id`=%s LIMIT 1", (recycle_id,))
        entry = cursor.fetchone()
        if not entry:
            raise ValueError("Recycle entry not found.")

        table_name = entry.get("entity_table") if isinstance(entry, dict) else entry[1]
        payload_text = entry.get("payload") if isinstance(entry, dict) else entry[3]
        payload = json.loads(payload_text or "{}")
        if not isinstance(payload, dict):
            raise ValueError("Recycle payload is not a JSON object.")

        columns = get_table_columns(table_name)
        insert_data = {k: v for k, v in payload.items() if k in columns}
        if not insert_data:
            raise ValueError(f"Cannot restore: no matching columns for table '{table_name}'.")

        def _insert(row_data: dict) -> int:
            cols = list(row_data.keys())
            placeholders = ", ".join(["%s"] * len(cols))
            col_sql = ", ".join(f"`{c}`" for c in cols)
            cursor.execute(
                f"INSERT INTO `{table_name}` ({col_sql}) VALUES ({placeholders})",
                tuple(row_data[c] for c in cols),
            )
            return int(cursor.lastrowid or 0)

        def _is_fk_error(exc: Exception) -> bool:
            try:
                code = int(getattr(exc, "args", [None])[0])
            except Exception:
                code = None
            if code == 1452:
                return True
            return "foreign key constraint fails" in str(exc).lower()

        def _relax_foreign_keys(row_data: dict) -> dict:
            relaxed = dict(row_data)
            for key, value in list(relaxed.items()):
                if not str(key).endswith("_id"):
                    continue
                if value is None:
                    continue
                if str(value).strip() in {"", "0"}:
                    continue
                # If a referenced parent row is missing, restore anyway and let the user re-link later.
                relaxed[key] = None
            return relaxed

        restored_id = 0
        attempts = [insert_data]
        if "id" in insert_data:
            data_no_id = dict(insert_data)
            data_no_id.pop("id", None)
            attempts.append(data_no_id)
        attempts.append(_relax_foreign_keys(attempts[-1]))

        last_exc: Exception | None = None
        for data in attempts:
            try:
                restored_id = _insert(data)
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
                if _is_fk_error(exc):
                    continue
                # For non-FK errors, move to the next attempt (e.g. ID conflict), otherwise raise.
                continue

        if restored_id <= 0:
            raise last_exc or RuntimeError("Restore failed.")

        cursor.execute(
            "UPDATE `recycle_bin` SET `restored_at`=NOW(), `restored_by`=%s WHERE `id`=%s",
            (restored_by, recycle_id),
        )
        conn.commit()
        return restored_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def purge_recycle_entries(recycle_ids: Iterable[int]) -> int:
    ids = [int(x) for x in recycle_ids if x is not None]
    if not ids:
        return 0
    placeholders = ",".join(["%s"] * len(ids))

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM `recycle_bin` WHERE `id` IN ({placeholders})", tuple(ids))
        conn.commit()
        return cursor.rowcount or 0
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
