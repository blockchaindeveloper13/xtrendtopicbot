import requests
import oauthlib.oauth1
import time
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from urllib.parse import urlencode

# Günlük kaydı (Türkiye saati, detaylı loglama)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('solium_bot.log'), logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
logging.Formatter.converter = lambda *args: datetime.now(timezone(timedelta(hours=3))).timetuple()

# Sabit anahtarlar (yeni Generate edilenler)
CLIENT_ID = "OGhxeFZQQzJwSkFZdUw1M3FXQlU6MTpjaQ"
CLIENT_SECRET = "GKULoRy2CCdO6R-My_8wf5etL46zDIoEVqotNakXrBRoJN5FE9"
ACCESS_TOKEN = "1934310422313947136-5XtKb3i2TlbeiH7lR68C2DnePaeuAJ"
ACCESS_TOKEN_SECRET = "7w9o3C35gVv1EMpdaczIJkRsqCFNRPeXmkPvSus6xXukC"

# Twitter API v2 endpoint'leri
BASE_URL = "https://api.twitter.com/2"
GET_ME_URL = f"{BASE_URL}/users/me"
POST_TWEET_URL = f"{BASE_URL}/tweets"

# OAuth 1.0a authentication (form-urlencoded body ile doğru imza)
def get_oauth1_headers(url, method="GET", body=None):
    auth = oauthlib.oauth1.Client(
        client_key=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET
    )
    if body is None:
        body = ""
    elif isinstance(body, dict):
        body = urlencode(body)
    uri, headers, body = auth.sign(url, method, body=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return headers

# Test tweet'i gönder
def post_tweet():
    try:
        # Kimlik doğrulama testi (get_me)
        headers = get_oauth1_headers(GET_ME_URL)
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
        headers = get_oauth1_headers(POST_TWEET_URL, method="POST", body=tweet_data)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        logging.info(f"Tweet gönderiliyor: {tweet_data['text']}")
        response = requests.post(POST_TWEET_URL, headers=headers, data=urlencode(tweet_data))
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
