"""
CashTrace AI — Synthetic Demo Data Generator (SIH-26184)
Populates 160+ realistic cybercrime records, case activities, ATM locations,
police stations, AI predictions, and active alerts across Nagpur & Key Metros.
"""

import random
import datetime
from werkzeug.security import generate_password_hash
from backend.database.db import get_db_connection

def load_sample_data():
    """Populates realistic demo data for officers, citizens, police stations, complaints, activities, and predictions."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Seed Officers
    officers = [
        ('CT-9041', 'Demo Investigator', 'investigator.demo@cashtrace.local', 'Cyber Crime Cell', 'Nagpur Central & Vidarbha Zone', generate_password_hash('password123')),
        ('I4C-9042', 'ACP Priya Deshmukh', 'priya.deshmukh@mahapolice.gov.in', 'Financial Cyber Fraud Unit', 'Maharashtra Western Division', generate_password_hash('password123')),
        ('I4C-9043', 'DySP Amit Kulkarni', 'amit.kulkarni@i4c.gov.in', 'ATM Hotspot Intervention Wing', 'Delhi NCR & North Zone', generate_password_hash('password123')),
        ('I4C-9044', 'Inspector Sneha Patil', 'sneha.patil@cybercrime.gov.in', 'UPI & Phishing Taskforce', 'Nagpur South & Metro', generate_password_hash('password123')),
        ('I4C-9045', 'Sub-Inspector Vikram Rathore', 'vikram.rathore@cybercrime.gov.in', 'Rapid Action Cyber Dispatch', 'Nagpur East & Central', generate_password_hash('password123'))
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO officers (badge_number, name, email, department, jurisdiction, password_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, officers)

    # 2. Seed Citizens
    citizens_data = [
        ('Rahul Sharma', '9876543210', 'rahul.sharma@example.com', generate_password_hash('password123')),
        ('Pooja Deshpande', '9822314567', 'pooja.deshpande@example.com', generate_password_hash('password123')),
        ('Amit Verma', '9422890123', 'amit.verma@example.com', generate_password_hash('password123')),
        ('Neha Kulkarni', '9860123456', 'neha.kulkarni@example.com', generate_password_hash('password123')),
        ('Sanjay Mishra', '9765432109', 'sanjay.mishra@example.com', generate_password_hash('password123')),
        ('Deepak Raut', '9970112233', 'deepak.raut@example.com', generate_password_hash('password123')),
        ('Sunita Joshi', '9403887766', 'sunita.joshi@example.com', generate_password_hash('password123')),
        ('Aditya Iyer', '9890445566', 'aditya.iyer@example.com', generate_password_hash('password123')),
        ('Kavita Bawankar', '9730554433', 'kavita.b@example.com', generate_password_hash('password123')),
        ('Manish Agrawal', '9823001122', 'manish.agrawal@example.com', generate_password_hash('password123'))
    ]
    for c in citizens_data:
        cursor.execute("""
            INSERT OR IGNORE INTO citizens (name, phone, email, password_hash)
            VALUES (?, ?, ?, ?)
        """, c)

    # 3. Seed Police Stations
    police_stations = [
        ('Cyber Crime Police Station Sitabuldi', 'Tekdi Road, Sitabuldi, Nagpur, Maharashtra 440001', '0712-2561100', 21.1458, 79.0882, 'Sitabuldi, Sadar & Central Nagpur'),
        ('Dharampeth Police Station', 'West High Court Road, Dharampeth, Nagpur, Maharashtra 440010', '0712-2532200', 21.1396, 79.0601, 'Dharampeth, Gokulpeth & Shivaji Nagar'),
        ('Civil Lines Special Cyber Unit', 'Opposite High Court, Civil Lines, Nagpur, Maharashtra 440001', '0712-2565500', 21.1534, 79.0728, 'Civil Lines, Ramdaspeth & Seminary Hills'),
        ('Sonegaon & Wardha Road Cyber Desk', 'Wardha Road, Near Airport, Nagpur, Maharashtra 440025', '0712-2289100', 21.0921, 79.0624, 'Wardha Road, Sonegaon & Manish Nagar'),
        ('Sadar Police Station', 'Residency Road, Sadar, Nagpur, Maharashtra 440001', '0712-2533300', 21.1610, 79.0820, 'Sadar, Chaoni & Mankapur'),
        ('Kotwali Police Station Mahal', 'Gandhisagar Lake Road, Mahal, Nagpur, Maharashtra 440032', '0712-2724400', 21.1420, 79.1050, 'Mahal, Itwari & Gandhibagh'),
        ('BKC Cyber Police Station Mumbai', 'Bandra Kurla Complex, Bandra East, Mumbai 400051', '022-26504000', 19.0674, 72.8689, 'BKC & Mumbai Suburbs'),
        ('Connaught Place Cyber Cell Delhi', 'Barakhamba Road, Connaught Place, New Delhi 110001', '011-23746600', 28.6315, 77.2167, 'Central Delhi & CP Outer Circle'),
        ('Indiranagar Cyber Crime Station Bengaluru', '100 Feet Road, Indiranagar, Bengaluru, Karnataka 560038', '080-22942400', 12.9784, 77.6408, 'Indiranagar & East Bengaluru')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO police_stations (station_name, address, phone, latitude, longitude, jurisdiction_area)
        VALUES (?, ?, ?, ?, ?, ?)
    """, police_stations)

    # Ensure Case Activities Table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            officer_name TEXT NOT NULL,
            action_text TEXT NOT NULL,
            remarks TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. Generate 160+ Realistic Historical Complaints
    locations_pool = [
        ('Sitabuldi Market, Nagpur', 21.1460, 79.0885, 1),
        ('Sitabuldi Metro Plaza, Nagpur', 21.1455, 79.0879, 1),
        ('Tekdi Ganesh Road, Sitabuldi, Nagpur', 21.1470, 79.0890, 1),
        ('Sitabuldi Main Branch ATM Kiosk, Nagpur', 21.1452, 79.0880, 1),
        ('Sitabuldi Shopping Complex, Nagpur', 21.1465, 79.0875, 1),
        ('Munje Square, Sitabuldi, Nagpur', 21.1448, 79.0865, 1),
        
        ('Dharampeth WHC Road, Nagpur', 21.1402, 79.0610, 2),
        ('Gokulpeth Market, Dharampeth, Nagpur', 21.1385, 79.0592, 2),
        ('Dharampeth Extension, Nagpur', 21.1390, 79.0605, 2),
        ('Laxmi Nagar Square, Nagpur', 21.1275, 79.0655, 2),
        ('Bajaj Nagar, Nagpur', 21.1310, 79.0680, 2),
        ('Shivaji Nagar Park, Nagpur', 21.1425, 79.0550, 2),

        ('Civil Lines Court Complex, Nagpur', 21.1528, 79.0735, 3),
        ('Ramdaspeth Canal Road, Nagpur', 21.1350, 79.0760, 3),
        ('Seminary Hills Road, Nagpur', 21.1680, 79.0580, 3),
        ('VCA Stadium Area, Civil Lines, Nagpur', 21.1560, 79.0780, 3),

        ('Wardha Road Flyover Kiosk, Nagpur', 21.0950, 79.0650, 4),
        ('Manish Nagar Main Road, Nagpur', 21.0880, 79.0780, 4),
        ('Sonegaon Lake Area, Nagpur', 21.0980, 79.0540, 4),
        ('Chhatrapati Square, Wardha Rd, Nagpur', 21.1120, 79.0680, 4),
        ('IT Park Gayatri Nagar, Nagpur', 21.1240, 79.0510, 4),
        ('Khamla Market, Nagpur', 21.1160, 79.0610, 4),

        ('Sadar Residency Road, Nagpur', 21.1610, 79.0820, 5),
        ('Sadar Sadar Bazar, Nagpur', 21.1630, 79.0850, 5),
        ('Mankapur Ring Road, Nagpur', 21.1850, 79.0780, 5),
        ('Chaoni Square, Sadar, Nagpur', 21.1670, 79.0790, 5),
        ('Jaripatka Main Market, Nagpur', 21.1810, 79.1020, 5),

        ('Mahal Town Hall, Nagpur', 21.1420, 79.1050, 6),
        ('Gandhibagh Cloth Market, Nagpur', 21.1510, 79.1090, 6),
        ('Itwari Railway Station Road, Nagpur', 21.1560, 79.1180, 6),
        ('Nandanvan Colony, Nagpur', 21.1320, 79.1250, 6),

        ('BKC G-Block Financial Center, Mumbai', 19.0680, 72.8695, 7),
        ('Bandra Kurla Complex, Mumbai', 19.0665, 72.8675, 7),
        ('Connaught Place Inner Circle, New Delhi', 28.6320, 77.2175, 8),
        ('Connaught Place Outer Circle, New Delhi', 28.6308, 77.2155, 8),
        ('100 Feet Road, Indiranagar, Bengaluru', 12.9790, 77.6415, 9),
        ('Indiranagar Metro Station, Bengaluru', 12.9775, 77.6398, 9)
    ]

    crime_profiles = [
        ('UPI Fraud', 'Victim received fake QR code / payment request on phone.', 15000, 75000),
        ('UPI Fraud', 'Phishing call pretending to be electricity bill update with APK download.', 12000, 48000),
        ('ATM Fraud / Cash Mule', 'Rapid illicit ATM cash extraction noticed within 20 mins of fraud call.', 40000, 150000),
        ('Phishing & KYC SMS', 'Bank KYC suspension SMS containing fake net banking credential harvester link.', 25000, 95000),
        ('Investment & Crypto Scam', 'Telegram channel promising 300% daily returns on crypto arbitrage tasks.', 50000, 320000),
        ('Job & Task Scam', 'Fake part-time YouTube video liking task scam requiring security deposit.', 15000, 85000),
        ('Online Shopping Fraud', 'Counterfeit luxury apparel and electronic gadgets portal delivered dummy packet.', 5000, 35000),
        ('Remote Access APK Scam', 'Customer support imposter asked victim to install AnyDesk/QuickSupport tool.', 30000, 180000),
        ('Identity Theft & SIM Swap', 'Unauthorized duplicate eSIM issued; bank accounts wiped via OTP intercept.', 60000, 250000),
        ('Credit/Debit Card Fraud', 'Card cloning / skimming at local fuel pump / pos machine terminal.', 18000, 90000)
    ]

    statuses_pool = [
        'NEW', 'NEW', 'UNDER INVESTIGATION', 'UNDER INVESTIGATION', 'UNDER INVESTIGATION', 
        'SOLVED', 'SOLVED', 'SOLVED', 'PENDING', 'PENDING', 'CLOSED'
    ]

    complaints_data = []
    activities_data = []
    base_date = datetime.date(2026, 7, 15)
    
    cursor.execute("SELECT COUNT(*) FROM complaints")
    existing_count = cursor.fetchone()[0]

    if existing_count < 100:
        cursor.execute("DELETE FROM complaints")
        cursor.execute("DELETE FROM case_activities")

        random.seed(42)

        for idx in range(1, 165):
            cid = f"CYX-2026-{10000 + idx}"
            cit_id = (idx % len(citizens_data)) + 1
            
            loc_tuple = locations_pool[idx % len(locations_pool)]
            loc_name, base_lat, base_lon, station_id = loc_tuple
            
            lat = round(base_lat + random.uniform(-0.003, 0.003), 5)
            lon = round(base_lon + random.uniform(-0.003, 0.003), 5)

            crime_tuple = crime_profiles[idx % len(crime_profiles)]
            crime_name, desc_template, min_amt, max_amt = crime_tuple
            amt = float(random.randint(min_amt // 1000, max_amt // 1000) * 1000)

            day_offset = (idx * 54) // 165
            inc_date = (base_date + datetime.timedelta(days=day_offset)).isoformat()
            hour = random.randint(9, 21)
            minute = random.choice([0, 15, 30, 45])
            inc_time = f"{hour:02d}:{minute:02d}"

            st = random.choice(statuses_pool)
            if idx >= 155:
                inc_date = "2026-09-07"
                st = 'NEW'

            desc = f"{desc_template} Incident reported at {loc_name}. Defrauded sum: ₹{int(amt):,}."

            complaints_data.append((
                cid, cit_id, crime_name, amt, inc_date, inc_time,
                loc_name, lat, lon, desc, None, st, station_id
            ))

            activities_data.append((
                cid, "System Auto-Router", "Citizen Complaint Registered", "Report ingested via online portal and assigned to precinct.", f"{inc_date} 09:15 AM"
            ))
            if st in ['UNDER INVESTIGATION', 'SOLVED', 'CLOSED', 'PENDING']:
                activities_data.append((
                    cid, "Demo Investigator", "Investigation Initiated", "Subpoena issued to payment gateway / telecom operator.", f"{inc_date} 11:30 AM"
                ))
            if st in ['SOLVED', 'CLOSED']:
                activities_data.append((
                    cid, "Demo Investigator", "Case Resolved / Lien Successful", "Mule account frozen; recovery process initiated via 1930 portal.", f"{inc_date} 04:45 PM"
                ))

        cursor.executemany("""
            INSERT INTO complaints (
                complaint_id, citizen_id, crime_type, amount, incident_date, incident_time,
                location, latitude, longitude, description, evidence_file, status, assigned_station_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, complaints_data)

        cursor.executemany("""
            INSERT INTO case_activities (complaint_id, officer_name, action_text, remarks, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, activities_data)

    # 5. Seed High-Precision AI Risk Predictions
    predictions = [
        ('Sitabuldi Urban Hub, Nagpur', 'UPI & QR Phishing', 88, 'CRITICAL', 'Sitabuldi Metro Station & Tekdi Road ATMs', 'Next 7 Days',
         '["High density of reported QR phishing incidents (+44% surge this month)", "Fast cash mule withdrawal patterns within 1.5km radius of Munje Square", "Recurring peak activity between 14:00 and 19:30 hours", "Identical dummy merchant VPA handles detected across 12 complaints"]'),
        ('Dharampeth Commercial Zone, Nagpur', 'Investment & Telegram Scams', 72, 'HIGH', 'WHC Road & Gokulpeth Commercial ATMs', 'Next 7 Days',
         '["Surge in fake crypto investment and task fraud reports", "Frequent withdrawal hops across private bank kiosks", "Weekend velocity spikes targeting working professionals"]'),
        ('Wardha Road & Manish Nagar Corridor', 'ATM Mule Cash-Outs', 82, 'CRITICAL', 'Wardha Road Flyover & Manish Nagar Kiosks', 'Next 7 Days',
         '["Direct cash extraction within 25 minutes of phishing call", "Mule accounts operating in local retail ATM clusters", "Inter-district phone numbers linked to fraudulent transactions"]'),
        ('Civil Lines & Court Area, Nagpur', 'Phishing & KYC SMS Scams', 46, 'MEDIUM', 'Civil Lines Post Office & Bank Hub', 'Next 14 Days',
         '["Sporadic SMS phishing incidents targeting utility bill consumers", "Low physical withdrawal correlation; primarily digital wallet hops"]'),
        ('Sadar & Residency Road, Nagpur', 'Online Shopping & Job Scams', 62, 'HIGH', 'Residency Road Commercial Bank ATMs', 'Next 7 Days',
         '["Elevated complaints regarding deceptive promotional shopping domains", "Duplicate electronic gadget store scam patterns", "Recurring payment gateway manipulation"]'),
        ('Mahal & Itwari Market Hub, Nagpur', 'UPI & OTP Impersonation', 68, 'HIGH', 'Gandhisagar & Itwari Market ATMs', 'Next 7 Days',
         '["Merchant payment spoofing apps used in wholesale trade area", "Fake refund claims targeting small business owners"]'),
        ('Bandra Kurla Complex (BKC), Mumbai', 'Banking Fraud & SIM Swap', 84, 'CRITICAL', 'BKC G-Block & Bandra Station ATMs', 'Next 7 Days',
         '["High financial loss intensity (avg > ₹1,80,000 per complaint)", "Rapid mule account transfers occurring within 18 minutes of incident", "Cross-jurisdictional IP routing and VPN hopping observed"]'),
        ('Connaught Place, New Delhi', 'Card Skimming & OTP Fraud', 76, 'HIGH', 'Inner Circle Kiosks & Rajiv Chowk Metro ATMs', 'Next 7 Days',
         '["Weekend retail peak frequency correlation", "Skimming device alerts reported near fuel and retail outlets", "Subsequent off-hours cash extractions"]'),
        ('Indiranagar 100ft Road, Bengaluru', 'Rental & Remote Access Scams', 58, 'MEDIUM', 'Indiranagar Metro & CMH Road ATMs', 'Next 7 Days',
         '["Cluster of classified portal rental deposit frauds", "Remote desktop APK tools used to hijack banking credentials"]')
    ]
    cursor.execute("DELETE FROM risk_predictions")
    cursor.executemany("""
        INSERT INTO risk_predictions (
            area, crime_type, risk_score, risk_level, predicted_withdrawal_hotspot, forecast_period, reasons_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, predictions)

    # 6. Seed Actionable Emergency Alerts
    alerts = [
        ('WITHDRAWAL_HOTSPOT', 'High-Risk Cash Withdrawal Alert: Sitabuldi Metro Cluster',
         'Predictive analytics indicates 88% probability of illicit cash withdrawal activity at ATMs near Sitabuldi Metro within 4 hours of cyber fraud execution. I4C advises deploying surveillance teams.',
         'CRITICAL', 'Sitabuldi Urban Hub, Nagpur', 'UPI & QR Phishing'),
        ('RAPID_CLUSTER', 'Rapid UPI Fraud Surge Detected in Dharampeth & Sadar',
         '8 similar QR code refund scams reported within 48 hours. Common dummy merchant account flagged for immediate lien and freezing.',
         'HIGH', 'Dharampeth Commercial Zone, Nagpur', 'UPI Fraud'),
        ('MULE_ACCOUNT_ALERT', 'ATM Cash Mule Extraction Pattern Identified on Wardha Road',
         'Three consecutive high-value ATM withdrawals totaling ₹2,40,000 recorded within 35 minutes along Wardha Road corridor. Patrol units alerted.',
         'CRITICAL', 'Wardha Road & Manish Nagar Corridor', 'ATM Fraud / Cash Mule'),
        ('BANKING_ALERT', 'SIM Swap & High-Value Transfer Warning in BKC Hub',
         'Multiple unauthorized RTGS/NEFT hops detected originating from Mumbai BKC jurisdiction. Financial Cyber Fraud Reporting System alerted for instantaneous fund hold.',
         'HIGH', 'Bandra Kurla Complex (BKC), Mumbai', 'Banking Fraud')
    ]
    cursor.execute("DELETE FROM alerts")
    cursor.executemany("""
        INSERT INTO alerts (alert_type, title, message, severity, area, crime_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, alerts)

    conn.commit()
    conn.close()
    print("[OK] CashTrace AI Demo database populated with 160+ realistic complaints, audit logs, and predictions.")

if __name__ == '__main__':
    load_sample_data()