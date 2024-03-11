import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import pandas_ta as ta
from Packages.MarketData import marketdata


class BollingerBandsForwardTester:

    def __init__(self, symbol, bar_length, window_range, num_std_dev_range, fees_percentage=0.0050, tds_percentage=0.01, initial_balance=1000):
        self.symbol = symbol
        self.bar_length = bar_length
        self.window_range = window_range
        self.num_std_dev_range = num_std_dev_range
        self.fees_percentage = fees_percentage
        self.tds_percentage = tds_percentage
        self.initial_balance = initial_balance

    def forward_test(self, bar_length):
        # df = self.get_market_data2(bar_length)
        df = marketdata.get_market_data(self.symbol, bar_length)
        if df is None or df.empty:
            return 0

        print(f"Checking For: {self.symbol}, Length: {bar_length} , Window Range {self.window_range}, Deviation Range: {self.num_std_dev_range}\n")

        # Initialize variables to store the best parameters
        best_params = {'num_std_dev': 0, 'window': 0}
        best_balance = float('-inf')

        for window in self.window_range:
            for num_std_dev in self.num_std_dev_range:
                # Calculate Bollinger Bands
                df['MA'] = df['close'].rolling(window=window).mean()
                df['Upper'] = df['MA'] + (num_std_dev * df['close'].rolling(window=window).std())
                df['Lower'] = df['MA'] - (num_std_dev * df['close'].rolling(window=window).std())
#                 print(df)
                # Simulate trading
                balance = self.initial_balance
                position = 0
                b_trades = 0
                s_trades = 0
                fee_total = 0
                tds_total = 0
                

                for i in range(1, len(df)):
                    if df['close'].iloc[i] < df['Lower'].iloc[i] and df['close'].iloc[i-1] >= df['Lower'].iloc[i-1]:# and df['close'].iloc[i-2] >= df['Lower'].iloc[i-2]:
#                     if latest_price < df['Lower'].iloc[i] and df['close'].iloc[i] <= df['Lower'].iloc[i-1]:

                        # Buy Signal
                        
                        units = (balance * (1 - self.fees_percentage)) / df['close'].iloc[i]  # Adjust for fees
                        position += units
                        balance -= units * df['close'].iloc[i]
                        balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                        fee_total += units * df['close'].iloc[i] * self.fees_percentage
                        b_trades += 1

                    elif df['close'].iloc[i] > df['Upper'].iloc[i] and df['close'].iloc[i-1] <= df['Upper'].iloc[i-1] and df['close'].iloc[i-2] <= df['Upper'].iloc[i-2]:
#                     elif latest_price > df['Upper'].iloc[i] and df['close'].iloc[i-1] <= df['Upper'].iloc[i-1] and df['close'].iloc[i-2] <= df['Upper'].iloc[i-2]:
#                     elif df['close'].iloc[-1] > df['Upper'].iloc[-1] and df["close"].iloc[-2] < df["MA"].iloc[-1] and df["close"].iloc[-3] < df["MA"].iloc[-2]:
                        # Sell Signal
                        units = position
                        # print(units)
                        position -= units
                        balance += units * df['close'].iloc[i]
                        balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                        balance -= units * df['close'].iloc[i] * self.tds_percentage  # Subtract tds
                        fee_total += units * df['close'].iloc[i] * self.fees_percentage
                        tds_total += units * df['close'].iloc[i] * self.tds_percentage
                        # print(f"Total TDS: {tds_total}")
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
                    total_tds = tds_total
                    total_fee = fee_total
                    # print(f"Total TDS: {total_tds}")

        return best_std_dev, best_window, best_balance, all_B_trades, all_S_trades, bar_length, total_fee, total_tds

    
if __name__ == "__main__":
    crypto_name = "JASMY"
    base_currency = "INR"
    symbol_to_forward_test = f"{crypto_name}{base_currency}"
    window_range_values = range(1, 101)  # Adjust the range based on your requirements
    num_std_dev_range_values = range(0, 4)
    bar_lengths = ['1m', '5m','15m']#, '30m', '1h']
    initial_balance = 1500
#     bar_lengths = ['30m']
    best_results = []

    for bar_length in bar_lengths:
        forward_tester = BollingerBandsForwardTester(symbol=symbol_to_forward_test, bar_length=bar_length, window_range=window_range_values, num_std_dev_range=num_std_dev_range_values, initial_balance=initial_balance)
        std_dev, window, best_balance, all_B_trades, all_S_trades, chosen_bar_length, total_fee, total_tds = forward_tester.forward_test(bar_length)
        best_results.append((std_dev, window, best_balance, all_B_trades, all_S_trades, chosen_bar_length))

    # Find the best result based on maximum returns
    best_result = max(best_results, key=lambda x: x[2])
    std_dev, window, best_balance, all_B_trades, all_S_trades, chosen_bar_length = best_result
    percentage_increase = (best_balance - initial_balance) * 100 / initial_balance
    print("\n\n----------------------------------------------------------------------------------------------------")
    print(f"Pair: {symbol_to_forward_test}\nResult:\nStd Dev: {std_dev} | Window: {window} | Balance : {best_balance} | Chosen Bar Length: {chosen_bar_length}")
    print(f"Total Buy Trades : {all_B_trades} | Total Sell Trades : {all_S_trades}")
    print(f"Total Fee Paid : {total_fee} | Total TDS Paid : {total_tds}")
    print(f"Increment: {percentage_increase:.2f}%")
    print("----------------------------------------------------------------------------------------------------")