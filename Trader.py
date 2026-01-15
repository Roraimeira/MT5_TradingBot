import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

class Trader:
    def __init__(self):
        if not mt5.initialize():                                            # check if mt5 is open
            print('Failed to start. Error code = ', mt5.last_error())       # prints error, if needed
            mt5.shutdown()                                                  # if not open, stops

        print('Updating balance and positions...')
        self.positions = [i._asdict() for i in mt5.positions_get()]                         # gets open positions
        self.orders = [i._asdict() for i in mt5.orders_get()]                               # gets open orders
        self.h_orders = [i._asdict() for i in mt5.history_orders_get(0, datetime.now())]    # gets orders history
        self.h_deals = [i._asdict() for i in mt5.history_deals_get(0, datetime.now())]      # gets deals history
        print('Ready to trade.')

        self.tf_dict = {                         # timeframe dict
                'M1': [mt5.TIMEFRAME_M1, 60],
                'M2': [mt5.TIMEFRAME_M2, 120],
                'M3': [mt5.TIMEFRAME_M3, 180],
                'M4': [mt5.TIMEFRAME_M4, 240],
                'M5': [mt5.TIMEFRAME_M5, 300],
                'M6': [mt5.TIMEFRAME_M6, 360],
                'M10': [mt5.TIMEFRAME_M10, 600],
                'M12': [mt5.TIMEFRAME_M12, 720],
                'M15': [mt5.TIMEFRAME_M15, 900],
                'M20': [mt5.TIMEFRAME_M20, 1200],
                'M30': [mt5.TIMEFRAME_M30, 1800],
                'H1': [mt5.TIMEFRAME_H1, 3600],
                'H2': [mt5.TIMEFRAME_H2, 7200],
                'H3': [mt5.TIMEFRAME_H3, 10800],
                'H4': [mt5.TIMEFRAME_H4, 14400],
                'H6': [mt5.TIMEFRAME_H6, 21600],
                'H8': [mt5.TIMEFRAME_H8, 28800],
                'H12': [mt5.TIMEFRAME_H12, 43200],
                'D1': [mt5.TIMEFRAME_D1, 86400],
                'W1': [mt5.TIMEFRAME_W1, 604800],
                'MN1': [mt5.TIMEFRAME_MN1, 2592000],
    }


    # Positions and Orders
    def check_pos_orders(self):
        new_positions = [i._asdict() for i in mt5.positions_get()]                          # updates open positions
        new_orders = [i._asdict() for i in mt5.orders_get()]                                 # updates open orders
        check = (self.positions == new_positions) or (self.orders == new_orders)             # check if there is an update
        self.positions = new_positions
        self.orders = new_orders
        return check

    def check_orders_deals_hist(self, start_date= 0, end_date= datetime.now()):
        new_orders_hist = [i._asdict() for i in mt5.history_orders_get(start_date, end_date)]   # updates orders history
        new_deals_hist = [i._asdict() for i in mt5.history_deals_get(start_date, end_date)]     # updates deals history
        check = (self.h_orders != new_orders_hist) or (self.h_deals != new_deals_hist)          # check if there is an update
        return check

    # Getting Market Data
    def get_ohlc_range(self, symbol, timeframe, start_date, end_date=datetime.now()):   
        tf = self.tf_dict[timeframe][0]
        data_raw = mt5.copy_rates_range(symbol, tf, start_date, end_date)                       # gets asset data from metatrader
        df_data = self._format_ohlc(data_raw)                                                   # manipulates and transform to DF
        return df_data
        
    def get_ohlc_pos(self, symbol, timeframe, initial_pos, number_bars):
        tf = self.tf_dict[timeframe][0]
        data_raw = mt5.copy_rates_from_pos(symbol, tf, initial_pos, number_bars)                # gets asset data from metatrader
        df_data = self._format_ohlc(data_raw)                                                   # manipulates and transform to DF
        return df_data
    
    def _format_ohlc(self, data_raw):                                                           # format data_raw to DF
        if data_raw is None or len(data_raw) == 0:
            return
        df_data = pd.DataFrame(data_raw)
        df_data['time'] = pd.to_datetime(df_data['time'], unit = 's')
        df_data.set_index(df_data['time'], drop= True, inplace= True)                           # makes time the index and drops time column
        return df_data

    # Order Management
    def send_market(self, symbol, side, volume, deviation= 20, magic= 1, comment= 'test'):
        mt5.symbol_select(symbol, True)
        symbol_info = mt5.symbol_info(symbol)
        volume = float(volume)                                                                  # MT5 needs this value to be float
        action = ''

        if side == 'buy':
            side = mt5.ORDER_TYPE_BUY
            action = 'long'
        elif side == 'sell':
            side = mt5.ORDER_TYPE_SELL
            action = 'short'
        else:
            print('Side not defined. Unable to send order.')

        if symbol_info.visible:
            request = {
                "action": mt5.TRADE_ACTION_DEAL, 
                "symbol": symbol,
                "volume": volume,
                "type": side,
                "price": symbol_info.bid,
                "deviation": deviation,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            print(f'{symbol}, {action} market order of volume {volume} sent')
            return mt5.order_send(request)

        else:
            print(f'{symbol} not visible. Unable to send order.')

    def send_limit(self, symbol, side, price, volume, magic= 1, comment= 'test'):
        mt5.symbol_select(symbol, True)
        symbol_info = mt5.symbol_info(symbol)
        price = float(price); volume = float(volume)                                        # MT5 needs these values to be float
        action = ''

        if side == 'buy':
            side = mt5.ORDER_TYPE_BUY_LIMIT
            action = 'long'
        elif side == 'sell':
            side = mt5.ORDER_TYPE_SELL_LIMIT
            action = 'short'
        else:
            print('Side not defined. Unable to send order.')

        if symbol_info.visible:
            request = {
                "action": mt5.TRADE_ACTION_PENDING, 
                "symbol": symbol,
                "volume": volume,
                "type": side,
                "price": price,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            print(f'{symbol}, {action} limit order of volume {volume} sent')
            return mt5.order_send(request)
        else:
            print(f'{symbol} not visible. Unable to send order')

    def update_limit(self, order, price):
        price = float(price)                                                 # MT5 needs this value to be float     
        request = {
            'action': mt5.TRADE_ACTION_MODIFY,
            'order': order,
            'price': price,
        }
        return mt5.order_send(request)
    
    def cancel_limit(self, order):
        request = {
            'action': mt5.TRADE_ACTION_REMOVE,
            'order': order,
        }
        return mt5.order_send(request)



# quick test
if __name__ == '__main__':
    self = Trader()

    symbol = 'ETHUSD'
    tf = 'M30'
    volume = 1
    start_date = datetime(2025, 1, 30)
    end_date = datetime.today()
    side = 'buy' 
    price = 91000



    #data_range = self.get_ohlc_range(symbol, tf, start_date, end_date)
    data_pos = self.get_ohlc_pos(symbol, tf, initial_pos= 100, number_bars= 1000)

    #self.send_market(symbol, side, volume)
    #self.send_limit(symbol, side, price, volume)
    #self.update_limit(212661544, price)
    #self.cancel_limit(212661544)
    
    #self.check_pos_orders()
    #self.check_orders_deals_hist()
    
