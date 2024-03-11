import pandas as pd


def get_stock_data(symbol, bar_length):
    global bar_length_to_check
    if bar_length == '1m':
        bar_length_to_check = '5m'
    elif bar_length == '5m':
        bar_length_to_check = '15m'
    elif bar_length == '15m':
        bar_length_to_check = '30m'
    elif bar_length == '30m':
        bar_length_to_check = '1h'
    elif bar_length == '1h':
        bar_length_to_check = '4h'
    elif bar_length == '1d':
        bar_length_to_check = '1w'
    else:
        raise ValueError("Unsupported bar_length")
    
    data = marketdata.get_market_data2(symbol, bar_length_to_check)
    return data

def print_rsi_market_state(symbol, window=14, steps_back=4, bar_length='15m'):
    # Fetch historical data
    df = get_stock_data(symbol, bar_length)

    # Calculate daily returns
    df['close'] = df['close'].ffill()
    df['Daily Return'] = df['close'].pct_change()

    # Calculate average gain and average loss
    df['Gain'] = df['Daily Return'].apply(lambda x: max(0, x))
    df['Loss'] = df['Daily Return'].apply(lambda x: max(0, -x))

    avg_gain = df['Gain'].rolling(window=window).mean()
    avg_loss = df['Loss'].rolling(window=window).mean()

    # Calculate relative strength (RS)
    rs = avg_gain / avg_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    # Determine RSI trend state
    rsi_trend = "Unknown"
    rsi_change = rsi.diff(periods=steps_back).iloc[-1]

    if rsi_change > 0:
        rsi_trend = "Climbing"
    elif rsi_change < 0:
        rsi_trend = "Plunging"

    # Determine market state based on RSI values
    market_state = "Unknown"

    if all(35 <= val <= 65 for val in rsi.tail(steps_back)):
        market_state = "Flat"
        
    elif rsi.iloc[-1] or rsi.iloc[-2] or rsi.iloc[-3] or rsi.iloc[-4] >= 65:
        if rsi.iloc[-1] >= 65 or rsi.iloc[-2] > rsi.iloc[-3] > rsi.iloc[-4]:
            market_state = "Sell"
        elif rsi.iloc[-2] < rsi.iloc[-3] > rsi.iloc[-4]:
            market_state = "Flat"
        elif rsi.iloc[-2] < rsi.iloc[-3] < rsi.iloc[-4]:
            market_state = "Sell"
        else:
            market_state = "Sell"
            
    elif rsi.iloc[-1] or rsi.iloc[-2] or rsi.iloc[-3] or rsi.iloc[-4] <= 35:
        if rsi.iloc[-1] <= 35 or rsi.iloc[-2] < rsi.iloc[-3] < rsi.iloc[-4]:
            market_state = "Buy"
        elif rsi.iloc[-2] > rsi.iloc[-3] < rsi.iloc[-4]:
            market_state = "Flat"
        elif rsi.iloc[-2] > rsi.iloc[-3] > rsi.iloc[-4]:
            market_state = "Buy"
        else:
            market_state = "Buy"

    # Print RSI values for the last 5 steps
    print(f"RSI Values (last {steps_back} steps):")
    print(rsi.tail(steps_back).round(2))
    
    # Print RSI, trend state, and market state
    print("\nRSI ({} bars): {:.2f}".format(bar_length, rsi.iloc[-1]))
    print("RSI Trend State ({} steps back): {}".format(steps_back, rsi_trend))
    print("Market State: {}".format(market_state))
    
def get_rsi_market_state(symbol, window=14, steps_back=4, bar_length='15m'):
    # Fetch historical data
    df = marketdata.get_market_data2(symbol, bar_length)

    # Calculate daily returns
    df['close'] = df['close'].ffill()
    df['Daily Return'] = df['close'].pct_change()

    # Calculate average gain and average loss
    df['Gain'] = df['Daily Return'].apply(lambda x: max(0, x))
    df['Loss'] = df['Daily Return'].apply(lambda x: max(0, -x))

    avg_gain = df['Gain'].rolling(window=window).mean()
    avg_loss = df['Loss'].rolling(window=window).mean()

    # Calculate relative strength (RS)
    rs = avg_gain / avg_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    # Determine RSI trend state
    rsi_trend = "Unknown"
    rsi_change = rsi.diff(periods=steps_back).iloc[-1]

    if rsi_change > 0:
        rsi_trend = "Climbing"
    elif rsi_change < 0:
        rsi_trend = "Plunging"

    # Determine market state based on RSI values
    market_state = "Unknown"

    if all(35 <= val <= 65 for val in rsi.tail(steps_back)):
        market_state = "Flat"
        
    elif rsi.iloc[-1] or rsi.iloc[-2] or rsi.iloc[-3] or rsi.iloc[-4] >= 65:
        if rsi.iloc[-1] >= 65 or rsi.iloc[-2] > rsi.iloc[-3] > rsi.iloc[-4]:
            market_state = "Sell"
        elif rsi.iloc[-2] < rsi.iloc[-3] > rsi.iloc[-4]:
            market_state = "Flat"
        elif rsi.iloc[-2] < rsi.iloc[-3] < rsi.iloc[-4]:
            market_state = "Sell"
        else:
            market_state = "Sell"
            
    elif rsi.iloc[-1] or rsi.iloc[-2] or rsi.iloc[-3] or rsi.iloc[-4] <= 35:
        if rsi.iloc[-1] <= 35 or rsi.iloc[-2] < rsi.iloc[-3] < rsi.iloc[-4]:
            market_state = "Buy"
        elif rsi.iloc[-2] > rsi.iloc[-3] < rsi.iloc[-4]:
            market_state = "Flat"
        elif rsi.iloc[-2] > rsi.iloc[-3] > rsi.iloc[-4]:
            market_state = "Buy"
        else:
            market_state = "Buy"
    
    print(f"As per RSI, current Trend is : {rsi_trend} and Market State is :{market_state}")
    
    return market_state, rsi_trend


if __name__ == "__main__":
    import sys
    sys.path.append('../')  # Add the parent folder to the Python path
    from MarketData import marketdata
    symbol = input("Please Enter the Symbol you want to check: ")
    bar_length = input("Please Enter the bar length you are using currently: ")
    steps_back = int(input("Please Imput step-back level you want to check from: "))
    print_rsi_market_state(symbol, window=14, steps_back=steps_back, bar_length=bar_length)
else:
    from Packages.MarketData import marketdata
    

