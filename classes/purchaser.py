"""
GoatCLI - Purchaser

This is where even more fun happens

Copyright 2019 Alexander Gompper - All Rights Reserved

"""

from .logger import Logger

import threading
from time import time, sleep
import urllib3
import json

import requests
from requests.exceptions import Timeout, HTTPError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PURCHASE_DELAY = 2
DELAY = 4
TIMEOUT = 6


class Purchaser(threading.Thread):
    def __init__(self, username, password, target_pid, target_size, proxy=None):
        threading.Thread.__init__(self)

        # most of this stuff is the same as the Worker class...
        # TODO: make this a subclass of worker
        self.local = threading.local()

        # Save init vars
        self.local.pid = self.getName()
        self.username = username
        self.password = password

        # Update logger
        self.L = Logger(self.getName())
        self.log = self.L.log
        self.error = self.L.error

        # Worker session
        self.proxy = proxy
        self.auth_token = ''
        self.s = requests.Session()
        self.s.verify = False
        self.s.headers = {
            'Accept-Encoding': 'gzip,deflate',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Accept-Language': 'en-us',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/78.0.3904.108 Safari/537.36'
        }
        if self.proxy:
            # If someone has a better method, pls share.
            self.split_proxy = self.proxy.split(':')
            if len(self.split_proxy) is 4:
                self.prepared_proxy = '{}:{}@{}:{}'.format(
                    self.split_proxy[2],
                    self.split_proxy[3],
                    self.split_proxy[0],
                    self.split_proxy[1]
                )
            else:
                self.prepared_proxy = self.proxy
            self.s.proxies = {
                'http': 'http://{}'.format(self.prepared_proxy),
                'https': 'https://{}'.format(self.prepared_proxy)
            }
        self.target_pid = str(target_pid)
        self.target_size = str(target_size)
        self.order_id = 0
        self.final_price_cents = 0

    def get_csrf(self):
        self.log('gathering csrf and px data')
        home = 'https://www.goat.com'
        try:
            r = self.s.get(
                home,
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                self.error('[error] bad status {} from homepage request (csrf)')
                return False
        except Timeout:
            self.error('[error] timeout from homepage request (csrf)')
            return False
        for c in r.cookies:
            if c.name == "csrf":
                self.log('got csrf {}'.format(c.value))
                self.s.headers['X-CSRF-Token'] = c.value
                return True
        self.error('[error] failed to find a csrf token in the response cookies')
        return False

    def login(self):
        self.log('[{}:{}] - logging in'.format(self.username.ljust(30), self.password.rjust(30)))
        url = 'https://www.goat.com/web-api/v1/login'
        data = {
            "user": {
                "username": self.username,
                "password": self.password
            }
        }
        try:
            r = self.s.post(
                url,
                json=data,
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                if r.status_code == 422:
                    self.error('[error] incorrect username/password [{}:{}]'.format(self.username, self.password))
                    with open('purchaser-error-{}.txt'.format(time()), 'w') as errorfile:
                        errorfile.write('{}:{}'.format(self.username, self.password))
                        errorfile.close()
                    return False
                elif r.status_code == 429:
                    self.error('[error] banned proxy - sleeping 10m and retrying')
                    sleep(600)
                    return self.login()
                else:
                    self.error('[error] bad status {} from login request'.format(r.status_code))
                    with open('purchaser-error-code-{}.txt'.format(time()), 'w') as errorfile:
                        errorfile.write('{}:{} -> {}'.format(self.username, self.password, r.status_code))
                        errorfile.write(json.dumps(data))
                        errorfile.write(r.text)
                        errorfile.close()
                    return False
        except Timeout:
            self.error('[error] timeout from login request')
            return False
        return True

    def wait_for_product(self):
        self.log('waiting for product to go live')
        url = 'https://www.goat.com/web-api/v1/product_variants'
        params = {
            'productTemplateId': self.target_pid
        }
        try:
            r = self.s.get(
                url,
                params=params,
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                self.error('[error] bad status {} while waiting for product to go live'.format(r.status_code))
                return False
        except Timeout:
            self.error('[error] timeout while waiting for product to go live')
            return False
        j = r.json()
        if len(j) > 0:
            self.log('found {} sizes; product is live or loading up'.format(r.status_code))
            return True
        return False

    def create_order(self):
        self.log('creating a new order for {} in size {}'.format(self.target_pid, self.target_size))
        url = 'https://www.goat.com/web-api/v1/orders/create_for_product_template'
        data = {
            "order": {
                "boxCondition": "good_condition",
                "instantShip": False,
                "productTemplateId": self.target_pid,
                "size": self.target_size
            }
        }
        try:
            r = self.s.post(
                url,
                json=data,
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                if r.status_code == 422:
                    # assuming everything else is right, this indicates product isn't live yet
                    # using the regular delay here, we only want to use the 'spammy' delay when its right about to drop
                    self.log('[warn] unable to create new checkout session, will retry after {}s'.format(DELAY))
                    sleep(DELAY)
                    return self.create_order()
                else:
                    self.error('[error] bad status code {} while creating a new order'.format(r.status_code))
                    return False
        except Timeout:
            self.error('[error] timeout while creating a new order')
            return False
        j = r.json()
        self.order_id = j['order']['number']
        self.final_price_cents = j['order']['final_price_cents']
        self.log('created order {}, total price ${}'.format(self.order_id, round(self.final_price_cents / 100, 2)))
        return True

    def submit_order(self):
        self.log('submitting order completion')
        if self.order_id == 0 or self.final_price_cents == 0:
            self.error('[error] was attempting to submit but order id or final price was still zero')
        url = 'https://www.goat.com/web-api/v1/orders/{}/buy'.format(self.order_id)
        data = {
            "finalPriceCents": self.final_price_cents
        }
        try:
            r = self.s.put(
                url,
                json=data,
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                if r.status_code == 422:
                    self.log('unable to finalize order, will retry in {}s'.format(PURCHASE_DELAY))
                    sleep(PURCHASE_DELAY)
                    return self.submit_order()
                else:
                    self.error('[error] bad status code {} while finalizing order #{}'.format(
                        r.status_code,
                        self.order_id
                    ))
                    return False
        except Timeout:
            self.error('[error] timeout while finalizing order #{}'.format(self.order_id))
            return False
        self.log('[success] order #{} was successfully finalized'.format(self.order_id))
        return True

    def run(self) -> None:
        if not self.get_csrf():
            self.error('[failed] failed to get csrf token from homepage')
            return
        if not self.login():
            self.error('[failed] failed to login to account {}'.format(self.username))
            return
        if not self.create_order():
            self.error('[failed] failed to create a new order')
            return
        return
        if not self.submit_order():
            self.error('[failed] failed to submit order')
            return
        self.log('completed run')
        return

