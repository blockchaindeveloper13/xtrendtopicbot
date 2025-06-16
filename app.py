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
            logging.warning(f"{account_name} için Twitter rate limit bekleme: {wait_time:.1f} saniye")
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
        self.openai_client = self.initialize_openai_client()
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
                    wait_on_rate_limit=False  # Tweepy'nin otomatik beklemesini kapat, biz yönetelim
                )
                logging.info(f"{account} Twitter istemcisi başarıyla başlatıldı")
            except Exception as e:
                logging.error(f"{account} Twitter istemcisi başlatılamadı: {e}")
                raise
        
        return clients
    
    def initialize_openai_client(self):
        try:
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url="https://api.openai.com/v1",
                http_client=httpx.Client(
                    proxies=None,
                    timeout=30.0,
                    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)  # Bağlantı limitini artır
                )
            )
            logging.info("ChatGPT istemcisi başarıyla başlatıldı")
            return client
        except Exception as e:
            logging.error(f"ChatGPT istemcisi başlatılamadı: {e}")
            raise
    
    def generate_tweet_with_openai(self, account_name):
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
            logging.info(f"{account_name} için ChatGPT ile tweet içeriği üretiliyor...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompts[account_name]}],
                max_tokens=150,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.2,
                presence_penalty=0.2
            )
            
            tweet = response.choices[0].message.content.strip()
            selected_hashtags = random.sample(HASHTAGS, 3)
            hashtag_str = " ".join(selected_hashtags)
            
            # 280 karaktere doldur, hashtag'ler sonda
            current_length = len(tweet)
            if current_length < 240:
                padding = " " * (240 - current_length)
                tweet = f"{tweet}{padding}"
            elif current_length > 240:
                tweet = tweet[:237] + "..."
            
            final_tweet = f"{tweet} {hashtag_str}"
            logging.debug(f"{account_name} için oluşturulan tweet: {final_tweet}")
            return final_tweet
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                logging.warning(f"ChatGPT API rate limit aşıldı (Hesap: {account_name}), 60 saniye bekleniyor: {e}")
                time.sleep(60)
                return self.generate_tweet_with_openai(account_name)  # Tekrar dene
            logging.error(f"ChatGPT tweet üretimi hatası ({account_name}): {e}")
            return (
                f"soliumcoin.com Join the Web3 future with our presale! Be part of something big. Follow @soliumcoin "
                + " ".join(random.sample(HASHTAGS, 3))
            )
    
    def post_tweet(self, account_name):
        self.rate_limit_handler.check_rate_limit(account_name)
        
        try:
            logging.info(f"{account_name} için tweet gönderimi başlatılıyor...")
            tweet_text = self.generate_tweet_with_openai(account_name)
            
            logging.info(f"{account_name} için Twitter API çağrısı yapılıyor...")
            response = self.twitter_clients[account_name].create_tweet(text=tweet_text)
            
            tweet_id = response.data['id']
            logging.info(f"{account_name} tweet gönderildi (ID: {tweet_id}): {tweet_text[:50]}...")
            return True
            
        except tweepy.errors.Forbidden as e:
            logging.error(f"{account_name} yetki hatası (403 Forbidden), Twitter Developer Portal’da Read/Write izinlerini ve hesap kısıtlamalarını kontrol et. Tweet içeriği: {tweet_text if 'tweet_text' in locals() else 'N/A'}, Hata: {e}")
            return False
        except tweepy.TooManyRequests as e:
            headers = getattr(e, 'response', None).headers if hasattr(e, 'response') else {}
            reset_time = int(headers.get('x-rate-limit-reset', time.time() + 900))
            wait_time = max(reset_time - time.time(), 15)
            logging.warning(f"{account_name} için Twitter API rate limit aşıldı, {wait_time:.1f} saniye bekleniyor: {e}, Headers: {headers}")
            time.sleep(wait_time)
            return False
        except Exception as e:
            logging.error(f"{account_name} tweet gönderim hatası, Tweet içeriği: {tweet_text if 'tweet_text' in locals() else 'N/A'}, Hata: {e}")
            return False
    
    def schedule_tweets(self):
        interval = 5760  # 96 dakika
        
        for account_name in self.twitter_clients:
            self.scheduler.add_job(
                self.post_tweet,
                'interval',
                seconds=interval,
                args=[account_name],
                id=f"tweet_job_{account_name}",
                misfire_grace_time=300,
                coalesce=True
            )
        
        self.scheduler.start()
        logging.info("Zamanlayıcı başlatıldı (ChatGPT aktif)")
    
    def run_initial_tweets(self):
        logging.info("Başlangıç tweetleri gönderiliyor (ChatGPT ile)...")
        for account_name in self.twitter_clients:
            try:
                if self.post_tweet(account_name):
                    logging.info(f"{account_name} başlangıç tweeti başarıyla gönderildi")
                time.sleep(300)  # Hesaplar arasında 5 dakika bekle
            except Exception as e:
                logging.error(f"{account_name} başlangıç tweeti gönderilemedi: {e}")
    
    def start(self):
        logging.info("Solium Bot başlatılıyor (ChatGPT aktif)...")
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
