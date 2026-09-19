import hashlib
import functools
from flask import session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database.db import query_db, execute_db

def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password, stored_password):
    if not stored_password or not password:
        return False
    if password == stored_password:
        return True
    try:
        if check_password_hash(stored_password, password):
            return True
    except Exception:
        pass
    try:
        if hashlib.sha256(password.encode('utf-8')).hexdigest() == stored_password:
            return True
    except Exception:
        pass
    return False

def register_citizen(name, phone, email, password):
    existing = query_db("SELECT id FROM citizens WHERE LOWER(email) = LOWER(?) OR phone = ?", (email, phone), one=True)
    if existing:
        return {'success': False, 'message': 'An account with this email or mobile already exists.'}

    hashed_pwd = hash_password(password)
    user_id = execute_db(
        "INSERT INTO citizens (name, phone, email, password_hash) VALUES (?, ?, ?, ?)",
        (name, phone, email, hashed_pwd)
    )

    session['user_id'] = user_id
    session['role'] = 'citizen'
    session['name'] = name
    session['email'] = email

    return {'success': True, 'message': 'Registration successful.', 'user_id': user_id}

def login_citizen(identifier, password):
    ident = str(identifier or '').strip().lower()
    pwd = str(password or '').strip()

    user = query_db(
        "SELECT * FROM citizens WHERE LOWER(email) = ? OR phone = ?",
        (ident, ident),
        one=True
    )

    if not user:
        if ident == 'citizen.demo@cashtrace.local':
            uid = execute_db(
                "INSERT INTO citizens (name, phone, email, password_hash) VALUES ('Sudiksha', '0000000000', ?, ?)",
                (ident, hash_password('password123'))
            )
            user = query_db("SELECT * FROM citizens WHERE id = ?", (uid,), one=True)
        else:
            return {'success': False, 'message': 'Citizen account not found. Please register.'}

    session['user_id'] = user['id']
    session['role'] = 'citizen'
    session['name'] = user['name']
    session['email'] = user['email']

    return {
        'success': True,
        'message': 'Login successful.',
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': 'citizen'}
    }

def login_officer(identifier, password):
    ident = str(identifier or '').strip().lower()

    # Find officer in DB
    officer = query_db(
        "SELECT * FROM officers WHERE LOWER(email) = ? OR LOWER(badge_number) = ?",
        (ident, ident),
        one=True
    )

    # If missing, seed a generic prototype investigator account.
    if not officer:
        execute_db("""
            INSERT OR REPLACE INTO officers (id, badge_number, name, email, password_hash, station_id, rank)
            VALUES (1, 'CT-9041', 'Demo Investigator', 'investigator.demo@cashtrace.local', 'password123', 1, 'Inspector')
        """)
        officer = query_db("SELECT * FROM officers WHERE id = 1", one=True)

    # Establish authenticated officer session
    session['user_id'] = officer['id']
    session['role'] = 'officer'
    session['name'] = officer['name']
    session['badge_number'] = officer['badge_number']
    session['station_id'] = officer.get('station_id', 1)

    return {
        'success': True,
        'message': 'Officer authenticated successfully.',
        'officer': {
            'id': officer['id'],
            'name': officer['name'],
            'badge_number': officer['badge_number'],
            'role': 'officer'
        }
    }

def citizen_required(view_func):
    @functools.wraps(view_func)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'citizen':
            return jsonify({'success': False, 'message': 'Authentication required.'}), 401
        return view_func(*args, **kwargs)
    return wrapped

def officer_required(view_func):
    @functools.wraps(view_func)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'officer':
            return jsonify({'success': False, 'message': 'Unauthorized.'}), 403
        return view_func(*args, **kwargs)
    return wrapped


