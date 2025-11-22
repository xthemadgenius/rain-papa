#!/usr/bin/env python3
"""
Dependency Installation Script for Property Results Extractor

This script helps install the required dependencies for the property extractor.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install requirements from requirements.txt"""
    try:
        print("🔧 Installing required dependencies...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dependencies installed successfully!")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def check_chrome_driver():
    """Check if Chrome and ChromeDriver are available"""
    print("\n🔍 Checking Chrome and ChromeDriver...")
    
    try:
        # Try to import selenium and create a basic driver
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(options=options)
        driver.quit()
        
        print("✅ Chrome and ChromeDriver are working correctly!")
        return True
        
    except Exception as e:
        print(f"⚠️  Chrome/ChromeDriver issue: {e}")
        print("\n🔧 To fix this:")
        print("1. Make sure Google Chrome is installed")
        print("2. Install ChromeDriver:")
        print("   - On macOS: brew install chromedriver")
        print("   - On Ubuntu: sudo apt install chromium-chromedriver")
        print("   - On Windows: Download from https://chromedriver.chromium.org/")
        print("3. Or use Selenium Manager (automatic with Selenium 4.6+)")
        return False

def main():
    """Main setup function"""
    print("="*60)
    print("🚀 PROPERTY RESULTS EXTRACTOR - SETUP")
    print("="*60)
    
    # Check if we're in the right directory
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        print("Please run this script from the papa-rain directory")
        return
    
    # Install dependencies
    if not install_requirements():
        print("❌ Failed to install dependencies. Setup incomplete.")
        return
    
    # Check Chrome driver
    check_chrome_driver()
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("You can now run the property extractor with:")
    print("  python3 property_results_extractor.py")
    print()
    print("Or make it executable and run directly:")
    print("  chmod +x property_results_extractor.py")
    print("  ./property_results_extractor.py")
    print("="*60)

if __name__ == "__main__":
    main()