import os
from flask import Flask, jsonify
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    return webdriver.Chrome(
        executable_path=os.environ.get("CHROMEDRIVER_PATH"),
        options=chrome_options
    )

def get_trends():
    driver = None
    try:
        driver = init_driver()
        driver.get("https://trends24.in/")
        
        # Bekleme stratejisi
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.trend-card"))
        )
        
        trends = []
        cards = driver.find_elements(By.CSS_SELECTOR, "div.trend-card")
        
        for card in cards:
            location = card.find_element(By.CSS_SELECTOR, "h4").text
            items = card.find_elements(By.CSS_SELECTOR, "li")
            
            for item in items:
                try:
                    name = item.find_element(By.CSS_SELECTOR, "a").text
                    count = item.find_element(By.CSS_SELECTOR, "span.tweet-count").text
                    trends.append({"location": location, "name": name, "count": count})
                except:
                    continue
        
        return {"status": "success", "trends": trends[:20]}  # İlk 20 trend
    
    except Exception as e:
        app.logger.error(f"Hata: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    finally:
        if driver:
            driver.quit()

@app.route('/')
def home():
    return jsonify({"message": "Çalışıyor!", "endpoints": ["/trends"]})

@app.route('/trends')
def trends():
    return jsonify(get_trends())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
