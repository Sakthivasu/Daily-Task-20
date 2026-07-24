import os
import csv
import io
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
)
from flask_socketio import SocketIO 
import mysql.connector
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'edabip-super-secret-key-2026'
app.config['JWT_SECRET_KEY'] = 'jwt-super-secret-key-2026'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CORS(
    app, 
    resources={r"/api/*": {"origins": "*"}}, 
    allow_headers=["Content-Type", "Authorization"], 
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345',
    'database': 'edabip_mini'
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_activity(user_id, action):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO activity_log (user_id, action) VALUES (%s, %s)", (user_id, action))
    conn.commit()
    
    cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
    user_row = cursor.fetchone()
    user_name = user_row[0] if user_row else "User"
    
    cursor.close()
    conn.close()
    
    socketio.emit('activity_update', {
        'action': action,
        'user_name': user_name,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def role_required(roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = int(get_jwt_identity())
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if not user or user['role'] not in roles:
                return jsonify({'message': 'Access denied. Insufficient permissions.'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/api/home', methods=['GET'])
def api_home():
    return jsonify({
        'status': 'online',
        'app': 'EDABIP Mini Enterprise Analytics Platform',
        'version': '1.0.0'
    }), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'viewer')

    if not name or not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_pw, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        log_activity(user_id, f"New user registered: {name} ({role})")
        return jsonify({'message': 'User registered successfully'}), 201
    except mysql.connector.Error as err:
        return jsonify({'message': 'Email already exists'}), 400
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

    if user and bcrypt.check_password_hash(user['password'], password):
        token = create_access_token(identity=str(user['id']))
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
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['GET'])
@jwt_required()
def logout():
    return jsonify({'message': 'Successfully logged out'}), 200

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, role, avatar_url FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(user), 200

@app.route('/api/me', methods=['PUT'])
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    conn = get_db()
    cursor = conn.cursor()

    if password:
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute("UPDATE users SET name = %s, password = %s WHERE id = %s", (name, hashed_pw, user_id))
    else:
        cursor.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))

    conn.commit()
    cursor.close()
    conn.close()
    log_activity(user_id, "Updated profile credentials")
    return jsonify({'message': 'Profile updated successfully'}), 200

@app.route('/api/upload-avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    user_id = get_jwt_identity()
    if 'avatar' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['avatar']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'message': 'Invalid file format'}), 400

    filename = secure_filename(f"user_{user_id}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    avatar_url = f"/static/uploads/{filename}"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (avatar_url, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'avatar_url': avatar_url, 'message': 'Avatar uploaded'}), 200

@app.route('/static/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route('/api/kpis', methods=['GET'])
@jwt_required()
def get_kpis():
    dept_id = request.args.get('department')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    where_clauses = ["1=1"]
    params = []

    if dept_id:
        where_clauses.append("department_id = %s")
        params.append(dept_id)
    if from_date:
        where_clauses.append("recorded_on >= %s")
        params.append(from_date)
    if to_date:
        where_clauses.append("recorded_on <= %s")
        params.append(to_date)

    where_str = " AND ".join(where_clauses)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch Total Sum, Total Records Count, and Average Value
    cursor.execute(f"""
        SELECT 
            SUM(metric_value) as total_val, 
            COUNT(*) as total_recs,
            AVG(metric_value) as avg_val 
        FROM metrics 
        WHERE {where_str}
    """, params)
    overview = cursor.fetchone()

    # 2. Fetch Most Active Department
    cursor.execute(f"""
        SELECT d.name, COUNT(m.id) as cnt 
        FROM metrics m 
        JOIN departments d ON m.department_id = d.id 
        WHERE {where_str} 
        GROUP BY d.name 
        ORDER BY cnt DESC 
        LIMIT 1
    """, params)
    active_dept = cursor.fetchone()

    # 3. Fetch Month-over-Month (MoM) Growth
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN recorded_on >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN metric_value ELSE 0 END) as current_month,
            SUM(CASE WHEN recorded_on >= DATE_SUB(CURDATE(), INTERVAL 60 DAY) AND recorded_on < DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN metric_value ELSE 0 END) as previous_month
        FROM metrics
    """)
    mom = cursor.fetchone()

    curr = float(mom['current_month'] or 0)
    prev = float(mom['previous_month'] or 0)
    mom_change = (((curr - prev) / prev) * 100) if prev > 0 else 0.0

    cursor.close()
    conn.close()

    total_val = float(overview['total_val'] or 0)
    total_recs = overview['total_recs'] or 0
    avg_val = float(overview['avg_val'] or 0)

    return jsonify({
        'total_value': round(total_val, 2),
        'total_records': total_recs,
        'average_value': round(avg_val, 2),
        'most_active_department': active_dept['name'] if active_dept else 'N/A',
        'mom_change_pct': round(mom_change, 2)
    }), 200


@app.route('/api/metrics/trend', methods=['GET'])
@jwt_required()
def get_trend():
    dept_id = request.args.get('department')
    metric_name = request.args.get('metric_name')

    where_clauses = ["recorded_on >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)"]
    params = []

    if dept_id:
        where_clauses.append("department_id = %s")
        params.append(dept_id)
    if metric_name:
        where_clauses.append("metric_name LIKE %s")
        params.append(f"%{metric_name}%")

    where_str = " AND ".join(where_clauses)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""
        SELECT DATE_FORMAT(recorded_on, '%Y-%m') as month, SUM(metric_value) as total 
        FROM metrics 
        WHERE {where_str} 
        GROUP BY month ORDER BY month ASC
    """, params)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify([{'month': d['month'], 'total': float(d['total'])} for d in data]), 200

@app.route('/api/metrics/by-department', methods=['GET'])
@jwt_required()
def get_by_department():
    dept_id = request.args.get('department')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    where_clauses = ["1=1"]
    params = []

    if dept_id:
        where_clauses.append("m.department_id = %s")
        params.append(dept_id)
    if from_date:
        where_clauses.append("m.recorded_on >= %s")
        params.append(from_date)
    if to_date:
        where_clauses.append("m.recorded_on <= %s")
        params.append(to_date)

    where_str = " AND ".join(where_clauses)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""
        SELECT d.name as department, SUM(m.metric_value) as total_value 
        FROM metrics m JOIN departments d ON m.department_id = d.id 
        WHERE {where_str} 
        GROUP BY d.name
    """, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify([{'department': r['department'], 'total_value': float(r['total_value'])} for r in rows]), 200

@app.route('/api/metrics/top', methods=['GET'])
@jwt_required()
def get_top_metrics():
    dept_id = request.args.get('department')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    where_clauses = ["1=1"]
    params = []

    if dept_id:
        where_clauses.append("department_id = %s")
        params.append(dept_id)
    if from_date:
        where_clauses.append("recorded_on >= %s")
        params.append(from_date)
    if to_date:
        where_clauses.append("recorded_on <= %s")
        params.append(to_date)

    where_str = " AND ".join(where_clauses)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""
        SELECT metric_name, department_id, SUM(metric_value) as total_value 
        FROM metrics 
        WHERE {where_str}
        GROUP BY metric_name, department_id 
        ORDER BY total_value DESC LIMIT 5
    """, params)
    rows = cursor.fetchall()
    
    # department name 
    cursor.execute("SELECT id, name FROM departments")
    dept_map = {d['id']: d['name'] for d in cursor.fetchall()}
    
    cursor.close()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            'metric_name': r['metric_name'],
            'department': dept_map.get(r['department_id'], 'General'),
            'total_value': float(r['total_value'])
        })

    return jsonify(result), 200

@app.route('/api/metrics', methods=['GET'])
@jwt_required()
def get_metrics_paginated():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit
    dept_id = request.args.get('department')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    search = request.args.get('search')

    where_clauses = ["1=1"]
    params = []

    if dept_id:
        where_clauses.append("m.department_id = %s")
        params.append(dept_id)
    if from_date:
        where_clauses.append("m.recorded_on >= %s")
        params.append(from_date)
    if to_date:
        where_clauses.append("m.recorded_on <= %s")
        params.append(to_date)
    if search:
        where_clauses.append("m.metric_name LIKE %s")
        params.append(f"%{search}%")

    where_str = " AND ".join(where_clauses)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(f"SELECT COUNT(*) as total FROM metrics m WHERE {where_str}", params)
    total_records = cursor.fetchone()['total']

    query = f"""
        SELECT m.id, d.name as department, m.metric_name, m.metric_value, m.recorded_on, u.name as uploader
        FROM metrics m 
        JOIN departments d ON m.department_id = d.id 
        JOIN users u ON m.uploaded_by = u.id 
        WHERE {where_str} 
        ORDER BY m.recorded_on DESC 
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [limit, offset])
    records = cursor.fetchall()

    cursor.close()
    conn.close()

    formatted_records = []
    for r in records:
        r['metric_value'] = float(r['metric_value'])
        r['recorded_on'] = r['recorded_on'].strftime('%Y-%m-%d')
        formatted_records.append(r)

    return jsonify({
        'data': formatted_records,
        'page': page,
        'limit': limit,
        'total': total_records,
        'pages': (total_records + limit - 1) // limit
    }), 200

@app.route('/api/metrics', methods=['POST'])
@role_required(['admin', 'analyst'])
def add_metric():
    user_id = get_jwt_identity()
    data = request.get_json()

    dept_id = data.get('department_id')
    metric_name = data.get('metric_name')
    metric_value = data.get('metric_value')
    recorded_on = data.get('recorded_on')

    if not all([dept_id, metric_name, metric_value, recorded_on]):
        return jsonify({'message': 'Missing required fields'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO metrics (department_id, metric_name, metric_value, recorded_on, uploaded_by)
        VALUES (%s, %s, %s, %s, %s)
    """, (dept_id, metric_name, metric_value, recorded_on, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    log_activity(user_id, f"Added manual metric: {metric_name} (${metric_value})")
    return jsonify({'message': 'Metric record created successfully'}), 201

@app.route('/api/metrics/upload', methods=['POST'])
@role_required(['admin', 'analyst'])
def upload_csv():
    user_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({'message': 'No CSV file provided'}), 400
    file = request.files['file']

    if not file.filename.endswith('.csv'):
        return jsonify({'message': 'File must be CSV format'}), 400

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, name FROM departments")
    dept_map = {d['name'].lower(): d['id'] for d in cursor.fetchall()}

    records_to_insert = []
    for row in csv_input:
        dept_name = row.get('department', '').strip().lower()
        dept_id = dept_map.get(dept_name)
        if dept_id:
            records_to_insert.append((
                dept_id,
                row.get('metric_name'),
                float(row.get('metric_value', 0)),
                row.get('recorded_on'),
                user_id
            ))

    if records_to_insert:
        cursor.executemany("""
            INSERT INTO metrics (department_id, metric_name, metric_value, recorded_on, uploaded_by)
            VALUES (%s, %s, %s, %s, %s)
        """, records_to_insert)
        conn.commit()

    count = len(records_to_insert)
    cursor.close()
    conn.close()

    log_activity(user_id, f"Bulk uploaded CSV containing {count} metrics")
    return jsonify({'message': f'{count} records uploaded successfully.', 'count': count}), 200

@app.route('/api/metrics/<int:metric_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_metric(metric_id):
    user_id = get_jwt_identity()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM metrics WHERE id = %s", (metric_id,))
    conn.commit()
    cursor.close()
    conn.close()

    log_activity(user_id, f"Deleted metric record #{metric_id}")
    return jsonify({'message': f'Record #{metric_id} deleted successfully.'}), 200

@app.route('/api/metrics/<int:metric_id>', methods=['PUT', 'OPTIONS'])
def update_metric(metric_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    return update_metric_logic(metric_id)

@jwt_required()
@role_required(['admin', 'analyst'])
def update_metric_logic(metric_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()

    metric_name = data.get('metric_name')
    metric_value = data.get('metric_value')
    recorded_on = data.get('recorded_on')

    if not metric_name or not metric_value or not recorded_on:
        return jsonify({'message': 'Missing required fields'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE metrics 
        SET metric_name = %s, metric_value = %s, recorded_on = %s 
        WHERE id = %s
    """, (metric_name, metric_value, recorded_on, metric_id))
    conn.commit()
    cursor.close()
    conn.close()

    log_activity(user_id, f"Updated metric record #{metric_id}: {metric_name}")
    return jsonify({'message': f'Record #{metric_id} updated successfully.'}), 200

@app.route('/api/activity', methods=['GET'])
@jwt_required()
def get_activity():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, a.action, a.created_at, u.name as user_name 
        FROM activity_log a 
        JOIN users u ON a.user_id = u.id 
        ORDER BY a.created_at DESC LIMIT 20
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    for r in rows:
        r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(rows), 200

@app.route('/api/departments', methods=['GET'])
@jwt_required()
def get_departments():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, a.action, a.created_at, u.name as user_name 
        FROM activity_log a 
        JOIN users u ON a.user_id = u.id 
        ORDER BY a.created_at DESC LIMIT 10
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    for r in rows:
        r['created_at'] = r['created__at'].strftime('%Y-%m-%d %H:%M:%S') if 'created__at' in r else r['created_at'].strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(rows), 200

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activity_log WHERE id = %s", (notification_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Notification deleted successfully'}), 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)