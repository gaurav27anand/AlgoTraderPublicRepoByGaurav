import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import pandas_ta as ta

class BollingerBandsForwardTester:

    def __init__(self, symbol, bar_length, window_range, num_std_dev_range, fees_percentage=0.005, initial_balance=15000, historical_days = 2):
        self.historical_days = historical_days
        self.symbol = symbol
        self.bar_length = bar_length
        self.window_range = window_range
        self.num_std_dev_range = num_std_dev_range
        self.fees_percentage = fees_percentage
        self.initial_balance = initial_balance

    def get_market_data(self):
        url = f"https://api.coindcx.com/exchange/v1/markets_details"
        try:
            response = requests.get(url)
            response.raise_for_status()
            markets_details = response.json()

            pair = self.get_pair_details(self.symbol, markets_details)
            if pair:
                now = datetime.utcnow()
                past = now - timedelta(days=self.historical_days)  
                str_start = int(past.timestamp()) * 1000
                str_end = int(now.timestamp()) * 1000

                url = f'https://public.coindcx.com/market_data/candles?pair={pair}&interval={self.bar_length}&startTime={str_start}&endTime={str_end}&limit=1000'
                response = requests.get(url)
#                 print(url)

                if response.status_code == 200:
                    kline_data = response.json()
                    if not kline_data:
                        print("No data received for the specified time range.")
                        return None

                    df = pd.DataFrame(kline_data, columns=["open", "high", "low", "volume", "close", "time"])
                    df["Date"] = pd.to_datetime(df["time"], unit="ms")
                    print(df["Date"].iloc[0])
                    print(df["Date"].iloc[-1])
                    df.set_index("Date", inplace=True)
                    
                    return df
                else:
                    print(f"Error fetching data: {response.status_code}, {response.text}")
            else:
                print(f"The pair for symbol '{self.symbol}' not found.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")

        return None

    def get_pair_details(self, symbol, markets_details):
        for market in markets_details:
            if market['symbol'] == symbol:
                return market['pair']
        return None

    def forward_test_bollinger_bands_strategy_FIXRETURN(self):
        df = self.get_market_data()
        if df is None or df.empty:
            return 0
            
        print(f"Input Received: {self.symbol, self.bar_length, self.window_range, self.num_std_dev_range}")

        # Initialize variables to store the best parameters
        best_params = {'num_std_dev': 0, 'window': 0}
        best_balance = float('-inf')

        for window in self.window_range:
            for num_std_dev in self.num_std_dev_range:
                # Calculate Bollinger Bands
                df['MA'] = df['close'].rolling(window=window).mean()
                df['Upper'] = df['MA'] + (num_std_dev * df['close'].rolling(window=window).std())
                df['Lower'] = df['MA'] - (num_std_dev * df['close'].rolling(window=window).std())

                # Simulate trading
                balance = self.initial_balance
                position = 0
                b_trades = 0
                s_trades = 0

                for i in range(1, len(df)):
                    if df['close'].iloc[i] < df['Lower'].iloc[i] and df['close'].iloc[i-1] >= df['Lower'].iloc[i-1]:
                        # Buy Signal
                        units = (balance * (1 - self.fees_percentage)) / df['close'].iloc[i]  # Adjust for fees
                        position += units
                        balance -= units * df['close'].iloc[i]
                        balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                        b_trades += 1

                    elif df['close'].iloc[i] > df['Upper'].iloc[i] and df['close'].iloc[i-1] <= df['Upper'].iloc[i-1]:
                        # Sell Signal
                        units = position
                        position -= units
                        balance += units * df['close'].iloc[i]
                        balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                        s_trades += 1

                # Calculate final balance
                balance += position * df['close'].iloc[-1]

                # Update best parameters if the current balance is higher
                if balance > best_balance:
                    best_balance = balance
                    best_params['num_std_dev'] = num_std_dev
                    best_params['window'] = window
                    best_std_dev = num_std_dev
                    best_window = window
                    all_B_trades = b_trades
                    all_S_trades = s_trades
            
                

        return best_std_dev, best_window, best_balance, all_B_trades, all_S_trades


if __name__ == "__main__":
    symbol_to_forward_test = "REQINR"
    window_range_values = range(1, 100)  # Adjust the range based on your requirements
    num_std_dev_range_values = range(0, 4)
    history = 10
    forward_tester = BollingerBandsForwardTester(symbol=symbol_to_forward_test, bar_length='15m', window_range=window_range_values, num_std_dev_range=num_std_dev_range_values, historical_days=history)
    std_dev, window, best_balance, all_B_trades, all_S_trades = forward_tester.forward_test_bollinger_bands_strategy_FIXRETURN()
    print(f"Std Dev: {std_dev} | Window: {window} | Balance : {best_balance}")
    print(f"Total Buy Trades : {all_B_trades} | Total Sell Trades : {all_S_trades}")
    