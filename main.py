"""
GoatCLI - Main

This is the main functionality of this program. Intended to use with mass .csv files of accounts. Keep a 1:1 proxy
ratio to avoid soft bans. Fun fact: GOAT does not log IP addresses. I know this because someone won after I ran them,
and I used the same proxy on probably 100 other people as well. :)

Copyright 2018 Alexander Gompper - All Rights Reserved

"""

from classes.logger import Logger
from classes.worker import Worker
from classes.purchaser import Purchaser
from classes.proxy import Proxy

import csv
from time import sleep
import urllib3

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY_FILE_PATH = 'proxies.txt'
CSV_FILE_PATH = 'csv/accounts.csv'


def main():
    l = Logger(lid='M')
    log = l.log

    print(('=' * 20).center(80, ' '))
    print('GOAT Black Friday and Autocheckout'.center(80, ' '))
    print(
        """

                      _________  ___ ______  _______   ____
                     / ___/ __ \/ _ /_  __/ / ___/ /  /  _/
                    / (_ / /_/ / __ |/ /   / /__/ /___/ /  
                    \___/\____/_/ |_/_/    \___/____/___/  
                                           
        """
    )
    print('\u00a92019 Alexander Gompper'.center(80, ' '))
    print(('=' * 20).center(80, ' '))

    # Collection of workers
    workers = []

    # Collection of proxies
    log('Loading proxies')
    manager = Proxy(PROXY_FILE_PATH)
    log('Using {} proxies'.format(len(manager.proxies)))

    log('Loading accounts')
    with open(CSV_FILE_PATH) as csv_file:
        reader = csv.reader(csv_file)
        log('Loaded {} accounts'.format(sum(1 for _ in reader)))
        log('=' * 20)

        csv_file.seek(0)
        for idx, row in enumerate(reader):
            w = Worker(
                username=row[0],
                password=row[1],
                proxy=manager.get_proxy(),
                products=None,
                skip_to_idx=row[2]  # In case you crash or something you can skip all the previous entries
            )
            workers.append(w)
            workers[idx].start()
            sleep(0.1)  # makes output a little cleaner tbh


if __name__ == '__main__':
    main()
