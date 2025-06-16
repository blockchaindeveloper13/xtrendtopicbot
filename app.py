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
    level=logging.INFO,
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

class TwitterRateLimitHandler:
    def __init__(self):
        self.account_limits = {
            "X": {"last_call": 0, "retry_after": 0},
            "X2": {"last_call": 0, "retry_after": 0},
            "X3": {"last_call": 0, "retry_after": 0}
        }
    
    def check_rate_limit(self, account_name):
        now = time.time()
        account = self.account_limits[account_name]
        if now < account["last_call"] + account["retry_after"]:
            wait_time = (account["last_call"] + account["retry_after"]) - now
            logging.warning(f"{account_name} için rate limit bekleme: {wait_time:.1f} saniye")
            time.sleep(wait_time)
        return True
    
    def update_rate_limit(self, account_name, headers):
        if headers and 'x-rate-limit-reset' in headers:
            reset_time = int(headers['x-rate-limit-reset'])
            now = time.time()
            self.account_limits[account_name] = {
                "last_call": now,
                "retry_after": max(reset_time - now, 15)  # En az 15 saniye beklet
            }

class SoliumBot:
    def __init__(self):
        self.rate_limit_handler = TwitterRateLimitHandler()
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
                    access_token_secret=os.getenv(f"{account}_ACCESS_SECRET"),
                    wait_on_rate_limit=True
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
                http_client=httpx.Client(
                    proxies=None,
                    timeout=30.0,
                    limits=httpx.Limits(max_connections=5, max_keepalive_connections=3)
                )
            )
            logging.info("Grok-3 istemcisi başarıyla başlatıldı")
            return client
        except Exception as e:
            logging.error(f"Grok istemcisi başlatılamadı: {e}")
            raise
    
    def generate_tweet_with_grok(self, account_name):
        prompts = {
            "X": (
                "Create a professional English tweet (220-240 chars) for SoliumCoin starting with 'soliumcoin.com'. "
                "Focus on blockchain innovation, technology leadership, and real-world use cases. "
                "Mention the presale opportunity objectively. End with 'Follow @soliumcoin'. "
                "Avoid hype, keep it factual and engaging. No hashtags."
            ),
            "X2": (
                "Write a community-focused English tweet (220-240 chars) for SoliumCoin starting with 'soliumcoin.com'. "
                "Highlight the growing SoliumArmy, community benefits, and how to participate. "
                "Use friendly, inclusive language. End with 'Follow @soliumcoin'. No hashtags."
            ),
            "X3": (
                "Create an exciting but realistic English tweet (220-240 chars) for SoliumCoin starting with 'soliumcoin.com'. "
                "Emphasize the presale opportunity, growth potential, and roadmap milestones. "
                "Use energetic but professional tone. End with 'Follow @soliumcoin'. No hashtags."
            )
        }
        
        try:
            response = self.grok_client.chat.completions.create(
                model="grok-3",  # Grok-3 modeli kullanılıyor
                messages=[{"role": "user", "content": prompts[account_name]}],
                max_tokens=150,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.2,
                presence_penalty=0.2
            )
            
            tweet = response.choices[0].message.content.strip()
            selected_hashtags = random.sample(HASHTAGS, 3)
            final_tweet = f"{tweet} {' '.join(selected_hashtags)}"
            
            # Karakter sınırı ve son kontrol
            if len(final_tweet) > 280:
                final_tweet = final_tweet[:277] + "..."
            
            logging.debug(f"{account_name} için oluşturulan tweet: {final_tweet}")
            return final_tweet
            
        except Exception as e:
            logging.error(f"Grok-3 tweet üretimi hatası ({account_name}): {e}")
            raise Exception(f"Grok-3 ile tweet oluşturulamadı: {e}")
    
    def post_tweet(self, account_name):
        self.rate_limit_handler.check_rate_limit(account_name)
        
        try:
            # Önce tweet içeriğini oluştur
            tweet_text = self.generate_tweet_with_grok(account_name)
            
            # Sonra tweet'i gönder
            response = self.twitter_clients[account_name].create_tweet(text=tweet_text)
            
            # Başarılı ise logla
            tweet_id = response.data['id']
            logging.info(f"{account_name} tweet gönderildi (ID: {tweet_id}): {tweet_text[:50]}...")
            
            return True
            
        except tweepy.TooManyRequests as e:
            # Rate limit hatasını işle
            wait_time = 60 * 15  # 15 dakika bekle
            logging.warning(f"{account_name} için rate limit aşıldı. {wait_time/60} dakika bekleniyor...")
            time.sleep(wait_time)
            return False
            
        except Exception as e:
            logging.error(f"{account_name} tweet gönderim hatası: {str(e)}")
            return False
    
    def schedule_tweets(self):
        intervals = {
            "X": 120 * 60,  # 2 saat
            "X2": 115 * 60, # 115 dakika
            "X3": 110 * 60  # 110 dakika
        }
        
        for account_name in self.twitter_clients:
            self.scheduler.add_job(
                self.post_tweet,
                'interval',
                seconds=intervals[account_name],
                args=[account_name],
                id=f"tweet_job_{account_name}",
                misfire_grace_time=300,
                coalesce=True
            )
        
        self.scheduler.start()
        logging.info("Zamanlayıcı başlatıldı (Grok-3 aktif)")
    
    def run_initial_tweets(self):
        logging.info("Başlangıç tweetleri gönderiliyor (Grok-3 ile)...")
        for account_name in self.twitter_clients:
            try:
                if self.post_tweet(account_name):
                    logging.info(f"{account_name} başlangıç tweeti başarıyla gönderildi")
                time.sleep(30)  # Hesaplar arasında 30 saniye bekle
            except Exception as e:
                logging.error(f"{account_name} başlangıç tweeti gönderilemedi: {e}")
    
    def start(self):
        logging.info("Solium Bot başlatılıyor (Grok-3 aktif)...")
        self.run_initial_tweets()
        self.schedule_tweets()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("Bot durduruluyor...")
            self.scheduler.shutdown()
        except Exception as e:
            logging.error(f"Beklenmeyen hata: {e}")
            self.scheduler.shutdown()

if __name__ == "__main__":
    try:
        bot = SoliumBot()
        bot.start()
    except Exception as e:
        logging.error(f"Ölümcül hata: {e}")
