"""
models/record.py
----------------
All database operations related to Financial Records.
"""

import uuid
from datetime import datetime
from app.database import get_connection, _close

VALID_TYPES = ("income", "expense")


def _row_to_dict(row):
    return dict(row) if row else None


def create_record(amount: float, type_: str, category: str, date: str,
                  created_by: str, notes: str = "") -> dict:
    if type_ not in VALID_TYPES:
        raise ValueError(f"type must be one of {VALID_TYPES}")
    if amount <= 0:
        raise ValueError("amount must be greater than 0")

    record_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO records (id, amount, type, category, date, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (record_id, amount, type_, category, date, notes, created_by),
        )
        conn.commit()
    finally:
        _close(conn)

    return get_record_by_id(record_id)


def get_record_by_id(record_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM records WHERE id = ? AND is_deleted = 0", (record_id,)
    ).fetchone()
    _close(conn)
    return _row_to_dict(row)


def get_records(filters: dict = None, page: int = 1, per_page: int = 20) -> dict:
    filters = filters or {}
    conditions = ["is_deleted = 0"]
    params = []

    if filters.get("type"):
        conditions.append("type = ?")
        params.append(filters["type"])
    if filters.get("category"):
        conditions.append("category LIKE ?")
        params.append(f"%{filters['category']}%")
    if filters.get("date_from"):
        conditions.append("date >= ?")
        params.append(filters["date_from"])
    if filters.get("date_to"):
        conditions.append("date <= ?")
        params.append(filters["date_to"])

    where = " AND ".join(conditions)
    offset = (page - 1) * per_page

    conn = get_connection()
    total = conn.execute(f"SELECT COUNT(*) FROM records WHERE {where}", params).fetchone()[0]
    rows  = conn.execute(
        f"SELECT * FROM records WHERE {where} ORDER BY date DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()
    _close(conn)

    return {
        "records":     [_row_to_dict(r) for r in rows],
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


def update_record(record_id: str, updates: dict) -> dict | None:
    allowed = {"amount", "type", "category", "date", "notes"}
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        raise ValueError("No valid fields to update.")

    if "type" in fields and fields["type"] not in VALID_TYPES:
        raise ValueError(f"type must be one of {VALID_TYPES}")
    if "amount" in fields and fields["amount"] <= 0:
        raise ValueError("amount must be greater than 0")

    fields["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [record_id]

    conn = get_connection()
    conn.execute(
        f"UPDATE records SET {set_clause} WHERE id = ? AND is_deleted = 0", values
    )
    conn.commit()
    _close(conn)
    return get_record_by_id(record_id)


def soft_delete_record(record_id: str) -> bool:
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE records SET is_deleted = 1 WHERE id = ? AND is_deleted = 0", (record_id,)
    )
    conn.commit()
    affected = cursor.rowcount
    _close(conn)
    return affected > 0


def get_summary() -> dict:
    conn = get_connection()

    totals = conn.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END), 0) AS total_income,
            COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS total_expenses
        FROM records WHERE is_deleted = 0
    """).fetchone()

    by_category = conn.execute("""
        SELECT category, type, SUM(amount) AS total, COUNT(*) AS count
        FROM records WHERE is_deleted = 0
        GROUP BY category, type ORDER BY total DESC
    """).fetchall()

    monthly = conn.execute("""
        SELECT strftime('%Y-%m', date) AS month,
               SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
               SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expenses
        FROM records WHERE is_deleted = 0
        GROUP BY month ORDER BY month DESC LIMIT 12
    """).fetchall()

    recent = conn.execute("""
        SELECT * FROM records WHERE is_deleted = 0
        ORDER BY created_at DESC LIMIT 10
    """).fetchall()

    _close(conn)

    income   = totals["total_income"]
    expenses = totals["total_expenses"]

    return {
        "total_income":    round(income, 2),
        "total_expenses":  round(expenses, 2),
        "net_balance":     round(income - expenses, 2),
        "by_category":     [_row_to_dict(r) for r in by_category],
        "monthly_trends":  [_row_to_dict(r) for r in monthly],
        "recent_activity": [_row_to_dict(r) for r in recent],
    }
