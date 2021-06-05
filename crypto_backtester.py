import pandas as pd
import numpy as np 
import tqdm
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from binance.client import Client 
from datetime import datetime


class wallet:
    ''' 
    Required variable is starting cash. This wallet is meant to only test a strategy on one coin. I think having a separate class for a portfolio test is the best way to tackle
    that problem. When I get there I will have to clean some of the logic out of this class because I initially thought I could do it all in one class.

    Example to instantiate: test_wallet = cbt.wallet(10000)
    
    This object is the wallet that will keep track of your positions and portfolio value. All of the theoretical trades are executed using this class. The trade strategy
    is defined elsewhere 
    '''

    def __init__(self,starting_cash):
                
        self.starting_cash = float(starting_cash)
        self.s_cash_4_plot = float(starting_cash)
        
        self.account_value = self.starting_cash
        
        #append the time stamp and the value of the portfolio here for plotting purposes
#         first will be time stamp,second will be value
        self.account_value_history = [[],[]]
        
        
        
        self.act_holdings = []
        
        #this will be for journaling the moves
        self.journal =[[],[],[],[],[],[],[],[],[],[]]     

        #this variable is used in the functions that will force the algo to take a break should you tell it to.
        self.cooldown = 0
        
    
    
    def add_holding(self, ticker, price, time, stop_loss = .05, take_profit = .05):
        '''
        This is the main function that will add holdings to the wallet.
        * ticker, price, time are all required arguments
        * default stop loss is set to .05. You can obviously change this if you pass in a different value in your trading logic
        * default take profit is set to .05. You can obviously change this if you pass in a different value in your trading logic
        '''
        
        price_purchased = price
        ammount_purchased = self.starting_cash/price
        sum_price = price_purchased * ammount_purchased

        stop_loss_price = price_purchased - (price_purchased * stop_loss)
        take_profit_price = price_purchased + (price_purchased * take_profit)
        cooldown = 0


        
        now = time
        
        trade_id = f'{ticker}{now}'


        buy_dictionary = {'trade_id':trade_id,'ticker':ticker, 'price':price, 'ammount':ammount_purchased,'stop_loss':stop_loss_price, 'take_profit':take_profit_price,'cooldown':cooldown}
        self.act_holdings.append(buy_dictionary)

        #update cash position
        self.starting_cash = self.starting_cash - sum_price
        
        #journaling steps
        self.journal[0].append(now)
        self.journal[1].append('buy')
        self.journal[2].append(ticker)
        self.journal[3].append(price)  
        self.journal[4].append(ammount_purchased)
        self.journal[5].append(sum_price)
        self.journal[6].append(trade_id)
        self.journal[7].append(stop_loss_price)
        self.journal[8].append(take_profit_price)
        self.journal[9].append(cooldown)
        
        
    
    def sell_holding(self,trade_id, price, time):

        '''
        This is the primary function that is used to sell coins. 
        Required inputs are trade id, price, and time  (all to be passed in the trading algo)
        '''


        
        #i dont know if this is actually needed..... i guess for journaling
        trade_id_test = trade_id

        trade_dic = self.act_holdings[0]

        ticker = trade_dic['ticker']
        ammount_sold = float(trade_dic['ammount'])
        
        
        #this is the spot price. will figure out how to make more elaborate later
        sale_price = price
        
        
        sum_price = sale_price * ammount_sold

        #update cash position
        self.starting_cash = self.starting_cash + sum_price
        
        del self.act_holdings[0]
        
        now = time

        self.journal[0].append(now)
        self.journal[1].append('sell')
        self.journal[2].append(ticker)
        self.journal[3].append(price)  
        self.journal[4].append(ammount_sold)
        self.journal[5].append(sum_price)
        self.journal[6].append(trade_id)
        self.journal[7].append(0)
        self.journal[8].append(0)
        self.journal[9].append(0)
        


    def initiate_cooldown(self, cd_period = 1000):
        '''
        Function that will iniate a cool down period. Defaults to 1000 timesteps. can set this to whatever. Can even set them unevenly if you wanted to! doesnt have to be the same
        for each reason you initiate a cool down
        '''
        self.cooldown = self.cooldown + cd_period


    def update_cooldown(self):
        '''
        Function that updates the cooldown period if it is not 0. Subtracts 1 from the cooldown if it the cooldown value is greater than 0
        '''
        if self.cooldown > 0:
            self.cooldown = self.cooldown - 1
        else:
            pass
        

    def check_cooldown(self):
        ''' 
        Function that checks to see if the cool down is above 0 and then updates the cooldown if it is. At the moment
        this function isnt actually used in the code anywhere!
        '''
        if self.cooldown > 0:
            self.update_cooldown()



    def check_stop_loss(self, current_price, time):
        '''
        Function that checks to see if a stop loss has been crossed and sells if it has
        need to have the trading algo pass the current price and current time
        '''

        #need to check make sure you actually own something before calling this!

        if self.act_holdings:

            trade_id = self.get_trade_id_simple()


            if current_price <= self.act_holdings[0]['stop_loss']:
                #call your function that sells the holding. Price and time need to be passed in the algo function
                self.sell_holding(trade_id, current_price, time)
                #initiate cooldown
                self.initiate_cooldown()
                print('Stop Loss Triggered')



    def check_take_profit(self, current_price, time):
        '''
        Function that checks to see if a take profit event has been crossed and sells if it has
        need to have the trading algo pass the current price and current time
        '''
        #need to check make sure you actually own something before calling this!
        if self.act_holdings:

            trade_id = self.get_trade_id_simple()

            if current_price >= self.act_holdings[0]['take_profit']:
                #call your function that sells the holding. Price and time need to be passed in the algo function
                self.sell_holding(trade_id, current_price, time)
                #initiate cooldown
                self.initiate_cooldown()
                print('Take Profits Triggered')



    def print_journal(self):
        ''' This will print out the journal for the wallet as a df. If it has been backtested, this will contain all
        of the buy/sells. At the moment the time is broken. It records current time instead of backtest time.'''
        
        df = pd.DataFrame({'date':self.journal[0],'action':self.journal[1], 
                           'ticker':self.journal[2], 'price':self.journal[3],
                          'ammount':self.journal[4],'total_price': self.journal[5],
                          'trade_id':self.journal[6], 'stop_loss_price':self.journal[7],
                          'take_profit_price':self.journal[8], 'cooldown':self.journal[9]})
        return df
        print(df)
        
        
    
    def update_act_value_simple(self,price, time):
        '''
        Function that updates the account value
        Price, ammount, time are the variables in that order
        '''

        if self.act_holdings:
            ammount = self.act_holdings[0]['ammount']
        #yes this needs to be set to one. You multiply here so if you set it to 0 it will 0 out your account
        else:
            ammount = 1
        
        
        #if not empty
        if self.act_holdings:
            self.account_value = price * ammount
            self.account_value_history[0].append(time)
            self.account_value_history[1].append(self.account_value)     
        
        #if empty
        elif not self.act_holdings:
            #appends the time and act value to the history list
            self.account_value_history[0].append(time)
            self.account_value_history[1].append(self.account_value)       
        

    def plot_act_value_history(self, df):
        
        '''Plots the value of the account vs the value of whatever thing you are trading'''
        
        time = self.account_value_history[0]
        act_value = self.account_value_history[1]
        
        #this will get the journal so you can plot the buy and sell points
        journal_df = pd.DataFrame({'date':self.journal[0],'action':self.journal[1], 
                           'ticker':self.journal[2], 'price':self.journal[3],
                          'ammount':self.journal[4],'total_price': self.journal[5],
                          'trade_id':self.journal[6]})        
        
        
        buy_df = journal_df[journal_df['action'] == 'buy']
        sell_df = journal_df[journal_df['action'] == 'sell']                      
        
            
                          
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        #Plot the account value
        fig.add_trace(go.Scatter(x = time, y = act_value, line_color = 'blue', name = 'Account Value'))

        #add index price
        fig.add_trace(go.Scatter(x = df['time'], y = df['close'], line_color = 'black', name = 'Coin Price'),
        secondary_y = True)
        
        #add buy signals
        fig.add_trace(go.Scatter(x = buy_df['date'], y = buy_df['price'], line_color = 'green', name = 'Buy', mode="markers"),
        secondary_y = True)
 
        #add sell signals
        fig.add_trace(go.Scatter(x = sell_df['date'], y = sell_df['price'], line_color = 'red', name = 'sell', mode="markers"),
        secondary_y = True)
        
        fig.show()
        
        print(f'the strategy returned {round(1-(self.account_value_history[1][0]/self.account_value_history[1][-1]),2)}%')
        print(f'the traded coin returned {round(1-(df.close.iloc[0]/df.close.iloc[-1]),2)}%')

        
        
    def plot_act_value_history_percentage(self, df):
        
        dfc = df.copy()
    
        starting_coin_price = df.close.iloc[0]
        s_cash = self.s_cash_4_plot 
        
        dfc['percent_change'] = 1 - (starting_coin_price/dfc.close)
        
        act_value_perc_time = self.account_value_history[0]
        
    
        #need to divide each value in here by initial cash position
        act_value_perc = self.account_value_history[1]
        for i in range(len(act_value_perc)):
            act_value_perc[i] = 1 - (s_cash/act_value_perc[i])
            
        actfig = go.Figure()
        
        actfig.add_trace(go.Scatter(x = dfc.time, y = dfc.percent_change, line_color = 'black', name = 'coin returns'))
        actfig.add_trace(go.Scatter(x = act_value_perc_time, y = act_value_perc, line_color = 'red', name = 'algo returns'))
        
        actfig.show()
        
        print(f'the strategy returned {1-(self.account_value_history[1][0]/self.account_value_history[1][-1])}%')
        print(f'the traded coin returned {1-(df.close.iloc[0]/df.close.iloc[-1])}%')
    
    
    
    def get_trade_id_simple(self):
        ''' This assumes only 1 position in portfolio at a time. Wont work with multiple ones'''
        #sets a counter that will be used in the logic.
        
        trade_id_export = ''
        
        for dic in self.act_holdings:
            trade_dic = self.act_holdings[0]

            trade_id_export = trade_dic['trade_id']
            
#             print(trade_id_export)
               
        return trade_id_export


    
class backtest:
    ''' 
    Required variable is warm up period, the dataframe containing the historical data, the wallet object, and the ticker.

    example: sma_exp = btc.backtest(1000,data_df,btc_wallet,'btc')

    Currently a strategy is hardcoded in to here. I would like to make this take a function as an argument and then use that function throughout the backtesting logic.

    '''


    
    def __init__(self, warm_up, data, wallet,ticker):
        
        self.wallet = wallet
        self.warm_up = warm_up
        self.data = data
        self.ticker = ticker
        
        self.data = self.data.iloc[warm_up:]
        
        #
        self.total_epochs = len(self.data)
        
        
    
    
    
    def run_backtest(self):
        ''' may need to clear the journals and account before running this???'''
        
        for index, row in tqdm.tqdm(self.data.iterrows()):
            
            #get the current price in case you need to pass it to a buy or sell function
            price = row["close"]
            time = row["time"]
            #get the current sma value
            sma_value = row["1000_sma"]
            
            roc_value = row["roc_1000"]
#             print(roc_value)

            sma_check = price - sma_value

            #check to see if you are in cool down mode or if you have encountered stop loss or take profits. Probably should move the cooldown check into a function
            
            #maybe have this return a number and use that as the if statement?
            # self.wallet.check_cooldown()

            self.wallet.check_stop_loss(price,time)
            self.wallet.check_take_profit(price,time)
            if self.wallet.cooldown > 0:
                self.wallet.update_cooldown()
                # print('updating cooldown value')


            #If you pass the above criteria, implement the trade logic you want
            else:
                #check to see if the current price is above the sma and if you currently hold any btc
                if not self.wallet.act_holdings and sma_check > 0 and roc_value > 105.0:
                    self.wallet.add_holding(self.ticker, price, time)
                    self.wallet.update_act_value_simple(price,time)
                    print('creating position')
                    
                elif self.wallet.act_holdings and sma_check > 0:
                    self.wallet.update_act_value_simple(price,time)
                    # print('position already held, moving to next epoch')

                elif self.wallet.act_holdings and sma_check < 0:
                    #get the trade id on this step....maybe write this as a stand alone function in the wallet class
                    trade_id = self.wallet.get_trade_id_simple()
                    self.wallet.sell_holding(trade_id, price,time)
                    self.wallet.update_act_value_simple(price,time)
                    
                    
                    #testing cooldown feature. having the algo wait 1000 minutes before it re-enters the market after it sells a position
                    self.wallet.initiate_cooldown()

                    print('market turning, selling position. Initiated Cooldown')

                elif self.wallet.act_holdings and roc_value < 102:
                    #get the trade id on this step....maybe write this as a stand alone function in the wallet class
                    trade_id = self.wallet.get_trade_id_simple()
                    self.wallet.sell_holding(trade_id, price,time)                
                    self.wallet.update_act_value_simple(price,time)
                    
                    #testing cooldown feature. having the algo wait 1000 minutes before it re-enters the market after it sells a position
                    self.wallet.initiate_cooldown()
                    
                    print('Rally finished, selling position. Initiated Cooldown.') 
    
                elif not self.wallet.act_holdings and sma_check < 0:     
                    self.wallet.update_act_value_simple(price,time)
                    # print('bear market, moving to next epoch')        
                
                # when non of the buy or sell requirments are met, follow the usual update account value protocol
                else:
                    self.wallet.update_act_value_simple(price,time)



class trading_strategy:
    # '''
    #maybe a class really isnt the best option here. Maybe just feeding the backtester the testing function is better.

    # I would like to potentially use this as a class to pass to the backtester. Its where you will define the trading logic
    # '''
    
    def __init__(self):
        self.placeholder = 1
        

        

class data_downloader:   
    '''
    This utilizes the binance api and downloads minute data given a start and an end date.
    Example start date format: '1 Apr, 2021'
    Example Call: dl = cbt.data_downloader('1 Apr, 2021', '5 Apr, 2021')

    '''

    def __init__(self, start_date, end_date):

        self.start_date = start_date
        self.end_date = end_date


    def get_available_coins(self):
        api_key=''
        api_secret=''
        client = Client(api_key=api_key,api_secret=api_secret)


        a_coins = client.get_all_tickers()
        coin_list = []
        for dictionary in a_coins:
            coin_list.append(dictionary['symbol'])

        coin_list.sort()

        return coin_list

    
    def get_data(self, coin):

        api_key=''
        api_secret=''
        client = Client(api_key=api_key,api_secret=api_secret)
        
        for c in coin:
            print(f'Gathering {c} data...')
            data = client.get_historical_klines(symbol=f'{c}USDT',interval=Client.KLINE_INTERVAL_1MINUTE,start_str=self.start_date,end_str=self.end_date)
            cols = ['time','open','high','low','close','volume','CloseTime','QuoteAssetVolume','NumberOfTrades','TBBAV','TBQAV','null']
            df = pd.DataFrame(data,columns=cols)
            
            for i in range(len(df)):
                df['time'][i] = datetime.fromtimestamp(int(df['time'][i]/1000))           
                       
            return df




