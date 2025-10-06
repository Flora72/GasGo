import requests
from decouple import config
from datetime import datetime
import base64

# Safaricom Daraja credentials from .env
CONSUMER_KEY = config('MPESA_CONSUMER_KEY')
CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET')
SHORTCODE = config('MPESA_SHORTCODE')
PASSKEY = config('MPESA_PASSKEY')
CALLBACK_URL = config('MPESA_CALLBACK_URL')

# Endpoint URLs
ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox')

BASE_URL = 'https://sandbox.safaricom.co.ke' if ENVIRONMENT == 'sandbox' else 'https://api.safaricom.co.ke'

TOKEN_URL = f'{BASE_URL}/oauth/v1/generate?grant_type=client_credentials'
STK_PUSH_URL = f'{BASE_URL}/mpesa/stkpush/v1/processrequest'

def get_access_token():
    response = requests.get(TOKEN_URL, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    access_token = response.json().get('access_token')
    return access_token

def initiate_stk_push(phone_number, amount, account_reference):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((SHORTCODE + PASSKEY + timestamp).encode()).decode()

    headers = {
        'Authorization': f'Bearer {get_access_token()}',
        'Content-Type': 'application/json'
    }

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": "GasGo Payment"
    }

    response = requests.post(STK_PUSH_URL, json=payload, headers=headers)
    return response.json()
