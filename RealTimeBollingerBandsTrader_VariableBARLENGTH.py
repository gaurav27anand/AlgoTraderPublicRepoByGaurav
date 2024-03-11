import time
import locale
from BollingerBandsForwardTester import BollingerBandsForwardTester

class RealTimeBollingerBandsTrader(BollingerBandsForwardTester):
    def __init__(self, symbol, bar_length, bar_lengths, window_range, num_std_dev_range, initial_balance=1000):
        super().__init__(symbol, bar_length, window_range, num_std_dev_range, initial_balance)
        self.position = 0
        self.total_traded_amount = 0
        self.fees_percentage = 0.005  # Hardcoded fees percentage
        self.min_balance_threshold = 0.15 * self.initial_balance
        self.sleep_time = {'1m': 60, '15m': 900, '1h': 3600}.get(self.bar_length, 60)  # Default to 60 seconds
        self.initial_investment = self.initial_balance
        self.profit_percentage_threshold = 0.15  # 15% profit threshold
        self.count_sell = 0
        self.count_buy = 0
        locale.setlocale(locale.LC_MONETARY, 'en_IN')
        self.bar_lengths = bar_lengths
        
    def backtestToGetBestParams(self, symbol):
        print("Running backtest to get best params based on current data for this run . . .\n")
        window_range_values = self.window_range  
        num_std_dev_range_values = self.num_std_dev_range
        best_results = []
        for bar_length in self.bar_lengths:
            forward_tester = BollingerBandsForwardTester(symbol=self.symbol, bar_length=bar_length, window_range=window_range_values, num_std_dev_range=num_std_dev_range_values)
            std_dev, window, best_balance, all_B_trades, all_S_trades, chosen_bar_length = forward_tester.forward_test_bollinger_bands_strategy_with_fees(bar_length)
            best_results.append((std_dev, window, best_balance, all_B_trades, all_S_trades, chosen_bar_length))

        # Find the best result based on maximum returns
        best_result = max(best_results, key=lambda x: x[2])
        std_dev, window, best_balance, all_B_trades, all_S_trades, chosen_bar_length = best_result
        print(f"Std Dev: {std_dev} | Window: {window} | Balance : {best_balance} | Chosen Bar Length: {chosen_bar_length}")
        print(f"Total Buy Trades : {all_B_trades} | Total Sell Trades : {all_S_trades}")
        
        self.bar_length = chosen_bar_length
        print("----------------------------------------------------------------------------------------------------------")
        print(f"    Best Params are Standard Deviation: {std_dev} | Window: {window} | Bar Length : {chosen_bar_length}     ")
        print("----------------------------------------------------------------------------------------------------------")
        return std_dev, window, self.bar_length

    def run_real_time_trader(self):
        self.num_std_dev, self.window, self.bar_length = self.backtestToGetBestParams(self.symbol)
        print("Starting the Real Time Trading Action using th bellow parameters:")
        print(f"Deviation: {self.num_std_dev} | Window: {self.window} | Bar Length : {self.bar_length}")
        while True:
            # Fetch the latest market data
            df = self.get_market_data()
            if df is not None and not df.empty:
                # Calculate Bollinger Bands
                df['MA'] = df['close'].rolling(window=self.window).mean()
                df['Upper'] = df['MA'] + (self.num_std_dev * df['close'].rolling(window=self.window).std())
                df['Lower'] = df['MA'] - (self.num_std_dev * df['close'].rolling(window=self.window).std())
                # Calculate profit percentage
                current_value = self.position * df['close'].iloc[-1]
                profit_percentage = ((current_value - self.initial_investment) / self.initial_investment) * 100
            
                if profit_percentage >= self.profit_percentage_threshold:
                    # Exit position if profit reaches 15%
                    units = self.position
                    sell_price = df['close'].iloc[-1]
                    sell_amount = units * sell_price
                    fees = self.fees_percentage * units * sell_price
                    total_sell_amount = sell_amount - fees
                    self.position = 0
                    self.total_traded_amount += total_sell_amount
                    self.initial_balance += total_sell_amount
                    print("--------------------------------------------------------------------------------------------")
                    print(f"Profit Exit Signal | Profit Percentage: {profit_percentage:.2f}% | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)}")
                    print("--------------------------------------------------------------------------------------------")
                    self.count_sell += 1

                # Check the latest data point for a trading signal
                if df['close'].iloc[-1] < df['Lower'].iloc[-1] and self.initial_balance > self.min_balance_threshold:
                    # Buy Signal
                    print(f"Initial Position : {self.position} | Initial Balance : {self.initial_balance} ")
                    max_trade_amount = min(0.2 * self.initial_balance, self.initial_balance)
                    units = max_trade_amount / df['close'].iloc[-1]
                    self.position += units
                    self.initial_balance -= units * df['close'].iloc[-1]
                    self.total_traded_amount += units * df['close'].iloc[-1]
                    fees = self.fees_percentage * units * df['close'].iloc[-1]
                    self.total_traded_amount += fees
                    total_trade_amount = df['close'].iloc[-1] * units
                    print("--------------------------------------------------------------------------------------------")
                    print(f"Buy Signal | Units: {units:.15f} | Price: {locale.currency(df['close'].iloc[-1], grouping=True)} | Total Buy Amount: {locale.currency(total_trade_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)}")
                    print("--------------------------------------------------------------------------------------------")
                    self.count_buy += 1

                elif df['close'].iloc[-1] > df['Upper'].iloc[-1] and self.position > 0:
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
                            self.position = 0
                            self.total_traded_amount += total_sell_amount
                            self.initial_balance += total_sell_amount
                            print("--------------------------------------------------------------------------------------------")
                            print(f"Sell Signal | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)}")
                            print("--------------------------------------------------------------------------------------------")
                            self.count_sell += 1

                # Print current balance
                price = df['close'].iloc[-1]
                position_price = price * self.position
                over_all_status_amount = position_price + self.initial_balance
                print("\n**************************************************************************************************************************************************")
                print(f"#    Current Money Balance: {locale.currency(self.initial_balance, grouping=True)} | Crypto [{self.symbol}] in Holding: {self.position:.15f} | Value : {locale.currency(position_price, grouping=True)} | Overall Value of account : {locale.currency(over_all_status_amount, grouping=True)}   #")
                print(f"#    Count of Buy Trades : {self.count_buy} | Count of Sell Trades : {self.count_sell}      #")
                print("**************************************************************************************************************************************************\n")
            else:
                print("No data received from the Market API")

            # Sleep for a specified interval before fetching the next data
            time.sleep(self.sleep_time)

if __name__ == "__main__":
    symbol_to_forward_test = "BTCINR"
    window_value_range = range(1, 200)
    num_std_dev_range_values = range(1, 4)
    # bar_lengths = ['1m', '15m', '30m', '1h']
    bar_lengths = ['1m', '15m', '30m']
    real_time_trader = RealTimeBollingerBandsTrader(symbol=symbol_to_forward_test, bar_length='15m', bar_lengths=bar_lengths, window_range=window_value_range, num_std_dev_range=num_std_dev_range_values)
    real_time_trader.run_real_time_trader()
