#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import csv
import time
from datetime import datetime

def simple_papa_extractor():
    """
    Simple, direct extractor for PAPA results pages
    Designed specifically for Palm Beach County Property Appraiser results
    """
    
    print("🏠 Simple PAPA Results Extractor")
    print("="*50)
    print("This script connects to your current browser tab")
    print("Make sure you have PAPA results loaded first!")
    print()
    
    # Setup Chrome to connect to existing session
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Get user to navigate to results
        print("INSTRUCTIONS:")
        print("1. Make sure your PAPA search results are loaded")
        print("2. Press ENTER when ready to extract")
        input("Press ENTER to continue...")
        
        # Navigate to results page if needed
        current_url = input("Enter the results page URL (or press ENTER if already there): ").strip()
        if current_url:
            driver.get(current_url)
            time.sleep(3)
        
        print("\n🔍 Looking for results on page...")
        
        # Let's inspect what's actually on the page
        page_title = driver.title
        current_url = driver.current_url
        print(f"Page title: {page_title}")
        print(f"Current URL: {current_url}")
        
        # Save page source for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"papa_page_debug_{timestamp}.html"
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        print(f"Page source saved to {debug_file} for debugging")
        
        # Try different approaches to find results
        results_data = []
        
        print("\n📋 Attempting to extract data...")
        
        # Method 1: Look for tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(tables)} tables")
        
        for i, table in enumerate(tables):
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"  Table {i}: {len(rows)} rows")
            
            if len(rows) > 1:  # Has data
                print(f"  Extracting from table {i}...")
                
                # Get headers
                header_row = rows[0]
                headers = []
                
                # Try th first, then td
                header_cells = header_row.find_elements(By.TAG_NAME, "th")
                if not header_cells:
                    header_cells = header_row.find_elements(By.TAG_NAME, "td")
                
                for cell in header_cells:
                    headers.append(cell.text.strip())
                
                print(f"  Headers: {headers}")
                
                # Extract data rows
                for j, row in enumerate(rows[1:], 1):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) > 0:
                        row_data = {'Table': i, 'Row': j}
                        
                        for k, cell in enumerate(cells):
                            header = headers[k] if k < len(headers) else f"Column_{k}"
                            row_data[header] = cell.text.strip()
                        
                        results_data.append(row_data)
        
        # Method 2: Look for common result containers if no tables
        if not results_data:
            print("No table data found. Looking for other structures...")
            
            # Try various selectors for property results
            selectors = [
                ".result",
                ".property",
                ".listing",
                "[class*='result']",
                "[class*='property']",
                "[class*='record']",
                "tr",  # Just table rows
                "div[style*='border']",  # Bordered divs
                ".search-result",
                ".property-result"
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for i, element in enumerate(elements[:10]):  # Limit to first 10
                            text = element.text.strip()
                            if text and len(text) > 20:  # Non-empty, substantial content
                                results_data.append({
                                    'Selector': selector,
                                    'Element_Index': i,
                                    'Content': text[:500],  # First 500 chars
                                    'Full_Content': text
                                })
                        
                        if results_data:
                            break  # Use first successful selector
                            
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
        
        # Method 3: Last resort - get all visible text
        if not results_data:
            print("No structured data found. Extracting page text...")
            
            # Get all text content
            body = driver.find_element(By.TAG_NAME, "body")
            all_text = body.text
            
            # Split by lines and filter
            lines = all_text.split('\n')
            relevant_lines = []
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:
                    # Look for lines that might contain property info
                    if any(keyword in line.lower() for keyword in [
                        'palm beach', 'property', 'owner', 'address', 'value', '$', 'sqft', 'sq ft'
                    ]):
                        relevant_lines.append(line)
            
            # Add relevant lines as data
            for i, line in enumerate(relevant_lines[:50]):  # Max 50 lines
                results_data.append({
                    'Line_Number': i + 1,
                    'Content': line
                })
        
        # Export results
        if results_data:
            csv_filename = f"papa_results_{timestamp}.csv"
            
            print(f"\n💾 Saving {len(results_data)} records to {csv_filename}...")
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                if results_data:
                    fieldnames = results_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for row in results_data:
                        writer.writerow(row)
            
            print(f"✅ Data exported to {csv_filename}")
            
            # Show sample
            print(f"\n📋 Sample data (first 3 records):")
            print("-" * 60)
            for i, record in enumerate(results_data[:3]):
                print(f"Record {i+1}:")
                for key, value in record.items():
                    print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                print()
        
        else:
            print("❌ No data could be extracted from the page")
            print("Possible issues:")
            print("- Wrong page loaded")
            print("- Results not visible")
            print("- Page structure changed")
            print("- JavaScript content not loaded")
            print(f"Check {debug_file} for the full page content")
        
        print(f"\n🔍 Debug information:")
        print(f"- Page source saved: {debug_file}")
        print(f"- Results CSV: {csv_filename if results_data else 'None created'}")
        
        # Keep browser open
        print(f"\n⏳ Keeping browser open for 30 seconds for inspection...")
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    simple_papa_extractor()