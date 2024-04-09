# from keys import api, secret
from binance.um_futures import UMFutures
import ta
import pandas as pd
from time import sleep
from binance.error import ClientError

client = UMFutures(key = api, secret=secret)

# 0.012 means +1.2%, 0.009 is -0.9%
tp = 0.012
sl = 0.009
volume = 10  # volume for one order (if its 10 and leverage is 10, then you put 1 usdt to one position)
leverage = 10
type = 'ISOLATED'  # type is 'ISOLATED' or 'CROSS'
qty = 100  # Amount of concurrent opened positions

# getting your futures balance in USDT
def get_balance_usdt():
    """
    Retrieves the balance of USDT from the Binance Futures API.

    Returns:
        float: The balance of USDT.

    Raises:
        ClientError: If there is an error while retrieving the balance.
    """
    try:
        response = client.balance(recvWindow=6000)
        for elem in response:
            if elem['asset'] == 'USDT':
                return float(elem['balance'])

    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Getting all available symbols on the Futures ('BTCUSDT', 'ETHUSDT', ....)
def get_tickers_usdt():
    """
    Retrieves a list of ticker symbols that are paired with USDT.

    Returns:
        list: A list of ticker symbols paired with USDT.
    """
    tickers = []
    resp = client.ticker_price()
    for elem in resp:
        if 'USDT' in elem['symbol']:
            tickers.append(elem['symbol'])
    return tickers


# Getting candles for the needed symbol, its a dataframe with 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'
def klines(symbol):
    """
    Fetches kline data for a given symbol from the Binance Futures API.

    Args:
        symbol (str): The trading symbol for which to fetch the kline data.

    Returns:
        pandas.DataFrame: A DataFrame containing the kline data with columns:
            - Time: The timestamp of the kline.
            - Open: The opening price of the kline.
            - High: The highest price reached during the kline.
            - Low: The lowest price reached during the kline.
            - Close: The closing price of the kline.
            - Volume: The trading volume during the kline.

    Raises:
        ClientError: If there is an error while fetching the kline data from the API.
    """
    try:
        resp = pd.DataFrame(client.klines(symbol, '15m'))
        resp = resp.iloc[:,:6]
        resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        resp = resp.set_index('Time')
        resp.index = pd.to_datetime(resp.index, unit = 'ms')
        resp = resp.astype(float)
        return resp
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Set leverage for the needed symbol. You need this bcz different symbols can have different leverage
def set_leverage(symbol, level):
    """
    Sets the leverage level for a given symbol.

    Args:
        symbol (str): The trading symbol.
        level (int): The leverage level to set.

    Returns:
        None

    Raises:
        ClientError: If an error occurs while changing the leverage.

    """
    try:
        response = client.change_leverage(
            symbol=symbol, leverage=level, recvWindow=6000
        )
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# The same for the margin type
def set_mode(symbol, type):
    """
    Sets the margin type for a given symbol.

    Args:
        symbol (str): The trading symbol.
        type (str): The margin type to set.

    Returns:
        None

    Raises:
        ClientError: If an error occurs while changing the margin type.

    """
    try:
        response = client.change_margin_type(
            symbol=symbol, marginType=type, recvWindow=6000
        )
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Price precision. BTC has 1, XRP has 4
def get_price_precision(symbol):
    """
    Get the price precision for a given symbol.

    Parameters:
    symbol (str): The symbol for which to retrieve the price precision.

    Returns:
    int: The price precision for the given symbol.

    """
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['pricePrecision']


# Amount precision. BTC has 3, XRP has 1
def get_qty_precision(symbol):
    """
    Get the quantity precision for a given symbol.

    Parameters:
    symbol (str): The symbol for which to retrieve the quantity precision.

    Returns:
    int: The quantity precision for the given symbol.
    """
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['quantityPrecision']


# Open new order with the last price, and set TP and SL:
def open_order(symbol, side):
    """
    Opens a new order for the specified symbol and side.

    Args:
        symbol (str): The trading symbol for the order.
        side (str): The side of the order, either 'buy' or 'sell'.

    Returns:
        None

    Raises:
        ClientError: If an error occurs while placing the order.

    """
    price = float(client.ticker_price(symbol)['price'])
    qty_precision = get_qty_precision(symbol)
    price_precision = get_price_precision(symbol)
    qty = round(volume/price, qty_precision)
    if side == 'buy':
        try:
            resp1 = client.new_order(symbol=symbol, side='BUY', type='LIMIT', quantity=qty, timeInForce='GTC', price=price)
            print(symbol, side, "placing order")
            print(resp1)
            sleep(2)
            sl_price = round(price - price*sl, price_precision)
            resp2 = client.new_order(symbol=symbol, side='SELL', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price)
            print(resp2)
            sleep(2)
            tp_price = round(price + price * tp, price_precision)
            resp3 = client.new_order(symbol=symbol, side='SELL', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                                     stopPrice=tp_price)
            print(resp3)
        except ClientError as error:
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
    if side == 'sell':
        try:
            resp1 = client.new_order(symbol=symbol, side='SELL', type='LIMIT', quantity=qty, timeInForce='GTC', price=price)
            print(symbol, side, "placing order")
            print(resp1)
            sleep(2)
            sl_price = round(price + price*sl, price_precision)
            resp2 = client.new_order(symbol=symbol, side='BUY', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price)
            print(resp2)
            sleep(2)
            tp_price = round(price - price * tp, price_precision)
            resp3 = client.new_order(symbol=symbol, side='BUY', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                                     stopPrice=tp_price)
            print(resp3)
        except ClientError as error:
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )


# Your current positions (returns the symbols list):
def get_pos():
    """
    Retrieves the symbols of positions with non-zero position amounts.

    Returns:
        list: A list of symbols representing positions with non-zero position amounts.
    """
    try:
        resp = client.get_position_risk()
        pos = []
        for elem in resp:
            if float(elem['positionAmt']) != 0:
                pos.append(elem['symbol'])
        return pos
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def check_orders():
    """
    Retrieves the symbols of all orders using the Binance Futures API.

    Returns:
        list: A list of symbols of all orders.

    Raises:
        ClientError: If there is an error while retrieving the orders.
    """
    try:
        response = client.get_orders(recvWindow=6000)
        sym = []
        for elem in response:
            sym.append(elem['symbol'])
        return sym
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

# Close open orders for the needed symbol. If one stop order is executed and another one is still there
def close_open_orders(symbol):
    """
    Cancel all open orders for a given symbol.

    Parameters:
    - symbol (str): The trading symbol for which to cancel open orders.

    Returns:
    - None

    Raises:
    - ClientError: If there is an error while canceling open orders.

    """
    try:
        response = client.cancel_open_orders(symbol=symbol, recvWindow=6000)
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Strategy. Can use any other:
def str_signal(symbol):
    """
    Determines the trading signal based on the given symbol.

    Parameters:
    symbol (str): The symbol for which the trading signal is to be determined.

    Returns:
    str: The trading signal, which can be 'up', 'down', or 'none'.
    """
    kl = klines(symbol)
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    rsi_k = ta.momentum.StochRSIIndicator(kl.Close).stochrsi_k()
    rsi_d = ta.momentum.StochRSIIndicator(kl.Close).stochrsi_d()
    ema = ta.trend.ema_indicator(kl.Close, window=200)
    if rsi.iloc[-1] < 40 and ema.iloc[-1] < kl.Close.iloc[-1] and rsi_k.iloc[-1] < 20 and rsi_k.iloc[-3] < rsi_d.iloc[-3] and rsi_k.iloc[-2] < rsi_d.iloc[-2] and rsi_k.iloc[-1] > rsi_d.iloc[-1]:
        return 'up'
    if rsi.iloc[-1] > 60 and ema.iloc[-1] > kl.Close.iloc[-1] and rsi_k.iloc[-1] > 80 and rsi_k.iloc[-3] > rsi_d.iloc[-3] and rsi_k.iloc[-2] > rsi_d.iloc[-2] and rsi_k.iloc[-1] < rsi_d.iloc[-1]:
        return 'down'

    else:
        return 'none'


def rsi_signal(symbol):
    """
    Calculates the RSI signal for a given symbol.

    Parameters:
    symbol (str): The symbol for which to calculate the RSI signal.

    Returns:
    str: The RSI signal, which can be 'up', 'down', or 'none'.
    """
    kl = klines(symbol)
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    ema = ta.trend.ema_indicator(kl.Close, window=200)
    if rsi.iloc[-2] < 30 and rsi.iloc[-1] > 30:
        return 'up'
    if rsi.iloc[-2] > 70 and rsi.iloc[-1] < 70:
        return 'down'
    else:
        return 'none'


def macd_ema(symbol):
    """
    Calculates the MACD (Moving Average Convergence Divergence) and EMA (Exponential Moving Average) indicators for a given symbol.

    Parameters:
    symbol (str): The symbol for which to calculate the indicators.

    Returns:
    str: The signal indicating the trend based on the MACD and EMA indicators. Possible values are 'up', 'down', or 'none'.
    """
    kl = klines(symbol)
    macd = ta.trend.macd_diff(kl.Close)
    ema = ta.trend.ema_indicator(kl.Close, window=200)
    if macd.iloc[-3] < 0 and macd.iloc[-2] < 0 and macd.iloc[-1] > 0 and ema.iloc[-1] < kl.Close.iloc[-1]:
        return 'up'
    if macd.iloc[-3] > 0 and macd.iloc[-2] > 0 and macd.iloc[-1] < 0 and ema.iloc[-1] > kl.Close.iloc[-1]:
        return 'down'
    else:
        return 'none'


def ema200_50(symbol):
    """
    Calculates the EMA (Exponential Moving Average) for a given symbol and determines the trend based on the relationship between the EMA200 and EMA50.

    Parameters:
    - symbol (str): The symbol for which the EMA is calculated.

    Returns:
    - str: The trend based on the relationship between EMA200 and EMA50. Possible values are 'up', 'down', or 'none'.
    """
    kl = klines(symbol)
    ema200 = ta.trend.ema_indicator(kl.Close, window=100)
    ema50 = ta.trend.ema_indicator(kl.Close, window=50)
    if ema50.iloc[-3] < ema200.iloc[-3] and ema50.iloc[-2] < ema200.iloc[-2] and ema50.iloc[-1] > ema200.iloc[-1]:
        return 'up'
    if ema50.iloc[-3] > ema200.iloc[-3] and ema50.iloc[-2] > ema200.iloc[-2] and ema50.iloc[-1] < ema200.iloc[-1]:
        return 'down'
    else:
        return 'none'


orders = 0
symbol = ''
# getting all symbols from Binace Futures list:
symbols = get_tickers_usdt()

while True:
    # we need to get balance to check if the connection is good, or you have all the needed permissions
    balance = get_balance_usdt()
    sleep(1)
    if balance == None:
        print('Cant connect to API. Check IP, restrictions or wait some time')
    if balance != None:
        print("My balance is: ", balance, " USDT")
        # getting position list:
        pos = []
        pos = get_pos()
        print(f'You have {len(pos)} opened positions:\n{pos}')
        # Getting order list
        ord = []
        ord = check_orders()
        # removing stop orders for closed positions
        for elem in ord:
            if not elem in pos:
                close_open_orders(elem)

        if len(pos) < qty:
            for elem in symbols:
                # Strategies (you can make your own with the TA library):

                # signal = str_signal(elem)
                signal = rsi_signal(elem)
                # signal = macd_ema(elem)

                # 'up' or 'down' signal, we place orders for symbols that arent in the opened positions and orders
                # we also dont need USDTUSDC because its 1:1 (dont need to spend money for the commission)
                if signal == 'up' and elem != 'USDCUSDT' and not elem in pos and not elem in ord and elem != symbol:
                    print('Found BUY signal for ', elem)
                    set_mode(elem, type)
                    sleep(1)
                    set_leverage(elem, leverage)
                    sleep(1)
                    print('Placing order for ', elem)
                    open_order(elem, 'buy')
                    symbol = elem
                    order = True
                    pos = get_pos()
                    sleep(1)
                    ord = check_orders()
                    sleep(1)
                    sleep(10)
                    # break
                if signal == 'down' and elem != 'USDCUSDT' and not elem in pos and not elem in ord and elem != symbol:
                    print('Found SELL signal for ', elem)
                    set_mode(elem, type)
                    sleep(1)
                    set_leverage(elem, leverage)
                    sleep(1)
                    print('Placing order for ', elem)
                    open_order(elem, 'sell')
                    symbol = elem
                    order = True
                    pos = get_pos()
                    sleep(1)
                    ord = check_orders()
                    sleep(1)
                    sleep(10)
                    # break
    print('Waiting 3 min')
    sleep(180)



