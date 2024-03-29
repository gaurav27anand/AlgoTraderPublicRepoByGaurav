import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from math import floor
from termcolor import colored as cl
from datetime import datetime, timedelta

plt.style.use('fivethirtyeight')
plt.rcParams['figure.figsize'] = (20,10)

# EXTRACTING DATA


def get_market_data2(symbol, bar_length):
    url = f"https://api.coindcx.com/exchange/v1/markets_details"
    try:
        response = requests.get(url)
        response.raise_for_status()
        markets_details = response.json()

        pair = get_pair_details(symbol, markets_details)
        if pair:
            now = datetime.utcnow()
            past = now - timedelta(days=90)  # Fetch last 30 days for forward testing
            str_start = int(past.timestamp()) * 1000
            str_end = int(now.timestamp()) * 1000

            url = f'https://public.coindcx.com/market_data/candles?pair={pair}&interval={bar_length}&startTime={str_start}&endTime={str_end}&limit=1000'
#                 print(url)
            response = requests.get(url)

            if response.status_code == 200:
                kline_data = response.json()
                if not kline_data:
                    print(f"No data received for the specified time range and bar length: {bar_length}.")
                    return None

                df = pd.DataFrame(kline_data, columns=["open", "high", "low", "volume", "close", "time"])
                df["Date"] = pd.to_datetime(df["time"], unit="ms")
                df = df.iloc[::-1]
                # start_time = df["Date"].iloc[0]
                # end_time = df["Date"].iloc[-1]
                # print(f"Start Time: {start_time} || End Time : {end_time}")
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

def get_pair_details(symbol, markets_details):
    for market in markets_details:
        if market['symbol'] == symbol:
            return market['pair']
    return None


btcinr = get_market_data2('MAHAINR', '1h')
print(btcinr)
# SUPERTREND CALCULATION
def get_supertrend(high, low, close, lookback, multiplier):
    
    # ATR
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis = 1, join = 'inner').max(axis = 1)
    atr = tr.ewm(lookback).mean()
    
    # H/L AVG AND BASIC UPPER & LOWER BAND
    
    hl_avg = (high + low) / 2
    upper_band = (hl_avg + multiplier * atr).dropna()
    lower_band = (hl_avg - multiplier * atr).dropna()
    
    # FINAL UPPER BAND
    
    final_bands = pd.DataFrame(columns = ['upper', 'lower'])
    final_bands.iloc[:,0] = [x for x in upper_band - upper_band]
    final_bands.iloc[:,1] = final_bands.iloc[:,0]
    
    for i in range(len(final_bands)):
        if i == 0:
            final_bands.iloc[i,0] = 0
        else:
            if (upper_band.iloc[i] < final_bands.iloc[i-1,0]) | (close.iloc[i-1] > final_bands.iloc[i-1,0]):
                final_bands.iloc[i,0] = upper_band.iloc[i]
            else:
                final_bands.iloc[i,0] = final_bands.iloc[i-1,0]
    
    # FINAL LOWER BAND
    
    for i in range(len(final_bands)):
        if i == 0:
            final_bands.iloc[i, 1] = 0
        else:
            if (lower_band.iloc[i] > final_bands.iloc[i-1,1]) | (close.iloc[i-1] < final_bands.iloc[i-1,1]):
                final_bands.iloc[i,1] = lower_band.iloc[i]
            else:
                final_bands.iloc[i,1] = final_bands.iloc[i-1,1]
    
    # SUPERTREND
    
    supertrend = pd.DataFrame(columns = [f'supertrend_{lookback}'])
    supertrend.iloc[:,0] = [x for x in final_bands['upper'] - final_bands['upper']]
    
    for i in range(len(supertrend)):
        if i == 0:
            supertrend.iloc[i, 0] = 0
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 0] and close.iloc[i] < final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 0] and close.iloc[i] > final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 1] and close.iloc[i] > final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 1] and close.iloc[i] < final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]
    
    supertrend = supertrend.set_index(upper_band.index)
    supertrend = supertrend.dropna()[1:]
    
    # ST UPTREND/DOWNTREND
    
    upt = []
    dt = []
    close = close.iloc[len(close) - len(supertrend):]

    for i in range(len(supertrend)):
        if close.iloc[i] > supertrend.iloc[i, 0]:
            upt.append(supertrend.iloc[i, 0])
            dt.append(np.nan)
        elif close.iloc[i] < supertrend.iloc[i, 0]:
            upt.append(np.nan)
            dt.append(supertrend.iloc[i, 0])
        else:
            upt.append(np.nan)
            dt.append(np.nan)
            
    st, upt, dt = pd.Series(supertrend.iloc[:, 0]), pd.Series(upt), pd.Series(dt)
    upt.index, dt.index = supertrend.index, supertrend.index
    
    return st, upt, dt

btcinr['st'], btcinr['s_upt'], btcinr['st_dt'] = get_supertrend(btcinr['high'], btcinr['low'], btcinr['close'], 10, 3)
btcinr = btcinr[1:]
print(btcinr.head())

# SUPERTREND PLOT

plt.plot(btcinr['close'], linewidth = 2, label = 'CLOSING PRICE')
plt.plot(btcinr['st'], color = 'green', linewidth = 2, label = 'ST UPTREND 10,3')
plt.plot(btcinr['st_dt'], color = 'r', linewidth = 2, label = 'ST DOWNTREND 10,3')
plt.legend(loc = 'upper left')
plt.show()

# SUPERTREND STRATEGY

def implement_st_strategy(prices, st):
    buy_price = []
    sell_price = []
    st_signal = []
    signal = 0
    
    for i in range(len(st)):
        if st.iloc[i-1] > prices.iloc[i-1] and st.iloc[i] < prices.iloc[i]:
            if signal != 1:
                buy_price.append(prices.iloc[i])
                sell_price.append(np.nan)
                signal = 1
                st_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                st_signal.append(0)
        elif st.iloc[i-1] < prices.iloc[i-1] and st.iloc[i] > prices.iloc[i]:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(prices.iloc[i])
                signal = -1
                st_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                st_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            st_signal.append(0)
            
    return buy_price, sell_price, st_signal

buy_price, sell_price, st_signal = implement_st_strategy(btcinr['close'], btcinr['st'])

# SUPERTREND SIGNALS

plt.plot(btcinr['close'], linewidth = 2)
plt.plot(btcinr['st'], color = 'green', linewidth = 2, label = 'ST UPTREND')
plt.plot(btcinr['st_dt'], color = 'r', linewidth = 2, label = 'ST DOWNTREND')
plt.plot(btcinr.index, buy_price, marker = '^', color = 'green', markersize = 12, linewidth = 0, label = 'BUY SIGNAL')
plt.plot(btcinr.index, sell_price, marker = 'v', color = 'r', markersize = 12, linewidth = 0, label = 'SELL SIGNAL')
plt.title('BTCINR ST TRADING SIGNALS')
plt.legend(loc = 'upper left')
plt.show()

# GENERATING STOCK POSITION
position = []
for i in range(len(st_signal)):
    if st_signal[i] > 1:
        position.append(0)
    else:
        position.append(1)
        
for i in range(len(btcinr['close'])):
    if st_signal[i] == 1:
        position[i] = 1
    elif st_signal[i] == -1:
        position[i] = 0
    else:
        position[i] = position[i-1]
        
close_price = btcinr['close']
st = btcinr['st']
st_signal = pd.DataFrame(st_signal).rename(columns = {0:'st_signal'}).set_index(btcinr.index)
position = pd.DataFrame(position).rename(columns = {0:'st_position'}).set_index(btcinr.index)

frames = [close_price, st, st_signal, position]
strategy = pd.concat(frames, join = 'inner', axis = 1)

strategy.head()
print(strategy[20:25])
# BACKTESTING
tsla_ret = pd.DataFrame(np.diff(btcinr['close'])).rename(columns = {0:'returns'})
st_strategy_ret = []

for i in range(len(tsla_ret)):
    returns = tsla_ret['returns'].iloc[i]*strategy['st_position'].iloc[i]
    st_strategy_ret.append(returns)
    
st_strategy_ret_df = pd.DataFrame(st_strategy_ret).rename(columns = {0:'st_returns'})
investment_value = 100000
number_of_stocks = floor(investment_value/btcinr['close'].iloc[-1])
st_investment_ret = []

for i in range(len(st_strategy_ret_df['st_returns'])):
    returns = number_of_stocks*st_strategy_ret_df['st_returns'][i]
    st_investment_ret.append(returns)

st_investment_ret_df = pd.DataFrame(st_investment_ret).rename(columns = {0:'investment_returns'})
total_investment_ret = round(sum(st_investment_ret_df['investment_returns']), 2)
profit_percentage = floor((total_investment_ret/investment_value)*100)
print(cl('Profit gained from the ST strategy by investing $100k in BTCINR : {}'.format(total_investment_ret), attrs = ['bold']))
print(cl('Profit percentage of the ST strategy : {}%'.format(profit_percentage), attrs = ['bold']))
