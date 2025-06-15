import tweepy
import os
import time
import random
import logging
import httpx
from datetime import datetime, timezone, timedelta
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

# Günlük kaydı (Türkiye saati)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('solium_bot.log'), logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
logging.Formatter.converter = lambda *args: datetime.now(timezone(timedelta(hours=3))).timetuple()

# Çevre değişkenleri kontrol (3 hesap için)
required_env_vars = [
    "ACCOUNT1_X_API_KEY", "ACCOUNT1_X_SECRET_KEY", "ACCOUNT1_X_ACCESS_TOKEN", "ACCOUNT1_X_ACCESS_SECRET",
    "ACCOUNT2_X_API_KEY", "ACCOUNT2_X_SECRET_KEY", "ACCOUNT2_X_ACCESS_TOKEN", "ACCOUNT2_X_ACCESS_SECRET",
    "ACCOUNT3_X_API_KEY", "ACCOUNT3_X_SECRET_KEY", "ACCOUNT3_X_ACCESS_TOKEN", "ACCOUNT3_X_ACCESS_SECRET",
    "GROK_API_KEY"
]
for var in required_env_vars:
    if not os.getenv(var):
        logging.error(f"Çevre değişkeni eksik: {var}")
        raise EnvironmentError(f"Çevre değişkeni eksik: {var}")

# 3 hesap için istemciler
accounts = [
    {
        "client": tweepy.Client(
            consumer_key=os.getenv("ACCOUNT1_X_API_KEY"),
            consumer_secret=os.getenv("ACCOUNT1_X_SECRET_KEY"),
            access_token=os.getenv("ACCOUNT1_X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("ACCOUNT1_X_ACCESS_SECRET")
        ),
        "name": "Account1"
    },
    {
        "client": tweepy.Client(
            consumer_key=os.getenv("ACCOUNT2_X_API_KEY"),
            consumer_secret=os.getenv("ACCOUNT2_X_SECRET_KEY"),
            access_token=os.getenv("ACCOUNT2_X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("ACCOUNT2_X_ACCESS_SECRET")
        ),
        "name": "Account2"
    },
    {
        "client": tweepy.Client(
            consumer_key=os.getenv("ACCOUNT3_X_API_KEY"),
            consumer_secret=os.getenv("ACCOUNT3_X_SECRET_KEY"),
            access_token=os.getenv("ACCOUNT3_X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("ACCOUNT3_X_ACCESS_SECRET")
        ),
        "name": "Account3"
    }
]

# Grok istemcisi
try:
    client_grok = OpenAI(api_key=os.getenv("GROK_API_KEY"), base_url="https://api.x.ai/v1", http_client=httpx.Client(proxies=None))
    logging.info("Grok istemcisi başarıyla başlatıldı")
except Exception as e:
    logging.error(f"Grok istemcisi başlatılamadı: {e}")
    raise

# Sabitler
WEBSITE_URL = "https://soliumcoin.com"
SALE_MESSAGE = f" Join with BNB now via Binance Web3 Wallet, KuCoin Web3 Wallet, or MetaMask! Explore: {WEBSITE_URL}"
TEST_TWEET = f"{WEBSITE_URL} Test tweet for Solium Coin! @soliumcoin {SALE_MESSAGE} #Solium #Web3 #Crypto"

def check_rate_limit(client):
    try:
        response = client.get_me()
        rate_limit = response.meta.get('x-rate-limit-remaining', None)
        reset_time = response.meta.get('x-rate-limit-reset', time.time() + 3600)
        if rate_limit is not None:
            logging.info(f"Rate limit kalan: {rate_limit}, sıfırlanma: {datetime.fromtimestamp(reset_time, timezone.utc)}")
        return rate_limit, reset_time
    except Exception as e:
        logging.error(f"Rate limit kontrolü başarısız: {e}")
        return None, None

def post_tweet():
    for acc_idx, account in enumerate(accounts):
        try:
            rate_limit, reset_time = check_rate_limit(account["client"])
            if rate_limit == 0:
                wait_time = max(0, reset_time - time.time())
                logging.info(f"{account['name']} rate limit aşıldı, {wait_time/3600:.1f} saat bekleniyor")
                time.sleep(wait_time)

            logging.info(f"{account['name']} tweet gönderiliyor...")
            user = account["client"].get_me()
            logging.info(f"{account['name']} authentication successful, user: {user.data.username}")

            account["client"].create_tweet(text=TEST_TWEET)
            logging.info(f"{account['name']} posted test tweet: {TEST_TWEET}")
        except tweepy.TweepyException as e:
            error_details = getattr(e, 'api_errors', str(e))
            if "401" in str(e):
                logging.error(f"{account['name']} kimlik doğrulama hatası: {e}, Detay: {error_details}")
            elif "403" in str(e):
                logging.error(f"{account['name']} yazma izni hatası: {e}, Detay: {error_details}")
            elif "429" in str(e):
                logging.error(f"{account['name']} oran sınırı aşıldı: {e}, Detay: {error_details}")
                time.sleep(3600)
            else:
                logging.error(f"{account['name']} tweet hatası: {e}, Detay: {error_details}")

def schedule_tweets():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(post_tweet, 'interval', seconds=5760)  # 96 dk, 15 tweet/gün
    scheduler.start()

def main():
    logging.info("Solium Bot başlatılıyor...")
    post_tweet()  # İlk tweet
    schedule_tweets()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Bot durduruldu")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Ölümcül hata: {e}")
