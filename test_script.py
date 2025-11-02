#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_selenium_setup():
    """Test if Selenium and ChromeDriver are properly configured"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f"✓ Selenium test passed! Page title: {title}")
        return True
        
    except Exception as e:
        print(f"✗ Selenium test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Selenium setup...")
    test_selenium_setup()