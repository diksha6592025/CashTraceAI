# CashTrace AI — Predictive Fund-Lineage & Cash-Out Intelligence System

## 🚀 Live Prototype

🌐 **Live Demo:** https://cashtraceai-1.onrender.com/

> CashTrace AI is a prototype for predictive fund-lineage analysis,
> risk assessment, and cash-out location forecasting.

## Project Overview
CashTrace AI is an investigation-support prototype for SIH 2026 Problem Statement 26184. It connects a cybercrime case with authorized transaction records, probable fund-flow lineage, behavioral risk signals, cash-out forecasting, GIS context, explainable guidance, and investigator review.

> **Report Smart. Detect Patterns. Trace the Flow. Prevent Loss.**

## SIH 2026 Context
- **Problem Statement:** 26184
- **Organization:** Ministry of Home Affairs (MHA)
- **Department:** Indian Cyber Crime Coordination Centre (I4C), CIS Division
- **Category:** Software
- **Theme:** Blockchain & Cybersecurity

## Core Intelligence Flow
```text
Cybercrime Complaint → Investigation Account → Authorized Transactions
→ Probable Fund-Lineage Graph → Behavioral Risk → Cash-Out Forecast
→ Likely ATM / Location / Time Window → GIS + Alert → Investigator Review
```

## Main Modules
- Case Intake and Complainant Access
- Case Management and Investigation Console
- Probable Fund-Lineage / Money-Trail View
- Transaction Timeline
- Behavioral Risk Assessment
- Cash-Out Forecast
- GIS / Hotspot Analysis
- Alert and Investigator Action Center
- CashTrace Intelligence with RAG-grounded guidance
- Responsible AI, privacy, and human-review safeguards

## Technology Stack
| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.10+ / Flask 3.0 | REST API and server |
| Database | SQLite | Prototype data store |
| Frontend | HTML5, CSS3, Vanilla JavaScript | Responsive web UI |
| GIS | Leaflet.js | Maps and location analysis |
| Charts | Chart.js | Analytics visualization |
| Security | Werkzeug, sessions, input sanitization | Authentication / protection |
| AI guidance | Google GenAI (optional) + local RAG | Grounded assistance |
| Analytics | Pandas, NumPy, Scikit-learn | ML / analytics compatibility |

## Installation — Windows PowerShell
```powershell
cd "C:\path\to\CashTraceAI"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_project.py
```
Open **http://127.0.0.1:8000**. If `.venv` already exists, do not recreate it.

## Responsible AI and Limitations
The bundled account, transaction, withdrawal, lineage, and prediction records are synthetic/anonymized prototype data. Forecasts are probabilistic investigation-support signals and require authorized human review. They are not proof of guilt or guaranteed outcomes.

Money is fungible; the displayed lineage represents **probable fund-flow provenance**, not proof that identical physical currency moved through every hop. Branching flows and incomplete records can affect reliability.

## Demo Complainant Access
- Email: `citizen.demo@cashtrace.local`
- Password: `password123`

Do not use the demo password in production.
