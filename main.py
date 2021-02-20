import gc
import sys
import time
import threading

import click
import cbpro
from blessings import Terminal

import plotext as plt
import exchanges as ex
import components as cp


@click.command()
@click.option('--currency', prompt='Enter a crypto', help='"BTC-USD", "ETH-USD", etc')
def run(currency="btc-usd"):
    currency = currency.strip().upper()
    term = Terminal()

    plt.clp()
    plt.clt()
    with term.fullscreen():
        with cp.CurrentTrends(currency) as current_trends:
            width, height = current_trends.join()
            time.sleep(5)

        run_event = threading.Event()
        run_event.set()
        with cp.CurrentTrends(currency, poll_frequency=60, run_event=run_event) as current_trends:
            try:
                while True:
                    time.sleep(.1)
            except KeyboardInterrupt:
                run_event.clear()
                current_trends.join()
        time.sleep(5)

        # public_client = cbpro.PublicClient()
        # with term.location(0, height + 2):
        #     exchange = ex.Coinbase(currency)
        #     current_price_gen = exchange.get_current_price()
        #     for current_price in next(current_price_gen):
        #         print(f'>>> Current {currency} price: {current_price}\r', end="")
        #         time.sleep(1)


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        raise RuntimeError(e)
    finally:
        gc.collect()
        sys.exit()

"""
https://stackoverflow.com/questions/11436502/closing-all-threads-with-a-keyboard-interrupt
https://docs.pro.coinbase.com/
https://github.com/danpaquin/coinbasepro-python
https://github.com/pallets/click
https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python
https://github.com/erikrose/blessings
"""
