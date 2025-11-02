#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import time
import json
from datetime import datetime

def smart_extract_with_agent():
    """
    Uses AI agent to intelligently analyze and extract property data from results page
    """
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🤖 Smart Property Data Extractor with AI Agent")
        print("=" * 60)
        
        # Step 1: Get user to results page
        print("STEP 1: Load search results")
        print("Please ensure you have completed the search and have results loaded.")
        
        choice = input("\n1. Run search script first (y/n)? ").lower()
        
        if choice == 'y':
            print("Please run: python3 pbc_property_search.py")
            print("Complete the search, then come back here.")
            input("Press ENTER when you have results loaded...")
        
        # Step 2: Navigate to results or get current page
        driver.get("https://pbcpao.gov/AdvSearch/RealPropSearch")
        time.sleep(2)
        
        print("\nPlease navigate to your results page if not already there.")
        input("Press ENTER when results page is visible in browser...")
        
        # Step 3: Get page HTML for agent analysis
        print("\n🤖 AI Agent analyzing page structure...")
        
        page_source = driver.page_source
        current_url = driver.current_url
        
        # Save page source for agent analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_file = f"page_source_{timestamp}.html"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        
        print(f"📄 Page source saved to {html_file}")
        print(f"🌐 Current URL: {current_url}")
        
        # Step 4: Use AI agent to analyze structure and extract data
        print("\n🧠 Launching AI agent to analyze page structure...")
        
        # This will be handled by the Task agent
        agent_prompt = f"""
        Analyze the HTML page source in file {html_file} and extract structured property data.
        
        The page contains search results from Palm Beach County Property Appraiser for:
        - Commercial properties
        - In Palm Beach municipality  
        - With minimum 5000 square feet
        
        Please:
        1. Identify the structure of the results (table, divs, lists, etc.)
        2. Extract all property records with these fields if available:
           - Property Address
           - Owner Name
           - Property Value/Assessment
           - Square Footage
           - Property Type
           - Parcel ID/Account Number
           - Sale Price/Sale Date (if available)
           - Any other relevant property details
        
        3. Format the extracted data as a JSON array of objects
        4. Save the structured data to a file called 'extracted_data_{timestamp}.json'
        5. Provide a summary of what was found
        
        Current URL: {current_url}
        Timestamp: {timestamp}
        """
        
        return agent_prompt, html_file, timestamp, driver
        
    except Exception as e:
        print(f"Error in smart extractor: {e}")
        return None, None, None, driver

def finalize_csv_export(json_file, timestamp):
    """
    Convert the agent-extracted JSON data to CSV format
    """
    try:
        print(f"\n📊 Converting {json_file} to CSV...")
        
        # Read the JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("❌ No data found in JSON file")
            return
        
        # Create CSV filename
        csv_file = f"palm_beach_properties_{timestamp}.csv"
        
        # Write to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            if isinstance(data, list) and len(data) > 0:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
                
                print(f"✅ Successfully exported {len(data)} records to {csv_file}")
                
                # Show sample
                print(f"\nSample of exported data (first 2 records):")
                print("-" * 50)
                for i, row in enumerate(data[:2]):
                    print(f"Record {i+1}:")
                    for key, value in row.items():
                        print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                    print()
            else:
                print("❌ Invalid data format in JSON file")
                
    except Exception as e:
        print(f"Error converting to CSV: {e}")

if __name__ == "__main__":
    agent_prompt, html_file, timestamp, driver = smart_extract_with_agent()
    
    if agent_prompt:
        print("\n" + "=" * 60)
        print("🚀 READY FOR AI AGENT")
        print("=" * 60)
        print("Now run the AI agent with this prompt:")
        print("\nAgent Task:")
        print(agent_prompt)
        print("\n" + "=" * 60)
        
        input("\nPress ENTER after the AI agent completes the analysis...")
        
        # Check if agent created the JSON file
        json_file = f"extracted_data_{timestamp}.json"
        import os
        
        if os.path.exists(json_file):
            finalize_csv_export(json_file, timestamp)
        else:
            print(f"❌ Expected JSON file {json_file} not found")
            print("Please ensure the AI agent completed the task successfully")
        
        print("\nKeeping browser open for 30 seconds...")
        time.sleep(30)
        driver.quit()
    else:
        print("❌ Failed to initialize smart extractor")
        if driver:
            driver.quit()