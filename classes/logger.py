from datetime import datetime
from termcolor import colored


class Logger:
    def __init__(self, lid=None):
        self.lid = lid

    def log(self, text, error=False):
        color = 'red' if error else 'green'
        print(colored('[{}]:[{}] - {}'.format(
            datetime.now().strftime('%H:%M:%S'),
            str(self.lid).ljust(8),
            text
        ), color=color))

    def error(self, text):
        self.log(text, error=True)
