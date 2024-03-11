import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

class TripleSMAMACDForwardTester:

    def __init__(self, symbol, short_window, medium_window, long_window, signal_window, fees_percentage=0.0050, tds_percentage=0.01, initial_balance=1000):
        self.symbol = symbol
        self.short_window = short_window
        self.medium_window = medium_window
        self.long_window = long_window
        self.signal_window = signal_window
        self.fees_percentage = fees_percentage
        self.tds_percentage = tds_percentage
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
                past = now - timedelta(days=30)  # Fetch last 30 days for forward testing
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
                    df = df.iloc[::-1]
                    df.set_index("Date", inplace=True)
                    # print(df)
                    return df
                else:
                    print(f"Error fetching data: {response.status_code}, {response.text}")
            else:
                print(f"The pair for symbol '{self.symbol}' not found.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")

        return None
        
    def get_market_data2(self, bar_length):
        url = f"https://api.coindcx.com/exchange/v1/markets_details"
        try:
            response = requests.get(url)
            response.raise_for_status()
            markets_details = response.json()

            pair = self.get_pair_details(self.symbol, markets_details)
            if pair:
                now = datetime.utcnow()
                past = now - timedelta(days=3)  # Fetch last 30 days for forward testing
                str_start = int(past.timestamp()) * 1000
                str_end = int(now.timestamp()) * 1000

                url = f'https://public.coindcx.com/market_data/candles?pair={pair}&interval={bar_length}&startTime={str_start}&endTime={str_end}&limit=1000'
                response = requests.get(url)
#                 print(url)

                if response.status_code == 200:
                    kline_data = response.json()
                    if not kline_data:
                        print("No data received for the specified time range.")
                        return None

                    df = pd.DataFrame(kline_data, columns=["open", "high", "low", "volume", "close", "time"])
                    df["Date"] = pd.to_datetime(df["time"], unit="ms")
                    df = df.iloc[::-1]
                    df.set_index("Date", inplace=True)
                    # print(df)
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

    def forward_test_triple_sma_macd_strategy_with_fees(self, bar_length):
        df = self.get_market_data2(bar_length)
        if df is None or df.empty:
            return 0

        # Initialize variables to store the best parameters
        best_params = {'short_window': 0, 'medium_window': 0, 'long_window': 0, 'signal_window': 0}
        best_balance = float('-inf')

        for short_window in self.short_window:
            for medium_window in self.medium_window:
                for long_window in self.long_window:
                    for signal_window in self.signal_window:
                        # Calculate Triple SMA
                        df['Short_SMA'] = df['close'].rolling(window=short_window).mean()
                        df['Medium_SMA'] = df['close'].rolling(window=medium_window).mean()
                        df['Long_SMA'] = df['close'].rolling(window=long_window).mean()

                        # Calculate MACD
                        df['Short_EMA'] = df['close'].ewm(span=short_window, adjust=False).mean()
                        df['Long_EMA'] = df['close'].ewm(span=long_window, adjust=False).mean()
                        df['MACD'] = df['Short_EMA'] - df['Long_EMA']

                        # Calculate Signal Line
                        df['Signal_Line'] = df['MACD'].ewm(span=signal_window, adjust=False).mean()

                        # Simulate trading
                        balance = self.initial_balance
                        position = 0
                        b_trades = 0
                        s_trades = 0
                        fee_total = 0
                        tds_total = 0

                        for i in range(1, len(df)):
                            # Buy Signal
                            if df['Short_SMA'].iloc[i] > df['Medium_SMA'].iloc[i] and \
                                    df['Medium_SMA'].iloc[i] > df['Long_SMA'].iloc[i] and \
                                    df['MACD'].iloc[i] > df['Signal_Line'].iloc[i] and \
                                    df['MACD'].iloc[i - 1] <= df['Signal_Line'].iloc[i - 1]:
                                units = (balance * (1 - self.fees_percentage)) / df['close'].iloc[i]  # Adjust for fees
                                position += units
                                balance -= units * df['close'].iloc[i]
                                balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                                fee_total += units * df['close'].iloc[i] * self.fees_percentage
                                b_trades += 1

                            # Sell Signal
                            elif df['Short_SMA'].iloc[i] < df['Medium_SMA'].iloc[i] and \
                                    df['Medium_SMA'].iloc[i] < df['Long_SMA'].iloc[i] and \
                                    df['MACD'].iloc[i] < df['Signal_Line'].iloc[i] and \
                                    df['MACD'].iloc[i - 1] >= df['Signal_Line'].iloc[i - 1]:
                                units = position
                                position -= units
                                balance += units * df['close'].iloc[i]
                                balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                                balance -= units * df['close'].iloc[i] * self.tds_percentage  # Subtract tds
                                fee_total += units * df['close'].iloc[i] * self.fees_percentage
                                tds_total += units * df['close'].iloc[i] * self.tds_percentage
                                s_trades += 1

                        # Calculate final balance
                        balance += position * df['close'].iloc[-1]

                        # Update best parameters if the current balance is higher
                        if balance > best_balance:
                            best_balance = balance
                            best_params['short_window'] = short_window
                            best_params['medium_window'] = medium_window
                            best_params['long_window'] = long_window
                            best_params['signal_window'] = signal_window

        return best_params, best_balance, s_trades, b_trades, tds_total, fee_total


if __name__ == "__main__":
    crypto_name = "JASMY"
    base_currency = "INR"
    symbol_to_forward_test = f"{crypto_name}{base_currency}"
    short_window_range = range(2, 21, 1)
    medium_window_range = range(20, 61, 10)
    long_window_range = range(60, 101, 10)
    signal_window_range = range(5, 25, 1)
    bar_lengths = ['1m', '5m', '15m']
    initial_balance = 1500
    best_results = []

    for bar_length in bar_lengths:
        forward_tester = TripleSMAMACDForwardTester(symbol=symbol_to_forward_test,
                                                    short_window=short_window_range,
                                                    medium_window=medium_window_range,
                                                    long_window=long_window_range,
                                                    signal_window=signal_window_range,
                                                    initial_balance=initial_balance)
        best_params, best_balance, all_S_trades, all_B_trades, total_tds, total_fee = forward_tester.forward_test_triple_sma_macd_strategy_with_fees(bar_length)
        best_results.append((best_params, best_balance, all_S_trades, all_B_trades, bar_length, total_tds, total_fee))

    # Find the best result based on maximum returns
    best_result = max(best_results, key=lambda x: x[1])
    best_params, best_balance, all_S_trades, all_B_trades, chosen_bar_length, total_tds, total_fee = best_result
    percentage_increase = (best_balance - initial_balance) * 100 / initial_balance

    print("\n\n----------------------------------------------------------------------------------------------------")
    print(f"Pair: {symbol_to_forward_test}\nResult:\nBest Parameters: {best_params}\nBalance : {best_balance}\nChosen Bar Length: {chosen_bar_length}")
    print(f"Total Buy Trades : {all_B_trades} | Total Sell Trades : {all_S_trades}")
    print(f"Total Fee Paid : {total_fee} | Total TDS Paid : {total_tds}")
    print(f"Increment: {percentage_increase:.2f}%")
    print("----------------------------------------------------------------------------------------------------")
