import os, sys, argparse

from typing import List
from pathlib import Path
from configparser import ConfigParser
from collections import namedtuple


PROJ_ROOT = Path(__file__).parent


def settings_setup():
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15 (KHTML, like Gecko)',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
    ]
    PROXIES = []
    DB = {}

    Settings = namedtuple('Settings', 'DB PROXIES OVERWRITE DEBUG USER_AGENTS')

    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('-c', '--config', type=str, help='Configuration file (only .ini format accept).', default='config.ini')
    cli_parser.add_argument('-p', '--proxies', nargs='+', type=str, help='Use proxies ("host:port").', default=[])
    cli_parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite database with new data.')
    cli_parser.add_argument('-d', '--debug', action='store_true', help='Debug mode.')
    cli_parser.add_argument('-db', '--database', type=str, help='SQLite database file.', default='parser.db')

    cli_args = vars(cli_parser.parse_args())
    config_file = PROJ_ROOT/cli_args['config']

    if config_file.exists():
        config_parser = ConfigParser()
        config_parser.read(config_file)

        if 'proxies' in config_parser.sections() and not cli_args['proxies']:
            PROXIES = [f'{host}:{port}' for host, port in config_parser.items('proxies')]

        if 'database' in config_parser.sections():
            DB = dict(config_parser.items('database'))
    else:
        sys.stdout.write(f'Config file {config_file} does not exist, take default args.\n')
    
    DB['name'] = cli_args['database']
    
    settings = Settings(
        DB=DB,
        PROXIES=cli_args['proxies'] or PROXIES,
        OVERWRITE=cli_args['overwrite'],
        DEBUG=cli_args['debug'],
        USER_AGENTS=USER_AGENTS
    )
    
    return settings
