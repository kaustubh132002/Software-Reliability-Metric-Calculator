"""
Database models and data access layer for Software Reliability Metric Calculator (SEQA).
Handles SQLite connection, schema initialization, authentication helpers,
and CRUD operations for reliability records.
"""

import sqlite3
import os
import math
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


def get_db(db_path=None):
    """
    Returns a database connection with Row factory enabled.
    """
    path = db_path or DB_FILE
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None):
    """
    Initializes the database schema if tables do not exist.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Reliability Records Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reliability_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            system_name TEXT NOT NULL,
            category TEXT DEFAULT 'General Software',
            operating_time REAL NOT NULL,
            failures INTEGER NOT NULL,
            repair_time REAL NOT NULL,
            mtbf REAL NOT NULL,
            mttr REAL NOT NULL,
            failure_rate REAL NOT NULL,
            availability REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Create indexes for search performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_user ON reliability_records(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_system ON reliability_records(system_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_created ON reliability_records(created_at)")

    conn.commit()
    conn.close()


# -----------------------------------------------------------------------------
# Metric Calculation Logic (SEQA Mathematical Standards)
# -----------------------------------------------------------------------------

def calculate_metrics(operating_time, failures, repair_time):
    """
    Computes SEQA software reliability metrics.
    
    Formulas:
      - MTBF = Operating Time / Failures
      - MTTR = Repair Time / Failures
      - Failure Rate (lambda) = Failures / Operating Time
      - Availability = MTBF / (MTBF + MTTR) * 100
                     = Operating Time / (Operating Time + Repair Time) * 100
    
    Handles boundary conditions:
      - Failures == 0: MTBF is set to operating_time, MTTR = 0, Failure Rate = 0, Availability = 100%
      - Total Time == 0: Avoid zero-division, return safe defaults
    """
    try:
        op_time = float(operating_time)
        fails = int(failures)
        rep_time = float(repair_time)
    except (ValueError, TypeError):
        raise ValueError("Invalid numeric values provided for metrics calculation.")

    if op_time < 0 or fails < 0 or rep_time < 0:
        raise ValueError("Inputs must be non-negative values.")

    # 1. Failure Rate (lambda)
    if op_time > 0:
        failure_rate = fails / op_time
    else:
        failure_rate = 0.0

    # 2. MTBF (Mean Time Between Failures)
    if fails > 0:
        mtbf = op_time / fails
    else:
        # Zero failures indicates no failure occurred during the observed operating period
        mtbf = op_time if op_time > 0 else 0.0

    # 3. MTTR (Mean Time To Repair)
    if fails > 0:
        mttr = rep_time / fails
    else:
        mttr = 0.0 if rep_time == 0 else rep_time

    # 4. System Availability (A)
    total_time = op_time + rep_time
    if total_time > 0:
        availability = (op_time / total_time) * 100.0
    elif (mtbf + mttr) > 0:
        availability = (mtbf / (mtbf + mttr)) * 100.0
    else:
        availability = 100.0 if fails == 0 else 0.0

    # Cap availability between 0% and 100%
    availability = max(0.0, min(100.0, availability))

    # Determine qualitative reliability grade / status
    if availability >= 99.99:
        status_label = "High Availability (Four 9s+)"
        status_color = "success"
    elif availability >= 99.0:
        status_label = "Acceptable Reliability"
        status_color = "primary"
    elif availability >= 95.0:
        status_label = "Moderate Degradation"
        status_color = "warning"
    else:
        status_label = "Critical / Poor Reliability"
        status_color = "danger"

    return {
        'operating_time': round(op_time, 2),
        'failures': fails,
        'repair_time': round(rep_time, 2),
        'mtbf': round(mtbf, 2),
        'mttr': round(mttr, 2),
        'failure_rate': round(failure_rate, 6),
        'availability': round(availability, 3),
        'status_label': status_label,
        'status_color': status_color
    }


# -----------------------------------------------------------------------------
# User Management Helpers
# -----------------------------------------------------------------------------

def create_user(name, email, password, role='user', db_path=None):
    """
    Creates a new user with hashed password.
    Returns the newly created user_id or None if email already exists.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()
    hashed_pwd = generate_password_hash(password, method='pbkdf2:sha256')

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name.strip(), email.strip().lower(), hashed_pwd, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email, db_path=None):
    """
    Retrieves user record by email.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id, db_path=None):
    """
    Retrieves user record by user ID.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def verify_user(email, password, db_path=None):
    """
    Verifies user credentials.
    Returns user dict if valid, else None.
    """
    user = get_user_by_email(email, db_path)
    if user and check_password_hash(user['password'], password):
        return user
    return None


def list_all_users(db_path=None):
    """
    Retrieves all registered users (for admin dashboard).
    """
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.role, u.created_at,
               COUNT(r.id) AS record_count,
               AVG(r.availability) AS avg_user_availability
        FROM users u
        LEFT JOIN reliability_records r ON u.id = r.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return users


def count_users(db_path=None):
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    count = cursor.fetchone()['total']
    conn.close()
    return count


# -----------------------------------------------------------------------------
# Reliability Records CRUD & Aggregations
# -----------------------------------------------------------------------------

def create_record(user_id, system_name, operating_time, failures, repair_time,
                  notes=None, category='General Software', db_path=None):
    """
    Calculates metrics and stores a new reliability record.
    """
    metrics = calculate_metrics(operating_time, failures, repair_time)

    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reliability_records (
            user_id, system_name, category, operating_time, failures,
            repair_time, mtbf, mttr, failure_rate, availability, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        system_name.strip(),
        category.strip() if category else 'General Software',
        metrics['operating_time'],
        metrics['failures'],
        metrics['repair_time'],
        metrics['mtbf'],
        metrics['mttr'],
        metrics['failure_rate'],
        metrics['availability'],
        notes.strip() if notes else None
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id


def get_record_by_id(record_id, user_id=None, db_path=None):
    """
    Retrieves a single record by ID.
    If user_id is provided, ensures ownership (or bypass if user is admin).
    """
    conn = get_db(db_path)
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT * FROM reliability_records WHERE id = ? AND user_id = ?", (record_id, user_id))
    else:
        cursor.execute("SELECT * FROM reliability_records WHERE id = ?", (record_id,))
    record = cursor.fetchone()
    conn.close()
    return record


def get_records(user_id=None, search=None, category=None,
                sort_by='created_at', sort_order='DESC',
                limit=None, offset=0, db_path=None):
    """
    Queries records with flexible search, category filter, sorting, and pagination.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    query = """
        SELECT r.*, u.name AS author_name, u.email AS author_email
        FROM reliability_records r
        JOIN users u ON r.user_id = u.id
        WHERE 1=1
    """
    params = []

    if user_id is not None:
        query += " AND r.user_id = ?"
        params.append(user_id)

    if search:
        query += " AND (r.system_name LIKE ? OR r.notes LIKE ? OR r.category LIKE ?)"
        pattern = f"%{search.strip()}%"
        params.extend([pattern, pattern, pattern])

    if category and category != 'All':
        query += " AND r.category = ?"
        params.append(category.strip())

    # Whitelist valid sort columns to prevent SQL injection
    valid_sorts = {
        'id': 'r.id',
        'system_name': 'r.system_name',
        'created_at': 'r.created_at',
        'mtbf': 'r.mtbf',
        'mttr': 'r.mttr',
        'availability': 'r.availability',
        'failure_rate': 'r.failure_rate',
        'operating_time': 'r.operating_time',
        'failures': 'r.failures'
    }
    col = valid_sorts.get(sort_by, 'r.created_at')
    order = 'ASC' if str(sort_order).upper() == 'ASC' else 'DESC'

    query += f" ORDER BY {col} {order}"

    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([int(limit), int(offset)])

    cursor.execute(query, params)
    records = cursor.fetchall()
    conn.close()
    return records


def count_records(user_id=None, search=None, category=None, db_path=None):
    """
    Counts total matching records for pagination.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    query = "SELECT COUNT(*) AS total FROM reliability_records r WHERE 1=1"
    params = []

    if user_id is not None:
        query += " AND r.user_id = ?"
        params.append(user_id)

    if search:
        query += " AND (r.system_name LIKE ? OR r.notes LIKE ? OR r.category LIKE ?)"
        pattern = f"%{search.strip()}%"
        params.extend([pattern, pattern, pattern])

    if category and category != 'All':
        query += " AND r.category = ?"
        params.append(category.strip())

    cursor.execute(query, params)
    total = cursor.fetchone()['total']
    conn.close()
    return total


def update_record(record_id, user_id, system_name, operating_time, failures,
                  repair_time, notes=None, category='General Software', db_path=None):
    """
    Recalculates metrics and updates an existing record.
    """
    metrics = calculate_metrics(operating_time, failures, repair_time)

    conn = get_db(db_path)
    cursor = conn.cursor()

    # Check if record belongs to user
    cursor.execute("SELECT user_id FROM reliability_records WHERE id = ?", (record_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return False
    
    # If user_id is supplied and doesn't match, verify permissions
    if user_id is not None and existing['user_id'] != user_id:
        conn.close()
        return False

    cursor.execute("""
        UPDATE reliability_records
        SET system_name = ?,
            category = ?,
            operating_time = ?,
            failures = ?,
            repair_time = ?,
            mtbf = ?,
            mttr = ?,
            failure_rate = ?,
            availability = ?,
            notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        system_name.strip(),
        category.strip() if category else 'General Software',
        metrics['operating_time'],
        metrics['failures'],
        metrics['repair_time'],
        metrics['mtbf'],
        metrics['mttr'],
        metrics['failure_rate'],
        metrics['availability'],
        notes.strip() if notes else None,
        record_id
    ))
    conn.commit()
    conn.close()
    return True


def delete_record(record_id, user_id=None, db_path=None):
    """
    Deletes a record. If user_id is given, ensures user ownership.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("DELETE FROM reliability_records WHERE id = ? AND user_id = ?", (record_id, user_id))
    else:
        cursor.execute("DELETE FROM reliability_records WHERE id = ?", (record_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_summary_stats(user_id=None, db_path=None):
    """
    Calculates aggregated reliability KPI metrics for Dashboard.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    query = """
        SELECT 
            COUNT(*) AS total_systems,
            COALESCE(SUM(failures), 0) AS total_failures,
            COALESCE(SUM(operating_time), 0.0) AS total_operating_time,
            COALESCE(SUM(repair_time), 0.0) AS total_repair_time,
            COALESCE(AVG(mtbf), 0.0) AS avg_mtbf,
            COALESCE(AVG(mttr), 0.0) AS avg_mttr,
            COALESCE(AVG(availability), 0.0) AS avg_availability,
            COALESCE(AVG(failure_rate), 0.0) AS avg_failure_rate,
            COALESCE(MAX(availability), 0.0) AS max_availability,
            COALESCE(MIN(availability), 0.0) AS min_availability
        FROM reliability_records
        WHERE 1=1
    """
    params = []
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()

    total_systems = row['total_systems'] or 0
    total_failures = row['total_failures'] or 0
    avg_mtbf = round(row['avg_mtbf'] or 0.0, 2)
    avg_mttr = round(row['avg_mttr'] or 0.0, 2)
    avg_avail = round(row['avg_availability'] or 0.0, 2)
    avg_fr = round(row['avg_failure_rate'] or 0.0, 6)

    # Weighted overall availability across all operating vs repair hours
    tot_op = row['total_operating_time'] or 0.0
    tot_rep = row['total_repair_time'] or 0.0
    tot_time = tot_op + tot_rep
    system_wide_availability = round((tot_op / tot_time * 100.0), 2) if tot_time > 0 else (100.0 if total_systems > 0 else 0.0)

    return {
        'total_systems': total_systems,
        'total_failures': total_failures,
        'total_operating_time': round(tot_op, 2),
        'total_repair_time': round(tot_rep, 2),
        'avg_mtbf': avg_mtbf,
        'avg_mttr': avg_mttr,
        'avg_availability': avg_avail,
        'system_wide_availability': system_wide_availability,
        'avg_failure_rate': avg_fr,
        'max_availability': round(row['max_availability'] or 0.0, 2),
        'min_availability': round(row['min_availability'] or 0.0, 2)
    }


def get_charts_data(user_id=None, limit=12, db_path=None):
    """
    Returns chronological data arrays ready for Chart.js visualization.
    """
    conn = get_db(db_path)
    cursor = conn.cursor()

    query = """
        SELECT system_name, mtbf, mttr, availability, failure_rate, created_at
        FROM reliability_records
        WHERE 1=1
    """
    params = []
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)

    query += " ORDER BY created_at ASC"
    if limit is not None:
        query += f" LIMIT {int(limit)}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    labels = []
    mtbf_data = []
    mttr_data = []
    avail_data = []
    fr_data = []

    for r in rows:
        labels.append(r['system_name'])
        mtbf_data.append(round(r['mtbf'], 2))
        mttr_data.append(round(r['mttr'], 2))
        avail_data.append(round(r['availability'], 2))
        fr_data.append(round(r['failure_rate'], 5))

    return {
        'labels': labels,
        'mtbf': mtbf_data,
        'mttr': mttr_data,
        'availability': avail_data,
        'failure_rate': fr_data
    }
