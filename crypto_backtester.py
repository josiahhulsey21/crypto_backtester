import pandas as pd
import numpy as np 
import tqdm
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from binance.client import Client 
import sqlite3
from datetime import datetime, timedelta


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



    def dynamic_stop_loss(self, current_price, floor_shift = .01):
        
        '''
        Function that updates the stop loss to protect profits. It will dynamically change the stop loss once the price gets above your take profits threshold.
        This function also modifies the take profits value for the trade (even though it wont ever be used in the actual trading algo).
        
        Floor shift variable is the variable that will be used to adjust the stop loss. Its default is set to one percent below the current price. This can be changed 
        You probably dont want to have it set at the current price due to volatility.
        '''
        
        if self.act_holdings:

            trade_id = self.get_trade_id_simple()

            if current_price >= self.act_holdings[0]['take_profit']:
                
                new_sl = current_price - (current_price * floor_shift)
                new_tp = current_price + (current_price * floor_shift)
                
                self.act_holdings[0]['stop_loss'] = new_sl
                self.act_holdings[0]['take_profit'] = new_sl

                # print('Updated Stop Loss to protect profits')



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
        

    def print_statistics(self):
        lose_list = []
        win_list = []

        def Average(lst):
            return sum(lst) / len(lst)

        #this calls the print journal function......probably not good to have it print out every time. Can fix this
        working_df = self.print_journal()


        # https://stackoverflow.com/questions/22607324/start-end-and-duration-of-maximum-drawdown-in-python

        ##not working!!!!
        # xs = np.array(self.account_value_history[1]).cumsum()
        # i = np.argmax(np.maximum.accumulate(xs) - xs) # end of the period
        # print(i)
        # j = np.argmax(xs[:i]) # start of period
        # print(xs)

        for pair in working_df.trade_id.unique():
            dfc = working_df.copy()
            dfc = dfc[dfc['trade_id'] == pair]
            
            buy_price = dfc[dfc['action'] == 'buy'].total_price.max()
            sell_price = dfc[dfc['action'] == 'sell'].total_price.max()
            
            trade_result = sell_price - buy_price
            if trade_result < 0:
                lose_list.append(trade_result)
            elif trade_result > 0:
                win_list.append(trade_result)   

        print(f'the strategy returned {round(1-(self.account_value_history[1][0]/self.account_value_history[1][-1]),2)}%')
        # print(i)
        print()
        print(f'There were a total of {len(lose_list) + len(win_list)} trades made in the backtest')
        print(f'The winning percentage of the algo was {len(win_list)/(len(lose_list) + len(win_list))}')
        print(f'The average winning trade made {Average(win_list)}')
        print(f'The average losing trade made {Average(lose_list)}')
        print(f'The best trade made {max(win_list)}')
        print(f'The worst trade lost {min(lose_list)}')
            
    
    
    
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
        fig.add_trace(go.Scatter(x = df.index, y = df['close'], line_color = 'black', name = 'Coin Price'),
        secondary_y = True)
        
        #add buy signals
        fig.add_trace(go.Scatter(x = buy_df.index, y = buy_df['price'], line_color = 'green', name = 'Buy', mode="markers"),
        secondary_y = True)
 
        #add sell signals
        fig.add_trace(go.Scatter(x = sell_df.index, y = sell_df['price'], line_color = 'red', name = 'sell', mode="markers"),
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
        
        actfig.add_trace(go.Scatter(x = dfc.close_time, y = dfc.percent_change, line_color = 'black', name = 'coin returns'))
        actfig.add_trace(go.Scatter(x = act_value_perc_time, y = act_value_perc, line_color = 'red', name = 'algo returns'))
        
        actfig.show()
        
        print(f'the strategy returned {1-(self.account_value_history[1][0]/self.account_value_history[1][-1])}%')
        print(f'the traded coin returned {1-(dfc.close.iloc[0]/dfc.close.iloc[-1])}%')
    
    
    
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
    Required variable is the dataframe containing the historical data, the wallet object, and the ticker. Automatically drops rows with NA in them

    example: sma_exp = btc.backtest(1000,data_df,btc_wallet,'btc')

    Currently a strategy is hardcoded in to here. I would like to make this take a function as an argument and then use that function throughout the backtesting logic.

    '''


    
    def __init__(self, data, wallet,ticker):
        
        self.wallet = wallet
  
        self.data = data
        self.ticker = ticker
        self.data.dropna(inplace = True)
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
            self.wallet.dynamic_stop_loss(price)
            self.wallet.check_stop_loss(price,time)
            # self.wallet.check_take_profit(price,time)
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
#
    def run_backtest_2(self, trade_logic):
        trade_logic(self.wallet, self.data,self.ticker)


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
        '''
        This function will return a list of all available coins on Binance sorted alphabetically
        '''
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
        '''
        Function that downloads data using the binance API.
        '''

        api_key=''
        api_secret=''
        client = Client(api_key=api_key,api_secret=api_secret)
        
        # for c in coin:
        print(f'Gathering {coin} data...')
        data = client.get_historical_klines(symbol=f'{coin}USDT',interval=Client.KLINE_INTERVAL_1MINUTE,start_str=self.start_date,end_str=self.end_date)
        cols = ['date_and_time','open','high','low','close','volume','close_time','quote_asset_volume','number_of_trades','TBBAV','TBQAV','dropme']
        df = pd.DataFrame(data,columns=cols)
        df.drop(['dropme'], inplace = True, axis = 1)
        
        # for whatever reason, most of the columns come in as strings when you download from binance. This converts to floats. You have to have time come in as an object for the for loop
        # to work!!!
        
        #this is for the database
        df['coin'] = coin
        df['id'] = df['coin']+df['date_and_time'].astype('string')


        for i in range(len(df)):
            df['date_and_time'][i] = datetime.fromtimestamp(int(df['date_and_time'][i]/1000))

        df['date'] = [d.date() for d in df['date_and_time']]
        df['time'] = [d.time() for d in df['date_and_time']]           
        
        # for whatever reason, most of the columns come in as strings when you download from binance. This converts to floats. You have to have time come in as an object for the for loop
        # to work!!! You need to explicitly declare the date and time as a string, otherwise you will get an error!
        df = df.astype({'date_and_time':object,'open': float,'high':float,'low':float,'close':float,'volume':float, 'quote_asset_volume':float,'TBBAV':float,'TBQAV':float,'date':str,'time':str})
            
        return df





def create_database(directory, db_name):

    '''
    This function creates a database in a given directory with a given name. The database is setup to work well with the logic of the backtester. You are free to edit
    it as you choose, but using any functions outside the provided one may lead to performance problems!
    '''
    
    full_db = f'{directory}\{db_name}.db'
    con = sqlite3.connect(full_db)
    cur = con.cursor()

    cur.execute(""" CREATE TABLE IF NOT EXISTS historical_coin_data(
        "id" TEXT PRIMARY KEY,
        "coin" TEXT,
        "date" TEXT,
        "time" TEXT,
        "date_and_time" TEXT,
        "open" REAL,
        "high" REAL,
        "low" REAL,
        "close" REAL,
        "volume" REAL,
        "close_time" TEXT,
        "quote_asset_volume" REAL,
        "number_of_trades" INTEGER,
        "tbbav" REAL,
        "tbqav" REAL,
        unique (id));""")

    con.commit()
    cur.close()
    con.close()

    print(f'Created a sqlite database named {db_name} in {directory}')


def update_database(filepath,data_frame):
    '''
    Function that stores data in the database
    '''
    
    con = sqlite3.connect(filepath)
    cur = con.cursor() 
    
    for index, row in tqdm.tqdm(data_frame.iterrows()):
        
        sqlite_insert_query = """INSERT OR REPLACE INTO historical_coin_data
                            (id, coin, date, time, date_and_time,open,high,low,close,volume,close_time,quote_asset_volume,number_of_trades,tbbav,tbqav) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) """
    
        
        data_tuple =(row.id, row.coin, row.date, row.time, row.date_and_time, row.open,row.high,row.low,row.close,row.volume,row.close_time,
        row.quote_asset_volume, row.number_of_trades,row.TBBAV,row.TBQAV)
        
        
        cur.execute(sqlite_insert_query, data_tuple)

    con.commit()
    cur.close()
    con.close()  
    print('Updated Database')


def retrieve_data_single_coin(db_file,coin):
    '''
    Function that returns all data for a given coin in your database
    '''

    con = sqlite3.connect(db_file)
    cur = con.cursor() 

    lu_coin = coin.upper()

    df = pd.read_sql(f"SELECT * FROM historical_coin_data WHERE coin == '{lu_coin}'",con)
    df = df.sort_values(by='date_and_time',ascending=True)

    cur.close()
    con.close()

    return df


def check_unique_db(db_file):
    '''
    Function that will return all the coins that you have stored in your database
    '''

    unique_list = []

    #sql query that selects all of the unique values from the coin column
    query = "SELECT DISTINCT(coin) FROM historical_coin_data"

    con = sqlite3.connect(db_file)
    cur = con.cursor() 

    cur=con.execute(query)
    for row in cur:
        unique_list.append(row[0])
    cur.close()
    con.close()

    return unique_list


def get_data_by_date(db_file,start_date,end_date):
    '''
    Function that returns data from database using dates as a control
    Expected date format is:  '2021-06-01'
    '''

    con = sqlite3.connect(db_file)
    cur = con.cursor() 
    
    df = pd.read_sql(f"SELECT * FROM historical_coin_data WHERE date between date('{start_date}') AND date('{end_date}')",con)

    cur.close()
    con.close()

    return df
   


def download_data_for_automated_updating(coin, start_date, end_date):
    '''
    Function that downloads data using the binance API.
    '''

    api_key=''
    api_secret=''
    client = Client(api_key=api_key,api_secret=api_secret)
    
    # for c in coin:
    print(f'Gathering {coin} data...')
    data = client.get_historical_klines(symbol=f'{coin}USDT',interval=Client.KLINE_INTERVAL_1MINUTE,start_str=start_date,end_str=end_date)
    cols = ['date_and_time','open','high','low','close','volume','close_time','quote_asset_volume','number_of_trades','TBBAV','TBQAV','dropme']
    df = pd.DataFrame(data,columns=cols)
    df.drop(['dropme'], inplace = True, axis = 1)
    
    # for whatever reason, most of the columns come in as strings when you download from binance. This converts to floats. You have to have time come in as an object for the for loop
    # to work!!!
    
    #this is for the database
    df['coin'] = coin
    df['id'] = df['coin']+df['date_and_time'].astype('string')


    for i in range(len(df)):
        df['date_and_time'][i] = datetime.fromtimestamp(int(df['date_and_time'][i]/1000))

    df['date'] = [d.date() for d in df['date_and_time']]
    df['time'] = [d.time() for d in df['date_and_time']]           
    
    # for whatever reason, most of the columns come in as strings when you download from binance. This converts to floats. You have to have time come in as an object for the for loop
    # to work!!! You need to explicitly declare the date and time as a string, otherwise you will get an error!
    df = df.astype({'date_and_time':object,'open': float,'high':float,'low':float,'close':float,'volume':float, 'quote_asset_volume':float,'TBBAV':float,'TBQAV':float,'date':str,'time':str})
        
    return df





def update_all_coins(db_file):
    '''
    Function that will update data for all coins in the database to the current day
    '''
    now = datetime.now()
    now = now.strftime("%Y/%m/%d")
    
    #put this before you open the database otherwise you might get weird results since this will also open and close the db
    coins_in_db = check_unique_db(db_file)
    
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    for coin in coins_in_db:
        #query that selects the most recent date
        query = f"SELECT date FROM historical_coin_data WHERE coin == '{coin}' ORDER BY date DESC LIMIT 1";
        #execute query
        cur=con.execute(query)

        #returns the latest date for the coin
        sql_date = cur.fetchone()

        #returns the actual date from sqlite
        sql_date = sql_date[0]

        #convert it to a date time object
        formater = "%Y-%m-%d"
        sql_date = datetime.strptime(sql_date, formater)

        #subtract 1 day from the most recent date
        max_date_minus_1 = sql_date.date()
        max_date_minus_1 = max_date_minus_1 - timedelta(days=1)
        max_date_minus_1 = max_date_minus_1.strftime("%Y-%m-%d")

        df = download_data_for_automated_updating(coin,max_date_minus_1,now)

        update_database(db_file,df)

        print(f'updated {coin} in database')

    con.commit()
    cur.close()
    con.close()








