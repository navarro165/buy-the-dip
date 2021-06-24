import cbpro
import configparser

config = configparser.ConfigParser()
has_config_file = config.read('config.ini')

if not has_config_file:
    raise EnvironmentError('Config file is missing')

if 'ACCOUNT' not in config.sections():
    raise EnvironmentError(
        'Account details are missing, please configure "config.ini"')

KEY = config['ACCOUNT'].get('key')
SECRET = config['ACCOUNT'].get('secret')
PASSPHRASE = config['ACCOUNT'].get('passphrase')

if not all([KEY, SECRET, PASSPHRASE]):
    raise EnvironmentError(
        'Missing one of the following: '
        'KEY, SECRET, PASSPHRASE in the config.ini')


class Coinbase:

    def __init__(self, coin):
        self.coin = coin
        self.auth_client = cbpro.AuthenticatedClient(KEY, SECRET, PASSPHRASE)

    def get_accounts(self):
        return {_['currency']: _ for _ in self.auth_client.get_accounts()}

    @property
    def accounts(self):
        return self.get_accounts()

    @property
    def current_account(self):
        current_account = {
            **self.accounts[self.coin],
            'usd': self.accounts['USD']
        }
        return current_account

    @property
    def usd_balance(self):
        return round(float(self.current_account['usd']['balance']), 2)

    @property
    def is_coin_enabled(self):
        return self.current_account['trading_enabled']

    def buy(self, funds=5):
        has_valid_funds_size = self.is_coin_enabled \
                               and self.usd_balance > funds > 5

        if not has_valid_funds_size:
            return "Verify Coin is enabled for trading, purchase above $5, " \
                   "and enough balance is available to trade."

        response = self.auth_client.place_market_order(
            product_id=f'{self.coin}-USD',
            side='buy',
            funds=funds
        )
        if 'message' in response:
            return response['message']


if __name__ == '__main__':
    client = Coinbase('BTC')
    print(client.usd_balance)
    print(client.buy())
    print(client.usd_balance)
