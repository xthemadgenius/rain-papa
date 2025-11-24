#!/usr/bin/env python3
"""
Automated Property Extraction Master Script

This script provides seamless one-command execution:
1. Launches pbc_property_search.py to fill form and search
2. Monitors for results page completion
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
from selenium.common.exceptions import TimeoutException, WebDriverException

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
        print("• Monitor for results page completion")
        print("• Extract data from ALL pages automatically")
        print("• Save everything to one CSV file")
        print("=" * 60)
        print()

    def launch_property_search(self):
        """Launch the property search script"""
        print("🔍 Step 1: Launching Property Search...")
        print("-" * 40)
        
        try:
            # Launch pbc_property_search.py in the background
            self.search_process = subprocess.Popen([
                sys.executable, 'pbc_property_search.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("✅ Property search script launched successfully")
            print("🔄 Form filling and search automation in progress...")
            
            return True
            
        except FileNotFoundError:
            print("❌ Error: pbc_property_search.py not found in current directory")
            print("Make sure you're running this script from the correct folder")
            return False
        except Exception as e:
            print(f"❌ Error launching property search: {e}")
            return False

    def wait_for_search_completion(self, timeout_minutes: int = 3):
        """Wait for the search process to complete first"""
        print(f"\n⏳ Step 2a: Waiting for Search Process to Complete")
        print("-" * 40)
        
        if not self.search_process:
            print("❌ No search process to monitor")
            return False
        
        timeout_seconds = timeout_minutes * 60
        start_time = time.time()
        
        # Wait for the search process to complete
        while self.search_process.poll() is None:
            elapsed = int(time.time() - start_time)
            
            if elapsed >= timeout_seconds:
                print(f"⏰ Search process timeout ({timeout_minutes} minutes)")
                print("🛑 Terminating search process...")
                self.search_process.terminate()
                time.sleep(2)
                return False
            
            print(f"🔄 Search process running... ({elapsed}s elapsed)")
            time.sleep(5)
        
        # Process completed
        return_code = self.search_process.returncode
        elapsed = int(time.time() - start_time)
        
        if return_code == 0:
            print(f"✅ Search process completed successfully! ({elapsed}s)")
            return True
        else:
            print(f"❌ Search process failed with return code: {return_code}")
            return False

    def wait_for_results_page_ready(self, timeout_minutes: int = 2):
        """Monitor for results page to be fully loaded and ready"""
        print(f"\n🕐 Step 2b: Verifying Results Page Ready (timeout: {timeout_minutes}min)")
        print("-" * 40)
        
        timeout_seconds = timeout_minutes * 60
        start_time = time.time()
        check_interval = 5  # Check every 5 seconds
        
        # Give initial time for page transition after search completion
        print("⏱️ Allowing time for page transition...")
        time.sleep(10)
        
        stable_results_count = 0  # Track consecutive successful checks
        required_stable_checks = 3  # Need 3 consecutive confirmations
        
        while time.time() - start_time < timeout_seconds:
            try:
                # Try to connect to the browser
                if self.connect_to_search_browser():
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    
                    print(f"📄 Current page: {page_title}")
                    print(f"🌐 URL: {current_url}")
                    
                    # Check if we're on a results page
                    if self.is_results_page_loaded():
                        stable_results_count += 1
                        print(f"✅ Results page confirmed! (check {stable_results_count}/{required_stable_checks})")
                        
                        if stable_results_count >= required_stable_checks:
                            print("🎯 Results page is stable and ready for extraction!")
                            return True
                    else:
                        stable_results_count = 0  # Reset counter if page not ready
                        print("⏳ Results page not ready yet...")
                else:
                    stable_results_count = 0
                    print("🔄 Browser connection not ready...")
                
                elapsed = int(time.time() - start_time)
                remaining = int(timeout_seconds - elapsed)
                print(f"⏳ Waiting for stable results page... ({elapsed}s elapsed, {remaining}s remaining)")
                
                time.sleep(check_interval)
                
            except Exception as e:
                stable_results_count = 0
                elapsed = int(time.time() - start_time)
                print(f"🔄 Checking page state... ({elapsed}s elapsed)")
                time.sleep(check_interval)
        
        print(f"⏰ Timeout reached ({timeout_minutes} minutes)")
        print("❌ Results page was not stable within timeout period")
        return False

    def connect_to_search_browser(self):
        """Connect to the search browser session"""
        try:
            if not self.driver:
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Test connection
            _ = self.driver.current_url
            return True
            
        except (WebDriverException, TimeoutException):
            return False
        except Exception as e:
            return False

    def is_results_page_loaded(self):
        """Check if we're on a loaded results page"""
        try:
            current_url = self.driver.current_url.lower()
            page_title = self.driver.title.lower()
            
            # Check URL patterns for results
            url_indicators = [
                'getsalessearch',
                'search',
                'result',
                'property'
            ]
            
            # Check title patterns
            title_indicators = [
                'search',
                'result',
                'property',
                'sales'
            ]
            
            # Check if URL suggests results page
            url_match = any(indicator in current_url for indicator in url_indicators)
            title_match = any(indicator in page_title for indicator in title_indicators)
            
            if not (url_match or title_match):
                return False
            
            # Look for actual data content
            content_indicators = [
                "//table//tr[td]",  # Tables with data rows
                "//div[contains(@class, 'result')]",  # Result divs
                "//*[contains(text(), 'records')]",  # Text mentioning records
                "//*[contains(text(), 'properties')]",  # Text mentioning properties
                "//a[contains(@href, 'property') or contains(@href, 'parcel')]"  # Property/parcel links
            ]
            
            data_found = False
            for pattern in content_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    if elements and len(elements) > 0:
                        data_found = True
                        print(f"   ✓ Found data content: {len(elements)} elements matching '{pattern}'")
                        break
                except:
                    continue
            
            if data_found:
                print("   ✓ Results page contains data - ready for extraction!")
                return True
            else:
                print("   ⏳ Results page found but data still loading...")
                return False
                
        except Exception as e:
            print(f"   ❌ Error checking results page: {e}")
            return False

    def launch_data_extraction(self):
        """Launch the multi-page data extractor"""
        print(f"\n📊 Step 3: Launching Data Extraction...")
        print("-" * 40)
        
        try:
            # Terminate the search process if still running
            if self.search_process and self.search_process.poll() is None:
                print("🛑 Terminating search process (no longer needed)")
                self.search_process.terminate()
                time.sleep(2)
            
            # Launch multi_page_extractor.py
            print("🔄 Starting multi-page data extraction...")
            result = subprocess.run([
                sys.executable, 'multi_page_extractor.py'
            ], capture_output=False, text=True)
            
            if result.returncode == 0:
                print("✅ Data extraction completed successfully!")
                return True
            else:
                print(f"❌ Data extraction failed with return code: {result.returncode}")
                return False
                
        except FileNotFoundError:
            print("❌ Error: multi_page_extractor.py not found in current directory")
            return False
        except Exception as e:
            print(f"❌ Error launching data extraction: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.search_process and self.search_process.poll() is None:
                print("🧹 Cleaning up search process...")
                self.search_process.terminate()
                self.search_process.wait(timeout=5)
        except:
            pass
        
        # Note: We don't close the browser driver because multi_page_extractor needs it

    def run_automated_extraction(self):
        """Main execution workflow"""
        self.print_header()
        
        success = False
        
        try:
            # Step 1: Launch property search
            if not self.launch_property_search():
                return False
            
            # Step 2a: Wait for search process to complete
            if not self.wait_for_search_completion(timeout_minutes=3):
                print("\n❌ Search process did not complete successfully")
                print("Possible issues:")
                print("• Search form filling failed")
                print("• Browser automation issues")
                print("• Network connection problems")
                return False
            
            # Step 2b: Verify results page is ready
            if not self.wait_for_results_page_ready(timeout_minutes=2):
                print("\n❌ Results page not ready for extraction")
                print("Possible issues:")
                print("• Page still loading")
                print("• No search results found") 
                print("• Website structure changes")
                return False
            
            # Step 3: Launch data extraction
            if not self.launch_data_extraction():
                return False
            
            # Success!
            total_time = datetime.now() - self.start_time
            print(f"\n🎉 AUTOMATED EXTRACTION COMPLETE!")
            print("=" * 60)
            print(f"⏱️  Total execution time: {total_time}")
            print("📁 Check the 'extracted' folder for your CSV file")
            print("🎯 All property data has been consolidated into one file!")
            
            success = True
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Process interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            self.cleanup()
        
        return success

def main():
    """Main entry point"""
    print("Starting Automated Property Extraction Pipeline...")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Check required files exist
    required_files = ['pbc_property_search.py', 'multi_page_extractor.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   • {file}")
        print("\nMake sure you're running this script from the correct directory.")
        return False
    
    # Create extracted directory
    os.makedirs("extracted", exist_ok=True)
    
    # Run automation
    automation = AutomatedPropertyExtraction()
    return automation.run_automated_extraction()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)