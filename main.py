import os
import time
import random
import logging
from typing import NoReturn
import requests

import pymongo
from twikit import Client, Tweet
from dotenv import load_dotenv
from funcs import *

# Set up logging
logging.basicConfig(
    filename="log.txt",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Add a StreamHandler to print log messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# Load environment variables
load_dotenv()

# Configuration
MONGO_URI = os.getenv("MONGO_URI")


def interval(t=18):
    # get a random figure between 18 and 60
    inter = random.randint(t, 70)
    print(f"Interval set to %s" % inter)
    return inter


def fetch_proxies(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        proxies = response.text.splitlines()  # Split the content into lines
        return proxies
    except requests.RequestException as e:
        logging.error(f"Error fetching the proxies: {e}")
        return []


def random_proxy():
    proxies_list = fetch_proxies(
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    )
    selected_prox = str(random.choice(proxies_list))
    parsed = f"http://{selected_prox}"
    return parsed


class TwikitBot:
    def __init__(self):
        self.client = None
        self.db = None
        self.old_tweet = ""
        self.first_run = True
        self.proxies = load_proxies()

    """def get_random_proxy_string(self):
        proxy = random.choice(self.proxies)
        ans = proxy.split(':')
        username = ans[0]
        rest = ans[1]
        password = rest.split('@')[0]
        host = rest.split('@')[1]
        port = ans[2]
        return f"http://{username}:{password}@{host}:{port}
        """
    
    def send_error_to_db(self, error_message: str):
        try:
            # Assuming we're using a collection named 'KronosTwikitErrors'
            error_collection = self.db["KronosTwikitErrors"]
            
            # Update the error field of the document with _id: 0
            # If the document doesn't exist, it will be created
            error_collection.update_one(
                {"_id": 0},
                {"$set": {"last_error": error_message}},
                upsert=True
            )
            
            print(f"Error message sent to DB: {error_message}")
        except Exception as e:
            logging.error(f"Failed to send error to database: {e}")

    def setup_mongodb(self):
        print("Setting up MongoDB connection...")
        client = pymongo.MongoClient(MONGO_URI)
        self.db = client["KronosTwikit"]
        print("MongoDB connection established.")

    def setup_twikit(self):
        print("Attempting to set up Twikit")
        self.main_proxy = get_random_proxy_string()
        try:
            self.client = Client("en-US", self.main_proxy)
            print("Twikit setup successful")
            print(f"Proxy: {self.main_proxy}")
        except Exception as e:
            logging.error(f"Error setting up Twikit: {e}")
            raise Exception("Error setting up Twikit")
        credentials = self.db["KronosTwikit"].find_one({"_id": 0})
        print(f"Credentials retrieved: {credentials['main_bot_username']}")
        self.login(credentials)
        print("Logged in successfully")

    def login(self, credentials):
        email = credentials["main_bot_email"]
        password = credentials["main_bot_password"]
        username = credentials["main_bot_username"]

        print(f"Logging in with username: {username}")

        max_retries = 3
        for _ in range(max_retries):
            try:
                self.client.login(
                    auth_info_1=username, auth_info_2=email, password=password
                )
                self.client.save_cookies("cookies.json")
                return
            except Exception as e:
                logging.warning(f"Error during login: {e}. Trying a different proxy.")
                proxy = get_random_proxy_string()
                self.client.proxy = self.main_proxy

        logging.error("Failed to login after multiple attempts.")
        raise Exception("Login failed")

    def get_latest_tweet(self, user_id: str) -> Tweet:
        print(f"Getting latest tweet from {user_id}")
        max_retries = 3
        for _ in range(max_retries):
            try:
                tweets = self.client.get_user_tweets(user_id, "Tweets")
                return tweets[0]
            except Exception as e:
                if "403" in str(e):
                    logging.error(
                        f"403 Forbidden error for user {user_id}. The account might be suspended or have privacy restrictions."
                    )
                    return None  # or raise a custom exception
                logging.warning(
                    f"Error getting latest tweet: {e}. Trying a different proxy."
                )
                proxy = get_random_proxy_string()
                self.client.proxy = proxy
                time.sleep(60)  # Wait a bit before retrying

        logging.error("Failed to get latest tweet after multiple attempts.")
        raise Exception("Failed to get latest tweet")

    def reply_to_tweet(self, tweet: Tweet):
        reply_list = self.db["KronosTwikitReplies"].find_one({"_id": 0})
        reply = random.choice(reply_list["replies"])
        tweet.reply(reply)
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
            logging.info(
                f"New tweet from {latest_tweet.user.name}: {latest_tweet.text}"
            )
            self.reply_to_tweet(latest_tweet)
        else:
            print(f"No new tweets. Latest tweet: {latest_tweet.text}")

    def run(self):
        print("Setting up Twikit....")
        self.setup_twikit()

        while True:
            print("Checking power state....")
            power_state = self.db["KronosTwikitPowerState"].find_one({"_id": 0})
            if power_state["power_state"] == "on":
                print("Bot is on, processing tweets....")
                accounts = self.db["KronosTwikitWatch"].find_one({"_id": 0})[
                    "watch_accounts"
                ]
                for account in accounts:
                    print(f"Processing tweets from {account}")
                    self.process_tweet(account)
                    CHECK_INTERVAL = interval()
                    time.sleep(CHECK_INTERVAL)
            else:
                print("Bot is off, waiting for 1 minute.")
                time.sleep(60)

    def check_power_state(self):
        power_state = self.db["KronosTwikitPowerState"].find_one({"_id": 0})
        return power_state["power_state"] == "on"


def main() -> NoReturn:
    print("Starting TwikitBot")
    bot = TwikitBot()
    print("Setting up Database....")
    bot.setup_mongodb()
    print("Bot initialized")
    while True:
        if bot.check_power_state():
            try:
                print("Running bot")
                bot.run()
            except Exception as e:
                error_message = f"Error in main loop: {str(e)}"
                logging.error(error_message)
                bot.send_error_to_db(error_message)
                sleep_interval = interval(60)
                time.sleep(sleep_interval)
        else:
            print("Bot is off, waiting for 1 minute.")
            sleep_interval = interval(60)
            time.sleep(sleep_interval)


if __name__ == "__main__":
    main()
