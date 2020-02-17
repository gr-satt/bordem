> Wrapper that returns BitMEX XBTUSD OHLCV data, 150+ indicator values, interacts directly with BitMEX REST API and performs other trade related functions necessary to implement automated trading strategies.

> Python 3.7+

## Example
```python
from bordemwrapper import Data, Trade
from bordemwrapper import schedule, alert

# return BitMEX daily OHLCV data for the past 25 (instances) days
data = Data().ohlcv(symbol='XBTUSD', timeframe='1d', instances=25)

# return XBTUSD 14-period RSI values for the past 20 (instances) hourly candles
# params: symbol, timeframe, instances, indicator, <indicator args>, <indicator kwargs>
# args: 'close' arg converts to array of close values | 'open' 'high' 'low' 'close' 'volume'
# call indicator_help to see needed args, kwargs
indicator = Data().indicator('XBTUSD', '1h', 20, 'RSI', 'close', timeperiod=14)

# indicator help - show params & output
help_ = Data().indicator_help('STOCH')

# return current price
price = Trade().price(symbol='XBTUSD')

# set leverage - 2x on XBTUSD
Trade().qty_update(lev=2, symbol='XBTUSD')

# market order
Trade().market(symbol='XBTUSD', qty=10)

# bulk order: 10 (default amt) orders of 25 contracts every 1% above $10,000
Trade().bulk(symbol='XBTUSD', qty=25, price=10000, offset=1)

# handling multiple accounts
Trade(api_key='Acct_1_Key', api_secret='Acct_2_Secret')\
        .limit(symbol='XBTUSD', qty=10, price=1000)
Trade(api_key='Acct_2_Key', api_secret='Acct_2_Secret')\
        .limit(symbol='XBTUSD', qty=-1, price=1000)

# schedule - 9:30AM, 5:00PM
schedule(9, 30, 0)
schedule(17, 0, 0)

# send email alert
alert(subj='example', msg='message')

```

## Features
- OHLCV data for any BitMEX-support contract and timeframe
- return 150+ technical indicator values (ta-lib)
- interact directly with BitMEX rest api
- main & testnet support
- logging

## Methods
### Data(...)
- .ohlcv(...)
- .indicator(...)       `full list here: https://github.com/mrjbq7/ta-lib#supported-indicators-and-functions`
- .indicator_help(...)

### Trade(...)
- .balance()            `XBT quoted`
- .position()           `open position details`
- .price(...)
- .market(...)
- .limit(...)
- .bulk(...)
- .close(...)               `close open positions`
- .cancel()
- .balance_check()         `check/log balance`
- .qty_update(...)          `change leverage`

### Other BitMEX Endpoints:
- use cryptowrapper `https://github.com/xnr-k/cryptowrapper`
- for full list of endpoints visit `https://www.bitmex.com/api/explorer/`

## Other
- schedule(...)
- alert(...)          `email alert - from address, gmail support only`
    
## Requirements
- pandas 
- numpy
- TA Lib `http://mrjbq7.github.io/ta-lib/install.html`
- cryptowrapper `https://github.com/xnr-k/cryptowrapper`

## Setup
- manage settings in `config.py`

## Installation
- git clone `https://github.com/gr-satt/bordemwrapper`

## TODO
- expand supported timeframes
- backtesting
- gui

## Contact
- `bordemxbt@protonmail.com`
