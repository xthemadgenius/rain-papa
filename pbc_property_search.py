#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def search_palm_beach_properties():
    """
    Automates property search on Palm Beach County Property Appraiser website
    Workflow:
    1. Opens https://pbcpao.gov/
    2. Clicks Advanced Sales Search button
    3. Selects Commercial option
    4. Selects Palm Beach from Municipality dropdown
    5. Enters 5000 in first Square Footage Range box
    6. Submits search
    """
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Opening Palm Beach County Property Appraiser main page...")
        driver.get("https://pbcpao.gov/")
        
        wait = WebDriverWait(driver, 10)
        
        print("Waiting for main page to load...")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        time.sleep(3)
        
        print("Looking for Advanced Sales Search button...")
        advanced_search_button = None
        
        try:
            advanced_search_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Advanced Sales Search') or contains(text(), 'Advanced Search')]"))
            )
            print("Found Advanced Sales Search button")
        except:
            try:
                advanced_search_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Advanced Sales Search')]")
                print("Found Advanced Sales Search button (button element)")
            except:
                try:
                    advanced_search_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Advanced') and contains(text(), 'Search')]")
                    print("Found Advanced Search link/button")
                except:
                    print("Available links and buttons on page:")
                    links = driver.find_elements(By.TAG_NAME, "a")
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    
                    for i, link in enumerate(links[:10]):
                        text = link.text.strip()
                        href = link.get_attribute("href") or "no href"
                        if text:
                            print(f"Link {i}: '{text}' -> {href}")
                    
                    for i, button in enumerate(buttons[:10]):
                        text = button.text.strip()
                        if text:
                            print(f"Button {i}: '{text}'")
        
        if advanced_search_button:
            print("Clicking Advanced Sales Search button...")
            driver.execute_script("arguments[0].click();", advanced_search_button)
            time.sleep(3)
            
            print("Waiting for Advanced Search page to load...")
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            time.sleep(2)
        else:
            print("Could not find Advanced Sales Search button. Trying direct URL...")
            driver.get("https://pbcpao.gov/AdvSearch/RealPropSearch")
            time.sleep(3)
        
        print("Looking for Commercial option...")
        commercial_option = None
        
        try:
            commercial_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='radio' and @value='Commercial'] | //input[@type='radio' and contains(@name, 'commercial')]"))
            )
            print("Found Commercial radio button")
        except:
            try:
                commercial_option = driver.find_element(By.XPATH, "//label[contains(text(), 'Commercial')]/input[@type='radio'] | //label[contains(text(), 'Commercial')]")
                print("Found Commercial option via label")
            except:
                try:
                    commercial_option = driver.find_element(By.XPATH, "//*[contains(text(), 'Commercial') and (@type='radio' or parent::label)]")
                    print("Found Commercial option")
                except:
                    print("Available radio buttons and checkboxes:")
                    radios = driver.find_elements(By.XPATH, "//input[@type='radio']")
                    checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                    
                    for i, radio in enumerate(radios):
                        name = radio.get_attribute("name") or "no name"
                        value = radio.get_attribute("value") or "no value"
                        nearby_text = driver.execute_script("""
                            var element = arguments[0];
                            var parent = element.parentElement;
                            return parent ? parent.textContent.trim().substring(0, 50) : '';
                        """, radio)
                        print(f"Radio {i}: name='{name}', value='{value}', nearby: '{nearby_text}'")
        
        if commercial_option:
            print("Clicking Commercial option...")
            driver.execute_script("arguments[0].click();", commercial_option)
            time.sleep(1)
            print("✓ Selected Commercial option")
        
        time.sleep(2)
        
        print("Looking for Municipality radio button (SaleSrchType=MUNI)...")
        muni_radio = None
        
        try:
            muni_radio = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='radio' and @name='SaleSrchType' and @value='MUNI']"))
            )
            print("Found Municipality radio button")
        except:
            try:
                muni_radio = driver.find_element(By.XPATH, "//input[@name='SaleSrchType' and @value='MUNI']")
                print("Found Municipality radio button (fallback)")
            except:
                print("Could not find Municipality radio button")
        
        if muni_radio:
            print("Clicking Municipality radio button to enable dropdown...")
            driver.execute_script("arguments[0].click();", muni_radio)
            time.sleep(2)
            print("✓ Selected Municipality search type")
        
        print("Looking for Municipality dropdown field...")
        municipality_dropdown = None
        
        try:
            municipality_dropdown = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//select[contains(@name, 'Municipality') or contains(@id, 'Municipality')]"))
            )
            print("Found Municipality dropdown field")
        except:
            try:
                municipality_dropdown = driver.find_element(By.XPATH, "//label[contains(text(), 'Municipality')]/following-sibling::select")
                print("Found Municipality dropdown via label")
            except:
                try:
                    municipality_dropdown = driver.find_element(By.XPATH, "//label[contains(text(), 'Municipality')]/..//select")
                    print("Found Municipality dropdown in same container as label")
                except:
                    selects = driver.find_elements(By.TAG_NAME, "select")
                    print("Available select elements:")
                    for i, select in enumerate(selects):
                        name = select.get_attribute("name") or "no name"
                        id_attr = select.get_attribute("id") or "no id"
                        nearby_text = driver.execute_script("""
                            var element = arguments[0];
                            var parent = element.parentElement;
                            return parent ? parent.textContent.trim().substring(0, 50) : '';
                        """, select)
                        print(f"Select {i}: name='{name}', id='{id_attr}', nearby text: '{nearby_text}'")
                    
                    if selects:
                        municipality_dropdown = selects[0]
                        print("Using first select element as municipality dropdown")
        
        if municipality_dropdown:
            print("Clicking Municipality field...")
            driver.execute_script("arguments[0].click();", municipality_dropdown)
            time.sleep(1)
            
            print("Selecting 'Palm Beach' from dropdown options...")
            select_obj = Select(municipality_dropdown)
            
            palm_beach_selected = False
            print("Available options in Municipality dropdown:")
            for option in select_obj.options:
                option_text = option.text.strip()
                option_value = option.get_attribute("value").strip()
                print(f"  - '{option_text}' (value: '{option_value}')")
                
                # Check both text and value for "Palm Beach"
                if "palm beach" in option_text.lower() or "palm beach" in option_value.lower():
                    try:
                        # Scroll dropdown into view and ensure it's visible
                        driver.execute_script("arguments[0].scrollIntoView(true);", municipality_dropdown)
                        time.sleep(1)
                        
                        # Try selecting using JavaScript for better compatibility
                        if option_text:
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", 
                                               municipality_dropdown, option_value)
                            print(f"✓ Selected by JavaScript (text): {option_text}")
                        else:
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", 
                                               municipality_dropdown, option_value)
                            print(f"✓ Selected by JavaScript (value): {option_value}")
                        palm_beach_selected = True
                        break
                    except Exception as e:
                        print(f"JavaScript selection failed: {e}")
                        try:
                            # Fallback to Selenium methods
                            if option_text:
                                select_obj.select_by_visible_text(option_text)
                                print(f"✓ Selected by text: {option_text}")
                            else:
                                select_obj.select_by_value(option_value)
                                print(f"✓ Selected by value: {option_value}")
                            palm_beach_selected = True
                            break
                        except Exception as e2:
                            print(f"Standard selection also failed: {e2}")
                            continue
            
            if not palm_beach_selected:
                print("Could not find exact 'Palm Beach' option. Trying partial matches...")
                for option in select_obj.options:
                    option_text = option.text.strip()
                    option_value = option.get_attribute("value").strip()
                    
                    # Check for partial matches in both text and value
                    text_match = option_text and ("palm" in option_text.lower() and "beach" in option_text.lower())
                    value_match = option_value and ("palm" in option_value.lower() and "beach" in option_value.lower())
                    
                    if text_match or value_match:
                        try:
                            # Use JavaScript for partial matches too
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", 
                                               municipality_dropdown, option_value)
                            if option_text:
                                print(f"✓ Selected closest match by JavaScript (text): {option_text}")
                            else:
                                print(f"✓ Selected closest match by JavaScript (value): {option_value}")
                            palm_beach_selected = True
                            break
                        except Exception as e:
                            print(f"JavaScript partial selection failed: {e}")
                            try:
                                if option_text:
                                    select_obj.select_by_visible_text(option_text)
                                    print(f"✓ Selected closest match by text: {option_text}")
                                else:
                                    select_obj.select_by_value(option_value)
                                    print(f"✓ Selected closest match by value: {option_value}")
                                palm_beach_selected = True
                                break
                            except Exception as e2:
                                print(f"Standard partial selection also failed: {e2}")
                                continue
        
        print("Looking for Square Footage Range input field...")
        sqft_input = None
        
        try:
            sqft_input = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Square Footage')]/following-sibling::*//input[1]"))
            )
            print("Found first Square Footage Range input field")
        except:
            try:
                sqft_input = driver.find_element(By.XPATH, "//label[contains(text(), 'Square Footage')]/..//input[1]")
                print("Found first Square Footage input in same container")
            except:
                try:
                    sqft_input = driver.find_element(By.XPATH, "//input[contains(@name, 'Square') or contains(@id, 'Square')][1]")
                    print("Found first Square Footage input by name/id")
                except:
                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    print("Available input fields:")
                    for i, inp in enumerate(inputs):
                        name = inp.get_attribute("name") or "no name"
                        id_attr = inp.get_attribute("id") or "no id"
                        placeholder = inp.get_attribute("placeholder") or "no placeholder"
                        input_type = inp.get_attribute("type") or "text"
                        nearby_text = driver.execute_script("""
                            var element = arguments[0];
                            var parent = element.parentElement;
                            return parent ? parent.textContent.trim().substring(0, 80) : '';
                        """, inp)
                        print(f"Input {i}: name='{name}', id='{id_attr}', type='{input_type}', placeholder='{placeholder}'")
                        print(f"         nearby text: '{nearby_text}'")
                        
                        if ("square" in nearby_text.lower() or "footage" in nearby_text.lower()) and input_type in ['text', 'number']:
                            sqft_input = inp
                            print(f"✓ Using input {i} as first Square Footage field")
                            break
        
        if sqft_input:
            print("Clicking first Square Footage Range input box...")
            driver.execute_script("arguments[0].click();", sqft_input)
            time.sleep(0.5)
            
            print("Entering 5000 in the first Square Footage Range box...")
            sqft_input.clear()
            sqft_input.send_keys("5000")
            print("✓ Entered 5000 in Square Footage minimum field")
        
        print("Submitting form naturally...")
        
        try:
            # Find the form element and submit it directly
            form = driver.find_element(By.TAG_NAME, "form")
            print("Found form element, submitting...")
            form.submit()
            
            print("Form submitted! Waiting for results...")
            time.sleep(5)
            
        except Exception as e:
            print(f"Form submit failed: {e}")
            print("Trying to trigger form submission with Enter key...")
            try:
                # Try pressing Enter on the square footage input to trigger submission
                if sqft_input:
                    from selenium.webdriver.common.keys import Keys
                    sqft_input.send_keys(Keys.RETURN)
                    print("Pressed Enter on square footage field")
                    time.sleep(3)
                else:
                    # Try JavaScript form submission
                    driver.execute_script("document.forms[0].submit();")
                    print("Used JavaScript to submit first form")
                    time.sleep(3)
                    
            except Exception as e2:
                print(f"Alternative submission methods failed: {e2}")
                print("Form may need manual submission or different approach")
        
        current_url = driver.current_url
        print(f"Current URL after submission: {current_url}")
        
        # Check if we got redirected to results
        if current_url != "https://pbcpao.gov/AdvSearch/RealPropSearch":
            print("✓ Form appears to have been submitted successfully!")
            print("✓ Redirected to results page")
        else:
            print("? Still on search page - form may not have submitted")
        
        print("Keeping browser open for 30 seconds to view results...")
        time.sleep(30)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    print("Palm Beach County Property Search Automation")
    print("=" * 50)
    search_palm_beach_properties()