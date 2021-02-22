import time
import queue
import requests
import threading

import cbpro
import pandas as pd

import plots as pl
import data_tools as dt

from blessed import Terminal
term = Terminal()


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
                 frequency=None, event=None):
        self.thread = None
        self.event = event
        self.frequency = frequency  # in secs
        self.was_joined = False
        self.currency = currency
        self.out_queue = queue.Queue()
        self.public_client = public_client

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
        print(term.home + term.clear)
        if not self.was_joined:
            try:
                self.thread.join()
            except Exception as e:
                raise RuntimeError(f"Current trends process failed. Message: {e}")

    @classmethod
    def get_trends(cls, currency, out_queue=None, frequency=None, event=None):
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
            width, height = pl.Plotter.plot(
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

        _get_trends()
        if frequency and event:
            initial_time = time.time()
            while event.is_set():
                if time.time() - initial_time > frequency:
                    _get_trends()
                    initial_time = time.time()
                time.sleep(.1)


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
                print(term.home + term.clear)
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
                        print(
                            term.move_xy(self.term_x_pos, self.term_y_pos) +
                            f'>>> Current {currency} price: '
                            f'${float(ws_client.message["price"]):,}\r',
                            end=""
                        )
                    time.sleep(1)
                ws_client.close()
            except Exception as e:
                raise RuntimeError(e)
            finally:
                event.clear()
