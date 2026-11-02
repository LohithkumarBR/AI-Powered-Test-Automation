import logging
import time
import os
from html_extractor import HtmlExtractor
from chrome_debug_session import BrowserDebugSession
from selenium.common.exceptions import WebDriverException, NoSuchElementException, ElementNotInteractableException, UnexpectedAlertPresentException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
from finding_nlp import convert_memory_to_clean_json
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from vision import Vision
from lxml import html, etree
from dump import Find_element_by_ff_js_script
from verify import execute_verification, NLP_LIST
from switch import execute_switch
from get import execute_get
from html_extractor import keyword_extractor
from dump import INJECT_AND_SERIALIZE_DOM_JS, TOAST_WATCHER_JS,SHADOW_DOM_CLICK_JS, SHADOW_DOM_ENTER_JS, SHADOW_DOM_UPLOAD_JS
from selenium.common.exceptions import TimeoutException
import threading

# Global session manager to prevent GC of driver references
logging.getLogger("urllib3").setLevel(logging.ERROR)

from urllib3.util.retry import Retry
Retry.DEFAULT = Retry(total=0)

ACTIVE_SESSIONS = {}
TERMINATE_FLAGS = {}


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding="utf-8"
)

class PseudoElement:
    """A mock WebElement for handling virtual elements like alerts."""
    def __init__(self, tag_name, text, attributes):
        self.tag_name = tag_name
        self.text = text
        self.attributes = attributes

    def get_attribute(self, name):
        return self.attributes.get(name)

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True

    def is_selected(self):
        return False

    @property
    def location(self):
        return {'x': 0, 'y': 0}

    @property
    def size(self):
        return {'height': 0, 'width': 0}

class WebStepExecutor:
    """Handles element interaction (click, input, verify) for web automation."""

    def __init__(self, driver):
        self.driver = driver
        self.execution_steps = []
        self.total_time = 0
        self.memory = []
        self.annotated_dom = "" 
        self.vision = Vision() 
        self.vision_fallback = True 
        self.last_exception = None 
        

    def _find_element_by_ff_js(self, ff_inspecter_num):
        if ff_inspecter_num in [None, -1]:
            return None, []

        ff_str = str(ff_inspecter_num)
        if not ff_str.startswith("Fire-Flink-"):
            ff_str = f"Fire-Flink-{ff_str}"

        try:
            result = self.driver.execute_async_script(
                Find_element_by_ff_js_script,
                ff_str
            )

            if not isinstance(result, dict) or not result.get("success"):
                logger.warning(f"JS failed: {result}")
                return None, []

            xpath = result.get("xpath")
            frames = result.get("frames", [])

            logger.info(f"JS resolved XPath: {xpath}, frames={frames}")
            return xpath, frames

        except Exception as e:
            logger.error(f"JS ff-inspect lookup failed: {e}")
            return None, []

    def _switch_to_iframe_by_meta(self, frame_meta):
        attempts = []

        if frame_meta.get("id"):
            xp = f"//*[@id='{frame_meta['id']}']"
            attempts.append((lambda: self.driver.find_element(By.ID, frame_meta["id"]), xp))

        if frame_meta.get("name"):
            xp = f"//*[@name='{frame_meta['name']}']"
            attempts.append((lambda: self.driver.find_element(By.NAME, frame_meta["name"]), xp))

        if frame_meta.get("title"):
            xp = f"//iframe[@title='{frame_meta['title']}']"
            attempts.append((lambda: self.driver.find_element(By.XPATH, xp), xp))

        if frame_meta.get("aria"):
            xp = f"//iframe[@aria-label='{frame_meta['aria']}']"
            attempts.append((lambda: self.driver.find_element(By.XPATH, xp), xp))

        if frame_meta.get("src"):
            xp = f"//iframe[contains(@src,'{frame_meta['src']}')]"
            attempts.append((lambda: self.driver.find_element(By.XPATH, xp), xp))

        # Try one by one and return only the xpath that worked
        for finder, xpath_used in attempts:
            try:
                iframe = finder()
                self.driver.switch_to.frame(iframe)

                logger.info(f"[Locator] Switched to iframe using XPath: {xpath_used}")

                # ✅ only xpath returned
                return xpath_used

            except Exception:
                continue

        logger.warning(f"[Locator] Could not resolve iframe from metadata: {frame_meta}")
        return None



    def _resolve_element(self, xpath_path, ff_inspecter_num):
        element = None
        _iframe_ = None
        if xpath_path:
            
            try:
                
                if ff_inspecter_num not in [None, -1] and "iframe" in xpath_path:
                    try:
                        xpath_js, frames = self._find_element_by_ff_js(ff_inspecter_num)

                        if xpath_js:
                            # logger.info("[Locator] XPath resolved via FF JS")

                            # Always reset
                            # self.driver.switch_to.default_content()

                            # Switch iframe chain if any
                            iframe_chain_info = []

                            for frame_meta in frames:
                                info = self._switch_to_iframe_by_meta(frame_meta)
                                if info:
                                    iframe_chain_info.append(info)
                                else:
                                    return None, None, [False,""]
                            
                            # logger.info(f"[Locator] Switched to iframe chain: {iframe_chain_info}")
                            _iframe_= [True,iframe_chain_info]
                            element = self.driver.find_element(By.XPATH, xpath_js)
                            return element, xpath_js, _iframe_

                    except Exception as e:
                        logger.error(f"[Locator] FF lookup error: {e}")
                        return None, None, [False,""]

                elif ff_inspecter_num not in [None, -1] and "shadow" in xpath_path:   
                    try:
                        element = None
                        return element, xpath_path, [False,""]
                    except Exception as e:
                        logger.error(f"[Locator] Shadow lookup error: {e}")
                        return None, None, [False,""]

                elif ff_inspecter_num not in [None, -1] and "svg" in xpath_path:
                    try:
                        # Extract svg index
                        match = re.search(r"svg\[(\d+)\]", xpath_path)
                        svg_index = match.group(1) if match else "1"

                        # Replace only the svg part, keep full parent path
                        xpath_path = re.sub(
                            r"svg\[\d+\]",
                            f"*[name()='svg'][{svg_index}]",
                            xpath_path
                        )

                        logger.info(f"Trying SVG-safe XPath : {xpath_path}")

                        element = self.driver.find_element(By.XPATH, xpath_path)
                        return element, xpath_path, [False, ""]

                    except Exception as e:
                        logger.error(f"[Locator] SVG XPath lookup error: {e}")
                        return None, None, [False, ""]

                else:
                    try:
                        logger.info("[Locator] Attempting XPath with normal driver")
                        element = self.driver.find_element(By.XPATH, xpath_path)
                        return element, xpath_path, [False,""]
                    except Exception as e:
                        logger.error(f"[Locator] XPath lookup error: {e}")
                        return None, None, [False,""]
            except Exception as e:
                try:
                    element = self.driver.find_element(By.XPATH, xpath_path)
                    return element, xpath_path, [False,""]
                except Exception as ex:
                    logger.error(f"[Locator] Fallback XPath lookup error: {ex}")
                    return None, None, [False,""]

        return None, None, [False,""]
    
    def safe_click(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            element.click()  # normal click first attempt
            # self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to click element: {e}")
            self.last_exception = e
            return False
        # except :
        #     try:
        #         self.driver.execute_script("arguments[0].click();", element)
        #         return True
        #     except Exception as e:
        #         logger.error(f"[ERROR] Failed to click element: {e}")
        #         return False

    def execute_step(self, step, step_index, ff_inspecter_num=None, action=None,
                     input_text=None, keyword=None, num_of_scrolls=None, direction=None, xpath_path=None):
        start_time = time.time()
        success = False
        xpath_js = None 
        
        # logger.info(f"FF Inspecter Num: {ff_inspecter_num}")

        

        try:
            element = None
            iframe = [False,""]
            # ... (rest of the logic remains the same)
            
            if action == "wait": 
                try:
                    if not input_text:
                        input_text = 5
                    input_text = int(input_text)
                    logger.info(f"[Step {step_index}] Waiting for {input_text} seconds...")
                    success = True
                    time.sleep(input_text)
                    action = "Sleep"
                    return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f"[ERROR] Failed to wait for {input_text} seconds: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
            
            elif action == "maximize":
                try:
                    logger.info("[INFO] Maximizing the browser window...")
                    self.driver.maximize_window()
                    success = True
                    action = "MaximizeBrowser"
                    # logger.info("[SUCCESS] Browser window maximized successfully.")
                    return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f"[ERROR] Failed to maximize browser window: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
            elif action == "enterdatatoalert":
                try:
                    alert = self.driver.switch_to.alert
                    alert.send_keys(input_text)
                    logger.info(" Accepted alert popup after entering data.")
                    # alert.accept()
                    action = "EnterDataToAlert"
                    success = True
                    return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f" Failed to enter data into alert: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
            elif action == "clickokonalertpopup":
                try:
                    alert = self.driver.switch_to.alert
                    alert.accept()
                    logger.info(" Clicked OK on alert popup.")
                    action = "ClickOkOnAlertPopup"
                    success = True
                    return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f" Failed to click OK on alert popup: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
            elif action == "clickcancelonalertpopup":
                try:
                    alert = self.driver.switch_to.alert
                    alert.dismiss()
                    logger.info(" Clicked Cancel on alert popup.")
                    action = "ClickCancelOnAlertPopup"
                    success = True
                    return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f" Failed to click Cancel on alert popup: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
            elif action == "verifyalertpopupisplayed":
                try:
                    action = "VerifyAlertPopupIsDisplayed"
                    logger.info("  alert popup is displayed.")
                    success = True
                    return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f" Failed to verify alert popup: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
            elif action == "gettextpresentonalertpopup":
                try:
                    action = "GetTextPresentOnAlertPopup"
                    logger.info(" Getting text present on alert popup.")
                    success = True
                    return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f" Failed to get text present on alert popup: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
            elif action == "verifyalertpopupmessagecontainsstring":
                try:
                    alert = self.driver.switch_to.alert
                    text = alert.text
                    if input_text.lower() in text.lower():
                        logger.info(" Alert popup message contains string.")
                        action = "VerifyAlertPopUpMessageContainsString"
                        success = True
                        return success, action, xpath_path, iframe, input_text
                    else:
                        logger.error(" Alert popup message does not contain string.")
                        success = False
                        return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f" Failed to verify alert popup message contains string: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
            elif action == "verifytextpresentonalertpopup":
                try:
                    alert = self.driver.switch_to.alert
                    text = alert.text
                    if input_text.lower() == text.lower():
                        logger.info(" Alert popup message matches string.")
                        action = "VerifyTextPresentOnAlertPopup"
                        success = True
                        return success, action, xpath_path, iframe, input_text
                    else:
                        logger.error(" Alert popup message does not matches string.")
                        success = False
                        return success, action, xpath_path, iframe, input_text
                except Exception as e:
                    logger.error(f" Failed to verify text present on alert popup: {e}")
                    self.last_exception = e
                    success = False
                    return success, action, xpath_path, iframe, input_text
                    
            
            # Resolve element early if needed
            if (action != "builtin_draganddroptoelement"
                and isinstance(ff_inspecter_num, (int, str))
                and int(ff_inspecter_num) > 0):
                element, xpath_js, iframe = self._resolve_element(xpath_path, ff_inspecter_num)
                if not element and "shadow" not in xpath_path:
                    logger.warning(f"[Step {step_index}] Element not found for '{step}'.")
                    self.last_exception = Exception(f"Element not found for step '{step}'")
                    return success, action, xpath_js, iframe, input_text
            
            if "shadow" in xpath_path and int(ff_inspecter_num) > 0:
                logger.info("Found shadow element")
                if action == "click":
                    try:
                        # logger.info(f"[Step {step_index}] Clicking shadow element via JS resolver")
                        success = self.driver.execute_script(SHADOW_DOM_CLICK_JS, xpath_path)
                        if success:
                            action = "ExecuteJavaScript"
                            input_text = SHADOW_DOM_CLICK_JS.replace("const path = arguments[0];", f'const path = "{xpath_path}";')
                            logger.info(f"[Step {step_index}] Clicked shadow element successfully.")
                        else:
                            logger.error(f"[Step {step_index}] Failed to resolve or click shadow element.")
                    except Exception as e:
                        logger.error(f"[Step {step_index}] Error during shadow element click: {e}")
                        self.last_exception = e
                        success = False
                elif action == "enter":
                    try:
                        # logger.info(f"[Step {step_index}] Entering shadow element via JS resolver")
                        value_to_enter = input_text
                        success = self.driver.execute_script(SHADOW_DOM_ENTER_JS, xpath_path, value_to_enter)
                        if success:
                            action = "ExecuteJavaScript"
                            input_text = SHADOW_DOM_ENTER_JS.replace("const path = arguments[0];", f'const path = "{xpath_path}";')
                            input_text = input_text.replace("const value = arguments[1];", f'const value = "{value_to_enter}";')
                            logger.info(f"[Step {step_index}] Entered shadow element successfully.")
                        else:
                            logger.error(f"[Step {step_index}] Failed to resolve or enter shadow element.")
                    except Exception as e:
                        logger.error(f"[Step {step_index}] Error during shadow element enter: {e}")
                        self.last_exception = e
                        success = False
                elif action == "upload":
                    try:
                        element = self.driver.execute_script(SHADOW_DOM_UPLOAD_JS, xpath_path)
                        if element:
                            element.send_keys(input_text)
                            action = "ExecuteJavaScript"
                            logger.info(f"[Step {step_index}] Uploaded file to shadow element successfully.")
                            success = True
                        else:
                            logger.error(f"[Step {step_index}] Failed to resolve shadow element for upload.")
                            success = False
                    except Exception as e:
                        logger.error(f"[Step {step_index}] Error during shadow element upload: {e}")
                        self.last_exception = e
                        success = False
                else:
                    logger.warning(f"[Step {step_index}] Unknown or unhandled action: {action}")
                    self.last_exception = Exception(f"Unknown action '{action}' for shadow DOM element")
                    success = False
            else:
                if action == "scroll":
                    try:
                        # Case 1: Scroll by direction + count
                        num_of_scrolls = int(num_of_scrolls)
                        if num_of_scrolls != 0 and direction is not None:
                            try:
                                logger.info(f"[Step {step_index}] Scrolling {num_of_scrolls} times in {direction} direction...")
                                for _ in range(num_of_scrolls):
                                    if direction == "up":
                                        self.driver.execute_script("window.scrollBy(0, -150)")
                                    elif direction == "down":
                                        self.driver.execute_script("window.scrollBy(0, 150)")
                                    time.sleep(0.15)
                                success = True
                            except Exception as e:
                                logger.error(f"[Step {step_index}] Failed to scroll: {e}")
                                self.last_exception = e
                                success = False
                        
                        else:
                            # Case 2: Scroll to a specific element
                            logger.info(f"[Step {step_index}] Scrolling to element")
                            
                            try:
                                if element:
                                    self.driver.execute_script(
                                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element
                                    )   
                                    logger.info(f"[Step {step_index}] Scrolled to element")
                                    success = True
                                    action = "ScrollToElement"
                                else:
                                    logger.warning(f"[Step {step_index}] Cannot scroll to element (Element is None)")
                            except Exception as e:
                                logger.error(f"[ERROR] Scroll failed: {e}")
                                self.last_exception = e
                                success = False
                    except Exception as e:
                        logger.error(f"[ERROR] Scroll failed: {e}")
                        self.last_exception = e
                        success = False
                    
                elif action == "click" and int(ff_inspecter_num) > 0:
                    if self.safe_click(element):
                        logger.info(f"[Step {step_index}] Clicked element.")
                        success = True
                        action = "Click"

                        #toast dom watcher
                        try:
                            if not is_alert_present(self.driver,0):
                                self.driver.execute_script(TOAST_WATCHER_JS)
                        except UnexpectedAlertPresentException:
                            logger.info(f"[Step {step_index}] Alert present after click, skipping toast watcher injection.")
                        except Exception as e:
                            logger.debug(f"[Step {step_index}] Failed to inject toast watcher: {e}")
                    else:
                        logger.error(f"[Step {step_index}] Failed to click element.")
                        self.last_exception = Exception("Failed to click element (safe_click returned False)")
                        success = False
                elif action == "doubleclick" and int(ff_inspecter_num) > 0:
                    try:
                        actions = ActionChains(self.driver)
                        actions.double_click(element).perform()

                        logger.info(f"[Step {step_index}] Double clicked element.")
                        success = True
                        action = "DoubleClick"
                    except Exception as e:
                        logger.error(f"[Step {step_index}] Failed to double click element: {e}")
                        self.last_exception = e
                        success = False
                elif action == "rightclick" and int(ff_inspecter_num) > 0:
                    try:
                        actions = ActionChains(self.driver)
                        actions.context_click(element).perform()
                        logger.info(f"[Step {step_index}] Right clicked element.")
                        success = True
                        action = "RightClick"
                    except Exception as e:
                        logger.error(f"[Step {step_index}] Failed to right click element: {e}")
                        self.last_exception = e
                        success = False
                            
                elif (action == "enter" or action == "upload") and int(ff_inspecter_num) > 0 : 
                    try:
                        element.send_keys(input_text)
                        logger.info(f"[Step {step_index}] Typed '{input_text}' into element.")
                        success = True
                        if action == "enter":
                            action = "SendKeys"
                        else:
                            action = "UploadFilePathUsingRobot"
                    except Exception as e:
                        logger.error(f"[Step {step_index}] Failed to type into element: {e}")
                        self.last_exception = e
                        success = False
                elif action == "clearandenter" and int(ff_inspecter_num) > 0:
                    try:
                        element.clear()
                        element.send_keys(input_text)
                        logger.info(f"[Step {step_index}] Cleared and typed '{input_text}' into element.")
                        success = True
                        action = "ClearThenEnterInput"
                    except Exception as e:
                        logger.error(f"[Step {step_index}] Failed to clear and type into element: {e}")
                        self.last_exception = e
                        success = False
                elif action == "cleartext" and int(ff_inspecter_num) > 0:
                    try:
                        element.clear()
                        logger.info(f"[Step {step_index}] Cleared text from element.")
                        success = True
                        action = "Clear"
                    except Exception as e:
                        logger.error(f"[Step {step_index}] Failed to clear text from element: {e}")
                        self.last_exception = e
                        success = False
                elif action == "builtin_draganddroptoelement":
                    try:
                        # ff_inspecter_num MUST be [source, target]
                        source_ff, dest_ff = ff_inspecter_num

                        source_xpath = xpath_path[0]
                        dest_xpath = xpath_path[1]

                        source_element, _, _ = self._resolve_element(source_xpath, source_ff)
                        dest_element, _, _ = self._resolve_element(dest_xpath, dest_ff)

                        if not source_element or not dest_element:
                            raise Exception("Source or destination element not found")

                        ActionChains(self.driver) \
                            .drag_and_drop(source_element, dest_element) \
                            .perform()

                        logger.info(
                            f"[Step {step_index}] Dragged Fire-Flink-{source_ff} → Fire-Flink-{dest_ff}"
                        )

                        success = True
                        action = "Builtin_DragAndDropToElement"
                        xpath_js = f"{source_xpath}|||{dest_xpath}"

                    except Exception as e:
                        logger.error(f"[Step {step_index}] DragAndDrop failed: {e}")
                        self.last_exception = e
                        success = False
                else:
                    if int(ff_inspecter_num) == 0:
                        logger.warning(f"[Step {step_index}] Element not found for '{step}'.")
                        self.last_exception = Exception(f"Element not found for step '{step}' (FF-inspecter=0)")
                        success = False
                    else:
                        logger.warning(f"[Step {step_index}] Unknown or unhandled action: {action}")
                        self.last_exception = Exception(f"Unknown or unhandled action: {action}")
                        success = False
            
            if iframe[0]:
                logger.info("switched to default content")
                self.driver.switch_to.default_content()

        except NoSuchElementException as e:
            logger.error(f"[Step {step_index}]  Element not found in DOM.")
            self.last_exception = e
        except ElementNotInteractableException as e:
            logger.error(f"[Step {step_index}]  Element not interactable.")
            self.last_exception = e
        except UnexpectedAlertPresentException:
            # logger.error(f"[Step {step_index}]  Alert present on page.")
            pass
        except Exception as e:
            logger.error(f"[Step {step_index}]  Error executing step: {e}")
            self.last_exception = e
        finally:
            step_time = time.time() - start_time
            self.total_time += step_time
            
            self.execution_steps.append({
                "step": step,
                "index": step_index,
                "success": success,
                "time": step_time
            })
            
            
            logger.info(f"[Step {step_index}] Step Success={success}")

            

            return success, action, xpath_js, iframe, input_text

    def _try_vision_fallback(self, step,context,annotated_dom,element_name, step_index, action, input_text=None,server_host=None):
        success = False
        xpath_js = ""
        iframe = [False,""]
        ff_num = 0
        
        from html_extractor import HtmlExtractor, is_editable
        extractor = HtmlExtractor(self.driver)

        xpath_path = None
        try:
            logger.info(f"[Step {step_index}] Starting vision-based element detection...")
            try:
                _ = self.driver.current_url
            except Exception:
                logger.error(f"Browser was forcefully closed before Step {step_index}")
                self.last_exception = Exception(f"Browser was forcefully closed before Step {step_index}")
                # Browser closure will be handled by Agent.call_agent
                return False, action, xpath_js, 0, iframe
            
            # Use Vision class to get the Fire-Flink-XX identifier
            # Note: vision.py needs chrome_session and start_time, we'll pass dummy values
            vision_result = self.vision.generate_vision_code(step,context, self.driver, time.time(),server_host)
            try:
                if not vision_result or vision_result == "Fire-Flink-0":
                    logger.error(f"[Step {step_index}] First vision fallback failed - no result returned")
                    vision_result = self.vision.generate_vision_code_2(step,context, self.driver, time.time(),server_host)
                    if not vision_result or vision_result == "Fire-Flink-0":
                        logger.error(f"[Step {step_index}] Second vision fallback failed - no result returned")
                        self.last_exception = Exception(f"Vision fallback failed to identify element for step '{step}'")
                        return False, action, xpath_js, 0, iframe
            except Exception as e:
                raise e

            extractor.auto_healing.send_locator_request(annotated_dom, vision_result, element_name, server_host, source="vision")
            
            # Extract the Fire-Flink number from the result
         
            match = re.search(r'Fire-Flink-(\d+)', vision_result)
            if not match:
                logger.error(f"[Step {step_index}] Vision fallback failed - could not parse index number from: {vision_result}")
                self.last_exception = Exception(f"Vision fallback returned invalid format: {vision_result}")
                return False, action, xpath_js, 0, iframe
            
            ff_num = int(match.group(1))
            logger.info(f"[Step {step_index}] Vision identified element index: {ff_num}")
            
            # Now try to interact with the identified element
            tree = html.fromstring(annotated_dom)
            target = tree.xpath(f"//*[@ff-inspect='Fire-Flink-{ff_num}']")
            if target:

                element = target[0]
                tag = element.tag.lower()
                elem_type = element.attrib.get("type", "").lower()
                if action == "enter" or action == "upload":
                    # Current element editable
                    if is_editable(element):
                        xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)
                    else:
                        # Search editable descendant
                        editable_child = None
                        for child in element.iter():
                            if is_editable(child):
                                editable_child = child
                                break
                        
                        if editable_child is not None:
                            xpath_path = editable_child.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(editable_child)
                        else:
                            # Try next 10 FF elements
                            found = False
                            for offset in range(1, 11): 
                                num = int(ff_num)
                                next_num = num + offset
                                next_target = tree.xpath(f"//*[@ff-inspect='Fire-Flink-{next_num}']")
                                
                                if next_target and is_editable(next_target[0]):
                                    element = next_target[0]
                                    ff_num = next_num 
                                    logger.info(f"Found editable element with FF number {ff_num}")
                                    xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)
                                    found = True
                                    break
                            
                            # Final fallback
                            if not found:
                                xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)
                else:
                    xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)

            if int(ff_num) > 0 and xpath_path:
                element, xpath_js, iframe = self._resolve_element(xpath_path, ff_num)
                if not element:
                    logger.warning(f"[Step {step_index}] Element not found for '{step}'.")
                    self.last_exception = Exception(f"Vision fallback element lookup failed for step '{step}'")
                    return False, action, xpath_js, ff_num, iframe  
            else:
                logger.warning(f"[Step {step_index}] Element details not found ")
                self.last_exception = Exception(f"Vision fallback failed to find element details for '{step}'")
                return False, action, xpath_js, ff_num, iframe


            
            logger.info(f"[Step {step_index}] Found element with xpath: {xpath_js}")
            element = self.driver.find_element(By.XPATH, xpath_js)
            
            if action == "click":
                if self.safe_click(element):
                    logger.info(f"[Step {step_index}]Vision fallback: Clicked element")
                    success = True
                    action = "Click"
                else:
                    logger.error(f"[Step {step_index}]Vision fallback: Failed to click element")
                    self.last_exception = Exception(f"Vision fallback failed to click element '{action}'")
                    success = False
            elif action == "enter" or action == "upload":
                try:
                    element.clear()
                    element.send_keys(input_text)
                    logger.info(f"[Step {step_index}] Vision fallback: Typed '{input_text}' into element")
                    if action == "enter":
                        action = "SendKeys"
                    else:
                        action = "UploadFilePathUsingRobot"
                    success = True
                except Exception as e:
                    logger.error(f"[Step {step_index}] Vision fallback typed failed: {e}")
                    self.last_exception = e
                    success = False
                
            elif action == "doubleclick" and int(ff_inspecter_num) > 0:
                try:
                    actions = ActionChains(self.driver)
                    actions.double_click(element).perform()

                    logger.info(f"[Step {step_index}] Double clicked element.")
                    success = True
                    action = "DoubleClick"
                except Exception as e:
                    logger.error(f"[Step {step_index}] Failed to double click element: {e}")
                    self.last_exception = e
                    success = False
            elif action == "rightclick" and int(ff_inspecter_num) > 0:
                try:
                    actions = ActionChains(self.driver)
                    actions.context_click(element).perform()
                    logger.info(f"[Step {step_index}] Right clicked element.")
                    success = True
                    action = "RightClick"
                except Exception as e:
                    logger.error(f"[Step {step_index}] Failed to right click element: {e}")
                    self.last_exception = e
                    success = False
            else:
                logger.warning(f"[Step {step_index}] Vision fallback does not support action: {action}")
                self.last_exception = Exception(f"Vision fallback does not support action: {action}")
                success = False
            
                
        except Exception as e:
            logger.error(f"[Step {step_index}] Vision fallback error: {e}")
            if "forcefully closed" in str(e) or "invalid session id" in str(e).lower() or "disconnected" in str(e).lower():
                raise e
            self.last_exception = e
            success = False
            
        return success, action, xpath_js, ff_num, iframe

def _record_forceful_closure(memory, exec_steps, driver_ref, test_steps=None, force_close=False):
    """Handle case where browser was already closed (manually or crash)."""
    should_close = force_close
    if test_steps and not should_close:
        should_close = any("close browser" in str(s).lower() for s in test_steps)
    
    if should_close:
        if not memory or memory[-1].get("action") != "CloseBrowser":
            logger.warning("Detected forceful browser closure. Recording to memory...")
            memory.append({
                "step": "Close Browser forcefully",
                "action": "CloseBrowser",
                "result": True
            })
            if not exec_steps or exec_steps[-1] != "Close Browser":
                exec_steps.append("Close Browser")
    
    # Return None to signal driver should be nullified if we closed it or it's gone
    return None

def is_alert_present(driver, timeout=5):
    try:
        if not driver:
            return False
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        return True
    except TimeoutException:
        return False

def _record_failure_and_close(memory, exec_steps, driver, reason="Execution completed", browser_session=None, test_steps=None, force_close=False):
    """Handle execution completion or failure by recording and closing browser safely."""
    should_close = force_close
    if test_steps and not should_close:
        should_close = any("close browser" in str(s).lower() for s in test_steps)

    if should_close:
        if not memory or memory[-1].get("action") != "CloseBrowser":
            logger.info(f"{reason}. Recording 'Close Browser'...")
            memory.append({
                "step": "Close Browser",
                "action": "CloseBrowser",
                "result": True
            })
            if not exec_steps or exec_steps[-1] != "Close Browser":
                exec_steps.append("Close Browser")
    
    if driver and should_close:
        try:
            logger.info("Closing browser session...")
            driver.quit()
        except Exception:
            pass
    
    # Return None to signal driver should be nullified if we closed it
    return None if should_close else driver

class Agent:
    def __init__(self, browser_name,driver_path):
        self.browser_name = browser_name
        self.driver_path = driver_path

        # Execution metrics
        self.memory = []
        self.exec_steps = []
        self.total_time = 0
        self.cleaned_memory = []
        self.driver = None
        self.browser_session = None
        self.used_element_names = []
        self.toast_lock = threading.Lock()
        self.toast_dom = None
        self.failed_step = None
        self.failed_step_raw = None
        self.last_navigation_intent = {
            "type": None,     # "tab" | "window" | None
            "step": None,
            "source": None
        }
    
    def has_been_force_closed(self):
        if self.browser_session:
            return self.browser_session.has_been_force_closed()
        return True

    def _toast_dom_worker(self):
        try:
            detected = self.driver.execute_script("return window.__toastDetected === true;")
            text = self.driver.execute_script("return window.__lastToastText;")

            logger.info(f"Toast detection result: {detected}, text: {text}")

            if detected:
                dom = self.driver.execute_script(INJECT_AND_SERIALIZE_DOM_JS)

                os.makedirs("dom_dumps", exist_ok=True)
                with open("dom_dumps/annotated_html_toast.html", "w", encoding="utf-8") as f:
                    f.write(dom)

                with self.toast_lock:
                    self.toast_dom = dom

                logger.info("[ToastWatcher] Toast DOM captured")

        except Exception as e:
            logger.debug(f"[ToastWatcher] ignored error: {e}")
    # Browser setup (Selenium Chrome)
    def start_browser_session(self):
        """Initialize Selenium WebDriver session using BrowserDebugSession."""
        try:
            # self.browser_session = BrowserDebugSession._start_browser()
            self.driver = BrowserDebugSession(self.browser_name,self.driver_path)._start_browser()
            self.driver.implicitly_wait(30)
            logger.info(f"{self.browser_name} browser session started successfully via BrowserDebugSession")
            return self.driver
        except Exception as e:
            logger.error(f"Error starting {self.browser_name} session: {str(e)}")
            raise e


    def call_agent(self, test_steps,server_host, serviceProvider, model, apiKey,service_accounts,session_id=None):
        """Main entry to run test steps sequentially."""
        self.cleaned_memory = None  
        start_time = time.time()
        # logger.info(f"Starting web automation for {len(test_steps)} steps")

        extractor = None
        try:
            self.driver = self.start_browser_session()
            self.last_known_handles = set(self.driver.window_handles)
            
            if session_id:
                ACTIVE_SESSIONS[session_id] = self.driver
                logger.info(f"Registered session {session_id} in ACTIVE_SESSIONS")
            # print("openned")
            extractor = HtmlExtractor(self.driver)
            executor = WebStepExecutor(self.driver) 
        except Exception as e:
            logger.error(f"Failed to initialize browser session: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise e

        try:
            for i, step in enumerate(test_steps, 1):
                logger.info("*" * 50)
                # self.driver.implicitly_wait(30)
                logger.info(f"Step {i}/{len(test_steps)} → {step}")
                # logger.info("*" * 50)
                step_start = time.time()
                ff_num = 0

                if session_id and TERMINATE_FLAGS.get(session_id):
                    logger.info("Execution stopped by API termination.")
                    TERMINATE_FLAGS.pop(session_id)
                    break

                # 1. Action Extraction (needed for conditional liveness check)
                try:
                    start = max(0, i - 3)
                    end = min(len(test_steps), i + 4)
                    context = test_steps[start:end]
                    # keywords_response, element_name, step_action = keyword_extractor(step, context, serviceProvider, model, apiKey, service_accounts)
                except Exception as e:
                    logger.warning(f"Failed to extract keywords for step '{step}': {e}")
                    keywords_response, element_name, step_action = [], None, None

                # 2. Liveness Check / Lifecycle Handling
                try:
                    if step_action != "open":
                        if not self.driver:
                            if step_action == "close":
                                logger.info(f"[Step {i}] Browser already closed, treating as success.")
                                self.memory.append({"step": step, "action": "CloseBrowser", "result": True})
                                self.exec_steps.append(step)
                                continue
                            
                            if step_action == "verify" and "closed" in step.lower() and "browser" in step.lower():
                                logger.info(f"[Step {i}] Verifying browser is closed. Browser is already closed. Success.")
                                self.memory.append({"step": step, "action": "VerifyBrowserClosed", "result": True})
                                self.exec_steps.append(step)
                                continue

                            raise Exception(f"No active browser session for step {i}: {step}")

                        try:
                            if is_alert_present(self.driver, 1):
                                logger.info(f"[Step {i}] Alert is present, browser is alive.")
                            else:
                                _ = self.driver.current_url

                        except Exception:
                            # if alert is present, browser is NOT closed
                            if is_alert_present(self.driver, 1):
                                logger.info(f"[Step {i}] Alert is present, browser is alive.")
                            else:
                                # if it's a close action, we don't care if it's already dead
                                if step_action == "close":
                                    logger.info(f"[Step {i}] Browser detected as closed during CloseBrowser step.")
                                    self.memory.append({"step": step, "action": "CloseBrowser", "result": True})
                                    self.exec_steps.append(step)
                                    self.driver = None
                                    continue

                                logger.error(f"[Step {i}] Browser was forcefully closed. Raising error.")
                                self.driver = _record_forceful_closure(self.memory, self.exec_steps, self.driver, test_steps=test_steps, force_close=True)
                                raise Exception(f"Browser was forcefully closed at step {i}: {step}")

                        before_handles = set(self.driver.window_handles)
                        # previous_handle = self.driver.current_window_handle
                    else:
                        before_handles = set()
                except Exception as e:
                    if "forcefully closed" in str(e) or "No active browser session" in str(e):
                        raise e
                    before_handles = set()
                    logger.warning(
                        f"Could not read window handles before executing step '{step}': {e}"
                    )
                
                # Responsive check moved inside try block after action is known

                try:
                    start = max(0, i - 3)
                    end = min(len(test_steps), i + 4)
                    context = test_steps[start:end]
                    # print(context)
                    # Extract Keywords for RapidFuzz
                    keywords_response,element_name, step_action = keyword_extractor(step, context, serviceProvider, model, apiKey,service_accounts)
                    # logger.info(f"[Step {i}] Keywords extracted: {keywords_response}")
                    try:
                        current_handles = set(self.driver.window_handles)
                        new_handles = current_handles - self.last_known_handles

                        if new_handles and step_action != "switch":

                            original_handle = self.driver.current_window_handle
                            valid_window_found = False

                            for new_handle in new_handles:
                                try:
                                    self.driver.switch_to.window(new_handle)
                                    time.sleep(0.3)

                                    new_url = self.driver.current_url

                                    # Ignore devtools / chrome internal / blank
                                    if (
                                        not new_url
                                        or new_url.startswith("devtools://")
                                        or new_url.startswith("chrome://")
                                        or new_url == "about:blank"
                                    ):
                                        logger.info(f"Ignoring non-user window: {new_url}")
                                        
                                        #s SWITCH BACK immediately
                                        self.driver.switch_to.window(original_handle)
                                        continue

                                    # Real window detected
                                    logger.info(f"Detected REAL new window/tab. Auto-switched focus to: {new_handle}")

                                    intent = (self.last_navigation_intent or {}).get("type")
                                    logger.info(f"Intent---------------------------->: {intent}")

                                    if intent == "window":
                                        action = "SwitchToWindowBasedOnURL"
                                    else:
                                        action = "SwitchToTabBasedOnUrl"

                                    self.memory.append({
                                        "step": step,
                                        "ff_inspecter": "",
                                        "action": action,
                                        "input": new_url,
                                        "keyword": "",
                                        "xpath": "",
                                        "xpath_js": "",
                                        "element_name": action,
                                        "iframe": "",
                                        "drag_element_name": "",
                                        "drop_element_name": "",
                                        "result": True,
                                        "source": "auto_sync"
                                    })

                                    valid_window_found = True
                                    break

                                except Exception as e:
                                    logger.warning(f"Failed inspecting new handle: {e}")
                                    self.driver.switch_to.window(original_handle)

                            # If no valid window found, ensure we are on original
                            if not valid_window_found:
                                self.driver.switch_to.window(original_handle)

                        self.last_known_handles = current_handles


                    except UnexpectedAlertPresentException:
                        logger.info("Alert present during window sync, skipping handles update.")
                    except Exception as e:
                        logger.warning(f"Failed window synchronization: {e}")

                    if element_name:
                        base_name = element_name
                        new_name = base_name
                        count = 0

                        while new_name in self.used_element_names:
                            count += 1
                            new_name = f"{base_name}_{count}"

                        element_name = new_name
                        self.used_element_names.append(element_name)

                    # Liveness check moved to start of loop

                    if step_action == "open" :
                        logger.info(f"[Step {i}] Opening browser...")
                        # if self.has_been_force_closed():
                        if i != 1:
                            self.driver = self.start_browser_session()
                            # Update driver in dependent components
                            extractor.driver = self.driver
                            executor.driver = self.driver
                            self.last_known_handles = set(self.driver.window_handles)
                        
                        memory_item = {
                            "step": step,
                            "action": "OpenBrowser",
                            "input": "",
                            "result": True
                        }
                        self.memory.append(memory_item)
                        self.exec_steps.append(step)
                        continue

                    
                        
                    # Special handling for navigation steps
                    elif step_action == "navigate" :
                        # Detect "previous / back" navigation
                        if "verify" not in step.lower():
                            if "previous" in step.lower() or "back" in step.lower():
                                try:
                                    logger.info(f"[Step {i}] Navigating back to previous page...")
                                    self.driver.back()
                                    memory_item = {
                                        "step": step,
                                        "action": "NavigateBack",
                                        "input": None,
                                        "result": True
                                    }
                                    self.memory.append(memory_item)
                                    self.exec_steps.append(step)

                                    # logger.info(f"[Step {i}] Navigated back successfully.")
                                except Exception as e:
                                    logger.error(f"[Step {i}] Failed to navigate back: {e}")
                                step_time = time.time() - step_start
                                self.total_time += step_time
                                # logger.info(f"[Step {i}] Completed in {step_time:.2f}s")
                                continue

                            # Normal "navigate to URL"
                            url_match = keywords_response[0]
                            if url_match:
                                url = url_match
                                logger.info(f"[Step {i}] Navigating to: {url}")
                                self.driver.get(url)
                                time.sleep(2)

                                memory_item = {
                                    "step": step,
                                    "action": "NavigateToURL",
                                    "input": url,
                                    "result": True
                                }
                                self.memory.append(memory_item)
                                self.exec_steps.append(step)

                                # logger.info(f"[Step {i}] Navigated successfully.")
                            else:
                                logger.warning(f"[Step {i}] No valid URL found in step: {step}")
                                raise Exception(f"No valid URL found in navigation step {i}: {step}")

                            step_time = time.time() - step_start
                            self.total_time += step_time
                            # logger.info(f"[Step {i}] Completed in {step_time:.2f}s")
                            continue
                        else:
                            step_action = "verify"
                    

                    elif step_action == "close":
                        if not self.memory or self.memory[-1].get("action") != "CloseBrowser":
                            logger.info(f"[Step {i}] : {step}")
                            self.memory.append({
                                "step": step,
                                "action": "CloseBrowser",
                                "result": True
                            })
                            # if not self.exec_steps or self.exec_steps[-1] != step:
                            #     self.exec_steps.append(step)
                        self.driver.quit()
                        continue
                        

                    # Capture current DOM
                    if step_action != "wait":
                        if (is_alert_present(self.driver,0)):
                            step_action = "alert"
                            logger.info(f"[Step {i}] Detected an alert popup!")
                            # If there's an alert, extract its details using FF-inspector
                            action,input_text = extractor.ff_inspecter_num_extractor(
                                step, step_action, filtered_json, annotated_dom, element_name, context,server_host, serviceProvider, model, apiKey,service_accounts,isAlert=True
                            )
                    
                    # Annotate and Filter DOM using RapidFuzz
                    if step_action not in ["wait", "close","maximize","open","alert"]:
                        try:
                            # time.sleep(3)
                            raw_dom = self.driver.execute_script(INJECT_AND_SERIALIZE_DOM_JS)
                            # logger.info(f"[INFO] Captured stable DOM for step: {step}")
                        except Exception as e:
                            logger.error(f"[ERROR] Failed to capture DOM: {e}")
                            raw_dom = ""
                        annotated_dom, filtered_json = extractor.annotate_and_simplify_dom(keywords_response, raw_dom, i)
                    else:
                        annotated_dom = ""
                        filtered_json = ""

                    iframe = [False,""]
                    drag_element_name = ""
                    drop_element_name = ""
                    element_type = ""

                    # Handle verification steps
                    if step_action == "verify":
                        # logger.info(f"[Step {i}] Detected verification step, routing to verify module...")
                        
                        
                        try:
                            # Execute verification
                            verification_result, ff_num, verify_action, keyword,element_type, verify_input, xpath_path, xpath_js, iframe = execute_verification(
                                self.driver, annotated_dom, filtered_json, step, element_name, server_host, context, serviceProvider, model, apiKey, service_accounts, auto_healing=extractor.auto_healing
                            )
                            
                            # logger.info(f"DEBUG: verification_result type={type(verification_result)}, value={verification_result!r}")

                            # ---------- TOAST FALLBACK ----------
                            if not verification_result:
                                # logger.info("[Toast Check] Verification failed, checking for toast...")

                                # Run toast worker
                                self._toast_dom_worker()

                                with self.toast_lock:
                                    toast_dom = self.toast_dom

                                toast_text = self.driver.execute_script("return window.__lastToastText;")

                                # logger.info(f"[Toast Check] DOM={bool(toast_dom)}, text={toast_text}")

                                # 1) FIRST: DOM retry (keeps xpath, ff_num, healing)
                                if toast_dom:
                                    logger.info("[Fallback] Retrying verification using toast DOM")

                                    annotated_dom, filtered_json = extractor.annotate_and_simplify_dom(
                                        keywords_response, toast_dom, i
                                    )

                                    verification_result, ff_num, verify_action, keyword, verify_input, xpath_path, xpath_js, iframe = execute_verification(
                                        self.driver,
                                        annotated_dom,
                                        filtered_json,
                                        step,
                                        element_name,
                                        server_host,
                                        context,
                                        serviceProvider,
                                        model,
                                        apiKey,
                                        service_accounts,
                                        auto_healing=extractor.auto_healing
                                    )

                                    if verification_result:
                                        logger.info("Verification passed using toast DOM")


                                # if not toast_dom and not toast_text:
                                #     logger.info("No toast available")

                            # ---------- STOP WATCHER + RESET (ONLY HERE!) ----------
                            self.driver.execute_script("""
                            if (window.__toastObserver) {
                                try { window.__toastObserver.disconnect(); } catch(e) {}
                            }
                            window.__toastDetected = false;
                            window.__lastToastText = null;
                            """)
                            # ALSO reset python state
                            with self.toast_lock:
                                self.toast_dom = None


                            # Store verification result
                            memory_item = {
                                "step": step,
                                "ff_inspecter": ff_num,
                                "action": verify_action,
                                "input": verify_input,
                                "keyword": keyword,
                                "xpath": xpath_path,
                                "xpath_js": xpath_js,
                                "element_type": element_type,
                                "result": verification_result,
                                "iframe": iframe,
                                "drag_element_name": drag_element_name,
                                "drop_element_name": drop_element_name,
                                "element_name": element_name,
                                "source": "primary"
                            }
                            
                            self.memory.append(memory_item)
                            self.exec_steps.append(step)

                            if verification_result:
                                logger.info(f"[Step {i}] Verification PASSED: {verify_action}")
                            else:
                                logger.warning(f"[Step {i}] Verification FAILED: {verify_action}")
                            
                            self.total_time += step_time
                            logger.info(f"[Step {i}] Verification completed in {step_time:.2f}s")
                            self._update_cleaned_memory(extractor)
                            continue
                            
                        except Exception as e:
                            logger.error(f"[Step {i}] Verification processing error: {e}")
                            # Add failed verification to memory
                            memory_item = {
                                "step": step,
                                "action": "VerificationError",
                                "input": None,
                                "result": False,
                                "error": str(e)
                            }
                            self.memory.append(memory_item)
                            continue
                    
                    # Handle get steps
                    elif step_action == "get":
                        logger.info(f"[Step {i}] Detected get step, routing to get module...")
                        try:
                            # Execute get
                            get_result, ff_num, get_action, keyword,element_type, get_input, xpath_path, xpath_js, iframe = execute_get(
                                self.driver, annotated_dom, filtered_json, step,element_name, context,server_host, serviceProvider, model, apiKey,service_accounts, auto_healing=extractor.auto_healing
                            )
                            
                            # Store get result in memory
                            
                            memory_item = {
                                "step": step,
                                "ff_inspecter": ff_num,
                                "action": get_action,
                                "input": get_input,
                                "keyword": keyword,
                                "xpath": xpath_path,
                                "xpath_js": xpath_js,
                                "result": get_result,
                                "element_type": element_type,
                                "iframe": iframe,
                                "drag_element_name":drag_element_name,
                                "drop_element_name":drop_element_name,
                                "element_name": element_name,
                                "source": "primary"
                            }
                            self.memory.append(memory_item)
                            
                            self.exec_steps.append(step)
                            
                            # logger.info(f"[Step {i}] Get SUCCESS for {get_action}: {get_result}")
                            
                            step_time = time.time() - step_start
                            self.total_time += step_time
                            logger.info(f"[Step {i}] Get completed in {step_time:.2f}s")
                            self._update_cleaned_memory(extractor)
                            continue
                            
                        except Exception as e:
                            logger.error(f"[Step {i}] Get processing error: {e}")
                            memory_item = {
                                "step": step,
                                "action": "GetError",
                                "input": None,
                                "result": "error",
                                "error": str(e)
                            }
                            self.memory.append(memory_item)
                            continue

                    elif step_action == "switch":
                        logger.info(f"[Step {i}] Detected switch step, routing to switch module...")
                        try:
                            # Execute switch
                            switch_result, ff_num, switch_action, keyword,element_type, switch_input, xpath_path, xpath_js, iframe = execute_switch(
                                self.driver, annotated_dom, filtered_json, step,element_name, context,server_host, serviceProvider, model, apiKey,service_accounts, auto_healing=extractor.auto_healing
                            )
                            
                            # Store switch result in memory
                            
                            memory_item = {
                                "step": step,
                                "ff_inspecter": ff_num,
                                "action": switch_action,
                                "input": switch_input,
                                "keyword": keyword,
                                "element_type": element_type,
                                "xpath": xpath_path,
                                "xpath_js": xpath_js,
                                "result": switch_result,
                                "iframe": iframe,
                                "drag_element_name":drag_element_name,
                                "drop_element_name":drop_element_name,
                                "element_name": element_name,
                                "source": "primary"
                            }
                            self.memory.append(memory_item)
                            
                            self.exec_steps.append(step)
                            
                            # logger.info(f"[Step {i}] switch SUCCESS for {switch_action}: {switch_result}")
                            
                            step_time = time.time() - step_start
                            self.total_time += step_time
                            logger.info(f"[Step {i}] switch completed in {step_time:.2f}s")
                            self._update_cleaned_memory(extractor)
                            continue
                            
                        except Exception as e:
                            logger.error(f"[Step {i}] switch processing error: {e}")
                            memory_item = {
                                "step": step,
                                "action": "switchError",
                                "input": None,
                                "result": "error",
                                "error": str(e)
                            }
                            self.memory.append(memory_item)
                            continue

                    elif step_action == "drag_and_drop":
                        action, drag, drop,xpath_path, drag_element_name,drop_element_name,element_type = extractor.ff_inspecter_num_extractor(
                            step, step_action, filtered_json, annotated_dom, element_name, context,server_host, serviceProvider, model, apiKey,service_accounts,isDrag=True
                        )
                        ff_num1 = int(drag.split("-")[-1])
                        ff_num2 = int(drop.split("-")[-1])
                        ff_num = [ff_num1,ff_num2]
                        action = "builtin_draganddroptoelement"
                        input_text = ""
                        num_of_scrolls = None
                        direction = None
                        keyword = "drag and drop"
                        context = ""
                        server_host = ""

                    elif step_action == "maximize":
                        ff_num = 0
                        action = "maximize"
                        input_text = ""
                        xpath_path = ""
                        num_of_scrolls = None
                        direction = None
                        keyword = "maximize window"
                        context = ""
                        server_host = ""

                        
                    elif step_action == "alert":
                        ff_num = 0
                        action = action
                        input_text = input_text
                        xpath_path = ""
                        num_of_scrolls = None
                        direction = None
                        keyword = "alert"
                        context = ""
                        server_host = ""
                                        
                    else:
                        # Use LLM to determine element (FF-inspecter) using Filtered JSON
                        ff_num, action, input_text,keyword,element_type, num_of_scrolls, direction, xpath_path = extractor.ff_inspecter_num_extractor(
                            step, step_action, filtered_json, annotated_dom, element_name, context,server_host, serviceProvider, model, apiKey,service_accounts
                        )

                    logger.info(
                        f"XPath={xpath_path}"
                    )

                   

                    # Store annotated_dom in executor for screenshot fallback
                    executor.annotated_dom = annotated_dom

                    # Execute the step using the WebStepExecutor instance
                    success, action, xpath_js, iframe, input_text = executor.execute_step(
                        step, i, ff_num, action, input_text, keyword, num_of_scrolls, direction, xpath_path
                    )
                    # Record success/failure and update memory
                    source = "primary"
                    if not success:
                        logger.warning(f"[Step {i}] Primary execution failed. Attempting vision fallback...")
                        # Try vision fallback
                        success, action, xpath_js, ff_num_vision, iframe = executor._try_vision_fallback(step, context ,annotated_dom,element_name, i, action, input_text,server_host)
                        if success:
                            logger.info(f"[Step {i}] Vision fallback succeeded!")            
                            ff_num = ff_num_vision
                            source = "vision"
                        else:
                            logger.error(f"[Step {i}] Vision fallback also failed.")
                            source = None
                            # self.driver = _record_failure_and_close(self.memory, self.exec_steps, self.driver, reason=f"Vision fallback also failed during Step {i}", browser_session=self.browser_session, test_steps=test_steps, force_close=True)
                            # self.browser_session = None
                            # break
                        
                        if not hasattr(executor, 'last_exception') or not executor.last_exception:
                             executor.last_exception = Exception(f"Vision fallback also failed for step '{step}'")

                    if success:
                        memory_item = {
                            "step": step,
                            "ff_inspecter": ff_num,
                            "action": action,
                            "input": input_text,
                            "keyword": keyword,
                            "xpath": xpath_path,
                            "xpath_js": xpath_js,
                            "element_name": element_name,
                            "element_type": element_type,
                            "iframe": iframe,
                            "drag_element_name":drag_element_name,
                            "drop_element_name":drop_element_name,
                            "result": True,
                            "source": source
                        }
                        self.memory.append(memory_item)


                        
                            
                        self.exec_steps.append(step)
                        logger.info(f"[Step {i}] Executed successfully.")
                    else:
                        logger.error(f"[Step {i}] Failed to execute after primary and vision attempts.")
                        _record_failure_and_close(self.memory, self.exec_steps, self.driver, reason=f"Step {i} failed", browser_session=self.browser_session, test_steps=test_steps, force_close=True)
                        self.browser_session = None
                        self.failed_step_raw = json.dumps([{
                            "step": step,
                            "ff_inspecter": ff_num,
                            "action": action,
                            "input": input_text,
                            "keyword": keyword,
                            "element_type": element_type,
                            "xpath": xpath_path,
                            "xpath_js": xpath_js,
                            "element_name": element_name,
                            "iframe": iframe,
                            "drag_element_name":drag_element_name,
                            "drop_element_name":drop_element_name,
                            "result": False,
                            "source": source
                        }])
                        if hasattr(executor, 'last_exception') and executor.last_exception:
                             raise executor.last_exception
                        raise Exception(f"Automation stopped at Step {i}: '{step}'. Element not found or action failed after multiple attempts.")

                except WebDriverException as e:
                    logger.error(f" WebDriver crashed during Step {i}: {e}")
                    _record_failure_and_close(self.memory, self.exec_steps, self.driver, reason=f"WebDriver crashed during Step {i}", browser_session=self.browser_session, test_steps=test_steps, force_close=True)
                    self.browser_session = None
                    raise e
                except Exception as e:
                    logger.error(f" Unexpected error during Step {i}: {e}")
                    
                    
                    
                    if "Document is empty" in str(e) or "Refused" in str(e):
                        _record_forceful_closure(self.memory, self.exec_steps, self.driver, test_steps=test_steps, force_close=True)
                    else:
                        _record_failure_and_close(self.memory, self.exec_steps, self.driver, reason=f"Unexpected error during Step {i}: {str(e)}", test_steps=test_steps, force_close=True)
                        
                    # Don't double-wrap specific stop errors
                    if "Automation stopped" in str(e) or "forcefully closed" in str(e):
                        raise e
                        
                    raise e

                # Timing
                step_time = time.time() - step_start
                self.total_time += step_time
                logger.info(f"[Step {i}]  Completed in {step_time:.2f}s")
                
                # Update partial memory after each successful step
                self._update_cleaned_memory(extractor)
        
        except Exception as e:
            if 'extractor' in locals() and extractor:
                self._update_cleaned_memory(extractor)
            raise e
        finally:
            if 'extractor' in locals() and extractor:
                self._update_cleaned_memory(extractor)
            
        return self.cleaned_memory, self.exec_steps

    def _update_cleaned_memory(self, extractor):
        """Helper to convert current memory to cleaned JSON and store on self."""
        try:
            json_memory = json.dumps(self.memory)
            auto_healing_results = extractor.auto_healing.get_all_results()
            self.cleaned_memory = convert_memory_to_clean_json(json_memory, auto_healing_results)
            
            if self.failed_step_raw:
                failed_items = convert_memory_to_clean_json(self.failed_step_raw, auto_healing_results)
                if failed_items:
                    self.failed_step = failed_items[0]
        except Exception as e:
            logger.error(f"Failed to convert memory: {e}")
