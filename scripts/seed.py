import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import ensure_schema, get_conn  # noqa: E402
from app.ingest import ingest  # noqa: E402

EMPLOYEES = [
    ("E100", "Ira Malhotra", "ira.malhotra@goaified.example", "+91 90000 00100", "Leadership", "Founder", None, "2024-01-08"),
    ("E101", "Aarav Mehta", "aarav.mehta@goaified.example", "+91 90000 00101", "Engineering", "Senior AI Engineer", "E100", "2024-03-11"),
    ("E102", "Diya Sharma", "diya.sharma@goaified.example", "+91 90000 00102", "Engineering", "AI Engineer", "E101", "2025-01-20"),
    ("E103", "Kabir Rao", "kabir.rao@goaified.example", "+91 90000 00103", "Sales", "Account Executive", "E100", "2025-04-02"),
    ("E104", "Meera Iyer", "meera.iyer@goaified.example", "+91 90000 00104", "People Ops", "People Partner", "E100", "2024-05-06"),
    ("E105", "Rohan Gupta", "rohan.gupta@goaified.example", "+91 90000 00105", "IT", "IT Support Lead", "E100", "2024-07-15"),
    ("E106", "Ananya Nair", "ananya.nair@goaified.example", "+91 90000 00106", "Finance", "Finance Lead", "E100", "2024-02-19"),
]

LEAVE = {
    "E100": [("casual", 12, 2), ("sick", 10, 0), ("earned", 18, 4)],
    "E101": [("casual", 12, 4), ("sick", 10, 2), ("earned", 18, 6)],
    "E102": [("casual", 12, 9), ("sick", 10, 10), ("earned", 18, 5)],
    "E103": [("casual", 12, 0), ("sick", 10, 3), ("earned", 18, 0)],
    "E104": [("casual", 12, 2), ("sick", 10, 1), ("earned", 18, 15)],
    "E105": [("casual", 12, 5), ("sick", 10, 0), ("earned", 18, 2)],
    "E106": [("casual", 12, 12), ("sick", 10, 0), ("earned", 18, 18)],
}


def seed_employees(conn) -> int:
    for row in EMPLOYEES:
        conn.execute(
            """
            INSERT INTO employees
                (employee_id, name, email, phone, department, role, manager_id, joined_on)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (employee_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                phone = EXCLUDED.phone,
                department = EXCLUDED.department,
                role = EXCLUDED.role,
                manager_id = EXCLUDED.manager_id,
                joined_on = EXCLUDED.joined_on
            """,
            row,
        )
    for employee_id, balances in LEAVE.items():
        for leave_type, entitled, used in balances:
            conn.execute(
                """
                INSERT INTO leave_balances (employee_id, leave_type, entitled, used)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (employee_id, leave_type) DO UPDATE SET
                    entitled = EXCLUDED.entitled,
                    used = EXCLUDED.used
                """,
                (employee_id, leave_type, entitled, used),
            )
    conn.commit()
    return len(EMPLOYEES)


def main() -> None:
    with get_conn() as conn:
        ensure_schema(conn)
        employee_count = seed_employees(conn)
        summary = ingest(conn)
    summary["employees"] = employee_count
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
