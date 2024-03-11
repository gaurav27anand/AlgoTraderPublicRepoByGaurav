import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from Packages.MarketData import marketdata
import warnings
warnings.filterwarnings('ignore')

class SupertrendsForwardTester:

    def __init__(self, symbol, bar_length, period_range, multiplier_range, fees_percentage=0.005, tds_percentage=0.01, initial_balance=10000):
        self.symbol = symbol
        self.bar_length = bar_length
        self.period_range = period_range
        self.multiplier_range = multiplier_range
        self.fees_percentage = fees_percentage
        self.tds_percentage = tds_percentage
        self.initial_balance = initial_balance
        self.total_fees_paid = 0
        self.total_tds_paid = 0
        self.total_buy_trades = 0
        self.total_sell_trades = 0
        self.in_position = False

    '''    
    def calculate_supertrend(self, df, period=7, multiplier=3):
        df['ATR'] = df['high'] - df['low']
        df['ATR'] = df['ATR'].rolling(period).mean()

        df['Upper_band'] = df['high'] + multiplier * df['ATR']
        df['Lower_band'] = df['low'] - multiplier * df['ATR']

        df['Trend_direction'] = 0
        df['Trend_direction'] = np.where(df['close'] > df['Upper_band'], 1, df['Trend_direction'])
        df['Trend_direction'] = np.where(df['close'] < df['Lower_band'], -1, df['Trend_direction'])

        df['Supertrend'] = df['close']
        for i in range(1, len(df)):
            if df['Trend_direction'].iloc[i] == 1:
                df.loc[df.index[i], 'Supertrend'] = df['Lower_band'].iloc[i]
            elif df['Trend_direction'].iloc[i] == -1:
                df.loc[df.index[i], 'Supertrend'] = df['Upper_band'].iloc[i]
            else:
                df.loc[df.index[i], 'Supertrend'] = df['Supertrend'].iloc[i - 1]

        return df
    '''    
        
        
        
    def tr(self, data):
        data['previous_close'] = data['close'].shift(1)
        data['high-low'] = abs(data['high'] - data['low'])
        data['high-pc'] = abs(data['high'] - data['previous_close'])
        data['low-pc'] = abs(data['low'] - data['previous_close'])

        tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

        return tr

    def atr(self, data, period):
        data['tr'] = self.tr(data)
        atr = data['tr'].rolling(period).mean()

        return atr
        
    def supertrend(self, df, period=7, atr_multiplier=3):
        hl2 = (df['high'] + df['low']) / 2
        df['atr'] = self.atr(df, period)
        df['upperband'] = hl2 + (atr_multiplier * df['atr'])
        df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
        df['in_uptrend'] = True

        for current in range(1, len(df.index)):
            previous = current - 1

            if df['close'].iloc[current] > df['upperband'].iloc[previous]:
                df['in_uptrend'].iloc[current] = True
            elif df['close'].iloc[current] < df['lowerband'].iloc[previous]:
                df['in_uptrend'].iloc[current] = False
            else:
                df['in_uptrend'].iloc[current] = df['in_uptrend'].iloc[previous]

                if df['in_uptrend'].iloc[current] and df['lowerband'].iloc[current] < df['lowerband'].iloc[previous]:
                    df['lowerband'].iloc[current] = df['lowerband'].iloc[previous]

                if not df['in_uptrend'].iloc[current] and df['upperband'].iloc[current] > df['upperband'].iloc[previous]:
                    df['upperband'].iloc[current] = df['upperband'].iloc[previous]

        return df



        
        
        
        
        
    
    
    '''
    def check_buy_sell_signals(df):
        global in_position

        print("checking for buy and sell signals")
        print(df.tail(5))
        last_row_index = len(df.index) - 1
        previous_row_index = last_row_index - 1

        if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
            print("changed to uptrend, buy")
            if not in_position:
                order = exchange.create_market_buy_order('ETH/USD', 0.05)
                print(order)
                in_position = True
            else:
                print("already in position, nothing to do")
        
        if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
            if in_position:
                print("changed to downtrend, sell")
                order = exchange.create_market_sell_order('ETH/USD', 0.05)
                print(order)
                in_position = False
            else:
                print("You aren't in position, nothing to sell")
                
    '''
        
    def forward_test_supertrends_strategy(self, bar_length):
        df = marketdata.get_market_data(self.symbol, bar_length)
        if df is None or df.empty:
            return 0

        print(f"Checking For: {self.symbol}, Length: {bar_length}, Period Range: {self.period_range}, Multiplier Range: {self.multiplier_range}\n")

        # Initialize variables to store the best parameters
        best_params = {'period': 0, 'multiplier': 0}
        best_balance = float('-inf')

        for period_value in self.period_range:
            for multiplier_value in self.multiplier_range:
                # Calculate Supertrends
                # df = self.calculate_supertrend(df, period=period_value, multiplier=multiplier_value)
                df = self.supertrend(df, period=period_value, atr_multiplier=multiplier_value)
                
                # print(df)


                # Simulate trading
                balance = self.initial_balance
                position = 0
                b_trades = 0
                s_trades = 0
                fee_total = 0
                tds_total = 0

                for i in range(1, len(df)):
                    # global in_position

                    # print("checking for buy and sell signals")
                    # print(df.tail(5))
                    last_row_index = len(df.index) - 1
                    previous_row_index = last_row_index - 1

                    if not df['in_uptrend'].iloc[previous_row_index] and df['in_uptrend'].iloc[last_row_index]:
                        # print("changed to uptrend, buy")
                        if not self.in_position:
                            units = (balance * (1 - self.fees_percentage)) / df['close'].iloc[i]  # Adjust for fees
                            position += units
                            balance -= units * df['close'].iloc[i]
                            balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                            fee_total += units * df['close'].iloc[i] * self.fees_percentage
                            b_trades += 1
                            self.in_position = True
                        # else:
                            # print("already in position, nothing to do")
                    
                    if df['in_uptrend'].iloc[previous_row_index] and not df['in_uptrend'].iloc[last_row_index]:
                        if self.in_position:
                            # print("changed to downtrend, sell")
                            # Sell Signal
                            units = position
                            position -= units
                            balance += units * df['close'].iloc[i]
                            balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                            balance -= units * df['close'].iloc[i] * self.tds_percentage  # Subtract tds
                            fee_total += units * df['close'].iloc[i] * self.fees_percentage
                            tds_total += units * df['close'].iloc[i] * self.tds_percentage
                            s_trades += 1
                            self.in_position = False
                        # else:
                            # print("You aren't in position, nothing to sell")
                    
                    '''
                    if df['Trend_direction'].iloc[i] == 1 and df['close'].iloc[i] > df['Supertrend'].iloc[i - 1]:
                        # Buy Signal
                        units = (balance * (1 - self.fees_percentage)) / df['close'].iloc[i]  # Adjust for fees
                        position += units
                        balance -= units * df['close'].iloc[i]
                        balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                        fee_total += units * df['close'].iloc[i] * self.fees_percentage
                        b_trades += 1

                    elif df['Trend_direction'].iloc[i] == -1 and df['close'].iloc[i] < df['Supertrend'].iloc[i - 1]:
                        # Sell Signal
                        units = position
                        position -= units
                        balance += units * df['close'].iloc[i]
                        balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                        balance -= units * df['close'].iloc[i] * self.tds_percentage  # Subtract tds
                        fee_total += units * df['close'].iloc[i] * self.fees_percentage
                        tds_total += units * df['close'].iloc[i] * self.tds_percentage
                        s_trades += 1
                    '''

                # Calculate final balance
                balance += position * df['close'].iloc[-1]

                # Update best parameters if the current balance is higher
                if balance > best_balance:
                    best_balance = balance
                    best_params['period'] = period_value
                    best_params['multiplier'] = multiplier_value
                    best_position = position

        return best_params['period'], best_params['multiplier'], best_balance, b_trades, s_trades, bar_length, fee_total, tds_total, df, best_position
    
    
    
if __name__ == "__main__":
    crypto_name = "ARKM"
    base_currency = "INR"
    symbol_to_forward_test = f"{crypto_name}{base_currency}"
    period_range_values = range(5, 51)  # Adjust the range based on your requirements
    multiplier_range_values = range(1, 10)
    bar_lengths = ['1m', '5m']#, '30m', '1h']  # Adjust the bar lengths based on your requirements
    initial_balance = 1500
    best_results = []

    for bar_length in bar_lengths:
        forward_tester = SupertrendsForwardTester(symbol=symbol_to_forward_test, bar_length=bar_length, period_range=period_range_values, multiplier_range=multiplier_range_values, initial_balance=initial_balance)
        period, multiplier, best_balance, all_B_trades, all_S_trades, chosen_bar_length, total_fee, total_tds, df1, best_position = forward_tester.forward_test_supertrends_strategy(bar_length)
        best_results.append((period, multiplier, best_balance, all_B_trades, all_S_trades, chosen_bar_length))

    # Find the best result based on maximum returns
    best_result = max(best_results, key=lambda x: x[2])
    period, multiplier, best_balance, all_B_trades, all_S_trades, chosen_bar_length = best_result
    percentage_increase = (best_balance - initial_balance) * 100 / initial_balance
    print("\n\n----------------------------------------------------------------------------------------------------")
    print(f"Pair: {symbol_to_forward_test}\nResult:\nPeriod: {period} | Multiplier: {multiplier} | Balance : {best_balance} | Chosen Bar Length: {chosen_bar_length}")
    print(f"Total Buy Trades : {all_B_trades} | Total Sell Trades : {all_S_trades}")
    print(f"Total Fee Paid : {total_fee} | Total TDS Paid : {total_tds}")
    print(f"Increment: {percentage_increase:.2f}% || Final Position: {best_position} ")
    print("----------------------------------------------------------------------------------------------------")
#     print(df1)
