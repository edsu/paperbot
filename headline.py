#!/usr/bin/env python

"""
Kind of an insane little script that looks at all the newspapers in 
Chronicling America for the current calendar day, one hundred years ago. 
It then attempts to extract headlines from the front page of each paper
that is available, and sends the "best" chunk of text it can find as a 
twitter status update.
"""

import os
import dbm
import sys
import json
import random
import urllib
import datetime

import bitlyapi

from lxml import etree

import twitter
import config

def main(argv):
    if len(argv) > 1: # for testing
        date = datetime.datetime.strptime(argv[1], '%m/%d/%Y')
    else:
        today = datetime.date.today()
        date = datetime.date(today.year-100, today.month, today.day)

    headlines = []
    for page in front_pages(date):
        headlines.extend(blocks(page))

    headlines.sort(tweetability)
    msg = twitter_msg(headlines[0], date)
    twitter.tweet(msg)


def front_pages(date):
    """
    Returns all newspaper front pages for a given day.
    """
    day = datetime.datetime.strftime(date, '%m/%d/%Y')
    search = "http://chroniclingamerica.loc.gov/search/pages/results/" + \
             "?date1=%s&date2=%s&format=json&dateFilterType=range&page=%s" + \
             "&lccn=%s" 
    for lccn in lccns():
        search_page = 1
        while True:
            url = search % (day, day, search_page, lccn) 
            response = json.loads(urllib.urlopen(url).read())
            front_page = None
            
            for hit in response['items']:
                if hit['sequence'] == 1:
                    front_page = hit

            if front_page:
                yield front_page
                break
            # maybe put this back in if there isn't a 302 redirect when 
            # the requested search page is out of bounds...
            #elif len(response) > 0:
            #    search_page += 1
            else:
                break


def blocks(page):
    """
    Returns blocks of ocr text from a page, limited to the first 120 characters
    along with some metadata associated with the block: height, width
    number of dictionary words, etc.
    """
    url = 'http://chroniclingamerica.loc.gov/' + page['id'] + 'ocr.xml'
    ns = {'alto': 'http://schema.ccs-gmbh.com/ALTO'}
    doc = etree.parse(url)
    dictionary = Dictionary()

    blocks = []
    for b in doc.xpath('//alto:TextBlock', namespaces=ns): 
        text = []
        text_length = 0
        confidence = 0.0
        string_count = 0
        dictionary_words = 0.0
        for l in b.xpath('alto:TextLine', namespaces=ns):
            for s in l.xpath('alto:String[@CONTENT]', namespaces=ns):
                string = s.attrib['CONTENT']
                text.append(string)
                text_length += len(string)
                confidence += float(s.attrib['WC'])
                string_count += 1
                if dictionary.is_word(string):
                    dictionary_words += 1

            # can't use more text than this in twitter anyhow
            if text_length > 120:
                break

        if string_count == 0 or dictionary_words == 0:
            continue

        h = float(b.attrib['HEIGHT'])
        w = float(b.attrib['WIDTH'])
        word_ratio = dictionary_words / string_count
        confidence = confidence / string_count

        # should be a good amount of real words
        if word_ratio < 0.95:
            continue

        b = {'text': ' '.join(text), 'confidence': confidence,
             'height': h, 'width': w, 'word_ratio': word_ratio,
             'lccn': page['lccn'], 'page_id': page['id']} 

        blocks.append(b)

    return blocks


def tweetability(a, b):
    def index(block):
        return block['height'] * block['word_ratio']
    return cmp(index(b), index(a))


def twitter_msg(headline, date):
    # calculate how much tweet space there is for a snippet
    # 140 - (date + short_url + punctuation)
    d = datetime.datetime.strftime(date, '%b %d, %Y')
    remaining = 140 - (len(d) + 20 + 5) 
    snippet = headline['text'][0:remaining]

    # shorten the url
    url = "http://chroniclingamerica.loc.gov%s" % headline['page_id']
    bitly = bitlyapi.BitLy(config.bitly_username, config.bitly_key)
    response = bitly.shorten(longUrl=url)
    short_url = response['url']

    msg = '%s: "%s" %s' % (d, snippet, short_url)
    return msg


def lccns():
    url = 'http://chroniclingamerica.loc.gov/newspapers.txt'
    for line in urllib.urlopen(url):
        line = line.strip()
        if not line: continue
        yield line.split(" | ")[3]


class Dictionary:

    def __init__(self):
        self._open()

    def is_word(self, w):
        return self.db.has_key(w.lower().encode('utf-8')) == 1

    def _open(self):
        try:
            self.db = dbm.open('dictionary', 'r')
        except dbm.error:
            self._make()
            self.db = dbm.open('dictionary', 'r')


    def _make(self):
        word_file = '/etc/dictionaries-common/words'
        if not os.path.isfile(word_file):
            raise Exception("can't find word file: %s" % word_file)
        db = dbm.open('dictionary', 'c')
        for word in open(word_file, 'r'):
            word = word.lower().strip()
            db[word] = '1'
        db.close()


if __name__ == '__main__':
    main(sys.argv)
