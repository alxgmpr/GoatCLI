"""
GoatCLI - Worker

This is where the fun happens

Copyright 2018 Alexander Gompper - All Rights Reserved

"""

from .logger import Logger
from .encoder import Encoder

import threading
from time import time, sleep
import urllib3

import requests
from requests.exceptions import Timeout, HTTPError

E = Encoder(secret_key='AirGOAT1')  # Ooh security.

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # We're way past the point of security here.

SOCIALS = ['instagram', 'instagram_story', 'facebook', 'twitter']
VIEWS = ['view', 'visit']

DELAY = 3
TIMEOUT = 6


class Worker(threading.Thread):
    def __init__(self, username, password, proxy=None, products=None, locations=None, skip_to_idx=None):
        threading.Thread.__init__(self)
        self.local = threading.local()

        # Save init vars
        self.local.pid = self.getName()
        self.username = username
        self.password = password

        # Skip (for errors)
        try:
            self.skip_to_idx = int(skip_to_idx)
        except TypeError:
            self.skip_to_idx = 0

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
            'Host':             'www.goat.com',
            'Accept-Encoding':  'gzip,deflate',
            'Connection':       'keep-alive',
            'Accept':           '*/*',
            'Accept-Language':  'en-US;q=1',
            'User-Agent':       'GOAT/2.7.0 (iPhone; iOS 12.1; Scale/3.00)'  # Keep this updated.
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
                'http':     'http://{}'.format(self.prepared_proxy),
                'https':    'https://{}'.format(self.prepared_proxy)
            }

        # Add products and locations
        self.products = products
        self.locations = locations

    def login(self):
        self.log('[{}:{}] - logging in'.format(self.username.ljust(30), self.password.rjust(30)))
        url = 'https://www.goat.com/api/v1/users/sign_in'
        data = {
            'user[login]':      self.username,
            'user[password]':   self.password
        }
        try:
            r = self.s.post(
                url,
                data=data,
                timeout=5
            )
            try:
                r.raise_for_status()
            except HTTPError:
                if r.status_code == 422:
                    self.error('[error] incorrect username/password [{}:{}]'.format(self.username, self.password))
                    with open('error-{}.txt'.format(time()), 'w') as errorfile:
                        errorfile.write('{}:{}'.format(self.username, self.password))
                        errorfile.close()
                    return False
                elif r.status_code == 429:
                    self.error('[error] banned proxy - sleeping 10m and retrying')
                    sleep(600)
                    return self.login()
                else:
                    self.error('[error] bad status {} from login request'.format(r.status_code))
                    with open('errorcode-{}.txt'.format(time()), 'w') as errorfile:
                        errorfile.write('{}:{}'.format(self.username, self.password))
                        errorfile.write(r.text)
                        errorfile.close()
                    return False
        except Timeout:
            self.error('[error] timeout from login request')
            return False
        j = r.json()
        try:
            self.auth_token = j['authToken']
            self.s.headers['Authorization'] = 'Token token="{}"'.format(self.auth_token)
        except (KeyError, ValueError):
            self.error('[error] couldnt find auth token in response')
            return False
        return True

    def submit_shared(self, pid, share_type, idx):
        url = 'https://www.goat.com/api/v1/contests/3/shared'
        ts = int(time())
        data = {
            'digest':               E.encode_share(timestamp=ts, template_id=pid, share_type=share_type),
            'productTemplateId':    pid,
            'socialMediaType':      share_type,
            'timestamp':            ts
        }
        try:
            self.log('[{}] submitting share [{}] [{}]'.format(str(idx).ljust(4), str(pid).ljust(6), share_type.ljust(15)))
            r = self.s.post(
                url,
                data=data,
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                if r.status_code == 429:
                    self.error('[error] [{}] banned proxy - sleeping 10m and retrying'.format(self.username))
                    sleep(600)
                    return self.submit_shared(pid, share_type, idx)
                else:
                    self.error('[error] [{}] bad status code {} from share [{}] [{}]'.format(
                        self.username,
                        r.status_code,
                        pid,
                        share_type))
                    return False
        except Timeout:
            self.error('[error] [{}] timeout from share [{}] [{}] - sleeping 30sec and retrying'.format(
                self.username,
                pid,
                share_type))
            sleep(30)
            return self.submit_shared(pid, share_type, idx)
        return True

    def submit_visited(self, pid, visit_type, idx):
        url = 'https://www.goat.com/api/v1/contests/3/visited'
        ts = int(time())
        data = {
            'digest':               E.encode_visit(timestamp=ts, location_id=pid, visit_type=visit_type),
            'contestLocationId':    pid,
            'visitType':            visit_type,
            'timestamp':            ts
        }
        try:
            self.log('[{}] submitting visit [{}] [{}]'.format(str(idx).ljust(4), str(pid).ljust(6), visit_type.ljust(15)))
            r = self.s.post(
                url,
                data=data,
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                if r.status_code == 429:
                    self.error('[error] banned proxy - sleeping 10m and retrying')
                    sleep(600)
                    return self.submit_visited(pid, visit_type, idx)
                else:
                    self.error('[error] [{}] bad status code {} from visit [{}] [{}]'.format(
                        self.username,
                        r.status_code,
                        pid,
                        visit_type))
                    return False
        except Timeout:
            self.error('[error] [{}] timeout from visit [{}] [{}] - sleeping 30sec and retrying'.format(
                self.username,
                pid,
                visit_type))
            return self.submit_visited(pid, visit_type, idx)
        return True

    def run(self):
        if not self.login():
            self.error('[failed] failed to login')
            return False
        for idx, product in enumerate(self.products):
            if idx <= self.skip_to_idx:
                continue
            for social in SOCIALS:
                sleep(DELAY)
                if not self.submit_shared(product, social, idx):
                    self.error('[{}] [failed] failed to submit [{}] [{}]'.format(str(idx).ljust(4), product, social))
                    return False
        for idx, location in enumerate(self.locations):
            for view in VIEWS:
                sleep(DELAY)
                if not self.submit_visited(location, view, idx):
                    self.error('[{}] [failed] failed to submit [{}] [{}]'.format(str(idx).ljust(4), location, view))
                    return False
        return True
