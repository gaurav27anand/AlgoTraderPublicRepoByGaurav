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
from Packages.Tester.BollingerBandsForwardTester import BollingerBandsForwardTester
from Packages.MarketData import marketdata
from Packages.Logger import logger
from Packages.TradeExtractor.CoinDCX import extractor
from Packages.GetPrice.CoinDCX import priceFinder
from Packages.ExchangeConnector.CoinDCX import test_exchange as exchange

def get_next_start_time(bar_length):
    current_time = datetime.now()
    current_minute = current_time.minute

    if bar_length == '1m':
        valid_minutes = list(range(1, 61))
    elif bar_length == '5m':
        valid_minutes = list(range(1, 61, 5))
    elif bar_length == '15m':
        valid_minutes = list(range(1, 61, 15))
    elif bar_length == '30m':
        valid_minutes = list(range(1, 61, 30))
    elif bar_length == '1h':
        valid_minutes = [1]
    else:
        raise ValueError("Unsupported bar_length")

    next_start_time = current_time.replace(second=0, microsecond=0)

    for minute in valid_minutes:
        if current_minute < minute:
            next_start_time = next_start_time.replace(minute=minute)
            break

    if current_minute >= valid_minutes[-1]:
        next_start_time += timedelta(hours=1)
        next_start_time = next_start_time.replace(minute=valid_minutes[0])

    return next_start_time


class RealTimeBollingerBandsTrader(BollingerBandsForwardTester):

    starting_timestamp = datetime.now(timezone("Asia/Kolkata")).strftime('%Y%m%d%H%M%S')
    
    def __init__(self, symbol, bar_length, window_range, num_std_dev_range,
                    starting_balance=15000, cname='', given_window="", given_stdDev="", reset_period=4):
        super().__init__(symbol, bar_length, window_range, num_std_dev_range, initial_balance=starting_balance)
        # self.starting_balance = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret, target_currency='INR')
        self.starting_balance = starting_balance
        self.cname = cname
        
        self.amount_precision, self.quantity_precision, self.order_types, self.crypto_name, self.currency_name, self.min_trade_amount = marketdata.get_precision(self.symbol)
                
        if "market_order" in self.order_types:
            self.order_allowed = 2
        else:
            self.order_allowed = 1
        
        logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"\n\t\t\t\t\t Starting Trade for : {self.crypto_name} ==> {self.symbol} \n\n \t Initial Balance (INR) :{self.starting_balance} | Amount Precision Required: {self.amount_precision} || Quantity Precision Required: {self.quantity_precision} \n\n\t\t\t\t Allowed Order Types: {self.order_types}\n", type="plus")
        
        self.position = 0
        self.reset_period = reset_period
        minimum_profit = 20
        self.maximum_profit = 150
        self.maximum_loss = 20
        self.minumum_profit_percentage = 1 + (minimum_profit / 100)
        self.maximum_profit_percentage = 1 + (self.maximum_profit / 100)
        self.maximum_loss_percentage = 1 - (self.maximum_loss / 100)
        self.total_traded_amount = 0
        self.fees_percentage = 0.005  # Hardcoded fees percentage
        self.tds_percentage = 0.01  # Hardcoded 1% TDS for sell transations
        self.min_balance_threshold = 0.10 * self.starting_balance
        self.sleep_time = {'1m': 60, '5m': 300, '15m': 900, '30m': 1800, '1h': 3600}.get(self.bar_length, 60)  # Default to 60 seconds
        self.initial_investment = self.starting_balance
        self.count_sell = 0
        self.count_buy = 0
        self.total_amount_sell = 0
        self.total_amount_buy = 0
        self.total_amount_fees = 0
        self.total_amount_tds = 0
        self.last_buy_price = 0
        self.last_buy_time = 0
        self.last_sell_time = 0
        self.cum_profits = 0
        self.trades = 0
        self.highest_value = 0
        self.highest_value_time = 0
        locale.setlocale(locale.LC_MONETARY, 'en_IN')
        start_time_str = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
        self.start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        self.given_window = given_window
        self.given_stdDev = given_stdDev
        
        
    def update_last_buy_price(self, side="sell", buy_price=0):
        if side == "buy":
            if not self.last_buy_price == 0:
                self.last_buy_price = max(self.last_buy_price, buy_price)
            else:
                self.last_buy_price = buy_price
        elif side == "sell":
            self.last_buy_price = 0


    def backtestToGetBestParams(self, symbol):
        print("Running backtest to get best params based on current data for this run . . .\n")
        window_range_values = self.window_range
        num_std_dev_range_values = self.num_std_dev_range
        forward_tester_BB = BollingerBandsForwardTester(symbol=self.symbol, bar_length=self.bar_length,
                                                     window_range=window_range_values,
                                                     num_std_dev_range=num_std_dev_range_values,
                                                     initial_balance=self.starting_balance)
        std_dev, window, best_balance, all_B_trades, all_S_trades, chosen_bar_length, total_fee, total_tds = forward_tester_BB.forward_test(self.bar_length)

        print(f"\nBest Params are Standard Deviation: {std_dev} and Window: {window} || With initial Investment of {self.starting_balance} got final (trade+holding) : {best_balance}\n")

        return std_dev, window

    def run_real_time_trader(self, api_key, api_secret):
        self.loop_start_time = datetime.now(timezone("Asia/Kolkata"))
        if not self.given_window  or not self.given_stdDev:
            self.num_std_dev, self.window = self.backtestToGetBestParams(self.symbol)
        else:
            self.num_std_dev = self.given_stdDev
            self.window = self.given_window
            
        print(f"Standard Deviation: {self.num_std_dev} | Window: {self.window} || These settings will be reset in {self.reset_period} hours.")
        while True:
            
            current_time = datetime.now(timezone("Asia/Kolkata")).astimezone(timezone("UTC"))
            elapsed_time = current_time - self.loop_start_time
            
            # Calculate remaining time
            remaining_time = timedelta(hours=self.reset_period) - (current_time - self.loop_start_time)
            remaining_hours, remaining_minutes = divmod(remaining_time.seconds, 3600)
            remaining_minutes, seconds = divmod(remaining_minutes, 60)            
            
            logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Time left to reset: {remaining_hours} hours and {remaining_minutes} minutes", type="underscore")
            
            
            if elapsed_time >= timedelta(hours=self.reset_period):
                print(f"{self.reset_period} hours have passed since the start. Resetting the Standard Deviation and Window after backtest.")
                self.loop_start_time = datetime.now(timezone("Asia/Kolkata"))                
                # self.num_std_dev, self.window = self.backtestToGetBestParams(self.symbol)
                if not self.given_window  or not self.given_stdDev:
                    self.num_std_dev, self.window = self.backtestToGetBestParams(self.symbol)
                    print(f"New: Standard Deviation: {self.num_std_dev} | Window: {self.window}")
                else:
                    self.num_std_dev = self.given_stdDev
                    self.window = self.given_window
                    print(f"Keeping the same Standard Deviation: {self.num_std_dev} | Window: {self.window} as its user provided")
                    
                
            # Fetch the latest market data
            # df = self.get_market_data()
            df = marketdata.get_market_data2(self.symbol, self.bar_length)
            if df is not None and not df.empty:
                # Calculate Bollinger Bands
                df['MA'] = df['close'].rolling(window=self.window).mean()
                df['Upper'] = df['MA'] + (self.num_std_dev * df['close'].rolling(window=self.window).std())
                df['Lower'] = df['MA'] - (self.num_std_dev * df['close'].rolling(window=self.window).std())
                # print(df.iloc[-1])
                # print("\n\n")
                # print(df.iloc[-2])
                latest_price = priceFinder.get_latest_price(self.symbol, self.amount_precision)
                buy_signal = False
                sell_signal = False
                # print(f" Last Moving Average of {self.window} period on bar length : {self.bar_length} ==> {df['MA'].iloc[-2]} \n Last Upper Value ==> {df['Upper'].iloc[-2]} \n Last Lower Value ==> {df['Lower'].iloc[-2]} \n Last Close Price ==> {df['close'].iloc[-2]} \n Latest Price==> {latest_price}  \n")
                # Calculate profit percentage
                # self.position = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret, target_currency=self.cname)
                # print(self.position)
                current_value = self.position * df['close'].iloc[-2]
                
                if self.total_traded_amount > 500000:
                    self.fees_percentage = 0.0025
                elif self.total_traded_amount > 7500000:
                    self.fees_percentage = 0.0015
                elif self.total_traded_amount > 50000000:
                    self.fees_percentage = 0.0012
                elif self.total_traded_amount > 100000000:
                    self.fees_percentage = 0.001
                else:
                    self.fees_percentage = 0.005

                # self.starting_balance = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret)
                max_trade_amount = min(0.35 * self.starting_balance, self.starting_balance)
                # units = (max_trade_amount * (1 - self.fees_percentage)) / df['close'].iloc[-2]  # Adjust for fees
                
                max_decimal_points_amount = self.amount_precision
                max_decimal_points_quantity = self.quantity_precision
                
                price = round(priceFinder.get_ask_price(self.symbol), max_decimal_points_amount)
                price = max(price, df['close'].iloc[-2])
                units = round((max_trade_amount * (1 - self.fees_percentage)) / price, max_decimal_points_quantity)
                # print(units)
                trade_amount = units * price
                
                # Check the latest data point for a trading signal
                # print(f"Last Close: {df['close'].iloc[-2]} | Last Lower: {df['Lower'].iloc[-2]} | Last Upper: {df['Upper'].iloc[-2]} || Second Last Close: {df['close'].iloc[-2]} | Second Last Lower: {df['Lower'].iloc[-2]} | Second Last Upper: {df['Upper'].iloc[-2]}")
                # if df['close'].iloc[-2] < df['Lower'].iloc[-2] and df['close'].iloc[-2] < df['Lower'].iloc[-2] and self.starting_balance > self.min_balance_threshold and units > 0 and trade_amount >= self.min_trade_amount:
                # if df['close'].iloc[-2] < df['Lower'].iloc[-2] and self.starting_balance > self.min_balance_threshold and units > 0 and trade_amount >= self.min_trade_amount:
                # if latest_price < df['Lower'].iloc[-2] and df['close'].iloc[-2] <= df['Lower'].iloc[-2] and self.starting_balance > self.min_balance_threshold and units > 0 and trade_amount >= self.min_trade_amount:
                if df['close'].iloc[-2] <= df['Lower'].iloc[-2] and self.starting_balance > self.min_balance_threshold and units > 0 and trade_amount >= self.min_trade_amount:
                    # Buy Signal
                    logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"\t\t\t ----Buy Signal Received | Current Price: {latest_price}----", type="dot")
                    buy_signal = True
                    if buy_signal == True:
                        
                        # self.position = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret, target_currency=self.cname)
                        # self.starting_balance = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret,)
                        print(f"\n Close Price : {df['close'].iloc[-2]} || Ask Price : {price} ")
                        print(f"\nPrice being used to Buy : {price} \n")
                        
                        print(f"Initial Position : {self.position:.15f} | Initial Balance : {self.starting_balance:.4f} ")
                        order_response = exchange.place_market_order(api_key = api_key, api_secret = api_secret, symbol = self.symbol, side = "buy", order_type = "LIMIT", quantity = units, price = price)
                        
                        buy_price, fees, id = extractor.extract_trade_details(order_response, "GOING LONG")
                        
                        
                        
                        self.update_last_buy_price(side="buy", buy_price=buy_price)
                        
                        # fees = units * price * self.fees_percentage
                        
                        status = exchange.get_order_status(id = id, api_key = api_key, api_secret = api_secret)
                        
                        if status == "partially_filled":
                            order_response = exchange.update_price(id=id, side="sell", api_key = api_key, api_secret = api_secret)
                            buy_price, fees, id = extractor.extract_updated_trade_details(order_response, "GOING LONG - Price Update")
                        elif status == "partially_cancelled":
                            order_response = exchange.update_price(id=id, side="sell", api_key = api_key, api_secret = api_secret)
                            buy_price, fees, id = extractor.extract_updated_trade_details(order_response, "GOING LONG - Price Update")
                        
                        # logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Status : {status}", type="hyphen")
                        
                        
                        if status == "filled":
                        
                            # self.position = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret, target_currency=self.cname)
                            self.position += units
                            # self.starting_balance  = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret)
                            self.starting_balance  -= price * units
                            self.total_traded_amount += units * df['close'].iloc[-2]
                            self.total_traded_amount -= fees
                            total_trade_amount = df['close'].iloc[-2] * units
                            total_trade_amount -= fees
                            
                            logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Buy Signal | Units: {units:.15f} | Price: {locale.currency(df['close'].iloc[-2], grouping=True)} | Total Buy Amount: {locale.currency(total_trade_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)} \n\t\t\t Status : {status}", type="hyphen")
                            
                            self.count_buy += 1
                            self.total_amount_buy += total_trade_amount
                            self.total_amount_fees += fees
                            self.last_buy_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %I:%M:%S %p')
                        
                        else:
                            print("Unknown Error, exiting")
                            sys.exit(130)
                    else:
                        print("Buy Signal Ignored as it was not approved")
                # elif latest_price > df['Upper'].iloc[-2] and df['close'].iloc[-2] <= df['Upper'].iloc[-2] and df['close'].iloc[-3] <= df['Upper'].iloc[-3] and self.position > 0 :
                # elif df['close'].iloc[-2] > df['Upper'].iloc[-2] and df['close'].iloc[-2] <= df['Upper'].iloc[-2] and df['close'].iloc[-3] <= df['Upper'].iloc[-3] and self.position > 0 :
                # elif df['high'].iloc[-2] > df['Upper'].iloc[-2] and df["close"].iloc[-2] < df["MA"].iloc[-2] and df["close"].iloc[-3] < df["MA"].iloc[-2] and self.position > 0 :
                elif latest_price > df['Upper'].iloc[-2] and self.position > 0 or df['close'].iloc[-2] > df['Upper'].iloc[-2] and self.position > 0:
                    logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"\t\t\t ----Sell Signal Received  | Current Price : {latest_price} ----", type="dot")
                    sell_signal = True
                    if sell_signal == True:
                        # self.position = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret, target_currency=self.cname)
                        units = round(self.position - 0.5 * 10**(-max_decimal_points_quantity), max_decimal_points_quantity)
                        sell_price = df['close'].iloc[-2]
                        sell_amount = units * sell_price
                        fees = self.fees_percentage * units * sell_price
                        tds_fees = self.tds_percentage * units * sell_price
                        total_sell_amount = sell_amount - fees - tds_fees
                        
                        if units > 0 and total_sell_amount >= self.min_trade_amount and sell_price >= self.minumum_profit_percentage * self.last_buy_price:

                            if self.total_traded_amount + total_sell_amount < self.total_traded_amount:
                                # Prevent sell if it results in a loss
                                logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Sell Signal Ignored | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)} | Fees by Govt(TDS) : {locale.currency(tds_fees, grouping=True)}", type="hyphen")
                            else:
                            
                                price = round(priceFinder.get_bid_price(self.symbol), max_decimal_points_amount)

                                print(f"\n Close Price : {df['close'].iloc[-2]} || Bid Price : {price} ")
                                
                                price = max(price, df['close'].iloc[-2])
                                
                                print(f"\nPrice being used to Sell : {price} \n")
                                
                                if self.order_allowed == 2:
                                    order_response = exchange.place_market_order(api_key = api_key, api_secret = api_secret, symbol = self.symbol, side = "sell", order_type = "MARKET", quantity = units)
                                else:
                                    order_response = exchange.place_market_order(api_key = api_key, api_secret = api_secret, symbol = self.symbol, side = "sell", order_type = "LIMIT", quantity = units, price = price)
                                
                            
                                sell_price, fees, id = extractor.extract_trade_details(order_response, "GOING SHORT")
                                self.update_last_buy_price()
                                self.position -= units
                                self.last_sell_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %I:%M:%S %p')
                                
                                    
                                status = exchange.get_order_status(id = id, api_key = api_key, api_secret = api_secret)
                                tds_fees = self.tds_percentage * units * sell_price
                                
                                sell_amount = units * sell_price
                                total_sell_amount = sell_amount - fees - tds_fees         
                                
                                # self.starting_balance = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret)
                                self.starting_balance += total_sell_amount
                                self.total_traded_amount += total_sell_amount
                                
                                logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Sell Signal | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)} | Fees by Govt. : {locale.currency(tds_fees, grouping=True)} \n\t\t\t Status : {status}", type="hyphen")
                                self.count_sell += 1
                                self.total_amount_sell += total_sell_amount
                                self.total_amount_fees += fees
                                self.total_amount_tds += tds_fees
                                
                        else:
                            print("Sell Signal Ignored as sell price is lower than buy price")
                    else:
                        print("Sell Signal Ignored as it was not approved")
                        
                elif self.last_buy_price > 0 and df['close'].iloc[-2] < self.maximum_loss_percentage * self.last_buy_price  and latest_price < self.maximum_loss_percentage * self.last_buy_price : 
                    logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Stop Loss HIT at {latest_price} which is {self.maximum_loss}% negative to Buy Price Average: {self.last_buy_price} || PUT A SELL ORDER MANUALLY", type="hyphen")
                    # self.position = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret, target_currency=self.cname)
                    # units = round(self.position - 0.5 * 10**(-max_decimal_points_quantity), max_decimal_points_quantity)
                    # sell_price = df['close'].iloc[-2]
                    # sell_amount = units * sell_price
                    # fees = self.fees_percentage * units * sell_price
                    # tds_fees = self.tds_percentage * units * sell_price
                    # total_sell_amount = sell_amount - fees - tds_fees
                    
                    # if units > 0 and total_sell_amount >= self.min_trade_amount and sell_price >= self.minumum_profit_percentage * self.last_buy_price:

                        # if self.total_traded_amount + total_sell_amount < self.total_traded_amount:
                            # # Prevent sell if it results in a loss
                            # logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Sell Signal Ignored | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)} | Fees by Govt(TDS) : {locale.currency(tds_fees, grouping=True)}", type="hyphen")
                        # else:
                        
                            # price = round(priceFinder.get_bid_price(self.symbol), max_decimal_points_amount)

                            # print(f"\n Close Price : {df['close'].iloc[-2]} || Bid Price : {price} ")
                            
                            # price = max(price, df['close'].iloc[-2])
                            
                            # print(f"\nPrice being used to Sell : {price} \n")
                            
                            # if self.order_allowed == 2:
                                # order_response = exchange.place_market_order(api_key = api_key, api_secret = api_secret, symbol = self.symbol, side = "sell", order_type = "MARKET", quantity = units)
                            # else:
                                # order_response = exchange.place_market_order(api_key = api_key, api_secret = api_secret, symbol = self.symbol, side = "sell", order_type = "LIMIT", quantity = units, price = price)
                            
                        
                            # sell_price, fees, id = extractor.extract_trade_details(order_response, "GOING SHORT")
                            
                            # self.update_last_buy_price()
                            
                            # if not fees or fees < 0.1:
                                # time.sleep(2)
                                # fees = exchange.get_fee_collected(id = id, api_key = api_key, api_secret = api_secret)
                                
                            # status = exchange.get_order_status(id = id, api_key = api_key, api_secret = api_secret)
                            # tds_fees = self.tds_percentage * units * sell_price
                            
                            # if status == "partially_filled":
                                # order_response = exchange.update_price(id=id, side="sell",  api_key = api_key, api_secret = api_secret)
                                # buy_price, fees, id = extractor.extract_updated_trade_details(order_response, "GOING LONG - Price Update")
                                
                            # elif status == "partially_cancelled":
                                # order_response = exchange.update_price(id=id, side="sell", api_key = api_key, api_secret = api_secret)
                                # buy_price, fees, id = extractor.extract_updated_trade_details(order_response, "GOING LONG - Price Update")
                            
                            
                            # sell_amount = units * sell_price
                            # total_sell_amount = sell_amount - fees - tds_fees         
                            
                            # self.starting_balance = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret)
                            # self.total_traded_amount += total_sell_amount
                            
                            # logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Sell Signal | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)} | Fees by Govt. : {locale.currency(tds_fees, grouping=True)} \n\t\t\t Status : {status}", type="hyphen")
                            # self.count_sell += 1
                            # self.total_amount_sell += total_sell_amount
                            # self.total_amount_fees += fees
                            # self.total_amount_tds += tds_fees
                
                elif self.last_buy_price > 0 and latest_price >= self.maximum_profit_percentage * self.last_buy_price : 
                    logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f" TARGET of {self.maximum_profit_percentage}% HIT at {latest_price} which is {self.maximum_profit}% upwards to Buy Price Average: {self.last_buy_price}", type="hyphen")
                    # self.position = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret, target_currency=self.cname)
                    units = round(self.position - 0.5 * 10**(-max_decimal_points_quantity), max_decimal_points_quantity)
                    sell_price = df['close'].iloc[-2]
                    sell_amount = units * sell_price
                    fees = self.fees_percentage * units * sell_price
                    tds_fees = self.tds_percentage * units * sell_price
                    total_sell_amount = sell_amount - fees - tds_fees
                    
                    if units > 0 and total_sell_amount >= self.min_trade_amount and sell_price >= self.minumum_profit_percentage * self.last_buy_price:

                        if self.total_traded_amount + total_sell_amount < self.total_traded_amount:
                            # Prevent sell if it results in a loss
                            logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Sell Signal Ignored | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)} | Fees by Govt(TDS) : {locale.currency(tds_fees, grouping=True)}", type="hyphen")
                        else:
                        
                            price = round(priceFinder.get_bid_price(self.symbol), max_decimal_points_amount)

                            print(f"\n Close Price : {df['close'].iloc[-2]} || Bid Price : {price} || Latest Price : {latest_price} ")
                            
                            price = max(price, df['close'].iloc[-2], latest_price)
                            
                            print(f"\nPrice being used to Sell : {price} \n")
                            
                            if self.order_allowed == 2:
                                order_response = exchange.place_market_order(api_key = api_key, api_secret = api_secret, symbol = self.symbol, side = "sell", order_type = "MARKET", quantity = units)
                            else:
                                order_response = exchange.place_market_order(api_key = api_key, api_secret = api_secret, symbol = self.symbol, side = "sell", order_type = "LIMIT", quantity = units, price = price)
                            
                        
                            sell_price, fees, id = extractor.extract_trade_details(order_response, "GOING SHORT")
                            
                            self.update_last_buy_price()
                            self.last_sell_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %I:%M:%S %p')
                            self.position -= units
                            if not fees or fees < 0.1:
                                time.sleep(2)
                                fees = exchange.get_fee_collected(id = id, api_key = api_key, api_secret = api_secret)
                                
                            status = exchange.get_order_status(id = id, api_key = api_key, api_secret = api_secret)
                            tds_fees = self.tds_percentage * units * sell_price
                            
                            if status == "partially_filled":
                                order_response = exchange.update_price(id=id, side="sell",  api_key = api_key, api_secret = api_secret)
                                buy_price, fees, id = extractor.extract_updated_trade_details(order_response, "GOING LONG - Price Update")
                                
                            elif status == "partially_cancelled":
                                order_response = exchange.update_price(id=id, side="sell", api_key = api_key, api_secret = api_secret)
                                buy_price, fees, id = extractor.extract_updated_trade_details(order_response, "GOING LONG - Price Update")
                            
                            # logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Status : {status}", type="hyphen")
                            
                            sell_amount = units * sell_price
                            total_sell_amount = sell_amount - fees - tds_fees         
                            
                            # self.starting_balance = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret)
                            self.starting_balance += total_sell_amount
                            self.total_traded_amount += total_sell_amount
                            
                            logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Sell Signal | Units: {units:.15f}  | Price: {locale.currency(sell_price, grouping=True)} | Total Sell Amount: {locale.currency(total_sell_amount, grouping=True)} | Fees by Exchange : {locale.currency(fees, grouping=True)} | Fees by Govt. : {locale.currency(tds_fees, grouping=True)} \n\t\t\t Status : {status}", type="hyphen")
                            self.count_sell += 1
                            self.total_amount_sell += total_sell_amount
                            self.total_amount_fees += fees
                            self.total_amount_tds += tds_fees
                
                
                
                # Print current balance
                price = priceFinder.get_latest_price(self.symbol, self.amount_precision)
                # self.position = exchange.get_balance_for_currency(api_key=api_key, api_secret=api_secret, target_currency=self.cname)
                position_price = price * self.position
                over_all_status_amount = position_price + self.starting_balance
                # ind_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                current_time_str = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                current_time = datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S')
                time_difference = current_time - self.start_time
                hours, remainder = divmod(time_difference.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                # Format the output with AM/PM
                start_time_formatted = self.start_time.strftime('%Y-%m-%d %I:%M:%S %p')
                current_time_formatted = current_time.strftime('%Y-%m-%d %I:%M:%S %p')
                
                if not self.last_buy_price == 0:
                    current_to_buy_price_percent = ((price - self.last_buy_price) / self.last_buy_price) * 100
                else:
                    current_to_buy_price_percent = 0
                
                if position_price > self.highest_value:
                    self.highest_value = position_price
                    self.highest_value_time = current_time_formatted
                
                logger.print_centered_box(exchange="coindcx", symbol=self.symbol, id=RealTimeBollingerBandsTrader.starting_timestamp,  content=f"Start Time : {start_time_formatted} IST | Current Time: {current_time_formatted} IST || Total Run: {hours} hours, {minutes} minutes, {seconds} seconds | Bar Length: {self.bar_length} \n\n\t Current Money Balance: {locale.currency(self.starting_balance, grouping=True)} | Crypto [{self.symbol}] in Holding: {self.position:.15f} | Value : {locale.currency(position_price, grouping=True)} | Highest Value achieved: {self.highest_value:.4f} at {self.highest_value_time} \n\n\t\t\t\t\t Overall Value of account : {locale.currency(over_all_status_amount, grouping=True)} \n\n\t Count of Buy Trades : {self.count_buy} | Count of Sell Trades : {self.count_sell}  ||  Total Amount Bought : {self.total_amount_buy} | Total Amount Sold : {self.total_amount_sell} | Total Fees Paid: {self.total_amount_fees:.4f} | Total TDS Paid: {self.total_amount_tds:.4f} \n\n\t Last Buy Time: {self.last_buy_time} | Last Buy Price: {self.last_buy_price} | Current Price: {price} [{current_to_buy_price_percent:.2f}% of Last Buy Price] \t|| \t Last Sell Time: {self.last_sell_time}", type="star")
                
            # Sleep for a specified interval before fetching the next data
            time.sleep(self.sleep_time)


if __name__ == "__main__":
    crypto_name = ""
    if not crypto_name:
        crypto_name = input("Enter the crypto name without the base currency : ")
        
    base_currency = "INR"
    bar_length = '15m'
    symbol_to_forward_test = f"{crypto_name}{base_currency}"
    window_value_range = range(1, 101)
    window_value = 6
    stdDevVal = 1
    num_std_dev_range_values = range(1, 3)
    user_starting_balance = 20000
    reset_period = 12
    
    # Get the next valid start time
    script_start_time = get_next_start_time(bar_length)

    # Calculate the waiting time
    wait_time = (script_start_time - datetime.now()).total_seconds()

    # Wait until the next valid start time
    if wait_time > 0:
        print(f"Waiting for {wait_time} seconds until the next valid start time.")
        time.sleep(wait_time)
    
    
    api_key = 'GAURAV_KEY'
    api_secret = 'GAURAV_SECRET'
    start_time_str = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    
    try:
        real_time_trader = RealTimeBollingerBandsTrader(symbol=symbol_to_forward_test, bar_length=bar_length,
                                                        window_range=window_value_range,
                                                        num_std_dev_range=num_std_dev_range_values,
                                                        starting_balance=user_starting_balance,
                                                        cname = crypto_name,
                                                        given_window=window_value, given_stdDev=stdDevVal,
                                                        reset_period=reset_period)
        real_time_trader.run_real_time_trader(api_key, api_secret)

    except KeyboardInterrupt:
        print('Interrupted by user - Exiting')
        ended_at_str = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
        ended_at = datetime.strptime(ended_at_str, '%Y-%m-%d %H:%M:%S')
        time_difference = ended_at - start_time
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        # Format the output with AM/PM
        start_time_formatted = start_time.strftime('%Y-%m-%d %I:%M:%S %p')
        ended_at_formatted = ended_at.strftime('%Y-%m-%d %I:%M:%S %p')
        print(
            f"\n Start Time : {start_time_formatted} IST | End Time: {ended_at_formatted} IST      \n\n      ---------- Total Run Time: {hours} hours, {minutes} minutes, {seconds} seconds  --------- \n\n")
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
