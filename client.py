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


if __name__ == '__main__':
    import pprint

    client = Coinbase('BTC')
    pprint.pprint(client.current_account)
