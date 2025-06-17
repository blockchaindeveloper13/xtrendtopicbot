import os
import tweepy
import time
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import random
import requests

# Günlük kaydı (Türkiye saati)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('solium_bot.log'), logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
logging.Formatter.converter = lambda *args: datetime.now(timezone(timedelta(hours=3))).timetuple()

# Hashtag havuzu
HASHTAGS = [
    "#SoliumCoin", "#Web3", "#Crypto", "#Blockchain",
    "#Presale", "#DeFi", "#CryptoFuture", "#JoinTheFuture"
]

# Ortam değişkenleri (sadece X3)
required_env_vars = ["X3_API_KEY", "X3_SECRET_KEY", "X3_ACCESS_TOKEN", "X3_ACCESS_SECRET", "GROK_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        logging.error(f"Ortam değişkeni eksik: {var}")
        exit(1)

# Twitter API v2 istemcisi (sadece X3)
try:
    client = tweepy.Client(
        consumer_key=os.getenv("X3_API_KEY"),
        consumer_secret=os.getenv("X3_SECRET_KEY"),
        access_token=os.getenv("X3_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X3_ACCESS_SECRET")
    )
    logging.info("X3 Twitter API istemcisi başarıyla başlatıldı")
except Exception as e:
    logging.error(f"X3 Twitter API istemcisi başlatılamadı: {e}")
    raise

# Grok API ile tweet içeriği üret
def generate_tweet_content():
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('GROK_API_KEY')}",
            "Content-Type": "application/json"
        }
        prompt = (
            "Generate a unique, engaging English tweet for SoliumCoin that starts with 'soliumcoin.com', "
            "invites people to join the presale, emphasizes Web3's future, and avoids exaggerated promises "
            "(e.g., no 'get rich quick' claims). Use a calm, persuasive tone like 'Web3's future is here, "
            "don't miss out!' or 'Join us!'. End with 'Follow @soliumcoin'. "
            "Do not include hashtags in the content, they will be added separately. Keep it under 240 characters."
        )
        response = requests.post(
            "https://api.x.ai/v1/grok/generate",
            headers=headers,
            json={"prompt": prompt}
        )
        response.raise_for_status()
        tweet = response.json().get("text", "").strip()
        selected_hashtags = random.sample(HASHTAGS, 3)
        tweet = f"{tweet} {' '.join(selected_hashtags)} (#{random.randint(1000, 9999)})"
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
        logging.info("Grok API ile tweet içeriği üretildi")
        return tweet
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            reset_time = int(e.response.headers.get('x-rate-limit-reset', 0))
            wait_time = max(0, reset_time - time.time()) + 10
            logging.warning(f"Grok API oran sınırı aşıldı, {wait_time} saniye bekleniyor")
            time.sleep(wait_time)
            return generate_tweet_content()
        logging.error(f"Grok API hatası: {e}")
        return (
            f"soliumcoin.com Join the Web3 future with our presale! Be part of something big. Follow @soliumcoin "
            + f"{' '.join(random.sample(HASHTAGS, 3))} (#{random.randint(1000, 9999)})"
        )
    except Exception as e:
        logging.error(f"Grok tweet üretimi hatası: {e}")
        return (
            f"soliumcoin.com Join the Web3 future with our presale! Be part of something big. Follow @soliumcoin "
            + f"{' '.join(random.sample(HASHTAGS, 3))} (#{random.randint(1000, 9999)})"
        )

# Tweet önbelleği
tweet_cache = []
def get_tweet_content():
    global tweet_cache
    if not tweet_cache:
        tweet_cache = [generate_tweet_content() for _ in range(5)]  # 5 tweet önbelleğe al
    return tweet_cache.pop()

# Tweet gönder
def post_tweet():
    try:
        tweet_text = get_tweet_content()
        response = client.create_tweet(text=tweet_text)
        logging.info(f"X3 tweet gönderildi, ID: {response.data['id']}, Tweet: {tweet_text}")
        logging.debug(f"API Başlıkları: {response.headers}")
    except tweepy.errors.TooManyRequests as e:
        headers = e.response.headers
        reset_time = int(headers.get('x-rate-limit-reset', 0))
        wait_time = max(0, reset_time - time.time()) + 10
        logging.warning(f"Twitter API oran sınırı aşıldı, X3 için {wait_time} saniye bekleniyor. "
                       f"Kalan App Limit: {headers.get('x-app-limit-24hour-remaining')}, "
                       f"Kalan User Limit: {headers.get('x-user-limit-24hour-remaining')}")
        time.sleep(wait_time)
        post_tweet()
    except Exception as e:
        logging.error(f"X3 tweet gönderim hatası: {e}")

# Tweet zamanlama
def schedule_tweets():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        post_tweet,
        'interval',
        seconds=5000,  # 90 dk, ~16 tweet/gün
        id="tweet_job_X3",
        jitter=300  # 5 dk rastgele gecikme
    )
    scheduler.start()
    logging.info("X3 için tweet zamanlayıcı başlatıldı")

def main():
    logging.info("Solium Bot başlatılıyor (tek hesap: X3)...")
    post_tweet()  # İlk tweet'i hemen gönder
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
