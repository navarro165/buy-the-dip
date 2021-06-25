import sys
import time
import threading

import click

import utils as ut
import components as cp


@click.command()
@click.option('--currency',
              prompt='Enter a crypto',
              help='"BTC", "ETH", etc')
@click.option('--buy_the_dip',
              prompt='***COINBASE PRO CONFIG REQUIRED*** -- buy the dip (y/n)?',
              help='"Coinbase Pro account config setup needed')
def run(currency, buy_the_dip):

    if buy_the_dip in ['y', 'Y']:
        buy_the_dip = True
    elif buy_the_dip in ['n', 'N']:
        buy_the_dip = False
    else:
        raise ValueError('Param "buy_the_dip" can be either "n" or "y')

    currency = currency.strip().upper() + '-USD'
    buy_obj = type('buy_obj', (object,), {'frequency': None, 'amount': None})

    if buy_the_dip:
        frequency = float(input('\nHow often do you want to buy (in minutes)? '))
        amount = float(input('Enter recurring purchase amount (min=$5): '))

        if frequency < 1 or amount < 5:
            raise ValueError("Please select valid purchase frequency and amount")

        buy_obj.amount = amount
        buy_obj.frequency = frequency

    with cp.Trends(currency, buy_the_dip=buy_the_dip, buy_obj=buy_obj) as trends:
        width, height = trends.join()

    event = threading.Event()
    event.set()
    with cp.Trends(currency, event=event, buy_the_dip=buy_the_dip, buy_obj=buy_obj) as trends:
        with cp.CurrentPrice(currency, event,
                             term_x_pos=0,
                             term_y_pos=height) as cur_price:
            try:
                while True:
                    time.sleep(.1)
            except KeyboardInterrupt:
                event.clear()
                trends.join()
                cur_price.join()


if __name__ == '__main__':
    with ut.term.fullscreen():
        try:
            run()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            sys.exit(e)
        else:
            sys.exit()
