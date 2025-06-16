import os
import tweepy
import time
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import random
import httpx
from openai import OpenAI

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

# Twitter hesapları için API istemcileri
def initialize_twitter_clients():
    clients = {}
    accounts = ["X", "X2", "X3"]
    
    for account in accounts:
        try:
            clients[account] = tweepy.Client(
                consumer_key=os.getenv(f"{account}_API_KEY"),
                consumer_secret=os.getenv(f"{account}_SECRET_KEY"),
                access_token=os.getenv(f"{account}_ACCESS_TOKEN"),
                access_token_secret=os.getenv(f"{account}_ACCESS_SECRET")
            )
            logging.info(f"{account} Twitter istemcisi başarıyla başlatıldı")
        except Exception as e:
            logging.error(f"{account} Twitter istemcisi başlatılamadı: {e}")
            raise
    
    return clients

# Grok API istemcisi
def initialize_grok_client():
    try:
        client = OpenAI(
            api_key=os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
            http_client=httpx.Client(proxies=None)
        )
        logging.info("Grok istemcisi başarıyla başlatıldı")
        return client
    except Exception as e:
        logging.error(f"Grok istemcisi başlatılamadı: {e}")
        raise

# Grok API ile her hesap için farklı tweet içeriği üret
def generate_unique_tweet(account_name):
    try:
        prompts = {
            "X": (
                "Generate a unique, engaging English tweet for SoliumCoin that starts with 'soliumcoin.com', "
                "focuses on the technology and innovation behind the project. Emphasize the Web3 future and "
                "the benefits of joining early. Keep it professional and informative. "
                "End with 'Follow @soliumcoin'. Length: 220-240 characters."
            ),
            "X2": (
                "Create a friendly, community-focused tweet for SoliumCoin starting with 'soliumcoin.com'. "
                "Talk about the growing SoliumArmy and how everyone can be part of this movement. "
                "Use a welcoming tone. End with 'Follow @soliumcoin'. Length: 220-240 characters."
            ),
            "X3": (
                "Generate an exciting tweet for SoliumCoin starting with 'soliumcoin.com'. "
                "Highlight the presale opportunity and potential growth. Use an energetic but "
                "realistic tone. End with 'Follow @soliumcoin'. Length: 220-240 characters."
            )
        }
        
        response = client_grok.chat.completions.create(
            model="grok-1",
            messages=[{"role": "user", "content": prompts[account_name]}],
            max_tokens=150,
            temperature=0.7
        )
        
        tweet = response.choices[0].message.content.strip()
        
        # Hashtag ekle (3 rastgele hashtag)
        selected_hashtags = random.sample(HASHTAGS, 3)
        tweet = f"{tweet} {' '.join(selected_hashtags)}"
        
        # Karakter sınırı kontrolü
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
            
        return tweet
    
    except Exception as e:
        logging.error(f"Grok tweet üretimi hatası ({account_name}): {e}")
        # Fallback tweet
        fallback_tweets = {
            "X": "soliumcoin.com Building the future of Web3 with innovative blockchain solutions. Join us in shaping tomorrow's decentralized world. Follow @soliumcoin",
            "X2": "soliumcoin.com The SoliumArmy grows stronger every day! Be part of our thriving community and help build the future together. Follow @soliumcoin",
            "X3": "soliumcoin.com Don't miss the SoliumCoin presale! This is your chance to get in early on an exciting Web3 project with huge potential. Follow @soliumcoin"
        }
        return f"{fallback_tweets[account_name]} {' '.join(random.sample(HASHTAGS, 3))}"

# Tweet gönder
def post_tweet(account_name, client):
    try:
        # Kimlik doğrulama testi
        me = client.get_me()
        logging.info(f"{account_name} kimlik doğrulama başarılı, kullanıcı: {me.data.username}")
        
        # Tweet içeriği üret
        tweet_text = generate_unique_tweet(account_name)
        response = client.create_tweet(text=tweet_text)
        logging.info(f"{account_name} tweet gönderildi, ID: {response.data['id']}, Tweet: {tweet_text}")
    except Exception as e:
        logging.error(f"{account_name} tweet gönderim hatası: {e}")

# Tweet zamanlama
def schedule_tweets():
    scheduler = BackgroundScheduler(timezone="UTC")
    for account_name, client in twitter_clients.items():
        scheduler.add_job(
            post_tweet,
            'interval',
            seconds=11520,  # 96 dk, 15 tweet/gün
            args=[account_name, client],
            id=f"tweet_job_{account_name}",
            jitter=300  # 5 dk rastgele gecikme
        )
    scheduler.start()
    logging.info("Tweet zamanlayıcı başlatıldı")

def main():
    logging.info("Solium Bot başlatılıyor...")
    
    # İstemcileri başlat
    global twitter_clients, client_grok
    twitter_clients = initialize_twitter_clients()
    client_grok = initialize_grok_client()
    
    # Başlangıç tweet'leri gönder
    for account_name, client in twitter_clients.items():
        post_tweet(account_name, client)
    
    # Zamanlayıcıyı başlat
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
