"""
GoatCLI - Main

This is the main functionality of this program. Intended to use with mass .csv files of accounts. Keep a 1:1 proxy
ratio to avoid soft bans. Fun fact: GOAT does not log IP addresses. I know this because someone won after I ran them,
and I used the same proxy on probably 100 other people as well. :)

Copyright 2018 Alexander Gompper - All Rights Reserved

"""

from classes.logger import Logger
from classes.worker import Worker
from classes.proxy import Proxy

import csv
from time import sleep
import urllib3

import requests
from requests.exceptions import Timeout

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXYFILE = 'proxies.txt'
CSVFILE = 'csv/accounts.csv'

DUMMYUSER = 'xxx'
DUMMYPASS = 'yyy'


def main():
    l = Logger(lid='M')
    log = l.log
    error = l.error

    s = requests.Session()
    s.verify = False
    s.headers = {
        'Host': 'www.goat.com',
        'Accept-Encoding': 'gzip,deflate',
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'Accept-Language': 'en-US;q=1',
        'User-Agent': 'GOAT/2.7.0 (iPhone; iOS 12.1; Scale/3.00)'  # Keep this updated.
    }

    print(('=' * 20).center(80, ' '))
    print('GOAT Black Friday / Summer Raffle Tickets'.center(80, ' '))
    print(
        """

                      _________  ___ ______  _______   ____
                     / ___/ __ \/ _ /_  __/ / ___/ /  /  _/
                    / (_ / /_/ / __ |/ /   / /__/ /___/ /  
                    \___/\____/_/ |_/_/    \___/____/___/  
                                           
        """
    )
    print('\u00a92018 Alexander Gompper'.center(80, ' '))
    print(('=' * 20).center(80, ' '))

    # Collection of workers
    workers = []

    # Collection of proxies
    log('Loading proxies')
    manager = Proxy(PROXYFILE)
    log('Using {} proxies'.format(len(manager.proxies)))

    # TODO: change status code handling for 429 errors from scraping

    # Collection of products
    log('Loading products')
    products = []
    for page in range(5):
        sleep(1)
        url = 'https://www.goat.com/api/v1/contests/3?page={}'.format(page)
        try:
            r = s.get(
                url,
                timeout=5
            )
            if r.status_code == 200:
                try:
                    r = r.json()
                    for prod in r['productTemplates']:
                        products.append(prod['id'])
                        # log('{} \t\t|| {}'.format(prod['id'], prod['name'].encode('utf-8')))
                    log('scraped {} ids'.format(len(products)))
                except KeyError:
                    error('[failed] failed to scrape product ids')
                    return False
            else:
                error('got bad status code {} from pid scrape'.format(r.status_code))
                return False
        except Timeout:
            error('[error] timeout from pid scrape')
            return False
    print(products)
    sleep(3)

    # Collection of locations
    log('Loading locations')
    # Need to have a dummy worker to login so that we dont get denied looking for locations
    # No clue why you must be logged in to get location ids but not social... nice.
    dummy_worker = Worker(username=DUMMYUSER, password=DUMMYPASS)
    dummy_worker.login()
    locations = []
    url = 'https://www.goat.com/api/v1/contests/3/locations'
    try:
        r = dummy_worker.s.get(
            url,
            timeout=5
        )
        if r.status_code == 200:
            try:
                r = r.json()
                for loc in r:
                    locations.append(loc['id'])
                    # log('{} \t {}'.format(loc['id'], loc['name'].encode('utf-8')))
                log('scraped {} loc ids'.format(len(locations)))
            except KeyError:
                error('couldnt find location ids')
                return False
        else:
            error('got bad status code {} from loc scrape'.format(r.status_code))
            return False
    except requests.exceptions.Timeout:
        error('timeout from loc scrape')
        return False
    print(locations)
    sleep(3)

    log('Loading accounts')
    with open(CSVFILE) as csvfile:
        reader = csv.reader(csvfile)
        log('Loaded {} accounts'.format(sum(1 for _ in reader)))
        log('=' * 20)

        csvfile.seek(0)
        for idx, row in enumerate(reader):
            w = Worker(
                username=row[0],
                password=row[1],
                proxy=manager.get_proxy(),
                products=products,
                locations=locations,
                skip_to_idx=row[2]  # In case you crash or something you can skip all the previous entries
            )
            w.start()
            workers.append(w)
            sleep(0.05)


if __name__ == '__main__':
    main()
