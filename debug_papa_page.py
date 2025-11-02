#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime

def debug_papa_page():
    """
    Debug script to analyze the PAPA results page structure
    This will help us understand what elements are actually present
    """
    
    print("🔍 PAPA Page Structure Debugger")
    print("="*50)
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("1. First, run your search and get results loaded")
        print("2. Then press ENTER here to analyze the page")
        input("Press ENTER when results are visible in browser...")
        
        # Get basic page info
        current_url = driver.current_url
        page_title = driver.title
        
        print(f"\n📄 Page Info:")
        print(f"URL: {current_url}")
        print(f"Title: {page_title}")
        
        # Check for common elements
        print(f"\n🔍 Element Analysis:")
        
        # Count basic elements
        elements = {
            'tables': driver.find_elements(By.TAG_NAME, "table"),
            'divs': driver.find_elements(By.TAG_NAME, "div"),
            'forms': driver.find_elements(By.TAG_NAME, "form"),
            'links': driver.find_elements(By.TAG_NAME, "a"),
            'spans': driver.find_elements(By.TAG_NAME, "span"),
            'paragraphs': driver.find_elements(By.TAG_NAME, "p")
        }
        
        for element_type, element_list in elements.items():
            print(f"  {element_type}: {len(element_list)}")
        
        # Analyze tables in detail
        print(f"\n📊 Table Analysis:")
        tables = elements['tables']
        
        for i, table in enumerate(tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"  Table {i}: {len(rows)} rows")
                
                if rows:
                    # Analyze first few rows
                    for j, row in enumerate(rows[:3]):
                        cells = row.find_elements(By.TAG_NAME, "td")
                        th_cells = row.find_elements(By.TAG_NAME, "th")
                        total_cells = len(cells) + len(th_cells)
                        
                        print(f"    Row {j}: {total_cells} cells")
                        
                        # Show cell contents for first row
                        if j == 0 and (cells or th_cells):
                            all_cells = th_cells + cells
                            cell_texts = [cell.text.strip()[:30] for cell in all_cells[:5]]  # First 5 cells
                            print(f"      Content: {cell_texts}")
            except Exception as e:
                print(f"    Error analyzing table {i}: {e}")
        
        # Look for text that might indicate results
        print(f"\n📝 Text Content Analysis:")
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            full_text = body.text
            
            # Look for key indicators
            indicators = ['palm beach', 'property', 'address', 'owner', 'value', 'sqft', 'parcel', '$']
            found_indicators = []
            
            for indicator in indicators:
                count = full_text.lower().count(indicator)
                if count > 0:
                    found_indicators.append(f"{indicator}: {count}")
            
            print(f"  Key terms found: {found_indicators}")
            
            # Show first 500 characters
            print(f"  First 500 chars of page text:")
            print(f"  '{full_text[:500]}...'")
            
        except Exception as e:
            print(f"  Error analyzing text content: {e}")
        
        # Look for specific PAPA elements
        print(f"\n🏠 PAPA-Specific Element Check:")
        papa_selectors = [
            "[class*='result']",
            "[class*='property']", 
            "[class*='search']",
            "[class*='record']",
            "[id*='result']",
            "[id*='property']",
            ".data-table",
            "#results",
            "#searchResults"
        ]
        
        for selector in papa_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  {selector}: {len(elements)} elements")
                    # Show first element's text preview
                    if elements[0].text.strip():
                        preview = elements[0].text.strip()[:100]
                        print(f"    Preview: '{preview}...'")
            except Exception as e:
                print(f"  {selector}: Error - {e}")
        
        # Save full page source for manual inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_file = f"papa_debug_full_{timestamp}.html"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        print(f"\n💾 Full page source saved to: {html_file}")
        print("   You can open this file in a text editor to see all HTML")
        
        # Check if there are any iframes
        print(f"\n🖼️  Iframe Check:")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"  Found {len(iframes)} iframes")
        
        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute("src") or "No src"
            print(f"    Iframe {i}: {src[:50]}...")
        
        print(f"\n✅ Analysis complete!")
        print(f"Check the saved HTML file for detailed inspection: {html_file}")
        
        input("Press ENTER to close browser...")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    debug_papa_page()