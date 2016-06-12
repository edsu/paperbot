#!/usr/bin/env python

"""
Retweet people that look like they are finding interesting stuff on 
chroniclingamerica.loc.gov; might need to turn this off if it proves 
to be too noisy.

We remember which tweets we've already retweeted by setting the mtime
on touchfile to the date of the last tweet we've seen. We also take 
care not to retweet ourselves, and not to retweet other retweets, which
could create a literal echo chamber :-)

Lastly, we make sure to only retweet tweets that link exclusively to
chroniclingamerica.loc.gov. If a tweet also has links to other places it won't
get retweeted. This is a conservative measure to prevent the spread of spam
and other weirdness.
"""

import os
import time
import config
import random
import datetime
import requests

from twitter import twitter

def all_chronam_urls(tweet):
    """return True if all the urls in a tweet target Chronicling America"""
    for u in tweet.entities['urls']:
        url = u['expanded_url']
        try:
            r = requests.get(url)
            if not r.url.startswith('http://chroniclingamerica.loc.gov'):
                return False
        except:
            # if we couldn't fetch the URL we don't want to tweet it anyway
            return False
    return True

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
    if hasattr(tweet, 'possibly_sensitive') and tweet.possibly_sensitive:
        continue
    if tweet.user.screen_name in config.block:
        continue
    if last and tweet.created_at <= last:
        continue
    if tweet.text.startswith("RT"):
        continue
    if not all_chronam_urls(tweet):
        continue
    try:
        tweet.retweet()
    except Exception as e:
        print e
    time.sleep(random.randint(2, 30))

if not os.path.isfile(touchfile):
    open(touchfile, "w")

if new_last:
    os.utime(touchfile, (0, int(time.mktime(new_last.timetuple()))))
