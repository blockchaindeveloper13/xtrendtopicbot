import os
import time
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import tweepy

# Günlük kaydı (Türkiye saati)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('solium_bot.log'), logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
logging.Formatter.converter = lambda *args: datetime.now(timezone(timedelta(hours=3))).timetuple()

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
                raise
        
        return clients
    
    def get_fallback_tweet(self, account_name):
        # Fallback tweet içeriği
        tweet = f"soliumcoin.com Join Web3! Don’t miss our presale! Follow @soliumcoin {' '.join(HASHTAGS)}"
        logging.info(f"{account_name} için fallback tweet içeriği ({len(tweet)} karakter): {tweet}")
        return tweet
    
    def post_tweet(self, account_name):
        self.rate_limit_handler.check_rate_limit(account_name)
        
        try:
            logging.info(f"{account_name} için tweet gönderimi başlatılıyor...")
            tweet_text = self.get_fallback_tweet(account_name)
            
            logging.info(f"{account_name} için Twitter API çağrısı yapılıyor...")
            response = self.twitter_clients[account_name].create_tweet(text=tweet_text)
            
            tweet_id = response.data['id']
            logging.info(f"{account_name} tweet gönderildi (ID: {tweet_id}): {tweet_text[:50]}...")
            return True
            
        except tweepy.TooManyRequests as e:
            headers = getattr(e, 'response', None).headers if hasattr(e, 'response') else {}
            app_limit_remaining = headers.get('x-app-limit-24hour-remaining', 'N/A')
            user_limit_remaining = headers.get('x-user-limit-24hour-remaining', 'N/A')
            if app_limit_remaining == '0' or user_limit_remaining == '0':
                reset_time = int(headers.get('x-app-limit-24hour-reset', time.time() + 7200))
                wait_time = 7200  # 2 saat bekle
                logging.warning(
                    f"{account_name} için Twitter 24 saatlik kota doldu (App: {app_limit_remaining}, User: {user_limit_remaining}), "
                    f"{wait_time:.1f} saniye bekleniyor (sıfırlama: {datetime.fromtimestamp(reset_time, tz=timezone(timedelta(hours=3)))}): {e}"
                )
                time.sleep(wait_time)
                return self.post_tweet(account_name)
            else:
                reset_time = int(headers.get('x-rate-limit-reset', time.time() + 900))
                wait_time = max(reset_time - time.time(), 15)
                logging.warning(
                    f"{account_name} için Twitter API rate limit aşıldı, {wait_time:.1f} saniye bekleniyor: {e}, "
                    f"Headers: {headers}"
                )
                time.sleep(wait_time)
                return False
        except tweepy.errors.Forbidden as e:
            logging.error(
                f"{account_name} yetki hatası (403 Forbidden), Twitter Developer Portal’da Read/Write izinlerini ve hesap kısıtlamalarını kontrol et. "
                f"Tweet içeriği: {tweet_text if 'tweet_text' in locals() else 'N/A'}, Hata: {e}"
            )
            return False
        except Exception as e:
            logging.error(
                f"{account_name} tweet gönderim hatası, Tweet içeriği: {tweet_text if 'tweet_text' in locals() else 'N/A'}, Hata: {e}"
            )
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
        
        self.scheduler.start()
        logging.info("Zamanlayıcı başlatıldı")
    
    def run_initial_tweets(self):
        logging.info("Başlangıç tweetleri gönderiliyor...")
        for account_name in self.twitter_clients.keys():
            try:
                if self.post_tweet(account_name):
                    logging.info(f"{account_name} başlangıç tweeti başarıyla gönderildi")
                time.sleep(300)  # Hesaplar arasında 5 dakika bekle
            except Exception as e:
                logging.error(f"{account_name} başlangıç tweeti gönderilemedi: {e}")
    
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
