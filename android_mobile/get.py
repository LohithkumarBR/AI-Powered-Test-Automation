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

class nlpGet_enum(Enum):
    MOB_GetDeviceLocation = "MOB_GetDeviceLocation"
    MOB_GetAttribute = "MOB_GetAttribute"
    MOB_GetBatteryPercentage = "MOB_GetBatteryPercentage"
    MOB_GetSize = "MOB_GetSize"
    MOB_GetLongitude = "MOB_GetLongitude"
    MOB_GetText = "MOB_GetText"
    MOB_GetRect = "MOB_GetRect"
    MOB_GetPerformanceData = "MOB_GetPerformanceData"
    MOB_GetAltitude = "MOB_GetAltitude"
    MOB_GetLatitude = "MOB_GetLatitude"
    MOB_GetY = "MOB_GetY"
    MOB_GetLocation = "MOB_GetLocation"
    MOB_GetX = "MOB_GetX"
    MOB_GetCurrentDeviceDate = "MOB_GetCurrentDeviceDate"
    MOB_GetMinuteFromCurrentDeviceTime = "MOB_GetMinuteFromCurrentDeviceTime"
    MOB_GetCurrentAppPackage = "MOB_GetCurrentAppPackage"
    MOB_GetAllContexts = "MOB_GetAllContexts"
    MOB_GetHourFromCurrentDeviceTime = "MOB_GetHourFromCurrentDeviceTime"
    MOB_GetSecondFromCurrentDeviceTime = "MOB_GetSecondFromCurrentDeviceTime"
    MOB_GetSupportedPerformanceDataTypes = "MOB_GetSupportedPerformanceDataTypes"
    MOB_GetCurrentOrientation = "MOB_GetCurrentOrientation"
    MOB_GetCurrentDeviceTime = "MOB_GetCurrentDeviceTime"
    MOB_GetCurrentContext = "MOB_GetCurrentContext"
    MOB_GetClipBoardText = "MOB_GetClipBoardText"
    MOB_GetCurrentDeviceStatus = "MOB_GetCurrentDeviceStatus"
    MOB_GetCurrentDeviceSettings = "MOB_GetCurrentDeviceSettings"
    MOB_GetSizeOfScreen = "MOB_GetSizeOfScreen"
    MOB_GetWidthOfElement = "MOB_GetWidthOfElement"
    MOB_GetScreenshotAs = "MOB_GetScreenshotAs"
    MOB_GetWidthOfScreen = "MOB_GetWidthOfScreen"
    MOB_GetADBLogsForGivenAppPackage = "MOB_GetADBLogsForGivenAppPackage"
    MOB_GetBatteryStatus = "MOB_GetBatteryStatus"
    MOB_GetHexCodeForGivenXYCoordinatesOfImage = "MOB_GetHexCodeForGivenXYCoordinatesOfImage"
    MOB_GetCurrentActivity = "MOB_GetCurrentActivity"
    MOB_GetCurrentDeviceSystemBars = "MOB_GetCurrentDeviceSystemBars"
    MOB_GetScreenshot = "MOB_GetScreenshot"
    MOB_GetHeightOfElement = "MOB_GetHeightOfElement"
    MOB_GetTextFromElementAndSetToClipBoard = "MOB_GetTextFromElementAndSetToClipBoard"
    MOB_GetHeightOfScreen = "MOB_GetHeightOfScreen"
    MOB_GetCurrentSessionId = "MOB_GetCurrentSessionId"
    MOB_GetListOfElementsFromLocatorTypeLocatorValue = "MOB_GetListOfElementsFromLocatorTypeLocatorValue"
    MOB_GetCurrentWindowHandle = "MOB_GetCurrentWindowHandle"
    MOB_GetTagName = "MOB_GetTagName"
    MOB_GetTextFromListOfWebElements = "MOB_GetTextFromListOfWebElements"
    MOB_GetDriverInstance = "MOB_GetDriverInstance"
    MOB_GetImplicitTimeOut = "MOB_GetImplicitTimeOut"
    MOB_GetDeviceName = "MOB_GetDeviceName"
    MOB_GetDeviceUdid = "MOB_GetDeviceUdid"
    MOB_GetDeviceOsVersion = "MOB_GetDeviceOsVersion"
    MOB_GetAttributeValueFromListOfWebElements = "MOB_GetAttributeValueFromListOfWebElements"
    GetCurrentSystemDay = "GetCurrentSystemDay"
    GetCurrentSystemMonth = "GetCurrentSystemMonth"
    MOB_GetAllWindowHandles = "MOB_GetAllWindowHandles"

    

class FFInspecterResponse(BaseModel):
    FF_inspector_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element.",
        examples=["Fire-Flink-x"]
    )

    nlpName:nlpGet_enum = Field(..., description="The selected NLP name.", examples=["x"])

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
    attribute_type: str = Field(
        ...,
        description="Locator type that mentioned in step (like text,content-desc,resource-id).",
        examples=["x"]
    )

GET_NLP_STRING = (
"MOB_GetDeviceLocation","MOB_GetBatteryPercentage","MOB_GetLongitude","MOB_GetAltitude","MOB_GetLatitude",
"MOB_GetCurrentDeviceDate","MOB_GetMinuteFromCurrentDeviceTime","MOB_GetCurrentAppPackage","MOB_GetAllContexts",
"MOB_GetHourFromCurrentDeviceTime","MOB_GetSecondFromCurrentDeviceTime","MOB_GetSupportedPerformanceDataTypes",
"MOB_GetCurrentOrientation","MOB_GetCurrentDeviceTime","MOB_GetCurrentContext","MOB_GetCurrentDeviceSettings","GetCurrentSystemDay",
"MOB_GetClipBoardText","GetCurrentSystemMonth","MOB_GetCurrentDeviceStatus","MOB_GetSizeOfScreen","MOB_GetAllWindowHandles","MOB_GetWidthOfScreen",
"MOB_GetBatteryStatus","MOB_GetCurrentActivity","MOB_GetDeviceOsVersion","MOB_GetDeviceUdid","MOB_GetDeviceName","MOB_GetImplicitTimeOut",
"MOB_GetDriverInstance","MOB_GetCurrentWindowHandle","MOB_GetCurrentSessionId","MOB_GetHeightOfScreen","MOB_GetCurrentDeviceSystemBars",
"MOB_GetAttributeValueFromListOfWebElements","MOB_GetTagName","MOB_GetListOfElementsFromLocatorTypeLocatorValue","MOB_GetScreenshot","MOB_GetTextFromElementAndSetToClipBoard",
"MOB_GetHeightOfElement","MOB_GetTextFromListOfWebElements","MOB_GetHexCodeForGivenXYCoordinatesOfImage","MOB_GetADBLogsForGivenAppPackage","MOB_GetScreenshotAs","MOB_GetWidthOfElement",
"MOB_GetX", "MOB_GetLocation","MOB_GetY","MOB_GetPerformanceData","MOB_GetRect","MOB_GetText","MOB_GetSize","MOB_GetAttribute"
)



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
  "locator_type": "x",
  "attribute_type": "x"
}}
Rules:
- nlpName must be exactly one from the provided list.
- for screenshots, extract the input_text from the step. like what they what to name image.if not present then leave it empty.
- Use context from the steps : {filtered_steps}, keyword and json to search for FF-inspecter.
- **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
- Extract input_text from the step, if you can't find any input text in the step, return keyword as input_text.
    ex:Fetch the ADB logs for the abhibus 
    here input: abhibus
- Extract keyword from the step, if the step contains any keyword.
- Use the closest semantic match for the {step}; return attribute_value as Fire-Flink-0, only if nothing is found.
- if step is get location of device or get device location then map to MOB_GetDeviceLocation nlp.
- Based on step give most relevant type of element. use this list to choose element_type: {elementType} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
- Extract locator_type if mentioned in the step, like(text,resource-id,content-desc,xpath) 
- Extract attribute_type if mentioned in the step, like (text,resource-id,content-desc,className).
- Respond with valid JSON only.
"""
    usage = {}
    try:
         # Call Groq LLM using your wrapper
        response_text, usage = call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts)

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try cleaning or fallback extraction
            cleaned = response_text.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
        logger.info("[JSON Get Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))

        #  Validate with Pydantic model
        validated = FFInspecterResponse(**data)
        # logger.info(f"[Validation Success]: {validated}")

        ff_num = validated.FF_inspector_value.split("-")[-1]
        nlpName = validated.nlpName.value
        input_text = validated.input_text
        keyword = validated.keyword
        element_type = validated.element_type
        locator_type = validated.locator_type
        attribiute_type = validated.attribute_type

        return ff_num,nlpName,input_text,keyword, element_type,locator_type,attribiute_type,usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
    except ValidationError as e:
        logger.info(f" Pydantic Validation Error]: {e}")
        return -1, None, "", "","","","",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]

    except Exception as e:
        logger.info(f"[ Error in ff_inspecter_num_extractor]: {e}")
        return -1, None, "", "","","","",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
            

# Execution functions for each NLP

def execute_get_attribute_value_from_list_of_web_elements(driver,element,input,attribute_type):
    try:
        attr_value = element.get_attribute(attribute_type)
        if attr_value:
            logger.info(f"Attribute Value: {attr_value}")
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] execute_get_tag_name failed: {e}")
        return False

def execute_get_tag_name(driver, element, input):
    try:
        tag = element.tag_name
        if not tag:
            tag = element.get_attribute("className")
        if not tag:
            tag = element.get_attribute("class")
            
        logger.info(f"Tag Name: {tag}")
        
        if tag:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] execute_get_tag_name failed: {e}")
        return False
def execute_get_list_of_elements_from_locator(driver,element,input):
    try:
        if element:
            text = element.get_attribute("text")
            content_desc = element.get_attribute("content-desc")
            resource_id = element.get_attribute("resource-id")
            logger.info(f"Found elements with text: {text}, content-desc: {content_desc}, resource-id: {resource_id}")
    
        if text or content_desc or resource_id:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] execute_get_tag_name failed: {e}")
        return False

def execute_get_screenshot(driver, element, filename):
    try:
        # Always enforce .png extension
        if not filename.lower().endswith(".png"):
            filename = f"{filename}.png"

        # Take and save screenshot
        success = driver.get_screenshot_as_file(filename)

        if success:
            # Return success + only the file name
            return True, filename
        else:
            return False, None

    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False, None

def execute_get_text_from_element_and_set_to_clipboard(driver, element,input):
    try:
        text = element.text 
        clip = driver.set_clipboard_text(text)
        if clip:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False

def execute_get_height_of_element(driver, element,input):
    try:
        element_height = element.size['height']
        if element_height:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_get_text_from_list_of_web_elements(driver,element,input):
    try:
        text=element.get_attribute("text")
        if text:
            logger.info(f"Text from elements: {text}")
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] execute_get_tag_name failed: {e}")
        return False
# def execute_get_hex_code_for_xy(driver, x, y):
#     return driver.get_pixel_color(x, y), True
def execute_get_adb_logs_for_given_app_package(driver,element,input):
    try:
        app_package = driver.capabilities.get("appPackage")
        cmd = f'adb logcat -d | findstr {app_package}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        logs = result.stdout.strip()
        if logs:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False

def execute_get_screenshot_as(driver, element, filename):
    if not filename.lower().endswith(".png"):
            filename += ".png"
    try:    
        img = element.screenshot(filename)
        if img:
            return True , filename
        else:
            return False,None
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False,None
def execute_get_width_of_element(driver, element,input):
    try:
        element_width = element.size['width']
        if element_width:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_get_x(driver, element,input):
    try:
        loc = element.location
        actual_x = loc.get("x")
        if actual_x:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_get_location(driver, element,input):
    try:
        loc = element.location
        if loc:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_get_y(driver, element,input):
    try:
        loc = element.location
        actual_y = loc.get("y")
        if actual_y:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
# def execute_get_performance_data(driver, package_name, data_type):
#     return driver.get_performance_data(package_name, data_type), True
def execute_get_rect(driver, element,input):
    try:
        location = element.location
        x = location['x']
        y = location['y']
        # Element size (Width, Height)
        size = element.size
        width = size['width']
        height = size['height']
        if location and size:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_get_text(driver, element,input):
    # text=element.get_attribute("text")
    try:    
        text = element.text 
        if text:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_get_size(driver, element,input):
    try:
        size = element.size
        if size:
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False
def execute_get_attribute(driver, element, attribute):
    try:
        if element.get_attribute(attribute):
            return True
        else:
            return False
    except Exception as e:
        logger.info(f"[ERROR] Screenshot failed: {e}")
        return False


# Map NLP names to functions
EXECUTE_GET_FUNCTIONS = {
    "MOB_GetAttribute": execute_get_attribute,
    "MOB_GetSize": execute_get_size,
    "MOB_GetText": execute_get_text,
    "MOB_GetRect": execute_get_rect,
    # "MOB_GetPerformanceData": execute_get_performance_data,
    "MOB_GetY": execute_get_y,
    "MOB_GetLocation": execute_get_location,
    "MOB_GetX": execute_get_x,
    "MOB_GetWidthOfElement": execute_get_width_of_element,
    "MOB_GetScreenshotAs": execute_get_screenshot_as,
    "MOB_GetADBLogsForGivenAppPackage": execute_get_adb_logs_for_given_app_package,
    # "MOB_GetHexCodeForGivenXYCoordinatesOfImage": execute_get_hex_code_for_given_xy_coordinates_of_image,
    "MOB_GetScreenshot": execute_get_screenshot,
    "MOB_GetHeightOfElement": execute_get_height_of_element,
    "MOB_GetListOfElementsFromLocatorTypeLocatorValue": execute_get_list_of_elements_from_locator,
    "MOB_GetTagName": execute_get_tag_name,
    "MOB_GetTextFromListOfWebElements": execute_get_text_from_list_of_web_elements,
    "MOB_GetAttributeValueFromListOfWebElements": execute_get_attribute_value_from_list_of_web_elements,
    "MOB_GetTextFromElementAndSetToClipBoard": execute_get_text_from_element_and_set_to_clipboard,
}

GET_SKIP_LIST = ["MOB_GetDeviceLocation","MOB_GetBatteryPercentage","MOB_GetLongitude","MOB_GetAltitude","MOB_GetLatitude",
"MOB_GetCurrentDeviceDate","MOB_GetMinuteFromCurrentDeviceTime","MOB_GetCurrentAppPackage","MOB_GetAllContexts",
"MOB_GetHourFromCurrentDeviceTime","MOB_GetSecondFromCurrentDeviceTime","MOB_GetSupportedPerformanceDataTypes",
"MOB_GetCurrentOrientation","MOB_GetCurrentDeviceTime","MOB_GetCurrentContext","MOB_GetCurrentDeviceSettings","GetCurrentSystemDay",
"MOB_GetClipBoardText","GetCurrentSystemMonth","MOB_GetCurrentDeviceStatus","MOB_GetSizeOfScreen","MOB_GetAllWindowHandles","MOB_GetWidthOfScreen",
"MOB_GetBatteryStatus","MOB_GetCurrentActivity","MOB_GetDeviceOsVersion","MOB_GetDeviceUdid","MOB_GetDeviceName","MOB_GetImplicitTimeOut",
"MOB_GetDriverInstance","MOB_GetCurrentWindowHandle","MOB_GetCurrentSessionId","MOB_GetHeightOfScreen","MOB_GetCurrentDeviceSystemBars"]

GET_EXECUTE_LIST =["MOB_GetAttributeValueFromListOfWebElements","MOB_GetTagName","MOB_GetListOfElementsFromLocatorTypeLocatorValue","MOB_GetScreenshot","MOB_GetTextFromElementAndSetToClipBoard",
"MOB_GetHeightOfElement","MOB_GetTextFromListOfWebElements","MOB_GetHexCodeForGivenXYCoordinatesOfImage","MOB_GetADBLogsForGivenAppPackage","MOB_GetScreenshotAs","MOB_GetWidthOfElement",
"MOB_GetX", "MOB_GetLocation","MOB_GetY","MOB_GetPerformanceData","MOB_GetRect","MOB_GetText","MOB_GetSize","MOB_GetAttribute"]

def execute_getAction(driver ,annotated_dom, simplified_dom, step,filtered_steps, serviceProvider, model, apiKey,service_accounts):
    attribute_type=""
    locator_type=""
    ff_num, nlp_name,input_text, keyword, element_type,locator_type,attribute_type, input_tokens,output_tokens,total_tokens = match_nlp_via_llm(simplified_dom, step, GET_NLP_STRING,filtered_steps, serviceProvider, model, apiKey,service_accounts)
    xpath_path=""
    if nlp_name in GET_SKIP_LIST:
        logger.info(f"Get result non-execution for {nlp_name}: {True}")
        return True, 0, nlp_name , input_text,keyword, xpath_path, element_type, locator_type,attribute_type,input_tokens,output_tokens,total_tokens
    
    if not nlp_name or nlp_name not in GET_EXECUTE_LIST:
        logger.info(f"No matching Execution NLP for step: {step} and nlp is {nlp_name}")
        return False, ff_num, nlp_name , input_text,keyword, xpath_path, element_type,locator_type,attribute_type, input_tokens,output_tokens,total_tokens

    try:
        tree = etree.fromstring(annotated_dom.encode('utf-8'))
        target = tree.xpath(f"//*[@FF-inspecter='Fire-Flink-{ff_num}']")
        element_xpath = target[0]
        xpath_path = etree.ElementTree(tree).getpath(element_xpath)
    except Exception as e:
        xpath_path = ""

    try:
        # xpath = f"//*[@FF-inspecter='Fire-Flink-{ff_num}']"

        element = driver.find_element(AppiumBy.XPATH,xpath_path)
        logger.info(xpath_path)

    except:
        element = None


    func = EXECUTE_GET_FUNCTIONS[nlp_name]
    if nlp_name in ["MOB_GetScreenshot","MOB_GetScreenshotAs"]:
        if input_text == "":
            input_text = "image"
        result,filename = func(driver, element,input_text)
    elif nlp_name == "MOB_GetAttributeValueFromListOfWebElements":
        result = func(driver, element,input_text,attribute_type)
    else:
        result = func(driver, element, input_text)

    logger.info(f"Get result for {nlp_name}: {result}")

    action = nlp_name

    return result,ff_num, action , input_text,keyword, xpath_path, element_type,locator_type,attribute_type, input_tokens,output_tokens,total_tokens
