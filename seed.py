import random
from datetime import datetime, timedelta
import mysql.connector
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345',
    'database': 'edabip_mini'
}

def seed_database():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("Clearing old data...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE activity_log;")
    cursor.execute("TRUNCATE TABLE metrics;")
    cursor.execute("TRUNCATE TABLE departments;")
    cursor.execute("TRUNCATE TABLE users;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    print("Seeding users...")
    hashed_password = bcrypt.generate_password_hash("Password123!").decode('utf-8')
    users = [
        ("Admin User", "admin@edabip.com", hashed_password, "admin"),
        ("Analyst User", "analyst@edabip.com", hashed_password, "analyst"),
        ("Viewer User", "viewer@edabip.com", hashed_password, "viewer")
    ]
    cursor.executemany(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        users
    )

    print("Seeding departments...")
    depts = ["Sales", "Marketing", "HR", "Finance", "Operations"]
    for dept in depts:
        cursor.execute("INSERT INTO departments (name) VALUES (%s)", (dept,))

    cursor.execute("SELECT id, name FROM departments")
    dept_map = {name: id for id, name in cursor.fetchall()}

    cursor.execute("SELECT id FROM users WHERE role = 'admin'")
    admin_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE role = 'analyst'")
    analyst_id = cursor.fetchone()[0]

    metric_definitions = {
        "Sales": ["Quarterly Revenue", "New Deals Closed", "Customer Acquisition Cost", "Conversion Rate"],
        "Marketing": ["Ad Spend", "Website Impressions", "Lead Generation Volume", "Click Through Rate"],
        "HR": ["Employee Turnover", "Training Hours", "Recruitment Cost", "Employee Engagement Score"],
        "Finance": ["Operating Expenses", "Net Margin", "Capital Expenditure", "Cash Reserve"],
        "Operations": ["Server Uptime", "Order Fulfillment Time", "Logistics Cost", "Ticket Resolution Rate"]
    }

    print("Seeding metrics (250+ entries over last 12 months)...")
    today = datetime.today()
    metrics_data = []

    for _ in range(260):
        dept_name = random.choice(depts)
        dept_id = dept_map[dept_name]
        metric_name = random.choice(metric_definitions[dept_name])
        metric_value = round(random.uniform(500.0, 75000.0), 2)
        days_ago = random.randint(0, 365)
        recorded_on = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        uploaded_by = random.choice([admin_id, analyst_id])

        metrics_data.append((dept_id, metric_name, metric_value, recorded_on, uploaded_by))

    cursor.executemany(
        "INSERT INTO metrics (department_id, metric_name, metric_value, recorded_on, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
        metrics_data
    )

    cursor.execute("INSERT INTO activity_log (user_id, action) VALUES (%s, %s)", 
                   (admin_id, "System initialized and seeded database with 260 metrics records."))

    conn.commit()
    cursor.close()
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()