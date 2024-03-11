import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import pandas_ta as ta

class DMARSIVolumeForwardTester:

    def __init__(self, symbol, bar_length, fast_ma_range, slow_ma_range, rsi_threshold_range, volume_threshold_range, fees_percentage=0.005, initial_balance=15000, historical_days=2):
        self.historical_days = historical_days
        self.symbol = symbol
        self.bar_length = bar_length
        self.fast_ma_range = fast_ma_range
        self.slow_ma_range = slow_ma_range
        self.rsi_threshold_range = rsi_threshold_range
        self.volume_threshold_range = volume_threshold_range
        self.fees_percentage = fees_percentage
        self.initial_balance = initial_balance
        self.df = self.get_market_data()

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

                if response.status_code == 200:
                    kline_data = response.json()
                    if not kline_data:
                        print("No data received for the specified time range.")
                        return None

                    df = pd.DataFrame(kline_data, columns=["open", "high", "low", "volume", "close", "time"])
                    df["Date"] = pd.to_datetime(df["time"], unit="ms")
                    start_time = df["Date"].iloc[-1]
                    end_time = df["Date"].iloc[0]
                    
                    print(f"Start Time : {start_time} || End Time: {end_time} ")
                    
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

    def test_parameters(self, params):
        fast_ma, slow_ma, rsi_threshold, volume_threshold = params

        # Fetch the market data
        df = self.df
        # df = self.get_market_data()
        if df is None or df.empty:
            return 0

        # Initialize variables to store the best parameters
        best_balance = float('-inf')

        # Calculate Double Moving Averages
        df['Fast_MA'] = df['close'].rolling(window=fast_ma).mean()
        df['Slow_MA'] = df['close'].rolling(window=slow_ma).mean()

        # Calculate RSI
        df['RSI'] = ta.rsi(df['close'], length=14)

        # Simulate trading
        balance = self.initial_balance
        position = 0
        b_trades = 0
        s_trades = 0

        for i in range(1, len(df)):
            if df['Fast_MA'].iloc[i] > df['Slow_MA'].iloc[i] and df['Fast_MA'].iloc[i-1] <= df['Slow_MA'].iloc[i-1] \
                    and df['RSI'].iloc[i] < rsi_threshold and df['volume'].iloc[i] > volume_threshold:
                # Buy Signal
                units = (balance * (1 - self.fees_percentage)) / df['close'].iloc[i]  # Adjust for fees
                position += units
                balance -= units * df['close'].iloc[i]
                balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                b_trades += 1

            elif df['Fast_MA'].iloc[i] < df['Slow_MA'].iloc[i] and df['Fast_MA'].iloc[i-1] >= df['Slow_MA'].iloc[i-1] \
                    and df['RSI'].iloc[i] > rsi_threshold and df['volume'].iloc[i] > volume_threshold:
                # Sell Signal
                units = position
                position -= units
                balance += units * df['close'].iloc[i]
                balance -= units * df['close'].iloc[i] * self.fees_percentage  # Subtract fees
                s_trades += 1

        # Calculate final balance
        balance += position * df['close'].iloc[-1]

        return (fast_ma, slow_ma, rsi_threshold, volume_threshold), balance, b_trades, s_trades

    def forward_test_dma_rsi_volume_strategy(self):
        # Generate all combinations of parameters
        parameter_combinations = [(fast_ma, slow_ma, rsi_threshold, volume_threshold)
                                  for fast_ma in self.fast_ma_range
                                  for slow_ma in self.slow_ma_range
                                  for rsi_threshold in self.rsi_threshold_range
                                  for volume_threshold in self.volume_threshold_range]

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(self.test_parameters, parameter_combinations))

        # Find the parameters with the best balance
        best_params, best_balance, all_B_trades, all_S_trades = max(results, key=lambda x: x[1])

        return best_params, best_balance, all_B_trades, all_S_trades


if __name__ == "__main__":
    symbol_to_forward_test = "BTCINR"
    fast_ma_range_values = range(5, 50)  # Adjust the range based on your requirements
    slow_ma_range_values = range(100, 200)
    rsi_threshold_values = range(30, 71, 5)
    volume_threshold_values = range(100, 1001, 100)
    history = 2
    forward_tester = DMARSIVolumeForwardTester(symbol=symbol_to_forward_test, bar_length='15m',
                                               fast_ma_range=fast_ma_range_values,
                                               slow_ma_range=slow_ma_range_values,
                                               rsi_threshold_range=rsi_threshold_values,
                                               volume_threshold_range=volume_threshold_values, historical_days=history)
    best_params, best_balance, all_B_trades, all_S_trades = forward_tester.forward_test_dma_rsi_volume_strategy()
    print(f"Best Parameters: {best_params} | Balance: {best_balance}")
    print(f"Total Buy Trades: {all_B_trades} | Total Sell Trades: {all_S_trades}")
