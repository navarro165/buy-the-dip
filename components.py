import time
import queue
import requests
import threading

import cbpro
import pandas as pd

import plots as pl
import utils as ut
import client as cl
import data_tools as dt


class MyWebsocketClient(cbpro.WebsocketClient):
    def __init__(self, currency, channels="ticker"):
        super().__init__(products=currency, channels=[channels])
        self.should_print = False
        self.message = None

    def __enter__(self):
        self.start()
        return self

    def on_message(self, msg):
        self.message = msg

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()


class Trends:
    def __init__(self, currency, public_client=None,
                 frequency=60, event=None, buy_the_dip=False, buy_obj=None):
        self.thread = None
        self.event = event
        self.frequency = frequency  # in secs
        self.was_joined = False
        self.currency = currency
        self.buy_the_dip = buy_the_dip
        self.buy_obj = buy_obj
        self.out_queue = queue.Queue()
        self.public_client = public_client

        if self.buy_obj.frequency:
            self.frequency = int(self.frequency *buy_obj.frequency)

    def __enter__(self):
        thread_args = {
            'target': self.get_trends,
            'args': (self.currency, self.out_queue),
            'kwargs': {
                "frequency": self.frequency,
                "event": self.event
            }
        }
        self.thread = threading.Thread(**thread_args)
        self.thread.daemon = True
        self.thread.start()
        return self

    def join(self):
        self.thread.join()
        self.was_joined = True
        return self.out_queue.get()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        print(ut.term.home + ut.term.clear)
        if not self.was_joined:
            try:
                self.thread.join()
            except Exception as e:
                raise RuntimeError(f"Current trends process failed. Message: {e}")

    def get_trends(self, currency, out_queue=None, frequency=None, event=None):
        def _get_trends():
            response = requests.request(
                "GET",
                f"https://api.pro.coinbase.com/products/{currency}/candles",
                headers={'Cache-Control': 'no-cache', "Pragma": "no-cache"},
                data={'granularity': 60},
                timeout=5
            )
            if response.status_code != 200:
                raise ConnectionError("request failed")

            historic_rates = response.json()
            historic_rates_df = pd.DataFrame(
                historic_rates,
                columns=['time', 'low', 'high', 'open', 'close', 'volume']
            )
            historic_rates_df.drop(
                ['time', 'low', 'high', 'open', 'volume'],
                axis=1, inplace=True
            )
            historic_rates_df = historic_rates_df.iloc[::-1]  # invert row order
            historic_rates_df.reset_index(inplace=True)

            minute_mark = historic_rates_df.index
            closing_price = historic_rates_df.close

            lowess_df = dt.Lowess.get_lowess_trend(
                x=minute_mark,
                y=closing_price
            )
            lowess_trendlines = dt.Lowess.get_lowess_trendlines(lowess_df)
            width, height, last_sign, last_change = pl.Plotter.plot(
                x=minute_mark,
                y=closing_price,
                trendlines=lowess_trendlines,
                title=currency,
                xaxis_title="minutes",
                yaxis_title="price",
                _type="terminal"
            )
            if out_queue:
                out_queue.put((width, height))

            return width, height, last_sign, last_change

        _, height, last_sign, last_change = _get_trends()
        if self.buy_the_dip:
            ut.Messages.next_purchase(height, self.frequency)

        if frequency and event:
            counter = 0
            mins_elapsed = 0
            initial_time = time.time()

            client = cl.Coinbase(self.currency.replace('-USD', ""))
            available_balance = client.usd_balance

            while event.is_set():
                if time.time() - initial_time > frequency:
                    _get_trends()

                    if self.buy_the_dip and mins_elapsed % self.buy_obj.frequency == 0:
                        counter = 0
                        if last_sign == '-':
                            response = client.buy(self.buy_obj.amount)
                            available_balance = client.usd_balance
                            ut.Messages.buy(height, response)
                        else:
                            ut.Messages.not_dipping(height)

                    initial_time = time.time()
                    mins_elapsed += 1

                time.sleep(1)
                counter += 1

                if self.buy_the_dip:
                    ut.Messages.next_purchase(height, self.frequency - counter)
                    ut.Messages.available_balance(height, available_balance)


class CurrentPrice:
    def __init__(self, currency, event, term_x_pos=0, term_y_pos=0):
        self.thread = None
        self.event = event
        self.was_joined = False
        self.currency = currency
        self.term_x_pos = term_x_pos
        self.term_y_pos = term_y_pos

    def __enter__(self):
        thread_args = {
            'target': self.get_current_price,
            'kwargs': {
                'currency': self.currency,
                "event": self.event
            }
        }
        self.thread = threading.Thread(**thread_args)
        self.thread.daemon = True
        self.thread.start()
        return self

    def join(self):
        self.thread.join()
        self.was_joined = True

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self.was_joined:
            try:
                self.thread.join()
                print(ut.term.home + ut.term.clear)
            except Exception as e:
                raise RuntimeError(f"Current trends process failed. Message: {e}")

    def get_current_price(self, currency, event):
        with MyWebsocketClient(currency) as ws_client:
            try:
                while event.is_set():
                    if ws_client.error:
                        print("socket error")  # TODO: add logs
                        break

                    if ws_client.message:
                        price = f'{float(ws_client.message["price"]):,}'
                        ut.Messages.current_price(self.term_y_pos, currency, price)

                    time.sleep(1)
                ws_client.close()

            except Exception as e:
                raise RuntimeError(e)
            finally:
                event.clear()
