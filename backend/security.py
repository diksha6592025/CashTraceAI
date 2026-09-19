"""
Security and Privacy Enforcement Utilities for CashTrace AI.
Ensures PII protection, strict file validation, and input sanitization.
"""

import math
import os
import re
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    """Verifies file extension against authorized extensions."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def sanitize_user_input(text):
    """Basic sanitization of user text input."""
    if not text:
        return ""
    # Strip dangerous HTML/script tags
    clean = re.sub(r'<[^>]*?>', '', str(text))
    return clean.strip()

def mask_phone(phone):
    """Masks phone number for privacy (e.g. 9876543210 -> 987****210)."""
    if not phone or len(str(phone)) < 6:
        return "******"
    p = str(phone)
    return p[:3] + "****" + p[-3:]

def mask_email(email):
    """Masks email address for privacy (e.g. rahul.sharma@example.com -> r***a@example.com)."""
    if not email or '@' not in email:
        return "****@***.com"
    parts = email.split('@')
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[0] + "***" + user[-1]
    return f"{masked_user}@{domain}"

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates great-circle distance between two geographic coordinates in Kilometers.
    Formula: Haversine
    """
    R = 6371.0  # Earth radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return round(distance, 2)