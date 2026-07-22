import os
import csv
import io
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'edabip_jwt_super_secret_key_2026'
app.config['JWT_SECRET_KEY'] = 'edabip_jwt_super_secret_key_2026'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'csv'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345',
    'database': 'edabip_mini'
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def log_activity(user_id, action_text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activity_log (user_id, action) VALUES (%s, %s)",
        (user_id, action_text)
    )
    conn.commit()

    cursor.execute("""
        SELECT a.id, u.name, a.action, a.created_at 
        FROM activity_log a 
        JOIN users u ON a.user_id = u.id 
        WHERE a.id = LAST_INSERT_ID()
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        activity_payload = {
            'id': row[0],
            'user_name': row[1],
            'action': row[2],
            'created_at': row[3].strftime('%Y-%m-%d %H:%M:%S')
        }
        socketio.emit('activity_update', activity_payload)

# Helper function to check role authorization
def role_required(allowed_roles):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            role = claims.get('role', 'viewer')
            if role not in allowed_roles:
                return jsonify({'message': 'Forbidden: Insufficient privileges'}), 403
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return jwt_required()(wrapper)
    return decorator

# --- AUTH ROUTES ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'viewer')

    if not name or not email or not password:
        return jsonify({'message': 'All fields are required'}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_pw, role)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except mysql.connector.Error as err:
        return jsonify({'message': 'User already exists or database error'}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not bcrypt.check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = create_access_token(
        identity=str(user['id']),
        additional_claims={'role': user['role'], 'name': user['name'], 'email': user['email']}
    )

    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'avatar_url': user['avatar_url']
        }
    }), 200

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, role, avatar_url, created_at FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user['created_at']:
        user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(user), 200

@app.route('/api/me', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    name = request.form.get('name')
    password = request.form.get('password')
    file = request.files.get('avatar')

    avatar_url = None
    if file and file.filename != '':
        filename = secure_filename(f"avatar_{user_id}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        avatar_url = f"/static/uploads/{filename}"

    query = "UPDATE users SET name = %s"
    params = [name]

    if password:
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        query += ", password = %s"
        params.append(hashed)

    if avatar_url:
        query += ", avatar_url = %s"
        params.append(avatar_url)

    query += " WHERE id = %s"
    params.append(user_id)

    cursor.execute(query, tuple(params))
    conn.commit()

    cursor.execute("SELECT id, name, email, role, avatar_url FROM users WHERE id = %s", (user_id,))
    updated_user = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({'message': 'Profile updated successfully', 'user': updated_user}), 200

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- ANALYTICS ROUTES ---

@app.route('/api/departments', methods=['GET'])
@jwt_required()
def get_departments():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments ORDER BY name ASC")
    depts = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(depts), 200

@app.route('/api/kpis', methods=['GET'])
@jwt_required()
def get_kpis():
    dept = request.args.get('department')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    where_clauses = []
    params = []

    if dept:
        where_clauses.append("d.name = %s")
        params.append(dept)
    if from_date:
        where_clauses.append("m.recorded_on >= %s")
        params.append(from_date)
    if to_date:
        where_clauses.append("m.recorded_on <= %s")
        params.append(to_date)

    where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Total Value and Total Records
    q1 = f"SELECT COALESCE(SUM(m.metric_value), 0) AS total_value, COUNT(m.id) AS total_records FROM metrics m JOIN departments d ON m.department_id = d.id {where_str}"
    cursor.execute(q1, tuple(params))
    res1 = cursor.fetchone()

    # Most Active Department
    q2 = f"SELECT d.name, COUNT(m.id) as cnt FROM metrics m JOIN departments d ON m.department_id = d.id {where_str} GROUP BY d.name ORDER BY cnt DESC LIMIT 1"
    cursor.execute(q2, tuple(params))
    res2 = cursor.fetchone()
    most_active = res2['name'] if res2 else 'N/A'

    # Month-on-Month Comparison
    today = datetime.today()
    first_this_month = today.replace(day=1).strftime('%Y-%m-%d')
    first_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')

    cursor.execute("SELECT COALESCE(SUM(metric_value),0) as val FROM metrics WHERE recorded_on >= %s", (first_this_month,))
    this_month_val = float(cursor.fetchone()['val'])

    cursor.execute("SELECT COALESCE(SUM(metric_value),0) as val FROM metrics WHERE recorded_on >= %s AND recorded_on < %s", (first_last_month, first_this_month))
    last_month_val = float(cursor.fetchone()['val'])

    mom_change = 0.0
    if last_month_val > 0:
        mom_change = round(((this_month_val - last_month_val) / last_month_val) * 100, 2)
    elif this_month_val > 0:
        mom_change = 100.0

    cursor.close()
    conn.close()

    return jsonify({
        'total_value': float(res1['total_value']),
        'total_records': res1['total_records'],
        'most_active_department': most_active,
        'mom_change': mom_change
    }), 200

@app.route('/api/metrics/trend', methods=['GET'])
@jwt_required()
def get_metrics_trend():
    dept = request.args.get('department')
    metric_name = request.args.get('metric_name')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    where_clauses = ["m.recorded_on >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)"]
    params = []

    if dept:
        where_clauses.append("d.name = %s")
        params.append(dept)
    if metric_name:
        where_clauses.append("m.metric_name LIKE %s")
        params.append(f"%{metric_name}%")

    where_str = " WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT DATE_FORMAT(m.recorded_on, '%Y-%m') AS month, SUM(m.metric_value) AS total_value
        FROM metrics m
        JOIN departments d ON m.department_id = d.id
        {where_str}
        GROUP BY month
        ORDER BY month ASC
    """
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    data = [{'month': r['month'], 'total_value': float(r['total_value'])} for r in rows]
    return jsonify(data), 200

@app.route('/api/metrics/by-department', methods=['GET'])
@jwt_required()
def get_metrics_by_department():
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    where_clauses = []
    params = []

    if from_date:
        where_clauses.append("m.recorded_on >= %s")
        params.append(from_date)
    if to_date:
        where_clauses.append("m.recorded_on <= %s")
        params.append(to_date)

    where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    query = f"""
        SELECT d.name AS department, SUM(m.metric_value) AS total_value
        FROM metrics m
        JOIN departments d ON m.department_id = d.id
        {where_str}
        GROUP BY d.name
        ORDER BY total_value DESC
    """
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    data = [{'department': r['department'], 'total_value': float(r['total_value'])} for r in rows]
    return jsonify(data), 200

@app.route('/api/metrics/top', methods=['GET'])
@jwt_required()
def get_top_metrics():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT m.metric_name, d.name as department, SUM(m.metric_value) as total_value
        FROM metrics m
        JOIN departments d ON m.department_id = d.id
        GROUP BY m.metric_name, d.name
        ORDER BY total_value DESC
        LIMIT 5
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    data = [{'metric_name': r['metric_name'], 'department': r['department'], 'total_value': float(r['total_value'])} for r in rows]
    return jsonify(data), 200

@app.route('/api/metrics', methods=['GET'])
@jwt_required()
def get_metrics():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    dept = request.args.get('department')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    search = request.args.get('search')

    offset = (page - 1) * limit
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    where_clauses = []
    params = []

    if dept:
        where_clauses.append("d.name = %s")
        params.append(dept)
    if from_date:
        where_clauses.append("m.recorded_on >= %s")
        params.append(from_date)
    if to_date:
        where_clauses.append("m.recorded_on <= %s")
        params.append(to_date)
    if search:
        where_clauses.append("m.metric_name LIKE %s")
        params.append(f"%{search}%")

    where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Count Query
    count_query = f"SELECT COUNT(*) as total FROM metrics m JOIN departments d ON m.department_id = d.id {where_str}"
    cursor.execute(count_query, tuple(params))
    total_records = cursor.fetchone()['total']

    # Data Query
    data_query = f"""
        SELECT m.id, d.name AS department, m.metric_name, m.metric_value, 
               DATE_FORMAT(m.recorded_on, '%Y-%m-%d') AS recorded_on, u.name AS uploaded_by
        FROM metrics m
        JOIN departments d ON m.department_id = d.id
        JOIN users u ON m.uploaded_by = u.id
        {where_str}
        ORDER BY m.recorded_on DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    cursor.execute(data_query, tuple(params))
    records = cursor.fetchall()

    for r in records:
        r['metric_value'] = float(r['metric_value'])

    cursor.close()
    conn.close()

    total_pages = (total_records + limit - 1) // limit

    return jsonify({
        'data': records,
        'pagination': {
            'total_records': total_records,
            'total_pages': total_pages,
            'current_page': page,
            'limit': limit
        }
    }), 200

# --- DATA ENTRY ROUTES ---

@app.route('/api/metrics', methods=['POST'])
@role_required(['admin', 'analyst'])
def add_metric():
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_name = claims.get('name', 'User')

    data = request.get_json()
    dept_id = data.get('department_id')
    metric_name = data.get('metric_name')
    metric_value = data.get('metric_value')
    recorded_on = data.get('recorded_on')

    if not dept_id or not metric_name or not metric_value or not recorded_on:
        return jsonify({'message': 'Missing required fields'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO metrics (department_id, metric_name, metric_value, recorded_on, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
        (dept_id, metric_name, metric_value, recorded_on, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    log_activity(user_id, f"{user_name} created metric '{metric_name}' valued at ${metric_value}")
    return jsonify({'message': 'Metric added successfully'}), 201

@app.route('/api/metrics/upload', methods=['POST'])
@role_required(['admin', 'analyst'])
def upload_csv():
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_name = claims.get('name', 'User')

    if 'file' not in request.files:
        return jsonify({'message': 'No file submitted'}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'message': 'Only CSV files are allowed'}), 400

    stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
    csv_input = csv.DictReader(stream)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM departments")
    dept_map = {row['name'].lower(): row['id'] for row in cursor.fetchall()}

    records_inserted = 0
    for row in csv_input:
        dept_name = row.get('department', '').strip().lower()
        m_name = row.get('metric_name', '').strip()
        m_val = row.get('metric_value', '').strip()
        rec_on = row.get('recorded_on', '').strip()

        if dept_name in dept_map and m_name and m_val and rec_on:
            cursor.execute(
                "INSERT INTO metrics (department_id, metric_name, metric_value, recorded_on, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
                (dept_map[dept_name], m_name, float(m_val), rec_on, user_id)
            )
            records_inserted += 1

    conn.commit()
    cursor.close()
    conn.close()

    log_activity(user_id, f"{user_name} bulk uploaded {records_inserted} records via CSV")
    return jsonify({'message': f'{records_inserted} records uploaded successfully.'}), 200

@app.route('/api/metrics/<int:metric_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_metric(metric_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_name = claims.get('name', 'User')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM metrics WHERE id = %s", (metric_id,))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if affected == 0:
        return jsonify({'message': 'Record not found'}), 404

    log_activity(user_id, f"Admin {user_name} deleted metric record #{metric_id}")
    return jsonify({'message': 'Record deleted successfully'}), 200

@app.route('/api/activity', methods=['GET'])
@role_required(['admin'])
def get_activity_log():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, u.name as user_name, a.action, DATE_FORMAT(a.created_at, '%Y-%m-%d %H:%i:%s') as created_at
        FROM activity_log a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT 20
    """)
    activities = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(activities), 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)