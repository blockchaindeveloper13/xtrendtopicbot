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

# Ortam değişkenlerini ayarla (örnek, production'da .env dosyasından alınmalı)
os.environ["X_API_KEY"] = "OGhxeFZQQzJwSkFZdUw1M3FXQlU6MTpjaQ"
os.environ["X_SECRET_KEY"] = "GKULoRy2CCdO6R-My_8wf5etL46zDIoEVqotNakXrBRoJN5FE9"
os.environ["X_ACCESS_TOKEN"] = "1934310422313947136-5XtKb3i2TlbeiH7lR68C2DnePaeuAJ"
os.environ["X_ACCESS_SECRET"] = "7w9o3C35gVv1EMpdaczIJkRsqCFNRPeXmkPvSus6xXukC"

# Twitter API v2 istemcisi
try:
    client_x = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_SECRET_KEY"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET")
    )
    # Twitter API v1.1 istemcisi (isteğe bağlı, burada kullanmayacağız)
    auth = tweepy.OAuth1UserHandler(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_SECRET_KEY"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET")
    )
    api_x = tweepy.API(auth, wait_on_rate_limit=True)
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
