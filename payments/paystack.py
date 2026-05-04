import os
import hmac
import hashlib
import requests
from django.conf import settings

def initialize_transaction(email, amount_in_kobo, reference):
    """
    Initializes a Paystack transaction and returns the authorization URL.
    """
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY', '')
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "amount": amount_in_kobo,
        "reference": reference,
        "callback_url": f"{frontend_url}/dashboard"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['authorization_url']
    else:
        print("Paystack Error:", response.text)
    return None

def verify_signature(payload_body, signature_header):
    """
    Verifies that the incoming webhook is genuinely from Paystack.
    """
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY', '')
    secret = secret_key.encode('utf-8')
    hash = hmac.new(secret, payload_body, hashlib.sha512).hexdigest()
    return hash == signature_header

def verify_transaction(reference):
    """
    Verifies a Paystack transaction directly with the API.
    """
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY', '')
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json().get('data', {})
        if data.get('status') == 'success':
            return True, data
    return False, None
