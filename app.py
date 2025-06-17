import os
import time
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random
import tweepy
from apscheduler.schedulers.background import BackgroundScheduler

# Günlük kaydı (Türkiye saati: UTC+3)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('solium_bot.log'), logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
logging.Formatter.converter = lambda *args: datetime.now(ZoneInfo("Europe/Istanbul")).timetuple()

# Sabit hashtag’ler
HASHTAGS = ["#Solium", "#SoliumArmy", "#Web3", "#DeFi", "#Crypto", "#Cryptocurrency",
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
    "#BearMarket", "#Dubai", "#Innovation"]

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
            logging.warning(f"{account_name} için Twitter rate limit bekleniyor: {wait_time:.1f} saniye")
            time.sleep(wait_time)
        return True
    
    def update_rate_limit(self, account_name, headers):
        if headers and 'x-rate-limit-reset' in headers:
            reset_time = int(headers['x-rate-limit-reset'])
            now = time.time()
            self.account_limits[account_name] = {
                "last_call": now,
                "retry_after": max(reset_time - now, 15)
            }

class SoliumBot:
    def __init__(self):
        self.rate_limit_handler = TwitterRateLimitHandler()
        self.twitter_clients = self.initialize_twitter_clients()
        self.scheduler = BackgroundScheduler(timezone="UTC")
        
    def initialize_twitter_clients(self):
        clients = {}
        accounts = ["X", "X2", "X3"]
        
        for account in accounts:
            if not os.getenv(f"{account}_API_KEY"):
                logging.error(f"{account} için API anahtarı eksik")
                continue
            try:
                clients[account] = tweepy.Client(
                    consumer_key=os.getenv(f"{account}_API_KEY"),
                    consumer_secret=os.getenv(f"{account}_SECRET_KEY"),
                    access_token=os.getenv(f"{account}_ACCESS_TOKEN"),
                    access_token_secret=os.getenv(f"{account}_ACCESS_SECRET"),
                    wait_on_rate_limit=False
                )
                logging.info(f"{account} Twitter istemcisi başarıyla başlatıldı")
            except Exception as e:
                logging.error(f"{account} Twitter istemcisi başlatılamadı: {e}")
        
        if not clients:
            raise Exception("Hiçbir Twitter istemcisi başlatılamadı")
        return clients
    
    def get_fallback_tweet(self, account_name):
        selected_hashtags = random.sample(HASHTAGS, 3)
        tweet = f"visit soliumcoin.com Presale started 🚀 Join Web3! Hurry up! 💸 Don’t miss our presale! 🎉 Follow @soliumcoin 📌 {' '.join(selected_hashtags)}"
        logging.info(f"{account_name} için tweet içeriği ({len(tweet)} karakter): {tweet}")
        return tweet
    
    def post_tweet(self, account_name):
        if account_name not in self.twitter_clients:
            logging.error(f"{account_name} için Twitter istemcisi bulunamadı")
            return False
        
        self.rate_limit_handler.check_rate_limit(account_name)
        logging.info(f"{account_name} için tweet gönderimi başlatılıyor...")
        tweet_text = self.get_fallback_tweet(account_name)
        
        try:
            logging.info(f"{account_name} için Twitter API çağrısı yapılıyor...")
            response = self.twitter_clients[account_name].create_tweet(text=tweet_text)
            tweet_id = response.data['id']
            logging.info(f"{account_name} tweet gönderildi (ID: {tweet_id}): {tweet_text[:50]}...")
            return True
        
        except tweepy.TooManyRequests as e:
            headers = getattr(e, 'response', None).headers if hasattr(e, 'response') else {}
            app_limit_remaining = headers.get('x-app-limit-24hour-remaining', 'N/A')
            user_limit_remaining = headers.get('x-user-limit-24hour-remaining', 'N/A')
            wait_time = 5760  # 96 dakika
            if app_limit_remaining == '0' or user_limit_remaining == '0':
                reset_time = int(headers.get('x-app-limit-24hour-reset', time.time() + 7200))
                logging.warning(
                    f"{account_name} için Twitter 24 saatlik kota doldu (App: {app_limit_remaining}, User: {user_limit_remaining}), "
                    f"{wait_time:.1f} saniye bekleniyor (sıfırlama: {datetime.fromtimestamp(reset_time, tz=ZoneInfo('Europe/Istanbul'))}): {e}"
                )
            else:
                reset_time = int(headers.get('x-rate-limit-reset', time.time() + 5760))
                logging.warning(
                    f"{account_name} için Twitter API rate limit aşıldı, {wait_time:.1f} saniye bekleniyor: {e}, "
                    f"Headers: {headers}"
                )
            time.sleep(wait_time)
            return False
        except tweepy.errors.Forbidden as e:
            logging.error(
                f"{account_name} yetki hatası (403 Forbidden), Twitter Developer Portal’da Read/Write izinlerini kontrol et. "
                f"Tweet içeriği: {tweet_text}, Hata: {e}"
            )
            time.sleep(5760)
            return False
        except Exception as e:
            logging.error(
                f"{account_name} tweet gönderim hatası, Tweet içeriği: {tweet_text}, Hata: {e}"
            )
            time.sleep(5760)
            return False
    
    def schedule_tweets(self):
        interval = 5760  # 96 dakika
        for account_name in self.twitter_clients.keys():
            self.scheduler.add_job(
                self.post_tweet,
                'interval',
                seconds=interval,
                args=[account_name],
                id=f"tweet_job_{account_name}",
                misfire_grace_time=300,
                coalesce=True
            )
            logging.info(f"{account_name} için 96 dakikalık tweet zamanlayıcısı ayarlandı")
        self.scheduler.start()
        logging.info("Tüm zamanlayıcılar başlatıldı")
    
    def run_initial_tweets(self):
        logging.info("Başlangıç tweetleri gönderiliyor...")
        for account_name in self.twitter_clients.keys():
            logging.info(f"{account_name} için başlangıç tweet işlemi başlatılıyor...")
            if self.post_tweet(account_name):
                logging.info(f"{account_name} başlangıç tweeti başarıyla gönderildi")
            else:
                logging.warning(f"{account_name} başlangıç tweeti gönderilemedi, 96 dakika sonra tekrar denenecek")
            logging.info(f"{account_name} işlemi tamamlandı, bir sonraki hesaba geçiliyor")
            time.sleep(5)  # Hesaplar arasında 5 saniye bekle
    
    def start(self):
        logging.info("Solium Bot başlatılıyor...")
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
