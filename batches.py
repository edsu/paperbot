#!/usr/bin/env python

import os
import re
import json
import pickle
import urllib

import feedparser

import bitly
import twitter

batch_db = "batches.db"

def main():
    for batch in new_batches():
        url = bitly.shorten(batch['url'])
        json_url = batch['url'].strip('/') + '.json' 
        batch_info = json.loads(urllib.urlopen(json_url).read())
        name = format_name(batch['awardee'])
        msg = "%s newspaper pages were just loaded from %s %s" % \
            (batch_info['page_count'], name, url)
        twitter.tweet(msg)

def new_batches():
    seen = seen_batches()
    current = current_batches()
    for batch_name in current.keys():
        if not seen.has_key(batch_name):
            yield current[batch_name]

def seen_batches():
    if not os.path.isfile(batch_db):
        pickle.dump(current_batches(), open(batch_db, 'w'))
    return pickle.load(open(batch_db))

def current_batches():
    batches = {}
    feed = feedparser.parse('http://chroniclingamerica.loc.gov/batches/feed/')
    for entry in feed.entries:
        batches[entry.title] = {'name': entry.title,
                                'awardee': entry.author,
                                'url': entry.link, 
                                'updated': entry.updated_parsed}

    pickle.dump(batches, open(batch_db, 'w'))
    return batches

def format_name(name):
    name = re.split("[;,]", name)[0]
    name = re.sub("^(The )?", "the ", name)
    return name

if __name__ == "__main__":
    main()
