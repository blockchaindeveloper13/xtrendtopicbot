import requests
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

# Sabit anahtarlar (OAuth 2.0 için Access Token)
CLIENT_ID = "OGhxeFZQQzJwSkFZdUw1M3FXQlU6MTpjaQ"
CLIENT_SECRET = "GKULoRy2CCdO6R-My_8wf5etL46zDIoEVqotNakXrBRoJN5FE9"
ACCESS_TOKEN = "1934310422313947136-5XtKb3i2TlbeiH7lR68C2DnePaeuAJ"  # Verdiğin token, OAuth 2.0 için test edilecek

# Twitter API v2 endpoint'leri
BASE_URL = "https://api.twitter.com/2"
GET_ME_URL = f"{BASE_URL}/users/me"
POST_TWEET_URL = f"{BASE_URL}/tweets"

# Headers for OAuth 2.0
def get_oauth2_headers():
    return {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

# Test tweet'i gönder
def post_tweet():
    try:
        # Kimlik doğrulama testi (get_me)
        headers = get_oauth2_headers()
        logging.info(f"Kimlik doğrulama isteği yapılıyor: {GET_ME_URL}")
        response = requests.get(GET_ME_URL, headers=headers)
        logging.debug(f"Kimlik doğrulama yanıtı: {response.status_code} - {response.text}")
        if response.status_code == 200:
            logging.info(f"Kimlik doğrulama başarılı, kullanıcı: {response.json().get('data', {}).get('username')}")
        else:
            logging.error(f"Kimlik doğrulama hatası: {response.status_code} - {response.text}")
            return

        # Tweet gönder
        tweet_data = {"text": "Bu bir test mesajıdır"}
        headers = get_oauth2_headers()
        logging.info(f"Tweet gönderiliyor: {tweet_data['text']}")
        response = requests.post(POST_TWEET_URL, headers=headers, json=tweet_data)
        logging.debug(f"Tweet yanıtı: {response.status_code} - {response.text}")
        if response.status_code == 201:
            tweet_id = response.json().get('data', {}).get('id')
            logging.info(f"Tweet gönderildi, ID: {tweet_id}, Tweet: {tweet_data['text']}")
        else:
            logging.error(f"Tweet hatası: {response.status_code} - {response.text}")
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
