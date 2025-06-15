import tweepy
import random
import time
import os
import requests
from xai_sdk import XAIClient  # Grok API için, varsayım

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

# Grok API anahtarı
grok_api_key = os.environ["GROK_API_KEY"]
grok_client = XAIClient(api_key=grok_api_key)

# Grok ile tweet üret
def generate_tweet():
    prompt = "Solium Coin için 280 karakterden kısa, esprili ve dikkat çekici bir tanıtım tweet’i yaz. Kripto borsalarına hitap etsin, #SoliumCoin ve #Crypto etiketlerini kullansın. Samimi bir ton olsun."
    response = grok_client.generate_text(prompt=prompt, max_length=280)
    return response.text

# Borsaların son tweet ID’lerini çek
def get_post_ids(username, bearer_token):
    headers = {"Authorization": f"Bearer {bearer_token}"}
    url = f"https://api.x.com/2/users/by/username/{username}/tweets?max_results=10"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return [post["id"] for post in response.json().get("data", [])]
        else:
            print(f"Okuma hatası: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Okuma hatası: {e}")
        return []

# Hedef borsalar
target_borzas = ["Binance", "KuCoinCom", "Coinbase"]

# Ana döngü
for account in accounts:
    auth = tweepy.OAuthHandler(account["api_key"], account["api_secret"])
    auth.set_access_token(account["access_token"], account["access_token_secret"])
    api = tweepy.API(auth, wait_on_rate_limit=True)

    # Bağımsız tweet (günde max 16, ayda 500 limit için)
    for _ in range(5):  # Günde 5 bağımsız tweet
        tweet = generate_tweet()
        try:
            api.update_status(tweet)
            print(f"Hesap {account['access_token'][:10]}: {tweet}")
        except tweepy.TweepError as e:
            print(f"Tweet hatası: {e}")
        time.sleep(3600)  # 1 saat bekle

    # Borsalara yorum
    for borsa in target_borzas:
        post_ids = get_post_ids(borsa, account["bearer_token"])
        for post_id in post_ids[:2]:  # Her borsadan 2 gönderiye yorum
            comment = f"@{borsa} {generate_tweet()}"
            try:
                api.update_status(comment, in_reply_to_status_id=post_id)
                print(f"Yorum: {comment}")
            except tweepy.TweepError as e:
                print(f"Yorum hatası: {e}")
            time.sleep(3600)  # 1 saat bekle
