import os
import time
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

def create_driver():
    """Headless Chrome driver oluşturma"""
    options = Options()
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(
        executable_path=os.environ.get("CHROMEDRIVER_PATH"),
        options=options
    )
    return driver

def scrape_trends():
    driver = None
    try:
        driver = create_driver()
        driver.get("https://trends24.in/")
        
        # Sayfanın yüklenmesini bekle
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'page-title')]"))
        )
        
        # Sayfayı biraz kaydır (lazy loading için)
        driver.execute_script("window.scrollBy(0, 500)")
        time.sleep(2)
        
        # Trend verilerini çek
        trends = []
        trend_cards = driver.find_elements(By.CSS_SELECTOR, "div.trend-card")
        
        for card in trend_cards:
            try:
                location = card.find_element(By.CSS_SELECTOR, "h4").text
                items = card.find_elements(By.CSS_SELECTOR, "li")
                
                for item in items:
                    try:
                        name = item.find_element(By.CSS_SELECTOR, "a").text
                        count = item.find_element(By.CSS_SELECTOR, "span.tweet-count").text
                        url = item.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        
                        trends.append({
                            "location": location,
                            "name": name,
                            "count": count,
                            "url": url
                        })
                    except:
                        continue
            except:
                continue
        
        return {
            "status": "success",
            "trends": trends,
            "count": len(trends),
            "source": "trends24.in"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "solution": "Check if page structure changed"
        }
    finally:
        if driver:
            driver.quit()

@app.route('/')
def home():
    return jsonify({
        "endpoints": {
            "/trends": "Get all trends",
            "/top?limit=5": "Get top trends"
        }
    })

@app.route('/trends')
def get_trends():
    return jsonify(scrape_trends())

@app.route('/top')
def top_trends():
    limit = int(request.args.get('limit', 5))
    data = scrape_trends()
    if data['status'] == 'success':
        data['trends'] = sorted(
            data['trends'],
            key=lambda x: float(x['count'].replace('K', '000').replace('M', '000000')),
            reverse=True
        )[:limit]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
