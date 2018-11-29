"""
GoatCLI - Webhook

A webhook listener that waits for incoming selly.gg purchases and then automatically spoofs their account tickets.
Check out ngrok for a way to tie this to a public URL. Is this secure? Probably not. Easily interceptable.

Copyright 2018 Alexander Gompper - All Rights Reserved

"""


from classes.logger import Logger
from classes.worker import Worker
from classes.proxy import Proxy

from flask import Flask, request, abort

app = Flask(__name__)

L = Logger(lid='WEB')
log = L.log

manager = Proxy('proxies.txt')

# Uh I dont feel like making more requests. Hardcoded.
PRODUCTS = [12130, 136666, 182326, 246778, 249946, 149380, 249937, 147583, 249941, 188248, 348523, 80082, 347495, 70878,
            70879, 34176, 54311, 471786, 438280, 442438, 471791, 329483, 436992, 436994, 436993, 12130, 136666, 182326,
            246778, 249946, 149380, 249937, 147583, 249941, 188248, 348523, 80082, 347495, 70878, 70879, 34176, 54311,
            471786, 438280, 442438, 471791, 329483, 436992, 436994, 436993, 438645, 261860, 149374, 371224, 406001,
            447420, 447421, 447419, 447422, 415778, 415779, 471789, 385730, 471788, 94407, 348063, 152982, 155573,
            315071, 317455, 386481, 195483, 471790, 105568, 471787, 273072, 424139, 178709, 305021, 13606, 13661,
            377540, 377542, 218099, 261948, 432477, 386497, 306892, 365514, 316993, 471792, 420223, 420208, 309050,
            38194, 446471, 300179, 434629, 292215, 331911, 331914, 14548, 15029, 459602, 429772, 351623, 355667]

LOCATIONS = [99, 96, 157, 141, 90, 91, 92, 93, 94, 95, 97, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 113,
             114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134,
             135, 136, 137, 138, 139, 140, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156,
             158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 175, 177, 178, 176, 174]


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        handle_incoming(request.json)
        return '', 200
    else:
        abort(400)


def handle_incoming(json):
    log('Inbound purchase')
    log(json)
    try:
        # Should probably do some more verification of the response.
        if int(json['status']) != 100:  # Paid in full
            return False
        # A little verification (note this is probably terribly insecure)
        # if 'soleus' in json['product_title'].lower():
        #     if json['referral'] is not None:
        #         with open('notsoleus-{}'.format(time()), 'w') as errorfile:
        #             errorfile.write(json)
        #             errorfile.close()
        #         return False
        w = Worker(
            username=json['custom']['0'],
            password=json['custom']['1'],
            products=PRODUCTS,
            locations=LOCATIONS,
            proxy=manager.get_proxy()
        )
        w.start()
        return True
    except (KeyError, ValueError):
        return False


if __name__ == '__main__':
    app.run()
