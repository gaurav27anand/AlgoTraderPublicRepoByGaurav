import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from Packages.MarketData import marketdata

class FibonacciRetracementStrategy:

    def __init__(self, symbol, bar_length, fibonacci_levels, ma_periods, atr_periods, min_holding_period, stop_loss_factors, take_profit_factors, transaction_cost_pct=0.005, tds_cost_pct=0.01):
        self.symbol = symbol
        self.bar_length = bar_length
        self.fibonacci_levels = fibonacci_levels
        self.ma_periods = ma_periods
        self.atr_periods = atr_periods
        self.min_holding_period = min_holding_period
        self.stop_loss_factors = stop_loss_factors
        self.take_profit_factors = take_profit_factors
        self.transaction_cost_pct = transaction_cost_pct
        self.tds_cost_pct = tds_cost_pct

    # def fibonacci_retracement_strategy(self, df, fibonacci_level, ma_period, atr_period):
    def fibonacci_retracement_strategy(self, df, fibonacci_level=0.618, ma_period=20, atr_period=14, min_holding_period=5, stop_loss_factor=1.5, take_profit_factor=2.0):
        # Calculate Fibonacci retracement levels
        high = df['high'].max()
        low = df['low'].min()
        retracement_level = low + fibonacci_level * (high - low)

        # Generate signals based on closing price crossing above the retracement level
        df['Signal'] = np.where(df['close'] > retracement_level, 1, 0)

        # Trend filter using a simple moving average
        df['MA'] = df['close'].rolling(window=ma_period).mean()
        df['Signal'] = np.where(df['close'] > df['MA'], df['Signal'], 0)

        # Apply the strategy to simulate trades
        df['Position'] = df['Signal'].diff()

        # Calculate Average True Range (ATR)
        df['ATR'] = df['high'] - df['low']
        df['ATR'] = df['ATR'].rolling(window=atr_period).mean()

        # Apply dynamic stop-loss and take-profit levels based on ATR
        df['Stop Loss'] = df['close'] - stop_loss_factor * df['ATR']
        df['Take Profit'] = df['close'] + take_profit_factor * df['ATR']

        return df


    def backtest_strategy(self, strategy_data, initial_balance=1000):
        balance = initial_balance
        position = 0
        b_trades = 0
        s_trades = 0
        fee_total = 0
        tds_total = 0
        # print(strategy_data)
        for i in range(1, len(strategy_data)):
            # Simulate Buy Signal
            if strategy_data['Signal'].iloc[i] == 1:
                units = (balance * (1 - self.transaction_cost_pct)) / strategy_data['close'].iloc[i]
                position += units
                balance -= units * strategy_data['close'].iloc[i]
                balance -= units * strategy_data['close'].iloc[i] * self.transaction_cost_pct
                fee_total += units * strategy_data['close'].iloc[i] * self.transaction_cost_pct
                b_trades += 1
            # Simulate Sell Signal
            elif strategy_data['Signal'].iloc[i] == -1:
                units = position
                position -= units
                balance += units * strategy_data['close'].iloc[i]
                balance -= units * strategy_data['close'].iloc[i] * self.transaction_cost_pct
                fee_total += units * strategy_data['close'].iloc[i] * self.transaction_cost_pct
                balance -= units * strategy_data['close'].iloc[i] * self.tds_cost_pct
                tds_total += units * strategy_data['close'].iloc[i] * self.tds_cost_pct
                s_trades += 1

        # Calculate final balance
        balance += position * strategy_data['close'].iloc[-1]
        
        return balance, b_trades, s_trades, fee_total, tds_total


    def optimize_strategy_parameters(self):
        df = marketdata.get_market_data(symbol, bar_length)
        if df is None or df.empty:
            return

        best_params = {'fibonacci_level': 0, 'ma_period': 0, 'atr_period': 0, 'stop_loss_factor': 0, 'take_profit_factor': 0}
        best_balance = float('-inf')

        for fib_level in self.fibonacci_levels:
            for ma_period in self.ma_periods:
                for atr_period in self.atr_periods:
                    for stop_loss_factor in self.stop_loss_factors:
                        for take_profit_factor in self.take_profit_factors:
                            strategy_data = self.fibonacci_retracement_strategy(df, fib_level, ma_period, atr_period)
                            # final_balance = self.backtest_strategy(strategy_data)
                            # print(fib_level, ma_period, atr_period, stop_loss_factor, take_profit_factor)
                            final_balance, b_trades, s_trades, fee_total, tds_total = self.backtest_strategy(strategy_data=strategy_data)
                            # print(final_balance)
                            if final_balance > best_balance:
                                best_balance = final_balance
                                total_buy = b_trades
                                total_sell = s_trades
                                final_fee = fee_total
                                final_tds = tds_total
                                best_params = {
                                    'fibonacci_level': fib_level,
                                    'ma_period': ma_period,
                                    'atr_period': atr_period,
                                    'stop_loss_factor': stop_loss_factor,
                                    'take_profit_factor': take_profit_factor
                                }

        return best_balance, best_params, total_buy, total_sell, final_fee, final_tds

if __name__ == "__main__":
    # symbol = input("Please Enter the Symbol you want to check: ")
    # bar_length = input("Please Enter the bar length you are using currently: ")
    symbol = "BTCUSDT"
    bar_length = "30m"

    fibonacci_levels = [0.382, 0.5, 0.618]
    ma_periods = [10, 20, 50, 100, 150]
    atr_periods = [10, 14, 20, 35]
    min_holding_period = 2
    stop_loss_factors = [1.0, 1.5]
    take_profit_factors = [1.5, 2.0, 2.5, 3.0]

    fibonacci_strategy = FibonacciRetracementStrategy(symbol, bar_length, fibonacci_levels, ma_periods, atr_periods, min_holding_period, stop_loss_factors, take_profit_factors)
    best_balance, best_params, total_buy, total_sell, final_fee, final_tds = fibonacci_strategy.optimize_strategy_parameters()

    print(f"Best Parameters: {best_params}")
    print(f"Best Final Balance: {best_balance:.2f}")
    print(f"Best total_buy: {total_buy:.2f}")
    print(f"Best total_sell: {total_sell:.2f}")
    print(f"Best final_fee: {final_fee:.2f}")
    print(f"Best final_tds: {final_tds:.2f}")
