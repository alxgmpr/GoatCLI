# GoatCLI

A little raffle script to give people lots of tickets on their Black Friday / Summer raffle accounts.

### Requirements

* Python3
* pip (requests, flask, urllib4, and termcolor)
* 1:1 proxies:accounts. IP or `user:pass` format is fine.

### Running

Clone down and install requirements.

```
$ pip3 install -r requirements.txt
```

Put some accounts in the `accounts.csv` in the `csv` folder.

CSV format:

```
usernameoremail,password,skipidx
```

Skip index is if your program crashes...proxy error...close your laptop, so that you can pickup where you left off.

```
$ python3 main.py
```


### Notes

I've tried my best to handle most errors that I've come accross. The program automatically detects soft bans based on 
error codes.

If you run `webhook.py` and `main.py` at the same time they will use the same proxies! Easily changeable. 

I recommend you give decompiling the GOAT Android a whirl to practice a little weak decryption. All you really need is
apktool and some Java/Kotlin finesse and it'll spit the HMAC key right out. They'll probably change it up next year!


### Common Questions

* How do I run this?

 > If you can't figure this out based on this doc, you need to do some google-fu and learn yourself.

* Wont they ban IP addresses?

 > Apparently not lol.

* Does spoofing disqualify your account?

 > See above.
 
 
 ### Disclaimer
 
 This was mainly for fun. I made a few bucks running peoples accounts to get them to 15k tickets but that was just a
 bonus. I provide no insurance of the code provided. Use at your own risk. If they ban your account (or mine), that
 sucks for us. StockX is better anyway.
 
 
 ### MIT License
 
 See the `LICENSE` file.