import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import pytz


ist_tz = pytz.timezone('Asia/Kolkata')

# Get current IST time
now_ist = datetime.now(ist_tz)

# Calculate past time by subtracting 20 days from now
past_ist = now_ist - timedelta(days=20)

# Convert both times to timestamps in milliseconds
str_start = int(past_ist.timestamp()) * 1000
str_end = int(now_ist.timestamp()) * 1000

def get_market_data(symbol, bar_length):
    url = f"https://api.coindcx.com/exchange/v1/markets_details"
    try:
        response = requests.get(url)
        response.raise_for_status()
        markets_details = response.json()
        pair = get_pair_details(symbol, markets_details)
        if pair:
            # url = f'https://public.coindcx.com/market_data/candles?pair={pair}&interval={bar_length}&startTime={str_start}&endTime={str_end}'
            url = f'https://public.coindcx.com/market_data/candles?pair={pair}&interval={bar_length}'
            print(url)
            response = requests.get(url)
            
            if response.status_code == 200:
                kline_data = response.json()
                if not kline_data:
                    print(f"No data received for the specified time range and bar length: {bar_length}.")
                    return None
                
                df = pd.DataFrame(kline_data, columns=["open", "high", "low", "volume", "close", "time"])
                df["Date"] = pd.to_datetime(df["time"], unit="ms")
                df = df.iloc[::-1]
                start_time = df["Date"].iloc[0]
                end_time = df["Date"].iloc[-1]
                print(f"Start Time: {start_time} || End Time : {end_time}")
                df.set_index("Date", inplace=True)
                return df
            else:
                print(f"Error fetching data: {response.status_code}, {response.text}")
        else:
            print(f"The pair for symbol '{symbol}' not found.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    
    return None
	
def get_precision(user_symbol):
    api_url = 'https://api.coindcx.com/exchange/v1/markets_details'
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        markets_details = response.json()
        
        # {"coindcx_name":"FIDAINR","base_currency_short_name":"INR","target_currency_short_name":"FIDA","target_currency_name":"Bonfida","base_currency_name":"Indian Rupee","min_quantity":1.0e-07,"max_quantity":10000000.0,"max_quantity_market":10000000.0,"min_price":9.825666666666667,"max_price":88.431,"min_notional":100.0,"base_currency_precision":3,"target_currency_precision":1,"step":0.1,"order_types":["limit_order"],"symbol":"FIDAINR","ecode":"I","bo_sl_safety_percent":null,"max_leverage":null,"max_leverage_short":null,"pair":"I-FIDA_INR","status":"active"}

        # Find precision for the user-specified symbol
        for market_info in markets_details:
            symbol = market_info['coindcx_name']
            if symbol == user_symbol:
                amount_orecision = market_info['base_currency_precision']
                quantity_precision = market_info['target_currency_precision']
                order_types = market_info['order_types']
                crypto_name = market_info['target_currency_name']
                currency_name = market_info['base_currency_name']
                minimum_amount = market_info['min_notional']
                return amount_orecision, quantity_precision, order_types, crypto_name, currency_name, minimum_amount

        print(f"Symbol '{user_symbol}' not found in the exchange.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange info: {e}")
        return None

	

def get_market_data2(symbol, bar_length):
    url = f"https://api.coindcx.com/exchange/v1/markets_details"
    try:
        response = requests.get(url)
        response.raise_for_status()
        markets_details = response.json()
        
        pair = get_pair_details(symbol, markets_details)
        if pair:
            # url = f'https://public.coindcx.com/market_data/candles?pair={pair}&interval={bar_length}&startTime={str_start}&endTime={str_end}'
            url = f'https://public.coindcx.com/market_data/candles?pair={pair}&interval={bar_length}'
            # print(url)
            response = requests.get(url)
            
            if response.status_code == 200:
                kline_data = response.json()
                if not kline_data:
                    print(f"No data received for the specified time range and bar length: {bar_length}.")
                    return None
                
                df = pd.DataFrame(kline_data, columns=["open", "high", "low", "volume", "close", "time"])
                df["Date"] = pd.to_datetime(df["time"], unit="ms")
                # Set the timezone of the 'time' column to UTC
                df['Date'] = df['Date'].dt.tz_localize('UTC')
                
                # Convert the 'time' column to IST
                df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')
                
                df = df.iloc[::-1]
                df.set_index("Date", inplace=True)
                
                return df
            else:
                print(f"Error fetching data: {response.status_code}, {response.text}")
        else:
            print(f"The pair for symbol '{symbol}' not found.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    
    return None

def get_pair_details(symbol, markets_details):
	for market in markets_details:
		if market['symbol'] == symbol:
			return market['pair']
	return None
