from twikit import Client, Tweet
import time
from typing import NoReturn

USERNAME = "abuonx"
EMAIL = "exbytevpn@gmail.com"
PASSWORD = "97167059cc"


# Initialize client
client = Client("en-US")

#client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)

import os
if os.path.exists("cookies.json"):
    try:
        client.load_cookies("cookies.json")
    except:
        client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
        client.save_cookies("cookies.json")
else:
    client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
    client.save_cookies("cookies.json")

"""tweets = client.search_tweet("python", "Latest")

for tweet in tweets:
    print(tweet.user.name, tweet.text, tweet.created_at)"""

# get the user's ID
user_id = "1388186312860184584"
check_interval = (60*15)/50
print(f"Will check every {check_interval} seconds or every {check_interval/60} minutes.")

def callback(tweet: Tweet) -> None:
    print(f"{tweet.user.name}: {tweet.text}")

def get_latest_tweet(user_id: str) -> Tweet:
    tweets = client.get_user_tweets(user_id, "Tweets")
    print(tweets[0].full_text)
    return tweets[0]

#print(get_latest_tweet(user_id))

old_tweet = ""

def main() -> NoReturn:
    global old_tweet
    before_tweet = get_latest_tweet(user_id)

    while True:
        time.sleep(check_interval)
        latest_tweet = get_latest_tweet(user_id)
        if (
            before_tweet != latest_tweet and
            before_tweet.created_at_datetime < latest_tweet.created_at_datetime
        ):
            callable(latest_tweet)
        before_tweet = latest_tweet
        
        if latest_tweet.text != old_tweet:
            old_tweet = latest_tweet.text
            # reply to the tweet
            main_reply = latest_tweet.reply("lol")
            
            # login to other accounts and reply to the reply
            cli

main()