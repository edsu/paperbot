"""
Little utilities around tweepy for twitter interaction.
"""

import tweepy

import config

def tweet(msg):
    auth = tweepy.OAuthHandler(config.twitter_oauth_consumer_key, 
                               config.twitter_oauth_consumer_secret)
    auth.set_access_token(config.twitter_oauth_access_token_key,
                          config.twitter_oauth_access_token_secret)
    twitter = tweepy.API(auth)
    twitter.update_status(msg)


