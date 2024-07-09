import os
import time
import random
import logging
from typing import NoReturn

import pymongo
from twikit import Client, Tweet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Configuration
MONGO_URI = os.getenv("MONGO_URI")
CHECK_INTERVAL = 18  # 15 minutes / 50

class TwikitBot:
    def __init__(self):
        self.client = None
        self.db = None
        self.old_tweet = ""
        self.first_run = True
        self.proxies = [
            "MrAndersonFlushed01:wxvyskd1q5rb:x282.fxdx.in:14361",
            "MrAndersonFlushed02:sbkpmgmsb99s:x174.fxdx.in:16469",
            "MrAndersonFlushed03:vzcy5g5xw572:x314.fxdx.in:14033",
            "MrAndersonFlushed04:hzadxjwrm3p3:x314.fxdx.in:14034",
            "MrAndersonFlushed05:pszf1mzrhhfy:x321.fxdx.in:14274"
        ]

    def get_random_proxy_string(self):
        proxy = random.choice(self.proxies)
        username, password, host, port = proxy.split(':')
        return f"http://{username}:{password}@{host}:{port}"

    def setup_mongodb(self):
        client = pymongo.MongoClient(MONGO_URI)
        self.db = client["KronosTwikit"]

    def setup_twikit(self):
        print("Attempting to set up Twikit")
        proxy = self.get_random_proxy_string()
        try:
            print(f"Using proxy: {proxy}")
            self.client = Client("en-US", proxy=proxy)
            print("Twikit setup successful")
        except Exception as e:
            logging.error(f"Error setting up Twikit: {e}")
            print(f"Error setting up Twikit: {e}")
            raise Exception("Error setting up Twikit")
        credentials = self.db["KronosTwikit"].find_one({"_id": 0})
        print(f"Credentials: {credentials}")
        self.login(credentials)
        print("Logged in successfully")

    def login(self, credentials):
        email = credentials["main_bot_email"]
        password = credentials["main_bot_password"]
        username = credentials["main_bot_username"]

        print(f"Logging in with {email} and {password}")
        
        max_retries = 3
        for _ in range(max_retries):
            try:
                self.client.login(auth_info_1=username, auth_info_2=email, password=password)
                self.client.save_cookies("cookies.json")
                return
            except Exception as e:
                logging.warning(f"Error during login: {e}. Trying a different proxy.")
                print(f"Error during login: {e}. Trying a different proxy.")
                proxy = self.get_random_proxy_string()
                self.client.proxy = proxy
        
        logging.error("Failed to login after multiple attempts.")
        print("Failed to login after multiple attempts.")
        raise Exception("Login failed")

    def get_latest_tweet(self, user_id: str) -> Tweet:
        logging.info(f"Getting latest tweet from {user_id}")
        max_retries = 3
        for _ in range(max_retries):
            try:
                tweets = self.client.get_user_tweets(user_id, "Tweets")
                return tweets[0]
            except Exception as e:
                logging.warning(f"Error getting latest tweet: {e}. Trying a different proxy.")
                print(f"Error getting latest tweet: {e}. Trying a different proxy.")
                proxy = self.get_random_proxy_string()
                self.client.proxy = proxy
                time.sleep(60)  # Wait a bit before retrying
        
        logging.error("Failed to get latest tweet after multiple attempts.")
        print("Failed to get latest tweet after multiple attempts.")
        raise Exception("Failed to get latest tweet")

    def reply_to_tweet(self, tweet: Tweet):
        reply_list = self.db["KronosTwikitReplies"].find_one({"_id": 0})
        reply = random.choice(reply_list["replies"])
        tweet.reply(reply)
        logging.info(f"Replied to {tweet.user.name}'s tweet with: {reply}")
        print(f"Replied to {tweet.user.name}'s tweet with: {reply}")

    def process_tweet(self, username: str):
        print(f"Getting user ID for {username}")
        user_id = self.client.get_user_by_screen_name(username).id
        print(f"User ID: {user_id}")
        latest_tweet = self.get_latest_tweet(user_id)
        print(f"Latest tweet: {latest_tweet.text}")
        
        if self.first_run:
            self.old_tweet = latest_tweet.text
            self.first_run = False
            print("First run, setting old tweet")
            logging.info("PROGRAM STARTED")
        
        if latest_tweet.text != self.old_tweet:
            print("New tweet found, replying")
            self.old_tweet = latest_tweet.text
            logging.info(f"New tweet from {latest_tweet.user.name}: {latest_tweet.text}")
            self.reply_to_tweet(latest_tweet)
        else:
            logging.info(f"No new tweets. Latest tweet: {latest_tweet.text}")
            print(f"No new tweets. Latest tweet: {latest_tweet.text}")

    def run(self):
        #print("Setting up MongoDB....")
        #self.setup_mongodb()
        print("Setting up Twikit....")
        self.setup_twikit()

        while True:
            print("Checking power state....")
            power_state = self.db["KronosTwikitPowerState"].find_one({"_id": 0})
            if power_state["power_state"] == "on":
                print("Bot is on, processing tweets....")
                accounts = self.db["KronosTwikitWatch"].find_one({"_id": 0})["watch_accounts"]
                for account in accounts:
                    print(f"Processing tweets from {account}")
                    self.process_tweet(account)
                    time.sleep(CHECK_INTERVAL)
            else:
                logging.info("Bot is off, waiting for 1 minute.")
                print("Bot is off, waiting for 1 minute.")
                time.sleep(60)
    
    def check_power_state(self):
        power_state = self.db["KronosTwikitPowerState"].find_one({"_id": 0})
        return power_state["power_state"] == "on"

def main() -> NoReturn:
    print("Starting TwikitBot")
    bot = TwikitBot()
    # set up mongodb
    print("Setting up Database....")
    bot.setup_mongodb()
    print("Bot initialized")
    while True:
        if bot.check_power_state():
            try:
                print("Running bot")
                bot.run()
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                print(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    main()