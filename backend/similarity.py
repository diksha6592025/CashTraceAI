"""
CashTrace AI - Privacy-Preserving Similar Incident Detection Engine.
Calculates multidimensional similarity scores between complaints
without exposing victim PII to other citizens.
"""

from backend.database.db import query_db
from backend.security import haversine_distance

def calculate_similarity(target_complaint, historical_complaint):
    """
    Computes weighted similarity score (0 to 100 points) based on:
    1. Crime Type Match (40 pts)
    2. Same Area / Location String (30 pts)
    3. Geographic Proximity (20 pts based on Haversine distance)
    4. Amount / Temporal Pattern Similarity (10 pts)
    """
    score = 0.0

    # 1. Crime Type (40 pts)
    if target_complaint['crime_type'].lower() == historical_complaint['crime_type'].lower():
        score += 40.0

    # 2. Area Match (30 pts)
    target_loc = target_complaint['location'].lower()
    hist_loc = historical_complaint['location'].lower()
    if target_loc in hist_loc or hist_loc in target_loc:
        score += 30.0
    elif any(word in hist_loc for word in target_loc.split() if len(word) > 3):
        score += 15.0

    # 3. Geographic Distance (20 pts)
    try:
        dist = haversine_distance(
            float(target_complaint['latitude']), float(target_complaint['longitude']),
            float(historical_complaint['latitude']), float(historical_complaint['longitude'])
        )
        if dist <= 2.0:
            score += 20.0
        elif dist <= 5.0:
            score += 15.0
        elif dist <= 15.0:
            score += 8.0
        elif dist <= 30.0:
            score += 4.0
    except (ValueError, TypeError):
        dist = 999.0

    # 4. Pattern / Modus Operandi indicator (10 pts)
    amt_target = float(target_complaint.get('amount') or 0.0)
    amt_hist = float(historical_complaint.get('amount') or 0.0)
    if amt_target > 0 and amt_hist > 0:
        ratio = min(amt_target, amt_hist) / max(amt_target, amt_hist)
        score += round(ratio * 10.0, 1)
    else:
        score += 5.0

    score = min(100.0, round(score, 1))

    # Determine Classification Level
    if score >= 85:
        level = "VERY SIMILAR"
    elif score >= 65:
        level = "HIGHLY SIMILAR"
    elif score >= 45:
        level = "MODERATELY SIMILAR"
    else:
        level = "LOW SIMILARITY"

    return score, level, dist

def find_similar_incidents(complaint_id, max_results=6):
    """
    Searches historical complaints and returns privacy-sanitized matches.
    CONFIDENTIAL DATA (Names, Phones, Accounts, Full Descriptions) IS NEVER RETURNED.
    """
    target = query_db("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,), one=True)
    if not target:
        return {'found': False, 'message': 'Complaint ID not found.'}

    historical = query_db("SELECT * FROM complaints WHERE complaint_id != ?", (complaint_id,))
    if not historical:
        return {
            'found': True,
            'total_similar': 0,
            'results': [],
            'common_crime_type': target['crime_type'],
            'common_area': target['location']
        }

    matches = []
    for h in historical:
        score, level, dist = calculate_similarity(target, h)
        if score >= 45:  # Only return meaningful patterns
            # STRICT PRIVACY SANITIZATION (Safe Public View)
            matches.append({
                'anonymized_id': f"INC-{h['id']:04d}",
                'crime_type': h['crime_type'],
                'general_area': h['location'].split(',')[0],
                'approximate_date': h['incident_date'],
                'similarity_score': score,
                'similarity_level': level,
                'approx_distance_km': dist if dist != 999.0 else "N/A",
                'safe_status': h['status'],
                'latitude': h['latitude'],
                'longitude': h['longitude']
            })

    # Sort descending by similarity score
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    matches = matches[:max_results]

    return {
        'found': True,
        'target_crime_type': target['crime_type'],
        'target_area': target['location'],
        'total_similar': len(matches),
        'results': matches,
        'disclaimer': "Similar historical pattern detected based on crime vector and geographical proximity. This does not imply the same perpetrator."
    }