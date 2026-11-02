from appium.options.android import UiAutomator2Options
from appium import webdriver
import time
import os
from appium.webdriver.common.appiumby import AppiumBy
from requests import options
from selenium.webdriver.common.by import By
from verify import execute_verification
from get import execute_getAction
from wait import execute_waitAction
from combined_nlp import execute_combinedAction
from scroll import execute_scroll
from screenshot import Screenshot
from appium.options.android import UiAutomator2Options
from appium import webdriver
import subprocess
import xml.etree.ElementTree as ET
from lxml import etree
import logging
import combined_nlp
from xml_extractor import Extractor,keyword_extractor
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# def is_uia2_installed(device_id):
#     packages = os.popen(
#         f"adb -s {device_id} shell pm list packages | findstr io.appium.uiautomator2"
#     ).read()
#     return (
#         "io.appium.uiautomator2.server" in packages
#         and "io.appium.uiautomator2.server.test" in packages
#     )
# def is_uia2_running(device_id):
#     pid = os.popen(
#         f"adb -s {device_id} shell pidof io.appium.uiautomator2.server"
#     ).read().strip()
#     return pid != ""
# def is_uia2_port_ready(device_id):
#     out = os.popen(
#         f"adb -s {device_id} shell netstat -an | findstr 6790"
#     ).read()
#     return "LISTEN" in out or "ESTABLISHED" in out

# def is_uia2_healthy(device_id):
#     if not is_uia2_installed(device_id):
#         return False
#     if not is_uia2_running(device_id):
#         return False
#     if not is_uia2_port_ready(device_id):
#         return False
#     return True

def clear_uiautomator2(device_id):
    cmds = [
        f"adb -s {device_id} shell pm clear io.appium.uiautomator2.server",
        f"adb -s {device_id} shell pm clear io.appium.uiautomator2.server.test"
    ]

    for cmd in cmds:
        # print(f"[INFO] Running: {cmd}")
        subprocess.run(cmd, shell=True, check=False)




# def force_grant_permissions(device_id, app_package):
#     # Location Permissions
#     try:
#         os.system(f"adb -s {device_id} shell pm grant {app_package} android.permission.ACCESS_FINE_LOCATION")
#         os.system(f"adb -s {device_id} shell pm grant {app_package} android.permission.ACCESS_COARSE_LOCATION")

#         # Notification Permission (Android 13+)
#         os.system(f"adb -s {device_id} shell pm grant {app_package} android.permission.POST_NOTIFICATIONS")
#         return True
#     except Exception as e:
#         logger.info(f"Failed to grant permissions: {e}")
#         return False

def create_driver(real_device_id, platform_version, app_package=None, app_activity=None):
    os.system(f"adb -s {real_device_id} shell pm clear {app_package}")
    # clear_uiautomator2(real_device_id)
    # time.sleep(1)
    # uia2_present = is_uia2_healthy(real_device_id)
    # logger.info(f"[INFO] UIAutomator2 present: {uia2_present}")
    # chromedriver_path = get_matching_chromedriver(real_device_id)
    # logger.info(f"[INFO] Using Chromedriver at: {chromedriver_path}")
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = str(platform_version)
    options.set_capability("deviceName", "AndroidDevice")
    options.set_capability("udid", real_device_id)
    options.automation_name = "UiAutomator2"
    # options.full_reset = False
    # options.set_capability("skipDeviceInitialization", True)
    # options.set_capability("skipServerInstallation", uia2_present)
    # options.set_capability("skipServerInitialization", True)
    options.set_capability("ignoreHiddenApiPolicyError", True)
    # result=force_grant_permissions(real_device_id, app_package)
    # logger.info(f"[INFO] Force grant permissions result: {result}")
    options.set_capability("shouldUseCompactResponses", True)
    options.set_capability("ignoreUnimportantViews", False)
    # 🚀 UIAutomator2 performance boosters
    options.set_capability("disableAndroidWatcher", True)
    options.set_capability("disableWindowAnimation", True)
    # options.set_capability("autoGrantPermissions", True)
    options.set_capability("uiautomator2ServerLaunchTimeout", 120000)
    options.set_capability("uiautomator2ServerReadTimeout", 120000)

    # 🚀 DO NOT WAIT FOR IDLE (Biggest speed win)
    # options.set_capability("disableWaitForIdle", True)
    options.set_capability("waitForIdleTimeout", 1000)
    options.set_capability("waitForIdlePollingInterval", 1000)

    # Reduce time Appium waits for element find
    options.set_capability("waitForSelectorTimeout", 1000)

    # PRO TIP: Boost sendKeys speed
    # options.set_capability("unicodeKeyboard", True)
    # options.set_capability("resetKeyboard", True)


    
    # # Inject package and activity
    # if app_package:
    #     options.app_package = app_package
    # if app_activity:
    #     options.app_activity = app_activity
    #     options.set_capability("appWaitActivity", app_activity)
    # First, check if the app package is installed on the device
    # logger.info(f"[INFO] Checking if app {app_package} is installed...")
    check_app_cmd = f"adb -s {real_device_id} shell pm list packages | findstr {app_package}"
    check_output = os.popen(check_app_cmd).read().strip()
    
    if not check_output or app_package not in check_output:
        error_msg = f"App not found: '{app_package}' is not installed on device '{real_device_id}'"
        logger.error(f"[FATAL] {error_msg}")
        return None, error_msg
    
    logger.info(f"[INFO] App {app_package} is installed. Launching app: {app_package}/{app_activity}")

    # adb_output = os.popen(
    # f"adb -s {real_device_id} shell monkey -p {app_package} 1 2>&1"
    #     ).read()

    adb_output = os.popen(
                f"adb -s {real_device_id} shell am start -n {app_package}/{app_activity} 2>&1"
            ).read()

    if "device" in adb_output.lower() and "not found" in adb_output.lower():
        error_msg = f"Device '{real_device_id}' not found or offline."
        logger.error(f"[FATAL] {error_msg}")
        return None, error_msg

    if "Error type 3" in adb_output or "does not exist" in adb_output:
        error_msg = f"App not found or invalid activity: {app_package}/{app_activity} is not installed on the device"
        logger.error(f"[FATAL] {error_msg}")
        return None, error_msg
    
    if "monkey aborted" in adb_output.lower() or "no activities found" in adb_output.lower():
        error_msg = f"Failed to launch app: {app_package} - Invalid activity '{app_activity}' or app not properly installed"
        logger.error(f"[FATAL] {error_msg}")
        return None, error_msg

    # -----------------------
    # Create driver session
    # -----------------------
    start_time = time.time()
    try:
        # driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)
        # time.sleep(1.5)
    except Exception as e:
        error_msg = f"Failed to create driver: {str(e)}"
        logger.error(f"[FATAL] {error_msg}")
        return None, error_msg
    

    total_time = time.time() - start_time
    logger.info(f"[INFO] Driver created in {total_time:.2f} seconds.")

    return driver, None



class AppiumStepExecutor:
    def __init__(self, driver, app_package, real_device_id,filtered_steps):
        self.driver = driver
        self.app_package = app_package
        self.real_device_id = real_device_id
        self.execution_steps = []
        self.all_tokens = 0
        self.memory = []
        self.filtered_steps=filtered_steps

    def execute_close_app(self):
        try:
            self.driver.terminate_app(self.app_package)
        except Exception as error:
            logger.info(f"Warning: could not close app {self.app_package}: {error}")

    def has_been_force_closed(self):
        try:
            cmd = f'adb -s {self.real_device_id} shell dumpsys activity activities | findstr "VisibleActivity"'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(errors="ignore")

            # App is visible → continue execution
            if self.app_package in output:
                return False  # App is visible -> Has been force closed? NO.

            # App NOT visible → closed or crashed
            logger.info(" App force-closed or backgrounded detected")
            self.execute_close_app()

            # Prevent duplicate memory entries if already recorded
            if not self.memory or self.memory[-1].get("action") != "MOB_CloseApp":
                self.memory.append({
                    "step": "Closing Mobile App",
                    "action": "MOB_CloseApp"
                })

            return True  # App NOT visible -> Has been force closed? YES.

        except subprocess.CalledProcessError:
            return False     # On error, assume app is running/not force closed to be safe
        except Exception as e:
            raise Exception("ADB check failed: " + str(e))


    def execute_step(self,filtered_steps,xml_source,step_index, action,element_type,element_name, ff_inspecter_num, xpath_path, input_text, step_str,simplified_json,serviceProvider, model, apiKey,
    step_input_tokens, step_output_tokens, step_total_tokens,keyword):
        if self.has_been_force_closed():
                logger.info("App is closed.")
                return False
                
        result=True
        keycode=""
        ff_inspecter_num = int(ff_inspecter_num) if ff_inspecter_num else 0
        if ff_inspecter_num != 0 or action in ["MOB_DoubleTapAtSpecifiedLocation","MOB_TapOnSpecifiedLocation"]:
            if action in ['navigation']:
                if action == 'navigation':  # Navigation actions
                    if 'back' in step_str.lower():
                        self.driver.back()
                        action = "MOB_PressBackKey"
                        keyword="Back Key"
                        logger.info(f"Performed back action")
                        time.sleep(0.5)
                        
                        # Check if app was force-closed after back
                        # if self.has_been_force_closed():
                        #     logger.info("App force-closed after back action")
                        #     return False
                        # else:
                        success = True
                            
                    elif 'home' in step_str.lower():
                        self.driver.press_keycode(3)  # Home button keycode
                        action = "MOB_PressHomeKey"
                        keyword="Home Key"
                        logger.info(f"Performed home action")
                        time.sleep(0.5)
                        success = True  # Home always succeeds (app goes to background)
                        
                    elif 'recent' in step_str.lower():
                        self.driver.press_keycode(187)  # Recent apps keycode
                        action = "PressAppSwitchKey"
                        keyword="Recent Apps Key"
                        logger.info(f"Performed recent apps action")
                        time.sleep(0.5)
                        success = True  # Recent apps always succeeds
                        
                    else:
                        logger.info(f"Unknown navigation action in step: {step_str}")
                        success = False
                    

            else:
                if xpath_path:
                    logger.info(f"XPath from json")
                    try:
                        element = self.driver.find_element(by="xpath", value=xpath_path)
                    except Exception as e:
                        logger.info(f" Failed to find element with XPath from json")
                        element = None
                        success = False
                else:
                    try:
                        xpath_path = f"//*[@FF-inspecter='Fire-Flink-{ff_inspecter_num}']"
                        logger.info(f"XPath")
                        element = self.driver.find_element(by="xpath", value=xpath_path)
                    except Exception as e:
                        logger.info(f" Failed to find element with FF-inspecter")
                        element = None
                        success = False
                
                if "tap" in action.lower():
                    if action == "MOB_Tap":  # Tap
                        try:
                            element.click()
                            logger.info(f" Tapped element with FF-inspecter {ff_inspecter_num}")
                            success = True
                            action = "MOB_Tap"
                        except Exception as e:
                            logger.info(f"Failed to tap element with FF-inspecter")
                            success = False
                    elif action == "MOB_DoubleTap":  # Double Tap
                        try:
                            success,value=combined_nlp.execute_double_tap(self.driver, element,input_text)
                            logger.info(f" Double Tapped element with FF-inspecter {ff_inspecter_num}")
                        except Exception as e:
                            logger.info(f"Failed to double tap element with FF-inspecter")
                            success = False
                    elif action == "MOB_TapNTimes":  # Tap N Times
                        try:
                            success,value=combined_nlp.execute_tap_n_times(self.driver, element,input_text)
                            logger.info(f" Tapped {value} times element with FF-inspecter {ff_inspecter_num}")
                            print(success,value)
                        except Exception as e:
                            logger.info(f"Failed to tap n times element with FF-inspecter")
                            success = False
                    elif action == "MOB_TapOnSpecifiedLocation":  # Tap on Specified Location
                        try:
                            print("Executing tap on specified location")
                            success,value=combined_nlp.execute_tap_on_specified_location(self.driver, element,input_text)
                            logger.info(f"Tapped on specified location element with FF-inspecter {ff_inspecter_num}")
                        except Exception as e:
                            logger.info(f"Failed to tap on specified location element with FF-inspecter")
                            success = False
                    elif action == "MOB_DoubleTapAtSpecifiedLocation":  # Double Tap on Specified Location
                        try:
                            success,value=combined_nlp.execute_double_tap_at_specified_location(self.driver, element,input_text)
                            logger.info(f"Double Tapped on specified location element with FF-inspecter {ff_inspecter_num}")
                        except Exception as e:
                            logger.info(f"Failed to double tap on specified location element with FF-inspecter")
                            success = False

                elif "enter" in action.lower():  # Enter input
                    try:
                        if action == "MOB_Enter": 
                            element.send_keys(input_text)
                            if element.get_attribute("text") != input_text:
                                os.system(f'adb shell input text {input_text}')
                                logger.info(f"Used adb shell input text as fallback for element with FF-inspecter {ff_inspecter_num}")
                            logger.info(f"Entered '{input_text}' into element with FF-inspecter {ff_inspecter_num}")
                            success = True
                            action = "MOB_SendKeys"
                        elif any(word in step_str.lower() for word in ["clear", "remove"]):
                            element.clear()
                            element.send_keys(input_text)
                            if element.get_attribute("text") != input_text:
                                os.system(f'adb shell input text {input_text}')
                                logger.info(f"Used adb shell input text as fallback for element with FF-inspecter {ff_inspecter_num}")
                            logger.info(f"Entered '{input_text}' into element with FF-inspecter {ff_inspecter_num}")
                            success = True
                            action = "MOB_ClearThenEnterInput"
                        # elif action == "MOB_PressEnterKey":
                        #     try:
                        #         success,value=combined_nlp.execute_press_enter_key(self.driver)
                        #         logger.info(f"Pressed Enter key")
                        #         success = True
                            # except Exception as e:
                            #     logger.info(f"Failed to press Enter key")
                            #     success = False
                        elif action == "MOB_EnterDataAndPressKey":
                            try:
                                ff_num, nlp_name,input_text, keyword, element_type,keycode, input_tokens,output_tokens,total_tokens = combined_nlp.match_nlp_via_llm(simplified_json, step_str, action,filtered_steps, serviceProvider, model, apiKey)
                                success,value=combined_nlp.execute_enter_data_and_press_key(self.driver, element,input_text,keycode)
                                logger.info(f"Entered data and pressed key")
                                # success = True
                            except Exception as e:
                                logger.info(f"Failed to enter data and press key")
                                success = False
                        elif action == "MOB_EnterInputIntoElementFromClipBoard":
                            try:
                                success,value=combined_nlp.execute_enter_input_into_element_from_clipboard(self.driver, element,input_text)
                                logger.info(f"Entered input into element from clipboard")
                                # success = True
                            except Exception as e:
                                logger.info(f"Failed to enter input into element from clipboard")
                                success = False
                        elif action == "MOB_EnterUrl":
                            try:
                                success,value=combined_nlp.execute_enter_url(self.driver, element,input_text)
                                logger.info(f"Entered URL into element")
                                # success = True
                            except Exception as e:
                                logger.info(f"Failed to enter URL into element")
                                success = False
                    except Exception as e:
                        logger.info(f" Failed to enter text into element with FF-inspecter {ff_inspecter_num}: {e}")
                        success = False
                else:
                    logger.info(f"Unknown action {action} for element {ff_inspecter_num}")
                    success = False
        else:
            logger.info(f"FF-inspecter number is 0, cannot locate element.")
            success = False
        self.all_tokens += step_total_tokens

        

        # Save memory only if success
        if success:
            memory_item = {
                    "step":step_str,
                    "type":element_type,
                    "ff_inspecter": ff_inspecter_num,
                    "result": result,
                    "keyword":keyword,
                    "action": action,
                    "input": input_text,
                    "xpath": xpath_path,
                    "element_name":element_name,
                    "keycode":keycode
                    
            }
            self.memory.append(memory_item)

        self.execution_steps.append({
        "step": step_str,
        "index": step_index,
        "success": success,
        "result": result,
        "input_tokens": step_input_tokens,
        "output_tokens": step_output_tokens,
        "total_tokens": step_total_tokens
        })
        

        logger.info(f"Step {step_index} — Input: {step_input_tokens}, Output: {step_output_tokens}, Total: {step_total_tokens}")

        if not success:
            screenshot=Screenshot()
            result,memory,input_tokens,completion_tokens,total_tokens=screenshot.main(step_str,filtered_steps,self.driver,xml_source,keyword,action=action,input_value=input_text,element_type=element_type,element_name=element_name)
            logger.info(f"Step {step_index} — Input: {step_input_tokens}, Output: {step_output_tokens}, Total: {step_total_tokens}")
            if any(word.lower() not in ["swipe", "scroll"] for s in step_str for word in s.split()):
                self.execution_steps.append({
                        "step": step_str,
                        "index": step_index,
                        "success": success,
                        "result": result,
                        "openai_input_tokens": input_tokens,
                        "openai_output_tokens": completion_tokens,
                        "openai_total_tokens": total_tokens
                    })
                if result:
                    time.sleep(2)
                    success = True
                    self.memory.append(memory)
                    
                    return success
                else:
                    success = False
                    return success
            else:
                logger.info("screenshot capture not possible due to swipe/scroll action.")
                success = False
                return success
        
        return success

    def execute_step_files(self, action,step_index,element_name, annotated_dom, simplified_json, step_str, serviceProvider, model, apiKey,service_accounts, initial_input_tokens=0, initial_output_tokens=0, initial_total_tokens=0):
        if self.has_been_force_closed():
                logger.info("App is closed.")
                return False
        result=True
        locator_type = ""
        attribute_type = ""
        keycode = ""
        num_of_scrolls = 0
        direction = ""
        ref_xpath = ""
        if action == 'verification':
            (result,ff_inspecter_num, action ,keyword, input_text,xpath_path, element_type, attribute_type, step_input_tokens,step_output_tokens,step_total_tokens) = execute_verification(self.driver,annotated_dom,simplified_json, step_str,self.filtered_steps, serviceProvider, model, apiKey,service_accounts)
            
            success = result
        elif action == 'get':
            (result,ff_inspecter_num, action , input_text,keyword, xpath_path, element_type, locator_type, attribute_type, step_input_tokens,step_output_tokens,step_total_tokens) = execute_getAction(self.driver,annotated_dom,simplified_json, step_str,self.filtered_steps, serviceProvider, model, apiKey,service_accounts)
            
            success = result
        elif action == 'wait':
            (result,ff_inspecter_num, action , input_text,keyword, xpath_path, element_type, step_input_tokens,step_output_tokens,step_total_tokens) = execute_waitAction(self.driver,annotated_dom,simplified_json, step_str,self.filtered_steps, serviceProvider, model, apiKey,service_accounts)
            
            success = result
        elif action == 'combined':
            (result,ff_inspecter_num, action , input_text,keyword, xpath_path, element_type,keycode, step_input_tokens,step_output_tokens,step_total_tokens) = execute_combinedAction(self.driver,annotated_dom,simplified_json, step_str,self.filtered_steps, serviceProvider, model, apiKey,service_accounts)
            
            success = result
        elif action == 'scroll':
            (result, ff_inspecter_num, action, keyword, input_text, xpath_path,ref_xpath, element_type, num_of_scrolls, direction,
                step_input_tokens, step_output_tokens, step_total_tokens) = execute_scroll(self,
                self.driver, annotated_dom, simplified_json, step_str, self.filtered_steps, serviceProvider, model, apiKey,service_accounts
            )
            # logger.info(f"direction: {direction}, num_of_scrolls: {num_of_scrolls}")
            
            success = result

        else:
            logger.info(f"Unknown action {action} for step {step_str}")
            success = False

        # Add initial tokens (from keyword_extractor) to the step totals
        step_input_tokens += initial_input_tokens
        step_output_tokens += initial_output_tokens
        step_total_tokens += initial_total_tokens

        self.all_tokens += step_total_tokens

        # Save memory only if success
        if success:
            memory_item = {
                    "step":step_str,
                    "type":element_type,
                    "ff_inspecter": ff_inspecter_num,
                    "result": result,
                    "keyword":keyword,
                    "action": action,
                    "input": input_text,
                    "xpath": xpath_path,
                    "locator_type":locator_type,
                    "attribute_type":attribute_type,
                    "keycode":keycode,
                    "element_name":element_name,
                    "num_of_scrolls": num_of_scrolls,
                    "direction": direction,
                    "ref_xpath": ref_xpath
            }
            self.memory.append(memory_item)

        self.execution_steps.append({
        "step": step_str,
        "index": step_index,
        "success": success,
        "result": result,
        "input_tokens": step_input_tokens,
        "output_tokens": step_output_tokens,
        "total_tokens": step_total_tokens
        })
        

        logger.info(f"Step {step_index} — Input: {step_input_tokens}, Output: {step_output_tokens}, Total: {step_total_tokens}")


        return success

    

