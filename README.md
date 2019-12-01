> Wrapper returns BitMEX OHLCV data, 150+ indicator values, interacts directly with BitMEX REST API and performs other trade related functions necessary to implement automated trading strategies.
> Geared more towards those just getting beginning to automate trading strategies or those just starting out with python.

## Example
```python
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

# bulk order: 10 (default amt) orders of 10 contracts every 1 percent above $10,000
BitMEXFunctions().bulk_order(symbol='XBTUSD', qty=10, price=10000, offset=1)

# handling multiple accounts
BitMEXFunctions(api_key='Acct_1_Key', api_secret='Acct_2_Secret').limit_order(symbol='XBTUSD', qty=10, price=1000)
BitMEXFunctions(api_key='Acct_2_Key', api_secret='Acct_2_Secret').limit_order(symbol='XBTUSD', qty=-1, price=1000)

# send email alert
TradeFunctions().send_alert(subj='example', msg='message')

```

## Features
- OHLCV data for any BitMEX contract & BitMEX-supported timeframe
- return 150+ technical indicator values
- interact directly with BitMEX rest api to fetch balance, current price, open position, vwap, as well as create market, limit, and bulk orders (built-in functions)
- main & testnet support
- logging

## Methods
### BitMEXData(...)
- .get_ohlcv(...)
- .get_indicator(...)       | full list here: `https://github.com/mrjbq7/ta-lib#supported-indicators-and-functions`

### BitMEXFunctions(...)
- .get_balance()            | XBT quoted
- .get_position()           | open position details
- .get_xbt_price()
- .get_xbt_vwap()
- .market_order(...)
- .limit_order(...)
- .bulk_order(...)
- .close(...)               | close open positions
- .cancel_orders()
- .balance_update()         | check/log balance
- .qty_update(...)          | change leverage

### Other BitMEX Endpoints:
- use cryptowrapper `https://github.com/xnr-k/cryptowrapper`
- for full list of endpoints visit `https://www.bitmex.com/api/explorer/`

### TradeFunctions()
- .fetch_current_hr(...)
- .fetch_current_min(...)
- .fetch_current_sec(...)
- .send_alert(...)          | email alert - from address, gmail support only
    
## Requirements
- pandas 
- numpy
- TA Lib `http://mrjbq7.github.io/ta-lib/install.html`
- cryptowrapper `https://github.com/xnr-k/cryptowrapper`

## TODO
- more timeframes
- strategy backtesting

## Setup
- in `inputs` directory open `config.py` - enter email info & API keys

## Clone
- Clone this repo to your local machine using `https://github.com/gr-satt/bordemwrapper`

## Requests / Contact
- to request unsupported exhange, symbol, timeframe, etc. --> message --> `bordemxbt@protonmail.com`
