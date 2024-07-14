import os
import time
import random
import logging
from typing import NoReturn
import requests

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

def fetch_proxies(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        proxies = response.text.splitlines()  # Split the content into lines
        return proxies
    except requests.RequestException as e:
        print(f"Error fetching the proxies: {e}")
        return []


def random_proxy():
    proxies_list = fetch_proxies("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt")
    selected_prox = str(random.choice(proxies_list))
    parsed = f"http://{selected_prox}"
    return parsed

def load_proxies():
    proxy_list = []
    try:
        with open("proxies.txt", "r") as file:
            for line in file:
                line = line.split("//")
                line = line[1]
                proxy_list.append(line.strip())
    except FileNotFoundError:
        print("Error: proxies.txt file not found.")
    except IOError:
        print("Error: Unable to read proxies.txt file.")
    return proxy_list

class TwikitBot:
    def __init__(self):
        self.client = None
        self.db = None
        self.old_tweet = ""
        self.first_run = True
        self.proxies = load_proxies()

    def get_random_proxy_string(self):
        proxy = random.choice(self.proxies)
        ans = proxy.split(':')
        username = ans[0]
        rest = ans[1]
        password = rest.split('@')[0]
        host = rest.split('@')[1]
        port = ans[2]
        return f"http://{username}:{password}@{host}:{port}"

    def setup_mongodb(self):
        client = pymongo.MongoClient(MONGO_URI)
        self.db = client["KronosTwikit"]

    def setup_twikit(self):
        print("Attempting to set up Twikit")
        #proxy = random_proxy()
        #try:
        #print(f"Using proxy: {proxy}")
        self.client = Client("en-US", 'http://brd-customer-hl_d38b4176-zone-residential_proxy1:swyj946btrg8@brd.superproxy.io:22225')
        print("Twikit setup successful")
        """except Exception as e:
            logging.error(f"Error setting up Twikit: {e}")
            print(f"Error setting up Twikit: \n{Exception}")
            raise Exception("Error setting up Twikit")"""
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
                self.client.login(auth_info_1="abuonx", auth_info_2="exbytevpn@gmail.com", password="97167059cc")
                self.client.save_cookies("cookies.json")
                return
            except Exception as e:
                logging.warning(f"Error during login: {e}. Trying a different proxy.")
                print(f"Error during login: {e}. Trying a different proxy.")
                proxy = self.get_random_proxy_string()
                self.client.proxy = 'http://brd-customer-hl_d38b4176-zone-residential_proxy1:swyj946btrg8@brd.superproxy.io:22225'
        
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
            #try:
            print("Running bot")
            bot.run()
            #except Exception as e:
            #    logging.error(f"Error in main loop: {e}")
            #    print(f"Error in main loop: {e}")
            #    time.sleep(60)
        else:
            logging.info("Bot is off, waiting for 1 minute.")
            print("Bot is off, waiting for 1 minute.")
            time.sleep(60)

if __name__ == "__main__":
    main()