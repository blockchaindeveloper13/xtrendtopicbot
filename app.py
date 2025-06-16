import os
import tweepy
import time
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# Günlük kaydı (Türkiye saati, detaylı loglama)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('solium_bot.log'), logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
logging.Formatter.converter = lambda *args: datetime.now(timezone(timedelta(hours=3))).timetuple()

# Ortam değişkenlerini ayarla (production'da Heroku config'den alınmalı)
os.environ["X_API_KEY"] = "NyNa2C6mMipndxv4JaBDzQuff"
os.environ["X_SECRET_KEY"] = "LRd8CAm7ln3frXkCsLjQUh7j7imxf1Cqw2UZZk6jdC1rvEvVQC"
os.environ["X_ACCESS_TOKEN"] = "1934310422313947136-Vhy6BjfCO9l8wkdTQCpYi3UkpyhrHy"
os.environ["X_ACCESS_SECRET"] = "SnecmKFCYvPaIWbO7FGOHsaOTWyhWhiXoKMuNdl9orWeC"

# Twitter API v2 istemcisi
try:
    client_x = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_SECRET_KEY"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET")
    )
    logging.info("X API istemcileri başarıyla başlatıldı")
except Exception as e:
    logging.error(f"X API istemcileri başlatılamadı: {e}")
    raise

# Test tweet'i gönder
def post_tweet():
    try:
        # Kimlik doğrulama testi (kullanıcı bilgisi alma)
        me = client_x.get_me()
        logging.info(f"Kimlik doğrulama başarılı, kullanıcı: {me.data.username}")
        
        # Tweet gönder
        tweet_text = "Bu bir test mesajıdır"
        response = client_x.create_tweet(text=tweet_text)
        logging.info(f"Tweet gönderildi, ID: {response.data['id']}, Tweet: {tweet_text}")
    except Exception as e:
        logging.error(f"Genel hata: {e}")

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
