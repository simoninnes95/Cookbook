import tweepy,json

access_token="DpwizYuwSP2LboPh3f7nl6bGk"
access_token_secret="iKWiFmkPny7cb6bmaeU8j0ArmLKQhTIGgmlsKgCJoh7iRKmOA2"
consumer_key=""
consumer_secret=""
bearer_token="AAAAAAAAAAAAAAAAAAAAAEpsZwEAAAAAkOmk6GGCu0iOu0pBo%2F8AbnidTa8%3DuYTcF68Aa56mnpXAKWfIi5UorCHFq2uVndm5NLbhqpr8pgBJMa"

# auth= tweepy.OAuthHandler(consumer_key,consumer_secret)
# auth.set_access_token(access_token,access_token_secret)

auth = tweepy.OAuth2BearerHandler(bearer_token)
api = tweepy.API(auth)

# auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
# api = tweepy.API(auth)

print(api)


# the screen name of the user
# screen_name = "@Steph_gilmore"
  
# fetching the user
user = api.get_user(screen_name="@Steph_gilmore")
  
# fetching the followers_count
followers_count = user.followers_count

print(followers_count)