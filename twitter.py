"""
Little utilities around tweepy for twitter interaction.
"""

import sys
import tweepy
import config

auth = tweepy.OAuthHandler(config.twitter_oauth_consumer_key, 
                           config.twitter_oauth_consumer_secret)
auth.set_access_token(config.twitter_oauth_access_token_key,
                      config.twitter_oauth_access_token_secret)
twitter = tweepy.API(auth)

def tweet(msg):
    twitter.update_status(msg)

if __name__ == '__main__':
    tweet(sys.argv[1])


