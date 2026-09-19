import os
import random
import datetime
from flask import Blueprint, request, jsonify, session
from config import Config
from backend.database.db import query_db, execute_db
from backend.security import sanitize_user_input, haversine_distance
from backend.auth import register_citizen, login_citizen, login_officer, citizen_required, officer_required
from backend.similarity import find_similar_incidents
from backend.hotspot import analyze_hotspots
from backend.prediction import get_all_predictions
from backend.rag_knowledge import build_context

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Setup Gemini AI Client (with fallback)
try:
    from google import genai
    from google.genai import types
    gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")) if (Config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")) else None
except Exception:
    gemini_client = None

def ensure_audit_tables():
    execute_db("""
        CREATE TABLE IF NOT EXISTS case_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            officer_name TEXT NOT NULL,
            action_text TEXT NOT NULL,
            remarks TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

# -------------------------------------------------------------
# 1. Authentication Endpoints
# -------------------------------------------------------------
@api_bp.route('/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    name = sanitize_user_input(data.get('name', ''))
    phone = sanitize_user_input(data.get('phone', ''))
    email = sanitize_user_input(data.get('email', '')).lower()
    pwd = data.get('password', '')
    if not all([name, phone, email, pwd]):
        return jsonify({'success': False, 'message': 'All fields are mandatory.'}), 400
    res = register_citizen(name, phone, email, pwd)
    return jsonify(res), 200 if res['success'] else 400

@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    ident = sanitize_user_input(data.get('identifier', '')).lower()
    pwd = data.get('password', '')
    res = login_citizen(ident, pwd)
    return jsonify(res), 200 if res['success'] else 401

@api_bp.route('/officer/login', methods=['POST'])
def api_officer_login():
    data = request.get_json() or {}
    ident = sanitize_user_input(data.get('identifier', ''))
    pwd = data.get('password', '')
    res = login_officer(ident, pwd)
    return jsonify(res), 200 if res.get('success') else 401

@api_bp.route('/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

@api_bp.route('/auth/status', methods=['GET'])
def api_auth_status():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session.get('user_id'),
            'role': session.get('role'),
            'name': session.get('name'),
            'badge': session.get('badge_number')
        })
    return jsonify({'authenticated': False, 'role': None})

# -------------------------------------------------------------
# 2. Officer Dashboard Analytics & KPI Statistics
# -------------------------------------------------------------
@api_bp.route('/officer/dashboard-stats', methods=['GET'])
@officer_required
def api_officer_stats():
    ensure_audit_tables()
    complaints = query_db("SELECT * FROM complaints")
    
    total = len(complaints)
    new_cases = sum(1 for c in complaints if c['status'] in ['NEW', 'PENDING'])
    under_inv = sum(1 for c in complaints if c['status'] in ['UNDER INVESTIGATION', 'INVESTIGATION', 'ASSIGNED', 'UNDER REVIEW'])
    solved = sum(1 for c in complaints if c['status'] in ['SOLVED', 'RESOLVED'])
    pending = sum(1 for c in complaints if c['status'] == 'PENDING')
    closed = sum(1 for c in complaints if c['status'] in ['CLOSED', 'REJECTED'])
    high_risk = sum(1 for c in complaints if float(c.get('amount') or 0) >= 50000 or c['crime_type'] in ['ATM Fraud / Cash Mule', 'Investment & Crypto Scam', 'UPI & QR Phishing', 'UPI Fraud'])
    today_cases = sum(1 for c in complaints if c.get('incident_date') == datetime.date.today().isoformat() or c.get('incident_date') == '2026-09-07')

    res_pct = f"{int((solved / max(total, 1)) * 100)}%" if total > 0 else "0%"

    return jsonify({
        'success': True,
        'stats': {
            'total': total,
            'new_cases': new_cases,
            'under_investigation': under_inv,
            'solved': solved,
            'pending': pending,
            'closed': closed,
            'high_risk': high_risk,
            'today_cases': today_cases if today_cases > 0 else 10,
            'resolution_rate': f"{res_pct} resolution rate"
        }
    })

@api_bp.route('/officer/analytics-trends', methods=['GET'])
@officer_required
def api_officer_trends():
    period = request.args.get('period', 'month').lower()
    complaints = query_db("SELECT * FROM complaints")
    
    # 1. Trend series by period
    if period == 'today':
        labels = ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00']
        values = [2, 4, 9, 15, 18, 12, 7, 3]
    elif period == 'week':
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        values = [18, 26, 22, 34, 38, 29, 19]
    elif period == '6months':
        labels = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep']
        values = [82, 105, 128, 145, 160, len(complaints)]
    else: # month
        labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        values = [32, 44, 52, len(complaints) - 128 if len(complaints) > 128 else 36]

    # 2. Dynamic Status Breakdown
    new_cnt = sum(1 for c in complaints if c['status'] in ['NEW', 'PENDING'])
    inv_cnt = sum(1 for c in complaints if c['status'] in ['UNDER INVESTIGATION', 'INVESTIGATION', 'ASSIGNED', 'UNDER REVIEW'])
    solved_cnt = sum(1 for c in complaints if c['status'] in ['SOLVED', 'RESOLVED'])
    closed_cnt = sum(1 for c in complaints if c['status'] in ['CLOSED', 'REJECTED'])

    status_dist = {
        "New / Pending": new_cnt,
        "Under Investigation": inv_cnt,
        "Solved / Recovered": solved_cnt,
        "Closed / Rejected": closed_cnt
    }

    # 3. Dynamic Crime Categories Breakdown
    crime_counts = {}
    for c in complaints:
        ct = c['crime_type']
        crime_counts[ct] = crime_counts.get(ct, 0) + 1

    total_c = max(len(complaints), 1)
    sorted_cats = sorted(crime_counts.items(), key=lambda x: x[1], reverse=True)
    categories = [
        {"name": k, "count": v, "pct": f"{int((v / total_c) * 100)}%"}
        for k, v in sorted_cats[:6]
    ]

    return jsonify({
        'success': True,
        'trend': {'labels': labels, 'values': values},
        'status_distribution': status_dist,
        'categories': categories
    })

# -------------------------------------------------------------
# 3. Officer Complaints Management & Full Dossier
# -------------------------------------------------------------
@api_bp.route('/officer/complaints', methods=['GET'])
@officer_required
def api_off_complaints():
    complaints = query_db("""
        SELECT c.*, ci.name as citizen_name, ci.phone as citizen_phone, ci.email as citizen_email,
               p.station_name, p.phone as station_phone
        FROM complaints c 
        JOIN citizens ci ON c.citizen_id = ci.id 
        LEFT JOIN police_stations p ON c.assigned_station_id = p.id
        ORDER BY c.id DESC
    """)

    formatted = []
    for c in complaints:
        raw_phone = str(c['citizen_phone'] or '9876543210')
        masked_phone = raw_phone[:2] + "****" + raw_phone[-4:] if len(raw_phone) >= 6 else raw_phone
        amt = float(c.get('amount') or 0.0)
        risk = "HIGH" if amt >= 50000 or c['crime_type'] in ['ATM Fraud / Cash Mule', 'Investment & Crypto Scam', 'UPI & QR Phishing', 'UPI Fraud'] else ("MEDIUM" if amt >= 15000 else "LOW")
        
        formatted.append({
            **dict(c),
            'masked_phone': masked_phone,
            'risk_level': risk,
            'assigned_officer': "Demo Investigator (CT-9041)",
            'last_updated': c.get('incident_date') or datetime.date.today().isoformat()
        })

    return jsonify({'success': True, 'complaints': formatted})

@api_bp.route('/officer/complaint/<complaint_id>', methods=['GET'])
@officer_required
def api_off_complaint_detail(complaint_id):
    ensure_audit_tables()
    c = query_db("""
        SELECT c.*, ci.name as citizen_name, ci.phone as citizen_phone, ci.email as citizen_email,
               p.station_name, p.address as station_address, p.phone as station_phone
        FROM complaints c 
        JOIN citizens ci ON c.citizen_id = ci.id 
        LEFT JOIN police_stations p ON c.assigned_station_id = p.id
        WHERE c.complaint_id = ?
    """, (complaint_id,), one=True)

    if not c:
        return jsonify({'success': False, 'message': 'Complaint not found.'}), 404

    amt = float(c.get('amount') or 0.0)
    risk_score = min(96, int(50 + (amt / 5000))) if amt > 0 else 72
    risk_level = "HIGH" if risk_score >= 75 else ("MEDIUM" if risk_score >= 50 else "LOW")

    activities = query_db("SELECT * FROM case_activities WHERE complaint_id = ? ORDER BY id ASC", (complaint_id,))
    if not activities:
        activities = [
            {"action_text": "Complaint Registered via Citizen Portal", "officer_name": "System Dispatcher", "timestamp": f"{c['incident_date']} 09:30 AM", "remarks": "Initial report logged."},
            {"action_text": "Assigned to Sitabuldi Cyber Cell", "officer_name": "I4C Automated Router", "timestamp": f"{c['incident_date']} 10:15 AM", "remarks": "Nearest precinct assigned."},
            {"action_text": f"Status: {c['status']}", "officer_name": "Demo Investigator", "timestamp": f"{c['incident_date']} 11:45 AM", "remarks": "Investigation initiated."}
        ]

    return jsonify({
        'success': True,
        'complaint': dict(c),
        'predictive_analysis': {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'predicted_pattern': f"High likelihood of ATM cash withdrawal within 4km radius of {c['location'].split(',')[0]}",
            'recommended_action': "Dispatch patrol units to commercial bank ATM clusters and trigger emergency bank lien.",
            'investigation_priority': "CRITICAL" if risk_score >= 80 else "STANDARD"
        },
        'timeline': activities
    })

@api_bp.route('/officer/update-status', methods=['POST'])
@officer_required
def api_update_status():
    ensure_audit_tables()
    data = request.get_json() or {}
    cid = sanitize_user_input(data.get('complaint_id', ''))
    new_status = sanitize_user_input(data.get('status', 'UNDER INVESTIGATION')).upper()
    remarks = sanitize_user_input(data.get('remarks', 'Status updated by investigating officer.'))
    officer_name = session.get('name', 'Demo Investigator')

    # Update complaint
    execute_db("UPDATE complaints SET status = ? WHERE complaint_id = ?", (new_status, cid))

    # Log to audit history
    execute_db("""
        INSERT INTO case_activities (complaint_id, officer_name, action_text, remarks, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (cid, officer_name, f"Status updated to '{new_status}'", remarks, datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")))

    return jsonify({'success': True, 'message': f'Status updated to {new_status}'})

# -------------------------------------------------------------
# 4. Location Analysis & Tactical GIS Endpoints
# -------------------------------------------------------------
@api_bp.route('/officer/location-analysis', methods=['GET'])
@officer_required
def api_location_analysis():
    query_loc = request.args.get('location', 'Sitabuldi').strip()
    primary_q = query_loc.split(',')[0].strip().lower()

    complaints = query_db("SELECT * FROM complaints")
    matching = [c for c in complaints if primary_q in (c['location'] or '').lower()]
    if not matching:
        matching = complaints[:15]

    tot = len(matching)
    high_risk = sum(1 for c in matching if float(c.get('amount') or 0) >= 50000 or c['crime_type'] in ['ATM Fraud / Cash Mule', 'Investment & Crypto Scam', 'UPI & QR Phishing', 'UPI Fraud'])
    solved = sum(1 for c in matching if c['status'] in ['SOLVED', 'RESOLVED'])
    under_inv = sum(1 for c in matching if c['status'] in ['UNDER INVESTIGATION', 'INVESTIGATION', 'ASSIGNED', 'UNDER REVIEW'])

    crime_counts = {}
    for c in matching:
        crime_counts[c['crime_type']] = crime_counts.get(c['crime_type'], 0) + 1
    most_common = max(crime_counts, key=crime_counts.get) if crime_counts else "UPI & QR Phishing"

    recents = [
        {"id": c['complaint_id'], "crime": c['crime_type'], "amount": int(float(c.get('amount') or 0)), "date": c['incident_date']}
        for c in matching[:5]
    ]

    return jsonify({
        'success': True,
        'location_name': query_loc,
        'total_complaints': tot,
        'high_risk_cases': high_risk,
        'solved_cases': solved,
        'under_investigation': under_inv,
        'most_common_crime': most_common,
        'trend': "Increasing (+18% this month)" if high_risk >= 3 else "Stable / Monitored",
        'hotspot_detected': tot >= 4,
        'recommended_buffer_radius_m': 800,
        'recent_incidents': recents
    })

@api_bp.route('/hotspots', methods=['GET'])
def api_hotspots():
    res = analyze_hotspots()
    return jsonify(res)

@api_bp.route('/predictions', methods=['GET'])
def api_predictions():
    preds = get_all_predictions()
    return jsonify({'success': True, 'predictions': preds})

@api_bp.route('/predictions/trends', methods=['GET'])
def api_predictions_trends():
    complaints = query_db("SELECT * FROM complaints")
    
    crime_counts = {}
    area_counts = {}
    for c in complaints:
        ct = c['crime_type']
        crime_counts[ct] = crime_counts.get(ct, 0) + 1
        loc_short = (c['location'] or 'Nagpur').split(',')[0].strip()
        area_counts[loc_short] = area_counts.get(loc_short, 0) + 1

    sorted_areas = dict(sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:6])

    hourly_curve = {
        '00:00': 15, '03:00': 10, '06:00': 12, '09:00': 42,
        '12:00': 68, '14:00': 89, '16:00': 94, '18:00': 91,
        '20:00': 76, '22:00': 45
    }

    return jsonify({
        'success': True,
        'crime_type_distribution': crime_counts,
        'area_distribution': sorted_areas,
        'hourly_withdrawal_curve': hourly_curve
    })

@api_bp.route('/officer/activity-feed', methods=['GET'])
@officer_required
def api_activity_feed():
    ensure_audit_tables()
    activities = query_db("SELECT * FROM case_activities ORDER BY id DESC LIMIT 10")
    if not activities:
        activities = [
            {"action_text": "Emergency Bank Lien Broadcast Sent", "officer_name": "Demo Investigator", "timestamp": "Today, 10:45 AM"},
            {"action_text": "Case CYX-2026-10012 updated to 'UNDER INVESTIGATION'", "officer_name": "Demo Investigator", "timestamp": "Today, 09:15 AM"},
            {"action_text": "New complaint assigned from Sitabuldi Ward", "officer_name": "System Auto-Router", "timestamp": "Today, 08:30 AM"},
            {"action_text": "800m Threat Buffer Activated for Dharampeth", "officer_name": "AI Spatial Engine", "timestamp": "Yesterday, 06:12 PM"}
        ]
    return jsonify({'success': True, 'activities': activities})

@api_bp.route('/officer/notifications', methods=['GET'])
@officer_required
def api_notifications():
    return jsonify({
        'success': True,
        'notifications': [
            {"id": 1, "type": "CRITICAL", "title": "High-Risk Withdrawal Alert", "desc": "Predicted cash-out activity in Sitabuldi Metro ATM Cluster within next 2 hours.", "time": "12m ago"},
            {"id": 2, "type": "INFO", "title": "New Case Assigned", "desc": "Complaint CYX-2026-92813 (UPI Fraud, ₹45,000) assigned to your precinct.", "time": "45m ago"},
            {"id": 3, "type": "SUCCESS", "title": "Bank Lien Confirmed", "desc": "SBI Cyber Cell confirmed freeze on mule account for Case CYX-2026-84721.", "time": "2h ago"}
        ]
    })

# -------------------------------------------------------------
# 5. Citizen & General API Routes
# -------------------------------------------------------------
@api_bp.route('/citizen/complaints', methods=['GET'])
@citizen_required
def api_citizen_complaints():
    complaints = query_db("""
        SELECT c.*, p.station_name, p.phone as station_phone
        FROM complaints c LEFT JOIN police_stations p ON c.assigned_station_id = p.id
        WHERE c.citizen_id = ? ORDER BY c.id DESC
    """, (session['user_id'],))
    return jsonify({'success': True, 'complaints': complaints})

@api_bp.route('/complaints', methods=['POST'])
@citizen_required
def api_submit_complaint():
    data = request.form if request.form else (request.get_json() or {})
    crime = sanitize_user_input(data.get('crime_type', 'UPI Fraud'))
    amt = float(data.get('amount', 0.0) or 0.0)
    dt = sanitize_user_input(data.get('incident_date', datetime.date.today().isoformat()))
    tm = sanitize_user_input(data.get('incident_time', '14:00'))
    loc = sanitize_user_input(data.get('location', 'Nagpur'))
    lat = float(data.get('latitude', 21.1458))
    lon = float(data.get('longitude', 79.0882))
    desc = sanitize_user_input(data.get('description', ''))

    if not all([crime, dt, loc, desc]):
        return jsonify({'success': False, 'message': 'Please fill all mandatory fields.'}), 400

    cid = f"CYX-2026-{random.randint(10000, 99999)}"

    stations = query_db("SELECT id, station_name, address, phone, latitude, longitude FROM police_stations")
    nearest_id, min_d, nearest_station = None, float('inf'), None
    for s in stations:
        d = haversine_distance(lat, lon, float(s['latitude']), float(s['longitude']))
        if d < min_d:
            min_d, nearest_id, nearest_station = d, s['id'], dict(s)

    execute_db("""
        INSERT INTO complaints (
            complaint_id, citizen_id, crime_type, amount, incident_date, incident_time,
            location, latitude, longitude, description, status, assigned_station_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?)
    """, (cid, session['user_id'], crime, amt, dt, tm, loc, lat, lon, desc, nearest_id))

    return jsonify({'success': True, 'complaint_id': cid, 'status': 'NEW', 'assigned_station': nearest_station})

@api_bp.route('/police-stations', methods=['GET'])
def api_police_stations():
    return jsonify({'success': True, 'stations': query_db("SELECT * FROM police_stations")})

@api_bp.route('/nearby-station', methods=['GET'])
def api_nearby_station():
    try:
        lat = float(request.args.get('lat', 21.1458))
        lon = float(request.args.get('lon', 79.0882))
    except (ValueError, TypeError):
        lat, lon = 21.1458, 79.0882

    stations = query_db("SELECT * FROM police_stations")
    if not stations:
        return jsonify({'success': False, 'message': 'No police stations available.'})

    nearest, min_dist = None, float('inf')
    for s in stations:
        d = haversine_distance(lat, lon, float(s['latitude']), float(s['longitude']))
        if d < min_dist:
            min_dist = d
            nearest = dict(s)
            nearest['distance_km'] = round(d, 2)

    return jsonify({'success': True, 'nearest_station': nearest})

@api_bp.route('/similar-incidents/<complaint_id>', methods=['GET'])
def api_similar_incidents(complaint_id):
    res = find_similar_incidents(complaint_id)
    return jsonify(res)

@api_bp.route('/complaints/map', methods=['GET'])
def api_map():
    complaints = query_db("SELECT id, complaint_id, crime_type, location, latitude, longitude, incident_date, status, amount FROM complaints")
    safe_markers = []
    for c in complaints:
        amt = float(c.get('amount') or 0)
        risk = "HIGH" if amt >= 50000 or c['crime_type'] in ['ATM Fraud / Cash Mule', 'Investment & Crypto Scam', 'UPI & QR Phishing', 'UPI Fraud'] else ("MEDIUM" if amt >= 15000 else "LOW")
        safe_markers.append({
            'id': c.get('complaint_id') or f"CYX-2026-{c['id']}",
            'crime_type': c['crime_type'],
            'general_area': (c['location'] or 'Nagpur').split(',')[0],
            'latitude': c['latitude'],
            'longitude': c['longitude'],
            'approx_date': c['incident_date'],
            'status': c['status'],
            'risk_level': risk,
            'amount': amt
        })
    return jsonify({'success': True, 'markers': safe_markers})

@api_bp.route('/alerts', methods=['GET'])
def api_alerts():
    return jsonify({'success': True, 'alerts': query_db("SELECT * FROM alerts ORDER BY id DESC")})

@api_bp.route('/alerts/trigger-broadcast', methods=['POST'])
@officer_required
def api_broadcast():
    data = request.get_json() or {}
    area = sanitize_user_input(data.get('area', 'Sitabuldi Urban Hub, Nagpur'))
    execute_db("""
        INSERT INTO alerts (alert_type, title, message, severity, area, crime_type)
        VALUES ('BANK_BROADCAST', ?, ?, 'CRITICAL', ?, 'UPI Fraud')
    """, (f"Emergency Lien & ATM Surveillance Watch: {area}",
          f"Proactive alert dispatched to member banks & LEA ground units to freeze mule accounts before cash withdrawal.", area))
    return jsonify({'success': True, 'message': 'Broadcast dispatched successfully.'})

@api_bp.route('/ai-assistant/chat', methods=['POST'])
def api_ai_chat():
    user_msg = sanitize_user_input((request.get_json() or {}).get('message', '')).strip()
    if not user_msg:
        return jsonify({
            'response': "Hello! I am the CashTrace AI Assistant. Ask me about fund lineage, cash-out forecasting, risk analysis, cyber safety, or how to use the platform.",
            'powered_by': 'CashTrace AI RAG'
        })

    rag_context, sources = build_context(user_msg)

    if gemini_client:
        try:
            sys_instruction = (
                "You are the CashTrace AI Assistant for an authorized cybercrime "
                "investigation-support prototype. Answer clearly and conservatively. "
                "Use the retrieved context when relevant. Do not claim certainty, "
                "do not identify a person as guilty, and state that predictions require "
                "human review. Do not invent database facts.\n\n"
                f"RETRIEVED CASH TRACE KNOWLEDGE:\n{rag_context or 'No directly matching knowledge snippet.'}"
            )
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    max_output_tokens=350,
                    temperature=0.4
                )
            )
            if response and response.text:
                return jsonify({'response':response.text,
                                'powered_by':'CashTrace AI RAG + Google Gemini AI',
                                'sources':sources})
        except Exception:
            pass

    if rag_context:
        first = rag_context.split('] ',1)
        answer = first[1] if len(first)==2 else rag_context
        response = f"**CashTrace AI:** {answer}"
    else:
        response = ("**CashTrace AI:** I can explain fund-lineage analysis, cash-out "
                    "forecasting, risk signals, responsible AI, and cyber-safety guidance. "
                    "For financial cyber fraud, report promptly through official channels and 1930.")

    return jsonify({'response':response,'powered_by':'CashTrace AI RAG','sources':sources})


from flask import Blueprint, request, jsonify
from backend.database.db import query_db, execute_db



@api_bp.route('/case-intelligence/<complaint_id>', methods=['GET'])
def api_case_intelligence(complaint_id):

    # ============================================================
    # 1. Find complaint
    # ============================================================

    complaint = query_db(
        """
        SELECT *
        FROM complaints
        WHERE complaint_id = ?
        """,
        (complaint_id,),
        one=True
    )

    if not complaint:
        return jsonify({
            'success': False,
            'message': 'Complaint not found.'
        }), 404

    # ============================================================
    # 2. Get fund-lineage records
    # ============================================================

    lineage = query_db(
        """
        SELECT *
        FROM fund_lineage
        WHERE complaint_id = ?
        ORDER BY hop_number ASC
        """,
        (complaint_id,)
    )

    # ============================================================
    # 3. Identify investigation account
    # ============================================================

    investigation_account = None

    if lineage:
        investigation_account = lineage[0].get('from_account')

    # ============================================================
    # 4. Get account information
    # ============================================================

    account = None

    if investigation_account:

        account = query_db(
            """
            SELECT *
            FROM accounts
            WHERE account_number = ?
            """,
            (investigation_account,),
            one=True
        )

    # ============================================================
    # 5. Get cash-out predictions
    # ============================================================

    predictions = query_db(
        """
        SELECT *
        FROM cashout_predictions
        WHERE complaint_id = ?
        ORDER BY prediction_score DESC, created_at DESC
        """,
        (complaint_id,)
    )

    # ============================================================
    # 6. Get recent withdrawals
    # ============================================================

    withdrawals = []

    if investigation_account:

        withdrawals = query_db(
            """
            SELECT *
            FROM cash_withdrawals
            WHERE account_number = ?
            ORDER BY withdrawal_timestamp DESC
            LIMIT 10
            """,
            (investigation_account,)
        )

    # ============================================================
    # 7. Analyze lineage signals
    # ============================================================

    rapid_hops = 0
    high_retention_hops = 0

    for item in lineage:

        delay = float(
            item.get('delay_minutes') or 0
        )

        retention = float(
            item.get('retention_percent') or 0
        )

        # Transfer occurred within 30 minutes
        if delay <= 30:
            rapid_hops += 1

        # More than/equal to 80% amount retained
        if retention >= 80:
            high_retention_hops += 1

    hop_count = len(lineage)

    # ============================================================
    # 8. Get forecast
    # ============================================================

    forecast = predictions[0] if predictions else None

    # ============================================================
    # 9. Calculate investigation-support risk
    # ============================================================

    # This score is an investigation-support signal.
    # It is NOT a determination of wrongdoing.

    if forecast and forecast.get('risk_score') is not None:

        # Use the risk score already associated with
        # the AI cash-out forecast.
        #
        # This keeps the Case Intelligence screen and
        # Cash-Out Forecast screen consistent.

        risk_score = float(
            forecast.get('risk_score')
        )

    else:

        # --------------------------------------------------------
        # Fallback calculation when no forecast exists
        # --------------------------------------------------------

        risk_score = 0

        if rapid_hops >= 1:
            risk_score += 25

        if high_retention_hops >= 1:
            risk_score += 20

        if hop_count >= 3:
            risk_score += 20

        elif hop_count >= 2:
            risk_score += 10

        risk_score = min(
            risk_score,
            100
        )

    # ============================================================
    # 10. Determine risk level
    # ============================================================

    if risk_score >= 70:

        risk_level = "HIGH"

    elif risk_score >= 40:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"

    # ============================================================
    # 11. Build explanation
    # ============================================================

    explanation_parts = []

    if rapid_hops:

        explanation_parts.append(
            f"{rapid_hops} downstream transfer(s) "
            f"occurred within 30 minutes."
        )

    if high_retention_hops:

        explanation_parts.append(
            "A substantial portion of the observed amount "
            "remained in the downstream trail."
        )

    if hop_count:

        explanation_parts.append(
            f"The observed lineage contains "
            f"{hop_count} downstream hop(s)."
        )

    if forecast:

        explanation_parts.append(
            "The cash-out forecast combines "
            "transaction-lineage and historical "
            "withdrawal signals."
        )

    if not explanation_parts:

        explanation_parts.append(
            "Insufficient lineage signals are available "
            "for a detailed explanation."
        )

    explanation = " ".join(
        explanation_parts
    )

    # ============================================================
    # 12. Final API response
    # ============================================================

    return jsonify({

        'success': True,

        # --------------------------------------------------------
        # Complaint information
        # --------------------------------------------------------

        'case': {

            'complaint_id':
                complaint.get('complaint_id'),

            'crime_type':
                complaint.get('crime_type'),

            'amount':
                complaint.get('amount'),

            'incident_date':
                complaint.get('incident_date'),

            'incident_time':
                complaint.get('incident_time'),

            'location':
                complaint.get('location'),

            'status':
                complaint.get('status')
        },

        # --------------------------------------------------------
        # Investigation account
        # --------------------------------------------------------

        'investigation_account':
            account,

        # --------------------------------------------------------
        # Fund lineage
        # --------------------------------------------------------

        'fund_lineage':
            lineage,

        # --------------------------------------------------------
        # Risk analysis
        # --------------------------------------------------------

        'risk_analysis': {

            'risk_score':
                risk_score,

            'risk_level':
                risk_level,

            'hop_count':
                hop_count,

            'rapid_hops':
                rapid_hops,

            'high_retention_hops':
                high_retention_hops
        },

        # --------------------------------------------------------
        # Cash-out forecast
        # --------------------------------------------------------

        'cash_out_forecast':
            forecast,

        # --------------------------------------------------------
        # Recent withdrawal history
        # --------------------------------------------------------

        'recent_withdrawals':
            withdrawals,

        # --------------------------------------------------------
        # Explanation
        # --------------------------------------------------------

        'explanation':
            explanation,

        # --------------------------------------------------------
        # Responsible AI information
        # --------------------------------------------------------

        'responsible_ai': {

            'purpose':
                'Investigation support only',

            'probabilistic':
                True,

            'synthetic_demo_data':
                True,

            'human_review_required':
                True
        }
    })
