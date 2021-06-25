import datetime

from blessed import Terminal
term = Terminal()


def print_to_terminal(x, y, message, end='\n'):
    print(term.move_xy(x, y) + message, end=end)


def current_time():
    now = datetime.datetime.now()
    return now.strftime('%H:%M:%S')


class Messages:

    @classmethod
    def current_price(cls, height, currency, price):
        print_to_terminal(
            x=0, y=height+1,
            message=f'> Current {currency} price: ${price}   \r',
            end=""
        )

    @classmethod
    def next_purchase(cls, height, frequency):
        print_to_terminal(
            x=0, y=height + 3,
            message=f'> Next purchase attempt in {frequency} (s)   \r',
            end=""
        )

    @classmethod
    def available_balance(cls, height, available_balance):
        print_to_terminal(
            x=0, y=height + 5,
            message=f'> Available USD balance: $ {available_balance}.  \r',
            end=""
        )

    @classmethod
    def buy(cls, height, response):
        if not response:
            message = f"Last purchase made at {current_time()}"
        else:
            message = f"Purchase failed: '{response}'"

        print_to_terminal(
            x=0, y=height + 7,
            message=f'*** {message}   \r',
            end=""
        )

    @classmethod
    def not_dipping(cls, height):
        print_to_terminal(
            x=0, y=height + 7,
            message=f'*** Waiting for dip to start buying!    \r',
            end=""
        )
