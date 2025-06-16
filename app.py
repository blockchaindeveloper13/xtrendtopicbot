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

# Twitter API v2 istemcilerini başlat
clients = {
    "X": None,
    "X2": None,
    "X3": None
}
for account_name in clients.keys():
    try:
        clients[account_name] = tweepy.Client(
            consumer_key=os.getenv(f"{account_name}_API_KEY"),
            consumer_secret=os.getenv(f"{account_name}_SECRET_KEY"),
            access_token=os.getenv(f"{account_name}_ACCESS_TOKEN"),
            access_token_secret=os.getenv(f"{account_name}_ACCESS_SECRET")
        )
        logging.info(f"{account_name} API istemcisi başarıyla başlatıldı")
    except Exception as e:
        logging.error(f"{account_name} API istemcisi başlatılamadı: {e}")
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
            "don't miss out!' or 'Join us, or we're one person short!'. End with 'Follow @soliumcoin'. "
            "Do not include hashtags in the content, they will be added separately. Aim for 260-270 characters to fill the tweet."
        )
        response = requests.post(
            "https://api.x.ai/v1/grok/generate",
            headers=headers,
            json={"prompt": prompt}
        )
        response.raise_for_status()
        tweet = response.json().get("text", "").strip()
        # Hashtag ekle
        selected_hashtags = random.sample(HASHTAGS, 3)
        hashtag_str = " ".join(selected_hashtags)
        tweet = f"{tweet} {hashtag_str}"
        # 280 karaktere doldur
        current_length = len(tweet)
        if current_length < 280:
            padding = " " * (280 - current_length - 3) + "..."
            tweet = f"{tweet}{padding}"
        elif current_length > 280:
            tweet = tweet[:277] + "..."  # Twitter karakter limiti
        return tweet
    except Exception as e:
        logging.error(f"Grok tweet üretimi hatası: {e}")
        default_tweet = (
            "soliumcoin.com Join the Web3 future with our presale! Be part of something big with SoliumCoin. "
            "The decentralized world is evolving, don’t miss your chance to shape it. Follow @soliumcoin "
        )
        selected_hashtags = random.sample(HASHTAGS, 3)
        hashtag_str = " ".join(selected_hashtags)
        tweet = f"{default_tweet}{hashtag_str}"
        current_length = len(tweet)
        if current_length < 280:
            padding = " " * (280 - current_length - 3) + "..."
            tweet = f"{tweet}{padding}"
        elif current_length > 280:
            tweet = tweet[:277] + "..."  # Twitter karakter limiti
        return tweet

# Tweet gönder
def post_tweet(account_name, client):
    try:
        # Kimlik doğrulama testi
        me = client.get_me()
        logging.info(f"{account_name} kimlik doğrulama başarılı, kullanıcı: {me.data.username}")
        
        # Tweet içeriği üret
        tweet_text = generate_tweet_content()
        response = client.create_tweet(text=tweet_text)
        logging.info(f"{account_name} tweet gönderildi, ID: {response.data['id']}, Tweet: {tweet_text}")
    except tweepy.errors.TooManyRequests as e:
        logging.warning(f"{account_name} API limitine takıldı, 96 dakika sonra tekrar denenecek: {e}")
        time.sleep(5760)  # 96 dakika bekle
        post_tweet(account_name, client)  # Tekrar dene
    except Exception as e:
        logging.error(f"{account_name} tweet gönderim hatası: {e}")

# Tweet zamanlama
def schedule_tweets():
    scheduler = BackgroundScheduler(timezone="UTC")
    for account_name, client in clients.items():
        scheduler.add_job(
            post_tweet,
            'interval',
            seconds=5760,  # 96 dk, 15 tweet/gün
            args=[account_name, client],
            id=f"tweet_job_{account_name}",
            jitter=300  # 5 dk rastgele gecikme
        )
    scheduler.start()

def main():
    logging.info("Solium Bot başlatılıyor...")
    for account_name, client in clients.items():
        post_tweet(account_name, client)
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
