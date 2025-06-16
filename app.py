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

# Ortam değişkenlerini set et (test için, production’da Heroku Config Vars’tan çek)
os.environ["X_API_KEY"] 
os.environ["X_SECRET_KEY"] 
os.environ["X_ACCESS_TOKEN"] 
os.environ["X_ACCESS_SECRET"] 
os.environ["X2_API_KEY"] 
os.environ["X2_SECRET_KEY"] 
os.environ["X2_ACCESS_TOKEN"] 
os.environ["X2_ACCESS_SECRET"] 
os.environ["X3_API_KEY"] 
os.environ["X3_SECRET_KEY"] 
os.environ["X3_ACCESS_TOKEN"] 
os.environ["X3_ACCESS_SECRET"] 
os.environ["GROK_API_KEY"] 

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

# Grok istemcisi
try:
    client_grok = OpenAI(api_key=os.getenv("GROK_API_KEY"), base_url="https://api.x.ai/v1", http_client=httpx.Client(proxies=None))
    logging.info("Grok istemcisi başarıyla başlatıldı")
except Exception as e:
    logging.error(f"Grok istemcisi başlatılamadı: {e}")
    raise

# Grok API ile tweet içeriği üret
def generate_tweet_content():
    try:
        response = client_grok.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": "You are a helpful assistant creating tweets for SoliumCoin."},
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
        tweet = f"{tweet} {' '.join(selected_hashtags)}"
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."  # Twitter karakter limiti
        return tweet
    except Exception as e:
        logging.error(f"Grok tweet üretimi hatası: {e}")
        return (
            "soliumcoin.com Join the Web3 future with our presale! Be part of something big. Follow @soliumcoin "
            + " ".join(random.sample(HASHTAGS, 3))
        )

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
    except Exception as e:
        logging.error(f"{account_name} tweet gönderim hatası: {e}")

# Tweet zamanlama
def schedule_tweets():
    scheduler = BackgroundScheduler(timezone="UTC")
    for account_name, client in clients.items():
        scheduler.add_job(
            post_tweet,
            'interval',
            seconds=11520,  # 96 dk, 15 tweet/gün
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
