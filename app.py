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
os.environ["X_API_KEY"] = "FSuTbPdww7NRgJYvnKjANUX5Y"
os.environ["X_SECRET_KEY"] = "x9InJfYGu49pUlRTf5dmIIZwEUCOiSNYsXwVHIS8ZlnKfBrVwu"
os.environ["X_ACCESS_TOKEN"] = "1667664491675361281-BQzHkPKAppuT3OHR7XIeYIFxGKfttr"
os.environ["X_ACCESS_SECRET"] = "2kYv9KzfZfqWlk1vVY3H8qr4m9tUegW5ovrZCt7yO4o3d"

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
        
        # Benzersiz tweet içeriği (zaman damgası ile)
        timestamp = datetime.now(timezone(timedelta(hours=3))).strftime("%H:%M:%S")
        tweet_text = f"Bu bir test mesajıdır - {timestamp}"
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
