import requests

def get_ask_price(symbol):
    #Market Details
    url = f"https://api.coindcx.com/exchange/v1/markets_details"
    response = requests.get(url)
    response.raise_for_status()
    markets_details = response.json()
    pair = get_pair_details(symbol, markets_details)
    
    url = f'https://public.coindcx.com/market_data/orderbook?pair={pair}'
    response = requests.get(url)
    
    try:
        data = response.json()
        asks = data.get("asks", {})

        # Find the best ask price (minimum price)
        best_ask_price = round(min(map(float, asks.keys())), 4)

        return best_ask_price
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None


def get_latest_price(symbol, amount_precision):
    url = 'https://api.coindcx.com/exchange/ticker'

    try:
        response = requests.get(url)
        response.raise_for_status()
        ticker_data = response.json()

        for market_data in ticker_data:
            if market_data['market'] == symbol:
                return round(float(market_data['last_price']), amount_precision)

        print(f"Symbol '{symbol}' not found in the ticker data.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching ticker data: {e}")
        return None


def get_pair_details(symbol, markets_details):
	for market in markets_details:
		if market['symbol'] == symbol:
			return market['pair']
	return None


def get_bid_price(symbol):
    #Market Details
    url = f"https://api.coindcx.com/exchange/v1/markets_details"
    response = requests.get(url)
    response.raise_for_status()
    markets_details = response.json()
    
    pair = get_pair_details(symbol, markets_details)
    
    url = f'https://public.coindcx.com/market_data/orderbook?pair={pair}'
    response = requests.get(url)
    
    try:
        data = response.json()
        bids = data.get("bids", {})

        # Find the best bid price (max price)
        best_bid_price = round(max(map(float, bids.keys())), 4)
        
        return best_bid_price
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None