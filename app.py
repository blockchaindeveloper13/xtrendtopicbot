import tweepy
import time
import os
import logging

# Logging ayarı
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config Vars’tan anahtarları çek (OAuth 2.0 için)
accounts = [
    {
        "client_id": os.environ.get("ACCOUNT1_CLIENT_ID", ""),
        "client_secret": os.environ.get("ACCOUNT1_CLIENT_SECRET", ""),
        "access_token": os.environ.get("ACCOUNT1_ACCESS_TOKEN", ""),
        "refresh_token": os.environ.get("ACCOUNT1_REFRESH_TOKEN", "")  # Opsiyonel, yenileme için
    },
    {
        "client_id": os.environ.get("ACCOUNT2_CLIENT_ID", ""),
        "client_secret": os.environ.get("ACCOUNT2_CLIENT_SECRET", ""),
        "access_token": os.environ.get("ACCOUNT2_ACCESS_TOKEN", ""),
        "refresh_token": os.environ.get("ACCOUNT2_REFRESH_TOKEN", "")  # Opsiyonel
    },
    {
        "client_id": os.environ.get("ACCOUNT3_CLIENT_ID", ""),
        "client_secret": os.environ.get("ACCOUNT3_CLIENT_SECRET", ""),
        "access_token": os.environ.get("ACCOUNT3_ACCESS_TOKEN", ""),
        "refresh_token": os.environ.get("ACCOUNT3_REFRESH_TOKEN", "")  # Opsiyonel
    }
]

# Deneme tweet’i
TEST_TWEET = "Test tweet for Solium Coin! @soliumcoin https://bit.ly/3HHUPTQ #Solium #Web3 #Crypto"

def send_test_tweet():
    for acc_idx, account in enumerate(accounts):
        if not all([account["client_id"], account["client_secret"], account["access_token"]]):
            logger.error(f"Missing API credentials for account {acc_idx}: {account}")
            continue

        try:
            # OAuth 2.0 ile client credentials
            client = tweepy.Client(
                consumer_key=account["client_id"],
                consumer_secret=account["client_secret"],
                access_token=account["access_token"],
                # refresh_token=account["refresh_token"]  # Eğer varsa
            )
            
            # Kullanıcı doğrulama
            user = client.get_me()
            logger.info(f"Authentication successful for account {acc_idx}, user: {user.data.username}")
            
            # Tweet at
            client.create_tweet(text=TEST_TWEET)
            logger.info(f"Account {acc_idx} posted test tweet: {TEST_TWEET}")
        except tweepy.errors.Unauthorized as e:
            logger.error(f"Authentication failed for account {acc_idx}: {str(e)}, credentials: {account}")
        except tweepy.errors.Forbidden as e:
            logger.error(f"Tweet error for account {acc_idx}: {str(e)}")
        except tweepy.errors.TweepyException as e:
            logger.error(f"API error for account {acc_idx}: {str(e)}")

if __name__ == "__main__":
    send_test_tweet()
    while True:
        time.sleep(3600)  # 1 saat bekle, tekrar deneme
