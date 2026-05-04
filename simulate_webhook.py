import os
import sys
import hmac
import hashlib
import json
import requests
from dotenv import load_dotenv

# Load env variables from .env to get PAYSTACK_SECRET_KEY
load_dotenv()
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')

def simulate(reference):
    print(f"Simulating Paystack webhook for reference: {reference}")
    url = "http://localhost:8000/api/payments/webhook/paystack/"
    
    payload = {
        "event": "charge.success",
        "data": {
            "reference": reference,
            "id": 123456789,
            "status": "success"
        }
    }
    
    payload_body = json.dumps(payload).encode('utf-8')
    secret = PAYSTACK_SECRET_KEY.encode('utf-8')
    signature = hmac.new(secret, payload_body, hashlib.sha512).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "x-paystack-signature": signature
    }
    
    try:
        response = requests.post(url, data=payload_body, headers=headers)
        if response.status_code == 200:
            print("Webhook simulated successfully. User should now be enrolled.")
        else:
            print(f"Failed to simulate webhook. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error simulating webhook: {str(e)}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python simulate_webhook.py <reference>")
        sys.exit(1)
    
    simulate(sys.argv[1])
