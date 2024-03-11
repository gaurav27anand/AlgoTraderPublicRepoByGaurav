import time
import locale
import sys
import os
import requests
from datetime import datetime, timedelta
import pandas as pd
import pandas_ta as ta

class RealTimeDMARSIVolumeTrader:
    def __init__(self, symbol, bar_length, fast_ma_range, slow_ma_range, rsi_threshold_range, volume_threshold_range, starting_balance=15000):
        self.symbol = symbol
        self.bar_length = bar_length
        self.fast_ma_range = fast_ma_range
        self.slow_ma_range = slow_ma_range
        self.rsi_threshold_range = rsi_threshold_range
        self.volume_threshold_range = volume_threshold_range
        self.starting_balance = starting_balance
        self.position = 0
        self.total_traded_amount = 0
        self.fees_percentage = 0.005  # Hardcoded fees percentage
        self.min_balance_threshold = 0.10 * self.starting_balance
        self.sleep_time = {'1m': 60, '15m': 900, '30m': 1800, '1h': 3600}.get(self.bar_length, 60)  # Default to 60 seconds
        self.initial_investment = self.starting_balance
        self.profit_percentage_threshold = 0.25  # 25% profit threshold
        self.count_sell = 0
        self.count_buy = 0
        self.total_amount_sell = 0
        self.total_amount_buy = 0
        self.total_amount_fees = 0
        locale.setlocale(locale.LC_MONETARY, 'en_IN')

    def get_market_data(self):
        url = f"https://api.coindcx.com/exchange/v1/markets_details"
        try:
            response = requests.get(url)
            response.raise_for_status()
            markets_details = response.json()

            pair = self.get_pair_details(self.symbol, markets_details)
            if pair:
                now = datetime.utcnow()
                past = now - timedelta(days=2)
                str_start = int(past.timestamp()) * 1000
                str_end = int(now.timestamp()) * 1000

                url = f'https://public.coindcx.com/market_data/candles?pair={pair}&interval={self.bar_length}&startTime={str_start}&endTime={str_end}&limit=1000'
                response = requests.get(url)

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

    def backtestToGetBestParams(self, symbol):
        # print("Running backtest to get best params based on current data for this run . . .\n")
        # fast_ma_range_values = self.fast_ma_range
        # slow_ma_range_values = self.slow_ma_range
        # rsi_threshold_values = self.rsi_threshold_range
        # volume_threshold_values = self.volume_threshold_range

        # Add logic to find best parameters based on backtesting
        # You can use similar logic as in the previous backtesting script

        # best_params = {'fast_ma': 0, 'slow_ma': 0, 'rsi_threshold': 0, 'volume_threshold': 0}
        # best_balance = float('-inf')

        # for fast_ma in fast_ma_range_values:
            # for slow_ma in slow_ma_range_values:
                # for rsi_threshold in rsi_threshold_values:
                    # for volume_threshold in volume_threshold_values:
                        Your backtesting logic here

        # print(f"\nBest Params are Fast MA: {best_params['fast_ma']}, Slow MA: {best_params['slow_ma']}, RSI Threshold: {best_params['rsi_threshold']}, Volume Threshold: {best_params['volume_threshold']} \n")

        # return best_params
        
        fast_sma = 44
        slow_sma = 200
        

    def run_real_time_trader(self):
        best_params = self.backtestToGetBestParams(self.symbol)
        print(f"Best Params: {best_params}")
        while True:
            # Fetch the latest market data
            df = self.get_market_data()
            if df is not None and not df.empty:
                # Calculate Double Moving Averages
                df['Fast_MA'] = df['close'].rolling(window=fast_ma).mean()
                df['Slow_MA'] = df['close'].rolling(window=slow_ma).mean()

                # Calculate RSI
                df['RSI'] = ta.rsi(df['close'], length=14)

                # Simulate trading
                # balance = self.initial_balance
                position = 0
                b_trades = 0
                s_trades = 0

                for i in range(1, len(df)):
                    if df['Fast_MA'].iloc[i] > df['Slow_MA'].iloc[i] and df['Fast_MA'].iloc[i-1] <= df['Slow_MA'].iloc[i-1] \
                            and df['RSI'].iloc[i] < rsi_threshold and df['volume'].iloc[i] > volume_threshold:
                        # Buy Signal
                        print(f"Initial Position : {self.position} | Initial Balance : {self.starting_balance} ")
                        max_trade_amount = min(0.3 * self.starting_balance, self.starting_balance)
                        units = (max_trade_amount * (1 - self.fees_percentage)) / df['close'].iloc[i]  # Adjust for fees
                        self.position += units
                        self.starting_balance -= units * df['close'].iloc[-1]
                        self.starting_balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                        self.total_traded_amount += units * df['close'].iloc[-1]
                        fees = self.fees_percentage * units * df['close'].iloc[-1]
                        self.total_traded_amount -= fees
                        total_trade_amount = df['close'].iloc[-1] * units
                        total_trade_amount -= fees
                        print("--------------------------------------------------------------------------------------------")
                        print(f"Buy Signal | Units: {units:.15f} | Price: {locale.currency(df['close'].iloc[-1], grouping=True)} | Total Buy Amount: {locale.currency(total_trade_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)}")
                        print("--------------------------------------------------------------------------------------------")
                        self.count_buy += 1
                        self.total_amount_buy += total_trade_amount
                        self.total_amount_fees += fees
                        

                    elif df['Fast_MA'].iloc[i] < df['Slow_MA'].iloc[i] and df['Fast_MA'].iloc[i-1] >= df['Slow_MA'].iloc[i-1] \
                            and df['RSI'].iloc[i] > rsi_threshold and df['volume'].iloc[i] > volume_threshold:
                        # Sell Signal
                        units = self.position
                        sell_price = df['close'].iloc[-1]
                        sell_amount = units * sell_price
                        fees = self.fees_percentage * units * sell_price
                        total_sell_amount = sell_amount - fees
                        
                        if self.total_traded_amount + total_sell_amount < self.total_traded_amount:
                            # Prevent sell if it results in a loss
                            print("--------------------------------------------------------------------------------------------")
                            print(f"Sell Signal Ignored | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)}")
                            print("--------------------------------------------------------------------------------------------")
                        else:
                            self.position -= units
                            self.starting_balance += units * df['close'].iloc[i]
                            self.starting_balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                            self.total_traded_amount += total_sell_amount
                            print("--------------------------------------------------------------------------------------------")
                            print(f"Sell Signal | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)}")
                            print("--------------------------------------------------------------------------------------------")
                            self.count_sell += 1
                            self.total_amount_sell += total_sell_amount
                            self.total_amount_fees += fees
                        
                        
                # Print current balance
                price = df['close'].iloc[-1]
                position_price = price * self.position
                over_all_status_amount = position_price + self.starting_balance
                print("\n**************************************************************************************************************************************************")
                print(f"#    Current Money Balance: {locale.currency(self.starting_balance, grouping=True)} | Crypto [{self.symbol}] in Holding: {self.position:.15f} | Value : {locale.currency(position_price, grouping=True)} | Overall Value of account : {locale.currency(over_all_status_amount, grouping=True)}   #")
                print(f"#    Count of Buy Trades : {self.count_buy} | Count of Sell Trades : {self.count_sell}  ||  Total Amount Bought : {self.total_amount_buy} | Total Amount Sold : {self.total_amount_sell} | Total Fees Paid: {self.total_amount_fees}  #")
                print("**************************************************************************************************************************************************\n")
                
                # Sleep for a specified interval before fetching the next data
                time.sleep(self.sleep_time)

if __name__ == "__main__":
    symbol_to_forward_test = "BTCINR"
    fast_ma_range_values = range(5, 21)
    slow_ma_range_values = range(20, 41)
    rsi_threshold_values = range(30, 71, 10)
    volume_threshold_values = range(100, 1001, 100)
    user_starting_balance = 20000
    try:
        real_time_trader = RealTimeDMARSIVolumeTrader(symbol=symbol_to_forward_test, bar_length='1d',
                                                      fast_ma_range=fast_ma_range_values,
                                                      slow_ma_range=slow_ma_range_values,
                                                      rsi_threshold_range=rsi_threshold_values,
                                                      volume_threshold_range=volume_threshold_values,
                                                      starting_balance=user_starting_balance)
        real_time_trader.run_real_time_trader()

    except KeyboardInterrupt:
        print('Interrupted by user')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
