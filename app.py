import os
import logging
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import WebDriverException

app = Flask(__name__)

# Detaylı log ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_step(step, message):
    """Her adımı loglar"""
    logger.info(f"[STEP {step}] {message}")
    return step + 1

def init_driver():
    """Chrome driver başlatma"""
    step = 1
    step = log_step(step, "Driver ayarları yapılıyor")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    
    try:
        step = log_step(step, "Chrome binary path kontrol ediliyor")
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        step = log_step(step, f"Chrome binary: {chrome_options.binary_location}")
        
        step = log_step(step, "ChromeDriver path kontrol ediliyor")
        driver_path = os.environ.get("CHROMEDRIVER_PATH")
        step = log_step(step, f"Driver path: {driver_path}")
        
        step = log_step(step, "Driver oluşturuluyor")
        driver = webdriver.Chrome(
            executable_path=driver_path,
            options=chrome_options
        )
        step = log_step(step, "Driver başarıyla oluşturuldu")
        return driver
    except WebDriverException as e:
        logger.error(f"Driver oluşturma hatası: {str(e)}")
        raise

def get_trends():
    """Trend verilerini çeker"""
    step = 1
    driver = None
    try:
        step = log_step(step, "Driver başlatılıyor")
        driver = init_driver()
        
        step = log_step(step, "Trends24 sayfası açılıyor")
        driver.get("https://trends24.in/")
        step = log_step(step, "Sayfa yüklendi")
        
        step = log_step(step, "Trend kartları bekleniyor (20 sn timeout)")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.trend-card"))
        )
        step = log_step(step, "Trend kartları bulundu")
        
        trends = []
        step = log_step(step, "Trend kartları aranıyor")
        cards = driver.find_elements(By.CSS_SELECTOR, "div.trend-card")
        step = log_step(step, f"{len(cards)} trend kartı bulundu")
        
        for i, card in enumerate(cards, 1):
            try:
                step_card = 1
                step_card = log_step(step_card, f"{i}. kart işleniyor")
                
                location = card.find_element(By.CSS_SELECTOR, "h4").text
                step_card = log_step(step_card, f"Konum: {location}")
                
                items = card.find_elements(By.CSS_SELECTOR, "li")
                step_card = log_step(step_card, f"{len(items)} trend öğesi bulundu")
                
                for j, item in enumerate(items, 1):
                    try:
                        step_item = 1
                        name = item.find_element(By.CSS_SELECTOR, "a").text
                        step_item = log_step(step_item, f"Trend adı: {name}")
                        
                        count = item.find_element(By.CSS_SELECTOR, "span.tweet-count").text
                        step_item = log_step(step_item, f"Tweet sayısı: {count}")
                        
                        trends.append({
                            "location": location,
                            "name": name,
                            "count": count,
                            "position": f"{i}.{j}"
                        })
                    except Exception as e:
                        logger.error(f"{i}.{j} öğe işlenirken hata: {str(e)}")
                        continue
            except Exception as e:
                logger.error(f"{i}. kart işlenirken hata: {str(e)}")
                continue
        
        return {
            "status": "success",
            "trends": trends[:20],  # İlk 20 trend
            "steps_completed": step
        }
    
    except Exception as e:
        logger.error(f"KRİTİK HATA: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "failed_step": step
        }
    
    finally:
        if driver:
            step = log_step(step, "Driver kapatılıyor")
            try:
                driver.quit()
                step = log_step(step, "Driver başarıyla kapatıldı")
            except Exception as e:
                logger.error(f"Driver kapatma hatası: {str(e)}")
@app.route('/test')
def test_selenium():
    try:
        driver = create_driver()
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        return jsonify({
            "status": "success",
            "title": title,
            "message": "Selenium başarıyla çalıştı"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "chrome_bin": os.environ.get("GOOGLE_CHROME_BIN"),
            "driver_path": os.environ.get("CHROMEDRIVER_PATH")
        })


@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "endpoints": ["/trends", "/debug"]
    })

@app.route('/trends')
def trends():
    return jsonify(get_trends())

@app.route('/debug')
def debug():
    """Sistem bilgilerini gösterir"""
    return jsonify({
        "chromedriver_path": os.environ.get("CHROMEDRIVER_PATH"),
        "chrome_bin": os.environ.get("GOOGLE_CHROME_BIN"),
        "memory_limit": os.environ.get("WEB_MEMORY"),
        "concurrency": os.environ.get("WEB_CONCURRENCY")
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
