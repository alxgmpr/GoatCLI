from .logger import Logger

L = Logger(lid='P')
log = L.log


class Proxy:
    def __init__(self, file):
        self.i = -1
        with open(file) as proxyfile:
            self.proxies = proxyfile.read().splitlines()

    def get_proxy(self):
        if len(self.proxies) is 0:
            return None
        self.i += 1
        if self.i >= len(self.proxies):
            self.i = 0
        return self.proxies[self.i]
