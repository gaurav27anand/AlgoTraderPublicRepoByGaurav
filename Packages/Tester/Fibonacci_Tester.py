import time
import locale
import json
import hmac
import hashlib
import requests
from datetime import datetime, timedelta, timezone
from pytz import timezone 
import sys, os
import pandas as pd
import numpy as np
from decimal import Decimal
import base64


def fibonacci_retracement_strategy(df, fibonacci_level=0.618, ma_period=20, atr_period=14, min_holding_period=5, stop_loss_factor=1.5, take_profit_factor=2.0):
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

def backtest_strategy(df, initial_balance=1000, transaction_cost_pct=0.005):
    balance = initial_balance
    position_size_pct = 0.2  # 20% of the available balance per trade
    min_holding_days = 5  # Minimum holding period in trading days

    # Initialize variables for tracking position and holding days
    shares_bought = 0
    entry_price = 0
    holding_days = 0
    buy_count = 0
    sell_count = 0

    for index, row in df.iterrows():
        if row['Position'] == 1:  # Buy signal
            shares_bought = int((balance * position_size_pct) / row['close'])
            transaction_cost = shares_bought * row['close'] * transaction_cost_pct
            balance -= (shares_bought * row['close']) + transaction_cost
            entry_price = row['close']
            holding_days = 0
            buy_count += 1
        elif row['Position'] == -1:  # Sell signal
            balance += (shares_bought * row['close']) - transaction_cost
            shares_bought = 0
            entry_price = 0
            holding_days = 0
            sell_count += 1
        else:
            # Hold position and update holding days
            holding_days += 1

            # Check if the minimum holding period is reached
            if holding_days >= min_holding_days:
                # Apply stop-loss and take-profit conditions
                if row['close'] <= row['Stop Loss'] or row['close'] >= row['Take Profit']:
                    balance += (shares_bought * row['close']) - transaction_cost
                    shares_bought = 0
                    entry_price = 0
                    holding_days = 0
                    sell_count += 1
                    
    print(f"
    # Print buy and sell signals
    # for index, row in df.iterrows():
        # if row['Position'] == 1:
            # print(f"Buy Signal at {index}")
        # elif row['Position'] == -1:
            # print(f"Sell Signal at {index}")

    # Consider the final position at the last data point
    if shares_bought > 0:
        balance += (shares_bought * df['close'].iloc[-1]) - transaction_cost

    print(balance)
    return balance


def optimize_strategy_parameters(symbol, bar_length):
    # Fetch historical data
    # df = fetch_historical_data(symbol, bar_length)
    df = marketdata.get_market_data2(symbol, bar_length)
    if df is None:
        return None, None

    # Define parameter ranges for optimization
    fibonacci_levels = [0.382, 0.5, 0.618]
    ma_periods = [10, 20, 50]
    atr_periods = [10, 14, 20]
    min_holding_periods = [3, 5, 7]
    stop_loss_factors = [1.0, 1.5, 2.0]
    take_profit_factors = [1.5, 2.0, 2.5]

    best_final_balance = float('-inf')
    best_parameters = {}

    for fib_level in fibonacci_levels:
        for ma_period in ma_periods:
            for atr_period in atr_periods:
                for min_holding_period in min_holding_periods:
                    for stop_loss_factor in stop_loss_factors:
                        for take_profit_factor in take_profit_factors:
                            # Apply Fibonacci retracement strategy
                            strategy_data = fibonacci_retracement_strategy(df, 
                                                                           fibonacci_level=fib_level,
                                                                           ma_period=ma_period,
                                                                           atr_period=atr_period,
                                                                           min_holding_period=min_holding_period,
                                                                           stop_loss_factor=stop_loss_factor,
                                                                           take_profit_factor=take_profit_factor)

                            # Backtest the strategy
                            final_balance = backtest_strategy(strategy_data)
                            
                            if final_balance > 1000:
                                print(final_balance)

                            # Update best parameters if current iteration is more profitable
                            if final_balance > best_final_balance:
                                best_final_balance = final_balance
                                best_parameters = {
                                    'fibonacci_level': fib_level,
                                    'ma_period': ma_period,
                                    'atr_period': atr_period,
                                    'min_holding_period': min_holding_period,
                                    'stop_loss_factor': stop_loss_factor,
                                    'take_profit_factor': take_profit_factor
                                }

    return best_final_balance, best_parameters

def main():
    # Define the trading symbol and date range for backtesting
    symbol = input("Please Enter the Symbol you want to check: ")
    bar_length = input("Please Enter the bar length you are using currently: ")
    # Fetch historical data
    data = marketdata.get_market_data2(symbol, bar_length)

    if data is not None:
        # Optimize strategy parameters
        best_balance, best_params = optimize_strategy_parameters(symbol, bar_length)

        # Print the best parameters and corresponding final balance
        print(f"Best Parameters: {best_params}")
        print(f"Best Final Balance: ${best_balance:.2f}")

if __name__ == "__main__":
    import os, sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from MarketData import marketdata
    from Logger import logger
    from TradeExtractor.CoinDCX import extractor
    from GetPrice.CoinDCX import priceFinder
    from ExchangeConnector.CoinDCX import test_exchange as exchange
    main()
else:
    from Packages.MarketData import marketdata
    from MarketData import marketdata
    from Packages.MarketData import marketdata
    from Packages.Logger import logger
    from Packages.TradeExtractor.CoinDCX import extractor
    from Packages.GetPrice.CoinDCX import priceFinder
    from Packages.ExchangeConnector.CoinDCX import test_exchange as exchange
    

