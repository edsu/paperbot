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
    search = "https://chroniclingamerica.loc.gov/search/pages/results/" + \
             "?date1=%s&date2=%s&format=json&dateFilterType=range&page=%s" + \
             "&lccn=%s" 
    for lccn in lccns():
        search_page = 1
        while True:
            url = search % (day, day, search_page, lccn) 
            try:
                response = json.loads(urllib.urlopen(url).read())
            except ValueError, e:
                continue

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
    url = 'https://chroniclingamerica.loc.gov/' + page['id'] + 'ocr.xml'
    ns = {'alto': 'http://schema.ccs-gmbh.com/ALTO'}
    dictionary = Dictionary()

    blocks = []
    try:
        # some pages are not digitized, and don't have ocr
        xml = urllib.urlopen(url).read()
        doc = etree.fromstring(xml)
    except Exception as e:
        return blocks

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

        if string_count == 0 or dictionary_words == 0:
            continue

        text = ' '.join(text)
        h = int(b.attrib['HEIGHT'])
        w = int(b.attrib['WIDTH'])
        vpos = float(b.attrib['VPOS'])

        # ignore masthead
        if vpos < 1800:
            continue

        # ignore text > 80 characters, we're looking for short headlines
        if len(text) > 80:
            continue

        word_ratio = dictionary_words / len(text)
        confidence = confidence / string_count

        b = {'text': text, 'confidence': confidence,
             'height': h, 'width': w, 'word_ratio': word_ratio,
             'vpos': vpos, 'lccn': page['lccn'], 'page_id': page['id']} 

        blocks.append(b)

    return blocks


def tweetability(a, b):
    def index(block):
        return ((block['height'] * block['width']) ^ 2) * block['word_ratio'] * len(block['text']) * (1/block['vpos'])
    return cmp(index(b), index(a))


def twitter_msg(headline, date):
    # calculate how much tweet space there is for a snippet
    # 140 - (date + short_url + punctuation)
    d = datetime.datetime.strftime(date, '%b %d, %Y')
    remaining = 140 - (len(d) + 20 + 5) 
    snippet = headline['text'][0:remaining]

    # shorten the url
    url = "https://chroniclingamerica.loc.gov%s" % headline['page_id']

    msg = '%s: "%s" %s' % (d, snippet, url)
    return msg


def lccns():
    url = 'https://chroniclingamerica.loc.gov/newspapers.txt'
    lccns = []
    for line in urllib.urlopen(url):
        line = line.strip()
        if not line: continue
        cols = line.split(" | ")
        lccns.append(cols[3])
    return lccns

class Dictionary:

    def __init__(self):
        self._open()

    def is_word(self, w):
        w = w.lower()
        if len(w) < 4:
            return False
        return self.db.has_key(w.encode('utf-8')) == 1

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
