#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import time
import re
from datetime import datetime

def extract_results_to_csv():
    """
    Extracts search results from Palm Beach County Property Appraiser results page
    and saves them to a CSV file
    """
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Starting result extraction process...")
        print("="*60)
        print("INSTRUCTIONS:")
        print("1. First run: python3 pbc_property_search.py")
        print("2. When it prompts you, manually click SEARCH")
        print("3. Wait for results to load (30-60 seconds)")
        print("4. Then run this script to extract results")
        print("="*60)
        
        # Ask user to confirm they have results loaded
        input("\nPress ENTER when you have search results loaded in your browser...")
        
        print("\nAttempting to find active browser tab with results...")
        
        # Try to connect to existing browser session or open new one
        try:
            # First, let's navigate to a results page to see what we're working with
            print("Please manually navigate to your results page, then press ENTER...")
            input("Press ENTER when results page is open...")
            
            # Now try to get the current page
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
            
        except Exception as e:
            print(f"Browser connection issue: {e}")
            print("Let's navigate to the search page and have you load results...")
            
            driver.get("https://pbcpao.gov/AdvSearch/RealPropSearch")
            time.sleep(3)
            
            print("\n" + "="*50)
            print("Please complete the search manually:")
            print("1. Select Commercial")
            print("2. Select Municipality radio button") 
            print("3. Choose Palm Beach from dropdown")
            print("4. Enter 5000 in Square Footage")
            print("5. Click SEARCH")
            print("6. Wait for results to load")
            print("="*50)
            
            input("\nPress ENTER when results are loaded...")
        
        print("\nAnalyzing results page structure...")
        
        # Wait for results to be present
        wait = WebDriverWait(driver, 10)
        
        # Try different selectors to find results table/data
        results_data = []
        
        try:
            # Look for tables first
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} table(s) on page")
            
            if tables:
                for i, table in enumerate(tables):
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"Table {i}: {len(rows)} rows")
                    
                    if len(rows) > 1:  # Has header and data
                        print(f"Using table {i} for data extraction")
                        
                        # Extract headers
                        header_row = rows[0]
                        headers = []
                        header_cells = header_row.find_elements(By.TAG_NAME, "th")
                        if not header_cells:
                            header_cells = header_row.find_elements(By.TAG_NAME, "td")
                        
                        for cell in header_cells:
                            headers.append(cell.text.strip())
                        
                        print(f"Headers found: {headers}")
                        
                        # Extract data rows
                        for row in rows[1:]:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            row_data = {}
                            
                            for j, cell in enumerate(cells):
                                if j < len(headers):
                                    row_data[headers[j]] = cell.text.strip()
                            
                            if row_data and any(row_data.values()):  # Non-empty row
                                results_data.append(row_data)
                        
                        break
            
            # If no tables, look for other data structures
            if not results_data:
                print("No table data found. Looking for other data structures...")
                
                # Look for divs or other containers that might hold property data
                property_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'property') or contains(@class, 'result') or contains(@class, 'listing')]")
                
                if not property_containers:
                    # Try more generic selectors
                    property_containers = driver.find_elements(By.XPATH, "//div[contains(text(), 'Palm Beach') or contains(text(), '$') or contains(text(), 'sq')]")
                
                print(f"Found {len(property_containers)} potential property containers")
                
                for container in property_containers[:10]:  # Limit to first 10
                    text_content = container.text.strip()
                    if text_content and len(text_content) > 20:  # Non-empty, substantial content
                        # Try to parse key information
                        property_data = {
                            'Raw_Content': text_content,
                            'Contains_Dollar': '$' in text_content,
                            'Contains_SqFt': any(word in text_content.lower() for word in ['sq', 'square', 'feet', 'ft']),
                            'Contains_Address': any(word in text_content.lower() for word in ['st', 'ave', 'rd', 'dr', 'way', 'ln'])
                        }
                        results_data.append(property_data)
            
        except Exception as e:
            print(f"Error extracting data: {e}")
            
            # Fallback: get all text content
            print("Fallback: extracting all page text...")
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Split into lines and filter for relevant content
            lines = page_text.split('\n')
            relevant_lines = []
            
            for line in lines:
                line = line.strip()
                if line and (
                    '$' in line or 
                    'palm beach' in line.lower() or 
                    any(word in line.lower() for word in ['sq', 'square', 'feet', 'address', 'property'])
                ):
                    relevant_lines.append(line)
            
            if relevant_lines:
                for i, line in enumerate(relevant_lines[:20]):  # First 20 relevant lines
                    results_data.append({
                        'Line_Number': i+1,
                        'Content': line
                    })
        
        # Save to CSV
        if results_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"palm_beach_properties_{timestamp}.csv"
            
            print(f"\nExtracting {len(results_data)} records to {filename}...")
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if results_data:
                    fieldnames = results_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for row in results_data:
                        writer.writerow(row)
            
            print(f"✅ Successfully exported {len(results_data)} records to {filename}")
            
            # Show sample of what was extracted
            print("\nSample of extracted data:")
            print("-" * 40)
            for i, row in enumerate(results_data[:3]):
                print(f"Record {i+1}:")
                for key, value in row.items():
                    print(f"  {key}: {value}")
                print()
            
        else:
            print("❌ No data was extracted. The page might not have loaded properly.")
            print("Current page source (first 500 chars):")
            print(driver.page_source[:500])
        
        print("\nKeeping browser open for 30 seconds for review...")
        time.sleep(30)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    print("Palm Beach County Property Results Extractor")
    print("=" * 50)
    extract_results_to_csv()