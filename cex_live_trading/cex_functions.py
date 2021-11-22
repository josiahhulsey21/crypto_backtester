import requests
import json
import hmac
import hashlib
import time

def get_latest_price(coin,currency ='USD'):
    '''
    Function that returns the latest price for a coin. 

    '''
    coin = coin.upper()
    r = requests.get(f'https://cex.io/api/last_price/{coin}/{currency}')
    data = r.json()
    return data

def get_order_book(coin,currency = 'USD'):
    '''
    Function that will return the order book
    '''
    coin = coin.upper()
    r = requests.get(f"https://cex.io/api/order_book/{coin}/{currency}/")
    data = r.json()
    return data



def gen_sig(key,uid,api_secret):
    '''
    Function that generates a signature for private requests.
    '''
    nonce = int(time.time())
    nonce = str(nonce)
    message = nonce + uid + key
    signature = hmac.new(bytearray(api_secret.encode('utf-8')), message.encode('utf-8'), digestmod = hashlib.sha256).hexdigest().upper()
#     got to return the nonce as well!!!!
    return signature,nonce