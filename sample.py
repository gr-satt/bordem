from bordemwrapper import BitMEXData, BitMEXFunctions, TradeFunctions


# return BitMEX hourly OHLCV data for the past 25 hours
data = BitMEXData().get_ohlcv(symbol='XBTUSD', timeframe='1h', instances=25)

# return XBTUSD 20-period RSI values for the past 25 daily candles
indicator = BitMEXData().get_indicator(symbol='XBTUSD', timeframe='1d',
                                       indicator='RSI', period=20,
                                       source='close', instances=25)

# return current price
price = BitMEXFunctions().get_price(symbol='XBTUSD')

# market order
BitMEXFunctions().market_order(symbol='XBTUSD', qty=10)

# bulk order: 10 (default amt) orders of 10 contracts every 1% above $10,000
BitMEXFunctions().bulk_order(symbol='XBTUSD', qty=10, price=10000, offset=1)

# handling multiple accounts
BitMEXFunctions(api_key='Acct_1_Key', api_secret='Acct_2_Secret')\
        .limit_order(symbol='XBTUSD', qty=10, price=1000)
BitMEXFunctions(api_key='Acct_2_Key', api_secret='Acct_2_Secret')\
        .limit_order(symbol='XBTUSD', qty=-1, price=1000)

# send email alert
TradeFunctions().send_alert(subj='example', msg='message')
