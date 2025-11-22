#!/usr/bin/env python3
"""
Multi-Page Property Extractor for Palm Beach County Property Appraiser

This script automatically:
1. Connects to existing browser session from pbc_property_search.py
2. Extracts data from current page
3. Navigates to next page every 45 seconds
4. Combines all data into one large CSV file
5. Continues until no more pages are found
"""

import time
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dataclasses import dataclass, asdict
import os

@dataclass
class PropertyRecord:
    """Data class for property information"""
    property_address: str = ""
    owner_name: str = ""
    parcel_number: str = ""
    property_value: str = ""
    assessed_value: str = ""
    market_value: str = ""
    square_footage: str = ""
    property_type: str = ""
    sale_price: str = ""
    sale_date: str = ""
    year_built: str = ""
    lot_size: str = ""
    bedrooms: str = ""
    bathrooms: str = ""
    municipality: str = ""
    zoning: str = ""
    tax_amount: str = ""
    record_url: str = ""
    extraction_date: str = ""
    page_number: int = 0

class MultiPageExtractor:
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.driver = None
        self.logger = self.setup_logging()
        self.all_records = []
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_filename = f"multi_page_extractor_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = os.path.join("extracted", log_filename)
        
        # Create extracted directory if it doesn't exist
        os.makedirs("extracted", exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO if self.debug_mode else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def connect_to_browser(self) -> bool:
        """Connect to existing browser session"""
        try:
            print("🔗 Connecting to existing Chrome browser session...")
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            print(f"✅ Connected to browser successfully!")
            print(f"   Current page: {page_title}")
            print(f"   URL: {current_url}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to browser: {e}")
            print(f"❌ Failed to connect to browser session: {e}")
            print("Make sure you ran 'python3 pbc_property_search.py' first and browser is still open")
            return False

    def wait_for_page_load(self, timeout: int = 10) -> bool:
        """Wait for page to fully load"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  # Additional buffer
            return True
        except TimeoutException:
            self.logger.warning(f"Page load timeout after {timeout} seconds")
            return False

    def extract_current_page_data(self, page_number: int) -> List[PropertyRecord]:
        """Extract property data from current page"""
        print(f"📄 Extracting data from page {page_number}...")
        records = []
        
        try:
            # Wait for page to load
            self.wait_for_page_load()
            
            # Look for common table structures first
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            if tables:
                print(f"   Found {len(tables)} tables on page")
                for table_idx, table in enumerate(tables):
                    table_records = self.extract_from_table(table, page_number)
                    records.extend(table_records)
                    print(f"   Table {table_idx + 1}: {len(table_records)} records")
            
            # If no tables, look for result rows/divs
            if not records:
                result_rows = self.find_result_rows()
                if result_rows:
                    print(f"   Found {len(result_rows)} result rows")
                    records = self.extract_from_rows(result_rows, page_number)
                    
            # Fallback to text extraction
            if not records:
                print("   Using fallback text extraction...")
                records = self.extract_from_text(page_number)
            
            print(f"✅ Extracted {len(records)} records from page {page_number}")
            return records
            
        except Exception as e:
            self.logger.error(f"Error extracting data from page {page_number}: {e}")
            print(f"❌ Error on page {page_number}: {e}")
            return []

    def extract_from_table(self, table, page_number: int) -> List[PropertyRecord]:
        """Extract data from HTML table"""
        records = []
        
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row_idx, row in enumerate(rows[1:], 1):  # Skip header
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) >= 3:  # Minimum cells for meaningful data
                    record = PropertyRecord()
                    record.page_number = page_number
                    record.extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Extract text from each cell
                    cell_texts = [cell.text.strip() for cell in cells]
                    
                    # Common patterns for property data
                    for i, text in enumerate(cell_texts):
                        if text:
                            # Address patterns
                            if any(keyword in text.upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR']):
                                record.property_address = text
                            # Owner name (usually has spaces and proper case)
                            elif ' ' in text and text.replace(' ', '').replace(',', '').isalpha():
                                if not record.owner_name:  # Take first name found
                                    record.owner_name = text
                            # Parcel/Account number (usually alphanumeric)
                            elif any(c.isdigit() for c in text) and len(text) >= 6:
                                if not record.parcel_number:
                                    record.parcel_number = text
                            # Values (contain $ or are large numbers)
                            elif '$' in text or (text.replace(',', '').replace('.', '').isdigit() and len(text.replace(',', '')) >= 4):
                                if '$' in text:
                                    if not record.property_value:
                                        record.property_value = text
                                    elif not record.assessed_value:
                                        record.assessed_value = text
                                    elif not record.market_value:
                                        record.market_value = text
                    
                    # Get links from the row
                    links = row.find_elements(By.TAG_NAME, "a")
                    if links:
                        record.record_url = links[0].get_attribute("href") or ""
                    
                    # Only add record if it has meaningful data
                    if record.property_address or record.owner_name or record.parcel_number:
                        records.append(record)
                        
        except Exception as e:
            self.logger.error(f"Error extracting from table: {e}")
            
        return records

    def find_result_rows(self):
        """Find result rows using various patterns"""
        selectors = [
            "div[class*='result']",
            "tr[class*='result']",
            "div[class*='property']",
            "div[class*='record']",
            ".search-result",
            ".property-result",
            "[id*='result']"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 1:  # Found multiple results
                    return elements
            except:
                continue
                
        return []

    def extract_from_rows(self, rows, page_number: int) -> List[PropertyRecord]:
        """Extract data from result rows/divs"""
        records = []
        
        for row in rows:
            try:
                record = PropertyRecord()
                record.page_number = page_number
                record.extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                row_text = row.text
                self.extract_patterns_from_text(row_text, record)
                
                # Get links
                links = row.find_elements(By.TAG_NAME, "a")
                if links:
                    record.record_url = links[0].get_attribute("href") or ""
                
                if record.property_address or record.owner_name or record.parcel_number:
                    records.append(record)
                    
            except Exception as e:
                self.logger.error(f"Error processing row: {e}")
                continue
                
        return records

    def extract_from_text(self, page_number: int) -> List[PropertyRecord]:
        """Fallback text extraction method"""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Split into potential records (basic heuristic)
            lines = page_text.split('\n')
            records = []
            current_record = PropertyRecord()
            current_record.page_number = page_number
            current_record.extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for line in lines:
                line = line.strip()
                if line:
                    self.extract_patterns_from_text(line, current_record)
            
            if current_record.property_address or current_record.owner_name:
                records.append(current_record)
                
            return records
            
        except Exception as e:
            self.logger.error(f"Error in text extraction: {e}")
            return []

    def extract_patterns_from_text(self, text: str, record: PropertyRecord):
        """Extract common patterns from text"""
        import re
        
        # Address patterns
        address_pattern = r'\b\d+\s+[A-Z][a-z]*\s+(St|Ave|Blvd|Rd|Ln|Ct|Dr|Way|Pl)\b'
        if not record.property_address:
            address_match = re.search(address_pattern, text, re.IGNORECASE)
            if address_match:
                record.property_address = address_match.group().strip()
        
        # Dollar amounts
        dollar_pattern = r'\$[\d,]+\.?\d*'
        dollar_matches = re.findall(dollar_pattern, text)
        if dollar_matches:
            if not record.property_value:
                record.property_value = dollar_matches[0]
            if len(dollar_matches) > 1 and not record.assessed_value:
                record.assessed_value = dollar_matches[1]
        
        # Parcel numbers (alphanumeric with dashes/spaces)
        parcel_pattern = r'\b[A-Z0-9][\w\-\s]{6,20}\b'
        if not record.parcel_number:
            parcel_match = re.search(parcel_pattern, text)
            if parcel_match and any(c.isdigit() for c in parcel_match.group()):
                record.parcel_number = parcel_match.group().strip()

    def navigate_to_next_page(self, current_page: int) -> bool:
        """Navigate to next page"""
        try:
            print(f"🔄 Looking for next page button on page {current_page}...")
            
            # Common next page patterns
            next_patterns = [
                "//a[contains(text(), 'Next')]",
                "//button[contains(text(), 'Next')]",
                "//input[contains(@value, 'Next')]",
                "//a[contains(text(), '>')]",
                "//button[contains(text(), '>')]",
                f"//a[text()='{current_page + 1}']",
                "//a[@title='Next Page']",
                "//*[contains(@class, 'next')]",
                "//*[contains(@id, 'next')]"
            ]
            
            for pattern in next_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"   Found next button: {element.text or element.get_attribute('value')}")
                            
                            # Scroll to element
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)
                            
                            # Click using JavaScript for reliability
                            self.driver.execute_script("arguments[0].click();", element)
                            
                            print(f"✅ Clicked next page button")
                            
                            # Wait for page to load
                            self.wait_for_page_load(15)
                            
                            return True
                            
                except Exception as e:
                    continue
            
            print("🚫 No next page button found - reached end")
            return False
            
        except Exception as e:
            self.logger.error(f"Error navigating to next page: {e}")
            print(f"❌ Error navigating to next page: {e}")
            return False

    def save_results_to_csv(self, filename: str = None) -> str:
        """Save all extracted records to CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extracted/multi_page_properties_{timestamp}.csv"
        
        os.makedirs("extracted", exist_ok=True)
        
        if not self.all_records:
            print("⚠️ No records to save")
            return filename
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                # Get all field names from the dataclass
                fieldnames = list(asdict(self.all_records[0]).keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in self.all_records:
                    writer.writerow(asdict(record))
            
            print(f"✅ Saved {len(self.all_records)} records to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error saving CSV: {e}")
            print(f"❌ Error saving CSV: {e}")
            return filename

    def run_multi_page_extraction(self, max_pages: int = 50):
        """Main extraction workflow"""
        print("🚀 Starting Multi-Page Property Extraction")
        print("=" * 60)
        
        # Connect to browser
        if not self.connect_to_browser():
            return
        
        page_number = 1
        consecutive_empty_pages = 0
        
        try:
            while page_number <= max_pages:
                print(f"\n📄 Processing Page {page_number}")
                print("-" * 40)
                
                # Extract data from current page
                page_records = self.extract_current_page_data(page_number)
                
                if page_records:
                    self.all_records.extend(page_records)
                    consecutive_empty_pages = 0
                    print(f"📊 Page {page_number}: {len(page_records)} records")
                    print(f"📈 Total so far: {len(self.all_records)} records")
                else:
                    consecutive_empty_pages += 1
                    print(f"⚠️ Page {page_number}: No data found")
                    
                    if consecutive_empty_pages >= 3:
                        print("🛑 Found 3 consecutive empty pages. Stopping extraction.")
                        break
                
                # Try to navigate to next page
                if not self.navigate_to_next_page(page_number):
                    print(f"🏁 No more pages found. Extraction complete.")
                    break
                
                page_number += 1
                
                # Wait 45 seconds as requested
                if page_number <= max_pages:
                    print(f"⏱️ Waiting 45 seconds before processing page {page_number}...")
                    time.sleep(45)
            
            # Save results
            print(f"\n🎉 Extraction Complete!")
            print("=" * 60)
            print(f"📊 Total pages processed: {page_number}")
            print(f"📊 Total records extracted: {len(self.all_records)}")
            
            if self.all_records:
                csv_file = self.save_results_to_csv()
                print(f"💾 Results saved to: {csv_file}")
            
        except KeyboardInterrupt:
            print(f"\n⏹️ Extraction stopped by user")
            if self.all_records:
                csv_file = self.save_results_to_csv()
                print(f"💾 Partial results saved to: {csv_file}")
        
        except Exception as e:
            self.logger.error(f"Fatal error in extraction: {e}")
            print(f"❌ Fatal error: {e}")
            if self.all_records:
                csv_file = self.save_results_to_csv()
                print(f"💾 Partial results saved to: {csv_file}")
        
        finally:
            print("\n👋 Multi-page extraction finished")

if __name__ == "__main__":
    print("Multi-Page Palm Beach County Property Extractor")
    print("=" * 60)
    print("This script will automatically:")
    print("• Connect to your existing browser session")
    print("• Extract data from all pages")
    print("• Navigate between pages every 45 seconds")
    print("• Save everything to one CSV file")
    print()
    
    extractor = MultiPageExtractor(debug_mode=True)
    extractor.run_multi_page_extraction()