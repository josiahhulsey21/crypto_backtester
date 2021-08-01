import robin_stocks.robinhood as rs
import numpy as np 
import pandas as pd

#get your cash balance
def get_cash_balance():
    profile = rs.profiles.load_account_profile()
    cash = float(profile['cash'])
#     print(cash)
    return cash

#checks to see if you have open orders    
def check_open_orders():
    return rs.get_all_open_crypto_orders()

#returns a dictionary of your holdings 
def check_act_pos():
    return rs.build_holdings()
#This will be used to get the buy/sell price
def get_price(coin):
    price = rs.crypto.get_crypto_quote(coin)
    return round(float(price['mark_price']),0)

#this is used to update the current dataframe 
def update_price(coin,df):
    price = rs.crypto.get_crypto_quote(coin)
    df.loc[len(df.index)] = [price['open_price'], price['high_price'],price['low_price'],price['mark_price'], 0] 

#see how much you own. if you have multiple coins this needs to be complexified
def get_ammount_owned():
    positions = rs.get_crypto_positions()
    return float(positions[0]['quantity_available'])


#calculate the take profit
def calculate_take_profit(take_profit = .05):
    positions = rs.get_crypto_positions()
    order_total_invested = float(order_details[0]['direct_cost_basis'])
    order_quantity = float(order_details[0]['direct_quantity'])
    
    price_purchased = order_total_invested/order_quantity
    
    take_profit_price = price_purchased + (price_purchased * take_profit)
    
#     print(price_purchased)
#     print(take_profit_price)
    
    return take_profit_price
    
#function that places a sell order with the limit being the current price
def sell_coin(price, coin="BTC"):
    a_owned = get_ammount_owned()
#     price = get_price(coin)
    rs.orders.order_sell_crypto_limit(coin,a_owned,price)    

#function that will invest all your available cash into a coin
def buy_coin(price,coin="BTC"):
    cash = get_cash_balance()
#     price = get_price(coin)
    rs.orders.order_buy_crypto_limit_by_price(coin,cash,price)   
    
    
#submits a market order to buy 
def buy_coin_m(coin = "BTC"):
    cash = get_cash_balance()
    rs.orders.order_buy_crypto_by_price(coin,cash)   
#submits a market order to sell all your holdings
def sell_coin_m(coin = "BTC"):
    a_owned = get_ammount_owned()
    price = get_price(coin)
    rs.orders.order_sell_crypto_by_quantity(coin,a_owned)      

    
    
def check_order_time_elapsed(elapsed_threshold = -5):
    '''
    Checks to see if you have any open orders and cancels them if they have taken longer than elapsed_threshold minutes
    to fill
    '''
    
    #check if you have any open orders
    if rs.get_all_open_crypto_orders():
    
        now = datetime.now() 
        orders = rs.get_all_open_crypto_orders()
        string_date = orders[0]['created_at']
        string_date = string_date[:-6]
        string_date = string_date.replace("T",' ')
        formatter = '%Y-%m-%d %H:%M:%S.%f'
        order_time = datetime.strptime(string_date, formatter)

        time_elapsed = order_time - now

        time_elapsed = ((time_elapsed.total_seconds())/60) -60

        if time_elapsed < elapsed_threshold:
            rs.orders.cancel_all_crypto_orders()
            print('cancelled order')
            logging.info(f'Order cancelled because {elapsed_threshold} minutes had passed since order entry')

    
def check_stop_loss(current_price, stop_loss = .05):
    
    #get your position
    positions = rs.get_crypto_positions()
    
    #if you have a position, check the stop loss
    if float(positions[0]['quantity_available']) != 0.0:
   
        order_total_invested = float(positions[0]['direct_cost_basis'])
        order_quantity = float(positions[0]['direct_quantity'])

        price_purchased = order_total_invested/order_quantity

        stop_loss_price = price_purchased - (price_purchased * stop_loss)
#         if the stoploss has been triggered, sell the coin
        if stop_loss_price > current_price:
            sell_coin_m()
            logging.info(f'Stop loss triggered. Selling position at market price')



        
    