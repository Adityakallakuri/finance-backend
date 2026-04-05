"""
seed.py
-------
Populates the database with sample users and financial records.
Run ONCE after setting up: python seed.py
"""

from app import create_app
from app.models.user   import create_user, get_user_by_username
from app.models.record import create_record

app = create_app()

SAMPLE_USERS = [
    {"username": "admin_user",   "email": "admin@finance.com",   "password": "admin123",   "role": "admin"},
    {"username": "analyst_user", "email": "analyst@finance.com", "password": "analyst123", "role": "analyst"},
    {"username": "viewer_user",  "email": "viewer@finance.com",  "password": "viewer123",  "role": "viewer"},
]

SAMPLE_RECORDS = [
    {"amount": 5000.00, "type_": "income",  "category": "Salary",      "date": "2024-01-01", "notes": "Monthly salary"},
    {"amount": 1200.00, "type_": "expense", "category": "Rent",        "date": "2024-01-05", "notes": "January rent"},
    {"amount": 350.00,  "type_": "expense", "category": "Groceries",   "date": "2024-01-10", "notes": "Weekly groceries"},
    {"amount": 2500.00, "type_": "income",  "category": "Freelance",   "date": "2024-01-15", "notes": "Web project"},
    {"amount": 80.00,   "type_": "expense", "category": "Utilities",   "date": "2024-01-18", "notes": "Electricity bill"},
    {"amount": 5000.00, "type_": "income",  "category": "Salary",      "date": "2024-02-01", "notes": "Monthly salary"},
    {"amount": 1200.00, "type_": "expense", "category": "Rent",        "date": "2024-02-05", "notes": "February rent"},
    {"amount": 200.00,  "type_": "expense", "category": "Transport",   "date": "2024-02-12", "notes": "Fuel"},
    {"amount": 800.00,  "type_": "income",  "category": "Freelance",   "date": "2024-02-20", "notes": "Logo design"},
    {"amount": 450.00,  "type_": "expense", "category": "Groceries",   "date": "2024-02-25", "notes": "Monthly groceries"},
    {"amount": 5000.00, "type_": "income",  "category": "Salary",      "date": "2024-03-01", "notes": "Monthly salary"},
    {"amount": 1200.00, "type_": "expense", "category": "Rent",        "date": "2024-03-05", "notes": "March rent"},
    {"amount": 300.00,  "type_": "expense", "category": "Healthcare",  "date": "2024-03-14", "notes": "Doctor visit"},
    {"amount": 1500.00, "type_": "income",  "category": "Investment",  "date": "2024-03-22", "notes": "Dividend payout"},
    {"amount": 120.00,  "type_": "expense", "category": "Utilities",   "date": "2024-03-28", "notes": "Internet bill"},
]

with app.app_context():
    print("Seeding users...")
    admin_user = None
    for u in SAMPLE_USERS:
        if get_user_by_username(u["username"]):
            print(f"  ⚠  {u['username']} already exists, skipping.")
            if u["role"] == "admin":
                admin_user = get_user_by_username(u["username"])
        else:
            user = create_user(**u)
            print(f"  ✓  Created {user['role']}: {user['username']}")
            if u["role"] == "admin":
                admin_user = user

    print("\nSeeding financial records...")
    if admin_user:
        for r in SAMPLE_RECORDS:
            rec = create_record(**r, created_by=admin_user["id"])
            print(f"  ✓  {rec['type'].upper():7s} | {rec['category']:12s} | ₹{rec['amount']:.2f}")
    else:
        print("  ⚠  No admin user found, skipping records.")

    print("\n✅ Seeding complete!")
    print("\nLogin credentials:")
    print("  Admin   → username: admin_user   | password: admin123")
    print("  Analyst → username: analyst_user | password: analyst123")
    print("  Viewer  → username: viewer_user  | password: viewer123")
