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

def get_next_stock_data(symbol, bar_length):
    global next_bar_length_to_check
    if bar_length == '1m':
        next_bar_length_to_check = '30m'
    elif bar_length == '5m':
        next_bar_length_to_check = '1h'
    elif bar_length == '15m':
        next_bar_length_to_check = '2h'
        alt_next_bar_length_to_check = '4h'
    elif bar_length == '30m':
        next_bar_length_to_check = '4h'
    elif bar_length == '1h':
        next_bar_length_to_check = '1d'
    elif bar_length == '1d':
        next_bar_length_to_check = '1w'
    else:
        raise ValueError("Unsupported bar_length")
    
    data = marketdata.get_market_data2(symbol, next_bar_length_to_check)
    if data is None:
        data = marketdata.get_market_data(symbol, alt_next_bar_length_to_check)
    return data

def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['Short_MA'] = data['close'].ewm(span=short_window, adjust=False).mean()
    data['Long_MA'] = data['close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['Short_MA'] - data['Long_MA']
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()

def generate_signals(data):
    data['Buy_Signal'] = (data['MACD'] > data['Signal_Line']) & (data['MACD'].shift(1) <= data['Signal_Line'].shift(1))
    data['Sell_Signal'] = (data['MACD'] < data['Signal_Line']) & (data['MACD'].shift(1) >= data['Signal_Line'].shift(1))
    data['Trend'] = None

    # Check if Short_MA - Long_MA difference is reducing for the last 3 bars
    reducing_diff_condition = (
        (data['Short_MA'].diff() < 0) & (data['Long_MA'].diff() < 0) &
        (data['Short_MA'].shift(1).diff() < 0) & (data['Long_MA'].shift(1).diff() < 0) &
        (data['Short_MA'].shift(2).diff() < 0) & (data['Long_MA'].shift(2).diff() < 0)
    )
    increasing_diff_condition = (
        (data['Short_MA'].diff() > 0) & (data['Long_MA'].diff() > 0) &
        (data['Short_MA'].shift(1).diff() > 0) & (data['Long_MA'].shift(1).diff() > 0) &
        (data['Short_MA'].shift(2).diff() > 0) & (data['Long_MA'].shift(2).diff() > 0)
    )
    
    # Conditions for Uptrend
    uptrend_condition = (
        # Condition 1
        ((data['Short_MA'] <= data['Long_MA']) & reducing_diff_condition) |
        # Condition 2
        ((data['Short_MA'] >= data['Long_MA']) & increasing_diff_condition) |
        # Condition 3
        ((data['Short_MA'].diff() > 0) & (data['Short_MA'].shift(1).diff() > 0) & (data['Short_MA'].shift(2).diff() > 0))
    )
    
    # Conditions for Downtrend
    downtrend_condition = (
        # Condition 1
        ((data['Short_MA'] >= data['Long_MA']) & reducing_diff_condition) |
        # Condition 2
        ((data['Short_MA'] <= data['Long_MA']) & increasing_diff_condition) |
        # Condition 3
        ((data['Short_MA'] <= data['Long_MA']) & (
            (data['Short_MA'].diff() > 0) |
            ((data['Short_MA'].diff() >= -0.1) & (data['Short_MA'].diff() <= 0.05)) &
            (data['Short_MA'].shift(1).diff() > 0) |
            ((data['Short_MA'].shift(1).diff() >= -0.1) & (data['Short_MA'].shift(1).diff() <= 0.05)) &
            (data['Short_MA'].shift(2).diff() > 0) |
            ((data['Short_MA'].shift(2).diff() >= -0.1) & (data['Short_MA'].shift(2).diff() <= 0.05))
        )) |
        # Condition 4
        ((data['Short_MA'].diff() < 0) & (data['Short_MA'].shift(1).diff() < 0) & (data['Short_MA'].shift(2).diff() < 0))
    )

    # Apply conditions to update the 'Trend' column
    data.loc[uptrend_condition, 'Trend'] = 'Uptrend'
    data.loc[downtrend_condition, 'Trend'] = 'Downtrend'



def print_trend(data):
    last_signal = data['Trend'].dropna().iloc[-1]
    print(f"The market is currently in {last_signal.lower()} trend.")
    
def get_trend(data):
    last_signal = data['Trend'].dropna().iloc[-1]
    
    if last_signal == "None":
        last_signal = "Flat"
    
    return last_signal.lower()

def get_current_trend(symbol, bar_length):
    # Get stock data
    stock_data_level_1 = get_stock_data(symbol, bar_length)
    
    if stock_data_level_1 is not None and not stock_data_level_1.empty:
        # Calculate MACD and generate signals
        calculate_macd(stock_data_level_1)
        generate_signals(stock_data_level_1)

        trend_level_1 = get_trend(stock_data_level_1)
    else:
        trend_level_1 = 'NO_DATA'
    
    # Get stock data
    stock_data_level_2 = get_next_stock_data(symbol, bar_length)
    if stock_data_level_2 is not None and not stock_data_level_2.empty:
        # Calculate MACD and generate signals
        calculate_macd(stock_data_level_2)
        generate_signals(stock_data_level_2)

        trend_level_2 = get_trend(stock_data_level_2)
    else:
        trend_level_2 = 'NO_DATA'
        
        
    print(f"\n Trend Check for {symbol} \n\nFor Level 1: {bar_length_to_check} bar ==> {trend_level_1} \nFor Level 2: {next_bar_length_to_check} bar ==> {trend_level_2}")
    return trend_level_1, trend_level_2

if __name__ == "__main__":
    import os, sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from MarketData import marketdata
    symbol = input("Please Enter the Symbol you want to check: ")
    bar_length = input("Please Enter the bar length you are using currently: ")
    get_current_trend(symbol=symbol, bar_length=bar_length)
else:
    from Packages.MarketData import marketdata
