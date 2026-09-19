-- CashTrace AI Relational Database Schema
-- SIH-26184 Cybercrime Predictive Analytics & Citizen Safety Platform

DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS risk_predictions;
DROP TABLE IF EXISTS complaints;
DROP TABLE IF EXISTS police_stations;
DROP TABLE IF EXISTS officers;
DROP TABLE IF EXISTS citizens;

-- 1. Citizens Table
CREATE TABLE citizens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Law Enforcement Officers Table
CREATE TABLE officers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    badge_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Police Stations Table
CREATE TABLE police_stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    jurisdiction_area TEXT NOT NULL
);

-- 4. Complaints Table
CREATE TABLE complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id TEXT NOT NULL UNIQUE,
    citizen_id INTEGER NOT NULL,
    crime_type TEXT NOT NULL,
    amount REAL DEFAULT 0.0,
    incident_date TEXT NOT NULL,
    incident_time TEXT NOT NULL,
    location TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    description TEXT NOT NULL,
    evidence_file TEXT,
    status TEXT DEFAULT 'PENDING',
    assigned_station_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citizen_id) REFERENCES citizens(id),
    FOREIGN KEY (assigned_station_id) REFERENCES police_stations(id)
);

-- 5. AI Risk Predictions Table
CREATE TABLE risk_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT NOT NULL,
    crime_type TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    predicted_withdrawal_hotspot TEXT NOT NULL,
    forecast_period TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Alerts & Actionable Interventions Table
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,
    area TEXT NOT NULL,
    crime_type TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CASH TRACE AI EXTENSION
-- Transaction & Fund-Lineage Intelligence
-- ============================================================

-- 7. Bank Accounts
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL UNIQUE,
    account_holder TEXT,
    bank_name TEXT,
    account_type TEXT,
    home_city TEXT,
    home_state TEXT,
    kyc_status TEXT DEFAULT 'VERIFIED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Financial Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL UNIQUE,
    complaint_id TEXT,
    sender_account TEXT NOT NULL,
    receiver_account TEXT NOT NULL,
    amount REAL NOT NULL,
    transaction_type TEXT,
    channel TEXT,
    transaction_timestamp TIMESTAMP NOT NULL,
    sender_balance_before REAL,
    sender_balance_after REAL,
    receiver_balance_before REAL,
    receiver_balance_after REAL,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
);

-- 9. Cash Withdrawal Events
CREATE TABLE IF NOT EXISTS cash_withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    withdrawal_id TEXT NOT NULL UNIQUE,
    account_number TEXT NOT NULL,
    atm_id TEXT NOT NULL,
    amount REAL NOT NULL,
    withdrawal_timestamp TIMESTAMP NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    city TEXT,
    state TEXT
);

-- 10. Fund-Lineage Links
CREATE TABLE IF NOT EXISTS fund_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id TEXT NOT NULL,
    from_account TEXT NOT NULL,
    to_account TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    hop_number INTEGER NOT NULL,
    amount REAL NOT NULL,
    delay_minutes REAL,
    retention_percent REAL,
    lineage_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. AI Cash-Out Predictions
CREATE TABLE IF NOT EXISTS cashout_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id TEXT,
    account_number TEXT NOT NULL,
    predicted_atm TEXT NOT NULL,
    predicted_city TEXT,
    predicted_state TEXT,
    prediction_score REAL NOT NULL,
    urgency TEXT,
    urgency_confidence REAL,
    risk_score REAL,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
