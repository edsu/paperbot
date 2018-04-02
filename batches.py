#!/usr/bin/env python

import os
import re
import json
import time
import pickle
import twitter
import urllib
import feedparser


batches_json = "batches.json"

def main():
    for batch in new_batches():
        json_url = batch['url'].strip('/') + '.json' 
        batch_info = json.loads(urllib.urlopen(json_url).read())
        name = format_name(batch['awardee'])
        msg = "%s newspaper pages were just loaded from %s %s" % \
            (batch_info['page_count'], name, batch['url'])
        twitter.tweet(msg)
        time.sleep(5)

def new_batches():
    seen = seen_batches()
    current = current_batches()
    if len(current) == 0:
        return
    for batch_name in current.keys():
        if not seen.has_key(batch_name):
            yield current[batch_name]
    save_batches(current)

def seen_batches():
    if not os.path.isfile(batches_json):
        batches = current_batches()
        save_batches(batches)
    return json.loads(open(batches_json).read())

def current_batches():
    feed = feedparser.parse('https://chroniclingamerica.loc.gov/batches/feed/')
    batches = {}
    for entry in feed.entries:
        batches[entry.title] = {'name': entry.title,
                                'awardee': entry.author,
                                'url': entry.link, 
                                'updated': entry.updated}
    return batches

def save_batches(batches):
    if len(batches) > 0:
        open(batches_json, "w").write(json.dumps(batches, indent=2))

def format_name(name):
    name = re.split("[;,]", name)[0]
    name = re.sub("^(The )?", "the ", name)
    return name

if __name__ == "__main__":
    main()
