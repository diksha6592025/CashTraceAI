"""
CashTrace AI - Synthetic Transaction & Fund-Lineage Demo Data

Creates synthetic/anonymized data for demonstrating:

Complaint
    ↓
Transaction Trail
    ↓
Behavioral Risk
    ↓
Cash-Out Forecast

This generator is designed to be safe to run multiple times:
- Accounts use INSERT OR IGNORE
- ATM withdrawals use INSERT OR IGNORE
- Transactions use INSERT OR IGNORE
- Fund-lineage records are inserted only when the transaction does not
  already have a lineage record
- Predictions are replaced per complaint so duplicate predictions
  are not created
"""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "cyberx.db"

random.seed(42)


def generate_accounts(conn):
    """Create synthetic bank accounts."""

    cursor = conn.cursor()

    cities = [
        ("Nagpur", "Maharashtra"),
        ("Delhi", "Delhi"),
        ("Gurugram", "Haryana"),
        ("Noida", "Uttar Pradesh"),
        ("Mumbai", "Maharashtra"),
        ("Bengaluru", "Karnataka"),
    ]

    accounts = []

    for i in range(1, 101):

        account_id = f"ACC_{i:05d}"
        city, state = random.choice(cities)

        accounts.append(
            (
                account_id,
                f"Demo Account {i:03d}",
                random.choice(["Demo Bank", "Synthetic Bank"]),
                random.choice(["SAVINGS", "CURRENT"]),
                city,
                state,
                "VERIFIED",
            )
        )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO accounts
        (
            account_number,
            account_holder,
            bank_name,
            account_type,
            home_city,
            home_state,
            kyc_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        accounts,
    )

    print(f"[OK] Accounts checked/created: {len(accounts)}")


def generate_atm_withdrawals(conn):
    """Create synthetic ATM withdrawal records."""

    cursor = conn.cursor()

    atms = [
        ("ATM_001", "Nagpur", "Maharashtra", 21.1458, 79.0882),
        ("ATM_002", "Nagpur", "Maharashtra", 21.1396, 79.0601),
        ("ATM_003", "Delhi", "Delhi", 28.6315, 77.2167),
        ("ATM_004", "Gurugram", "Haryana", 28.4595, 77.0266),
        ("ATM_005", "Noida", "Uttar Pradesh", 28.6139, 77.2090),
        ("ATM_006", "Mumbai", "Maharashtra", 19.0760, 72.8777),
        ("ATM_007", "Bengaluru", "Karnataka", 12.9716, 77.5946),
        ("ATM_008", "Gurugram", "Haryana", 28.4700, 77.0300),
        ("ATM_009", "Noida", "Uttar Pradesh", 28.5700, 77.3200),
        ("ATM_010", "Delhi", "Delhi", 28.6500, 77.2300),
    ]

    withdrawals = []

    base_time = datetime(2026, 9, 10, 10, 0)

    for i in range(1, 81):

        account = f"ACC_{random.randint(1, 100):05d}"
        atm = random.choice(atms)

        withdrawal_time = base_time + timedelta(
            hours=random.randint(0, 150)
        )

        amount = random.choice(
            [5000, 8000, 10000, 15000, 20000, 25000, 30000, 40000]
        )

        withdrawals.append(
            (
                f"WD_{i:05d}",
                account,
                atm[0],
                amount,
                withdrawal_time.strftime("%Y-%m-%d %H:%M:%S"),
                atm[3],
                atm[4],
                atm[1],
                atm[2],
            )
        )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO cash_withdrawals
        (
            withdrawal_id,
            account_number,
            atm_id,
            amount,
            withdrawal_timestamp,
            latitude,
            longitude,
            city,
            state
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        withdrawals,
    )

    print(f"[OK] ATM withdrawal records checked/created: {len(withdrawals)}")


def generate_transaction_trails(conn):
    """
    Create synthetic 3-hop transaction chains.

    Example:

    Victim
       |
       v
    Account A
       |
       v
    Account B
       |
       v
    Account C
    """

    cursor = conn.cursor()

    complaints = cursor.execute(
        """
        SELECT complaint_id, amount
        FROM complaints
        ORDER BY id
        LIMIT 20
        """
    ).fetchall()

    transactions = []
    lineage = []

    transaction_number = 1

    for index, complaint in enumerate(complaints, start=1):

        complaint_id = complaint[0]
        reported_amount = float(complaint[1] or 10000)

        victim = f"ACC_{(index * 3) % 100 + 1:05d}"
        account_a = f"ACC_{(index * 3 + 1) % 100 + 1:05d}"
        account_b = f"ACC_{(index * 3 + 2) % 100 + 1:05d}"
        account_c = f"ACC_{(index * 3 + 3) % 100 + 1:05d}"

        start_time = datetime(2026, 9, 15, 9, 0) + timedelta(
            minutes=index * 5
        )

        chain = [
            (victim, account_a, reported_amount, 0),
            (account_a, account_b, reported_amount * 0.92, 1),
            (account_b, account_c, reported_amount * 0.84, 2),
        ]

        for sender, receiver, amount, hop in chain:

            timestamp = start_time + timedelta(
                minutes=hop * 15
            )

            tx_id = f"TX_{transaction_number:06d}"

            transactions.append(
                (
                    tx_id,
                    complaint_id,
                    sender,
                    receiver,
                    round(amount, 2),
                    "TRANSFER",
                    random.choice(["UPI", "IMPS", "NEFT"]),
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    100000,
                    100000 - amount,
                    50000,
                    50000 + amount,
                )
            )

            delay = 0 if hop == 0 else 15

            retention = (
                amount / reported_amount
            ) * 100

            lineage.append(
                (
                    complaint_id,
                    sender,
                    receiver,
                    tx_id,
                    hop + 1,
                    round(amount, 2),
                    delay,
                    round(retention, 2),
                    round(retention / 100, 4),
                )
            )

            transaction_number += 1

    # ---------------------------------------------------------
    # Insert transactions safely
    # ---------------------------------------------------------

    cursor.executemany(
        """
        INSERT OR IGNORE INTO transactions
        (
            transaction_id,
            complaint_id,
            sender_account,
            receiver_account,
            amount,
            transaction_type,
            channel,
            transaction_timestamp,
            sender_balance_before,
            sender_balance_after,
            receiver_balance_before,
            receiver_balance_after
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        transactions,
    )

    # ---------------------------------------------------------
    # Insert lineage ONLY if that transaction has no lineage yet
    # ---------------------------------------------------------

    inserted_lineage = 0

    for record in lineage:

        complaint_id = record[0]
        transaction_id = record[3]

        existing = cursor.execute(
            """
            SELECT id
            FROM fund_lineage
            WHERE complaint_id = ?
              AND transaction_id = ?
            LIMIT 1
            """,
            (complaint_id, transaction_id),
        ).fetchone()

        if existing:
            continue

        cursor.execute(
            """
            INSERT INTO fund_lineage
            (
                complaint_id,
                from_account,
                to_account,
                transaction_id,
                hop_number,
                amount,
                delay_minutes,
                retention_percent,
                lineage_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            record,
        )

        inserted_lineage += 1

    print(f"[OK] Transactions checked/created: {len(transactions)}")
    print(f"[OK] New fund-lineage records added: {inserted_lineage}")


def create_predictions(conn):
    """
    Create one synthetic cash-out forecast for each of the
    first three complaint trails.

    The prediction account is automatically obtained from the
    first lineage hop instead of being manually hardcoded.
    """

    cursor = conn.cursor()

    complaint_ids = [
        "CYX-2026-10001",
        "CYX-2026-10002",
        "CYX-2026-10003",
    ]

    prediction_details = {
        "CYX-2026-10001": (
            "ATM_004",
            "Gurugram",
            "Haryana",
            0.87,
            "IMMEDIATE_0_60_MIN",
            0.82,
            78,
            "High transaction velocity, rapid fund forwarding, and geographic ATM activity indicate elevated cash-out risk.",
        ),
        "CYX-2026-10002": (
            "ATM_003",
            "Delhi",
            "Delhi",
            0.74,
            "SOON_1_6_HOURS",
            0.76,
            64,
            "Recent incoming funds followed by multiple transfers indicate a need for monitoring.",
        ),
        "CYX-2026-10003": (
            "ATM_005",
            "Noida",
            "Uttar Pradesh",
            0.69,
            "LATER_6_PLUS_HOURS",
            0.63,
            52,
            "Historical transaction behavior and ATM proximity contribute to the prediction.",
        ),
    }

    inserted = 0

    for complaint_id in complaint_ids:

        # Find the actual investigation account from lineage
        lineage_row = cursor.execute(
            """
            SELECT from_account
            FROM fund_lineage
            WHERE complaint_id = ?
            ORDER BY hop_number ASC
            LIMIT 1
            """,
            (complaint_id,),
        ).fetchone()

        if not lineage_row:
            print(
                f"[WARN] No lineage found for {complaint_id}; "
                "prediction skipped."
            )
            continue

        investigation_account = lineage_row[0]

        (
            atm,
            city,
            state,
            prediction_score,
            urgency,
            urgency_confidence,
            risk_score,
            explanation,
        ) = prediction_details[complaint_id]

        # Remove older prediction for this complaint.
        cursor.execute(
            """
            DELETE FROM cashout_predictions
            WHERE complaint_id = ?
            """,
            (complaint_id,),
        )

        cursor.execute(
            """
            INSERT INTO cashout_predictions
            (
                complaint_id,
                account_number,
                predicted_atm,
                predicted_city,
                predicted_state,
                prediction_score,
                urgency,
                urgency_confidence,
                risk_score,
                explanation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                complaint_id,
                investigation_account,
                atm,
                city,
                state,
                prediction_score,
                urgency,
                urgency_confidence,
                risk_score,
                explanation,
            ),
        )

        inserted += 1

        print(
            f"[OK] Prediction linked: "
            f"{complaint_id} -> {investigation_account}"
        )

    print(f"[OK] Predictions created/updated: {inserted}")


def main():

    print("=" * 60)
    print("CASH TRACE AI - SYNTHETIC DATA GENERATOR")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    try:

        generate_accounts(conn)

        generate_atm_withdrawals(conn)

        generate_transaction_trails(conn)

        create_predictions(conn)

        conn.commit()

        print("=" * 60)
        print("[SUCCESS] CashTrace demo data loaded successfully.")
        print("[INFO] Data is synthetic/anonymized for prototype demonstration.")
        print("=" * 60)

    except Exception as e:

        conn.rollback()

        print(f"[ERROR] {e}")

        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()