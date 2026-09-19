"""
CashTrace AI - lightweight Retrieval-Augmented Guidance layer.
Prototype keyword retrieval for cyber-safety, fund-lineage, prediction,
risk analysis, and responsible-AI guidance.
"""

KNOWLEDGE = [
    {"title":"CashTrace AI: Fund-Lineage Intelligence",
     "keywords":["fund","lineage","money trail","transaction","hop","flow"],
     "text":"CashTrace AI reconstructs a probable fund-flow lineage from authorized transaction records. A lineage represents observed transaction links; it does not prove the physical movement of specific currency."},
    {"title":"Cash-Out Forecasting",
     "keywords":["atm","cash","withdrawal","cash-out","hotspot","forecast","predict"],
     "text":"The prototype combines transaction-lineage signals, historical withdrawal patterns, account behavior, and location signals to estimate likely cash-out locations and an intervention time window. Predictions are probabilistic and require investigator review."},
    {"title":"Risk Analysis",
     "keywords":["risk","score","velocity","retention","rapid","behavior"],
     "text":"Risk signals can include rapid downstream transfers, transaction velocity, retained value across hops, and historical cash-withdrawal behavior. A risk score is an investigation-support signal, not a finding of guilt."},
    {"title":"Responsible AI",
     "keywords":["responsible","privacy","ethics","fairness","human","review","bias"],
     "text":"CashTrace AI is designed for authorized investigation support. Human review is required before enforcement action. Data minimization, access control, privacy protection, auditability, and awareness of model limitations are essential."},
    {"title":"Cyber-Safety Response",
     "keywords":["upi","scam","fraud","otp","pin","1930","complaint"],
     "text":"Never share an OTP, UPI PIN, password, or card security code. For a financial cyber-fraud incident in India, report promptly through official cybercrime reporting channels and the 1930 helpline."},
]

def retrieve_context(query, limit=3):
    q=(query or "").lower()
    scored=[]
    for item in KNOWLEDGE:
        score=sum(1 for k in item["keywords"] if k in q)
        if score: scored.append((score,item))
    scored.sort(key=lambda x:x[0], reverse=True)
    return [item for _,item in scored[:limit]]

def build_context(query, limit=3):
    items=retrieve_context(query,limit)
    return "\n\n".join(f"[{x['title']}] {x['text']}" for x in items), [x["title"] for x in items]
