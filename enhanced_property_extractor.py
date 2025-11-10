#!/usr/bin/env python3
"""
Enhanced Palm Beach County Property Appraiser Results Extractor

Improved version with:
- Better PAPA-specific data patterns
- More reliable extraction methods  
- Enhanced CSV output with proper formatting
- Robust error handling and recovery
- Natural timing and behavior
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
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import random

@dataclass
class PropertyRecord:
    """Enhanced data structure for PAPA property information with required fields"""
    # Primary identification
    parcel_number: str = ""  # Required: Parcel Number
    property_address: str = ""  # Required: Location
    owner_name: str = ""  # Required: Owner Name
    
    # Financial information  
    sale_price: str = ""  # Required: Sale Price
    sale_date: str = ""  # Required: Sale Date
    property_value: str = ""
    assessed_value: str = ""
    market_value: str = ""
    taxable_value: str = ""
    
    # Property details
    square_footage: str = ""  # Required: Sq. Ft
    lot_size: str = ""  # Required: Lot Size (renamed from lot_sqft)
    acres: str = ""  # Required: Acres
    municipality: str = ""  # Required: Municipality
    zoning: str = ""  # Required: Zoning
    
    # Mailing information
    mail_address: str = ""  # Required: Mail Address (renamed from mailing_address)
    mail_city_state_zip: str = ""  # Required: Mail City, State, Zip
    
    # Status
    homesteaded: str = ""  # Required: Homesteaded (renamed from homestead_exemption)
    
    # Legacy/additional fields
    property_type: str = ""
    property_use: str = ""
    account_number: str = ""
    folio_number: str = ""
    deed_book: str = ""
    year_built: str = ""
    bedrooms: str = ""
    bathrooms: str = ""
    half_baths: str = ""
    neighborhood: str = ""
    subdivision: str = ""
    land_use_code: str = ""
    building_class: str = ""
    tax_amount: str = ""
    exemption_amount: str = ""
    school_district: str = ""
    additional_info: str = ""
    record_url: str = ""
    extraction_date: str = ""

class EnhancedPropertyExtractor:
    """Enhanced extractor with PAPA-specific improvements"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.setup_logging()
        self.driver = None
        self.wait = None
        
    def setup_logging(self):
        """Configure logging"""
        log_level = logging.DEBUG if self.debug_mode else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'enhanced_property_extractor_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self) -> bool:
        """Setup Chrome with natural behavior patterns"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Natural user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Remove automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            self.wait = WebDriverWait(self.driver, 20)
            
            self.logger.info("✅ Enhanced Chrome WebDriver initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False
    
    def natural_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add natural human-like delays"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def wait_for_results_page(self) -> bool:
        """Enhanced user interaction for results page"""
        print("\n" + "="*80)
        print("🎯 ENHANCED PAPA RESULTS EXTRACTOR")
        print("="*80)
        
        # Check if we're already on a results page
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            print(f"Connected to page: {page_title}")
            print(f"URL: {current_url}")
            
            # Check if this looks like a results page
            if any(indicator in current_url.lower() for indicator in ['search', 'result']) or \
               any(indicator in page_title.lower() for indicator in ['search', 'result', 'property']):
                print("✅ Already connected to what appears to be a search results page!")
                
                auto_proceed = input("Proceed with extraction automatically? (y/n): ").lower().strip()
                if auto_proceed == 'y':
                    self.natural_delay(1, 2)
                    return True
        except Exception as e:
            self.logger.error(f"Error checking current page: {e}")
        
        print("\nInstructions:")
        print("1. Make sure you've clicked SEARCH and results are loaded")
        print("2. Ensure all results are visible (scroll if needed)")
        print("3. Confirm when ready to extract")
        print()
        
        while True:
            response = input("Are results loaded and ready to extract? (y/n): ").lower().strip()
            
            if response == 'y':
                try:
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    self.logger.info(f"Starting extraction on: {page_title} - {current_url}")
                    
                    # Wait for page to be fully loaded
                    self.natural_delay(2, 4)
                    return True
                        
                except Exception as e:
                    self.logger.error(f"Error checking current page: {e}")
                    return True
                    
            elif response == 'n':
                print("Please complete your search and return when ready.")
                print("Make sure to click SEARCH and wait for results to load.")
                continue
            else:
                print("Please enter 'y' or 'n'")
    
    def analyze_papa_page_structure(self) -> Dict[str, any]:
        """PAPA-specific page structure analysis"""
        self.logger.info("🔍 Analyzing PAPA page structure...")
        
        analysis = {
            'tables': [],
            'result_rows': [],
            'property_links': [],
            'pagination': False,
            'total_results': 0,
            'structure_type': 'unknown'
        }
        
        try:
            # Look for PAPA-specific result tables
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            for i, table in enumerate(tables):
                rows = table.find_elements(By.TAG_NAME, "tr")
                if len(rows) > 1:
                    # Check if this looks like a results table
                    header_text = table.text.lower()
                    if any(keyword in header_text for keyword in [
                        'property', 'address', 'owner', 'value', 'parcel', 'account'
                    ]):
                        analysis['tables'].append({
                            'index': i,
                            'rows': len(rows),
                            'element': table
                        })
            
            # Look for result rows (PAPA often uses table rows for results)
            result_rows = self.driver.find_elements(By.XPATH, "//tr[td[contains(@class, 'result') or contains(text(), 'PALM BEACH')]]")
            if not result_rows:
                # Broader search for data rows
                result_rows = self.driver.find_elements(By.XPATH, "//tr[count(td) >= 3]")
            
            analysis['result_rows'] = result_rows
            
            # Look for property detail links
            property_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'property') or contains(@href, 'parcel') or contains(@href, 'detail')]")
            analysis['property_links'] = property_links
            
            # Check for pagination
            pagination_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Next') or contains(text(), 'Page') or contains(@class, 'page')]")
            analysis['pagination'] = len(pagination_indicators) > 0
            
            # Determine structure type
            if analysis['tables']:
                analysis['structure_type'] = 'table'
                analysis['total_results'] = sum(table['rows'] - 1 for table in analysis['tables'])
            elif analysis['result_rows']:
                analysis['structure_type'] = 'rows'
                analysis['total_results'] = len(analysis['result_rows'])
            else:
                analysis['structure_type'] = 'text_based'
            
            self.logger.info(f"📊 PAPA page analysis complete:")
            self.logger.info(f"   Structure type: {analysis['structure_type']}")
            self.logger.info(f"   Data tables: {len(analysis['tables'])}")
            self.logger.info(f"   Result rows: {len(analysis['result_rows'])}")
            self.logger.info(f"   Property links: {len(analysis['property_links'])}")
            self.logger.info(f"   Estimated results: {analysis['total_results']}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing PAPA page structure: {e}")
            return analysis
    
    def extract_from_papa_table(self, table_element) -> List[PropertyRecord]:
        """Enhanced table extraction for PAPA results"""
        records = []
        
        try:
            rows = table_element.find_elements(By.TAG_NAME, "tr")
            if len(rows) < 2:
                return records
            
            # Analyze headers with PAPA-specific mapping
            header_row = rows[0]
            headers = []
            
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            if not header_cells:
                header_cells = header_row.find_elements(By.TAG_NAME, "td")
            
            for cell in header_cells:
                headers.append(cell.text.strip().lower())
            
            self.logger.debug(f"PAPA table headers: {headers}")
            
            # Create enhanced PAPA column mapping
            column_mapping = self._create_papa_column_mapping(headers)
            
            # Extract data from rows
            for row_idx, row in enumerate(rows[1:], 1):
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) == 0:
                    continue
                
                record = PropertyRecord()
                record.extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Extract cell data
                for col_idx, cell in enumerate(cells):
                    if col_idx < len(headers):
                        field_name = column_mapping.get(col_idx)
                        if field_name:
                            cell_text = self._clean_papa_text(cell.text)
                            setattr(record, field_name, cell_text)
                
                # Look for links to property details
                links = row.find_elements(By.TAG_NAME, "a")
                if links:
                    record.record_url = links[0].get_attribute("href") or ""
                
                # Extract additional info from the entire row
                row_text = row.text
                self._extract_papa_patterns(row_text, record)
                
                # Only add records with meaningful data
                if record.property_address or record.owner_name or record.parcel_number:
                    records.append(record)
                    
                    if self.debug_mode:
                        self.logger.debug(f"Extracted PAPA row {row_idx}: {record.property_address[:50]}...")
                
                # Natural delay between row processing
                if row_idx % 10 == 0:
                    self.natural_delay(0.1, 0.3)
            
            self.logger.info(f"✅ Extracted {len(records)} records from PAPA table")
            return records
            
        except Exception as e:
            self.logger.error(f"Error extracting from PAPA table: {e}")
            return records
    
    def _create_papa_column_mapping(self, headers: List[str]) -> Dict[int, str]:
        """Create PAPA-specific column mapping"""
        mapping = {}
        
        papa_field_keywords = {
            'property_address': ['address', 'location', 'street', 'site address', 'property location', 'situs'],
            'owner_name': ['owner', 'name', 'taxpayer', 'owner name', 'taxpayer name'],
            'mail_address': ['mailing', 'mail', 'mailing address', 'owner address'],
            'mail_city_state_zip': ['mail city', 'mail state', 'mail zip', 'city state zip', 'owner city'],
            'property_value': ['just value', 'market value', 'assessed', 'assessment', 'total value'],
            'assessed_value': ['assessed', 'assessed value', 'assessment'],
            'market_value': ['market', 'market value', 'fair market'],
            'taxable_value': ['taxable', 'taxable value', 'net taxable'],
            'square_footage': ['sqft', 'sq ft', 'square', 'footage', 'building area', 'living area'],
            'lot_size': ['lot', 'land', 'lot size', 'lot sqft', 'land sqft', 'lot area'],
            'acres': ['acres', 'acreage', 'acre'],
            'parcel_number': ['parcel', 'pcn', 'parcel id', 'parcel number'],
            'account_number': ['account', 'account number', 'acct'],
            'folio_number': ['folio', 'folio number'],
            'sale_price': ['sale', 'sold', 'price', 'sale price', 'last sale'],
            'sale_date': ['date', 'sold date', 'sale date', 'last sale date'],
            'year_built': ['year built', 'built', 'construction', 'year constructed'],
            'property_type': ['type', 'property type', 'class'],
            'property_use': ['use', 'land use', 'property use'],
            'municipality': ['city', 'municipality', 'jurisdiction'],
            'neighborhood': ['neighborhood', 'district', 'area'],
            'subdivision': ['subdivision', 'subdiv', 'plat'],
            'zoning': ['zone', 'zoning'],
            'land_use_code': ['land use', 'use code', 'luc'],
            'building_class': ['class', 'building class', 'bldg class'],
            'bedrooms': ['bed', 'br', 'bedroom', 'bedrooms'],
            'bathrooms': ['bath', 'bathroom', 'ba', 'full bath'],
            'half_baths': ['half bath', 'half', 'powder'],
            'tax_amount': ['tax', 'taxes', 'tax amount', 'annual tax'],
            'homesteaded': ['homestead', 'homestead exempt', 'homesteaded'],
            'exemption_amount': ['exempt', 'exemption', 'exempt amount']
        }
        
        for col_idx, header in enumerate(headers):
            header_lower = header.lower()
            for field, keywords in papa_field_keywords.items():
                if any(keyword in header_lower for keyword in keywords):
                    mapping[col_idx] = field
                    break
        
        return mapping
    
    def _clean_papa_text(self, text: str) -> str:
        """Clean text with PAPA-specific patterns"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Clean common PAPA formatting
        text = re.sub(r'^[:\-\s]+|[:\-\s]+$', '', text)  # Remove leading/trailing punctuation
        text = re.sub(r'\$\s*(\d)', r'$\1', text)  # Fix currency formatting
        
        return text
    
    def _extract_papa_patterns(self, text: str, record: PropertyRecord):
        """Extract PAPA-specific data patterns from text"""
        
        # Property address patterns (PAPA specific)
        if not record.property_address:
            address_patterns = [
                r'(\d+\s+[A-Z\s]+(?:ST|AVE|RD|DR|LN|CT|PL|WAY|BLVD|CIR)(?:\s+(?:APT|UNIT|STE)\s*[\w\d]+)?)',
                r'(\d+\s+[A-Z][A-Z\s]+[A-Z](?:\s+(?:STREET|AVENUE|ROAD|DRIVE|LANE|COURT|PLACE|WAY|BOULEVARD|CIRCLE)))',
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    record.property_address = match.group(1).strip()
                    break
        
        # Parcel Number patterns (PAPA format: XX-XXXX-XXX-XXXX)
        if not record.parcel_number:
            parcel_patterns = [
                r'([0-9]{2}-[0-9]{4}-[0-9]{3}-[0-9]{4})',
                r'PCN[:\s]*([A-Z0-9\-]+)',
                r'Parcel[:\s]*([A-Z0-9\-]+)'
            ]
            
            for pattern in parcel_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    record.parcel_number = match.group(1)
                    break
        
        # Value patterns with proper currency formatting
        if not record.property_value:
            value_patterns = [
                r'Just Value[:\s]*\$([0-9,]+)',
                r'Market Value[:\s]*\$([0-9,]+)',
                r'Total Value[:\s]*\$([0-9,]+)'
            ]
            
            for pattern in value_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    record.property_value = f"${match.group(1)}"
                    break
        
        # Municipality (should be Palm Beach)
        if not record.municipality:
            if "palm beach" in text.lower():
                record.municipality = "Palm Beach"
        
        # Acres patterns
        if not record.acres:
            acres_patterns = [
                r'([0-9]+\.?[0-9]*) acre[s]?',
                r'Acres?[:\s]*([0-9]+\.?[0-9]*)',
                r'([0-9]+\.?[0-9]*) ac'
            ]
            
            for pattern in acres_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    record.acres = match.group(1)
                    break
        
        # Mail City, State, Zip patterns
        if not record.mail_city_state_zip:
            mail_patterns = [
                r'([A-Z\s]+,\s*[A-Z]{2}\s+[0-9]{5}(?:-[0-9]{4})?)',
                r'Mail.*?([A-Z\s]+,\s*[A-Z]{2}\s+[0-9]{5})',
                r'Owner.*?([A-Z\s]+,\s*FL\s+[0-9]{5})'
            ]
            
            for pattern in mail_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    record.mail_city_state_zip = match.group(1).strip()
                    break
        
        # Homesteaded patterns
        if not record.homesteaded:
            homestead_patterns = [
                r'Homestead[:\s]*(Yes|No|Y|N)',
                r'Homesteaded[:\s]*(Yes|No|Y|N)',
                r'(Homestead Exemption)',
                r'(Yes).*?homestead',
                r'(No).*?homestead'
            ]
            
            for pattern in homestead_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).upper()
                    if value in ['YES', 'Y', 'HOMESTEAD EXEMPTION']:
                        record.homesteaded = 'Yes'
                    elif value in ['NO', 'N']:
                        record.homesteaded = 'No'
                    else:
                        record.homesteaded = value
                    break
        
        # Lot Size (additional to existing patterns)
        if not record.lot_size:
            lot_patterns = [
                r'Lot Size[:\s]*([0-9,]+)\s*sq\s*ft',
                r'Land Area[:\s]*([0-9,]+)',
                r'([0-9,]+)\s*sq\s*ft\s*lot'
            ]
            
            for pattern in lot_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    record.lot_size = match.group(1)
                    break
    
    def extract_all_papa_data(self) -> List[PropertyRecord]:
        """Main extraction method for PAPA data"""
        all_records = []
        
        # Analyze page structure
        analysis = self.analyze_papa_page_structure()
        
        # Try table extraction first (most common for PAPA)
        if analysis['structure_type'] == 'table':
            for table_info in analysis['tables']:
                self.logger.info(f"Processing PAPA table {table_info['index']} with {table_info['rows']} rows...")
                records = self.extract_from_papa_table(table_info['element'])
                all_records.extend(records)
                self.natural_delay(0.5, 1.0)
        
        # Try row-based extraction
        elif analysis['structure_type'] == 'rows':
            self.logger.info(f"Processing {len(analysis['result_rows'])} result rows...")
            for idx, row in enumerate(analysis['result_rows']):
                record = PropertyRecord()
                record.extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                row_text = row.text
                self._extract_papa_patterns(row_text, record)
                
                # Get links
                links = row.find_elements(By.TAG_NAME, "a")
                if links:
                    record.record_url = links[0].get_attribute("href") or ""
                
                if record.property_address or record.owner_name or record.parcel_number:
                    all_records.append(record)
                
                if idx % 5 == 0:
                    self.natural_delay(0.2, 0.5)
        
        # Fallback to text extraction
        else:
            self.logger.info("Using fallback text extraction...")
            all_records = self._extract_from_papa_text()
        
        # Remove duplicates
        unique_records = self._remove_duplicates(all_records)
        
        self.logger.info(f"🎯 Total unique PAPA records extracted: {len(unique_records)}")
        return unique_records
    
    def _extract_from_papa_text(self) -> List[PropertyRecord]:
        """Fallback text extraction for PAPA"""
        records = []
        
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            # Split by common PAPA separators
            blocks = re.split(r'\n\s*\n|\t\t+|_{3,}|-{3,}', text_content)
            
            # Filter for property-like blocks
            property_blocks = []
            for block in blocks:
                block = block.strip()
                if len(block) > 50 and any(keyword in block.lower() for keyword in [
                    'palm beach', 'parcel', 'property', 'owner', 'address', 'value'
                ]):
                    property_blocks.append(block)
            
            # Extract from blocks
            for idx, block in enumerate(property_blocks[:50]):
                record = PropertyRecord()
                record.extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                record.additional_info = block[:300]
                
                self._extract_papa_patterns(block, record)
                
                if record.property_address or record.owner_name or record.parcel_number:
                    records.append(record)
            
            self.logger.info(f"✅ Extracted {len(records)} records from text parsing")
            return records
            
        except Exception as e:
            self.logger.error(f"Error in text extraction: {e}")
            return records
    
    def _remove_duplicates(self, records: List[PropertyRecord]) -> List[PropertyRecord]:
        """Remove duplicates based on multiple criteria"""
        seen = set()
        unique_records = []
        
        for record in records:
            # Create unique key based on multiple fields
            key_parts = [
                record.property_address.lower().strip(),
                record.parcel_number.strip(),
                record.owner_name.lower().strip()
            ]
            key = "|".join(key_parts)
            
            if key not in seen and any(key_parts):
                seen.add(key)
                unique_records.append(record)
        
        return unique_records
    
    def export_to_enhanced_csv(self, records: List[PropertyRecord], filename: str = None) -> str:
        """Export to CSV with enhanced formatting"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"palm_beach_properties_enhanced_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:  # UTF-8 BOM for Excel
                if not records:
                    self.logger.warning("⚠️  No records to export")
                    return filename
                
                # Define field order for better CSV layout
                field_order = [
                    'property_address', 'owner_name', 'mailing_address',
                    'property_value', 'assessed_value', 'market_value', 'taxable_value',
                    'square_footage', 'lot_sqft', 'year_built',
                    'bedrooms', 'bathrooms', 'half_baths',
                    'property_type', 'property_use', 'building_class',
                    'parcel_id', 'account_number', 'folio_number',
                    'sale_price', 'sale_date', 'deed_book',
                    'municipality', 'neighborhood', 'subdivision', 'zoning',
                    'land_use_code', 'school_district',
                    'tax_amount', 'homestead_exemption', 'exemption_amount',
                    'record_url', 'additional_info', 'extraction_date'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=field_order)
                
                # Write header with friendly names
                friendly_headers = {
                    'property_address': 'Property Address',
                    'owner_name': 'Owner Name',
                    'mailing_address': 'Mailing Address',
                    'property_value': 'Property Value',
                    'assessed_value': 'Assessed Value',
                    'market_value': 'Market Value',
                    'taxable_value': 'Taxable Value',
                    'square_footage': 'Square Footage',
                    'lot_sqft': 'Lot Size (SqFt)',
                    'year_built': 'Year Built',
                    'bedrooms': 'Bedrooms',
                    'bathrooms': 'Bathrooms',
                    'half_baths': 'Half Baths',
                    'property_type': 'Property Type',
                    'property_use': 'Property Use',
                    'building_class': 'Building Class',
                    'parcel_id': 'Parcel ID',
                    'account_number': 'Account Number',
                    'folio_number': 'Folio Number',
                    'sale_price': 'Sale Price',
                    'sale_date': 'Sale Date',
                    'deed_book': 'Deed Book',
                    'municipality': 'Municipality',
                    'neighborhood': 'Neighborhood',
                    'subdivision': 'Subdivision',
                    'zoning': 'Zoning',
                    'land_use_code': 'Land Use Code',
                    'school_district': 'School District',
                    'tax_amount': 'Tax Amount',
                    'homestead_exemption': 'Homestead Exemption',
                    'exemption_amount': 'Exemption Amount',
                    'record_url': 'Record URL',
                    'additional_info': 'Additional Info',
                    'extraction_date': 'Extraction Date'
                }
                
                writer.writerow(friendly_headers)
                
                # Write data
                for record in records:
                    record_dict = asdict(record)
                    writer.writerow(record_dict)
                
                self.logger.info(f"✅ Successfully exported {len(records)} records to {filename}")
                
                # Show sample data
                self._show_enhanced_sample_data(records)
                
                return filename
                
        except Exception as e:
            self.logger.error(f"❌ Error exporting to CSV: {e}")
            return ""
    
    def _show_enhanced_sample_data(self, records: List[PropertyRecord], num_samples: int = 2):
        """Show enhanced sample of extracted data"""
        print(f"\n📋 Sample of extracted PAPA data (showing {min(num_samples, len(records))} records):")
        print("="*100)
        
        for i, record in enumerate(records[:num_samples]):
            print(f"\n🏠 Property Record {i+1}:")
            print("-" * 50)
            
            # Show key fields in logical order
            key_fields = [
                ('Property Address', record.property_address),
                ('Owner Name', record.owner_name),
                ('Property Value', record.property_value),
                ('Square Footage', record.square_footage),
                ('Parcel ID', record.parcel_id),
                ('Municipality', record.municipality),
                ('Year Built', record.year_built),
                ('Sale Price', record.sale_price),
                ('Sale Date', record.sale_date)
            ]
            
            for field_name, field_value in key_fields:
                if field_value and field_value.strip():
                    print(f"   {field_name:18}: {field_value}")
            
            if record.record_url:
                print(f"   {'Record URL':18}: {record.record_url[:60]}...")
        
        print("\n" + "="*100)
    
    def connect_to_search_session(self) -> bool:
        """Connect to the existing search browser session"""
        try:
            print("🔗 Attempting to connect to existing browser session...")
            
            # Connect to the Chrome session started by the search script
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Test connection
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            print(f"✅ Connected to existing browser session!")
            print(f"   Current page: {page_title}")
            print(f"   URL: {current_url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Could not connect to existing browser session: {e}")
            print("Make sure the search script (pbc_property_search.py) is still running!")
            return False

    def run_enhanced_extraction(self) -> Optional[str]:
        """Main enhanced extraction method"""
        print("🚀 Starting Enhanced PAPA Results Extraction...")
        
        # Try to connect to existing browser session first
        if not self.connect_to_search_session():
            print("\n⚠️  Could not connect to existing browser session.")
            print("Please make sure:")
            print("1. You ran 'python3 pbc_property_search.py' first")
            print("2. That browser window is still open")
            print("3. You've completed the search and have results loaded")
            
            # Fallback to new browser
            print("\nFalling back to new browser session...")
            if not self.setup_driver():
                print("❌ Failed to setup browser. Please ensure Chrome is installed.")
                return None
        
        try:
            # Wait for user to load results
            if not self.wait_for_results_page():
                print("❌ User cancelled or page not ready")
                return None
            
            print("\n🔄 Starting enhanced data extraction...")
            
            # Extract data
            records = self.extract_all_papa_data()
            
            if not records:
                print("❌ No property records found. Please check:")
                print("   - Are you on the PAPA results page?")
                print("   - Are there search results displayed?")
                print("   - Try scrolling to ensure all results are loaded")
                return None
            
            # Export to enhanced CSV
            csv_file = self.export_to_enhanced_csv(records)
            
            # Also export to JSON for backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = f"palm_beach_properties_enhanced_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                data = [asdict(record) for record in records]
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n🎉 Enhanced extraction completed successfully!")
            print(f"📊 Total records extracted: {len(records)}")
            print(f"📁 Enhanced CSV file: {csv_file}")
            print(f"📁 JSON backup file: {json_file}")
            print(f"📝 Log file: enhanced_property_extractor_{datetime.now().strftime('%Y%m%d')}.log")
            
            return csv_file
            
        except KeyboardInterrupt:
            print("\n⏹️  Extraction cancelled by user")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during extraction: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Keep browser open for review
            if self.driver:
                print("\n⏳ Keeping browser open for 30 seconds for review...")
                try:
                    time.sleep(30)
                    self.driver.quit()
                except:
                    pass

def main():
    """Enhanced main entry point"""
    print("="*100)
    print("🏠 ENHANCED PALM BEACH COUNTY PROPERTY APPRAISER")
    print("    INTELLIGENT RESULTS EXTRACTOR")
    print("="*100)
    print()
    print("Enhanced features:")
    print("✅ PAPA-specific data extraction patterns")
    print("✅ Natural browser behavior to avoid detection")
    print("✅ Enhanced CSV formatting with friendly headers")
    print("✅ Robust error handling and recovery")
    print("✅ Comprehensive property data capture")
    print("✅ Excel-compatible UTF-8 encoding")
    print()
    
    # Ask for debug mode
    debug_choice = input("Enable debug mode for detailed logging? (y/n): ").lower()
    debug_mode = debug_choice == 'y'
    
    # Create enhanced extractor
    extractor = EnhancedPropertyExtractor(debug_mode=debug_mode)
    
    try:
        # Run enhanced extraction
        csv_file = extractor.run_enhanced_extraction()
        
        if csv_file:
            print(f"\n🎯 SUCCESS! Enhanced property data exported to: {csv_file}")
            print("You can now open this file in Excel or any spreadsheet application.")
            print("The CSV includes friendly column headers and proper formatting.")
        else:
            print("\n❌ Extraction failed. Check the logs for details.")
    
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        logging.exception("Fatal error in enhanced main")
    
    finally:
        print("\n👋 Thank you for using the Enhanced Property Results Extractor!")
        print("For support, check the log file for detailed information.")

if __name__ == "__main__":
    main()