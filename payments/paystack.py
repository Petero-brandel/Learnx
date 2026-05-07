import os
import hmac
import hashlib
import requests
from django.conf import settings

PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')

def initialize_transaction(email, amount_in_kobo, reference):
    """
    Initializes a Paystack transaction and returns the authorization URL.
    """
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    payload = {
        "email": email,
        "amount": amount_in_kobo,
        "reference": reference,
        "callback_url": f"{frontend_url}/dashboard"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['authorization_url']
    return None

def verify_signature(payload_body, signature_header):
    """
    Verifies that the incoming webhook is genuinely from Paystack.
    """
    secret = PAYSTACK_SECRET_KEY.encode('utf-8')
    hash = hmac.new(secret, payload_body, hashlib.sha512).hexdigest()
    return hash == signature_header

def verify_payment_status(reference):
    """
    Calls Paystack to verify the status of a transaction.
    """
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None
