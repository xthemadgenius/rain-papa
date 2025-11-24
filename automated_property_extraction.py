#!/usr/bin/env python3
"""
Automated Property Extraction Master Script

This script provides seamless one-command execution:
1. Launches pbc_property_search.py to fill form and search
2. Monitors for GetSalesSearch results page
3. Automatically launches multi_page_extractor.py to extract all data
4. Produces one consolidated CSV with all property records

Usage: python3 automated_property_extraction.py
"""

import subprocess
import time
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

class AutomatedPropertyExtraction:
    def __init__(self):
        self.search_process = None
        self.driver = None
        self.start_time = datetime.now()
        
    def print_header(self):
        """Print header information"""
        print("🚀 Automated Property Extraction Pipeline")
        print("=" * 60)
        print("This will automatically:")
        print("• Run the property search (fill form + search)")
        print("• Monitor for GetSalesSearch results page")
        print("• Extract data from ALL pages automatically")
        print("• Save everything to one CSV file")
        print("=" * 60)
        print()

    def launch_property_search(self):
        """Launch the property search script"""
        print("🔍 Step 1: Launching Property Search...")
        print("-" * 40)
        
        try:
            self.search_process = subprocess.Popen([
                sys.executable, 'pbc_property_search.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("✅ Property search script launched")
            print("🔄 Form filling and search automation in progress...")
            return True
            
        except FileNotFoundError:
            print("❌ Error: pbc_property_search.py not found")
            return False
        except Exception as e:
            print(f"❌ Error launching search: {e}")
            return False

    def connect_to_browser(self):
        """Connect to the search browser session"""
        try:
            if not self.driver:
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Test connection
            _ = self.driver.current_url
            return True
            
        except WebDriverException:
            return False

    def monitor_for_results_page(self, timeout_minutes: int = 5):
        """Monitor browser for GetSalesSearch page"""
        print(f"\n🕐 Step 2: Monitoring for GetSalesSearch Page ({timeout_minutes}min timeout)")
        print("-" * 40)
        
        timeout_seconds = timeout_minutes * 60
        start_time = time.time()
        check_interval = 3
        
        # Initial wait for browser to start
        print("⏱️ Waiting for browser session...")
        time.sleep(10)
        
        while time.time() - start_time < timeout_seconds:
            elapsed = int(time.time() - start_time)
            remaining = int(timeout_seconds - elapsed)
            
            try:
                if self.connect_to_browser():
                    current_url = self.driver.current_url
                    print(f"🔍 [{elapsed}s] Checking: {current_url}")
                    
                    # Check for GetSalesSearch page
                    if 'AdvSearch/GetSalesSearch' in current_url:
                        print("🎯 GetSalesSearch page detected!")
                        return True
                    
                else:
                    print(f"🔄 [{elapsed}s] Browser not ready...")
                
                print(f"⏳ Monitoring continues... ({remaining}s remaining)")
                time.sleep(check_interval)
                
            except Exception:
                print(f"🔄 [{elapsed}s] Checking browser state...")
                time.sleep(check_interval)
        
        print("❌ GetSalesSearch page timeout reached")
        return False

    def verify_page_ready(self):
        """Verify the results page is fully loaded"""
        print(f"\n✅ Step 3: Verifying Page Ready")
        print("-" * 40)
        
        max_attempts = 5
        
        for attempt in range(1, max_attempts + 1):
            print(f"🔍 Verification attempt {attempt}/{max_attempts}...")
            
            try:
                if not self.connect_to_browser():
                    print("❌ Cannot connect to browser")
                    time.sleep(3)
                    continue
                
                current_url = self.driver.current_url
                
                # Confirm still on GetSalesSearch
                if 'AdvSearch/GetSalesSearch' not in current_url:
                    print(f"❌ No longer on GetSalesSearch: {current_url}")
                    return False
                
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

    def launch_extractor(self):
        """Launch the multi-page data extractor"""
        print(f"\n📊 Step 4: Launching Data Extractor")
        print("-" * 40)
        
        try:
            # Clean up search process
            if self.search_process and self.search_process.poll() is None:
                print("🛑 Terminating search process")
                self.search_process.terminate()
                time.sleep(2)
            
            # Final page confirmation
            if self.connect_to_browser():
                current_url = self.driver.current_url
                if 'AdvSearch/GetSalesSearch' in current_url:
                    print(f"✅ Confirmed on results page")
                else:
                    print(f"⚠️ Unexpected page: {current_url}")
            
            # Launch extractor
            print("🚀 Starting multi_page_extractor.py...")
            result = subprocess.run([
                sys.executable, 'multi_page_extractor.py'
            ], capture_output=False, text=True)
            
            return result.returncode == 0
                
        except FileNotFoundError:
            print("❌ multi_page_extractor.py not found")
            return False
        except Exception as e:
            print(f"❌ Extractor launch error: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.search_process and self.search_process.poll() is None:
                self.search_process.terminate()
                self.search_process.wait(timeout=5)
        except:
            pass

    def run(self):
        """Main execution workflow"""
        self.print_header()
        
        try:
            # Step 1: Launch search
            if not self.launch_property_search():
                return False
            
            # Step 2: Monitor for results page
            if not self.monitor_for_results_page():
                print("\n❌ Results page not reached")
                print("Check: Search form filling, network, website changes")
                return False
            
            # Step 3: Verify page ready
            if not self.verify_page_ready():
                print("\n❌ Results page not ready")
                print("Check: Data loading, search results, page rendering")
                return False
            
            # Step 4: Launch extractor
            if not self.launch_extractor():
                print("\n❌ Data extraction failed")
                return False
            
            # Success
            total_time = datetime.now() - self.start_time
            print(f"\n🎉 EXTRACTION COMPLETE!")
            print("=" * 60)
            print(f"⏱️  Total time: {total_time}")
            print("📁 Check 'extracted' folder for CSV file")
            print("🎯 All property data consolidated!")
            
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
    print("Starting Automated Property Extraction...")
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
    
    # Run automation
    automation = AutomatedPropertyExtraction()
    return automation.run()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)