import logging
from datetime import datetime
import json
import smtplib
import sys
import time

import numpy as np
import pandas as pd
import talib as ta
from cryptowrapper import BitMEX

import config


# disable msg -- %s %r has no %r member
# pylint: disable=E1101


# initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler = logging.FileHandler(filename='log.log', mode='a')        # full path may be needed in filename
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class BitMEXData:
    '''wrapper that returns:
    ohlcv dataframe (from bitmex rest api via cryptowrapper)
    indicator value (via TA-Lib)
    '''
    # for param errors
    supported_timeframes = ['1m', '5m', '1h', '1d']
    supported_indicators = ta.get_functions()
    supported_sources = ['open', 'close']

    def __init__(self, api_key: str = config.apiKey,
                 api_secret: str = config.apiSecret,
                 max_retries: int = 3, retry_time: int = 3,
                 request_timeout: int = 10, test: bool = False):
        '''params:
            api_key         (bitmex api)
            api_secret      (bitmex api)
            max_retries     (number of retries on error)
            retry_time      (time b/t retries - seconds)
            request_timeout (expiry - seconds)
            test            (live is default)
        '''
        self.api_key = api_key
        self.api_secret = api_secret
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.request_timeout = request_timeout
        self.test = test

    # cryptowrapper
    def init_request(self):
        bitmex = BitMEX(api_key=self.api_key, api_secret=self.api_secret,
                        max_retries=self.max_retries,
                        retry_time=self.retry_time,
                        request_timeout=self.request_timeout)
        # live (default) or testnet
        if self.test is True:
             bitmex.BASE_URL = 'https://testnet.bitmex.com/api/v1'
        else:
            bitmex.BASE_URL = 'https://www.bitmex.com/api/v1'
        return bitmex

    # endpoint
    def get_ohlcv(self, symbol: str = None, timeframe: str = None,
                  instances: int = 0):
        '''return ohlvc dataframe

        params:
            symbol      (str)
            timeframe   (str: 1m, 5m, 1h, 1d)
            instances   (int: last # of candles to get)
        '''
        #unsupported timeframe
        if timeframe not in self.supported_timeframes:
            raise ValueError('{} is not supported\n\nsupported timeframes:\n{}'\
                             .format(timeframe, self.supported_timeframes))

        # request
        bitmex = self.init_request()
        request = bitmex.trade_bucketed_GET(
            binSize=timeframe, partial=True, symbol=symbol,
            count=instances, reverse=True)
        header = [
            'timestamp', 'symbol', 'open', 'high', 'low', 'close', 'trades',
            'volume', 'vwap', 'last size', 'turnover', 'home notional',
            'foreign notional']
        data = pd.DataFrame.from_records(request, columns=header, index=None)
        data = data.iloc[::-1]
        data = data.dropna(axis=0, thresh=10)
        return data

    # endpoint
    def get_indicator(self, symbol: str = None, timeframe: str = None,
                      indicator: str = None, period: int = 0,
                      source: str = 'close', instances: int = 0):
        '''return indicator value

        params:
            symbol      (str)
            timeframe   (str: 1m, 5m, 1h, 1d)
            indicator   (str: see README)
            period      (int)
            source      (str: open / close)
            instances   (int: last # of candles to get)
        '''
        # unsupported timeframe
        if timeframe not in self.supported_timeframes:
            raise ValueError('{} is not supported\n\nsupported timeframes:\n{}'\
                             .format(timeframe, self.supported_timeframes))
        # unsupported indicator
        if indicator not in self.supported_indicators or None:
            raise ValueError('{} is not supported by ta-lib\n\nsupported\
                             indicators:\n{}'.format(indicator,
                                                     self.supported_indicators))
        # source error
        if source not in self.supported_sources or None:
            raise ValueError('unrecognized source param - sources:\n{}'\
                             .format(self.supported_sources))

        # request
        bitmex = self.init_request()
        request = bitmex.trade_bucketed_GET(
            binSize=timeframe, partial=True, symbol=symbol,
            count=instances + period, reverse=True)
        header = [
            'timestamp', 'symbol', 'open', 'high', 'low', 'close', 'trades',
            'volume', 'vwap', 'last size', 'turnover', 'home notional',
            'foreign notional']
        data = pd.DataFrame.from_records(request, columns=header, index=None)
        data = data.iloc[::-1]
        data = data.dropna(axis=0, thresh=10)

        # separate columns
        source = data[source]
        open_ = data['open']
        high = data['high']
        low = data['low']
        close = data['close']
        vol = data['volume']
        # TA-Lib req. numpy array
        array_source = source.to_numpy()
        array_open = open_.to_numpy()
        array_high = high.to_numpy()
        array_low = low.to_numpy()
        array_close = close.to_numpy()
        array_vol = vol.to_numpy()

        # TA-Lib
        # overlap studies
        if indicator == 'BBANDS':
            up, mid, low = ta.func.BBANDS(array_source, timeperiod=period,
                                          nbdevup=2, nbdevdn=2, matype=0)
            return up[-instances:], mid[-instances:], low[-instances:]
        if indicator == 'DEMA':
            value = ta.func.DEMA(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'EMA':
            value = ta.func.EMA(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'HT_TRENDLINE':
            value = ta.func.HT_TRENDLINE(array_source)
            return value[-instances:]
        if indicator == 'KAMA':
            value = ta.func.KAMA(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'MA':
            value = ta.func.MA(array_source, timeperiod=period, matype=0)
            return value[-instances:]
        if indicator == 'MAMA':
            raise NotImplementedError
        if indicator == 'MAVP':
            value = ta.func.MAVP(array_source, minperiod=(period / 2),
                                 maxperiod=(period * 2), matype=0)
            return value[-instances:]
        if indicator == 'MIDPOINT':
            value = ta.func.MIDPOINT(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'MIDPRICE':
            value = ta.func.MIDPRICE(array_high, array_low,
                                     timeperiod=period)
            return value[-instances:]
        if indicator == 'SAR':
            value = ta.func.SAR(array_high, array_low, acceleration=0.02,
                                maximum=0.2)
            return value[-instances:]
        if indicator == 'SAREXT':
            raise NotImplementedError
        if indicator == 'SMA':
            value = ta.func.SMA(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'T3':
            value = ta.func.T3(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'TEMA':
            value = ta.func.TEMA(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'TRIMA':
            value = ta.func.TRIMA(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'WMA':
            value = ta.func.WMA(array_source, timeperiod=period)
            return value[-instances:]
        # momentum indicators
        if indicator == 'ADX':
            value = ta.func.ADX(array_high, array_low, array_source,
                                timeperiod=period)
            return value[-instances:]
        if indicator == 'ADXR':
            value = ta.func.ADXR(array_high, array_low, array_source,
                                 timeperiod=period)
            return value[-instances:]
        if indicator == 'APO':
            value = ta.func.APO(array_source, fastperiod=12, slowperiod=26,
                                matype=0)
        if indicator == 'AROON':
            aroonup, aroondn = ta.func.AROON(array_high, array_low,
                               timeperiod=period)
            return aroonup[-instances:], aroondn[-instances:]
        if indicator == 'AROONOSC':
            value = ta.func.AROONOSC(array_high, array_low,
                                     timeperiod=period)
            return value[-instances:]
        if indicator == 'BOP':
            value = ta.func.BOP(array_open, array_high, array_low, array_close)
            return value[-instances:]
        if indicator == 'CCI':
            value = ta.func.CCI(array_high, array_low, array_source,
                                timeperiod=period)
            return value[-instances:]
        if indicator == 'CMO':
            value = ta.func.CMO(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'DX':
            value = ta.func.DX(array_high, array_low, array_source,
                               timeperiod=period)
            return value[-instances:]
        if indicator == 'MACD':
            macd, macdsignal, macdhist = ta.func.MACD(array_source,
                                                      fastperiod=12,
                                                      slowperiod=26,
                                                      signalperiod=9)
            return macd[-instances:], macdsignal[-instances:], macdhist[-instances:]
        if indicator == 'MACDEXT':
            raise NotImplementedError
        if indicator == 'MACDFIX':
            raise NotImplementedError
        if indicator == 'MFI':
            value = ta.func.MFI(array_high, array_low, array_source, array_vol,
                                timeperiod=period)
            return value[-instances:]
        if indicator == 'MINUS_DI':
            value = ta.func.MINUS_DI(array_high, array_low, array_source,
                                     timeperiod=period)
            return value[-instances:]
        if indicator == 'MINUS_DM':
            value = ta.func.MINUS_DM(array_high, array_low,
                                     timeperiod=period)
            return value[-instances:]
        if indicator == 'MOM':
            value = ta.func.MOM(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'PLUS_DI':
            value = ta.func.PLUS_DI(array_high, array_low, array_source,
                                    timeperiod=period)
            return value[-instances:]
        if indicator == 'PLUS_DM':
            value = ta.func.PLUS_DM(array_high, array_low,
                                    timeperiod=period)
            return value[-instances:]
        if indicator == 'PPO':
            value = ta.func.PPO(array_source, fastperiod=12, slowperiod=26,
                                matype=0)
            return value[-instances:]
        if indicator == 'ROC':
            value = ta.func.ROC(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'ROCP':
            value = ta.func.ROCP(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'ROCR100':
            value = ta.func.ROCR100(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'RSI':
            value = ta.func.RSI(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'STOCH':
            slowk, slowd = ta.func.STOCH(array_high, array_low, array_source,
                                         fastk_period=5, slowk_period=3,
                                         slowk_matype=0, slowd_period=3,
                                         slowd_matype=0)
            return slowk[-instances:], slowd[-self.instances]
        if indicator == 'STOCHF':
            fastk, fastd = ta.func.STOCHF(array_high, array_low, array_source,
                                          fastk_period=5, fastd_period=3,
                                          fastd_matype=0)
            return fastk[-instances:], fastd[-instances:]
        if indicator == 'STOCHRSI':
            fastk, fastd = ta.func.STOCHRSI(array_source,
                                            timeperiod=period,
                                            fastk_period=5, fastd_period=3,
                                            fastd_matype=0)
            return fastk[-instances:], fastd[-instances:]
        if indicator == 'TRIX':
            raise NotImplementedError
        if indicator == 'ULTOSC':
            value = ta.func.ULTOSC(array_high, array_low, array_source,
                                   timeperiod1=7, timeperiod2=14,
                                   timeperiod3=28)
            return value[-instances:]
        if indicator == 'WILLR':
            value = ta.func.WILLR(array_high, array_low, array_source,
                                  timeperiod=period)
            return value[-instances:]
        # volume indicators
        if indicator == 'AD':
            value = ta.func.AD(array_high, array_low, array_source, array_vol)
            return value[-instances:]
        if indicator == 'ADOSC':
            value = ta.func.ADOSC(array_high, array_low, array_source,
                                  array_vol, fastperiod=3, slowperiod=10)
            return value[-instances:]
        if indicator == 'OBV':
            value = ta.func.OBV(array_source, array_vol)
            return value[-instances:]
        # volatility indicators
        if indicator == 'ATR':
            value = ta.func.ATR(array_high, array_low, array_source,
                                timeperiod=period)
            return value[-instances:]
        if indicator == 'NATR':
            value = ta.func.NATR(array_high, array_low, array_source,
                                 timeperiod=period)
            return value[-instances:]
        if indicator == 'TRANGE':
            value = ta.func.TRANGE(array_high, array_low, array_source)
            return value[-instances:]
        # price transform
        if indicator == 'AVGPRICE':
            value = ta.func.AVGPRICE(array_open, array_high, array_low,
                                     array_source)
            return value[-instances:]
        if indicator == 'MEDPRICE':
            value = ta.func.MEDPRICE(array_high, array_low)
            return value[-instances:]
        if indicator == 'TYPRICE':
            value = ta.func.TYPRICE(array_high, array_low, array_source)
            return value[-instances:]
        if indicator == 'WCLPRICE':
            value = ta.func.WCLPRICE(array_high, array_low, array_source)
            return value[-instances:]
        # cycle indicators
        if indicator == 'HT_DCPERIOD':
            value = ta.func.HT_DCPERIOD(array_source)
            return value[-instances:]
        if indicator == 'HT_DCPHASE':
            value = ta.func.HT_DCPHASE(array_source)
            return value[-instances:]
        if indicator == 'HT_PHASOR':
            inphase, quadature = ta.func.HT_PHASOR(array_source)
            return inphase[-instances:], quadature[-instances:]
        if indicator == 'HT_SINE':
            sine, leadsine = ta.func.HT_SINE(array_source)
            return sine[-instances:], leadsine[-instances:]
        if indicator == 'HT_TRENDMODE':
            interger = ta.func.HT_TRENDMODE(array_source)
            return interger[-instances:]
        # pattern recognition
        if indicator == 'CDL2CROWS':
            interger = ta.func.CDL2CROWS(array_open, array_high, array_low,
                                         array_close)
            return interger[-instances:]
        if indicator == 'CDL3BLACKCROWS':
            interger = ta.func.CDL3BLACKCROWS(array_open, array_high,
                                              array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDL3INSIDE':
            interger = ta.func.CDL3INSIDE(array_open, array_high, array_low,
                                          array_close)
            return interger[-instances:]
        if indicator == 'CDL3LINESTRIKE':
            interger = ta.func.CDL3LINESTRIKE(array_open, array_high, array_low,
                                              array_close)
            return interger[-instances:]
        if indicator == 'CDL3OUTSIDE':
            interger = ta.func.CDL3OUTSIDE(array_open, array_high, array_low,
                                           array_close)
            return interger[-instances:]
        if indicator == 'CDL3STARSINSOUTH':
            interger = ta.func.CDL3STARSINSOUTH(array_open, array_high,
                                                array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDL3WHITESOLDIERS':
            interger = ta.func.CDL3WHITESOLDIERS(array_open, array_high,
                                                 array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLABANDONEDBABY':
            interger = ta.func.CDLABANDONEDBABY(array_open, array_high,
                                                array_low, array_close,
                                                penetration=0)
            return interger[-instances:]
        if indicator == 'CDLADVANCEBLOCK':
            interger = ta.func.CDLADVANCEBLOCK(array_open, array_high,
                                               array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLBELTHOLD':
            interger = ta.func.CDLBELTHOLD(array_open, array_high, array_low,
                                           array_close)
            return interger[-instances:]
        if indicator == 'CDLBREAKAWAY':
            interger = ta.func.CDLBREAKAWAY(array_open, array_high, array_low,
                                            array_close)
            return interger[-instances:]
        if indicator == 'CDLCLOSINGMARUBOZU':
            interger = ta.func.CDLCLOSINGMARUBOZU(array_open, array_high,
                                                  array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLCONCEALBABYSWALL':
            interger = ta.func.CDLCONCEALBABYSWALL(array_open, array_high,
                                                   array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLCOUNTERATTACK':
            interger = ta.func.CDLCOUNTERATTACK(array_open, array_high,
                                                array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLDARKCLOUDCOVER':
            interger = ta.func.CDLDARKCLOUDCOVER(array_open, array_high,
                                                 array_low, array_close,
                                                 penetration=0)
            return interger[-instances:]
        if indicator == 'CDLDOJI':
            interger = ta.func.CDLDOJI(array_open, array_high, array_low,
                                       array_close)
            return interger[-instances:]
        if indicator == 'CDLDOJISTAR':
            interger = ta.func.CDLDOJISTAR(array_open, array_high, array_low,
                                           array_close)
            return interger[-instances:]
        if indicator == 'CDLDRAGONFLYDOJI':
            interger = ta.func.CDLDRAGONFLYDOJI(array_open, array_high,
                                                array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLENGULFING':
            interger = ta.func.CDLENGULFING(array_open, array_high, array_low,
                                            array_close)
            return interger[-instances:]
        if indicator == 'CDLEVENINGDOJISTAR':
            interger = ta.func.CDLEVENINGDOJISTAR(array_open, array_high,
                                                  array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLEVENINGSTAR':
            interger = ta.func.CDLEVENINGSTAR(array_open, array_high,
                                              array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLGAPSIDESIDEWHITE':
            interger = ta.func.CDLGAPSIDESIDEWHITE(array_open, array_high,
                                                   array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLGRAVESTONEDOJI':
            interger = ta.func.CDLGRAVESTONEDOJI(array_open, array_high,
                                                 array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLHAMMER':
            interger = ta.func.CDLHAMMER(array_open, array_high, array_low,
                                         array_close)
            return interger[-instances:]
        if indicator == 'CDLHANGINGMAN':
            interger = ta.func.CDLHANGINGMAN(array_open, array_high, array_low,
                                             array_close)
            return interger[-instances:]
        if indicator == 'CDLHARAMI':
            interger = ta.func.CDLHARAMI(array_open, array_high, array_low,
                                         array_close)
            return interger[-instances:]
        if indicator == 'CLDHARAMICROSS':
            interger = ta.func.CLDHARAMICROSS(array_open, array_high,
                                              array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLHIGHWAVE':
            interger = ta.func.CDLHIGHWAVE(array_open, array_high,
                                           array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLHIKKAKE':
            interger = ta.func.CDLHIKKAKE(array_open, array_high,
                                          array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLHIKKAKEMOD':
            interger = ta.func.CDLHIKKAKEMOD(array_open, array_high,
                                             array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLHOMINGPIDGEON':
            interger = ta.func.CDLHOMINGPIDGEON(array_open, array_high,
                                                array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLIDENTICAL3CROWS':
            interger = ta.func.CDLIDENTICAL3CROWS(array_open, array_high,
                                                  array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLINNECK':
            interger = ta.func.CDLINNECK(array_open, array_high, array_low,
                                         array_close)
            return interger[-instances:]
        if indicator == 'CDLINVERTEDHAMMER':
            interger = ta.func.CDLINVERTEDHAMMER(array_open, array_high,
                                                 array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLKICKING':
            interger = ta.func.CDLKICKING(array_open, array_high, array_low,
                                                      array_close)
            return interger[-instances:]
        if indicator == 'CDLKICKINGBYLENGTH':
            interger = ta.func.CDLKICKINGBYLENGTH(array_open, array_high,
                                                  array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLLADDERBOTTOM':
            interger = ta.func.CDLLADDERBOTTOM(array_open, array_high,
                                               array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLLONGLEGGEDDOJI':
            interger = ta.func.CDLLONGLEGGEDDOJI(array_open, array_high,
                                                 array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLLONGLINE':
            interger = ta.func.CDLLONGLINE(array_open, array_high, array_low,
                                           array_close)
            return interger[-instances:]
        if indicator == 'CDLMARUBOZU':
            interger = ta.func.CDLMARUBOZU(array_open, array_high, array_low,
                                           array_close)
            return interger[-instances:]
        if indicator == 'CDLMATCHINGLOW':
            interger = ta.func.CDLMATCHINGLOW(array_open, array_high,
                                              array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLMATHOLD':
            interger = ta.func.CDLMATHOLD(array_open, array_high, array_low,
                                          array_close, penetration=0)
            return interger[-instances:]
        if indicator == 'CDLMORNINGSTARDOJI':
            interger = ta.func.CDLMORNINGSTARDOJI(array_open, array_high,
                                                  array_low, array_close,
                                                  penetration=0)
            return interger[-instances:]
        if indicator == 'CDLMORNINGSTAR':
            interger = ta.func.CDLMORNINGSTAR(array_open, array_high,
                                              array_low, array_close,
                                              penetration=0)
            return interger[-instances:]
        if indicator == 'CDLONNECK':
            interger = ta.func.CDLONNECK(array_open, array_high, array_low,
                                         array_close)
            return interger[-instances:]
        if indicator == 'CDLPIERCING':
            interger = ta.func.CDLPIERCING(array_open, array_high, array_low,
                                           array_close)
            return interger[-instances:]
        if indicator == 'CDLRICKSHAWMAN':
            interger = ta.func.CDLRICKSHAWMAN(array_open, array_high, array_low,
                                              array_close)
            return interger[-instances:]
        if indicator == 'CDLRISEFALL3METHODS':
            interger = ta.func.CDLRISEFALL3METHODS(array_open, array_high,
                                                   array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLSEPARATINGLINES':
            interger = ta.func.CDLSEPARATINGLINES(array_open, array_high,
                                                  array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLSHOOTINGSTAR':
            interger = ta.func.CDLSHOOTINGSTAR(array_open, array_high,
                                               array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLSHORTLINE':
            interger = ta.func.CDLSHORTLINE(array_open, array_high, array_low,
                                            array_close)
            return interger[-instances:]
        if indicator == 'CDLSPINNINGTOP':
            interger = ta.func.CDLSPINNINGTOP(array_open, array_high, array_low,
                                              array_close)
            return interger[-instances:]
        if indicator == 'CDLSTALLEDPATTERN':
            interger = ta.func.CDLSTALLEDPATTERN(array_open, array_high,
                                                 array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLSTICKSANDWICH':
            interger = ta.func.CDLSTICKSANDWICH(array_open, array_high,
                                                array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLTARUKI':
            interger = ta.func.CDLTARUKI(array_open, array_high, array_low,
                                         array_close)
            return interger[-instances:]
        if indicator == 'CDLTASUKIGAP':
            interger = ta.func.CDLTASUKIGAP(array_open, array_high, array_low,
                                            array_close)
            return interger[-instances:]
        if indicator == 'CDLTHRUSTING':
            interger = ta.func.CDLTHRUSTING(array_open, array_high, array_low,
                                            array_close)
            return interger[-instances:]
        if indicator == 'CDLTRISTAR':
            interger = ta.func.CDLTRISTAR(array_open, array_high, array_low,
                                          array_close)
            return interger[-instances:]
        if indicator == 'CDLUNIQUE3RIVER':
            interger = ta.func.CDLUNIQUE3RIVER(array_open, array_high,
                                               array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLUPSIDEGAP2CROWS':
            interger = ta.func.CDLUPSIDEGAP2CROWS(array_open, array_high,
                                                  array_low, array_close)
            return interger[-instances:]
        if indicator == 'CDLXSIDEGAP3METHODS':
            interger = ta.func.CDLXSIDEGAP3METHODS(array_open, array_high,
                                                   array_low, array_close)
            return interger[-instances:]
        # statistic functions
        if indicator == 'BETA':
            value = ta.func.BETA(array_high, array_low, timeperiod=period)
            return value[-instances:]
        if indicator == 'CORREL':
            value = ta.func.CORREL(array_high, array_low,
                                   timeperiod=period)
            return value[-instances:]
        if indicator == 'LINEARREG':
            value = ta.func.LINEARREG(array_close, timeperiod=period)
            return value[-instances:]
        if indicator == 'LINEARREG_ANGLE':
            value = ta.func.LINEARREG_ANGLE(array_close, timeperiod=period)
            return value[-instances:]
        if indicator == 'LINEARREG_INTERCEPT':
            value = ta.func.LINEARREG_INTERCEPT(array_close,
                                                timeperiod=period)
            return value[-instances:]
        if indicator == 'LINEARREG_SLOPE':
            value = ta.func.LINEARREG_SLOPE(array_close, timeperiod=period)
            return value[-instances:]
        if indicator == 'STDDEV':
            value = ta.func.STDDEV(array_close, timeperiod=period, nbdev=1)
            return value[-instances:]
        if indicator == 'TSF':
            value = ta.func.TSF(array_close, timeperiod=period)
            return value[-self.instances]
        if indicator == 'VAR':
            value = ta.func.VAR(array_close, timeperiod=period, nbdev=1)
            return value[-instances:]
        # math transform
        if indicator == 'ACOS':
            value = ta.func.ACOS(array_source)
            return value[-instances:]
        if indicator == 'ASIN':
            value = ta.func.ASIN(array_source)
            return value[-instances:]
        if indicator == 'ATAN':
            value = ta.func.ATAN(array_source)
            return value[-instances:]
        if indicator == 'CEIL':
            value = ta.func.CEIL(array_source)
            return value[-instances:]
        if indicator == 'COS':
            value = ta.func.COS(array_source)
            return value[-instances:]
        if indicator == 'COSH':
            value = ta.func.COSH(array_source)
            return value[-instances:]
        if indicator == 'EXP':
            value = ta.func.EXP(array_source)
            return value[-instances:]
        if indicator == 'FLOOR':
            value = ta.func.FLOOR(array_source)
            return value[-instances:]
        if indicator == 'LN':
            value = ta.func.LN(array_source)
            return value[-instances:]
        if indicator == 'SIN':
            value = ta.func.SIN(array_source)
            return value[-instances:]
        if indicator == 'SINH':
            value = ta.func.SINH(array_source)
            return value[-instances:]
        if indicator == 'SQRT':
            value = ta.func.SQRT(array_source)
            return value[-instances:]
        if indicator == 'TAN':
            value = ta.func.TAN(array_source)
            return value[-instances:]
        if indicator == 'TANH':
            value = ta.func.TANH(array_source)
            return value[-instances:]
        # math operators
        if indicator == 'ADD':
            value = ta.func.ADD(array_high, array_low)
            return value[-instances:]
        if indicator == 'DIV':
            value = ta.func.DIV(array_high, array_low)
            return value[-instances:]
        if indicator == 'MAX':
            value = ta.func.MAX(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'MAXINDEX':
            value = ta.func.MAXINDEX(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'MIN':
            value = ta.func.MIN(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'MININDEX':
            value = ta.func.MININDEX(array_source, timeperiod=period)
            return value[-instances:]
        if indicator == 'MINMAX':
            min_, max_ = ta.func.MINMAX(array_source, timeperiod=period)
            return min_[-instances:], max_[-instances:]
        if indicator == 'MINMAXINDEX':
            minidx, maxidx = ta.func.MINMAXINDEX(array_source,
                                                 timeperiod=period)
            return minidx[-instances:], maxidx[-instances:]
        if indicator == 'MULT':
            value = ta.func.MULT(array_high, array_low)
            return value[-instances:]
        if indicator == 'SUB':
            value = ta.func.SUB(array_high, array_low)
            return value[-instances:]
        if indicator == 'SUM':
            value = ta.func.SUM(array_source, timeperiod=period)
            return value[-instances:]
        else:
            raise ValueError('{} not recognized'.format(indicator))


class BitMEXFunctions:
    '''
    wrapper that performs:
    exchange operations (directly w/ bitmex rest api via cryptowrapper)
    '''
    def __init__(self, api_key: str = config.apiKey,
                 api_secret: str = config.apiSecret,
                 max_retries: int = 3, retry_time: int = 3,
                 request_timeout: int = 10,test: bool = False):
        '''params:
            api_key         (bitmex api)
            api_secret      (bitmex api)
            max_retries     (number of retries on error)
            retry_time      (time b/t retries - seconds)
            request_timeout (expiry - seconds)
        '''
        self.api_key = api_key
        self.api_secret = api_secret
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.request_timeout = request_timeout
        self.test = test

    # cryptowrapper
    def init_request(self):
        bitmex = BitMEX(api_key=self.api_key, api_secret=self.api_secret,
                        max_retries=self.max_retries,
                        retry_time=self.retry_time,
                        request_timeout=self.request_timeout)
        # live (default) or testnet
        if self.test is True:
             bitmex.BASE_URL = 'https://testnet.bitmex.com/api/v1'
        else:
            bitmex.BASE_URL = 'https://www.bitmex.com/api/v1'
        return bitmex

    # exchange / trading functions
    def get_balance(self):
        '''account balance (btc)'''
        bitmex = self.init_request()
        balance = bitmex.user_wallet_GET()['amount'] / 100000000
        logger.info('balance: {}'.format(balance))
        return balance

    def get_position(self):
        '''open position amt'''
        bitmex = self.init_request()
        open_qty = bitmex.position_GET()[0]['currentQty']
        logger.info('open qty: {}'.format(open_qty))
        return open_qty

    def get_price(self, symbol: str = 'XBTUSD'):
        '''contract current price'''
        bitmex = self.init_request()
        response = bitmex.instrument_GET()
        for contract in response:
            if contract['symbol'] == symbol:
                price = contract['lastPrice']
                logger.info('{} price: {}'.format(symbol, price))
                return price
        raise ValueError('could not find {} contract'.format(symbol))

    def market_order(self, symbol: str = None, qty: int = 0):
        '''market order'''
        bitmex = self.init_request()
        mkt = bitmex.order_POST(symbol=symbol, orderQty=qty, type='Market')
        logger.info('market order: {}'.format(mkt))
        return mkt

    def limit_order(self, symbol: str = None, qty: int = 0, price: int = None):
        '''limit order'''
        bitmex = self.init_request()
        lmt = bitmex.order_POST(symbol=symbol, orderQty=qty, price=price,
                                type='Limit')
        logger.info('limit order: {}'.format(lmt))
        return lmt

    def bulk_order(self, symbol: str = None, qty: int = 0, price: int = None,
                   offset: int = 0):
        '''bulk order 10 limit trades:

            qty     (quantity per 1 of 10 orders. qty = 10 --> 100 total)
            price   (starting price)
            offset  (% (+ or -) b/t each --> 1 = 1%)
        '''
        bitmex = self.init_request()
        bulk = bitmex.order_bulk_POST(
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
        logger.info('bulk order: {}'.format(bulk))
        return bulk

    def close(self, symbol: str = None):
        '''close out position'''
        bitmex = self.init_request()
        close = bitmex.order_POST(symbol=symbol, execInst='Close')
        logger.info('close position: {}'.format(close))
        return close

    def cancel_orders(self):
        '''cancel open orders'''
        bitmex = self.init_request()
        cancel = bitmex.order_all_DELETE()
        logger.info('cancel orders: {}'.format(cancel))
        return cancel

    def balance_update(self):
        '''
        check balance
        append balance to log
        failsafe check
        '''
        balance = self.get_balance()
        logger.info('balance: {}'.format(balance))

        # failsafe
        if balance < config.fail_safe_amount:
            self.close()
            self.cancel_orders()
            logger.info('failsafe')
            sys.exit('balance of {} has fallen below {} failsafe level'\
                     .format(balance, config.fail_safe_amount))
        else:
            pass

    def qty_update(self, lev: int = 1, symbol: str = 'XBTUSD'):
        '''set order qty / leverage'''
        qty = int(self.get_balance() * self.get_price(symbol) * lev)
        logger.info('order qty: {}'.format(qty))
        return qty


class TradeFunctions:
    '''non-BitMEX trading functions'''

    @staticmethod
    def hour(hr):
        '''0-23'''
        while True:
            if datetime.now().hour == hr:
                break
            time.sleep(0.5)

    @staticmethod
    def minute(minute):
        '''0-59'''
        while True:
            if datetime.now().minute == minute:
                break
            time.sleep(0.5)

    @staticmethod
    def second(sec):
        '''0-59'''
        while True:
            if datetime.now().second == sec:
                break
            time.sleep(0.5)

    @staticmethod
    def send_alert(subj, msg):
        '''send email alert

        inputs:
            from_email      (gmail)
            from_password   (gmail)
            to_email
        '''

        server = smtplib.SMTP('smtp.gmail.com:587')     # change server for non-gmail smtp
        server.ehlo()
        server.starttls()
        server.login(config.from_email, config.from_password)
        message = 'Subject: {}\n\n{}'.format(subj, msg)
        server.sendmail(from_addr=config.from_email, to_addrs=config.to_email,
                        msg=message)
        server.quit()
