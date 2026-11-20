import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from app.db import get_conn  # noqa: E402

mcp = FastMCP("goaified-hr")


def _round(value) -> float | int:
    number = float(value)
    return int(number) if number.is_integer() else round(number, 1)


@mcp.tool()
def get_leave_balance(employee_id: str) -> str:
    """Return the current leave balance for one employee, by leave type.

    Args:
        employee_id: Company employee id, for example E102.
    """
    employee_id = employee_id.strip().upper()
    with get_conn() as conn:
        employee = conn.execute(
            "SELECT employee_id, name, department FROM employees WHERE employee_id = %s",
            (employee_id,),
        ).fetchone()
        if not employee:
            return json.dumps({"found": False, "employee_id": employee_id})
        rows = conn.execute(
            """
            SELECT leave_type, entitled, used
            FROM leave_balances
            WHERE employee_id = %s
            ORDER BY leave_type
            """,
            (employee_id,),
        ).fetchall()

    balances = [
        {
            "leave_type": row["leave_type"],
            "entitled": _round(row["entitled"]),
            "used": _round(row["used"]),
            "remaining": _round(row["entitled"]) - _round(row["used"]),
        }
        for row in rows
    ]
    return json.dumps(
        {
            "found": True,
            "employee_id": employee["employee_id"],
            "name": employee["name"],
            "department": employee["department"],
            "leave_year": "2026-04-01 to 2027-03-31",
            "balances": balances,
            "total_remaining": round(sum(b["remaining"] for b in balances), 1),
        }
    )


@mcp.tool()
def get_employee_profile(employee_id: str) -> str:
    """Return the directory profile for one employee: role, department, manager, contact details.

    Args:
        employee_id: Company employee id, for example E102.
    """
    employee_id = employee_id.strip().upper()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT e.employee_id, e.name, e.email, e.phone, e.department, e.role,
                   e.joined_on, m.name AS manager_name
            FROM employees e
            LEFT JOIN employees m ON m.employee_id = e.manager_id
            WHERE e.employee_id = %s
            """,
            (employee_id,),
        ).fetchone()

    if not row:
        return json.dumps({"found": False, "employee_id": employee_id})
    return json.dumps(
        {
            "found": True,
            "employee_id": row["employee_id"],
            "name": row["name"],
            "email": row["email"],
            "phone": row["phone"],
            "department": row["department"],
            "role": row["role"],
            "manager": row["manager_name"],
            "joined_on": row["joined_on"].isoformat(),
        }
    )


if __name__ == "__main__":
    mcp.run()
