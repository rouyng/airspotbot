import tweepy

# Authenticate to Twitter
auth = tweepy.OAuthHandler("CONSUMER_KEY", "CONSUMER_SECRET")
auth.set_access_token("ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")

# Create API object
api = tweepy.API(auth)

# Create a tweet
api.update_status("Hello Tweepy")

# TODO: write functions to generate spot tweets based on adsbexchange api data
# TODO: write functions to pull supplementary information (registration, photos) for spots and add in tweet replies


