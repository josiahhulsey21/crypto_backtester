import pandas as pd
import numpy as np 
import tqdm
from plotly.subplots import make_subplots

class wallet:
    def __init__(self,starting_cash):
                
        self.starting_cash = float(starting_cash)
        self.s_cash_4_plot = float(starting_cash)
        
        self.account_value = self.starting_cash
        
        #append the time stamp and the value of the portfolio here for plotting purposes
#         first will be time stamp,second will be value
        self.account_value_history = [[],[]]
        
        
        
        self.act_holdings = []
        
        #this will be for journaling the moves
        self.journal =[[],[],[],[],[],[],[]]     
        
    
    
    def add_holding(self, ticker, price, time):
        
        price_purchased = price
        ammount_purchased = self.starting_cash/price
        sum_price = price_purchased * ammount_purchased
        
        now = time
#         now = now.strftime("%d/%m/%Y %H:%M:%S")
        
        trade_id = f'{ticker}{now}'

        
        buy_dictionary = {'trade_id':trade_id,'ticker':ticker, 'price':price, 'ammount':ammount_purchased}
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
    
    
    def sell_holding(self,trade_id, price, time):
        
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
#         now = now.strftime("%d/%m/%Y %H:%M:%S")
        

        self.journal[0].append(now)
        self.journal[1].append('sell')
        self.journal[2].append(ticker)
        self.journal[3].append(price)  
        self.journal[4].append(ammount_sold)
        self.journal[5].append(sum_price)
        self.journal[6].append(trade_id)
    
    
    
    
    def print_journal(self):
        ''' This will print out the journal for the wallet as a df. If it has been backtested, this will contain all
        of the buy/sells. At the moment the time is broken. It records current time instead of backtest time.'''
        df = pd.DataFrame({'date':self.journal[0],'action':self.journal[1], 
                           'ticker':self.journal[2], 'price':self.journal[3],
                          'ammount':self.journal[4],'total_price': self.journal[5],
                          'trade_id':self.journal[6]})
        return df
        print(df)
        
        
    
    def update_act_value_simple(self,price, time):
        '''Price, ammount, time are the variables in that order'''

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
        fig.add_trace(go.Scatter(x = df['time'], y = df['close'], line_color = 'black', name = 'Security Price'),
        secondary_y = True)
        
        #add buy signals
        fig.add_trace(go.Scatter(x = buy_df['date'], y = buy_df['price'], line_color = 'green', name = 'Buy', mode="markers"),
        secondary_y = True)
 
        #add sell signals
        fig.add_trace(go.Scatter(x = sell_df['date'], y = sell_df['price'], line_color = 'red', name = 'sell', mode="markers"),
        secondary_y = True)
        
        fig.show()
        
        print(f'the strategy returned {1-(self.account_value_history[1][0]/self.account_value_history[1][-1])}%')
        print(f'the traded coin returned {1-(df.close.iloc[0]/df.close.iloc[-1])}%')

        
        
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
        
        for index, row in self.data.iterrows():
            
            #get the current price in case you need to pass it to a buy or sell function
            price = row["close"]
            time = row["time"]
            #get the current sma value
            sma_value = row["1000_sma"]
            
            roc_value = row["roc_1000"]
#             print(roc_value)

            sma_check = price - sma_value
                 
            #check to see if the current price is above the sma and if you currently hold any btc
            if not self.wallet.act_holdings and sma_check > 0 and roc_value > 105.0:
                self.wallet.add_holding(self.ticker, price, time)
                self.wallet.update_act_value_simple(price,time)
                print('creating position')
                
            elif self.wallet.act_holdings and sma_check > 0:
                self.wallet.update_act_value_simple(price,time)
                print('position already held, moving to next epoch')

                
            elif self.wallet.act_holdings and sma_check < 0:
                #get the trade id on this step....maybe write this as a stand alone function in the wallet class
                trade_id = self.wallet.get_trade_id_simple()
                self.wallet.sell_holding(trade_id, price,time)                
                self.wallet.update_act_value_simple(price,time)
                print('market turning, selling position')

            elif self.wallet.act_holdings and roc_value < 102:
                #get the trade id on this step....maybe write this as a stand alone function in the wallet class
                trade_id = self.wallet.get_trade_id_simple()
                self.wallet.sell_holding(trade_id, price,time)                
                self.wallet.update_act_value_simple(price,time)
                print('Rally finished, selling position') 
   
            elif not self.wallet.act_holdings and sma_check < 0:     
                self.wallet.update_act_value_simple(price,time)
                print('bear market, moving to next epoch')        
            
            # when non of the buy or sell requirments are met, follow the usual update account value protocol
            else:
                self.wallet.update_act_value_simple(price,time)
