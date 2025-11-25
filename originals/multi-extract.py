#!/usr/bin/env python3
"""
Multi-Page Property Extractor for Palm Beach County Property Appraiser

This script automatically:
1. Connects to existing browser session from pbc_property_search.py
2. Extracts data from current page
3. Navigates to next page every 8 seconds
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
    """PAPA GetSalesSearch results structure - matching exact page layout"""
    # Core fields in exact order from GetSalesSearch page
    sale_price: str = ""           # Sale Price (first priority field)
    sale_date: str = ""            # Sale Date 
    owner_name: str = ""           # Owner Name
    property_address: str = ""     # Location/Property Address
    municipality: str = ""         # Municipality
    square_footage: str = ""       # Sq. Ft
    mail_address: str = ""         # Mail Address
    mail_city_state_zip: str = ""  # Mail City, State, Zip
    homesteaded: str = ""          # Homestead status
    
    # Additional useful fields (secondary priority)
    parcel_number: str = ""        # Parcel/Account Number
    property_value: str = ""       # Assessed/Market Value
    lot_size: str = ""            # Lot Size
    year_built: str = ""          # Year Built
    property_type: str = ""       # Property Type
    
    # Meta fields
    record_url: str = ""          # Link to detailed record
    extraction_date: str = ""     # When extracted
    page_number: int = 0          # Which results page

class MultiPageExtractor:
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.driver = None
        self.logger = self.setup_logging()
        self.all_records = []
        self.total_pages = None
        self.current_page = 1
        
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

    def detect_total_pages(self) -> int:
        """Detect total number of pages from pagination controls"""
        try:
            print("🔍 Detecting total number of pages...")
            
            # Common pagination patterns to find total pages
            total_page_patterns = [
                # "Page 1 of 15" format
                "//text()[contains(., 'Page') and contains(., 'of')]",
                "//span[contains(text(), 'of') and contains(text(), 'Page')]",
                "//div[contains(text(), 'of') and contains(text(), 'Page')]",
                
                # "1 of 15" or "1/15" format
                "//text()[contains(., 'of ') and preceding-sibling::*[contains(., '1')]]",
                "//*[contains(text(), 'of ') and contains(text(), '/')]",
                
                # Last page number in pagination
                "//*[contains(@class, 'pagination')]//a[last()]",
                "//*[contains(@class, 'pager')]//a[last()]",
                "//*[contains(@id, 'pagination')]//a[last()]",
                
                # Look for highest numbered page link
                "//a[contains(@href, 'page') or contains(@href, 'Page')]",
                "//a[text() and string-length(text()) <= 3 and translate(text(), '0123456789', '') = '']"
            ]
            
            max_pages_found = 0
            
            # Try text-based detection first
            for pattern in total_page_patterns[:5]:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        text = element.text if hasattr(element, 'text') else str(element)
                        
                        # Look for "Page X of Y" or "X of Y" patterns
                        import re
                        matches = re.findall(r'(?:Page\s+)?(\d+)\s+of\s+(\d+)', text, re.IGNORECASE)
                        if matches:
                            total = int(matches[0][1])
                            current = int(matches[0][0])
                            print(f"   Found pagination text: '{text}' -> Total pages: {total}")
                            self.current_page = current
                            return total
                            
                        # Look for "X/Y" format
                        matches = re.findall(r'(\d+)\s*/\s*(\d+)', text)
                        if matches:
                            total = int(matches[0][1])
                            current = int(matches[0][0])
                            print(f"   Found pagination text: '{text}' -> Total pages: {total}")
                            self.current_page = current
                            return total
                            
                except Exception as e:
                    continue
            
            # Try numbered page links detection
            print("   Trying numbered page links detection...")
            try:
                page_links = self.driver.find_elements(By.XPATH, "//a[text() and string-length(text()) <= 3 and translate(text(), '0123456789', '') = '']")
                page_numbers = []
                
                for link in page_links:
                    try:
                        page_num = int(link.text.strip())
                        if 1 <= page_num <= 1000:  # Reasonable range
                            page_numbers.append(page_num)
                    except (ValueError, AttributeError):
                        continue
                
                if page_numbers:
                    max_pages_found = max(page_numbers)
                    print(f"   Found page numbers: {sorted(set(page_numbers))} -> Max page: {max_pages_found}")
                    
            except Exception as e:
                self.logger.error(f"Error detecting page numbers: {e}")
            
            # Try pagination container analysis
            print("   Trying pagination container analysis...")
            try:
                pagination_containers = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'pagination') or contains(@class, 'pager') or contains(@id, 'pagination')]")
                
                for container in pagination_containers:
                    # Look for any numbers in the container
                    container_text = container.text
                    numbers = re.findall(r'\b(\d+)\b', container_text)
                    if numbers:
                        # Take the largest reasonable number as potential max page
                        largest_num = max([int(n) for n in numbers if 1 <= int(n) <= 1000])
                        if largest_num > max_pages_found:
                            max_pages_found = largest_num
                            print(f"   Found in pagination container: {container_text} -> Potential max page: {largest_num}")
                            
            except Exception as e:
                self.logger.error(f"Error analyzing pagination containers: {e}")
            
            # Final fallback - look for any "next" or "last" indicators
            if max_pages_found == 0:
                print("   No specific page count found, will detect dynamically during navigation")
                return None
            
            print(f"✅ Detected total pages: {max_pages_found}")
            return max_pages_found
            
        except Exception as e:
            self.logger.error(f"Error detecting total pages: {e}")
            print(f"⚠️ Could not detect total pages: {e}")
            return None

    def get_current_page_number(self) -> int:
        """Try to detect current page number from the page"""
        try:
            # Look for current page indicators
            patterns = [
                "//span[contains(@class, 'current') or contains(@class, 'active')]",
                "//a[contains(@class, 'current') or contains(@class, 'active')]",
                "//li[contains(@class, 'current') or contains(@class, 'active')]//a",
                "//*[contains(@class, 'pagination')]//*[contains(@class, 'current') or contains(@class, 'active')]"
            ]
            
            for pattern in patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        text = element.text.strip()
                        if text.isdigit() and 1 <= int(text) <= 1000:
                            return int(text)
                except:
                    continue
                    
            return self.current_page  # Fallback to tracked page
            
        except Exception as e:
            self.logger.error(f"Error detecting current page: {e}")
            return self.current_page

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
        """Extract data from GetSalesSearch results table with proper field mapping"""
        records = []
        
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            # Get header row to understand column structure
            header_row = None
            if rows:
                header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                if not header_cells:  # Try td for headers
                    header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                
                if header_cells:
                    header_row = [cell.text.strip().lower() for cell in header_cells]
                    print(f"   📋 Table headers detected: {header_row}")
            
            # Process data rows (skip header)
            data_rows = rows[1:] if len(rows) > 1 else rows
            
            for row_idx, row in enumerate(data_rows):
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) < 3:  # Skip rows with too few cells
                    continue
                
                record = PropertyRecord()
                record.page_number = page_number
                record.extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Extract text from each cell
                cell_texts = [cell.text.strip() for cell in cells]
                
                # Map fields based on GetSalesSearch typical column order
                # Common GetSalesSearch columns: Sale Price, Sale Date, Owner, Address, Municipality, etc.
                
                if header_row:
                    # Use header-based mapping
                    for i, (header, text) in enumerate(zip(header_row, cell_texts)):
                        if not text:
                            continue
                            
                        # Map based on header content
                        if any(keyword in header for keyword in ['sale', 'price']) and '$' in text:
                            record.sale_price = text
                        elif any(keyword in header for keyword in ['sale', 'date']) and ('/' in text or '-' in text):
                            record.sale_date = text
                        elif any(keyword in header for keyword in ['owner', 'name', 'taxpayer']):
                            record.owner_name = text
                        elif any(keyword in header for keyword in ['address', 'location', 'property']):
                            record.property_address = text
                        elif any(keyword in header for keyword in ['municipality', 'city']):
                            record.municipality = text
                        elif any(keyword in header for keyword in ['sq', 'sqft', 'footage']):
                            record.square_footage = text
                        elif any(keyword in header for keyword in ['mail', 'mailing']) and 'address' in header:
                            record.mail_address = text
                        elif any(keyword in header for keyword in ['mail']) and any(k in header for k in ['city', 'state', 'zip']):
                            record.mail_city_state_zip = text
                        elif any(keyword in header for keyword in ['homestead']):
                            record.homesteaded = text
                        elif any(keyword in header for keyword in ['parcel', 'account']):
                            record.parcel_number = text
                
                else:
                    # Fallback: position-based mapping (common GetSalesSearch order)
                    print(f"   ⚠️ No headers found, using position-based mapping")
                    
                    for i, text in enumerate(cell_texts):
                        if not text:
                            continue
                        
                        # Position-based field assignment for typical GetSalesSearch layout
                        if i == 0:  # First column often sale price
                            if '$' in text:
                                record.sale_price = text
                            elif any(c.isdigit() for c in text):
                                record.parcel_number = text  # Sometimes parcel is first
                        elif i == 1:  # Second column often sale date
                            if '/' in text or '-' in text or any(month in text.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                                record.sale_date = text
                            elif '$' in text and not record.sale_price:
                                record.sale_price = text
                        elif i == 2:  # Third column often owner name
                            if (len(text) > 3 and 
                                not text.replace(' ', '').replace(',', '').replace('.', '').isdigit() and
                                not any(keyword in text.upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR', 'WAY', 'PL'])):
                                record.owner_name = text
                        elif i == 3:  # Fourth column often property address
                            if any(keyword in text.upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR', 'WAY', 'PL']):
                                record.property_address = text
                        elif i == 4:  # Fifth column often municipality
                            if len(text) > 2 and text.replace(' ', '').isalpha():
                                record.municipality = text
                        elif i == 5:  # Sixth column might be square footage
                            if text.replace(',', '').replace('.', '').isdigit():
                                record.square_footage = text
                
                # Additional pattern-based extraction for missed fields
                for i, text in enumerate(cell_texts):
                    if not text:
                        continue
                    
                    # Sale Price - look for $ amounts
                    if '$' in text and not record.sale_price:
                        record.sale_price = text
                    
                    # Owner Name - aggressive name detection
                    elif (not record.owner_name and 
                          len(text) > 3 and
                          not '$' in text and
                          not text.replace(',', '').replace('.', '').isdigit() and
                          not any(keyword in text.upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR', 'WAY', 'PL']) and
                          not any(city in text.upper() for city in ['PALM BEACH', 'WEST PALM', 'BOCA', 'DELRAY', 'BOYNTON', 'WELLINGTON', 'JUPITER'])):
                        # Check if it has characteristics of a person's name
                        words = text.split()
                        if (len(words) >= 1 and 
                            all(word.replace(',', '').replace('.', '').isalpha() for word in words) and
                            any(word[0].isupper() for word in words if word)):  # At least one capitalized word
                            record.owner_name = text.strip()
                    
                    # Property Address - look for street indicators
                    elif any(keyword in text.upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR', 'WAY', 'PL']) and not record.property_address:
                        record.property_address = text
                    
                    # Municipality - look for city names (alphabetic, 2+ words or known cities)
                    elif (text.replace(' ', '').replace('-', '').isalpha() and 
                          len(text) > 2 and 
                          not record.municipality and 
                          text != record.owner_name and  # Don't confuse with owner name
                          not any(keyword in text.upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR'])):
                        # Check if it looks like a city name
                        if ' ' in text or any(city in text.upper() for city in ['PALM BEACH', 'WEST PALM', 'BOCA', 'DELRAY', 'BOYNTON']):
                            record.municipality = text
                    
                    # Square footage - numeric values that could be sq ft
                    elif (text.replace(',', '').replace('.', '').isdigit() and 
                          500 <= int(text.replace(',', '')) <= 50000 and 
                          not record.square_footage):
                        record.square_footage = text
                
                # Get links from the row
                links = row.find_elements(By.TAG_NAME, "a")
                if links:
                    record.record_url = links[0].get_attribute("href") or ""
                
                # Debug: Show what we extracted for this row
                if self.debug_mode:
                    print(f"   🔍 Row {row_idx + 1} debug:")
                    print(f"      Raw cells: {cell_texts}")
                    print(f"      Sale Price: '{record.sale_price}'")
                    print(f"      Owner Name: '{record.owner_name}'")
                    print(f"      Address: '{record.property_address}'")
                    print(f"      Municipality: '{record.municipality}'")
                
                # Only add record if it has core data
                if (record.sale_price or record.property_address or record.owner_name or 
                    record.municipality or record.parcel_number):
                    records.append(record)
                    print(f"   ✓ Row {row_idx + 1}: ${record.sale_price} | {record.owner_name} | {record.property_address}")
                else:
                    print(f"   ⚠️ Row {row_idx + 1}: Insufficient data, skipped")
                    if self.debug_mode:
                        print(f"      Available data: {[text for text in cell_texts if text]}")
                        
        except Exception as e:
            self.logger.error(f"Error extracting from table: {e}")
            print(f"   ❌ Table extraction error: {e}")
            
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
        """Extract data from result rows/divs with proper field mapping"""
        records = []
        
        for row_idx, row in enumerate(rows):
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
                
                # Only add if we have meaningful data
                if (record.sale_price or record.property_address or record.owner_name or 
                    record.municipality or record.parcel_number):
                    records.append(record)
                    print(f"   ✓ Row {row_idx + 1}: ${record.sale_price} | {record.owner_name} | {record.property_address}")
                    
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
        """Extract GetSalesSearch-specific patterns from text"""
        import re
        
        # Sale Price - look for dollar amounts (prioritize sale price)
        dollar_pattern = r'\$[\d,]+\.?\d*'
        dollar_matches = re.findall(dollar_pattern, text)
        if dollar_matches and not record.sale_price:
            record.sale_price = dollar_matches[0]  # First dollar amount is likely sale price
        
        # Sale Date - various date formats
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',          # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',          # MM-DD-YYYY  
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',          # YYYY-MM-DD
            r'\b[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}\b' # Jan 15, 2024
        ]
        
        if not record.sale_date:
            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    record.sale_date = date_match.group().strip()
                    break
        
        # Property Address - street address patterns
        address_patterns = [
            r'\b\d+\s+[A-Za-z\s]+(St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Ln|Lane|Ct|Court|Dr|Drive|Way|Pl|Place)\b',
            r'\b\d+\s+[A-Z][A-Za-z\s]+\s+(ST|AVE|BLVD|RD|LN|CT|DR|WAY|PL)\b'
        ]
        
        if not record.property_address:
            for pattern in address_patterns:
                address_match = re.search(pattern, text, re.IGNORECASE)
                if address_match:
                    record.property_address = address_match.group().strip()
                    break
        
        # Owner Name - multiple patterns for better detection
        if not record.owner_name:
            # Pattern 1: Last, First format
            name_pattern1 = r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
            name_match1 = re.search(name_pattern1, text)
            if name_match1:
                record.owner_name = name_match1.group().strip()
            else:
                # Pattern 2: First Last format (2+ words, proper case)
                name_pattern2 = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
                name_matches2 = re.findall(name_pattern2, text)
                for name in name_matches2:
                    # Skip if it looks like an address, municipality, or other non-name
                    if (not any(keyword in name.upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR', 'WAY', 'PL']) and
                        not any(city in name.upper() for city in ['PALM BEACH', 'WEST PALM', 'BOCA RATON', 'DELRAY BEACH', 'BOYNTON BEACH', 'WELLINGTON', 'JUPITER']) and
                        name.strip() != record.property_address and
                        name.strip() != record.municipality and
                        len(name.strip()) > 3):
                        record.owner_name = name.strip()
                        break
                
                # Pattern 3: Single capitalized word (less preferred but sometimes needed)
                if not record.owner_name:
                    name_pattern3 = r'\b[A-Z][A-Z\s]+[A-Z]\b'  # ALL CAPS names
                    name_match3 = re.search(name_pattern3, text)
                    if (name_match3 and 
                        len(name_match3.group().strip()) > 3 and
                        not any(keyword in name_match3.group().upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR'])):
                        record.owner_name = name_match3.group().strip()
        
        # Municipality - city names (alphabetic, often multiple words)
        municipality_patterns = [
            r'\b(Palm Beach|West Palm Beach|Boca Raton|Delray Beach|Boynton Beach|Wellington|Jupiter|Lake Worth)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'  # General capitalized words
        ]
        
        if not record.municipality:
            for pattern in municipality_patterns:
                muni_matches = re.findall(pattern, text, re.IGNORECASE)
                for muni in muni_matches:
                    # Skip addresses, owner names already captured, and small words
                    if (not any(keyword in muni.upper() for keyword in ['ST', 'AVE', 'BLVD', 'RD', 'LN', 'CT', 'DR']) and
                        muni != record.owner_name and
                        muni != record.property_address and
                        len(muni) > 2):
                        record.municipality = muni.strip()
                        break
                if record.municipality:
                    break
        
        # Square Footage - numeric values in reasonable range
        sqft_pattern = r'\b([1-9]\d{2,4})\b'  # 100-99999 range
        if not record.square_footage:
            sqft_matches = re.findall(sqft_pattern, text)
            for sqft in sqft_matches:
                sqft_num = int(sqft)
                if 500 <= sqft_num <= 50000:  # Reasonable house size range
                    record.square_footage = sqft
                    break
        
        # Parcel/Account numbers - alphanumeric with dashes
        parcel_patterns = [
            r'\b[A-Z0-9]{2,3}-[0-9]{2,4}-[0-9]{2,4}\b',  # XX-XXXX-XXXX format
            r'\b\d{2}-\d{2}-\d{2}-\d{2,5}\b',            # NN-NN-NN-NNNNN format
            r'\b[A-Z0-9]{10,15}\b'                        # Long alphanumeric
        ]
        
        if not record.parcel_number:
            for pattern in parcel_patterns:
                parcel_match = re.search(pattern, text)
                if parcel_match:
                    record.parcel_number = parcel_match.group().strip()
                    break
        
        # Homestead status - Y/N or Yes/No patterns
        homestead_pattern = r'\b(Y|N|Yes|No|TRUE|FALSE)\b'
        if not record.homesteaded:
            homestead_match = re.search(homestead_pattern, text, re.IGNORECASE)
            if homestead_match:
                record.homesteaded = homestead_match.group().strip()

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
        
        # Detect total pages available
        self.total_pages = self.detect_total_pages()
        
        if self.total_pages:
            print(f"📊 Total pages detected: {self.total_pages}")
            actual_max_pages = min(max_pages, self.total_pages)
        else:
            print(f"🔍 Page count unknown, will detect during navigation (max {max_pages})")
            actual_max_pages = max_pages
        
        # Get current page number
        self.current_page = self.get_current_page_number()
        print(f"📍 Starting from page: {self.current_page}")
        
        page_number = self.current_page
        consecutive_empty_pages = 0
        
        try:
            while page_number <= actual_max_pages:
                print(f"\n📄 Processing Page {page_number}")
                if self.total_pages:
                    print(f"    Progress: {page_number}/{self.total_pages} ({(page_number/self.total_pages*100):.1f}%)")
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
                
                # Check if we've reached the known total
                if self.total_pages and page_number >= self.total_pages:
                    print(f"🏁 Reached final page ({self.total_pages}). Extraction complete.")
                    break
                
                # Try to navigate to next page
                if not self.navigate_to_next_page(page_number):
                    print(f"🏁 No more pages found. Extraction complete.")
                    break
                
                page_number += 1
                self.current_page = page_number
                
                # Wait 8 seconds as requested
                if page_number <= actual_max_pages:
                    if self.total_pages:
                        print(f"⏱️ Waiting 8 seconds before processing page {page_number}/{self.total_pages}...")
                    else:
                        print(f"⏱️ Waiting 8 seconds before processing page {page_number}...")
                    time.sleep(8)
            
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
    print("• Navigate between pages every 8 seconds")
    print("• Save everything to one CSV file")
    print()
    
    extractor = MultiPageExtractor(debug_mode=True)
    extractor.run_multi_page_extraction()