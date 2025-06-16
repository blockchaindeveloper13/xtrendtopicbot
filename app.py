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

class SoliumBot:
    def __init__(self):
        self.twitter_clients = self.initialize_twitter_clients()
        self.grok_client = self.initialize_grok_client()
        self.scheduler = BackgroundScheduler(timezone="UTC")
        
    def initialize_twitter_clients(self):
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
    
    def initialize_grok_client(self):
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
    
    def generate_tweet_with_grok(self, account_name):
        try:
            prompts = {
                "X": (
                    "Create a professional English tweet for SoliumCoin starting with 'soliumcoin.com'. "
                    "Focus on blockchain innovation and technology. Mention the presale opportunity "
                    "and Web3 future. Keep it informative and engaging (220-240 chars). "
                    "End with 'Follow @soliumcoin'. No hashtags."
                ),
                "X2": (
                    "Write a community-focused English tweet for SoliumCoin starting with 'soliumcoin.com'. "
                    "Talk about the growing SoliumArmy and how to join. Use friendly tone (220-240 chars). "
                    "End with 'Follow @soliumcoin'. No hashtags."
                ),
                "X3": (
                    "Create an exciting English tweet for SoliumCoin starting with 'soliumcoin.com'. "
                    "Highlight the presale and potential. Use energetic but realistic tone (220-240 chars). "
                    "End with 'Follow @soliumcoin'. No hashtags."
                )
            }
            
            response = self.grok_client.chat.completions.create(
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
            # Fallback olmadan hata fırlat
            raise Exception(f"Grok tweet oluşturulamadı: {e}")
    
    def post_tweet(self, account_name):
        try:
            client = self.twitter_clients[account_name]
            
            # Kimlik doğrulama testi
            me = client.get_me()
            logging.info(f"{account_name} kimlik doğrulama başarılı, kullanıcı: {me.data.username}")
            
            # Tweet içeriği üret
            tweet_text = self.generate_tweet_with_grok(account_name)
            response = client.create_tweet(text=tweet_text)
            logging.info(f"{account_name} tweet gönderildi, ID: {response.data['id']}, Tweet: {tweet_text}")
            
            return True
        
        except Exception as e:
            logging.error(f"{account_name} tweet gönderim hatası: {e}")
            return False
    
    def schedule_tweets(self):
        for account_name in self.twitter_clients.keys():
            self.scheduler.add_job(
                self.post_tweet,
                'interval',
                seconds=11520,  # 96 dk, 15 tweet/gün
                args=[account_name],
                id=f"tweet_job_{account_name}",
                jitter=300  # 5 dk rastgele gecikme
            )
        
        self.scheduler.start()
        logging.info("Tweet zamanlayıcı başlatıldı")
    
    def run_initial_tweets(self):
        logging.info("Başlangıç tweetleri gönderiliyor...")
        for account_name in self.twitter_clients.keys():
            success = False
            retries = 3
            
            while not success and retries > 0:
                try:
                    success = self.post_tweet(account_name)
                    if not success:
                        retries -= 1
                        time.sleep(10)
                except Exception as e:
                    logging.error(f"{account_name} başlangıç tweeti gönderilemedi (kalan deneme: {retries}): {e}")
                    retries -= 1
                    time.sleep(10)
    
    def start(self):
        logging.info("Solium Bot başlatılıyor...")
        self.run_initial_tweets()
        self.schedule_tweets()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("Bot durduruldu")
            self.scheduler.shutdown()

if __name__ == "__main__":
    try:
        bot = SoliumBot()
        bot.start()
    except Exception as e:
        logging.error(f"Ölümcül hata: {e}")
