#!/usr/bin/env python3

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def check_chromedriver():
    """Check if ChromeDriver is available"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("ChromeDriver is working correctly!")
        return True
    except Exception as e:
        print("ChromeDriver issue: " + str(e))
        print("\nTo fix this, you can:")
        print("1. Install ChromeDriver using: brew install chromedriver")
        print("2. Or download from: https://chromedriver.chromium.org/")
        print("3. Make sure Chrome browser is installed")
        return False

if __name__ == "__main__":
    print("Setting up Palm Beach County Property Search...")
    
    install_requirements()
    
    if check_chromedriver():
        print("\nSetup complete! You can now run:")
        print("python pbc_property_search.py")
    else:
        print("\nPlease fix ChromeDriver installation before running the script.")