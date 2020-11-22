![Image of logo](https://i.imgur.com/Gvv27Mq.jpg)

> Build automated trading strategies for BitMEX contracts.

> Easily return BitMEX OHLCV data, 150+ indicator values.

> Interacts directly with BitMEX REST API v1.

> Main & Testnet support

> Python 3.7+

## Usage
```python
from bordemwrapper import Data, Trade
from bordemwrapper import schedule, alert

# return BitMEX daily OHLCV data for the past 25 (instances) days
# timeframe options: 1m, 5m, 1h, 1d
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
# bulk order: 10 (default amt) orders of 25 contracts every 1% below $10,000
Trade().bulk(symbol='XBTUSD', qty=25, price=10000, offset=-1)

# handling multiple accounts
Trade(api_key='Acct_1_Key', api_secret='Acct_2_Secret')\
        .limit(symbol='XBTUSD', qty=10, price=1000)
Trade(api_key='Acct_2_Key', api_secret='Acct_2_Secret')\
        .limit(symbol='XBTUSD', qty=-1, price=1000)

# schedule - 9:30AM, 5:00PM
# sleep until given time
schedule(9, 30, 0)
schedule(17, 0, 0)

# send email alert
alert(subj='example', msg='message')

```

## Methods
### Data(...)
- .ohlcv(...)
- .indicator(...)       `full list here: https://github.com/mrjbq7/ta-lib#supported-indicators-and-functions`
- .indicator_help(...)

### Trade(...)
- .balance()            `XBT quoted`
- .position()           `open position details`
- .price(...)           `current contract price`
- .market(...)          `market order`
- .limit(...)           `limit order`
- .bulk(...)            `order staggering`
- .close(...)           `close open positions`
- .cancel()             `cancel open order(s)`
- .balance_check()      `check/log balance`
- .qty_update(...)      `change leverage`

### Other
- schedule(...)
- alert(...)            `email alert - from address, gmail support only`