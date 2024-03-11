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
    
    retries = 0
    while retries <= max_retries:
        # Parse the response
        try:
            secret_bytes = bytes(api_secret, encoding='utf-8')
            # Generating a timestamp
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

            if data:
                # Extract balance for the specified currency
                status = data['status']
            else:                
                # return f"No data found for currency: {target_currency}"
                print(f"No status received for order id: {id}")
                status = 'Failed'
                # return status
            
            if status == "filled":
                break
            elif status == "partially_cancelled":
                print(f"Partially cancelled order - Rechecking in 10 seconds...")
                time.sleep(10)
                retries += 1
            elif status == "open":
                print(f"Order still open - Rechecking in 60 seconds...")
                time.sleep(60)
                retries += 1
            elif status == "partially_filled":
                print(f"Partially filled order - Rechecking in 20 seconds...")
                time.sleep(20)
                retries += 1
            elif status == "cancelled":
                print(f"Order : {id} has been cancelled.")
                break
            elif status == "rejected":
                print(f"Order : {id} has been rejected.")
                break
            elif status == "Failed":
                print(f"Failed to get status of Order : {id} ")
                break
            else:
                print(f"Unknown error for Order: {id}   || Status Received: {status} ")
                break
                
        except json.JSONDecodeError:
            print("Unable to decode JSON response - Exiting retry loop.")
            break
        
    return status
    
    
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
    base_url = "https://api.coindcx.com/exchange"
    endpoint = "/v1/orders/create"
    url = f"{base_url}{endpoint}"        

    secret_bytes = bytes(api_secret, encoding='utf-8')

    # Generating a timestamp.
    timeStamp = int(round(time.time() * 1000))

    client_order_id = f"{side}-{timeStamp}-{symbol}"

    # Request payload
    
    if order_type == "LIMIT":
        payload = {
            "side": side,  # "buy" or "sell"
            "order_type": "limit_order",
            "market": symbol,
            "price_per_unit": price, #This parameter is only required for a 'limit_order'
            "total_quantity": quantity,
            "timestamp": timeStamp,
            "client_order_id": client_order_id
        }
    else:
        payload = {
            "side": side,  # "buy" or "sell"
            "order_type": "market_order",
            "market": symbol,
            "total_quantity": quantity,
            "timestamp": timeStamp,
            "client_order_id": client_order_id
        }
    
    # print(payload)

    # Convert payload to JSON
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print(payload_json)

    # Create the signature
    signature = hmac.new(secret_bytes, payload_json.encode(), hashlib.sha256).hexdigest()

    # Headers
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': api_key,
        'X-AUTH-SIGNATURE': signature
    }

    retries = 0
    while retries <= max_retries:
        # Make the API request
        response = requests.post(url, data=payload_json, headers=headers)
        # Parse the response
        try:
            response_data = response.json()
            print("\n")
            print(response_data)
            print("\n")
            if response.status_code == 200:
                orderId = response_data["orders"][0]["id"]
                print(f"Order placed successfully! \n Order id: {orderId}")
                break
            elif response.status_code == 500:
                print(f"Internal Server Error (500) - Retrying in 10 seconds...")
                time.sleep(10)
                retries += 1
            else:
                handle_error_response(response.status_code, response_data)
                break
        except json.JSONDecodeError:
            print("Unable to decode JSON response - Exiting retry loop.")
            break

    if retries > max_retries:
        print(f"Max retries ({max_retries}) reached. Exiting.")
        
    return response_data
    
def handle_error_response(status_code, response_data):
    error_message = response_data.get('message', 'Unknown error')
    if status_code == 400:
        print(f"Bad Request :: Your request is invalid: {error_message}")
    elif status_code == 401:
        print(f"Unauthorized Error: {error_message}")
    elif status_code == 404:
        print(f"Not Found Error: {error_message}")
    elif status_code == 429:
        print(f"Too Many Requests Error: {error_message}")
    elif status_code == 500:
        print(f"Internal Server Error: {error_message}")
    elif status_code == 503:
        print(f"Service Unavailable Error: {error_message}")
    else:
        print(f"Unhandled Error - Status Code: {status_code}, Response: {response_data}")
    
    sys.exit(130)
    