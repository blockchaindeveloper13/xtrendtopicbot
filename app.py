import os
import tweepy
import time
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import random
import requests
from openai import OpenAI  # Grok istemcisi için gerekli
import httpx  # Grok istemcisi için gerekli

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
    "#Solium", "#SoliumArmy", "#Web3", "#DeFi", "#Crypto", "#Cryptocurrency",
    "#Cryptocurrencies", "#Blockchain", "#BlockchainTechnology", "#CryptoNews",
    "#CryptocurrencyNews", "#CryptoMarket", "#Cryptotrading", "#CryptoInvestor",
    "#Cryptoworld", "#Cryptolife", "#CryptoCommunity", "#Cryptomemes", "#Bitcoin",
    "#BTC", "#Ethereum", "#ETH", "#Binance", "#BNB", "#Solana", "#SOL", "#Ripple",
    "#XRP", "#Litecoin", "#LTC", "#Dogecoin", "#DOGE", "#Cardano", "#ADA",
    "#Polkadot", "#DOT", "#Chainlink", "#LINK", "#DAO", "#Decentralized",
    "#DecentralizedFinance", "#YieldFarming", "#Staking", "#NFT", "#NFTs",
    "#NFTArt", "#Metaverse", "#CryptoArt", "#NFTCommunity", "#Trading",
    "#CryptocurrencyTrading", "#Altcoin", "#Altcoins", "#HODL", "#CryptoExchange",
    "#BinanceFutures", "#Coinbase", "#KuCoin", "#Kraken", "#CryptoTwitter",
    "#BitcoinCommunity", "#EthereumCommunity", "#SolanaCommunity", "#BSC",
    "#MemeCoin", "#CryptoEvents", "#Invest", "#Investing", "#Investment",
    "#FinancialFreedom", "#PassiveIncome", "#CryptoInvesting", "#BullRun",
    "#BearMarket", "#Dubai", "#Innovation"
]

# Twitter API v2 istemcilerini başlat
try:
    client_x = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_SECRET_KEY"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET")
    )
    logging.info("X API istemcisi başarıyla başlatıldı")
except Exception as e:
    logging.error(f"X API istemcisi başlatılamadı: {e}")
    raise

try:
    client_x2 = tweepy.Client(
        consumer_key=os.getenv("X2_API_KEY"),
        consumer_secret=os.getenv("X2_SECRET_KEY"),
        access_token=os.getenv("X2_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X2_ACCESS_SECRET")
    )
    logging.info("X2 API istemcisi başarıyla başlatıldı")
except Exception as e:
    logging.error(f"X2 API istemcisi başlatılamadı: {e}")
    raise

try:
    client_x3 = tweepy.Client(
        consumer_key=os.getenv("X3_API_KEY"),
        consumer_secret=os.getenv("X3_SECRET_KEY"),
        access_token=os.getenv("X3_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X3_ACCESS_SECRET")
    )
    logging.info("X3 API istemcisi başarıyla başlatıldı")
except Exception as e:
    logging.error(f"X3 API istemcisi başlatılamadı: {e}")
    raise

# Grok istemcisi
try:
    client_grok = OpenAI(api_key=os.getenv("GROK_API_KEY"), base_url="https://api.x.ai/v1", http_client=httpx.Client(proxies=None))
    logging.info("Grok istemcisi başarıyla başlatıldı")
except Exception as e:
    logging.error(f"Grok istemcisi başlatılamadı: {e}")
    raise

# Grok API ile tweet içeriği üret
def generate_tweet_content(account_name):
    try:
        response = client_grok.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": f"You are a helpful assistant creating tweets for SoliumCoin for account {account_name}."},
                {"role": "user", "content": (
                    "Generate a unique, engaging English tweet for SoliumCoin that starts with 'soliumcoin.com', "
                    "invites people to join the presale, emphasizes Web3's future, and avoids exaggerated promises "
                    "(e.g., no 'get rich quick' claims). Use a calm, persuasive tone like 'Web3's future is here, "
                    "don't miss out!' or 'Join us, or we're one person short!'. End with 'Follow @soliumcoin'. "
                    "Do not include hashtags in the content, they will be added separately. Optimize the content to be minimum 220 characters and maximum 240 characters."
                )}
            ],
            max_tokens=100,
            temperature=0.7
        )
        tweet = response.choices[0].message.content.strip()
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
        logging.error(f"Grok tweet üretimi hatası (Hesap: {account_name}): {e}")
        return (
            "soliumcoin.com Join the Web3 future with our presale! Be part of something big. Follow @soliumcoin "
            + " ".join(random.sample(HASHTAGS, 3))
        )

# Tweet gönder (tek tweet, 280 karakter)
def post_tweet(account_name, client):
    logging.info(f"{account_name} için tweet gönderimi başlatılıyor...")
    try:
        # Kimlik doğrulama testi
        me = client.get_me()
        logging.info(f"{account_name} kimlik doğrulama başarılı, kullanıcı: {me.data.username}")
        
        # Tek tweet at (280 karakter)
        logging.info(f"{account_name} tweet hazırlanıyor...")
        tweet_text = generate_tweet_content(account_name)
        logging.info(f"{account_name} tweet içeriği: {tweet_text}, Karakter sayısı: {len(tweet_text)}")
        response = client.create_tweet(text=tweet_text)
        logging.info(f"{account_name} tweet gönderildi, ID: {response.data['id']}, Tweet: {tweet_text}, Karakter sayısı: {len(tweet_text)}")
    except tweepy.errors.Forbidden as e:
        logging.error(f"{account_name} yetki hatası (403 Forbidden), Twitter Developer Portal’da Read/Write izinlerini ve hesap kısıtlamalarını kontrol et. Tweet içeriği: {tweet_text if 'tweet_text' in locals() else 'N/A'}, Hata: {e}")
    except tweepy.errors.TooManyRequests as e:
        logging.warning(f"{account_name} API limitine takıldı, 96 dakika sonra tekrar denenecek: {e}")
        time.sleep(5760)  # 96 dakika bekle
        post_tweet(account_name, client)  # Tekrar dene
    except Exception as e:
        logging.error(f"{account_name} tweet gönderim hatası, Tweet içeriği: {tweet_text if 'tweet_text' in locals() else 'N/A'}, Hata: {e}")

# Tweet zamanlama
def schedule_tweets():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        post_tweet,
        'interval',
        seconds=5760,  # 96 dk, 15 tweet/gün
        args=["X", client_x],
        id="tweet_job_X",
        jitter=300
    )
    scheduler.add_job(
        post_tweet,
        'interval',
        seconds=5760,  # 96 dk, 15 tweet/gün
        args=["X2", client_x2],
        id="tweet_job_X2",
        jitter=300
    )
    scheduler.add_job(
        post_tweet,
        'interval',
        seconds=5760,  # 96 dk, 15 tweet/gün
        args=["X3", client_x3],
        id="tweet_job_X3",
        jitter=300
    )
    scheduler.start()

def main():
    logging.info("Solium Bot başlatılıyor...")
    # İlk tweet çağrısını kaldırdım, sadece scheduler çalışacak
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
