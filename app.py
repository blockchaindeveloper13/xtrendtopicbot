import tweepy
import random
import time
import os
import requests
import json
from xai_sdk import XAIClient  # Grok API için, gerçek kütüphaneyi ekle
from io import BytesIO

# Hashtag havuzu
HASHTAG_POOL = [
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

# Config Vars’tan anahtarları çek
accounts = [
    {
        "api_key": os.environ["ACCOUNT1_API_KEY"],
        "api_secret": os.environ["ACCOUNT1_API_SECRET"],
        "access_token": os.environ["ACCOUNT1_ACCESS_TOKEN"],
        "access_token_secret": os.environ["ACCOUNT1_ACCESS_TOKEN_SECRET"],
        "bearer_token": os.environ["ACCOUNT1_BEARER_TOKEN"]
    },
    {
        "api_key": os.environ["ACCOUNT2_API_KEY"],
        "api_secret": os.environ["ACCOUNT2_API_SECRET"],
        "access_token": os.environ["ACCOUNT2_ACCESS_TOKEN"],
        "access_token_secret": os.environ["ACCOUNT2_ACCESS_TOKEN_SECRET"],
        "bearer_token": os.environ["ACCOUNT2_BEARER_TOKEN"]
    },
    {
        "api_key": os.environ["ACCOUNT3_API_KEY"],
        "api_secret": os.environ["ACCOUNT3_API_SECRET"],
        "access_token": os.environ["ACCOUNT3_ACCESS_TOKEN"],
        "access_token_secret": os.environ["ACCOUNT3_ACCESS_TOKEN_SECRET"],
        "bearer_token": os.environ["ACCOUNT3_BEARER_TOKEN"]
    }
]

# Grok API
grok_api_key = os.environ["GROK_API_KEY"]
grok_client = XAIClient(api_key=grok_api_key)

# GitHub’daki resimler (repo ve dosya adlarını güncelle)
image_urls = [
    "https://raw.githubusercontent.com/kullanıcı-adın/solium-coin-bot/main/images/solium_promo1.png",
    "https://raw.githubusercontent.com/kullanıcı-adın/solium-coin-bot/main/images/solium_promo2.png",
    "https://raw.githubusercontent.com/kullanıcı-adın/solium-coin-bot/main/images/solium_promo3.png"
]

# Hedef hesaplar
target_accounts = [
    "Binance", "KuCoinCom", "BitMartExchange", "MEXC_Official", "Gate_io",
    "Shibtoken", "BabyDogeCoin", "trondao", "whale_alert", "Bitcoin"
]

# Son gönderi ID’lerini sakla
LAST_IDS_FILE = "last_ids.json"

def load_last_ids():
    try:
        with open(LAST_IDS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {account: 0 for account in target_accounts}

def save_last_ids(last_ids):
    with open(LAST_IDS_FILE, "w") as f:
        json.dump(last_ids, f)

# Tweet üret
def generate_tweet(target=None):
    base_prompt = (
        "Write a 170-char tweet in English for Solium Coin. Highlight the extended presale, BNB participation via Binance/KuCoin Web3 Wallet or MetaMask. "
        "Emphasize Dubai-inspired, BSC-Solana bridged, #SoliumArmy-led Web3 project. "
        "Avoid wealth promises or investment guarantees to comply with SEC’s Howey Test. "
        "Include https://bit.ly/3HHUPTQ naturally."
    )
    if target in ["Binance", "KuCoinCom", "BitMartExchange", "MEXC_Official", "Gate_io"]:
        prompt = f"{base_prompt} Call out {target} for listing."
    elif target in ["Shibtoken", "BabyDogeCoin"]:
        prompt = f"{base_prompt} Appeal to {target}’s community."
    else:
        prompt = base_prompt
    response = grok_client.generate_text(prompt=prompt, max_length=170)
    # Rastgele 3 hashtag ekle
    hashtags = random.sample(HASHTAG_POOL, 3)
    tweet = f"{response.text} https://bit.ly/3HHUPTQ {' '.join(hashtags)}"
    if len(tweet) > 280:
        # Kısalt
        text_part = response.text[:280 - len(" https://bit.ly/3HHUPTQ " + " ".join(hashtags))]
        tweet = f"{text_part} https://bit.ly/3HHUPTQ {' '.join(hashtags)}"
    return tweet

# Resmi GitHub’dan çek
def download_image():
    url = random.choice(image_urls)
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content), url.split("/")[-1]
    raise Exception(f"Image fetch failed: {response.status_code}")

# Hesapların tweet ID’lerini çek
def get_post_ids(username, bearer_token):
    headers = {"Authorization": f"Bearer {bearer_token}"}
    url = f"https://api.x.com/2/users/by/username/{username}/tweets?max_results=5"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            posts = response.json().get("data", [])
            return [post["id"] for post in posts]
        else:
            print(f"Read error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Read error: {e}")
        return []

# Ana döngü
last_ids = load_last_ids()
daily_counts = {i: 0 for i in range(3)}  # Hesap başına günlük post sayacı
last_reset = time.time()

while True:
    # Günlük limit sıfırlama (24 saat)
    if time.time() - last_reset >= 86400:
        daily_counts = {i: 0 for i in range(3)}
        last_reset = time.time()

    new_post_found = False
    target_post_id = None
    target_account = None

    # Yeni gönderi kontrolü
    for target in target_accounts:
        post_ids = get_post_ids(target, accounts[0]["bearer_token"])
        if not post_ids:
            continue
        latest_id = str(post_ids[0])
        if latest_id > str(last_ids.get(target, "0")):
            new_post_found = True
            target_post_id = latest_id
            target_account = target
            last_ids[target] = latest_id
            break

    # Tüm hesaplar için işlem
    for acc_idx, account in enumerate(accounts):
        if daily_counts[acc_idx] >= 15:  # Günlük limit
            continue

        auth = tweepy.OAuthHandler(account["api_key"], account["api_secret"])
        auth.set_access_token(account["access_token"], account["access_token_secret"])
        api = tweepy.API(auth, wait_on_rate_limit=True)

        if new_post_found:  # Yeni gönderiye yorum
            comment = f"@{target_account} {generate_tweet(target=target_account)}"
            try:
                img, img_name = download_image()
                media = api.media_upload(filename=img_name, file=img)
                api.update_status(status=comment, media_ids=[media.media_id], in_reply_to_status_id=target_post_id)
                print(f"Account {account['access_token'][:10]}: {comment} [Image: {img_name}]")
                daily_counts[acc_idx] += 1
            except tweepy.TweepError as e:
                print(f"Comment error: {e}")
        else:  # Bağımsız tweet
            tweet = generate_tweet()
            try:
                img, img_name = download_image()
                media = api.media_upload(filename=img_name, file=img)
                api.update_status(status=tweet, media_ids=[media.media_id])
                print(f"Account {account['access_token'][:10]}: {tweet} [Image: {img_name}]")
                daily_counts[acc_idx] += 1
            except tweepy.TweepError as e:
                print(f"Tweet error: {e}")

        time.sleep(5400 / len(accounts))  # 1.5 saat, hesaplar arasında bölüş

    save_last_ids(last_ids)
    time.sleep(5400)  # 1.5 saat bekle
