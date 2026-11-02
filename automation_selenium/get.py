import json
from LLMcall import call_grok_llm
import re
from lxml import etree, html 
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
from pydantic import BaseModel, Field, ValidationError
from enum import Enum
import logging
import requests
import os
from dump import SHADOW_DOM_GET_TEXT_JS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding="utf-8")

class nlpName_enum(Enum):
    GetAllTheOptionsFromListBoxAsTextInSortedOrder = "GetAllTheOptionsFromListBoxAsTextInSortedOrder"
    GetScreenshot = "GetScreenshot"
    GetAllTheOptionsFromListBoxAsText = "GetAllTheOptionsFromListBoxAsText"
    GetTheFirstSelectedOptionFromListBoxAsText = "GetTheFirstSelectedOptionFromListBoxAsText"
    GetAllTheSelectedOptionsFromListBoxAsText = "GetAllTheSelectedOptionsFromListBoxAsText"
    GetAttribute = "GetAttribute"
    GetTagName = "GetTagName"
    GetListBoxSize = "GetListBoxSize"
    GetWrappedOptionFromListBoxAsText = "GetWrappedOptionFromListBoxAsText"
    GetTextFromListOfWebElements = "GetTextFromListOfWebElements"
    GetCssValue = "GetCssValue"
    GetScreenshotAs = "GetScreenshotAs"
    GetFirstSelectedOption = "GetFirstSelectedOption"
    GetText = "GetText"
    GetOptions = "GetOptions"
    GetAllSelectedOptions = "GetAllSelectedOptions"
    GetSize = "GetSize"
    GetWrappedElement = "GetWrappedElement"
    GetRect = "GetRect"
    GetYLocationOfWebElement = "GetYLocationOfWebElement"
    GetLocation = "GetLocation"
    GetVideoMediaSource = "GetVideoMediaSource"
    GetListOfElementsFromLocatorTypeLocatorValue = "GetListOfElementsFromLocatorTypeLocatorValue"
    GetXLocationOfWebElement = "GetXLocationOfWebElement"
    GetVideoCurrentSeekTime = "GetVideoCurrentSeekTime"
    GetVideoMediaLength = "GetVideoMediaLength"
    GetVideoDefaultPlaybackRate = "GetVideoDefaultPlaybackRate"
    GetVideoHeight = "GetVideoHeight"
    GetAudioCurrentPlaybackRate = "GetAudioCurrentPlaybackRate"
    GetAudioDecodedByte = "GetAudioDecodedByte"
    GetVideoCurrentPlaybackRate = "GetVideoCurrentPlaybackRate"
    GetVideoCurrentVolume = "GetVideoCurrentVolume"
    GetVideoDimension = "GetVideoDimension"
    GetAudioDefaultPlaybackRate = "GetAudioDefaultPlaybackRate"
    GetVideoWidth = "GetVideoWidth"
    GetSingleApiStatusCode = "GetSingleApiStatusCode"
    GetSingleApiResponseTime = "GetSingleApiResponseTime"
    GetAudioCurrentVolume = "GetAudioCurrentVolume"
    GetSingleApiResponse = "GetSingleApiResponse"
    GetCollectiveApiStatusCode = "GetCollectiveApiStatusCode"
    GetVideoDecodedByte = "GetVideoDecodedByte"
    GetDataFromApiResponseForJsonPath = "GetDataFromApiResponseForJsonPath"
    GetAudioMediaSource = "GetAudioMediaSource"
    GetCollectiveApiResponseTime = "GetCollectiveApiResponseTime"
    GetStatusCodeOfALink = "GetStatusCodeOfALink"
    GetValueFromLocalStorage = "GetValueFromLocalStorage"
    GetHeightOfWebElement = "GetHeightOfWebElement"
    GetTunnelIdentifier = "GetTunnelIdentifier"
    GetWidthOfWebElement = "GetWidthOfWebElement"
    GetValueByCookieName = "GetValueByCookieName"
    GetAudioHeight = "GetAudioHeight"
    GetHexCodeForGivenXYCoordinatesOfImage = "GetHexCodeForGivenXYCoordinatesOfImage"
    GetAudioCurrentSeekTime = "GetAudioCurrentSeekTime"
    GetAudioWidth = "GetAudioWidth"
    GetAudioMediaLength = "GetAudioMediaLength"
    GetAudioDimension = "GetAudioDimension"
    ScrollPageToSpecificLocation = "ScrollPageToSpecificLocation"
    GetDateWithGivenFormat = "GetDateWithGivenFormat"
    GetBestPracticesScore = "GetBestPracticesScore"
    GetPwaScore = "GetPwaScore"
    GetDataFromApiRequestHeaderForJsonPath = "GetDataFromApiRequestHeaderForJsonPath"
    GetSeoScore = "GetSeoScore"
    GetValueOfSystemVariable = "GetValueOfSystemVariable"
    GetStringDataFromLocalFile = "GetStringDataFromLocalFile"
    GetAccessibilityScore = "GetAccessibilityScore"
    GetPerformanceScore = "GetPerformanceScore"
    GetSystemProperty = "GetSystemProperty"
    GetValueFromXmlPath = "GetValueFromXmlPath"
    RobotGetXLocationOfWebElement = "RobotGetXLocationOfWebElement"
    RobotGetYLocationOfWebElement = "RobotGetYLocationOfWebElement"
    GetSingleApiRequestPayload = "GetSingleApiRequestPayload"
    GetAllBrokenLinks = "GetAllBrokenLinks"
    GetHeightOfBrowserWindow = "GetHeightOfBrowserWindow"
    GetXLocationOfBrowserWindow = "GetXLocationOfBrowserWindow"
    GetAllBrokenLinkCount = "GetAllBrokenLinkCount"
    GetWidthOfBrowser = "GetWidthOfBrowser"
    GetCurrentWindowHandle = "GetCurrentWindowHandle"
    GetAllWindowHandles = "GetAllWindowHandles"
    GetURLPresentInAddressBar = "GetURLPresentInAddressBar"
    GetHTMLCodeOfPage = "GetHTMLCodeOfPage"
    GetPageTitle = "GetPageTitle"
    GetBrowserCount = "GetBrowserCount"
    GetBrowserVersion = "GetBrowserVersion"
    GetImplicitTimeOut = "GetImplicitTimeOut"
    GetCapabilityNames = "GetCapabilityNames"
    GetYLocationOfBrowserWindow = "GetYLocationOfBrowserWindow"
    GetCurrentSystemDate = "GetCurrentSystemDate"
    GetCurrentDayOfTheWeek = "GetCurrentDayOfTheWeek"
    GetCurrentSystemTime = "GetCurrentSystemTime"
    GetCurrentSecondsFromCurrentSystemTime = "GetCurrentSecondsFromCurrentSystemTime"
    GetCurrentSystemYear = "GetCurrentSystemYear"
    GetHourFromCurrentSystemTime = "GetHourFromCurrentSystemTime"
    GetMinuteFromCurrentSystemTime = "GetMinuteFromCurrentSystemTime"
    GetNumberOfLinksPresentInCurrentPage = "GetNumberOfLinksPresentInCurrentPage"
    GetAllConsoleWarnings = "GetAllConsoleWarnings"
    GetAllConsoleInformation = "GetAllConsoleInformation"
    GetAllConsoleErrors = "GetAllConsoleErrors"
    GetAllCookieValues = "GetAllCookieValues"
    GetSizeOfBrowserWindow = "GetSizeOfBrowserWindow"
    GetCurrentSystemMonth = "GetCurrentSystemMonth"
    GetCurrentSystemDay = "GetCurrentSystemDay"
    GetAllConsoleLogs = "GetAllConsoleLogs"
    GetTotalNumberOfCookies = "GetTotalNumberOfCookies"
    GetAllBrokenImages = "GetAllBrokenImages"
    GetAllCookieNames = "GetAllCookieNames"
    GetNumberOfWorkingLinksFromCurrentPage = "GetNumberOfWorkingLinksFromCurrentPage"
    GetNumberOfBrokenImages = "GetNumberOfBrokenImages"
    GetWorkingLinksFromCurrentPage = "GetWorkingLinksFromCurrentPage"
    BrowserWindowGetPosition = "BrowserWindowGetPosition"
    GetClipBoardText = "GetClipBoardText"
    GetDriverInstance = "GetDriverInstance"
    GetFullPaintTime = "GetFullPaintTime"
    GetFirstContentfulPaint = "GetFirstContentfulPaint"
    GetLargestContentfulPaint = "GetLargestContentfulPaint"
    GetNetworkRouteTime = "GetNetworkRouteTime"
    GetPerformanceMetrics = "GetPerformanceMetrics"
    GetUserHomeDirectory = "GetUserHomeDirectory"

class FFInspecterResponse(BaseModel):
    attribute_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element.",
        examples=["Fire-Flink-x"]
    )

    nlpName: nlpName_enum = Field(..., description="The selected NLP name.", examples=["x"])
    
    element_type: str = Field(
        ...,
        description="The type of element.",
        examples=["x"]
    )
    input_text: str = Field(
        "",
        description="Input text extracted from the step.",
        examples=["x"]
    )

    keyword: str = Field(
        "",
        description="element keyword or field name identified from the step.",
        examples=["x", "x"]
    )
GET_NLP = ["GetAllTheOptionsFromListBoxAsTextInSortedOrder", "GetScreenshot", "GetAllTheOptionsFromListBoxAsText", "GetTheFirstSelectedOptionFromListBoxAsText", "GetAllTheSelectedOptionsFromListBoxAsText", "GetAttribute", "GetTagName", "GetListBoxSize",
 "GetWrappedOptionFromListBoxAsText", "GetTextFromListOfWebElements", "GetCssValue", "GetScreenshotAs", "GetFirstSelectedOption", "GetText", "GetOptions", "GetAllSelectedOptions", "GetSize", "GetWrappedElement", "GetRect", "GetLocation", 
 "GetXLocationOfWebElement", "GetYLocationOfWebElement", "GetVideoMediaSource", "GetListOfElementsFromLocatorTypeLocatorValue",  "GetVideoCurrentSeekTime", "GetVideoMediaLength", "GetVideoDefaultPlaybackRate", "GetVideoHeight", "GetAudioCurrentPlaybackRate", 
 "GetAudioDecodedByte", "GetVideoCurrentPlaybackRate", "GetVideoCurrentVolume", "GetVideoDimension", "GetAudioDefaultPlaybackRate", "GetVideoWidth", "GetSingleApiStatusCode", "GetSingleApiResponseTime", "GetAudioCurrentVolume", "GetSingleApiResponse", 
 "GetCollectiveApiStatusCode", "GetVideoDecodedByte", "GetDataFromApiResponseForJsonPath", "GetAudioMediaSource", "GetCollectiveApiResponseTime", "GetStatusCodeOfALink", "GetValueFromLocalStorage", "GetHeightOfWebElement", "GetTunnelIdentifier", 
 "GetWidthOfWebElement", "GetValueByCookieName", "GetAudioHeight", "GetHexCodeForGivenXYCoordinatesOfImage", "GetAudioCurrentSeekTime", "GetAudioWidth", "GetAudioMediaLength", "GetAudioDimension", "ScrollPageToSpecificLocation", "GetDateWithGivenFormat", 

 "GetBestPracticesScore", "GetPwaScore", "GetDataFromApiRequestHeaderForJsonPath", "GetSeoScore", "GetValueOfSystemVariable", "GetStringDataFromLocalFile", "GetAccessibilityScore", "GetPerformanceScore", "GetSystemProperty", "GetValueFromXmlPath", 
 "RobotGetXLocationOfWebElement", "RobotGetYLocationOfWebElement", "GetSingleApiRequestPayload","GetAllBrokenLinks", "GetHeightOfBrowserWindow", "GetXLocationOfBrowserWindow", "GetAllBrokenLinkCount", "GetWidthOfBrowser", "GetCurrentWindowHandle", 
 "GetAllWindowHandles", "GetURLPresentInAddressBar", "GetHTMLCodeOfPage", "GetPageTitle", "GetBrowserCount", "GetBrowserVersion", "GetImplicitTimeOut", "GetCapabilityNames", "GetYLocationOfBrowserWindow", "GetCurrentSystemDate", 
 "GetCurrentDayOfTheWeek", "GetCurrentSystemTime", "GetCurrentSecondsFromCurrentSystemTime", "GetCurrentSystemYear", "GetHourFromCurrentSystemTime", "GetMinuteFromCurrentSystemTime", "GetNumberOfLinksPresentInCurrentPage", "GetAllConsoleWarnings", 
 "GetAllConsoleInformation", "GetAllConsoleErrors", "GetAllCookieValues", "GetSizeOfBrowserWindow", "GetCurrentSystemMonth", "GetCurrentSystemDay", "GetAllConsoleLogs", "GetTotalNumberOfCookies", "GetAllBrokenImages", "GetAllCookieNames", 
 "GetNumberOfWorkingLinksFromCurrentPage", "GetNumberOfBrokenImages", "GetWorkingLinksFromCurrentPage", "BrowserWindowGetPosition", "GetClipBoardText", "GetDriverInstance", "GetFullPaintTime", "GetFirstContentfulPaint", "GetLargestContentfulPaint", 
 "GetNetworkRouteTime", "GetPerformanceMetrics", "GetUserHomeDirectory"]

def match_get_nlp_via_llm(simplified_dom, step, nlp_list, filtered_steps, serviceProvider, model, apiKey,service_accounts):
    element_type = ['link','textfield','icon','button','radioButton','text','textarea','image','dropdown','checkbox','tab','action overflow button','hamburger icon','toggle button','suggestion','time picker','date picker','toaster message','card','tooltip','option','calender','sliders','visual testing']
    prompt = f"""
You are an intelligent assistant that extracts structured UI action data for fetching (GET) information.
Given the step: "{step}", the simplified DOM: {json.dumps(simplified_dom, ensure_ascii=False)}, and the list of NLP names: {GET_NLP}.

Select the perfect matching NLP name from the list that best fits the step's intent.
**The NLP name must match exactly one value from the approved NLP list. Do not generate or suggest any new NLP names under any condition.**

{{
  "attribute_value": "Fire-Flink-x",
  "nlpName": "x",
  "input_text":"x"
  "keyword": "x"
  "element_type": "x"
}}
Rules:
- nlpName must be exactly one from the provided list.
- Use context from the steps : {filtered_steps}, keyword and json to search for FF-inspecter.
- **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
- For some steps you can see two inputs but you need to understand step and send the required input_text. input_text can be string, number, url or xpath.
        ex: get the flights matches the flight, Get Single Api Response of url- 'https://app.talentscan.ai/login' and request url-'https://app.talentscan.ai/sign up', if they give x-30,y-50 just send 30,50 and for this nlps GetDataFromApiRequestHeaderForJsonPath and Get Data From Api Response of url- 'https://app.talentscan.ai/login' and request url-'https://app.talentscan.ai/sign up' For JsonPath - c:jsonpath format than fill input_text in this order "https://app.talentscan.ai/login,https://app.talentscan.ai/sign up,c:jsonpath"
        here keyword : "flights" , input : "flight", here input:"https://app.talentscan.ai/login,https://app.talentscan.ai/sign up" first input is url and second input is request url 
- If step is about getting text from list of web elements from locator type locator value then always follow this format first type next value input_text: "locator_type, locator_value". if they didn't give locator type then based on locator value find locator type.
and also If a step is about getting value from element or some kind of locator type then provide the input in the format input_text: "locator_type, locator_value".
- If step is about getting attribute value then map to attribute nlps and input_text: "attribute_name".
- if step is about tag name then input_text: "tag name". and if step is about getting tag name and with count then input_text: "tag name,count".
- if step is about getting screenshot of element then than map to GetScreenshotAs.
- If step is mapted to GetTunnelIdentifier nlp than input_text must have 4 values separated by comma.first will be datacenter second will be username third will be access key and fourth will be tunnel id. they must follow this order. if they miss any value than return all values except that value.
- If a step refers to location, use X-location or Y-location NLP only when X or Y is explicitly mentioned; otherwise, use the general location NLP.
- if step is about getting options than map to option nlps.
- for nlp GetBestPracticesScore,GetPwaScore and GetSeoScore input_text must have 2 values separated by comma.first will be url second will be device type. they must follow this order. if they miss any value than return all values except that value.
- If no explicit option is mentioned in the step, map it to the most relevant non-option getting NLP based on the intent of the step.
- Extract input_text from the step that is which is being getting in the {step}, if you can't find any input text in the step, return keyword as input_text.
- Extract keyword from the step, if the step contains any keyword.
- Use the closest semantic match for the {step}; return attribute_value as Fire-Flink-0, only if nothing is found.
- Based on step give most relevant type of element. use this list to choose element_type: {element_type} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
- **Respond with valid JSON only. don't return any other text* or or don't return response in list format*.
"""
    try:
        # Call Groq LLM using your wrapper
        response_text = call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts)
        # logger.info("[JSON Verification Extraction Success]:\n%s", response_text)

        # Parse JSON safely
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try cleaning or fallback extraction
            cleaned = response_text.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
        # logger.info("[JSON Get Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))
        log_data = {k: v for k, v in data.items() if k != "attribute_value"}

        logger.info(
            "[JSON Get Extraction Success]:\n%s",
            json.dumps(log_data, indent=2, ensure_ascii=False)
        )
        # Validate with Pydantic model
        validated = FFInspecterResponse(**data)

        ff_num = validated.attribute_value.split("-")[-1]
        nlpName = validated.nlpName.value
        input_text = validated.input_text
        keyword = validated.keyword
        element_type = validated.element_type
        
        return ff_num, nlpName, input_text, keyword, element_type
    except Exception as e:
        logger.error(f"Error in match_get_nlp_via_llm: {e}")
        raise e

# --- EXECUTION FUNCTIONS ---

def execute_get_all_the_options_from_list_box_as_text_in_sorted_order(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_all_the_options_from_list_box_as_text_in_sorted_order: {e}")
        return False

def execute_get_screenshot(driver, element, input_val, xpath_js):
    try:
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_screenshot: {e}")
        return False

def execute_get_all_the_options_from_list_box_as_text(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_all_the_options_from_list_box_as_text: {e}")
        return False

def execute_get_the_first_selected_option_from_list_box_as_text(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_the_first_selected_option_from_list_box_as_text : {e}")
        return False

def execute_get_all_the_selected_options_from_list_box_as_text(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_all_the_selected_options_from_list_box_as_text : {e}")
        return False

def execute_get_attribute(driver, element, input_val, xpath_js):
    try:
        if not element or not input_val: return False
        try:
            attr_value = element.get_attribute(input_val)
        except:
            attr_value = element.text
        # logger.info(f"Attribute value: {attr_value}")
        if attr_value: 
            return True
        return False
    except Exception as e:
        logger.error(f"Error in execute_get_attribute: {e}")
        return False

def execute_get_tag_name(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        tag_name = element.tag_name
        logger.info(f"Tag name: {tag_name}")
        if tag_name:
            return True
        return False
    except Exception as e:
        logger.error(f"Error in execute_get_tag_name: {e}")
        return False

def execute_get_list_box_size(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_list_box_size: {e}")
        return False

def execute_get_wrapped_option_from_list_box_as_text(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_wrapped_option_from_list_box_as_text: {e}")
        return False

def execute_get_text_from_list_of_web_elements(driver, element, input_val, xpath_js):
    try:
        if not input_val: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_text_from_list_of_web_elements: {e}")
        return False

def execute_get_css_value(driver, element, input_val, xpath_js):
    try:
        if not element or not input_val: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_css_value: {e}")
        return False

def execute_get_screenshot_as(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_screenshot_as: {e}")
        return False

def execute_get_first_selected_option(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_first_selected_option: {e}")
        return False

def execute_get_text(driver, element, input_val, xpath_js):
    try:
        if "shadow" in xpath_js:
            text = driver.execute_script(SHADOW_DOM_GET_TEXT_JS, xpath_js)
            if text:
                logger.info(f"Text: {text}")
                return True
            return False
        elif not element: return False
    except Exception as e:
        logger.error(f"Error in execute_get_text: {e}")
        return False

def execute_get_options(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_options: {e}")
        return False
    

def execute_get_all_selected_options(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        if element.tag_name.lower() != "select": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_all_selected_options: {e}")
        return False

def execute_get_size(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_size: {e}")
        return False

def execute_get_wrapped_element(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_wrapped_element: {e}")
        return False

def execute_get_rect(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_rect: {e}")
        return False

def execute_get_y_location_of_web_element(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_y_location_of_web_element: {e}")
        return False

def execute_get_location(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_location: {e}")
        return False

def execute_get_video_media_source(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_media_source: {e}")
        return False


def execute_get_list_of_elements_from_locator_type_locator_value(driver, element, input_val, xpath_js):
    try:
        if not input_val or not element: return False

        return True
    except Exception as e:
        logger.error(f"Error in execute_get_list_of_elements_from_locator_type_locator_value: {e}")
        return False

def execute_get_x_location_of_web_element(driver, element, input_val, xpath_js):
    try:
        if not element: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_x_location_of_web_element: {e}")
        return False

def execute_get_video_current_seek_time(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_media_source: {e}")
        return False
def execute_get_video_media_length(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_media_source: {e}")
        return False
def execute_get_video_default_playback_rate(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_media_source: {e}")
        return False
def execute_get_video_height(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_media_source: {e}")
        return False

def execute_get_audio_current_playback_rate(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_current_playback_rate: {e}")
        return False

def execute_get_audio_decoded_byte(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_decoded_byte: {e}")
        return False

def execute_get_video_current_playback_rate(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_current_playback_rate: {e}")
        return False

def execute_get_video_current_volume(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_current_volume: {e}")
        return False

def execute_get_video_dimension(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_dimension: {e}")
        return False

def execute_get_audio_default_playback_rate(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_default_playback_rate: {e}")
        return False

def execute_get_video_width(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_width: {e}")
        return False

def execute_get_single_api_status_code(driver, element, input_val, xpath_js):
    return requests.get(input_val).status_code if input_val else "null"

def execute_get_single_api_response_time(driver, element, input_val, xpath_js):
    try:
        if not input_val: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_single_api_response_time: {e}")
        return False

def execute_get_audio_current_volume(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_current_volume: {e}")
        return False

def execute_get_single_api_response(driver, element, input_val, xpath_js):
    try:
        if not input_val: return False
        input_val = input_val.split(",")
        if len(input_val) != 2: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_single_api_response: {e}")
        return False

def execute_get_collective_api_status_code(driver, element, input_val, xpath_js):
    try:
        if not input_val : return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_collective_api_status_code: {e}")
        return False
def execute_get_video_decoded_byte(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <video> tag
        if element.tag_name.lower() == "video":
            return True

        # 2. <source> inside <video>
        parent = driver.execute_script("return arguments[0].closest('video');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_video_media_source: {e}")
        return False

def execute_get_data_from_api_response_for_json_path(driver, element, input_val, xpath_js):
    try:
        if not input_val or "," not in input_val: return False
        input_val = input_val.split(",")
        if len(input_val) != 3: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_data_from_api_response_for_json_path: {e}")
        return False

def execute_get_audio_media_source(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_media_source: {e}")
        return False

def execute_get_collective_api_response_time(driver, element, input_val, xpath_js):
    if not isinstance(input_val,list): return "null"
    res=[]
    for u in input_val:
        s=time.time(); requests.get(u); res.append(time.time()-s)
    return res

def execute_get_status_code_of_a_link(driver, element, input_val, xpath_js):
    try: return requests.head(input_val,timeout=5).status_code
    except: return "error"

def execute_get_value_from_local_storage(driver, element, input_val, xpath_js):
    return driver.execute_script(f"return localStorage.getItem('{input_val}')")

def execute_get_height_of_web_element(driver, element, input_val, xpath_js):
    return element.size["height"] if element else "null"

def execute_get_width_of_web_element(driver, element, input_val, xpath_js):
    return element.size["width"] if element else "null"

def execute_get_value_by_cookie_name(driver, element, input_val, xpath_js):
    c=driver.get_cookie(input_val)
    return c["value"] if c else "null"

def execute_get_audio_height(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_height: {e}")
        return False

def execute_get_audio_current_seek_time(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_current_seek_time: {e}")
        return False

def execute_get_audio_width(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_width: {e}")
        return False

def execute_get_audio_media_length(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_media_length: {e}")
        return False

def execute_get_audio_dimension(driver, element, input_val, xpath_js):
    try:
        if not element:
            return False

        # 1. Direct <audio> tag
        if element.tag_name.lower() == "audio":
            return True

        # 2. <source> inside <audio>
        parent = driver.execute_script("return arguments[0].closest('audio');", element)
        if parent:
            return True

        return False

    except Exception as e:
        logger.error(f"Error in execute_get_audio_dimension: {e}")
        return False

def execute_scroll_page_to_specific_location(driver, element, input_val, xpath_js):
    if not input_val or "," not in input_val: return "error"
    x,y=input_val.split(",")
    driver.execute_script(f"window.scrollTo({x},{y})")
    return "done"

def execute_get_date_with_given_format(driver, element, input_val, xpath_js):
    return time.strftime(input_val)

def execute_get_value_of_system_variable(driver, element, input_val, xpath_js):
    try:
        if not input_val: return False
        result = os.environ.get(input_val,"null")
        # logger.info(f"Result: {result}")
        if result == "null": return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_value_of_system_variable: {e}")
        return False

def execute_get_string_data_from_local_file(driver, element, input_val, xpath_js):
    try:
        if not input_val or not os.path.exists(input_val): return False
        # with open(input_val,"r",encoding="utf-8") as f: return f.read()
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_string_data_from_local_file: {e}")
        return False

def execute_get_system_property(driver, element, input_val, xpath_js):
    return os.getenv(input_val,"null")

def execute_get_single_api_request_payload(driver, element, input_val, xpath_js):
    try:
        if not input_val or "," not in input_val: return False
        input_val=input_val.split(",")
        if len(input_val)!=2: return False
        
        return True
    except:
        return False
def execute_get_tunnel_identifier(driver, element, input_val, xpath_js):
    try:
        if not input_val: return False
        input_val = input_val.split(",")
        # logger.info(f"Input length: {len(input_val)}")
        if len(input_val) != 4: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_tunnel_identifier: {e}")
        return False 
        
def execute_get_best_practices_score(driver, element, input_val, xpath_js):
    try:
        if not input_val: return False
        input_val = input_val.split(",")
        if len(input_val) != 2: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_best_practices_score: {e}")
        return False

def execute_get_pwa_score(driver, element, input_val, xpath_js):
    try:
        if not input_val: return False
        input_val = input_val.split(",")
        if len(input_val) != 2: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_pwa_score: {e}")
        return False

def execute_get_seo_score(driver, element, input_val, xpath_js):
    try:
        if not input_val: return False
        input_val = input_val.split(",")
        if len(input_val) != 2: return False
        return True
    except Exception as e:
        logger.error(f"Error in execute_get_pwa_score: {e}")
        return False


EXECUTE_GET_FUNCTIONS = {
    "GetText": execute_get_text,
    "GetAttribute": execute_get_attribute,
    "GetTagName": execute_get_tag_name,
    "GetCssValue": execute_get_css_value,
    "GetSize": execute_get_size,
    "GetRect": execute_get_rect,
    "GetLocation": execute_get_location,
    "GetXLocationOfWebElement": execute_get_x_location_of_web_element,
    "GetYLocationOfWebElement": execute_get_y_location_of_web_element,
    "GetWidthOfWebElement": execute_get_width_of_web_element,
    "GetHeightOfWebElement": execute_get_height_of_web_element,
    "GetWrappedElement": execute_get_wrapped_element,

    "GetTextFromListOfWebElements": execute_get_text_from_list_of_web_elements,

    "GetOptions": execute_get_options,
    "GetFirstSelectedOption": execute_get_first_selected_option,
    "GetAllSelectedOptions": execute_get_all_selected_options,
    "GetListBoxSize": execute_get_list_box_size,

    "GetAllTheOptionsFromListBoxAsText": execute_get_all_the_options_from_list_box_as_text,
    "GetAllTheOptionsFromListBoxAsTextInSortedOrder": execute_get_all_the_options_from_list_box_as_text_in_sorted_order,
    "GetTheFirstSelectedOptionFromListBoxAsText": execute_get_the_first_selected_option_from_list_box_as_text,
    "GetAllTheSelectedOptionsFromListBoxAsText": execute_get_all_the_selected_options_from_list_box_as_text,
    "GetWrappedOptionFromListBoxAsText": execute_get_wrapped_option_from_list_box_as_text,

    "GetScreenshot": execute_get_screenshot,
    "GetScreenshotAs": execute_get_screenshot_as,

    "GetListOfElementsFromLocatorTypeLocatorValue": execute_get_list_of_elements_from_locator_type_locator_value,

    "GetVideoMediaSource": execute_get_video_media_source,
    "GetVideoMediaLength": execute_get_video_media_length,
    "GetVideoCurrentSeekTime": execute_get_video_current_seek_time,
    "GetVideoCurrentPlaybackRate": execute_get_video_current_playback_rate,
    "GetVideoDefaultPlaybackRate": execute_get_video_default_playback_rate,
    "GetVideoCurrentVolume": execute_get_video_current_volume,
    "GetVideoWidth": execute_get_video_width,
    "GetVideoHeight": execute_get_video_height,
    "GetVideoDimension": execute_get_video_dimension,
    "GetVideoDecodedByte": execute_get_video_decoded_byte,

    "GetAudioMediaSource": execute_get_audio_media_source,
    "GetAudioMediaLength": execute_get_audio_media_length,
    "GetAudioCurrentSeekTime": execute_get_audio_current_seek_time,
    "GetAudioCurrentPlaybackRate": execute_get_audio_current_playback_rate,
    "GetAudioDefaultPlaybackRate": execute_get_audio_default_playback_rate,
    "GetAudioCurrentVolume": execute_get_audio_current_volume,
    "GetAudioWidth": execute_get_audio_width,
    "GetAudioHeight": execute_get_audio_height,
    "GetAudioDimension": execute_get_audio_dimension,
    "GetAudioDecodedByte": execute_get_audio_decoded_byte,

    "GetSingleApiStatusCode": execute_get_single_api_status_code,
    "GetSingleApiResponse": execute_get_single_api_response,
    "GetSingleApiResponseTime": execute_get_single_api_response_time,
    "GetCollectiveApiStatusCode": execute_get_collective_api_status_code,
    "GetCollectiveApiResponseTime": execute_get_collective_api_response_time,
    "GetDataFromApiResponseForJsonPath": execute_get_data_from_api_response_for_json_path,
    "GetSingleApiRequestPayload": execute_get_single_api_request_payload,

    "GetValueFromLocalStorage": execute_get_value_from_local_storage,
    "GetValueByCookieName": execute_get_value_by_cookie_name,
    "GetValueOfSystemVariable": execute_get_value_of_system_variable,
    "GetSystemProperty": execute_get_system_property,
    "GetStringDataFromLocalFile": execute_get_string_data_from_local_file,

    "ScrollPageToSpecificLocation": execute_scroll_page_to_specific_location,
    "GetDateWithGivenFormat": execute_get_date_with_given_format,
    "GetTunnelIdentifier": execute_get_tunnel_identifier,
    "GetBestPracticesScore": execute_get_best_practices_score,
    "GetPwaScore": execute_get_pwa_score,
    "GetDataFromApiRequestHeaderForJsonPath": execute_get_data_from_api_response_for_json_path,
    "GetSeoScore": execute_get_seo_score,
}

GET_SKIP_LIST=["GetAllBrokenLinks", "GetHeightOfBrowserWindow", "GetXLocationOfBrowserWindow", "GetAllBrokenLinkCount", "GetWidthOfBrowser", "GetCurrentWindowHandle", "GetAllWindowHandles", "GetURLPresentInAddressBar", 
"GetHTMLCodeOfPage", "GetPageTitle", "GetBrowserCount", "GetBrowserVersion", "GetImplicitTimeOut", "GetCapabilityNames", "GetYLocationOfBrowserWindow", "GetCurrentSystemDate", "GetCurrentDayOfTheWeek", 
"GetCurrentSystemTime", "GetCurrentSecondsFromCurrentSystemTime", "GetCurrentSystemYear", "GetHourFromCurrentSystemTime", "GetMinuteFromCurrentSystemTime", "GetNumberOfLinksPresentInCurrentPage", "GetAllConsoleWarnings", 
"GetAllConsoleInformation", "GetAllConsoleErrors", "GetAllCookieValues", "GetSizeOfBrowserWindow", "GetCurrentSystemMonth", "GetCurrentSystemDay", "GetAllConsoleLogs", "GetTotalNumberOfCookies", "GetAllBrokenImages", 
"GetAllCookieNames", "GetNumberOfWorkingLinksFromCurrentPage", "GetNumberOfBrokenImages", "GetWorkingLinksFromCurrentPage", "BrowserWindowGetPosition", "GetClipBoardText", "GetDriverInstance", "GetFullPaintTime", 
"GetFirstContentfulPaint", "GetLargestContentfulPaint", "GetNetworkRouteTime", "GetPerformanceMetrics", "GetUserHomeDirectory"]

def execute_get(driver, annotated_dom, simplified_dom, step,element_name, test_steps,server_host, serviceProvider, model, apiKey,service_accounts, auto_healing=None):
    from agent import WebStepExecutor
    webstepexecutor = WebStepExecutor(driver)
    if auto_healing is None:
        from auto_healing import AutoHealing
        auto_healing = AutoHealing()
    
    nlp_list = [n.value for n in nlpName_enum]
    ff_num, nlp_name, input_text, keyword, element_type = match_get_nlp_via_llm(
        simplified_dom, step, nlp_list, test_steps, serviceProvider, model, apiKey,service_accounts
    )
    
    xpath_path = ""
    xpath_js = ""
    element = None
    iframe = [False,""]
    if ff_num in [0,"0"] :
        logger.info(f"element not found for : {step}")
        # return False, ff_num, nlp_name, keyword, input_text, "", "", element_type, i_tok, o_tok, t_tok
    
    if nlp_name in GET_SKIP_LIST:
        logger.info(f"Get result non-execution for {nlp_name}: {True}")
        return True, ff_num, nlp_name, keyword, element_type, input_text, "", "", iframe
    
    if nlp_name == "None" or nlp_name not in EXECUTE_GET_FUNCTIONS:
        return False, ff_num, nlp_name, keyword, element_type, input_text, "", "", iframe

    try:
        if annotated_dom and ff_num and ff_num not in ["0", 0, "-1", -1]:
            tree = html.fromstring(annotated_dom)
            target = tree.xpath(f"//*[@ff-inspect='Fire-Flink-{ff_num}']")
            if target:
                xpath_path = target[0].attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(target[0])
                element, xpath_js, iframe = webstepexecutor._resolve_element(xpath_path, ff_num)
                logger.info(f"Xpath:{xpath_js}")
    except Exception as e:
        logger.error(f"Error resolving element: {e}")
        element = None
    if element:
        auto_healing.send_locator_request(annotated_dom, f"Fire-Flink-{ff_num}", element_name,server_host, source="primary")
    elif "shadow" in xpath_js:
        auto_healing.send_locator_request(annotated_dom, f"Fire-Flink-{ff_num}", element_name,server_host, source="primary")
    
    func = EXECUTE_GET_FUNCTIONS[nlp_name]
    result = func(driver, element, input_text,xpath_js)
    logger.info(f"[GET] Result for {nlp_name}: {result}")

    if nlp_name in ["GetScreenshot", "GetScreenshotAs"]:
        if input_text:
            input_text = f"ss_{input_text}.png"
        else:
            input_text = f"ss_{int(time.time())}.png"
    elif "shadow" in xpath_js:
        nlp_name = "ExecuteJavaScript"
        input_text = SHADOW_DOM_GET_TEXT_JS.replace("const path = arguments[0];", f'const path = "{xpath_js}";')
    

    return result, ff_num, nlp_name, keyword, element_type, input_text, xpath_path, xpath_js, iframe
