#This script is the implementation of the slow k strategy. I did not work as it did in the backtest, but that could be due to the fact of low liquidity on RH and just an overall immature
#platform

#bring in your rh functions to run this!
import logging
import robin_stocks.robinhood as rs
from datetime import datetime
import talib
import numpy as np 
import pandas as pd
import schedule
from time import time, sleep
from binance.client import Client 




#binance log in for real time datastream
api_key=''
api_secret=''
client = Client(api_key=api_key,api_secret=api_secret)

#robinhood login for executing trades. Took username and pw out since this will be on github
rs.login(username='username',
         password='password',
         expiresIn=86400,
         by_sms=True)



#initialize a log. probably just put this in a function and initialize the log file with the date. Option to name it
logging.basicConfig(filename =r'C:\Users\josia\OneDrive\Documents\python_scripts\crypto\log_files\slow_k_log_4.log',
                    level = logging.INFO, filemode = 'w')


now = datetime.now()
logging.info(f'Started Running Algo at {now}')

#will be used for stop loss

cooldown = 0
while True:

    sleep(60 - time() % 60)
    
    api_key=''
    api_secret=''
    client = Client(api_key=api_key,api_secret=api_secret)

#     check to see if your orders got stuck and cancel them if they have
    check_order_time_elapsed()

    
    #pull in real time data from binacnce
    data = client.get_historical_klines(symbol=f'BTCUSDT',interval=Client.KLINE_INTERVAL_1MINUTE,start_str="2 hours ago UTC")
    cols = ['date_and_time','open','high','low','close','volume','close_time','quote_asset_volume','number_of_trades','TBBAV','TBQAV','dropme']
    df = pd.DataFrame(data,columns=cols)
    df = df.astype({'open': float,'high':float,'low':float,'close':float,'volume':float})
    slowk, slowd = talib.STOCH(df.high, df.low, df.close, fastk_period=9, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
    df['slowk'] = slowk   


    try:
        cash = get_cash_balance()
        current_price = df.close.iloc[-1]
        positions = rs.get_crypto_positions()

        #check your stop loss
#         check_stop_loss(current_price,.05)


        #check to see if the indicator level, if own any of the coin, and if you have any open orders
        if df.slowk.iloc[-1] > 80 and float(positions[0]['quantity_available']) != 0.0 and not check_open_orders():
            sell_coin(current_price, "BTC")
            logging.info(f'Submitted a sell order because the k value was at {df.slowk.iloc[-1]}')
            print(f'Sold coin, k at {df.slowk.iloc[-1]}, for {current_price}')
        #check to see if the indicator level, if own any of the coin, and if you have any open orders    
        elif df.slowk.iloc[-1] < 30 and float(positions[0]['quantity_available']) == 0.0 and not check_open_orders():
            buy_coin(current_price, "BTC")
            logging.info(f'Submitted a buy order because the k value was at {df.slowk.iloc[-1]}')
            print(f'bought coin, k at {df.slowk.iloc[-1]}, for {current_price}')
        else:
            logging.info(f'No action taken because you either have a position or the {df.slowk.iloc[-1]} doesnt meet conditions ')
            print(f'no action, k at {df.slowk.iloc[-1]}')
    except:
        logging.error('encountered an error. Likely due to robinhood connectivity issues')
