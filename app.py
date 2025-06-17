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

# Ortam değişkenleri (sadece X hesabı için)
required_env_vars = ["X_API_KEY", "X_SECRET_KEY", "X_ACCESS_TOKEN", "X_ACCESS_SECRET", "GROK_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        logging.error(f"Ortam değişkeni eksik: {var}")
        exit(1)

# Twitter API v2 istemcisi (sadece X)
try:
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_SECRET_KEY"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET")
    )
    logging.info("Twitter/X API istemcisi başarıyla başlatıldı")
except Exception as e:
    logging.error(f"Twitter/X API istemcisi başlatılamadı: {e}")
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
        tweet = f"{tweet} {' '.join(selected_hashtags)}"
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
            return generate_tweet_content()  # Tekrar dene
        logging.error(f"Grok API hatası: {e}")
        return (
            "soliumcoin.com Join the Web3 future with our presale! Be part of something big. Follow @soliumcoin "
            + " ".join(random.sample(HASHTAGS, 3))
        )
    except Exception as e:
        logging.error(f"Grok tweet üretimi hatası: {e}")
        return (
            "soliumcoin.com Join the Web3 future with our presale! Be part of something big. Follow @soliumcoin "
            + " ".join(random.sample(HASHTAGS, 3))
        )

# Tweet gönder
def post_tweet():
    try:
        tweet_text = generate_tweet_content()
        response = client.create_tweet(text=tweet_text)
        logging.info(f"X tweet gönderildi, ID: {response.data['id']}, Tweet: {tweet_text}")
    except tweepy.errors.TooManyRequests as e:
        reset_time = int(e.response.headers.get('x-rate-limit-reset', 0))
        wait_time = max(0, reset_time - time.time()) + 10
        logging.warning(f"Twitter API oran sınırı aşıldı, {wait_time} saniye bekleniyor")
        time.sleep(wait_time)
        post_tweet()  # Tekrar dene
    except Exception as e:
        logging.error(f"X tweet gönderim hatası: {e}")

# Tweet zamanlama
def schedule_tweets():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        post_tweet,
        'interval',
        seconds=5760,  # 96 dk, ~15 tweet/gün
        id="tweet_job_X",
        jitter=300  # 5 dk rastgele gecikme
    )
    scheduler.start()
    logging.info("Tweet zamanlayıcı başlatıldı")

def main():
    logging.info("Solium Bot başlatılıyor (tek hesap: X)...")
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
