import tweepy
import configparser

# TODO: write functions to generate spot tweets based on adsbexchange api data
# TODO: write functions to pull supplementary information (registration, photos) for spots and add in tweet replies


def initialize_twitter_api(ckey, csec, atkn, asec):
    # Authenticate to Twitter
    auth = tweepy.OAuthHandler(ckey, csec)
    auth.set_access_token(atkn, asec)
    # Create API object
    api = tweepy.API(auth)
    return api


if __name__ == "__main__":
        twapi = initialize_twitter_api("CONSUMER_KEY", "CONSUMER_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")
        # Create a tweet
        twapi.update_status("Hello Tweepy")
