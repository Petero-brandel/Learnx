import os
import hmac
import hashlib
import requests
from django.conf import settings

PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

def initialize_transaction(email, amount_in_kobo, reference):
    """
    Initializes a Paystack transaction and returns the authorization URL.
    """
    if not PAYSTACK_SECRET_KEY:
        return None

    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "amount": amount_in_kobo,
        "reference": reference,
        "callback_url": f"{FRONTEND_URL.rstrip('/')}/dashboard"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()['data']['authorization_url']
    except requests.RequestException:
        return None
    return None

def verify_signature(payload_body, signature_header):
    """
    Verifies that the incoming webhook is genuinely from Paystack.
    """
    secret = PAYSTACK_SECRET_KEY.encode('utf-8')
    hash = hmac.new(secret, payload_body, hashlib.sha512).hexdigest()
    return hash == signature_header

def verify_transaction(reference):
    """
    Verifies a transaction via Paystack's API.
    Returns the transaction data if successful, None otherwise.
    """
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('status') == 'success':
                return data['data']
    except requests.RequestException:
        return None
    return None

