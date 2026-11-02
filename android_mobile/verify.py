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
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
class nlpName_enum(Enum):
    MOB_VerifyText = "MOB_VerifyText"
    MOB_VerifyAttributeValue = "MOB_VerifyAttributeValue"
    MOB_VerifyPartialAttributeValue = "MOB_VerifyPartialAttributeValue"
    MOB_VerifyElementIsDisplayed = "MOB_VerifyElementIsDisplayed"
    MOB_VerifyElementIsEnabled = "MOB_VerifyElementIsEnabled"           
    MOB_VerifyElementIsDisabled = "MOB_VerifyElementIsDisabled"
    MOB_VerifyBatteryLevel = "MOB_VerifyBatteryLevel"
    MOB_VerifyPartialText = "MOB_VerifyPartialText"
    MOB_VerifyElementIsClickable = "MOB_VerifyElementIsClickable"
    MOB_VerifyIfKeyboardIsHidden = "MOB_VerifyIfKeyboardIsHidden"
    MOB_VerifyIfKeyboardIsShown = "MOB_VerifyIfKeyboardIsShown"
    MOB_VerifyIfXAndYCoordinateOfElement = "MOB_VerifyIfXAndYCoordinateOfElement"
    MOB_VerifyHeightOfElement = "MOB_VerifyHeightOfElement"
    MOB_VerifyXLocationOfAndroidElement = "MOB_VerifyXLocationOfAndroidElement"
    MOB_VerifyIfDeviceIsUnlocked = "MOB_VerifyIfDeviceIsUnlocked"
    MOB_VerifyIfWifiOff = "MOB_VerifyIfWifiOff"
    MOB_VerifyElementIsSelected = "MOB_VerifyElementIsSelected"
    MOB_VerifyIfWifiOn = "MOB_VerifyIfWifiOn"
    MOB_VerifyIfDeviceIsLocked = "MOB_VerifyIfDeviceIsLocked"
    MOB_VerifyIfAirplaneModeOff = "MOB_VerifyIfAirplaneModeOff"
    MOB_VerifyIfGpsOff = "MOB_VerifyIfGpsOff"
    MOB_VerifyHexCodeForGivenXYCoordinates = "MOB_VerifyHexCodeForGivenXYCoordinates"
    MOB_VerifyYLocationOfAndroidElement = "MOB_VerifyYLocationOfAndroidElement"
    MOB_VerifyIfGpsOn = "MOB_VerifyIfGpsOn"
    MOB_VerifyIfAirplaneModeOn = "MOB_VerifyIfAirplaneModeOn"
    MOB_VerifyWidthOfElement = "MOB_VerifyWidthOfElement"
    MOB_VerifyElementIsNotDisplayed = "MOB_VerifyElementIsNotDisplayed"
    MOB_VerifyElementNotContainsText = "MOB_VerifyElementNotContainsText"
    MOB_VerifyIfAppIsClosed = "MOB_VerifyIfAppIsClosed"
    MOB_VerifyElementIsDisplayedInSpecifiedTime = "MOB_VerifyElementIsDisplayedInSpecifiedTime"
    MOB_VerifyElementIsEnabledInSpecifiedTime = "MOB_VerifyElementIsEnabledInSpecifiedTime"
    MOB_VerifyElementIsDisabledInSpecifiedTime = "MOB_VerifyElementIsDisabledInSpecifiedTime"

    

class FFInspecterResponse(BaseModel):
    FF_inspector_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element. ",
        examples=["Fire-Flink-x"]
    )

    nlpName: nlpName_enum = Field(..., description="The selected NLP name.", examples=["x"])

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
    locator_type: str = Field(
        ...,
        description="Locator type that mentioned in step (like text,content-desc,resource-id).",
        examples=["x"]
    )

# Parse NLP list from the string
NLP_STRING = (
    "MOB_VerifyElementIsDisplayed,MOB_VerifyElementIsEnabled,MOB_VerifyElementIsSelected,MOB_VerifyText,MOB_VerifyAttributeValue,MOB_VerifyPartialAttributeValue,"
    "MOB_VerifyElementIsDisplayedInSpecifiedTime,MOB_VerifyElementIsEnabledInSpecifiedTime,MOB_VerifyElementIsDisabledInSpecifiedTime,"
    "MOB_VerifyBatteryLevel,MOB_VerifyPartialText,MOB_VerifyElementIsClickable,"
    "MOB_VerifyIfKeyboardIsHidden,MOB_VerifyIfKeyboardIsShown,MOB_VerifyIfXAndYCoordinateOfElement,"
    "MOB_VerifyHeightOfElement,MOB_VerifyXLocationOfAndroidElement,MOB_VerifyIfDeviceIsUnlocked,"
    "MOB_VerifyIfWifiOff,MOB_VerifyElementIsSelectedInSpecifiedTime,MOB_VerifyIfWifiOn,MOB_VerifyIfDeviceIsLocked,"
    "MOB_VerifyIfAirplaneModeOff,MOB_VerifyIfGpsOff,MOB_VerifyHexCodeForGivenXYCoordinates,"
    "MOB_VerifyYLocationOfAndroidElement,MOB_VerifyIfGpsOn,MOB_VerifyIfAirplaneModeOn,"
    "MOB_VerifyWidthOfElement,MOB_VerifyElementIsNotDisplayed,MOB_VerifyElementNotContainsText,"
    "MOB_VerifyIfAppIsClosed"
)

NLP_LIST = NLP_STRING.split(",")

def match_nlp_via_llm(simplified_dom, step, nlp_list,filtered_steps, serviceProvider, model, apiKey,service_accounts):
    elementType = ["link","textfield","icon","button","radiobutton","checkbox","tab","action overflow button","hamburger menu","toggle button","steppers","sliders"]
    prompt = f"""
You are an intelligent assistant that extracts structured UI action data.
Given the step: "{step}", the simplified DOM: {json.dumps(simplified_dom, ensure_ascii=False)}, and the list of NLP names: {nlp_list}.

Select the perfect matching NLP name from the list that best fits the step's intent.

Return **only valid JSON** in the following format:
{{
  "FF_inspector_value": "Fire-Flink-x",
  "nlpName": "x",
  "input_text":"x"
  "keyword": "x",
  "element_type": "x",
  "locator_type":"x"
}}
Rules:
- nlpName must be exactly one from the provided list.
- Use context from the steps : {filtered_steps}, keyword and json to search for FF-inspecter.
- **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
- For some steps you can see two inputs but you need to uderstand step and send the requred input_text.
        ex: Verify the flights matches the flight,Verify the home has 30 and 50 coordinates
        here keyword : "flights" , input : flight, here input:30,50
- If step mention time and element name then Input_text should be elementname,time.
        example: Verify the home is displayed for 30 seconds 
        here keyword : "home" , input : home,30
- If step mention verify text then only pick MOB_VerifyText nlp otherwise pick MOB_VerifyElementIsDisplayed.
- Extract input_text from the step that is which is being verified in the {step}, if you can't find any input text in the step, return keyword as input_text.
- Extract keyword from the step, if the step contains any keyword.
- Use the closest semantic match for the {step}; return attribute_value as Fire-Flink-0, only if nothing is found.
- Based on step give most relevant type of element. use this list to choose element_type: {elementType} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
- Extract locator_type if mentioned in the step, like(text,resource-id,content-desc) . if not found return 'empty'.
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
        logger.info("[JSON Verification Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))

        #  Validate with Pydantic model
        validated = FFInspecterResponse(**data)
        # logger.info(f"[Validation Success]: {validated}")

        ff_num = validated.FF_inspector_value.split("-")[-1]
        nlpName = validated.nlpName.value
        input = validated.input_text
        keyword = validated.keyword
        element_type = validated.element_type
        locator_type = validated.locator_type

        return ff_num,nlpName,input,keyword, element_type,locator_type,usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
    except ValidationError as e:
        logger.error(f" Pydantic Validation Error]: {e}")
        return -1, None, "", "","","",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]

    except Exception as e:
        logger.error(f"[ Error in ff_inspecter_num_extractor]: {e}")
        return -1, None, "", "","","",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
            

# Execution functions for each NLP

def execute_verify_text(driver,element,input):
    try:
        logger.info(element.get_attribute("text"))
        if element.get_attribute("text").lower() == input.lower() or element.get_attribute("content-desc").lower() == input.lower():
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_attribute_value(driver, element, input,attribute_name):
    try:
        logger.info(element.get_attribute(attribute_name))
        if element.get_attribute(attribute_name).lower() == input.lower():
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False

    
def execute_verify_partial_attribute_value(driver, element, input,attribute_name):
    try:
        logger.info(element.get_attribute(attribute_name))
        if input.lower() in element.get_attribute(attribute_name).lower():
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
    
def execute_verify_element_is_displayed(driver,element,input_text):
    try:
        if element:
            input_text = input_text.split(",")
            input_text = input_text[0]
            logger.info(element.get_attribute("enabled"))
            if element.get_attribute("enabled").lower() == "true":
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_element_is_enabled(driver,element,input_text):
    try:
        if element:
            input_text = input_text.split(",")
            input_text = input_text[0]
            if element.get_attribute("enabled") == "true":
                return True
            else:
                return False    
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
    
def execute_verify_element_is_disabled(driver,element,input):
    try:
        if element:
            if element.get_attribute("enabled") != "true":
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_battery_level(driver,element, input):
    try:
        if not input:
            return False
        expected_level =int(input)
        battery = driver.battery_info
        if battery is None:
            logger.info("Unable to fetch battery info from device.")
            return False
        actual_level = battery.get("level")
        if actual_level == expected_level:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_partial_text(driver, element, input):
    try:
        logger.info(element.get_attribute("text"))
        if input.lower() in element.get_attribute("text").lower():
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_element_is_clickable(driver,element, input):
    try:
        if element:
            if element.get_attribute("clickable") == "true":
                return True
            else:
                return False  # Approximation
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_keyboard_is_hidden(driver,element,input):
    try:
        if driver.is_keyboard_shown():
            return False
        else:
            return True
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_keyboard_is_shown(driver,element,input):
    try:
        if driver.is_keyboard_shown():
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_x_and_y_coordinate_of_element(driver,element, input):
    try:
        if len(input) < 2:
            logger.info("Expected X and Y are missing in input")
            return False
        expected_x = int(input[0])
        expected_y = int(input[1])
        loc = element.location
        actual_x = loc.get("x")
        actual_y = loc.get("y")
        if actual_x == expected_x and actual_y == expected_y:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_height_of_element(driver,element, input):
    try:
        if not input:
            logger.info("Height input missing.")
            return False
        expected_height = int(input)
        actual_height = element.size["height"]
        if actual_height == expected_height:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_x_location_of_android_element(driver,element, input):
    try:
        if not input:
            return False
        expected_x = int(input)
        loc = element.location
        actual_x = loc.get("x")
        if actual_x == expected_x:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_device_is_unlocked(driver,element,input):
    try:
        locked = driver.is_locked()
        if not locked:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_wifi_off(driver,element,input):
    try:
        connection_type = driver.network_connection
        logger.info(f"Current network connection type: {connection_type}")
        if connection_type in [2, 6]:
            return False
        else:
            return True # WiFi is OFF
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_element_is_selected(driver,element,input_text):
    try:
        input_text = input_text.split(",")
        input_text = input_text[0]
        if element.get_attribute("selected")== "true":
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_wifi_on(driver,element,input):
    try:
        connection_type = driver.network_connection
        logger.info(f"Current network connection type: {connection_type}")
        if connection_type in [2, 6]:
            return True
        else:
            return False# WiFi is OFF
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_device_is_locked(driver,element,input):
    try:
        locked = driver.is_locked()
        if locked:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_airplane_mode_off(driver,element,input):
    try:
        connection_type = driver.network_connection
        if connection_type == 1:
            return False
        else:
            return True
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_gps_off(driver,element,input):
    try:
        result = subprocess.run(
            ["adb", "shell", "settings", "get", "secure", "location_mode"],
            capture_output=True,
            text=True
        )
        mode = result.stdout.strip()
        if mode==0:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
# def execute_verify_hex_code_for_given_xy_coordinates(driver, element, input):
#     if len(input) < 3:
#         return False
#     x = int(input[0])
#     y = int(input[1])
#     expected_hex = input[2]
#     # Get pixel color at x,y
#     # Placeholder
#     return True
def execute_verify_y_location_of_android_element(driver,element, input):
    try:
        if not input:
            return False
        expected_y = int(input)
        loc = element.location
        actual_x = loc.get("x")
        if actual_x == expected_y:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_gps_on(driver,element,input):
    try:
        result = subprocess.run(
            ["adb", "shell", "settings", "get", "secure", "location_mode"],
            capture_output=True,
            text=True
        )
        mode = result.stdout.strip()
        if mode!=0:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_if_airplane_mode_on(driver, element, input):
    try:
        connection_type = driver.network_connection
        if connection_type == 1:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_width_of_element(driver,element, input):
    try:
        if not input:
            return False
        expected_width = int(input)
        if not element:
            logger.info("Element not found.")
            return False
        element = element[0]  # first match
        actual_width = element.size("width")
        if actual_width == expected_width:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_element_is_not_displayed(driver,element,input):
    try:
        if element:
            if element.get_attribute("enabled") != "true":
                return True
            else:
                return False
        else:
            return True
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_verify_element_not_contains_text(driver,element,input):
    try:
        if element:
            if element.get_attribute("text") !=input:
                return True
            else:
                return False
        else:
            return True
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
        
def execute_verify_if_app_is_closed(driver,element,input):
    try:
        app_package = driver.capabilities.get("appPackage")
        current_app = driver.current_package
        if current_app != app_package :
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False

# Map NLP names to functions
EXECUTE_FUNCTIONS = {
    "MOB_VerifyText": execute_verify_text,
    "MOB_VerifyAttributeValue": execute_verify_attribute_value,
    "MOB_VerifyPartialAttributeValue": execute_verify_partial_attribute_value,
    "MOB_VerifyElementIsDisplayed": execute_verify_element_is_displayed,
    "MOB_VerifyElementIsEnabled": execute_verify_element_is_enabled,
    "MOB_VerifyElementIsDisabled": execute_verify_element_is_disabled,
    "MOB_VerifyBatteryLevel": execute_verify_battery_level,
    "MOB_VerifyPartialText": execute_verify_partial_text,
    "MOB_VerifyElementIsClickable": execute_verify_element_is_clickable,
    "MOB_VerifyIfKeyboardIsHidden": execute_verify_if_keyboard_is_hidden,
    "MOB_VerifyIfKeyboardIsShown": execute_verify_if_keyboard_is_shown,
    "MOB_VerifyIfXAndYCoordinateOfElement": execute_verify_if_x_and_y_coordinate_of_element,
    "MOB_VerifyHeightOfElement": execute_verify_height_of_element,
    "MOB_VerifyXLocationOfAndroidElement": execute_verify_x_location_of_android_element,
    "MOB_VerifyIfDeviceIsUnlocked": execute_verify_if_device_is_unlocked,
    "MOB_VerifyIfWifiOff": execute_verify_if_wifi_off,
    "MOB_VerifyElementIsSelected": execute_verify_element_is_selected,
    "MOB_VerifyIfWifiOn": execute_verify_if_wifi_on,
    "MOB_VerifyIfDeviceIsLocked": execute_verify_if_device_is_locked,
    "MOB_VerifyIfAirplaneModeOff": execute_verify_if_airplane_mode_off,
    "MOB_VerifyIfGpsOff": execute_verify_if_gps_off,
    # "MOB_VerifyHexCodeForGivenXYCoordinates": execute_verify_hex_code_for_given_xy_coordinates,
    "MOB_VerifyYLocationOfAndroidElement": execute_verify_y_location_of_android_element,
    "MOB_VerifyIfGpsOn": execute_verify_if_gps_on,
    "MOB_VerifyIfAirplaneModeOn": execute_verify_if_airplane_mode_on,
    "MOB_VerifyWidthOfElement": execute_verify_width_of_element,
    "MOB_VerifyElementIsNotDisplayed": execute_verify_element_is_not_displayed,
    "MOB_VerifyElementNotContainsText": execute_verify_element_not_contains_text,
    "MOB_VerifyIfAppIsClosed": execute_verify_if_app_is_closed ,
    "MOB_VerifyElementIsDisplayedInSpecifiedTime": execute_verify_element_is_displayed,
    "MOB_VerifyElementIsEnabledInSpecifiedTime": execute_verify_element_is_enabled,
    "MOB_VerifyElementIsDisabledInSpecifiedTime": execute_verify_element_is_disabled,
}

def execute_verification(driver ,annotated_dom, simplified_dom, step,filtered_steps, serviceProvider, model, apiKey,service_accounts):
    attribute_type=""
    ff_num, nlp_name,input_text, keyword, element_type,attribute_type, input_tokens,output_tokens,total_tokens = match_nlp_via_llm(simplified_dom, step, NLP_LIST,filtered_steps, serviceProvider, model, apiKey,service_accounts)
    xpath_path = ""
    if not nlp_name or nlp_name not in EXECUTE_FUNCTIONS:
        logger.info(f"No matching NLP for step: {step}")
        return False, ff_num, nlp_name ,keyword, input_text, xpath_path, element_type,attribute_type, input_tokens,output_tokens,total_tokens
    
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

    except:
        element = None


    func = EXECUTE_FUNCTIONS[nlp_name]
    
       

    if func not in [execute_verify_attribute_value,execute_verify_partial_attribute_value]:
        result = func(driver, element, input_text)
    else:
        result = func(driver, element, input_text,attribute_type)

    logger.info(f"Verification result for {nlp_name}: {result}")
    if nlp_name == "MOB_VerifyBatteryLevel":
        input_text = float(input_text)
    elif nlp_name == "MOB_VerifyIfXAndYCoordinateOfElement":
        input_text = [x.strip() for x in str(input_text).replace(",", " ").split()]
    action = nlp_name
    if "check" in step.lower() :
        if action == "MOB_VerifyIfAppIsClosed":
            action = "MOB_CheckIfAppIsClosed"
        elif action == "MOB_VerifyElementIsDisplayed":
            action = "MOB_CheckIfElementIsDisplayed"


    return result,ff_num, action ,keyword, input_text, xpath_path, element_type,attribute_type, input_tokens,output_tokens,total_tokens
