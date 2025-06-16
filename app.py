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

# Sabit anahtarlar (yeni Generate edilenler)
CLIENT_ID = "dkdaZVhiVlYzd2EtcUFpMDZOS1A6MTpjaQ"
CLIENT_SECRET = "CMmIPHRswpHNxXlr3VJpOoMbICrKuOGD1pYD0LJfEnHPp8gnp8"
API_KEY = "TJE6mnAVYn2fSWzNisHP0oRbQ"
API_SECRET = "1BfFOKXXJO7L0jEAw1wAQ2fFGJbJAgrGiRR2r8dn1l6Of2h6SR"
ACCESS_TOKEN = "1934310422313947136-nz9YBN2Ibbj2Xqr9ILBBr49Hm9ndpR"
ACCESS_TOKEN_SECRET = "KG3gpiuEPZE4uyjZubCWkuIUL1lmDH9WaNq0TL2B48IzR"

# Twitter API v2 istemcisi (OAuth 2.0)
try:
    logging.debug(f"Client ID: {CLIENT_ID[:5]}... (gizlendi)")
    logging.debug(f"Client Secret: {CLIENT_SECRET[:5]}... (gizlendi)")
    logging.debug(f"API Key: {API_KEY[:5]}... (gizlendi)")
    logging.debug(f"API Secret: {API_SECRET[:5]}... (gizlendi)")
    logging.debug(f"Access Token: {ACCESS_TOKEN[:5]}... (gizlendi)")
    logging.debug(f"Access Token Secret: {ACCESS_TOKEN_SECRET[:5]}... (gizlendi)")
    
    client_x = tweepy.Client(
        consumer_key=CLIENT_ID,
        consumer_secret=CLIENT_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    logging.info("Twitter API v2 istemcisi başarıyla başlatıldı")
    user = client_x.get_me()
    logging.info(f"Kimlik doğrulama başarılı, kullanıcı: {user.data.username}")
except Exception as e:
    logging.error(f"Twitter API v2 istemcisi başlatılamadı: {e}")
    raise

# Sabitler
TEST_TWEET = "Bu bir test mesajıdır"

def check_rate_limit(client):
    try:
        response = client.get_me()
        rate_limit = response.meta.get('x-rate-limit-remaining', None)
        reset_time = response.meta.get('x-rate-limit-reset', time.time() + 3600)
        logging.info(f"Rate limit kalan: {rate_limit}, sıfırlanma: {datetime.fromtimestamp(reset_time, timezone.utc)}")
        return rate_limit, reset_time
    except Exception as e:
        logging.error(f"Rate limit kontrolü başarısız: {e}")
        return None, None

def post_tweet():
    try:
        rate_limit, reset_time = check_rate_limit(client_x)
        if rate_limit == 0:
            wait_time = max(0, reset_time - time.time())
            logging.info(f"Rate limit aşıldı, {wait_time/3600:.1f} saat bekleniyor")
            time.sleep(wait_time)

        logging.info(f"Tweet gönderiliyor: {TEST_TWEET}")
        response = client_x.create_tweet(text=TEST_TWEET)
        logging.info(f"Tweet gönderildi, ID: {response.data['id']}, Tweet: {TEST_TWEET}")
    except tweepy.TweepyException as e:
        error_details = getattr(e, 'api_errors', str(e))
        if "401" in str(e):
            logging.error(f"Kimlik doğrulama hatası: {e}, Detay: {error_details}")
        elif "403" in str(e):
            logging.error(f"Yazma izni hatası: {e}, Detay: {error_details}")
        elif "429" in str(e):
            logging.error(f"Oran sınırı aşıldı: {e}, Detay: {error_details}")
            time.sleep(3600)
        else:
            logging.error(f"Tweet hatası: {e}, Detay: {error_details}")
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
