import Trader
from datetime import datetime, timedelta
import os
import threading
from time import time, sleep

symbol= 'ETHUSD'
timeframe= 'M30' 
bars_window = 26
std_n = 2 
position_size = 100

trd = Trader.Trader()
    
status = threading.Event()
status.set()

def boll_bands():
    print('Starting Bollinger Bands...')
    print(f'Parameters: asset = {symbol}, timeframe = {timeframe}, size = {position_size} periods = {bars_window}, std deviation = {std_n}')
    close= 0 
    down_band= 0
    up_band= 0

    while status.is_set():
        df_data= trd.get_ohlc_pos(symbol, timeframe, initial_pos= 0, number_bars= bars_window + 10 )    # Gathers data

        # Indicator calculation
        df_data['roll_close_mean']= df_data['close'].rolling(bars_window).mean()   # Mean close price of past candlesticks
        df_data['roll_close_std']= df_data['close'].rolling(bars_window).std()     # Std of close price of past candles

        # Bollinger Bands
        df_data['up_band']= df_data['roll_close_mean'] + std_n*df_data['roll_close_std']
        df_data['down_band']= df_data['roll_close_mean'] - std_n*df_data['roll_close_std']

        trd.check_pos_orders()

        # Printing Data
        if df_data["close"].iloc[-2] != close or down_band != df_data["down_band"].iloc[-2] or df_data["up_band"].iloc[-2] != up_band:
            close= df_data['close'].iloc[-2]
            up_band= df_data['up_band'].iloc[-2]
            down_band= df_data['down_band'].iloc[-2]
            position = trd.positions
            print(f'{datetime.now()} - Last Close: {close:.2f} | Up: {up_band:.2f} | Down: {down_band:.2f} | Position: {position}')
        
        #Checking position and trading
        if len(trd.positions) == 0:
            c1 = close < down_band
            if c1:
                print('Opening Position...')
                trd.send_market(symbol, 'buy', position_size, comment= 'Open')
        else:
            if close > up_band:
                print('Closing Position')
                trd.send_market(symbol, 'sell', position_size, comment= 'Close')
        sleep(1)

    if len(trd.positions) > 0:
        print('Closing remaining positions...')
        trd.send_market(symbol, 'sell', position_size, comment= 'Close')
    print('Done.')

        


# Loop
while True:
    if not status.is_set():
        os.system("cls")
    print('-----------------------------------------')
    print('0: Exit, 1: Start Bollinger Bands, 2: Stop Bollinger Bands')
    print('-----------------------------------------')

    inp = int(input())
    if inp== 0:
        print('Closing')
        break

    elif inp== 1:
        t1= threading.Thread(target=boll_bands)
        t1.start()

    elif inp== 2:
        print('Stopping')
        status.clear()