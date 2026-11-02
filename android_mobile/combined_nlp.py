import json
from LLMcall import call_grok_llm
import re
from lxml import etree
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
import time
from pydantic import BaseModel, Field,ValidationError
from enum import Enum
import subprocess
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
import logging
import os
import glob
from appium.webdriver.connectiontype import ConnectionType
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class nlpCombined_enum(Enum):
    MOB_SetCapability = "MOB_SetCapability"
    MOB_EnterDataAndPressKey = "MOB_EnterDataAndPressKey"
    MOB_EnterUrl = "MOB_EnterUrl"
    MOB_OpenMobileApplication = "MOB_OpenMobileApplication"
    MOB_IsAppInstalled = "MOB_IsAppInstalled"
    MOB_SetEmulatorPowerPercentage = "MOB_SetEmulatorPowerPercentage"
    MOB_ReceiveMessageOnEmulator = "MOB_ReceiveMessageOnEmulator"
    MOB_UninstallAPK = "MOB_UninstallAPK"
    MOB_InstallAPK = "MOB_InstallAPK"
    MOB_SetClipBoardText = "MOB_SetClipBoardText"
    MOB_PressAnyKeyNTimes = "MOB_PressAnyKeyNTimes"
    MOB_SetContext = "MOB_SetContext"
    MOB_TerminateAppUsingAppPackage = "MOB_TerminateAppUsingAppPackage"
    MOB_OpenAppWithApkFilePath = "MOB_OpenAppWithApkFilePath"
    MOB_ActivateAppUsingAppPackage = "MOB_ActivateAppUsingAppPackage"
    MOB_ExecuteJavaScript = "MOB_ExecuteJavaScript"
    MOB_LongPress = "MOB_LongPress"
    MOB_Clear = "MOB_Clear"
    MOB_EnterInputIntoElementFromClipBoard = "MOB_EnterInputIntoElementFromClipBoard"
    MOB_FindElement = "MOB_FindElement"
    MOB_FindElements = "MOB_FindElements"
    MOB_OpenNotification = "MOB_OpenNotification"
    MOB_PressEnterKey = "MOB_PressEnterKey"
    MOB_ResetApp = "MOB_ResetApp"
    MOB_HideKeyboard = "MOB_HideKeyboard"
    MOB_SetEmulatorPowerStateOff = "MOB_SetEmulatorPowerStateOff"
    MOB_OpenChromeBrowser = "MOB_OpenChromeBrowser"
    MOB_SetDeviceOrientationAsPortrait = "MOB_SetDeviceOrientationAsPortrait"
    MOB_SetDeviceOrientationAsLandscape = "MOB_SetDeviceOrientationAsLandscape"
    MOB_SetEmulatorPowerStateOn = "MOB_SetEmulatorPowerStateOn"
    MOB_AirplaneModeSwitchOn = "MOB_AirplaneModeSwitchOn"
    MOB_LockDevice = "MOB_LockDevice"
    MOB_WifiSwitchOff = "MOB_WifiSwitchOff"
    MOB_WifiSwitchOn = "MOB_WifiSwitchOn"
    Continue = "Continue"
    MOB_GpsSwitchOn = "MOB_GpsSwitchOn"
    MOB_GpsSwitchOff = "MOB_GpsSwitchOff"
    MOB_RestartCurrentDevice = "MOB_RestartCurrentDevice"
    MOB_AirplaneModeSwitchOff = "MOB_AirplaneModeSwitchOff"
    Break = "Break"

    MOB_PinchInByPercent = "MOB_PinchInByPercent"
    MOB_PinchOutByPercent = "MOB_PinchOutByPercent"
    MOB_Click = "MOB_Click"
    MOB_CreateCapabilitiesInstance = "MOB_CreateCapabilitiesInstance"
    MOB_PressAnyKey = "MOB_PressAnyKey"
    MOB_PressBackSpaceKey = "MOB_PressBackSpaceKey"
    MOB_PressSpaceKey = "MOB_PressSpaceKey"
    MOB_RunAppInBackground = "MOB_RunAppInBackground"
    MOB_SetAppiumDriverSettings = "MOB_SetAppiumDriverSettings"
    MOB_SetDriverInstance = "MOB_SetDriverInstance"
    MOB_SetImplicitTimeOut = "MOB_SetImplicitTimeOut"
    MOB_SwitchToGivenActivity = "MOB_SwitchToGivenActivity"
    MOB_SwitchToNativeView = "MOB_SwitchToNativeView"
    MOB_SwitchToView = "MOB_SwitchToView"
    MOB_TakeScreenShotAndCompareWithImage = "MOB_TakeScreenShotAndCompareWithImage"
    MOB_TakeScreenshotAndCompareSectionWithImage = "MOB_TakeScreenshotAndCompareSectionWithImage"
    MOB_TakeScreenshotAndCompareWithImageIgnoringSpecifiedSection = "MOB_TakeScreenshotAndCompareWithImageIgnoringSpecifiedSection"

 

class FFInspecterResponse(BaseModel):
    attribute_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element.",
        examples=["Fire-Flink-x"]
    )

    nlpName:nlpCombined_enum = Field(..., description="The selected NLP name.", examples=["x"])

    input_text: str = Field(
        "",
        description="Input text extracted from the step.",
        examples=["x"]
    )

    keyword: str = Field(
        "",
        description="element keyword or field name identified from the step.",
        examples=[ "x","x"]
    )
    element_type: str = Field(
        ...,
        description="The type of the UI element (e.g.Button,Link,Text Field,Text,Image,Checkbox,Radio Button,Icon,Toggle Button ).",
        examples=["x"]
    )
    keycode: str = Field(
        ...,
        description="The keycode of the key mentioned in the step.",
        examples=["x"]
    )

# Parse NLP list from the string
COMBINED_NLP_STRING = (
"MOB_SetCapability","MOB_EnterUrl","MOB_OpenMobileApplication",
"MOB_IsAppInstalled","MOB_SetEmulatorPowerPercentage","MOB_ReceiveMessageOnEmulator","MOB_UninstallAPK",
"MOB_InstallAPK","MOB_SetClipBoardText","MOB_PressAnyKeyNTimes",
"MOB_SetContext","MOB_TerminateAppUsingAppPackage","MOB_OpenAppWithApkFilePath","MOB_ActivateAppUsingAppPackage",
"MOB_ExecuteJavaScript","MOB_LongPress","MOB_Clear","MOB_EnterInputIntoElementFromClipBoard",
"MOB_FindElement","MOB_FindElements","MOB_OpenNotification","MOB_PressEnterKey","MOB_ResetApp","MOB_HideKeyboard",
"MOB_SetEmulatorPowerStateOff","MOB_OpenChromeBrowser","MOB_SetDeviceOrientationAsPortrait","MOB_SetDeviceOrientationAsLandscape",
"MOB_SetEmulatorPowerStateOn","MOB_AirplaneModeSwitchOn","MOB_LockDevice","MOB_WifiSwitchOff",
"Continue","MOB_GpsSwitchOn","MOB_GpsSwitchOff","MOB_RestartCurrentDevice","MOB_AirplaneModeSwitchOff","Break","MOB_WifiSwitchOn",
"MOB_PinchInByPercent","MOB_PinchOutByPercent","MOB_Click",
"MOB_CreateCapabilitiesInstance","MOB_PressAnyKey","MOB_PressBackSpaceKey","MOB_PressSpaceKey","MOB_RunAppInBackground",
"MOB_SetAppiumDriverSettings","MOB_SetDriverInstance","MOB_SetImplicitTimeOut",
"MOB_TakeScreenShotAndCompareWithImage","MOB_TakeScreenshotAndCompareSectionWithImage","MOB_TakeScreenshotAndCompareWithImageIgnoringSpecifiedSection"

)


# NLP_LIST = WAIT_NLP_STRING.split(",")

def match_nlp_via_llm(simplified_dom, step, nlp_list,filtered_steps, serviceProvider, model, apiKey,service_accounts):
    elementType = ["link","textfield","icon","button","radiobutton","checkbox","tab","action overflow button","hamburger menu","toggle button","steppers","sliders"]
    prompt = f"""
You are an intelligent assistant that extracts structured UI action data.
Given the step: "{step}", the simplified DOM: {json.dumps(simplified_dom, ensure_ascii=False)}, and the list of NLP names: {nlp_list}.

Select the perfect matching NLP name from the list that best fits the step's intent.

Return **only valid JSON** in the following format:
{{
  "attribute_value": "Fire-Flink-x",
  "nlpName": "x",
  "input_text":"x",
  "keyword": "x",
  "element_type": "x",
  "keycode": "x"
}}
Rules:
- nlpName must be exactly one from the provided list.
- Use context from the steps : {filtered_steps}, keyword and json to search for FF-inspecter.
- **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
- If step has mutipul inputs add all in input_text and all matched attribute_value also.
- Extract input_text from the step, if you can't find any input text in the step, return keyword as input_text.input can be number, app package, apk file path.dont include extra words.
- Extract keyword from the step, if the step contains any keyword.
- Extract keycode of keys if the step contains any key name like ENTER,SPACE,BACKSPACE etc and give keycode of the given key.
- Use the closest semantic match for the {step}; return attribute_value as Fire-Flink-0, only if nothing is found.
- Based on step give most relevant type of element. use this list to choose element_type: {elementType} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
- Respond with valid JSON only.
"""
    usage = {}
    try:
         # Call Groq LLM using your wrapper
        response_text, usage = call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts)

        # Parse JSON safely
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try cleaning or fallback extraction
            cleaned = response_text.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
        logger.info("[JSON Combined_nlp Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))

        #  Validate with Pydantic model
        validated = FFInspecterResponse(**data)
        # logger.info(f"[Validation Success]: {validated}")

        # Extract all FF numbers
        # matches = re.findall(r'Fire-Flink-(\d+)', validated.attribute_value)
        # ff_num = ",".join(matches) if matches else validated.attribute_value.split("-")[-1]
        ff_num = validated.attribute_value.split("-")[-1]
        nlpName = validated.nlpName.value
        input_text = validated.input_text
        keyword = validated.keyword
        element_type = validated.element_type
        keycode = validated.keycode

        return ff_num,nlpName,input_text,keyword, element_type,keycode,usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
    except ValidationError as e:
        logger.info(f" Pydantic Validation Error]: {e}")
        return -1, None, "", "","","",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]

    except Exception as e:
        logger.info(f"[ Error in ff_inspecter_num_extractor]: {e}")
        return -1, None, "", "","","",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
            
#---------------- ACTION CHAINS ---------------- #
def actionchains_tap(driver, x, y):
    finger = PointerInput("touch", "finger")
    action = ActionBuilder(driver, mouse=finger)

    action.pointer_action.move_to_location(x, y)
    action.pointer_action.pointer_down()
    action.pointer_action.pause(0.05)
    action.pointer_action.pointer_up()
    action.perform()


def actionchains_double_tap(driver, x, y):
    actionchains_tap(driver, x, y)
    actionchains_tap(driver, x, y)


def actionchains_long_press(driver, x, y, duration_ms=800):
    finger = PointerInput("touch", "finger")
    action = ActionBuilder(driver, mouse=finger)

    action.pointer_action.move_to_location(x, y)
    action.pointer_action.pointer_down()
    action.pointer_action.pause(duration_ms / 1000)
    action.pointer_action.pointer_up()
    action.perform()


# ---------------- ACTION EXECUTION FUNCTIONS ---------------- #

def execute_find_element(driver, element, input_text):
    try:
        children = element.find_elements(AppiumBy.XPATH, "./*")
        child_info = []
        for el in children:
            child_info.append({
                "class": el.get_attribute("class"),
                "resource_id": el.get_attribute("resource-id"),
                "text": el.get_attribute("text"),
                "content_desc": el.get_attribute("content-desc"),
            })

        logger.info(f"Found {len(children)} child elements: {child_info}")
        return True, element
    except:
        return False, None


def execute_find_elements(driver, element, input_texts):
    try:
        children = element.find_elements(AppiumBy.XPATH, ".//*")
        child_info = []
        for el in children:
            child_info.append({
                "class": el.get_attribute("class"),
                "resource_id": el.get_attribute("resource-id"),
                "text": el.get_attribute("text"),
                "content_desc": el.get_attribute("content-desc"),
            })

        logger.info(f"Found {len(children)} child elements: {child_info}")
        return True, element
    except:
        return False, None


def execute_tap_n_times(driver, element, input_text):
    try:
        count = int(input_text)

        for _ in range(count):
            element.click()

        return True, count
    except:
        return False, None


def execute_long_press(driver, element, input_text):
    try:
        try:
            duration = int(input_text)
        except:
            duration = 900

        rect = element.rect
        x = rect["x"] + rect["width"] // 2
        y = rect["y"] + rect["height"] // 2

        actionchains_long_press(driver, x, y, duration)
        return True, duration
    except:
        return False, None


def execute_clear(driver, element, input_text):
    try:
        element.clear()
        return True, True
    except:
        return False, None


def execute_enter_input_into_element_from_clipboard(driver, element, input_text):
    try:
        text = driver.get_clipboard_text()
        element.send_keys(text)
        return True, text
    except:
        return False, None


def execute_double_tap(driver, element, input_text):
    try:
        if element is None:
            logger.info("Error: Element is None in execute_double_tap")
            return False, None
            
        rect = element.rect
        x = rect["x"] + rect["width"] // 2
        y = rect["y"] + rect["height"] // 2

        actionchains_double_tap(driver, x, y)
        return True, True
    except Exception as e:
        logger.info(f"Error in execute_double_tap: {e}")
        return False, None


def execute_tap_on_specified_location(driver, element, input_text):
    try:
        input_text = input_text.split(",")
        x, y = int(input_text[0]), int(input_text[1])
        actionchains_tap(driver, x, y)
        return True, (x, y)
    except:
        return False, None


def execute_set_capability(driver, element, input_text):
    try:
        return True, input_text
    except:
        return False, None


def execute_enter_url(driver, element, input_text):
    try:
        driver.get(input_text)
        return True, input_text
    except:
        return False, None


def execute_open_mobile_application(driver, element, input_text):
    try:
        package, activity = input_text
        driver.start_activity(package, activity)
        return True, package
    except:
        return False, None


def execute_is_app_installed(driver, element, input_text):
    try:
        if not input_text:
            logger.info("Error: input_text (package name or app name) is missing")
            return False, None
            
        target = str(input_text).strip()
        logger.info(f"Checking if app is installed: {target}")

        # 1. Try direct check (if input is a full package name)
        if driver.is_app_installed(target):
            logger.info(f"App '{target}' is installed (direct match).")
            return True, True

        # 2. Fallback: Search installed packages via ADB (if input is just a name like 'abhibus')
        # logger.info(f"Direct match failed. Searching for package containing '{target}' via ADB...")
        
        udid = driver.capabilities.get("udid")
        cmd_prefix = f"adb -s {udid} shell" if udid else "adb shell"
        cmd = f"{cmd_prefix} pm list packages"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            packages = result.stdout.lower()
            if target.lower() in packages:
                logger.info(f"Found package matching '{target}' in installed packages.")
                return True, True
        
        logger.info(f"App '{target}' not found.")
        return True, False 
        
    except Exception as e:
        logger.info(f"Error in execute_is_app_installed: {e}")
        return False, None


def execute_set_emulator_power_percentage(driver, element, input_text):
    try:
        percent = int(input_text)
        driver.set_power_capacity(percent)
        return True, percent
    except:
        return False, None


def execute_receive_message_on_emulator(driver, element, input_text):
    try:
        number, message = input_text
        driver.send_sms(number, message)
        return True, message
    except:
        return False, None


def execute_uninstall_apk(driver, element, input_text):
    try:
        if not input_text:
            return False, None
            
        target = str(input_text).strip()
        
        # 1. Try direct uninstall (assuming it's a full package name)
        if "." in target:
             try:
                 driver.remove_app(target)
                 return True, target
             except:
                 pass # Fallback to search

        # 2. Search installed packages
        udid = driver.capabilities.get("udid")
        cmd_prefix = f"adb -s {udid} shell" if udid else "adb shell"
        cmd = f"{cmd_prefix} pm list packages"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            packages = result.stdout.lower()
            # Find lines containing "package:" + target
            for line in packages.splitlines():
                if target.lower() in line:
                    # Extract package name: "package:com.example.app" -> "com.example.app"
                    pkg = line.replace("package:", "").strip()
                    logger.info(f"Uninstalling found package: {pkg}")
                    driver.remove_app(pkg)
                    return True, pkg
                    
        return False, None
    except Exception as e:
        logger.info(f"Error in execute_uninstall_apk: {e}")
        return False, None




def execute_install_apk(driver, element, input_text):
    try:
        if not input_text:
            return False, None
            
        target = str(input_text).strip()
        
        # 1. If it looks like a path or ends with .apk, try direct install
        if target.endswith(".apk") or "\\" in target or "/" in target:
            driver.install_app(target)
            return True, target
            
        # 2. Search for APK in current directory matching the name
        # e.g. "abhibus" -> find "abhibus.apk" or "*abhibus*.apk"
        logger.info(f"Searching for APK matching '{target}' in current directory...")
        files = glob.glob(f"*{target}*.apk")
        
        if files:
            apk_path = os.path.abspath(files[0])
            logger.info(f"Found APK: {apk_path}")
            driver.install_app(apk_path)
            return True, apk_path
            
        logger.info(f"No APK found matching '{target}'")
        return False, None
    except Exception as e:
        logger.info(f"Error in execute_install_apk: {e}")
        return False, None


def execute_set_clipboard_text(driver, element, input_text):
    try:
        driver.set_clipboard_text(input_text)
        return True, input_text
    except:
        return False, None


def execute_double_tap_at_specified_location(driver, element, input_text):
    try:
        input_text = input_text.split(",")
        x, y = int(input_text[0]), int(input_text[1])
        actionchains_double_tap(driver, x, y)
        return True, (x, y)
    except:
        return False, None


def execute_press_any_key_n_times(driver, element, input_text):
    try:
        keycode, count = input_text
        count = int(count)

        for _ in range(count):
            driver.press_keycode(int(keycode))

        return True, count
    except:
        return False, None


def execute_set_context(driver, element, input_text):
    try:
        driver.switch_to.context(input_text)
        return True, input_text
    except:
        return False, None


def execute_terminate_app_using_app_package(driver, element, input_text):
    try:
        driver.terminate_app(input_text)
        return True, input_text
    except:
        return False, None


def execute_open_app_with_apk_file_path(driver, element, input_text):
    # This function name implies "Open", but the implementation is "Install".
    # Reusing execute_install_apk to benefit from the robust search logic.
    # Note: This will NOT launch the app, only install it.
    return execute_install_apk(driver, element, input_text)


def execute_activate_app_using_app_package(driver, element, input_text):
    return execute_install_apk(driver, element, input_text)


def execute_execute_javascript(driver, element, input_text):
    try:
        result = driver.execute_script(input_text)
        return True, result
    except:
        return False, None





# --------------- #

def execute_pinch_in_by_percent(driver, element,input=20):
    """Pinch-in = zoom in"""
    try:
        opts = {
            "elementId": element.id,  # Targets your specific element
            "percent": int(input)/100  # Spread percentage
        }
        driver.execute_script("mobile: pinchOpenGesture", opts)
        # time.sleep(0.3)  # Pause between steps for smoothness

        # time.sleep(0.5)  # Let app react
        return True, None

    except Exception as e:
        logger.error(f"Zoom in failed: {e}")
        return False, str(e)


def execute_pinch_out_by_percent(driver, element, input=20):
    try:
        size = driver.get_window_size()
        w, h = size["width"], size["height"]

        # Center the gesture box horizontally and vertically
        margin_w = int(w * 0.20)   # 15% left + right excluded
        margin_h = int(h * 0.25)   # top & bottom excluded

        opts = {
            "left": margin_w,
            "top": margin_h,
            "width": w - (margin_w * 2),
            "height": h - (margin_h * 2),
            "percent": int(input) / 100,
            "speed": 600
        }

        driver.execute_script("mobile: pinchCloseGesture", opts)
        return True, None

    except Exception as e:
        return False, str(e)


# def execute_click(driver, element, *_):
#     try:
#         element.click()
#         return True, None
#     except:
#         return False, None

def execute_clear_then_enter_input(driver, element, input_text):
    try:
        element.clear()
        element.send_keys(input_text)
        return True, None
    except:
        return False, None


# def execute_click_at_specified_location(driver, input_text, *_):
#     try:
#         x, y = map(int, input_text.split(","))
#         driver.tap([(x, y)])
#         return True, None
#     except:
#         return False, None


# def execute_create_capabilities_instance(driver, *_):
#     try:
#         return True, None
#     except:
#         return False, None


def execute_enter_data_and_press_key(driver, element, input_text,key):
    try:
        element.send_keys(input_text)
        driver.press_keycode(int(key))
        logger.info(f"Entered data and pressed keycode {key}")
        return True, None
    except:
        return False, None


def execute_press_any_key(driver, element, input_text,key):
    try:
        driver.press_keycode(int(key))
        return True, None
    except:
        return False, None


def execute_press_back_space_key(driver, *_):
    try:
        driver.press_keycode(67)     # KEYCODE_DEL
        return True, None
    except:
        return False, None


def execute_press_space_key(driver, *_):
    try:
        driver.press_keycode(62)     # KEYCODE_SPACE
        return True, None
    except:
        return False, None


def execute_run_app_in_background(driver,element, input_text):
    try:
        driver.background_app(int(input_text))
        return True, None
    except:
        return False, None


# def execute_set_appium_driver_settings(driver, input_text, *_):
#     try:
#         driver.update_settings(eval(input_text))  # expects dict string format
#         return True, None
#     except:
#         return False, None


# def execute_set_driver_instance(driver, *_):
#     try:
#         return True, None
#     except:
#         return False, None


def execute_set_implicit_time_out(driver, input_text, *_):
    try:
        driver.implicitly_wait(int(input_text))
        return True, None
    except:
        return False, None


# def execute_switch_to_given_activity(driver, input_text, *_):
#     try:
#         pkg, act = input_text.split(",")
#         driver.start_activity(pkg, act)
#         return True, None
#     except:
#         return False, None


# def execute_switch_to_native_view(driver, *_):
#     try:
#         driver.context = "NATIVE_APP"
#         return True, None
#     except:
#         return False, None


# def execute_switch_to_view(driver, input_text, *_):
#     try:
#         driver.context = input_text
#         return True, None
#     except:
#         return False, None


# def execute_take_screen_shot_and_compare_with_image(driver, *_):
#     try:
#         driver.get_screenshot_as_png()
#         return True, None
#     except:
#         return False, None


# def execute_take_screenshot_and_compare_section_with_image(driver, *_):
#     try:
#         driver.get_screenshot_as_png()
#         return True, None
#     except:
#         return False, None


# def execute_take_screenshot_and_compare_with_image_ignoring_specified_section(driver, *_):
#     try:
#         driver.get_screenshot_as_png()
#         return True, None
#     except:
#         return False, None


# Map NLP names to functions
EXECUTE_Action_FUNCTIONS = {
    "MOB_FindElement": execute_find_element,
    "MOB_FindElements": execute_find_elements,
    "MOB_TapNTimes": execute_tap_n_times,
    "MOB_LongPress": execute_long_press,
    "MOB_Clear": execute_clear,
    "MOB_EnterInputIntoElementFromClipBoard": execute_enter_input_into_element_from_clipboard,
    "MOB_DoubleTap": execute_double_tap,
    "MOB_TapOnSpecifiedLocation": execute_tap_on_specified_location,
    "MOB_SetCapability": execute_set_capability,
    "MOB_EnterUrl": execute_enter_url,
    "MOB_OpenMobileApplication": execute_open_mobile_application,
    "MOB_IsAppInstalled": execute_is_app_installed,
    "MOB_SetEmulatorPowerPercentage": execute_set_emulator_power_percentage,
    "MOB_ReceiveMessageOnEmulator": execute_receive_message_on_emulator,
    "MOB_UninstallAPK": execute_uninstall_apk,
    "MOB_InstallAPK": execute_install_apk,
    "MOB_SetClipBoardText": execute_set_clipboard_text,
    "MOB_DoubleTapAtSpecifiedLocation": execute_double_tap_at_specified_location,
    "MOB_PressAnyKeyNTimes": execute_press_any_key_n_times,
    "MOB_SetContext": execute_set_context,
    "MOB_TerminateAppUsingAppPackage": execute_terminate_app_using_app_package,
    "MOB_OpenAppWithApkFilePath": execute_open_app_with_apk_file_path,
    "MOB_ActivateAppUsingAppPackage": execute_activate_app_using_app_package,
    "MOB_ExecuteJavaScript": execute_execute_javascript,

    "MOB_PinchInByPercent": execute_pinch_in_by_percent,
    "MOB_PinchOutByPercent": execute_pinch_out_by_percent,
    # "MOB_Click": execute_click,
    "MOB_ClearThenEnterInput": execute_clear_then_enter_input,
    # "MOB_ClickAtSpecifiedLocation": execute_click_at_specified_location,
    # "MOB_CreateCapabilitiesInstance": execute_create_capabilities_instance,
    "MOB_EnterDataAndPressKey": execute_enter_data_and_press_key,
    "MOB_PressAnyKey": execute_press_any_key,
    "MOB_PressBackSpaceKey": execute_press_back_space_key,
    "MOB_PressSpaceKey": execute_press_space_key,
    "MOB_RunAppInBackground": execute_run_app_in_background,
    # "MOB_SetAppiumDriverSettings": execute_set_appium_driver_settings,
    # "MOB_SetDriverInstance": execute_set_driver_instance,
    "MOB_SetImplicitTimeOut": execute_set_implicit_time_out,
    # "MOB_SwitchToGivenActivity": execute_switch_to_given_activity,
    # "MOB_SwitchToNativeView": execute_switch_to_native_view,
    # "MOB_SwitchToView": execute_switch_to_view,
    # "MOB_TakeScreenShotAndCompareWithImage": execute_take_screen_shot_and_compare_with_image,
    # "MOB_TakeScreenshotAndCompareSectionWithImage": execute_take_screenshot_and_compare_section_with_image,
    # "MOB_TakeScreenshotAndCompareWithImageIgnoringSpecifiedSection": execute_take_screenshot_and_compare_with_image_ignoring_specified_section
}

# -----------------------------
# DEVICE / SYSTEM FUNCTIONS

def execute_open_notification(driver):
    try:
        driver.open_notifications()
        return True, None
    except:
        return False, None


def execute_press_enter_key(driver):
    try:
        driver.press_keycode(66)  # KEYCODE_ENTER
        return True, None
    except:
        return False, None


def execute_reset_app(driver):
    try:
        app_package = driver.capabilities.get("appPackage")
        if not app_package:
            app_package = driver.current_package
            
        if app_package:
            driver.terminate_app(app_package)
            driver.activate_app(app_package)
            return True, None
        else:
            logger.info(" Error in execute_reset_app: Could not determine app_package")
            return False, None
    except Exception as e:
        logger.info(f" Error in execute_reset_app: {e}")
        return False, None


def execute_hide_keyboard(driver):
    try:
        driver.hide_keyboard()
        return True, None
    except:
        return False, None


def execute_set_emulator_power_state_off(driver):
    try:
        driver.set_power_state("off")
        return True, None
    except:
        return False, None


def execute_open_chrome_browser(driver):
    try:
        driver.activate_app("com.android.chrome")
        return True, "com.android.chrome"
    except:
        return False, None


def execute_set_device_orientation_portrait(driver):
    try:
        driver.orientation = "PORTRAIT"
        return True, "PORTRAIT"
    except Exception as e2:
        logger.info(f" Error in execute_set_device_orientation_portrait fallback: {e2}")
        return False, None


def execute_set_device_orientation_landscape(driver):
    try:
        driver.orientation = "LANDSCAPE"
        return True, "LANDSCAPE"
    except Exception as e2:
        logger.info(f" Error in execute_set_device_orientation_landscape fallback: {e2}")
        return False, None


def execute_set_emulator_power_state_on(driver):
    try:
        driver.set_power_state("on")
        return True, None
    except:
        return False, None


def execute_airplane_mode_switch_on(driver):
    try:
        driver.toggle_airplane_mode()
        return True, "ON"
    except Exception as e:
        logger.info(f"driver.toggle_airplane_mode failed: {e}")
        try:
            udid = driver.capabilities.get("udid")
            cmd_prefix = f"adb -s {udid} shell" if udid else "adb shell"
            
            logger.info(f"Attempting ADB fallback for AIRPLANE MODE ON...")
            # Try 'cmd connectivity' (Android 10+)
            subprocess.run(f"{cmd_prefix} cmd connectivity airplane-mode enable", shell=True)
            # Backup: settings put (might not trigger UI update without broadcast, but broadcast fails)
            subprocess.run(f"{cmd_prefix} settings put global airplane_mode_on 1", shell=True)
            
            time.sleep(2)
            return True, "ON"
        except Exception as e2:
            logger.info(f" Error in execute_airplane_mode_switch_on fallback: {e2}")
            return False, None


def execute_lock_device(driver):
    try:
        driver.lock()
        return True, None
    except:
        return False, None


def execute_wifi_switch_off(driver):
    try:
        current_state = driver.get_network_connection()
        
        # If Wi-Fi is ON (2 or 6), switch it OFF
        if current_state in [ConnectionType.WIFI_ONLY, ConnectionType.ALL_NETWORK_ON]:
            driver.set_network_connection(ConnectionType.DATA_ONLY)  # Wi-Fi OFF
            return True, "OFF"
        
        # Already OFF
        return True, "ALREADY_OFF"
    
    except Exception as e:
        return False, str(e)


def execute_wifi_switch_on(driver):
    try:
        current_state = driver.get_network_connection()
        
        # If Wi-Fi is OFF (0, 1, 4), switch it ON
        if current_state in [
            ConnectionType.NO_CONNECTION,
            ConnectionType.AIRPLANE_MODE,
            ConnectionType.DATA_ONLY,
        ]:
            driver.set_network_connection(ConnectionType.WIFI_ONLY)
            return True, "ON"
        
        # Already ON
        return True, "ALREADY_ON"
    
    except Exception as e:
        return False, str(e)


def execute_continue(driver):
    try:
        return True, "CONTINUE"
    except:
        return False, None


def execute_gps_switch_on(driver):
    try:
        current_state = driver.get_network_connection()

        # If GPS (Location Services) is OFF → switch ON
        # GPS ON is represented by ALL_NETWORK_ON on many Android versions (6)
        if current_state not in [ConnectionType.ALL_NETWORK_ON]:
            driver.toggle_location_services()   # enables GPS
            return True, "ON"
        
        # Already ON
        return True, "ALREADY_ON"
    
    except Exception as e:
        return False, str(e)

def execute_gps_switch_off(driver):
    try:
        current_state = driver.get_network_connection()

        # If GPS is ON (ALL_NETWORK_ON = 6), then switch OFF
        if current_state == ConnectionType.ALL_NETWORK_ON:
            driver.toggle_location_services()   # this will disable GPS
            return True, "OFF"
        
        # Already OFF
        return True, "ALREADY_OFF"
    
    except Exception as e:
        return False, str(e)



def execute_restart_current_device(driver):
    try:
        udid = driver.capabilities.get("udid")
        cmd_prefix = f"adb -s {udid}" if udid else "adb"
        
        logger.info(f" Attempting ADB reboot on {udid or 'default device'}...")
        subprocess.run(f"{cmd_prefix} reboot", shell=True)
        return True, None
    except Exception as e:
        logger.info(f" Error in execute_restart_current_device: {e}")
        return False, None


def execute_airplane_mode_switch_off(driver):
        try:
            udid = driver.capabilities.get("udid")
            cmd_prefix = f"adb -s {udid} shell" if udid else "adb shell"
            
            logger.info(f" Attempting ADB fallback for AIRPLANE MODE OFF...")
            # Try 'cmd connectivity' (Android 10+)
            subprocess.run(f"{cmd_prefix} cmd connectivity airplane-mode disable", shell=True)
            # Backup: settings put
            subprocess.run(f"{cmd_prefix} settings put global airplane_mode_on 0", shell=True)
            
            time.sleep(2)
            return True, "OFF"
        except Exception as e2:
            logger.info(f" Error in execute_airplane_mode_switch_off fallback: {e2}")
            return False, None


def execute_break(driver):
    try:
        return True, "BREAK"
    except:
        return False, None

EXECUTE_Utility_FUNCTIONS = {
    "MOB_OpenNotification": execute_open_notification,
    "MOB_PressEnterKey": execute_press_enter_key,
    "MOB_ResetApp": execute_reset_app,
    "MOB_HideKeyboard": execute_hide_keyboard,
    "MOB_SetEmulatorPowerStateOff": execute_set_emulator_power_state_off,
    "MOB_OpenChromeBrowser": execute_open_chrome_browser,
    "MOB_SetDeviceOrientationAsPortrait": execute_set_device_orientation_portrait,
    "MOB_SetDeviceOrientationAsLandscape": execute_set_device_orientation_landscape,
    "MOB_SetEmulatorPowerStateOn": execute_set_emulator_power_state_on,
    "MOB_AirplaneModeSwitchOn": execute_airplane_mode_switch_on,
    "MOB_LockDevice": execute_lock_device,
    "MOB_WifiSwitchOff": execute_wifi_switch_off,
    "MOB_WifiSwitchOn": execute_wifi_switch_on,
    "Continue": execute_continue,
    "MOB_GpsSwitchOn": execute_gps_switch_on,
    "MOB_GpsSwitchOff": execute_gps_switch_off,
    "MOB_RestartCurrentDevice": execute_restart_current_device,
    "MOB_AirplaneModeSwitchOff": execute_airplane_mode_switch_off,
    "Break": execute_break
}



def execute_combinedAction(driver ,annotated_dom, simplified_dom, step,filtered_steps, serviceProvider, model, apiKey,service_accounts):
    keycode=""
    ff_num, nlp_name,input_text, keyword, element_type,keycode, input_tokens,output_tokens,total_tokens = match_nlp_via_llm(simplified_dom, step, COMBINED_NLP_STRING,filtered_steps, serviceProvider, model, apiKey,service_accounts)
    xpath_path = ""
    if nlp_name in EXECUTE_Utility_FUNCTIONS:
        func = EXECUTE_Utility_FUNCTIONS[nlp_name]
        result = func(driver)
        logger.info(f"Get result non-execution for {nlp_name}: {result}")
        return result, 0, nlp_name , input_text,keyword, xpath_path, element_type,keycode, input_tokens,output_tokens,total_tokens
    # if nlp_name == "MOB_FindElements":
    #     ff_nums = [x.strip() for x in str(ff_num).replace(",", " ").split()]
    #     input_texts = [x.strip() for x in str(input_text).split(",")]
    #     elements=[]
    #     xpaths=[]
    #     for ff_val in ff_nums:
    #         try:
    #             tree = etree.fromstring(annotated_dom.encode('utf-8'))
    #             target = tree.xpath(f"//*[@FF-inspecter='Fire-Flink-{ff_val}']")
    #             if target:
    #                 element_xpath = target[0]
    #                 xpath_path = etree.ElementTree(tree).getpath(element_xpath)
    #                 xpaths.append(xpath_path)
    #             else:
    #                 xpath_path = ""
    #         except Exception as e:
    #             xpath_path = "" 
    #         try:
    #             # xpath = f"//*[@FF-inspecter='Fire-Flink-{ff_val}']"
    #             logger.info(xpath_path)
    #             element = driver.find_element(AppiumBy.XPATH,xpath_path)
    #             logger.info("Element found successfully")
    #             elements.append(element)
    #         except Exception as e:
    #             # logger.info(f"Failed to find element: {e}")
    #             element = None
    #             elements.append(element)
    #     # logger.info(len(elements),len(input_texts),elements)
    #     if len(elements)==len(input_texts):
    #         result=True
    #     else:
    #         result=False
    #     return result, ff_num, nlp_name , input_text,keyword, xpaths, element_type,keycode, input_tokens,output_tokens,total_tokens

    if not nlp_name or nlp_name not in EXECUTE_Action_FUNCTIONS  :
        logger.info(f"No matching Execution NLP for step: {step} and nlp is {nlp_name}")
        return False, ff_num, nlp_name , input_text,keyword, xpath_path, element_type,keycode, input_tokens,output_tokens,total_tokens
    
    

    try:
        tree = etree.fromstring(annotated_dom.encode('utf-8'))
        target = tree.xpath(f"//*[@FF-inspecter='Fire-Flink-{ff_num}']")
        element_xpath = target[0]
        xpath_path = etree.ElementTree(tree).getpath(element_xpath)
    except Exception as e:
        xpath_path = ""

    try:
        # xpath = f"//*[@FF-inspecter='Fire-Flink-{ff_num}']"
        logger.info(xpath_path)
        element = driver.find_element(AppiumBy.XPATH,xpath_path)
        logger.info("Element found successfully")

    except Exception as e:
        # logger.info(f"Failed to find element: {e}")
        element = None


    func = EXECUTE_Action_FUNCTIONS[nlp_name]
    
    # if nlp_name in ["MOB_FindElement", "MOB_FindElements"]:
    #     xpath = (AppiumBy.XPATH, xpath_path)
    #     result,value = func(driver, element, xpath)
    if nlp_name in ["MOB_EnterDataAndPressKey","MOB_PressAnyKey"]:
        result,value = func(driver, element, input_text,keycode)
    else:
        result,value = func(driver, element, input_text)

    logger.info(f"Combined result for {nlp_name}: {result}")

    action = nlp_name

    return result ,ff_num, action , input_text,keyword, xpath_path, element_type,keycode, input_tokens,output_tokens,total_tokens
