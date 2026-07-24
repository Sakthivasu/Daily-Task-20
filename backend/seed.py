import mysql.connector
from flask_bcrypt import Bcrypt
import random
from datetime import datetime, timedelta

# Database Connection Details
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345',
}

def seed_database():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create Database
    cursor.execute("CREATE DATABASE IF NOT EXISTS edabip_mini;")
    cursor.execute("USE edabip_mini;")

    # Drop existing tables to allow fresh rebuild
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("DROP TABLE IF EXISTS activity_log;")
    cursor.execute("DROP TABLE IF EXISTS metrics;")
    cursor.execute("DROP TABLE IF EXISTS departments;")
    cursor.execute("DROP TABLE IF EXISTS users;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # Create Tables
    cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin','analyst','viewer') DEFAULT 'viewer',
            avatar_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE departments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE
        );
    """)

    cursor.execute("""
        CREATE TABLE metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            department_id INT NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            metric_value DECIMAL(15,2) NOT NULL,
            recorded_on DATE NOT NULL,
            uploaded_by INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE activity_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            action VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    bcrypt = Bcrypt()

    # Seed Users with distinct individual passwords
    users_data = [
        ("Admin User", "admin@edabip.com", bcrypt.generate_password_hash("Admin123!").decode('utf-8'), "admin"),
        ("Analyst User", "analyst@edabip.com", bcrypt.generate_password_hash("Analyst123!").decode('utf-8'), "analyst"),
        ("Viewer User", "viewer@edabip.com", bcrypt.generate_password_hash("Viewer123!").decode('utf-8'), "viewer")
    ]
    
    cursor.executemany(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        users_data
    )

    # Seed Departments
    departments = [('Sales',), ('Marketing',), ('HR',), ('Finance',), ('Operations',)]
    cursor.executemany("INSERT INTO departments (name) VALUES (%s)", departments)

    # Metrics Pool
    metric_names = {
        1: ['Revenue', 'Deals Closed', 'Sales Conversion Rate', 'Customer Acquisition Cost'], # Sales
        2: ['Ad Spend', 'Leads Generated', 'CTR', 'Campaign ROI'],                              # Marketing
        3: ['Employee Turnover', 'Time to Hire', 'Training Hours', 'Employee Satisfaction'],    # HR
        4: ['Operating Margin', 'Net Income', 'Cash Flow', 'Expense Ratio'],                    # Finance
        5: ['Uptime', 'Fulfillment Time', 'Inventory Turnover', 'Order Accuracy']              # Operations
    }

    # Generate 220 random metric records over the last 12 months
    metrics_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    for _ in range(220):
        dept_id = random.randint(1, 5)
        m_name = random.choice(metric_names[dept_id])
        m_value = round(random.uniform(500.0, 50000.0), 2)
        
        # Random date within last year
        random_days = random.randint(0, 365)
        recorded_date = (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')
        
        uploader_id = random.choice([1, 2]) # Admin or Analyst
        metrics_data.append((dept_id, m_name, m_value, recorded_date, uploader_id))

    cursor.executemany("""
        INSERT INTO metrics (department_id, metric_name, metric_value, recorded_on, uploaded_by)
        VALUES (%s, %s, %s, %s, %s)
    """, metrics_data)

    # Initial Activity Logs
    activity_data = [
        (1, "System initialized and seed data loaded."),
        (2, "Analyst logged in and uploaded initial Q1 metrics batch.")
    ]
    cursor.executemany("INSERT INTO activity_log (user_id, action) VALUES (%s, %s)", activity_data)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database `edabip_mini` successfully seeded with 220+ records and 3 default users!")

if __name__ == '__main__':
    seed_database()