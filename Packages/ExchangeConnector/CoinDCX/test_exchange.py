import hmac
import hashlib
import requests
import base64
import time
import json
from datetime import datetime, timedelta, timezone


def get_balance_for_currency(api_key, api_secret, target_currency='INR'):
    secret_bytes = bytes(api_secret, encoding='utf-8')
    # Generating a timestamp
    timeStamp = int(round(time.time() * 1000))

    body = {
        "timestamp": timeStamp
    }

    json_body = json.dumps(body, separators = (',', ':'))

    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    url = "https://api.coindcx.com/exchange/v1/users/balances"

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': api_key,
        'X-AUTH-SIGNATURE': signature
    }

    response = requests.post(url, data = json_body, headers = headers)
    data = response.json();
    filtered_data = [entry for entry in data if entry['currency'] == target_currency]

    if not filtered_data:
        # return f"No data found for currency: {target_currency}"
        balance = 0
    else:
        # Extract balance for the specified currency
        balance = float(filtered_data[0]['balance'])
    return balance


def get_order_status(id, api_key, api_secret, max_retries=3):
    
    return "filled"
    
    
def update_price(symbol, id, side, api_key, api_secret):
  
    secret_bytes = bytes(api_secret, encoding='utf-8')

    timeStamp = int(round(time.time() * 1000))
    
    if side == "sell":
        new_price = priceFinder.get_bid_price(symbol)
    elif side == "buy":
        new_price = priceFinder.get_ask_price(symbol)
        
    body = {
          "id": id, # Enter your Order ID here.
          "timestamp": timeStamp,
          "price_per_unit": new_price
        }

    json_body = json.dumps(body, separators = (',', ':'))

    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    url = "https://api.coindcx.com/exchange/v1/orders/edit"

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': api_key,
        'X-AUTH-SIGNATURE': signature
    }

    response = requests.post(url, data = json_body, headers = headers)
    data = response.json()
    return(data)



def get_fee_collected(id, api_key, api_secret):
    secret_bytes = bytes(api_secret, encoding='utf-8')


    # Generating a timestamp.
    timeStamp = int(round(time.time() * 1000))

    body = {
      "id": id, # Enter your Order ID here.
      # "client_order_id": "2022.02.14-btcinr_1", # Enter your Client Order ID here.
      "timestamp": timeStamp
    }
    json_body = json.dumps(body, separators = (',', ':'))

    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    url = "https://api.coindcx.com/exchange/v1/orders/status"

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': api_key,
        'X-AUTH-SIGNATURE': signature
    }

    response = requests.post(url, data = json_body, headers = headers)
    data = response.json()
    # print(data)
    return(float(data["fee_amount"]))

def place_market_order(api_key, api_secret, symbol, side, order_type="MARKET", quantity=0, price = 0, max_retries=3):
    fees = price * quantity * 0.005
    payload = {
               "orders":[
                 {
                    "id":"TEST_ID",
                    "client_order_id": "TEST_CID",
                    "market":symbol,
                    "order_type":order_type,
                    "side":side,
                    "status":"filled",
                    "fee_amount":fees,
                    "fee":0.1,
                    "total_quantity":quantity,
                    "remaining_quantity":0,
                    "avg_price":price,
                    "price_per_unit":price,
                    "created_at":"CREATE_DATE",
                    "updated_at":"UPDATE_DATE"
                 }
               ]
            }
    
    return payload
    