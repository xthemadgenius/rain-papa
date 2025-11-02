#!/usr/bin/env python3
"""
Palm Beach County Property Appraiser Results Extractor

A comprehensive Python script that intelligently extracts property data from 
Palm Beach County Property Appraiser search results and converts it to CSV format.

Features:
- Connects to existing browser session or opens new one
- Waits for user to load search results
- Intelligently detects result structures (tables, divs, lists, etc.)
- Extracts comprehensive property information
- Handles multiple result formats gracefully
- Exports to timestamped CSV files
- Provides clear user feedback and error handling
- Shows sample of extracted data

Author: Created for property data extraction automation
Date: 2025
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup


@dataclass
class PropertyRecord:
    """Data structure for property information"""
    property_address: str = ""
    owner_name: str = ""
    property_value: str = ""
    assessed_value: str = ""
    market_value: str = ""
    square_footage: str = ""
    property_type: str = ""
    parcel_id: str = ""
    account_number: str = ""
    sale_price: str = ""
    sale_date: str = ""
    year_built: str = ""
    lot_size: str = ""
    bedrooms: str = ""
    bathrooms: str = ""
    property_use: str = ""
    municipality: str = ""
    neighborhood: str = ""
    zoning: str = ""
    tax_amount: str = ""
    homestead_exemption: str = ""
    additional_info: str = ""
    record_url: str = ""


class PropertyExtractor:
    """Main class for extracting property data from PAPA search results"""
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the PropertyExtractor
        
        Args:
            debug_mode: Enable detailed logging and debug output
        """
        self.debug_mode = debug_mode
        self.setup_logging()
        self.driver = None
        self.wait = None
        
    def setup_logging(self):
        """Configure logging for the extractor"""
        log_level = logging.DEBUG if self.debug_mode else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'property_extractor_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self, headless: bool = False) -> bool:
        """
        Setup Chrome WebDriver with optimized options
        
        Args:
            headless: Run browser in headless mode
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if headless:
                chrome_options.add_argument("--headless")
                
            # Increase page load timeout
            chrome_options.add_argument("--page-load-strategy=eager")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            
            self.logger.info("✅ Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False
    
    def connect_to_existing_session(self) -> bool:
        """
        Attempt to connect to an existing browser session
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            # Try to connect to existing Chrome session on default debugging port
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Test connection
            current_url = self.driver.current_url
            self.logger.info(f"✅ Connected to existing browser session: {current_url}")
            return True
            
        except Exception as e:
            self.logger.debug(f"Could not connect to existing session: {e}")
            return False
    
    def wait_for_results_page(self) -> bool:
        """
        Wait for user to navigate to results page and confirm
        
        Returns:
            bool: True if ready to proceed
        """
        print("\n" + "="*80)
        print("🎯 PROPERTY RESULTS EXTRACTOR")
        print("="*80)
        print("Instructions:")
        print("1. Make sure you have completed your property search")
        print("2. Navigate to the results page in your browser")
        print("3. Ensure all results are loaded (scroll if needed)")
        print("4. Come back here and confirm when ready")
        print()
        
        while True:
            response = input("Are you ready to extract data? (y/n/url): ").lower().strip()
            
            if response == 'y':
                try:
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    self.logger.info(f"Current page: {page_title} - {current_url}")
                    
                    if "search" in current_url.lower() or "result" in current_url.lower():
                        return True
                    else:
                        print("⚠️  It looks like you might not be on a results page.")
                        confirm = input("Continue anyway? (y/n): ").lower()
                        return confirm == 'y'
                        
                except Exception as e:
                    self.logger.error(f"Error checking current page: {e}")
                    return True  # Proceed anyway
                    
            elif response == 'n':
                print("Please complete your search and return when ready.")
                continue
                
            elif response == 'url':
                try:
                    url = input("Enter the results page URL: ").strip()
                    if url:
                        self.driver.get(url)
                        time.sleep(3)
                        print("✅ Navigated to provided URL")
                        return True
                    else:
                        print("No URL provided")
                        continue
                except Exception as e:
                    print(f"Error navigating to URL: {e}")
                    continue
            else:
                print("Please enter 'y', 'n', or 'url'")
    
    def analyze_page_structure(self) -> Dict[str, any]:
        """
        Analyze the current page to understand its structure
        
        Returns:
            dict: Analysis results including detected structures
        """
        self.logger.info("🔍 Analyzing page structure...")
        
        analysis = {
            'tables': [],
            'result_containers': [],
            'pagination': False,
            'total_results': 0,
            'structure_type': 'unknown'
        }
        
        try:
            # Look for tables
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            for i, table in enumerate(tables):
                rows = table.find_elements(By.TAG_NAME, "tr")
                if len(rows) > 1:  # Has header and data rows
                    analysis['tables'].append({
                        'index': i,
                        'rows': len(rows),
                        'element': table
                    })
            
            # Look for common result container patterns
            container_selectors = [
                ".property-result",
                ".result-item",
                ".search-result",
                "[data-property]",
                ".property-card",
                ".listing",
                "[class*='result']",
                "[class*='property']"
            ]
            
            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        analysis['result_containers'].append({
                            'selector': selector,
                            'count': len(containers),
                            'elements': containers
                        })
                except:
                    continue
            
            # Check for pagination
            pagination_selectors = [
                ".pagination",
                ".pager",
                "[class*='page']",
                "a[href*='page']"
            ]
            
            for selector in pagination_selectors:
                try:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        analysis['pagination'] = True
                        break
                except:
                    continue
            
            # Determine structure type
            if analysis['tables']:
                analysis['structure_type'] = 'table'
                analysis['total_results'] = max(table['rows'] - 1 for table in analysis['tables'])  # -1 for header
            elif analysis['result_containers']:
                analysis['structure_type'] = 'containers'
                analysis['total_results'] = max(container['count'] for container in analysis['result_containers'])
            else:
                analysis['structure_type'] = 'text_based'
            
            self.logger.info(f"📊 Page structure analysis complete:")
            self.logger.info(f"   Structure type: {analysis['structure_type']}")
            self.logger.info(f"   Tables found: {len(analysis['tables'])}")
            self.logger.info(f"   Container types: {len(analysis['result_containers'])}")
            self.logger.info(f"   Estimated results: {analysis['total_results']}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing page structure: {e}")
            return analysis
    
    def extract_from_table(self, table_element) -> List[PropertyRecord]:
        """
        Extract data from a table structure
        
        Args:
            table_element: The table WebElement to extract from
            
        Returns:
            List of PropertyRecord objects
        """
        records = []
        
        try:
            # Get all rows
            rows = table_element.find_elements(By.TAG_NAME, "tr")
            
            if len(rows) < 2:
                return records
            
            # Analyze header row to map columns
            header_row = rows[0]
            headers = [th.text.strip().lower() for th in header_row.find_elements(By.TAG_NAME, "th")]
            
            if not headers:
                headers = [td.text.strip().lower() for td in header_row.find_elements(By.TAG_NAME, "td")]
            
            self.logger.debug(f"Table headers: {headers}")
            
            # Create column mapping
            column_mapping = self._create_column_mapping(headers)
            
            # Extract data from remaining rows
            for row_idx, row in enumerate(rows[1:], 1):
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) == 0:
                    continue
                
                record = PropertyRecord()
                
                for col_idx, cell in enumerate(cells):
                    if col_idx < len(headers):
                        field_name = column_mapping.get(col_idx)
                        if field_name:
                            cell_text = self._clean_text(cell.text)
                            setattr(record, field_name, cell_text)
                
                # Try to extract URLs from links in the row
                links = row.find_elements(By.TAG_NAME, "a")
                if links:
                    record.record_url = links[0].get_attribute("href") or ""
                
                records.append(record)
                
                if self.debug_mode:
                    self.logger.debug(f"Extracted row {row_idx}: {record.property_address[:50]}...")
            
            self.logger.info(f"✅ Extracted {len(records)} records from table")
            return records
            
        except Exception as e:
            self.logger.error(f"Error extracting from table: {e}")
            return records
    
    def extract_from_containers(self, containers) -> List[PropertyRecord]:
        """
        Extract data from container-based results
        
        Args:
            containers: List of container WebElements
            
        Returns:
            List of PropertyRecord objects
        """
        records = []
        
        try:
            for idx, container in enumerate(containers):
                record = PropertyRecord()
                
                # Extract text content
                container_text = container.text
                
                # Look for specific patterns in the text
                record.property_address = self._extract_address(container_text)
                record.owner_name = self._extract_owner_name(container)
                record.property_value = self._extract_values(container_text, ['value', 'assessment', 'appraised'])
                record.square_footage = self._extract_square_footage(container_text)
                record.parcel_id = self._extract_parcel_id(container_text)
                record.sale_price = self._extract_values(container_text, ['sale', 'sold', 'price'])
                record.sale_date = self._extract_date(container_text)
                
                # Look for links
                links = container.find_elements(By.TAG_NAME, "a")
                if links:
                    record.record_url = links[0].get_attribute("href") or ""
                
                # Try to extract additional structured data
                self._extract_additional_details(container, record)
                
                records.append(record)
                
                if self.debug_mode:
                    self.logger.debug(f"Extracted container {idx + 1}: {record.property_address[:50]}...")
            
            self.logger.info(f"✅ Extracted {len(records)} records from containers")
            return records
            
        except Exception as e:
            self.logger.error(f"Error extracting from containers: {e}")
            return records
    
    def extract_from_text(self) -> List[PropertyRecord]:
        """
        Extract data using text-based parsing when no clear structure is found
        
        Returns:
            List of PropertyRecord objects
        """
        records = []
        
        try:
            # Get page source and parse with BeautifulSoup for better text handling
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            # Split into potential record blocks
            # Look for common separators
            separators = ['\n\n', '---', '===', '___', 'Property #', 'Record #']
            
            blocks = [text_content]
            for sep in separators:
                new_blocks = []
                for block in blocks:
                    new_blocks.extend(block.split(sep))
                blocks = new_blocks
            
            # Filter blocks that seem to contain property data
            property_blocks = []
            for block in blocks:
                block = block.strip()
                if len(block) > 100:  # Minimum length for property record
                    # Check if it contains property-like information
                    if any(keyword in block.lower() for keyword in [
                        'address', 'owner', 'parcel', 'value', 'sqft', 'sq ft', 'property'
                    ]):
                        property_blocks.append(block)
            
            # Extract data from each block
            for idx, block in enumerate(property_blocks[:50]):  # Limit to 50 to prevent overload
                record = PropertyRecord()
                
                record.property_address = self._extract_address(block)
                record.owner_name = self._extract_owner_from_text(block)
                record.property_value = self._extract_values(block, ['value', 'assessment', 'appraised'])
                record.square_footage = self._extract_square_footage(block)
                record.parcel_id = self._extract_parcel_id(block)
                record.sale_price = self._extract_values(block, ['sale', 'sold', 'price'])
                record.sale_date = self._extract_date(block)
                record.additional_info = block[:500]  # Store first 500 chars as additional info
                
                records.append(record)
                
                if self.debug_mode:
                    self.logger.debug(f"Extracted text block {idx + 1}: {record.property_address[:50]}...")
            
            self.logger.info(f"✅ Extracted {len(records)} records from text parsing")
            return records
            
        except Exception as e:
            self.logger.error(f"Error extracting from text: {e}")
            return records
    
    def _create_column_mapping(self, headers: List[str]) -> Dict[int, str]:
        """Create mapping from column index to PropertyRecord field"""
        mapping = {}
        
        field_keywords = {
            'property_address': ['address', 'location', 'street', 'property location'],
            'owner_name': ['owner', 'name', 'taxpayer'],
            'property_value': ['value', 'assessment', 'assessed', 'appraised', 'market value'],
            'square_footage': ['sqft', 'sq ft', 'square', 'footage', 'area', 'size'],
            'parcel_id': ['parcel', 'id', 'account', 'number', 'pcn'],
            'sale_price': ['sale', 'sold', 'price', 'amount'],
            'sale_date': ['date', 'sold date', 'sale date'],
            'year_built': ['year built', 'built', 'construction'],
            'property_type': ['type', 'use', 'classification'],
            'municipality': ['city', 'municipality', 'jurisdiction'],
            'lot_size': ['lot', 'land', 'acreage'],
            'bedrooms': ['bed', 'br', 'bedroom'],
            'bathrooms': ['bath', 'bathroom', 'ba'],
            'zoning': ['zone', 'zoning']
        }
        
        for col_idx, header in enumerate(headers):
            header_lower = header.lower()
            for field, keywords in field_keywords.items():
                if any(keyword in header_lower for keyword in keywords):
                    mapping[col_idx] = field
                    break
        
        return mapping
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if not text:
            return ""
        
        # Remove extra whitespace and line breaks
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = re.sub(r'[^\w\s\-\.\,\$\#\(\)\/]', '', text)
        
        return text
    
    def _extract_address(self, text: str) -> str:
        """Extract property address from text"""
        # Common address patterns
        patterns = [
            r'\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:ST|AVE|RD|DR|LN|CT|PL|WAY|BLVD|CIR))',
            r'\d+\s+[A-Z\s]+(?:STREET|AVENUE|ROAD|DRIVE|LANE|COURT|PLACE|WAY|BOULEVARD|CIRCLE)',
            r'Address[:\s]+([^\n\r]+)',
            r'Property[:\s]+([^\n\r]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if pattern.startswith('Address') or pattern.startswith('Property'):
                    return match.group(1).strip()
                else:
                    return match.group(0).strip()
        
        return ""
    
    def _extract_owner_name(self, element) -> str:
        """Extract owner name from container element"""
        try:
            # Look for common owner field patterns
            owner_selectors = [
                "[class*='owner']",
                "[class*='name']",
                "[class*='taxpayer']"
            ]
            
            for selector in owner_selectors:
                try:
                    owner_element = element.find_element(By.CSS_SELECTOR, selector)
                    return self._clean_text(owner_element.text)
                except:
                    continue
            
            # Fallback to text extraction
            return self._extract_owner_from_text(element.text)
            
        except:
            return ""
    
    def _extract_owner_from_text(self, text: str) -> str:
        """Extract owner name from text"""
        patterns = [
            r'Owner[:\s]+([^\n\r]+)',
            r'Taxpayer[:\s]+([^\n\r]+)',
            r'Name[:\s]+([^\n\r]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_values(self, text: str, keywords: List[str]) -> str:
        """Extract monetary values from text"""
        for keyword in keywords:
            pattern = f"{keyword}[:\s]*\$?([0-9,]+(?:\.[0-9]{{2}})?)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"${match.group(1)}"
        
        return ""
    
    def _extract_square_footage(self, text: str) -> str:
        """Extract square footage from text"""
        patterns = [
            r'(\d{1,6}(?:,\d{3})*)\s*(?:sq\.?\s*ft\.?|sqft|square\s*feet)',
            r'(?:sqft|sq\.?\s*ft\.?)[:\s]*(\d{1,6}(?:,\d{3})*)',
            r'square\s*footage[:\s]*(\d{1,6}(?:,\d{3})*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_parcel_id(self, text: str) -> str:
        """Extract parcel ID from text"""
        patterns = [
            r'(?:parcel|pcn|account)[:\s#]*([A-Z0-9\-]+)',
            r'([0-9]{2}-[0-9]{4}-[0-9]{3}-[0-9]{4})',  # Common PBC format
            r'([0-9]{10,15})'  # Numeric ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_date(self, text: str) -> str:
        """Extract dates from text"""
        patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\w+ \d{1,2}, \d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_additional_details(self, container, record: PropertyRecord):
        """Extract additional details from container"""
        try:
            # Look for specific data attributes
            attributes = [
                'data-property-type', 'data-zoning', 'data-municipality',
                'data-bedrooms', 'data-bathrooms', 'data-lot-size'
            ]
            
            for attr in attributes:
                value = container.get_attribute(attr)
                if value:
                    field_name = attr.replace('data-', '').replace('-', '_')
                    if hasattr(record, field_name):
                        setattr(record, field_name, value)
        
        except:
            pass
    
    def extract_all_data(self) -> List[PropertyRecord]:
        """
        Main extraction method that tries different strategies
        
        Returns:
            List of PropertyRecord objects
        """
        all_records = []
        
        # Analyze page structure
        analysis = self.analyze_page_structure()
        
        # Try table extraction first
        if analysis['structure_type'] == 'table':
            for table_info in analysis['tables']:
                records = self.extract_from_table(table_info['element'])
                all_records.extend(records)
        
        # Try container extraction
        elif analysis['structure_type'] == 'containers':
            for container_info in analysis['result_containers']:
                records = self.extract_from_containers(container_info['elements'])
                all_records.extend(records)
        
        # Fallback to text extraction
        else:
            records = self.extract_from_text()
            all_records.extend(records)
        
        # Remove duplicates based on address and parcel ID
        unique_records = self._remove_duplicates(all_records)
        
        self.logger.info(f"🎯 Total unique records extracted: {len(unique_records)}")
        return unique_records
    
    def _remove_duplicates(self, records: List[PropertyRecord]) -> List[PropertyRecord]:
        """Remove duplicate records"""
        seen = set()
        unique_records = []
        
        for record in records:
            # Create a unique key based on address and parcel ID
            key = f"{record.property_address.lower().strip()}|{record.parcel_id.strip()}"
            
            if key not in seen and (record.property_address or record.parcel_id):
                seen.add(key)
                unique_records.append(record)
        
        return unique_records
    
    def handle_pagination(self) -> List[PropertyRecord]:
        """
        Handle paginated results
        
        Returns:
            List of all records from all pages
        """
        all_records = []
        page_num = 1
        
        while True:
            self.logger.info(f"📄 Processing page {page_num}...")
            
            # Extract data from current page
            page_records = self.extract_all_data()
            all_records.extend(page_records)
            
            # Look for next page button
            next_button = None
            next_selectors = [
                "a[href*='next']",
                "a:contains('Next')",
                ".pagination .next",
                "input[value*='Next']",
                "button:contains('Next')"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        break
                    else:
                        next_button = None
                except:
                    continue
            
            if not next_button:
                break
            
            # Click next page
            try:
                next_button.click()
                time.sleep(3)  # Wait for page to load
                page_num += 1
                
                # Safety limit
                if page_num > 50:
                    self.logger.warning("⚠️  Reached maximum page limit (50)")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error navigating to next page: {e}")
                break
        
        self.logger.info(f"📊 Processed {page_num} pages total")
        return all_records
    
    def export_to_csv(self, records: List[PropertyRecord], filename: str = None) -> str:
        """
        Export records to CSV file
        
        Args:
            records: List of PropertyRecord objects
            filename: Optional custom filename
            
        Returns:
            str: Path to the created CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"palm_beach_properties_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if not records:
                    self.logger.warning("⚠️  No records to export")
                    return filename
                
                # Get field names from the first record
                fieldnames = [field.name for field in records[0].__dataclass_fields__]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in records:
                    writer.writerow(asdict(record))
                
                self.logger.info(f"✅ Successfully exported {len(records)} records to {filename}")
                
                # Show sample data
                self._show_sample_data(records)
                
                return filename
                
        except Exception as e:
            self.logger.error(f"❌ Error exporting to CSV: {e}")
            return ""
    
    def export_to_json(self, records: List[PropertyRecord], filename: str = None) -> str:
        """
        Export records to JSON file
        
        Args:
            records: List of PropertyRecord objects  
            filename: Optional custom filename
            
        Returns:
            str: Path to the created JSON file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"palm_beach_properties_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                data = [asdict(record) for record in records]
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
                
                self.logger.info(f"✅ Successfully exported {len(records)} records to {filename}")
                return filename
                
        except Exception as e:
            self.logger.error(f"❌ Error exporting to JSON: {e}")
            return ""
    
    def _show_sample_data(self, records: List[PropertyRecord], num_samples: int = 3):
        """Show sample of extracted data"""
        print(f"\n📋 Sample of extracted data (showing {min(num_samples, len(records))} records):")
        print("="*80)
        
        for i, record in enumerate(records[:num_samples]):
            print(f"\n🏠 Record {i+1}:")
            print("-" * 40)
            
            # Show non-empty fields
            for field_name, field_value in asdict(record).items():
                if field_value and field_value.strip():
                    # Format field name for display
                    display_name = field_name.replace('_', ' ').title()
                    # Truncate long values
                    display_value = str(field_value)[:100]
                    if len(str(field_value)) > 100:
                        display_value += "..."
                    print(f"   {display_name}: {display_value}")
        
        print("\n" + "="*80)
    
    def run_extraction(self) -> Optional[str]:
        """
        Main method to run the complete extraction process
        
        Returns:
            str: Path to CSV file if successful, None otherwise
        """
        print("🚀 Starting Property Results Extraction...")
        
        # Try to connect to existing browser session first
        if not self.connect_to_existing_session():
            print("No existing browser session found. Opening new browser...")
            if not self.setup_driver():
                print("❌ Failed to setup browser. Please ensure Chrome is installed.")
                return None
        
        try:
            # Wait for user to load results
            if not self.wait_for_results_page():
                print("❌ User cancelled or page not ready")
                return None
            
            print("\n🔄 Starting data extraction...")
            
            # Check if pagination exists
            analysis = self.analyze_page_structure()
            
            if analysis['pagination']:
                print("📄 Pagination detected. Will process all pages...")
                records = self.handle_pagination()
            else:
                print("📄 Single page detected. Processing current page...")
                records = self.extract_all_data()
            
            if not records:
                print("❌ No property records found. Please check:")
                print("   - Are you on the correct results page?")
                print("   - Are there any results displayed?")
                print("   - Try refreshing the page and running again")
                return None
            
            # Export to CSV
            csv_file = self.export_to_csv(records)
            
            # Also export to JSON for backup
            json_file = self.export_to_json(records)
            
            print(f"\n🎉 Extraction completed successfully!")
            print(f"📊 Total records extracted: {len(records)}")
            print(f"📁 CSV file: {csv_file}")
            print(f"📁 JSON file: {json_file}")
            
            return csv_file
            
        except KeyboardInterrupt:
            print("\n⏹️  Extraction cancelled by user")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during extraction: {e}")
            return None
        
        finally:
            # Keep browser open for user inspection
            if self.driver:
                print("\n⏳ Keeping browser open for 60 seconds for your review...")
                try:
                    time.sleep(60)
                    self.driver.quit()
                except:
                    pass


def main():
    """Main entry point"""
    print("="*80)
    print("🏠 PALM BEACH COUNTY PROPERTY APPRAISER")
    print("    INTELLIGENT RESULTS EXTRACTOR")
    print("="*80)
    print()
    print("This script will:")
    print("✅ Connect to your browser or open a new one")
    print("✅ Wait for you to load property search results")
    print("✅ Intelligently detect the page structure")
    print("✅ Extract comprehensive property information")
    print("✅ Export data to timestamped CSV and JSON files")
    print("✅ Show sample extracted data for verification")
    print()
    
    # Ask for debug mode
    debug_choice = input("Enable debug mode for detailed logging? (y/n): ").lower()
    debug_mode = debug_choice == 'y'
    
    # Create extractor instance
    extractor = PropertyExtractor(debug_mode=debug_mode)
    
    try:
        # Run extraction
        csv_file = extractor.run_extraction()
        
        if csv_file:
            print(f"\n🎯 SUCCESS! Property data exported to: {csv_file}")
            print("You can now open this file in Excel or any spreadsheet application.")
        else:
            print("\n❌ Extraction failed. Check the logs for details.")
    
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        logging.exception("Fatal error in main")
    
    finally:
        print("\n👋 Thank you for using the Property Results Extractor!")
        print("For support or issues, check the log file for detailed information.")


if __name__ == "__main__":
    main()