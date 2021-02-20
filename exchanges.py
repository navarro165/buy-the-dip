import gc
import sys
import time
import json
import requests
import pandas as pd

import cbpro

import plots as pl
import data_tools as dt


class MyWebsocketClient(cbpro.WebsocketClient):
    def __init__(self, currency="BTC-USD", channels="ticker"):
        super().__init__(currency, channels)
        self.ws_url = "wss://ws-feed.pro.coinbase.com"
        self.products = currency
        self.channels = channels
        self.should_print = False
        self.current_price = None

    def __enter__(self):
        self.start()
        return self

    def on_message(self, msg):
        self.current_price = msg

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()


class Coinbase:

    def __init__(self, public_client, currency="BTC-USD", frequency=60, channels=None):
        # self.socket_url = SOCKET_URL
        self.currency = currency
        self.channels = ["ticker"] if not channels else channels
        self.frequency = frequency

    def get_current_price(self):
        with MyWebsocketClient(self.currency, self.channels) as ws_client:
            try:
                while True:
                    current_price = ws_client.current_price
                    if current_price:
                        yield current_price.get("price")
                    time.sleep(1)
            except KeyboardInterrupt:
                ws_client.close()

            if ws_client.error:
                sys.exit(1)
            else:
                sys.exit(0)

    @classmethod
    def get_trends(cls, currency, out_queue=None, poll_frequency=None, run_event=None):
        def _get_trends():
            response = requests.request("GET",
                                        f"https://api.pro.coinbase.com/products/{currency}/candles",
                                        headers={'Cache-Control': 'no-cache', "Pragma": "no-cache"},
                                        data={'granularity': 60},
                                        timeout=5)

            if response.status_code != 200:
                raise ConnectionError("request failed")

            historic_rates = response.json()
            historic_rates_df = pd.DataFrame(historic_rates,
                                             columns=['time', 'low', 'high', 'open', 'close', 'volume'])
            historic_rates_df.drop(['time', 'low', 'high', 'open', 'volume'], axis=1, inplace=True)
            historic_rates_df = historic_rates_df.iloc[::-1]  # invert row order
            historic_rates_df.reset_index(inplace=True)
            minute_mark, closing_price = historic_rates_df.index, historic_rates_df.close

            lowess_df = dt.Lowess.get_lowess_trend(x=minute_mark, y=closing_price)
            lowess_trendlines = dt.Lowess.get_lowess_trendlines(lowess_df)
            width, height = pl.Plotter.plot(x=minute_mark, y=closing_price, trendlines=lowess_trendlines,
                                            title=currency, xaxis_title="minutes", yaxis_title="price",
                                            _type="terminal")

            if out_queue:
                out_queue.put((width, height))

        _get_trends()
        if poll_frequency and run_event:
            initial_time = time.time()
            while run_event.is_set():
                if time.time() - initial_time > poll_frequency:
                    _get_trends()
                    initial_time = time.time()
                time.sleep(.1)
