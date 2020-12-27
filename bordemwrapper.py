import logging
from datetime import datetime
import json
import smtplib
import time

import numpy as np
import pandas as pd
import talib as ta

import config
from bitmex_request import BitMEX


'''bordemwrapper 
gr-satt
'''


# BitMEX functions are generated dynamically.
# they exist after class object is initiated.
# linter won't recognize them.
#
# work-around:
# disable msg -- %s %r has no %r member
# pylint: disable=E1101


# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
handler = logging.FileHandler(filename='log.log', mode='a')        # `filename` may need path
handler.setFormatter(formatter)
logger.addHandler(handler)


class Data:
    '''ohlcv & indicator data'''
    def __init__(
            self, api_key: str = config.apiKey,
            api_secret: str = config.apiSecret):
        self.api_key = api_key
        self.api_secret = api_secret

        self.bitmex = BitMEX(api_key=self.api_key, api_secret=self.api_secret)

    def ohlcv(self, symbol: str = None, timeframe: str = None, instances: int = 0, reverse: bool = False):
        '''timeframes: 1m, 5m, 1h, 1d'''
        request = self.bitmex.trade_bucketed_GET(
                binSize=timeframe, partial=True, symbol=symbol,
                count=instances, reverse=reverse)
                
        header = [
            'timestamp', 'symbol', 'open', 'high', 'low', 'close',
            'trades', 'volume', 'vwap', 'last size', 'turnover',
            'home notional', 'foreign notional'
        ]
        # response to dataframe
        data = pd.DataFrame.from_records(request, columns=header, index=None)
        data = data.dropna(axis=0, thresh=10)
        return data

    def indicator(
            self, symbol: str = None, timeframe: str = None, instances: int = 0,
            indicator: str = None, *args, **kwargs):
        '''params: symbol, timeframe, instances, indicator, <indicator args>, <indicator kwargs>'''
        # find max period
        max_ = max([v for k,v in kwargs.items() if 'period' in k])
        # dataframe for indicator calculation
        data = self.ohlcv(symbol=symbol, timeframe=timeframe, instances=instances+max_)
        data = data.iloc[::-1]

        # convert header (str) to numpy array of its values from dataframe
        # i.e. 'close' arg converts to array of close values
        # 'open' 'high' 'low' 'close' 'volume'
        args = list(args)
        for i, arg in enumerate(args):
            try:
                args[i] = data[arg].to_numpy()
            except:
                continue
 
        # return indicator values
        values = getattr(ta.func, indicator)(*args, **kwargs)
        return values[-instances:]

    # get help w/ params needed to call indicator method
    @staticmethod
    def indicator_help(indicator: str = None):
        if indicator not in ta.get_functions():
            raise ValueError(
                f'{indicator} is not supported\n'
                'https://github.com/mrjbq7/ta-lib#supported-indicators-and-functions'
            )
        help(getattr(ta.func, indicator))

class Trade:
    '''bitmex api functions'''
    def __init__(
            self, api_key: str =config.apiKey,
            api_secret: str = config.apiSecret):
        self.api_key = api_key
        self.api_secret = api_secret

        self.bitmex = BitMEX(api_key=self.api_key, api_secret=self.api_secret)

    def balance(self):
        '''account balance in btc'''
        bal = self.bitmex.user_wallet_GET()['amount'] / 100000000
        logger.info(f'{self.balance.__name__}: {bal}')
        return bal

    def position(self):
        '''open position amt'''
        open_qty = self.bitmex.position_GET()[0]['currentQty']
        logger.info(f'{self.position.__name__}: {open_qty}')
        return open_qty

    def price(self, symbol: str = 'XBTUSD'):
        '''contract current price'''
        response = self.bitmex.instrument_GET()
        for contract in response:
            if contract['symbol'] == symbol:
                price = contract['lastPrice']
                logger.info(f'{symbol} {self.price.__name__}: {price}')
                return price
        raise ValueError(f'{symbol}')

    def market(self, symbol: str = None, qty: int = 0):
        '''market order'''
        mkt = self.bitmex.order_POST(symbol=symbol, orderQty=qty, type='Market')
        logger.info(f'{self.market.__name__}: {mkt}')
        return mkt

    def limit(self, symbol: str = None, qty: int = 0, price: int = None):
        '''limit order'''
        lmt = self.bitmex.order_POST(
            symbol=symbol, orderQty=qty, price=price, type='Limit')
        logger.info(f'{self.limit.__name__}: {lmt}')
        return lmt

    def bulk(self, symbol: str = None, qty: int = 0, price: int = None, offset: int = 0):
        '''bulk order: qty: per order | starting price | offset: % b/t each order'''
        bulk = self.bitmex.order_bulk_POST(
            orders=json.dumps([{'symbol': symbol, 'orderQty': qty,
                                'price': price, 'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 1))),
                                'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 2))),
                                'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 3))),
                                'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 4))),
                                'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 5))),
                                'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 6))),
                                'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 7))),
                                'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 8))),
                                'type': 'Limit'},
                               {'symbol': symbol, 'orderQty': qty,
                                'price': (price * (1 + ((offset / 100) * 9))),
                                'type': 'Limit'},]),)
        logger.info(f'{self.bulk.__name__}: {bulk}')
        return bulk

    def close(self, symbol: str = None):
        '''close position'''
        close = self.bitmex.order_POST(symbol=symbol, execInst='Close')
        logger.info(f'{self.close.__name__}: {close}')
        return close

    def cancel(self):
        '''cancel all open orders'''
        cancel = self.bitmex.order_all_DELETE()
        logger.info(f'{self.cancel.__name__}: {cancel}')
        return cancel

    def balance_check(self):
        '''log account balance & failsafe check'''
        balance = self.get_balance()
        logger.info(f'balance: {balance}')

        # minimum balance failsafe
        if balance < config.fail_safe_amount:
            self.close()
            self.cancel_orders()
            try:
                alert('FAILSAFE', f'failsafe: {balance} < {config.fail_safe_amount}')
            except:
                pass
            logger.info(f'failsafe: {balance} < {config.fail_safe_amount}')
            raise SystemExit

    def qty_update(self, lev: int = 1, symbol: str = 'XBTUSD'):
        '''set order qty / leverage'''
        qty = int(self.get_balance() * self.get_price(symbol) * lev)
        logger.info(f'{self.qty_update.__name__}: {qty}')
        return qty


# scheduling
def schedule(hour: int = None, minute: int = None, second: int = None):
    '''hr 0-24 / min 0-59 / sec 0-59'''
    if hour:
        _hr(hour)
    if minute:
        _min(minute)
    if second:
        _sec(second)

def _hr(hr):
    while True:
        if datetime.now().hour == hr:
            break
        time.sleep(0.5)
        
def _min(minute):
    while True:
        if datetime.now().minute == minute:
            break
        time.sleep(0.5)

def _sec(sec):
    while True:
        if datetime.now().second == sec:
            break
        time.sleep(0.5)


# email alert
def alert(subj, msg):
    '''send email alert'''
    server = smtplib.SMTP('smtp.gmail.com:587')         # adjust for non-gmail smtp
    server.ehlo()
    server.starttls()
    server.login(config.from_email, config.from_password)
    message = f'Subject: {subj}\n\n{msg}'
    server.sendmail(from_addr=config.from_email, to_addrs=config.to_email,
                    msg=message)
    server.quit()
