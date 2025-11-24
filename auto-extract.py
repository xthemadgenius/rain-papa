#!/usr/bin/env python3
"""
Headless Automated Property Extraction Script

This script provides seamless headless execution:
1. Runs property search in headless Chrome (no visible browser)
2. Automatically fills form and performs search
3. Extracts data from ALL pages automatically  
4. Produces one consolidated CSV with all property records

Usage: python3 auto-extract.py
"""

import subprocess
import time
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

class AutomatedPropertyExtraction:
    def __init__(self):
        self.search_process = None
        self.driver = None
        self.start_time = datetime.now()
        
    def print_header(self):
        """Print header information"""
        print("🚀 Headless Property Extraction Pipeline")
        print("=" * 60)
        print("This will automatically:")
        print("• Run headless Chrome browser (no visible window)")
        print("• Fill property search form automatically")  
        print("• Extract data from ALL pages automatically")
        print("• Save everything to one CSV file")
        print("=" * 60)
        print()

    def create_headless_search_script(self):
        """Create a temporary headless version of pbc_property_search.py"""
        print("🔧 Creating headless search script...")
        
        try:
            # Read the original pbc_property_search.py
            with open('pbc_property_search.py', 'r') as f:
                original_script = f.read()
            
            # Modify it to be headless
            headless_script = original_script.replace(
                'chrome_options.add_argument("--remote-debugging-port=9222")',
                '''chrome_options.add_argument("--headless")
    chrome_options.add_argument("--remote-debugging-port=9222")'''
            )
            
            # Write temporary headless version
            with open('temp_headless_search.py', 'w') as f:
                f.write(headless_script)
            
            print("✅ Created temporary headless search script")
            return True
            
        except Exception as e:
            print(f"❌ Error creating headless script: {e}")
            return False
    
    def run_headless_search(self):
        """Run property search using modified headless version"""
        print("🔍 Step 1: Running Headless Property Search...")
        print("-" * 40)
        
        try:
            # Create headless version of search script
            if not self.create_headless_search_script():
                return False
            
            # Run the headless search script
            print("🚀 Starting headless property search with anti-bot measures...")
            result = subprocess.run([
                sys.executable, 'temp_headless_search.py'
            ], capture_output=True, text=True, timeout=180)  # 3 minute timeout
            
            if result.returncode == 0:
                print("✅ Headless search completed successfully!")
                
                # Connect to the headless browser
                time.sleep(5)  # Give time for browser to settle
                
                try:
                    chrome_options = Options()
                    chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
                    self.driver = webdriver.Chrome(options=chrome_options)
                    
                    current_url = self.driver.current_url
                    print(f"🎯 Connected to headless browser: {current_url}")
                    
                    # Check if we're on results page
                    if 'GetSalesSearch' in current_url:
                        print("✅ Successfully on results page!")
                        return True
                    else:
                        print(f"⚠️ Not on expected results page, continuing anyway...")
                        return True
                        
                except Exception as e:
                    print(f"⚠️ Could not connect to headless browser: {e}")
                    return False
                    
            else:
                print(f"❌ Search script failed with return code: {result.returncode}")
                if result.stdout:
                    print(f"Output: {result.stdout}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Search script timeout - may still be running")
            # Try to connect anyway
            try:
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", "localhost:9222") 
                self.driver = webdriver.Chrome(options=chrome_options)
                return True
            except:
                return False
                
        except Exception as e:
            print(f"❌ Error in headless search: {e}")
            return False
        
        finally:
            # Cleanup temporary file
            try:
                if os.path.exists('temp_headless_search.py'):
                    os.remove('temp_headless_search.py')
                    print("🧹 Cleaned up temporary files")
            except:
                pass

    def verify_page_ready(self):
        """Verify the results page is fully loaded"""
        print(f"\n✅ Step 2: Verifying Results Page Ready")
        print("-" * 40)
        
        max_attempts = 5
        
        for attempt in range(1, max_attempts + 1):
            print(f"🔍 Verification attempt {attempt}/{max_attempts}...")
            
            try:
                current_url = self.driver.current_url
                print(f"   Current URL: {current_url}")
                
                # Check for data content
                if self.has_results_data():
                    print(f"✅ Page ready with data! (attempt {attempt})")
                    return True
                else:
                    print(f"⏳ Data still loading... (attempt {attempt})")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"⚠️ Verification error: {str(e)[:50]}")
                time.sleep(3)
        
        print("❌ Page verification failed")
        return False

    def has_results_data(self):
        """Check if page has actual results data"""
        try:
            # Check for loading indicators (should be absent)
            loading_selectors = [
                "//div[contains(text(), 'Loading')]",
                "//*[contains(@class, 'loading')]",
                "//*[contains(@class, 'spinner')]"
            ]
            
            for selector in loading_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if any(elem.is_displayed() for elem in elements):
                    print("   ⏳ Loading indicator still visible")
                    return False
            
            # Check for actual data rows
            data_selectors = [
                "//table//tr[td]",
                "//tbody//tr[td]", 
                "//table//tr[position()>1 and td]"
            ]
            
            for selector in data_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                visible_rows = [elem for elem in elements if elem.is_displayed()]
                if visible_rows:
                    print(f"   ✓ Found {len(visible_rows)} data rows")
                    
                    # Check DOM is ready
                    dom_ready = self.driver.execute_script("return document.readyState") == "complete"
                    if dom_ready:
                        print("   ✅ DOM ready")
                        return True
                    else:
                        print("   ⏳ DOM still loading")
                        return False
            
            # Check for "no results" messages
            no_results = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'No records') or contains(text(), 'No results')]")
            if any(elem.is_displayed() for elem in no_results):
                print("   ❌ No results found")
                return False
            
            print("   ⏳ No data rows detected yet")
            return False
            
        except Exception:
            return False

    def run_headless_extraction(self):
        """Run multi-page extraction using current headless driver with guaranteed CSV output"""
        print(f"\n📊 Step 3: Running Headless Data Extraction")
        print("-" * 40)
        
        extractor = None
        csv_file = None
        
        try:
            # Import the multi-page extractor and run it with our driver
            from multi_page_extractor import MultiPageExtractor
            
            print("🔄 Initializing headless extractor...")
            extractor = MultiPageExtractor(debug_mode=True)
            
            # Use our existing headless driver
            extractor.driver = self.driver
            
            print("🚀 Starting multi-page data extraction...")
            
            # Run the extraction directly
            extractor.total_pages = extractor.detect_total_pages()
            
            if extractor.total_pages:
                print(f"📊 Total pages detected: {extractor.total_pages}")
                actual_max_pages = min(50, extractor.total_pages)
            else:
                print(f"🔍 Page count unknown, will detect during navigation (max 50)")
                actual_max_pages = 50
            
            # Get current page number
            extractor.current_page = extractor.get_current_page_number()
            print(f"📍 Starting from page: {extractor.current_page}")
            
            page_number = extractor.current_page
            consecutive_empty_pages = 0
            
            try:
                while page_number <= actual_max_pages:
                    print(f"\n📄 Processing Page {page_number}")
                    if extractor.total_pages:
                        print(f"    Progress: {page_number}/{extractor.total_pages} ({(page_number/extractor.total_pages*100):.1f}%)")
                    print("-" * 40)
                    
                    # Extract data from current page
                    page_records = extractor.extract_current_page_data(page_number)
                    
                    if page_records:
                        extractor.all_records.extend(page_records)
                        consecutive_empty_pages = 0
                        print(f"📊 Page {page_number}: {len(page_records)} records")
                        print(f"📈 Total so far: {len(extractor.all_records)} records")
                        
                        # Save incremental results every 5 pages (backup)
                        if page_number % 5 == 0:
                            try:
                                backup_file = extractor.save_results_to_csv(filename=f"extracted/backup_page_{page_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                                print(f"💾 Incremental backup saved: {backup_file}")
                            except:
                                pass  # Don't fail extraction for backup issues
                    else:
                        consecutive_empty_pages += 1
                        print(f"⚠️ Page {page_number}: No data found")
                        
                        if consecutive_empty_pages >= 3:
                            print("🛑 Found 3 consecutive empty pages. Stopping extraction.")
                            break
                    
                    # Check if we've reached the known total
                    if extractor.total_pages and page_number >= extractor.total_pages:
                        print(f"🏁 Reached final page ({extractor.total_pages}). Extraction complete.")
                        break
                    
                    # Try to navigate to next page
                    if not extractor.navigate_to_next_page(page_number):
                        print(f"🏁 No more pages found. Extraction complete.")
                        break
                    
                    page_number += 1
                    extractor.current_page = page_number
                    
                    # Wait 8 seconds between pages
                    if page_number <= actual_max_pages:
                        if extractor.total_pages:
                            print(f"⏱️ Waiting 8 seconds before processing page {page_number}/{extractor.total_pages}...")
                        else:
                            print(f"⏱️ Waiting 8 seconds before processing page {page_number}...")
                        time.sleep(8)
                        
            except KeyboardInterrupt:
                print(f"\n⏹️ Extraction interrupted by user at page {page_number}")
                print(f"📊 Partial results: {len(extractor.all_records)} records extracted")
            
            # Always save results (complete or partial)
            print(f"\n💾 Saving final results...")
            print("=" * 60)
            print(f"📊 Total pages processed: {page_number}")
            print(f"📊 Total records extracted: {len(extractor.all_records)}")
            
            if extractor.all_records:
                csv_file = extractor.save_results_to_csv(filename=f"extracted/property_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                print(f"✅ Final results saved to: {csv_file}")
                
                # Clean up backup files
                try:
                    import glob
                    backup_files = glob.glob("extracted/backup_page_*.csv")
                    for backup in backup_files:
                        os.remove(backup)
                    if backup_files:
                        print(f"🧹 Cleaned up {len(backup_files)} backup files")
                except:
                    pass
                
                return True
            else:
                print("⚠️ No records were extracted")
                return False
                
        except ImportError:
            print("❌ Could not import multi_page_extractor")
            return False
        except Exception as e:
            print(f"❌ Headless extraction error: {e}")
            
            # Still try to save any partial results
            if extractor and extractor.all_records:
                try:
                    print(f"💾 Attempting to save partial results...")
                    csv_file = extractor.save_results_to_csv(filename=f"extracted/partial_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                    print(f"✅ Partial results saved to: {csv_file}")
                except Exception as save_error:
                    print(f"❌ Could not save partial results: {save_error}")
            
            return False

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                print("🧹 Closing headless browser...")
                self.driver.quit()
        except:
            pass

    def run(self):
        """Main headless execution workflow"""
        self.print_header()
        
        try:
            # Step 1: Run headless search
            if not self.run_headless_search():
                print("\n❌ Headless search failed")
                print("Check: Network connection, website changes, Chrome installation")
                return False
            
            # Step 2: Verify page ready
            if not self.verify_page_ready():
                print("\n❌ Results page not ready")
                print("Check: Search results, page rendering, data loading")
                return False
            
            # Step 3: Run headless extraction
            if not self.run_headless_extraction():
                print("\n❌ Data extraction failed")
                return False
            
            # Success
            total_time = datetime.now() - self.start_time
            print(f"\n🎉 HEADLESS EXTRACTION COMPLETE!")
            print("=" * 60)
            print(f"⏱️  Total time: {total_time}")
            print("📁 Check 'extracted' folder for CSV file")
            print("🎯 All property data consolidated!")
            print("🤖 Completed entirely in headless mode!")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Process interrupted")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            self.cleanup()
        
        return False

def main():
    """Main entry point"""
    print("Starting Headless Property Extraction...")
    print(f"Working directory: {os.getcwd()}\n")
    
    # Check required files
    required_files = ['pbc_property_search.py', 'multi_page_extractor.py']
    missing = [f for f in required_files if not os.path.exists(f)]
    
    if missing:
        print("❌ Missing files:")
        for file in missing:
            print(f"   • {file}")
        return False
    
    # Create output directory
    os.makedirs("extracted", exist_ok=True)
    
    # Run headless automation
    automation = AutomatedPropertyExtraction()
    return automation.run()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)