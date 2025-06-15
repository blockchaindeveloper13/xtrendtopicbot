import tweepy
import time
import os
import logging

# Logging ayarı
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config Vars’tan anahtarları çek (sadece v1)
accounts = [
    {
        "api_key": os.environ.get("ACCOUNT1_API_KEY", ""),
        "api_secret": os.environ.get("ACCOUNT1_API_SECRET", ""),
        "access_token": os.environ.get("ACCOUNT1_ACCESS_TOKEN", ""),
        "access_token_secret": os.environ.get("ACCOUNT1_ACCESS_TOKEN_SECRET", ""),
    },
    {
        "api_key": os.environ.get("ACCOUNT2_API_KEY", ""),
        "api_secret": os.environ.get("ACCOUNT2_API_SECRET", ""),
        "access_token": os.environ.get("ACCOUNT2_ACCESS_TOKEN", ""),
        "access_token_secret": os.environ.get("ACCOUNT2_ACCESS_TOKEN_SECRET", ""),
    },
    {
        "api_key": os.environ.get("ACCOUNT3_API_KEY", ""),
        "api_secret": os.environ.get("ACCOUNT3_API_SECRET", ""),
        "access_token": os.environ.get("ACCOUNT3_ACCESS_TOKEN", ""),
        "access_token_secret": os.environ.get("ACCOUNT3_ACCESS_TOKEN_SECRET", ""),
    }
]

# Deneme tweet’i
TEST_TWEET = "Test tweet for Solium Coin! @soliumcoin https://bit.ly/3HHUPTQ #Solium #Web3 #Crypto"

def send_test_tweet():
    for acc_idx, account in enumerate(accounts):
        if not all([account["api_key"], account["api_secret"], account["access_token"], account["access_token_secret"]]):
            logger.error(f"Missing API credentials for account {acc_idx}: {account}")
            continue

        try:
            auth = tweepy.OAuthHandler(account["api_key"], account["api_secret"])
            auth.set_access_token(account["access_token"], account["access_token_secret"])
            api = tweepy.API(auth, wait_on_rate_limit=True)
            user = api.verify_credentials()
            logger.info(f"Authentication successful for account {acc_idx}, user: {user.screen_name}")
            
            api.update_status(status=TEST_TWEET)
            logger.info(f"Account {acc_idx} posted test tweet: {TEST_TWEET}")
        except tweepy.errors.Unauthorized as e:
            logger.error(f"Authentication failed for account {acc_idx}: {str(e)}, credentials: {account}")
        except tweepy.errors.TweepyException as e:
            logger.error(f"Tweet error for account {acc_idx}: {str(e)}")

if __name__ == "__main__":
    send_test_tweet()
    while True:
        time.sleep(3600)  # 1 saat bekle, tekrar deneme
