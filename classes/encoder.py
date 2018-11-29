"""
GoatCLI - Encoder

18 lines of code! Not too bad.

This thing spits out the HMAC SHA256 digest based on the three components, hashed against the ever so secure key.

Copyright 2018 Alexander Gompper - All Rights Reserved

"""

import hmac
import hashlib
import binascii


class Encoder:
    def __init__(self, secret_key):
        self.secret_key = bytes(secret_key.encode('utf-8'))

    def encode_share(self, timestamp, template_id, share_type):
        message = bytes('{1}{2}{0}'.format(
            timestamp,
            share_type,
            template_id).encode('utf-8'))
        sig = hmac.new(self.secret_key, message, digestmod=hashlib.sha256).digest()
        return binascii.hexlify(sig)

    def encode_visit(self, timestamp, location_id, visit_type):
        return self.encode_share(timestamp, location_id, visit_type)
