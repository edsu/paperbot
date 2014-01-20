#!/usr/bin/env python

"""
Retweet people that look like they are finding interesting stuff on 
chroniclignamerica.loc.gov ; might need to turn this off if it proves 
to be too noisy.
"""

import os
import json
import time
import random
import datetime

from twitter import twitter

touchfile = "last_retweet"

if os.path.isfile(touchfile):
    last = datetime.datetime.fromtimestamp(os.stat(touchfile).st_mtime)
else: 
    last = None

tweets = twitter.search("chroniclingamerica", count=100)
tweets.reverse()

new_last = None
for tweet in tweets:
    new_last = tweet.created_at
    if hasattr(tweet, 'retweeted_status'):
        continue
    if tweet.user.screen_name == "paperbot":
        continue
    if tweet.possibly_sensitive:
        continue
    if last and tweet.created_at < last:
        continue
    if tweet.text.startswith("RT"):
        continue
    tweet.retweet()
    time.sleep(random.randint(30, 200))

if not os.path.isfile(touchfile):
    open(touchfile, "w")

if new_last:
    os.utime(touchfile, (0, int(time.mktime(new_last.timetuple()))))
