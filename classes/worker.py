"""
GoatCLI - Worker

This is where the fun happens

Copyright 2018 Alexander Gompper - All Rights Reserved

"""

from .logger import Logger

import threading
from time import time, sleep
import urllib3
import json

import requests
from requests.exceptions import Timeout, HTTPError

# welp they got rid of HMACs lol

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # We're way past the point of security here.

SOCIALS = ['SNAPCHAT', 'INSTAGRAM_STORY', 'FACEBOOK', 'TWITTER', 'INSTAGRAM']
VIEWS = ['view', 'visit']

TRIVIA_ID = "10-11-12-9"
PRIZE_SHARE = "SHARED_RAFFLE_ENTRY"
TRIVIA_SHARE = "SHARED_TRIVIA_GAME"
BLACK_FRIDAY_SHARE = "SHARED_BLACK_FRIDAY_RAFFLE"
ROUND_ID = 1

DELAY = 4
TIMEOUT = 6


class Worker(threading.Thread):
    def __init__(self, username, password, proxy=None, products=None, skip_to_idx=None):
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
            'X-PX-Authorization': '1:vIM4UuqX1Nke6DhOzkVTo1l0NK9LooAMWxGyxjIrbUzuJbmJ55anUdKpQft0HnkZT78ddpbrSysBefx3sa'
                                  'Evxw==:1000:uo7k5F8x43PNBHqMRfu0jltFBQAOvMpkXU/eMlC2on1rA4x/pDzJRwpMzH6c4YF3WBhP2tkQ'
                                  'qYHJTs3o7I3wSUwMfzhVHOQ81Qn8ANucHgGpusLiyaRC+GQYedD+OTej9e73u0q4N2GkS7cRfhCS/XxVi1qm'
                                  'kyNvzB4rxuNyVf+RHkiM0nOZFPuPcrbfQSdImPqExnxXfkAwC5x+Vj2h7rhb7avloAv0fZKNNhxveNhFhbIP'
                                  'OsmKN6fsZ0RSN8oGEity00QcQK29c77dVtyKSg==',
            'Accept-Encoding':  'gzip,deflate',
            'Connection':       'keep-alive',
            'Accept':           '*/*',
            'Accept-Language':  'en-us',
            'User-Agent':       'GOAT/2.23.1 (iPhone; iOS 13.2; Scale/3.00) Locale/en'  # Keep this updated.
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
        self.products = products if products else list()

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
                    with open('error-{}.txt'.format(time()), 'w') as error_file:
                        error_file.write('{}:{}'.format(self.username, self.password))
                        error_file.close()
                    return False
                elif r.status_code == 429:
                    self.error('[error] banned proxy - sleeping 10m and retrying')
                    sleep(600)
                    return self.login()
                else:
                    self.error('[error] bad status {} from login request'.format(r.status_code))
                    with open('error-code-{}.txt'.format(time()), 'w') as error_file:
                        error_file.write('{}:{} -> {}'.format(self.username, self.password, r.status_code))
                        error_file.write(json.dumps(data))
                        error_file.write(r.text)
                        error_file.close()
                    return False
        except Timeout:
            self.error('[error] timeout from login request')
            return False
        j = r.json()
        try:
            self.auth_token = j['authToken']
            self.s.headers['Authorization'] = 'Token token="{}"'.format(self.auth_token)
        except (KeyError, ValueError):
            self.error('[error] couldn\'t find auth token in response')
            return False
        return True

    def fetch_round(self, round_id):
        url = 'https://carnival-api.goat.com/api/contest/rounds/{}'.format(round_id)
        try:
            self.log('gathering products to share')
            r = self.s.get(
                url,
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                if r.status_code == 429:
                    self.error('[error] [{}] banned proxy - sleeping 10m and retrying'.format(self.username))
                    sleep(600)
                    return self.fetch_round(round_id)
                else:
                    self.error('[error] bad status code {} while gathering products'.format(r.status_code))
                    return False
        except Timeout:
            self.error('[error] timeout while gathering products')
            return False
        j = r.json()
        try:
            self.products = list(map(lambda x: x['prizeId'], j['prizes']))
        except (KeyError, IndexError):
            self.error('[error] unable to map prize ids')
            return False
        self.log('gathered [{}] products to share'.format(len(self.products)))
        return True

    def submit_share(self, pid, share_type, share_channel, idx):
        url = 'https://carnival-api.goat.com/api/contest/share'
        data = {
            'id': pid,
            'type': share_type,
            'channel': share_channel
        }
        try:
            self.log('[{}] submitting share [{}] [{}]'.format(
                str(idx).ljust(4),
                str(pid).ljust(6),
                share_type.ljust(15))
            )
            r = self.s.post(
                url,
                json={k: v for k, v in data.items() if v is not None},  # cool trick to remove keys w/ None vals
                timeout=TIMEOUT
            )
            try:
                r.raise_for_status()
            except HTTPError:
                if r.status_code == 429:
                    self.error('[error] [{}] banned proxy - sleeping 10m and retrying'.format(self.username))
                    sleep(600)
                    return self.submit_share(pid, share_type, share_channel, idx)
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
            return self.submit_share(pid, share_type, share_channel, idx)
        return True

    def run(self) -> None:
        # set auth token
        if not self.login():
            self.error('[failed] failed to login')
            return
        idx = 0
        # gather product ids if we dont already have a list from the top level
        if len(self.products) == 0:
            if not self.fetch_round(ROUND_ID):
                self.error('[failed] failed to gather product ids')
                return
            sleep(DELAY)

        # share the entire contest
        for social in SOCIALS:
            # there is no id when sharing the whole contest I guess
            if not self.submit_share(None, BLACK_FRIDAY_SHARE, social, idx):
                self.error('[{}] [failed] failed to submit [{}] [{}]'.format(str(idx).ljust(4), '-', social))
                break
            sleep(DELAY)
            idx += 1

        # share the trivia
        for social in SOCIALS:
            if not self.submit_share(TRIVIA_ID, TRIVIA_SHARE, social, idx):
                self.error('[{}] [failed] failed to submit [{}] [{}]'.format(str(idx).ljust(4), TRIVIA_ID, social))
                break
            sleep(DELAY)
            idx += 1

        # share the products
        for product in self.products:
            for social in SOCIALS:
                if not self.submit_share(product, PRIZE_SHARE, social, idx):
                    self.error('[{}] [failed] failed to submit [{}] [{}]'.format(str(idx).ljust(4), product, social))
                    return
                sleep(DELAY)
                idx += 1
