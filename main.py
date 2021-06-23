import sys
import time
import threading

import click
from blessed import Terminal

import components as cp
import client as cl


term = Terminal()


@click.command()
@click.option('--currency',
              prompt='Enter a crypto',
              help='"BTC", "ETH", etc')
@click.option('--buy_the_dip',
              prompt='***COINBASE PRO CONFIG REQUIRED*** -- buy the dip (y/n)?',
              help='"Coinbase Pro account config setup needed')
def run(currency, buy_the_dip):
    currency = currency.strip().upper()

    if buy_the_dip:
        auth_client = cl.Coinbase(currency)

    currency += '-USD'

    with cp.Trends(currency) as trends:
        width, height = trends.join()

    event = threading.Event()
    event.set()
    with cp.Trends(currency, frequency=60, event=event) as trends:
        with cp.CurrentPrice(currency, event,
                             term_x_pos=0,
                             term_y_pos=1+height) as cur_price:
            try:
                while True:
                    time.sleep(.1)
            except KeyboardInterrupt:
                event.clear()
                trends.join()
                cur_price.join()


if __name__ == '__main__':
    with term.fullscreen():
        try:
            run()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            sys.exit(e)
        else:
            sys.exit()
