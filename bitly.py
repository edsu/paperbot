import bitlyapi

import config

def shorten(url):
    bitly = bitlyapi.BitLy(config.bitly_username, config.bitly_key)
    response = bitly.shorten(longUrl=url)
    return response['url']


