import requests

def get_top_liquidity_pairs(top_n=5):
    '''
    Optional Parameter: Count of top 'n'. Default = 5
    It will give out top n liquid pairs to trade on
    '''
    
    try:
        # Fetch market data from the API
        api_url = 'https://api.coindcx.com/exchange/ticker'
        response = requests.get(api_url)
        response.raise_for_status()
        market_data = response.json()
        pairs_with_volumes = []

        # Assuming the market data structure has a list of trading pairs
        pairs_with_volumes = [(pair['market'], pair.get('volume', 0)) for pair in market_data]
        # Sort pairs based on volume in descending order
        sorted_pairs = sorted(pairs_with_volumes, key=lambda x: float(x[1]), reverse=True)

        # Return the top N pairs with the highest liquidity
        return sorted_pairs[:top_n]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


if __name__ == "__main__":
    top_liquidity_pairs = get_top_liquidity_pairs()
    if top_liquidity_pairs:
        print("Top 5 Crypto Pairs with Highest Liquidity:")
        for pair in top_liquidity_pairs:
            print(f"Symbol: {pair[0]}, Volume: {pair[1]}")