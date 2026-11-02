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
from dump import SHADOW_DOM_VERIFY_TEXT_JS,SHADOW_DOM_VERIFY_PARTIAL_TEXT_JS
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding="utf-8")

class nlpName_enum(Enum):
    VerifyIfOptionWithIndexIsSelectedInListBox = "VerifyIfOptionWithIndexIsSelectedInListBox"
    VerifyWidthOfElement = "VerifyWidthOfElement"
    VerifyBrowserWindowXLocation = "VerifyBrowserWindowXLocation"
    VerifyIfCookieNameIsDeleted = "VerifyIfCookieNameIsDeleted"
    VerifyBrowserWindowWidth = "VerifyBrowserWindowWidth"
    VerifyValueOfElementIsCleared = "VerifyValueOfElementIsCleared"
    VerifyTagName = "VerifyTagName"
    VerifyIfCookieNameIsAdded = "VerifyIfCookieNameIsAdded"
    VerifyLinkNavigatesToTitle = "VerifyLinkNavigatesToTitle"
    VerifyXLocationOfElement = "VerifyXLocationOfElement"
    VerifyAllOptionsAreDeselected = "VerifyAllOptionsAreDeselected"
    VerifyBrowserHtmlCodeContainsString = "VerifyBrowserHtmlCodeContainsString"
    VerifyBrowserWindowYLocation = "VerifyBrowserWindowYLocation"
    VerifyNumberOfElementsByTagName = "VerifyNumberOfElementsByTagName"
    VerifyListBoxOptionsAreSorted = "VerifyListBoxOptionsAreSorted"
    VerifyNavigateURL = "VerifyNavigateURL"
    VerifyHeightOfWebElement = "VerifyHeightOfWebElement"
    VerifyValueOfElementContainsString = "VerifyValueOfElementContainsString"
    VerifyBrowserWindowHeight = "VerifyBrowserWindowHeight"
    VerifyIfLinkIsBroken = "VerifyIfLinkIsBroken"
    VerifyValueOfElementIsString = "VerifyValueOfElementIsString"
    VerifyYLocationOfElement = "VerifyYLocationOfElement"
    VerifyNumberOfElementsByXpath = "VerifyNumberOfElementsByXpath"
    VerifyIfOptionWithIndexIsDeselectedInElement = "VerifyIfOptionWithIndexIsDeselectedInElement"
    VerifyAttributeValue = "VerifyAttributeValue"
    VerifyElementIsDisplayed = "VerifyElementIsDisplayed"
    VerifyAllOptionsAreSelected = "VerifyAllOptionsAreSelected"
    VerifyIfOptionWithValueIsDeselected = "VerifyIfOptionWithValueIsDeselected"
    VerifyTitleOfCurrentPage = "VerifyTitleOfCurrentPage"
    VerifyPartialTitleOfCurrentPage = "VerifyPartialTitleOfCurrentPage"
    VerifyElementIsNotDisplayed = "VerifyElementIsNotDisplayed"
    VerifyCssAttributeValue = "VerifyCssAttributeValue"
    VerifyPartialAttributeValue = "VerifyPartialAttributeValue"
    VerifyIfSpecifiedOptionIsSelected = "VerifyIfSpecifiedOptionIsSelected"
    VerifyTitleInAllPage = "VerifyTitleInAllPage"
    VerifyIfOptionWithValueIsSelected = "VerifyIfOptionWithValueIsSelected"
    VerifyIfVideoIsPlaying = "VerifyIfVideoIsPlaying"
    VerifyIfGivenOptionIsDuplicate = "VerifyIfGivenOptionIsDuplicate"
    VerifyRadioButtonIsSelected = "VerifyRadioButtonIsSelected"
    VerifyRadioButtonIsNotSelected = "VerifyRadioButtonIsNotSelected"
    VerifyThatSpecifiedOptionIsNotSelected = "VerifyThatSpecifiedOptionIsNotSelected"
    VerifyText = "VerifyText"
    VerifyPartialText = "VerifyPartialText"
    VerifyElementNotContainsText = "VerifyElementNotContainsText"
    VerifyElementIsClickable = "VerifyElementIsClickable"
    VerifyElementIsDisabled = "VerifyElementIsDisabled"
    VerifyElementIsEnabled = "VerifyElementIsEnabled"
    VerifyElementIsSelected = "VerifyElementIsSelected"
    VerifyCheckBoxIsSelected = "VerifyCheckBoxIsSelected"
    VerifyCheckBoxIsNotSelected = "VerifyCheckBoxIsNotSelected"
    VerifyUrlContainsExpectedUrl = "VerifyUrlContainsExpectedUrl"
    VerifyUrlIsString = "VerifyUrlIsString"
    VerifyBrowserWindowTitleContainsString = "VerifyBrowserWindowTitleContainsString"
    VerifyBrowserWindowTitleIsString = "VerifyBrowserWindowTitleIsString"
    VerifyIfBrowserWindowIsClosed = "VerifyIfBrowserWindowIsClosed"
    VerifyAllBrowserWindowsClosed = "VerifyAllBrowserWindowsClosed"
    VerifyIfAllCookiesAreDeleted = "VerifyIfAllCookiesAreDeleted"
    VerifyIfCookieObjectIsPresent = "VerifyIfCookieObjectIsPresent"
    VerifyIfXAndYCoordinateOfElement = "VerifyIfXAndYCoordinateOfElement"
    VerifyIfVideoIsMuted = "VerifyIfVideoIsMuted"
    VerifyIfVideoIsPaused = "VerifyIfVideoIsPaused"
    VerifyIfVideoEnded = "VerifyIfVideoEnded"
    VerifyIfVideoPlayingInMute = "VerifyIfVideoPlayingInMute"
    VerifyIfVideoPlayingInUnmute = "VerifyIfVideoPlayingInUnmute"
    VerifyIfAudioIsPlaying = "VerifyIfAudioIsPlaying"
    VerifyIfAudioIsPaused = "VerifyIfAudioIsPaused"
    VerifyIfAudioIsMuted = "VerifyIfAudioIsMuted"
    VerifyIfAudioEnded = "VerifyIfAudioEnded"
    VerifyIfLinkIsWorking = "VerifyIfLinkIsWorking"
    VerifyIfLinksAreWorking = "VerifyIfLinksAreWorking"
    VerifyIfLinksAreBroken = "VerifyIfLinksAreBroken"
    VerifyIfImageIsBroken = "VerifyIfImageIsBroken"
    VerifyAllBrokenImages = "VerifyAllBrokenImages"
    VerifyIfStatusCodeOfALinkIsStatusCode = "VerifyIfStatusCodeOfALinkIsStatusCode"
    VerifyIfStatusCodesOfLinks = "VerifyIfStatusCodesOfLinks"
    VerifyIfOptionWithVisibleTextIsSelected = "VerifyIfOptionWithVisibleTextIsSelected"
    VerifyIfOptionWithTextIsDeselected = "VerifyIfOptionWithTextIsDeselected"
    VerifyPerformanceScore = "VerifyPerformanceScore"
    VerifyAccessibilityScore = "VerifyAccessibilityScore"
    VerifyBestPracticesScore = "VerifyBestPracticesScore"
    VerifySeoScore = "VerifySeoScore"
    VerifyPwaScore = "VerifyPwaScore"
    VerifyHexCodeForGivenXYCoordinates = "VerifyHexCodeForGivenXYCoordinates"

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
        ...,
        description="Input text extracted from the step.",
        examples=["x"]
    )

    keyword: str = Field(
        ...,
        description="element keyword or field name identified from the step.",
        examples=["x", "x"]
    )
    

# Parse NLP list from the string
NLP_STRING = (
    "VerifyElementIsDisabled,VerifyElementIsEnabled,VerifyElementIsSelected,"
    "VerifyIfOptionWithIndexIsSelectedInListBox,VerifyWidthOfElement,VerifyBrowserWindowXLocation,"
    "VerifyIfCookieNameIsDeleted,VerifyBrowserWindowWidth,VerifyValueOfElementIsCleared,"
    "VerifyTagName,VerifyIfCookieNameIsAdded,VerifyLinkNavigatesToTitle,VerifyXLocationOfElement,"
    "VerifyAllOptionsAreDeselected,VerifyBrowserHtmlCodeContainsString,VerifyBrowserWindowYLocation,"
    "VerifyNumberOfElementsByTagName,VerifyListBoxOptionsAreSorted,VerifyNavigateURL,"
    "VerifyHeightOfWebElement,VerifyValueOfElementContainsString,VerifyBrowserWindowHeight,"
    "VerifyIfLinkIsBroken,VerifyValueOfElementIsString,VerifyYLocationOfElement,"
    "VerifyNumberOfElementsByXpath,VerifyIfOptionWithIndexIsDeselectedInElement,VerifyAttributeValue,"
    "VerifyElementIsDisplayed,VerifyAllOptionsAreSelected,VerifyIfOptionWithValueIsDeselected,"
    "VerifyTitleOfCurrentPage,VerifyPartialTitleOfCurrentPage,VerifyElementIsNotDisplayed,"
    "VerifyCssAttributeValue,VerifyPartialAttributeValue,VerifyIfSpecifiedOptionIsSelected,"
    "VerifyTitleInAllPage,VerifyIfOptionWithValueIsSelected,VerifyIfVideoIsPlaying,"
    "VerifyIfGivenOptionIsDuplicate,VerifyRadioButtonIsSelected,VerifyRadioButtonIsNotSelected,"
    "VerifyThatSpecifiedOptionIsNotSelected,"
    "VerifyText,VerifyPartialText,VerifyElementNotContainsText,VerifyElementIsClickable,"
    "VerifyCheckBoxIsSelected,VerifyCheckBoxIsNotSelected"
    "VerifyUrlContainsExpectedUrl,VerifyUrlIsString,"
    "VerifyBrowserWindowTitleContainsString,VerifyBrowserWindowTitleIsString,"
    "VerifyIfBrowserWindowIsClosed,VerifyAllBrowserWindowsClosed,"
    "VerifyIfAllCookiesAreDeleted,VerifyIfCookieObjectIsPresent,"
    "VerifyIfXAndYCoordinateOfElement,VerifyIfVideoIsMuted,VerifyIfVideoIsPaused,"
    "VerifyIfVideoEnded,VerifyIfVideoPlayingInMute,VerifyIfVideoPlayingInUnmute,"
    "VerifyIfAudioIsPlaying,VerifyIfAudioIsPaused,VerifyIfAudioIsMuted,VerifyIfAudioEnded,"
    "VerifyIfLinkIsWorking,VerifyIfLinksAreWorking,VerifyIfLinksAreBroken,"
    "VerifyIfImageIsBroken,VerifyAllBrokenImages,VerifyIfStatusCodeOfALinkIsStatusCode,"
    "VerifyIfStatusCodesOfLinks,VerifyIfOptionWithVisibleTextIsSelected,"
    "VerifyIfOptionWithTextIsDeselected,VerifyPerformanceScore,VerifyAccessibilityScore,"
    "VerifyBestPracticesScore,VerifySeoScore,VerifyPwaScore,VerifyHexCodeForGivenXYCoordinates"
)

NLP_LIST = NLP_STRING.split(",")

def match_nlp_via_llm(simplified_dom, step, nlp_list, filtered_steps, serviceProvider, model, apiKey,service_accounts):
    element_type = ['link','textfield','icon','button','radioButton','text','textarea','image','dropdown','checkbox','tab','action overflow button','hamburger icon','toggle button','suggestion','time picker','date picker','toaster message','card','tooltip','option','calender','sliders','visual testing']
    prompt = f"""
You are an intelligent assistant that extracts structured UI action data.
Given the step: "{step}", the simplified DOM: {json.dumps(simplified_dom, ensure_ascii=False)}, and the list of NLP names: {nlp_list}.

Select the perfect matching NLP name from the list that best fits the step's intent.
**The NLP name must match exactly one value from the approved NLP list. Do not generate or suggest any new NLP names under any condition.**
step may give any way u need to get most matching and related nlp name from the list.
example: verify if email element is present
nlp name should be VerifyElementIsDisplayed


{{
  "attribute_value": "Fire-Flink-x",
  "nlpName": "x",
  "input_text":"x"
  "keyword": "x",
  "element_type": "x"
}}

Rules:
- nlpName must be exactly one from the provided list.
- Use context from the steps : {filtered_steps}, keyword and json to search for FF-inspecter.
- **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
- For some steps you can see two inputs but you need to understand step and send the required input_text. input_text can be string, number, url or xpath.
        ex: Verify the flights matches the flight, Verify the home has 30 and 50 coordinates if they give x-30,y-50 just send 30,50 and verify hex code '#FFFFFF' for given (34,11) coordinates or they will give x-34,y-11 hexcode-#FFFFFF format than fill input_text in this order "#FFFFFF,34,11"
        here keyword : "flights" , input : "flight", here input:"30,50"  , here input:"#FFFFFF,34,11" 
- If step is about checking value of attribute then map to attribute nlps and input_text: "attribute_name,element_name" here attribute_name can be id,text,href etc not fire-flink-x. input_text should be in this format. 
and also If a step requires comparing two values, provide the input in the format input_text: "value1,value2".
- if step is about tag name then input_text: "tag name". and if step is about verifying tag name and with count then input_text: "tag name,count".
- if step is about verifying location then input_text: "coordinates".
- if step is about verifying options than map to option nlps.
- If a step involves a URL, map navigation/action keywords (navigate) to VerifyNavigateURL, partial match keywords (contains, includes) to VerifyUrlContainsExpectedUrl, exact match keywords (equals, is, exactly) to VerifyUrlIsString, default to exact match if unclear, and prioritize navigation if both intents exist.
- If no explicit option is mentioned in the step, map it to the most relevant non-option verification NLP based on the intent of the step.
- Extract input_text from the step that is which is being verified in the {step}, if you can't find any input text in the step, return keyword as input_text.
- Extract keyword from the step, if the step contains any keyword.
- Use the closest semantic match for the {step}; return attribute_value as Fire-Flink-0, only if nothing is found.
- Based on step give most relevant type of element. use this list to choose element_type: {element_type} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
- **Respond with valid JSON only. don't return any other text or don't return response in list format**
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
        # logger.info("[JSON Verification Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))
        log_data = {k: v for k, v in data.items() if k != "attribute_value"}

        logger.info(
            "[JSON Verification Extraction Success]:\n%s",
            json.dumps(log_data, indent=2, ensure_ascii=False)
        )
        # Validate with Pydantic model
        validated = FFInspecterResponse(**data)

        ff_num = validated.attribute_value.split("-")[-1]
        nlpName = validated.nlpName.value
        input_text = validated.input_text
        keyword = validated.keyword
        element_type = validated.element_type

        if nlpName == "VerifyUrlContainsExpectedUrl":
            nlpName = "VerifyBrowserWindowUrlContainsExpectedUrl"
        if nlpName == "VerifyUrlIsString":
            nlpName = "VerifyBrowserWindowUrlIsString"
     

        return ff_num, nlpName, input_text, keyword, element_type
    except ValidationError as e:
        logger.error(f"Pydantic Validation Error]: {e}")
        raise e
    except Exception as e:
        logger.error(f"[Error in match_nlp_via_llm]: {e}")
        raise e


# ---------------- VERIFICATION EXECUTION FUNCTIONS ---------------- #

def execute_verify_element_is_displayed(driver, element, input, xpath_js):
    """Verify element is displayed on the page"""
    try:
        if element and element.is_displayed():
            return True
        return False
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_element_is_not_displayed(driver, element, input, xpath_js):
    """Verify element is not displayed on the page"""
    try:
        if not element:
            return True
        return not element.is_displayed()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return True  # If element doesn't exist, it's not displayed

def execute_verify_attribute_value(driver, element, input, xpath_js):
    """Verify element attribute has exact value. Input format: 'attribute_name,expected_value,case_sensitive'"""
    try:
        if not input or not element:
            return False
        parts = str(input).split(",")
        if len(parts) < 2:
            return False
        
        attr_name = parts[0].strip()
        expected_value = parts[1].strip()
        # case_sensitive = parts[2].strip().lower() == "true" if len(parts) > 2 else False
        
        actual_value = element.get_attribute(attr_name) or element.text or ""
        
        # if case_sensitive:
        #     return actual_value == expected_value
        # else:
        #     return actual_value.lower() == expected_value.lower()
        logger.info("Actual value: %s, Expected value: %s", actual_value, expected_value)
        return actual_value.lower() == expected_value.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_partial_attribute_value(driver, element, input, xpath_js):
    """Verify element attribute contains value. Input format: 'attribute_name,expected_value,case_sensitive'"""
    try:
        if not input or not element:
            return False
        parts = str(input).split(",")
        if len(parts) < 2:
            return False
        
        attr_name = parts[0].strip()
        expected_value = parts[1].strip()
        # case_sensitive = parts[2].strip().lower() == "true" if len(parts) > 2 else False
        
        actual_value = element.get_attribute(attr_name) or element.text or ""
        
        # if case_sensitive:
        #     return expected_value in actual_value
        # else:
        #     return expected_value.lower() in actual_value.lower()

        return expected_value.lower() in actual_value.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_tag_name(driver, element, input, xpath_js):
    """Verify element tag name"""
    try:
        if not input or not element:
            return False
        expected_tag = str(input).strip().lower()
        actual_tag = element.tag_name.lower()
        return actual_tag == expected_tag
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_title_of_current_page(driver, element, input, xpath_js):
    """Verify page title exactly matches. Input format: 'expected_title,case_sensitive'"""
    try:
        if not input:
            return False
        expected_title = str(input).strip()
        actual_title = driver.title
        return actual_title == expected_title
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_partial_title_of_current_page(driver, element, input, xpath_js):
    """Verify page title contains text. Input format: 'expected_text,case_sensitive'"""
    try:
        if not input:
            return False
        expected_text = str(input).strip()
        actual_title = driver.title
        
        return expected_text.lower() in actual_title.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_navigate_url(driver, element, input, xpath_js):
    """Verify current URL matches"""
    try:
        if not input:
            return False
        expected_url = str(input).strip()
        actual_url = driver.current_url
        return actual_url == expected_url
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_value_of_element_is_string(driver, element, input, xpath_js):
    """Verify element value exactly matches. Input format: 'expected_value'"""
    try:
        if not input or not element:
            return False
        expected_value = input
        logger.info(f"Expected value: {expected_value}")

        actual_value = element.get_attribute("value") or element.text or ""
        logger.info(f"Actual value: {actual_value}")
        
        return actual_value.lower() == expected_value.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_value_of_element_contains_string(driver, element, input, xpath_js):
    """Verify element value contains text. Input format: 'expected_text,case_sensitive'"""
    try:
        if not input or not element:
            return False
        expected_text = input
        
        actual_value = element.get_attribute("value") or element.text or ""
        
        return expected_text.lower() in actual_value.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_value_of_element_is_cleared(driver, element, input, xpath_js):
    """Verify element value is empty"""
    try:
        if not element:
            return False
        actual_value = element.get_attribute("value") or ""
        return len(actual_value.strip()) == 0
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_x_location_of_element(driver, element, input, xpath_js):
    """Verify element X coordinate"""
    try:
        if not input or not element:
            return False
        expected_x = int(input)
        actual_x = element.location['x']
        # logger.info(f"Expected X: {expected_x}, Actual X: {actual_x}")
        return actual_x == expected_x
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_y_location_of_element(driver, element, input, xpath_js):
    """Verify element Y coordinate"""
    try:
        if not input or not element:
            return False
        expected_y = int(input)
        actual_y = element.location['y']
        # logger.info(f"Expected Y: {expected_y}, Actual Y: {actual_y}")
        return actual_y == expected_y
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_height_of_web_element(driver, element, input, xpath_js):
    """Verify element height"""
    try:
        if not input or not element:
            return False
        expected_height = int(input)
        actual_height = element.size['height']
        # logger.info(f"Expected Height: {expected_height}, Actual Height: {actual_height}")
        return actual_height == expected_height
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_width_of_element(driver, element, input, xpath_js):
    """Verify element width"""
    try:
        if not input or not element:
            return False
        expected_width = int(input)
        actual_width = element.size['width']
        # logger.info(f"Expected Width: {expected_width}, Actual Width: {actual_width}")
        return actual_width == expected_width
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_radio_button_is_selected(driver, element, input, xpath_js):
    """Verify radio button is selected"""
    try:
        if not element:
            return False
        return element.is_selected()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_radio_button_is_not_selected(driver, element, input, xpath_js):
    """Verify radio button is not selected"""
    try:
        if not element:
            return True
        return not element.is_selected()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_window_width(driver, element, input, xpath_js):
    """Verify browser window width"""
    try:
        if not input:
            return False
        expected_width = int(input)
        actual_width = driver.get_window_size()['width']
        # logger.info(f"Expected Width: {expected_width}, Actual Width: {actual_width}")
        return actual_width == expected_width
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_window_height(driver, element, input, xpath_js):
    """Verify browser window height"""
    try:
        if not input:
            return False
        expected_height = int(input)
        actual_height = driver.get_window_size()['height']
        logger.info(f"Expected Height: {expected_height}, Actual Height: {actual_height}")
        return actual_height == expected_height
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_window_x_location(driver, element, input, xpath_js):
    """Verify browser window X position"""
    try:
        if not input:
            return False
        expected_x = int(input)
        actual_x = driver.get_window_position()['x']
        # logger.info(f"Expected X: {expected_x}, Actual X: {actual_x}")
        return actual_x == expected_x
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_window_y_location(driver, element, input, xpath_js):
    """Verify browser window Y position"""
    try:
        if not input:
            return False
        expected_y = int(input)
        actual_y = driver.get_window_position()['y']
        # logger.info(f"Expected Y: {expected_y}, Actual Y: {actual_y}")
        return actual_y == expected_y
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_html_code_contains_string(driver, element, input, xpath_js):
    """Verify page source contains string"""
    try:
        if not input:
            return False
        expected_text = str(input).strip()
        page_source = driver.page_source
        # logger.info(f"Expected Text: {expected_text}, Actual Text: {page_source}")
        return expected_text in page_source
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_cookie_name_is_added(driver, element, input, xpath_js):
    """Verify cookie exists by name"""
    try:
        if not input:
            return False

        cookie_name = str(input)

        # First try Selenium API
        cookies = driver.get_cookies()
        logger.info(f"Cookies: {cookies}")
        if cookies:
            for cookie in cookies:
                if cookie.get("name") == cookie_name:
                    return True

        # Fallback to JS
        cookie_string = driver.execute_script("return document.cookie")
        logger.info(f"document.cookie = {cookie_string}")

        return cookie_name in cookie_string
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_cookie_name_is_deleted(driver, element, input, xpath_js):
    """Verify cookie does not exist by name"""
    try:
        if not input:
            return False
        cookie_name = str(input)
        cookie = driver.get_cookie(cookie_name)
        return cookie is None
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return True

def execute_verify_if_link_is_broken(driver, element, input, xpath_js):
    """Verify if link is broken by checking HTTP status"""
    try:
        if not input:
            return False
        url = str(input)
        response = requests.head(url, timeout=5, allow_redirects=True)
        # Link is broken if status code is 4xx or 5xx
        return response.status_code >= 400
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return True  # Consider broken if request fails

def execute_verify_css_attribute_value(driver, element, input, xpath_js):
    """Verify CSS property value. Input format: 'property_name,expected_value,case_sensitive'"""
    try:
        if not input or not element:
            return False
        parts = str(input).split(",")
        if len(parts) < 2:
            return False
        
        css_property = parts[0].strip()
        expected_value = parts[1].strip()
        case_sensitive = parts[2].strip().lower() == "true" if len(parts) > 2 else False
        
        actual_value = element.value_of_css_property(css_property) or ""
        
        if case_sensitive:
            return actual_value == expected_value
        else:
            return actual_value.lower() == expected_value.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_video_is_playing(driver, element, input, xpath_js):
    """Verify if video element is playing via JavaScript"""
    try:
        if not element:
            return False
        # Check if video is playing using JavaScript
        is_playing = driver.execute_script("""
            var video = arguments[0];
            return !video.paused && !video.ended && video.currentTime > 0 && video.readyState > 2;
        """, element)
        return is_playing
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_number_of_elements_by_tag_name(driver, element, input, xpath_js):
    """Verify count of elements by tag name. Input format: 'tag_name,expected_count'"""
    try:
        if not input:
            return False
        parts = str(input).split(",")
        if len(parts) < 2:
            return False
        
        tag_name = parts[0].strip()
        expected_count = int(parts[1].strip())
        
        elements = driver.find_elements(By.TAG_NAME, tag_name)
        actual_count = len(elements)
        logger.info(f"Expected Count: {expected_count}, Actual Count: {actual_count}")
        return actual_count == expected_count
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_number_of_elements_by_xpath(driver, element, input, xpath_js):
    """Verify count of elements by XPath. Input format: 'xpath,expected_count'"""
    try:
        if not input:
            return False

        parts = str(input).split(",")
        if len(parts) < 2:
            return False
        
        xpath = parts[0].strip()
        expected_count = int(parts[1].strip())
        
        elements = driver.find_elements(By.XPATH, xpath)
        actual_count = len(elements)
        # logger.info(f"Expected Count: {expected_count}, Actual Count: {actual_count}")
        return actual_count == expected_count
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_list_box_options_are_sorted(driver, element, input, xpath_js):
    """Verify dropdown/listbox options are in sorted order"""
    try:
        if not element:
            return False
        from selenium.webdriver.support.ui import Select
        select = Select(element)
        options = [option.text for option in select.options]
        logger.info(f"Options: {options}")
        if options:
            return True
        return False 
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_option_with_index_is_selected_in_list_box(driver, element, input, xpath_js):
    """Verify option at index is selected"""
    try:
        if not input or not element:
            return False
        from selenium.webdriver.support.ui import Select
        expected_index = int(input)
        select = Select(element)
        selected_options = select.all_selected_options
        if not selected_options:
            return False
        # Check if the option at the index is selected
        options = select.options
        if expected_index < len(options):
            return options[expected_index] in selected_options
        return False
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_option_with_index_is_deselected_in_element(driver, element, input, xpath_js):
    """Verify option at index is NOT selected"""
    try:
        if not input or not element:
            return False
        from selenium.webdriver.support.ui import Select
        expected_index = int(input)
        select = Select(element)
        selected_options = select.all_selected_options
        options = select.options
        if expected_index < len(options):
            return options[expected_index] not in selected_options
        return True
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_all_options_are_selected(driver, element, input, xpath_js):
    """Verify all options in multi-select are selected"""
    try:
        if not element:
            return False
        from selenium.webdriver.support.ui import Select
        select = Select(element)
        all_options = select.options
        selected_options = select.all_selected_options
        return len(all_options) == len(selected_options)
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_all_options_are_deselected(driver, element, input, xpath_js):
    """Verify no options are selected"""
    try:
        if not element:
            return False
        from selenium.webdriver.support.ui import Select
        select = Select(element)
        selected_options = select.all_selected_options
        return len(selected_options) == 0
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_option_with_value_is_selected(driver, element, input, xpath_js):
    """Verify option with specific value is selected"""
    try:
        if not input or not element:
            return False
        from selenium.webdriver.support.ui import Select
        expected_value = str(input).strip()
        select = Select(element)
        selected_options = select.all_selected_options
        for option in selected_options:
            if option.get_attribute("value") == expected_value:
                return True
        return False
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_option_with_value_is_deselected(driver, element, input, xpath_js):
    """Verify option with specific value is NOT selected"""
    try:
        if not input or not element:
            return False
        from selenium.webdriver.support.ui import Select
        expected_value = str(input).strip()
        select = Select(element)
        selected_options = select.all_selected_options
        for option in selected_options:
            if option.get_attribute("value") == expected_value:
                return False
        return True
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_specified_option_is_selected(driver, element, input, xpath_js):
    """Verify option with specific text is selected. Input format: 'option_text,case_sensitive'"""
    try:
        if not input or not element:
            return False
        from selenium.webdriver.support.ui import Select
        parts = str(input).split(",")
        expected_text = parts[0].strip()
        case_sensitive = parts[1].strip().lower() == "true" if len(parts) > 1 else False
        
        select = Select(element)
        selected_options = select.all_selected_options
        
        for option in selected_options:
            option_text = option.text
            if case_sensitive:
                if option_text == expected_text:
                    return True
            else:
                if option_text.lower() == expected_text.lower():
                    return True
        return False
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_that_specified_option_is_not_selected(driver, element, input, xpath_js):
    """Verify option with specific text is NOT selected. Input format: 'option_text,case_sensitive'"""
    try:
        if not input or not element:
            return False
        from selenium.webdriver.support.ui import Select
        parts = str(input).split(",")
        expected_text = parts[0].strip()
        case_sensitive = parts[1].strip().lower() == "true" if len(parts) > 1 else False
        
        select = Select(element)
        selected_options = select.all_selected_options
        
        for option in selected_options:
            option_text = option.text
            if case_sensitive:
                if option_text == expected_text:
                    return False
            else:
                if option_text.lower() == expected_text.lower():
                    return False
        return True
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_given_option_is_duplicate(driver, element, input, xpath_js):
    """Verify if given option text appears multiple times in dropdown"""
    try:
        if not input or not element:
            return False
        from selenium.webdriver.support.ui import Select
        option_text = str(input).strip()
        select = Select(element)
        options = [opt.text for opt in select.options]
        count = options.count(option_text)
        return count > 1
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_title_in_all_page(driver, element, input, xpath_js):
    """Verify title across all browser windows/tabs. Input format: 'expected_title'"""
    try:
        if not input:
            return False
        
        expected_title = input.strip().lower()
        
        current_handle = driver.current_window_handle
        all_handles = driver.window_handles
        
        for handle in all_handles:
            driver.switch_to.window(handle)
            actual_title = driver.title.lower()
            
            if actual_title != expected_title:
                driver.switch_to.window(current_handle)
                return False
        
        driver.switch_to.window(current_handle)
        return True
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        driver.switch_to.window(current_handle) if 'current_handle' in locals() else None
        return False

def execute_verify_link_navigates_to_title(driver, element, input, xpath_js):
    """Verify clicking link navigates to page with specific title. Input format: 'link_url,expected_title'"""
    try:
        if not input:
            return False
        parts = str(input).split(",")
        if len(parts) < 2:
            # logger.error("[ERROR] Invalid input format for VerifyLinkNavigatesToTitle")
            return False
        
        link_url = parts[0].strip()
        expected_title = parts[1].strip()
        
        # Save current window handle
        original_window = driver.title
        if original_window == expected_title:
            return True
        else:
            driver.get(link_url)
            time.sleep(3)  # Wait for page load
            driver.switch_to.window(driver.current_window_handle)
        
        actual_title = driver.title
        # logger.info(f"Actual title: {actual_title}")
        # logger.info(f"Expected title: {expected_title}")
        result = actual_title.lower() == expected_title.lower()
        return result
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False
def normalize_text(text):
    if not text:
        return ""
    # remove zero-width & non-printable chars
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    # normalize spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()

def execute_verify_text(driver, element, input, xpath_js):
    try:
        if "shadow" in xpath_js:
            result = driver.execute_script(SHADOW_DOM_VERIFY_TEXT_JS, xpath_js, input)
            return result
        else:
            if not element or not input:
                return False
            
            expected = normalize_text(input)
            # logger.info(f"Expected text: {expected}")

            texts = []

            # Visible text
            if element.text:
                texts.append(element.text)

            # Input value
            value = element.get_attribute("value")
            if value:
                texts.append(value)

            # Accessibility & UI labels
            for attr in ["placeholder", "aria-label", "name", "id"]:
                v = element.get_attribute(attr)
                if v:
                    texts.append(v)

            # Fallbacks
            for attr in ["textContent", "innerText"]:
                v = element.get_attribute(attr)
                if v:
                    texts.append(v)

            # logger.info(f"Raw element texts: {texts}")
            limited = [t[:50] + "..." if len(t) > 50 else t for t in texts]
            logger.info(f"Limited element texts: {limited}")

            for t in texts:
                clean = normalize_text(t)
                # logger.info(f"Checking cleaned text: {clean}")
                if expected == clean:
                    return True

            return False

    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False



def execute_verify_partial_text(driver, element, input, xpath_js):
    try:
        if "shadow" in xpath_js:
            result = driver.execute_script(SHADOW_DOM_VERIFY_PARTIAL_TEXT_JS, xpath_js, input)
            return result
        else:
            if not element or not input:
                return False
            expected = normalize_text(input)
            # logger.info(f"Expected text: {expected}")

            texts = []

            # Visible text
            if element.text:
                texts.append(element.text)

            # Input value
            value = element.get_attribute("value")
            if value:
                texts.append(value)

            # Accessibility & UI labels
            for attr in ["placeholder", "aria-label", "name", "id"]:
                v = element.get_attribute(attr)
                if v:
                    texts.append(v)

            # Fallbacks
            for attr in ["textContent", "innerText"]:
                v = element.get_attribute(attr)
                if v:
                    texts.append(v)

            # logger.info(f"Raw element texts: {texts}")

            for t in texts:
                clean = normalize_text(t)
                # logger.info(f"Checking cleaned text: {clean}")
                if expected in clean:
                    return True

            return False

    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_element_not_contains_text(driver, element, input, xpath_js):
    """Verify element does not contain text. Input format: 'text,case_sensitive'"""
    try:
        if not element or not input:
            return False
        expected = normalize_text(input)
        # logger.info(f"Expected text: {expected}")

        texts = []

        # Visible text
        if element.text:
            texts.append(element.text)

        # Input value
        value = element.get_attribute("value")
        if value:
            texts.append(value)

        # Accessibility & UI labels
        for attr in ["placeholder", "aria-label", "name", "id"]:
            v = element.get_attribute(attr)
            if v:
                texts.append(v)

        # Fallbacks
        for attr in ["textContent", "innerText"]:
            v = element.get_attribute(attr)
            if v:
                texts.append(v)

        # logger.info(f"Raw element texts: {texts}")

        for t in texts:
            clean = normalize_text(t)
            # logger.info(f"Checking cleaned text: {clean}")
            if expected in clean:
                return False

        return True

    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_element_is_clickable(driver, element, input, xpath_js):
    try:
        if not element:
            return False

        if not element.is_displayed():
            return False

        tag = element.tag_name.lower()

        # Native clickable elements
        if tag in ["button", "a"]:
            return element.is_enabled()

        if tag == "input":
            input_type = (element.get_attribute("type") or "").lower()
            if input_type in ["button", "submit", "checkbox", "radio", "image"]:
                return element.is_enabled()
            return False

        # Explicit JS handler
        if element.get_attribute("onclick"):
            return True

        # Keyboard accessible (important for accessibility)
        tabindex = element.get_attribute("tabindex")
        if tabindex is not None and tabindex != "-1":
            return True

        # ARIA roles (modern frameworks)
        role = (element.get_attribute("role") or "").lower()
        if role in ["button", "link", "menuitem", "option"]:
            return True

        # CSS pointer cursor (very common)
        cursor = driver.execute_script(
            "return window.getComputedStyle(arguments[0]).cursor;",
            element
        )
        if cursor == "pointer":
            return True

        # Framework-generated clickable (React/Vue/Angular)
        # Event listeners attached via JS (best-effort check)
        has_listener = driver.execute_script("""
            const el = arguments[0];
            return !!(el.onclick || el.onmousedown || el.onmouseup);
        """, element)
        if has_listener:
            return True

        # ❌ Otherwise NOT clickable
        return False

    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False


def execute_verify_element_is_disabled(driver, element, input, xpath_js):
    """Verify element is disabled"""
    try:
        if not element:
            return False
        return not element.is_enabled()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_element_is_enabled(driver, element, input, xpath_js):
    """Verify element is enabled"""
    try:
        if not element:
            return False
        return element.is_enabled()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_element_is_selected(driver, element, input, xpath_js):
    """Verify element is selected (checkbox/radio)"""
    try:
        if not element:
            return False
        return element.is_selected()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_checkbox_is_selected(driver, element, input, xpath_js):
    """Verify checkbox is selected"""
    try:
        if not element:
            return False
        return element.is_selected()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_checkbox_is_not_selected(driver, element, input, xpath_js):
    """Verify checkbox is not selected"""
    try:
        if not element:
            return True
        return not element.is_selected()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_window_url_contains_expected_url(driver, element, input, xpath_js):
    """Verify current URL contains expected string"""
    try:
        if not input:
            return False
        expected_url = str(input).strip()
        actual_url = driver.current_url
        return expected_url.lower() in actual_url.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_window_url_is_string(driver, element, input, xpath_js):
    """Verify current URL exactly matches string"""
    try:
        if not input:
            return False
        expected_url = str(input).strip()
        actual_url = driver.current_url
        return actual_url.lower() == expected_url.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_window_title_contains_string(driver, element, input, xpath_js):
    """Verify browser title contains string"""
    try:
        if not input:
            return False
        expected_text = str(input).strip()
        actual_title = driver.title
        return expected_text.lower() in actual_title.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_browser_window_title_is_string(driver, element, input, xpath_js):
    """Verify browser title exactly matches string"""
    try:
        if not input:
            return False
        expected_title = str(input).strip()
        actual_title = driver.title
        return actual_title.lower() == expected_title.lower()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_browser_window_is_closed(driver, element, input, xpath_js):
    """Verify if browser window is closed"""
    try:
        _ = driver.current_window_handle
        return False  # Window is still open
    except:
        return True  # Window is closed

def execute_verify_all_browser_windows_closed(driver, element, input, xpath_js):
    """Verify all browser windows are closed"""
    try:
        handles = driver.window_handles
        return len(handles) == 0
    except:
        return True  # Browser is closed

def execute_verify_if_all_cookies_are_deleted(driver, element, input, xpath_js):
    """Verify all cookies are deleted"""
    try:
        cookies = driver.get_cookies()
        return len(cookies) == 0
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_cookie_object_is_present(driver, element, input, xpath_js):
    """Verify if any cookie is present"""
    try:
        cookies = driver.get_cookies()
        return len(cookies) > 0
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_x_and_y_coordinate_of_element(driver, element, input, xpath_js):
    """Verify element X and Y coordinates. Input format: 'expected_x,expected_y'"""
    try:
        if not input or not element:
            return False
        parts = str(input).split(",")
        if len(parts) < 2:
            return False
        expected_x = int(parts[0].strip())
        expected_y = int(parts[1].strip())
        
        location = element.location
        # logger.info(f"Element location: {location}")
        # logger.info(f"Expected location: {expected_x, expected_y}")
        return location['x'] == expected_x and location['y'] == expected_y
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_video_is_muted(driver, element, input, xpath_js):
    """Verify if video is muted"""
    try:
        if not element:
            return False
        is_muted = driver.execute_script("return arguments[0].muted;", element)
        return is_muted
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_video_is_paused(driver, element, input, xpath_js):
    """Verify if video is paused"""
    try:
        if not element:
            return False
        is_paused = driver.execute_script("return arguments[0].paused;", element)
        return is_paused
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_video_ended(driver, element, input, xpath_js):
    """Verify if video has ended"""
    try:
        if not element:
            return False
        has_ended = driver.execute_script("return arguments[0].ended;", element)
        return has_ended
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_video_playing_in_mute(driver, element, input, xpath_js):
    """Verify if video is playing in mute"""
    try:
        if not element:
            return False
        is_playing = driver.execute_script("""
            var video = arguments[0];
            return !video.paused && !video.ended && video.currentTime > 0 && video.readyState > 2 && video.muted;
        """, element)
        return is_playing
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_video_playing_in_unmute(driver, element, input, xpath_js):
    """Verify if video is playing without mute"""
    try:
        if not element:
            return False
        is_playing = driver.execute_script("""
            var video = arguments[0];
            return !video.paused && !video.ended && video.currentTime > 0 && video.readyState > 2 && !video.muted;
        """, element)
        return is_playing
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_audio_is_playing(driver, element, input, xpath_js):
    try:
        if not element or not input:
            return False

        # Get displayed song name
        actual_song = element.text.strip()

        logger.info(
            "Now Playing song: '%s', Expected song: '%s'",
            actual_song, input
        )

        # Basic visibility check (generic)
        if not element.is_displayed():
            return False

        # Compare song names (case-insensitive)
        return actual_song.lower() == input.lower()

    except Exception as e:
        logger.error(f"[ERROR] Audio verification failed: {e}")
        return False


def execute_verify_if_audio_is_paused(driver, element, input, xpath_js):
    """Verify if audio is paused"""
    try:
        if not element:
            return False
        is_paused = driver.execute_script("return arguments[0].paused;", element)
        return is_paused
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_audio_is_muted(driver, element, input, xpath_js):
    """Verify if audio is muted"""
    try:
        if not element:
            return False
        is_muted = driver.execute_script("return arguments[0].muted;", element)
        return is_muted
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_audio_ended(driver, element, input, xpath_js):
    """Verify if audio has ended"""
    try:
        if not element:
            return False
        has_ended = driver.execute_script("return arguments[0].ended;", element)
        return has_ended
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_link_is_working(driver, element, input, xpath_js):
    """Verify if link is working (status code < 400)"""
    try:
        if not input:
            return False
        url = str(input).strip()
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_links_are_working(driver, element, input, xpath_js):
    """Verify all links on page are working"""
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                try:
                    response = requests.head(href, timeout=5, allow_redirects=True)
                    if response.status_code >= 400:
                        return False
                except:
                    return False
        return True
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_links_are_broken(driver, element, input, xpath_js):
    """Verify if there are any broken links on page"""
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                try:
                    response = requests.head(href, timeout=5, allow_redirects=True)
                    if response.status_code >= 400:
                        return True  # Found a broken link
                except:
                    return True  # Request failed, link is broken
        return False  # No broken links found
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_image_is_broken(driver, element, input, xpath_js):
    """Verify if specific image is broken"""
    try:
        if not input:
            return False
        image_url = str(input).strip()
        response = requests.head(image_url, timeout=5, allow_redirects=True)
        return response.status_code >= 400
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return True  # Consider broken if request fails

def execute_verify_all_broken_images(driver, element, input, xpath_js):
    """Verify if there are any broken images on page"""
    try:
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            src = img.get_attribute("src")
            if src:
                try:
                    response = requests.head(src, timeout=5, allow_redirects=True)
                    if response.status_code >= 400:
                        return True  # Found a broken image
                except:
                    return True  # Request failed, image is broken
        return False  # No broken images found
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False
#
def execute_verify_if_status_code_of_a_link_is_status_code(driver, element, input, xpath_js):
    """Verify status code of a link. Input format: 'expected_code,url'"""
    try:
        if not input:
            return False
        parts = str(input).split(",")
        if len(parts) < 2:
            return False
        expected_code = int(parts[0].strip())
        url = parts[1].strip()
        
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == expected_code
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False
#
def execute_verify_if_status_codes_of_links(driver, element, input, xpath_js):
    """Verify all links have specific status code"""
    try:
        if not input:
            return False
        expected_code = int(input)
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                try:
                    response = requests.head(href, timeout=5, allow_redirects=True)
                    if response.status_code != expected_code:
                        return False
                except:
                    return False
        return True
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False

def execute_verify_if_option_with_visible_text_is_selected(driver, element, input, xpath_js):
    """Verify option with given visible text IS selected (dropdown / checkbox / custom UI)"""
    try:
        if not input or not element:
            return False

        expected_text = str(input).strip().lower()
        tag_name = element.tag_name.lower()

        # -------- CASE 1: Native <select> dropdown --------
        if tag_name == "select":
            from selenium.webdriver.support.ui import Select
            select = Select(element)
            for option in select.all_selected_options:
                if option.text.strip().lower() == expected_text:
                    return True
            return False

        # -------- CASE 2: Native checkbox / radio --------
        if tag_name == "input":
            input_type = element.get_attribute("type")
            if input_type in ("checkbox", "radio"):
                return element.is_selected()

        # -------- CASE 3: Custom / Material UI checkbox --------
        checkbox = element.find_elements(
            "xpath",
            ".//input[@type='checkbox' or @type='radio']"
        )
        if checkbox:
            return checkbox[0].is_selected()

        # -------- CASE 4: ARIA-based selection --------
        aria_checked = element.get_attribute("aria-checked")
        if aria_checked is not None:
            return aria_checked.lower() == "true"

        # -------- CASE 5: CSS class-based selection --------
        class_attr = element.get_attribute("class") or ""
        if any(k in class_attr.lower() for k in ("checked", "selected", "active")):
            return True

        return False

    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False



def execute_verify_if_option_with_text_is_deselected(driver, element, input, xpath_js):
    """Verify option with given visible text is NOT selected (dropdown / checkbox / custom UI)"""
    try:
        if not input or not element:
            return False

        expected_text = str(input).strip().lower()
        tag_name = element.tag_name.lower()

        # -------- CASE 1: Native <select> dropdown --------
        if tag_name == "select":
            from selenium.webdriver.support.ui import Select
            select = Select(element)
            for option in select.all_selected_options:
                if option.text.strip().lower() == expected_text:
                    return False
            return True

        # -------- CASE 2: Native checkbox or radio --------
        if tag_name == "input":
            input_type = element.get_attribute("type")
            if input_type in ("checkbox", "radio"):
                return not element.is_selected()

        # -------- CASE 3: Material UI / custom checkbox --------
        # Look for an <input type="checkbox"> inside the element
        checkbox = element.find_elements(
            "xpath",
            ".//input[@type='checkbox' or @type='radio']"
        )
        if checkbox:
            return not checkbox[0].is_selected()

        # -------- CASE 4: ARIA-based selection --------
        aria_checked = element.get_attribute("aria-checked")
        if aria_checked is not None:
            return aria_checked.lower() == "false"

        # -------- CASE 5: CSS class based (fallback) --------
        class_attr = element.get_attribute("class") or ""
        if "checked" in class_attr.lower() or "selected" in class_attr.lower():
            return False

        # If none indicate selected → treat as deselected
        return True

    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False


def execute_verify_performance_score(driver, element, input, xpath_js):
    """
    Verify Performance readiness score for a page (NO Lighthouse).
    Input formats supported:
      - '70'
      - '70,https://example.com'
      - 'https://example.com,70'
    """
    print("Starting Performance verification...")
    try:
        if not input:
            return False

        parts = [p.strip() for p in str(input).split(",")]

        url = None
        expected_score = None

        for part in parts:
            if part.startswith("http"):
                url = part
            else:
                expected_score = int(part)

        if expected_score is None:
            return False

        # Navigate only if URL is provided
        if url:
            driver.get(url)

        # -------- Performance metrics (browser-native) --------
        metrics = driver.execute_script("""
            const timing = performance.timing;
            const paint = performance.getEntriesByType('paint');

            const fcp = paint.find(p => p.name === 'first-contentful-paint');
            const fcpTime = fcp ? fcp.startTime : null;

            return {
                domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                loadTime: timing.loadEventEnd - timing.navigationStart,
                firstContentfulPaint: fcpTime,
                resourceCount: performance.getEntriesByType('resource').length,
                transferSize: performance.getEntriesByType('resource')
                    .reduce((t, r) => t + (r.transferSize || 0), 0)
            };
        """)

        # -------- Scoring logic (simple & deterministic) --------
        checks = {
            # FCP under 2.5s
            "fcp_good": metrics["firstContentfulPaint"] is not None
                        and metrics["firstContentfulPaint"] <= 2500,

            # DOM ready under 3s
            "dom_ready_fast": metrics["domContentLoaded"] <= 3000,

            # Page load under 5s
            "load_fast": metrics["loadTime"] <= 5000,

            # Reasonable resource count
            "resource_count_ok": metrics["resourceCount"] <= 150,

            # Reasonable transfer size (< 5MB)
            "payload_ok": metrics["transferSize"] <= 5 * 1024 * 1024,
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        actual_score = int((passed / total) * 100)

        logger.info(
            f"[PERFORMANCE SCORE] URL={driver.current_url}, "
            f"Passed={passed}/{total}, "
            f"Score={actual_score}, "
            f"Expected={expected_score}, "
            f"Metrics={metrics}"
        )

        return actual_score >= expected_score

    except Exception as e:
        logger.error(f"[ERROR] Performance verification failed: {e}")
        return False


def execute_verify_accessibility_score(driver, element, input, xpath_js):
    """
    Verify Accessibility readiness score for a page (NO Lighthouse).
    Input formats supported:
      - '70'
      - '70,https://example.com'
      - 'https://example.com,70'
    """
    print("Starting Accessibility verification...")
    try:
        if not input:
            return False

        parts = [p.strip() for p in str(input).split(",")]

        url = None
        expected_score = None

        for part in parts:
            if part.startswith("http"):
                url = part
            else:
                expected_score = int(part)

        if expected_score is None:
            return False

        # Navigate only if URL is provided
        if url:
            driver.get(url)

        # -------- Accessibility readiness checks (page-level) --------
        checks = {
            # HTML lang attribute
            "html_lang": driver.execute_script(
                "return document.documentElement.hasAttribute('lang')"
            ),

            # Page title exists
            "title_present": driver.execute_script(
                "return document.title && document.title.trim().length > 0"
            ),

            # Images have alt attributes
            "img_alt": driver.execute_script(
                "return Array.from(document.images)"
                ".every(img => img.hasAttribute('alt'))"
            ),

            # Inputs have labels or aria-label
            "inputs_labeled": driver.execute_script(
                "return Array.from(document.querySelectorAll('input,textarea,select'))"
                ".every(el => el.labels?.length > 0 || el.hasAttribute('aria-label'))"
            ),

            # Buttons have accessible names
            "buttons_accessible": driver.execute_script(
                "return Array.from(document.querySelectorAll('button'))"
                ".every(btn => btn.innerText.trim().length > 0 || btn.hasAttribute('aria-label'))"
            ),

            # No focusable element hidden from screen readers
            "no_aria_hidden_focusable": driver.execute_script(
                "return Array.from(document.querySelectorAll('[aria-hidden=\"true\"]'))"
                ".every(el => el.tabIndex === -1)"
            ),

            # Basic color contrast presence (not full WCAG calc)
            "text_has_color": driver.execute_script(
                "return Array.from(document.querySelectorAll('body *'))"
                ".some(el => window.getComputedStyle(el).color !== 'rgba(0, 0, 0, 0)')"
            ),
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        actual_score = int((passed / total) * 100)

        logger.info(
            f"[ACCESSIBILITY SCORE] URL={driver.current_url}, "
            f"Passed={passed}/{total}, "
            f"Score={actual_score}, "
            f"Expected={expected_score}"
        )

        return actual_score >= expected_score

    except Exception as e:
        logger.error(f"[ERROR] Accessibility verification failed: {e}")
        return False


def execute_verify_best_practices_score(driver, element, input, xpath_js):
    """
    Verify Best Practices readiness score for a page (NO Lighthouse).
    Input formats supported:
      - '70'
      - '70,https://example.com'
      - 'https://example.com,70'
    """
    print("Starting Best Practices verification...")
    try:
        if not input:
            return False

        parts = [p.strip() for p in str(input).split(",")]

        url = None
        expected_score = None

        for part in parts:
            if part.startswith("http"):
                url = part
            else:
                expected_score = int(part)

        if expected_score is None:
            return False

        # Navigate only if URL is provided
        if url:
            driver.get(url)

        # -------- Best Practices checks (page-level) --------
        checks = {
            # HTTPS is mandatory
            "https": driver.current_url.startswith("https"),

            # No mixed content
            "no_mixed_content": driver.execute_script(
                "return Array.from(document.querySelectorAll('img,script,link'))"
                ".every(e => !e.src || e.src.startsWith('https') || e.src.startsWith('data:'))"
            ),

            # No deprecated HTML tags
            "no_deprecated_tags": driver.execute_script(
                "return document.querySelectorAll('font,center,marquee').length === 0"
            ),

            # No inline JS event handlers (onclick, onload, etc.)
            "no_inline_js": driver.execute_script(
                "return Array.from(document.querySelectorAll('*'))"
                ".every(el => !Array.from(el.attributes)"
                ".some(a => a.name.startsWith('on')))"
            ),

            # No JavaScript console errors
            "no_console_errors": driver.execute_script(
                "return window.__jsErrors__ === undefined || window.__jsErrors__.length === 0"
            ),

            # Secure iframe usage
            "secure_iframes": driver.execute_script(
                "return Array.from(document.querySelectorAll('iframe'))"
                ".every(f => !f.hasAttribute('sandbox') || f.getAttribute('sandbox').includes('allow-same-origin'))"
            ),
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        actual_score = int((passed / total) * 100)

        logger.info(
            f"[BEST PRACTICES SCORE] URL={driver.current_url}, "
            f"Passed={passed}/{total}, "
            f"Score={actual_score}, "
            f"Expected={expected_score}"
        )

        return actual_score >= expected_score

    except Exception as e:
        logger.error(f"[ERROR] Best Practices verification failed: {e}")
        return False

def execute_verify_seo_score(driver, element, input, xpath_js):
    """
    Verify SEO readiness score for a page (NO Lighthouse).
    Input formats supported:
      - '70'
      - '70,https://example.com'
      - 'https://example.com,70'
    """
    print("Starting SEO verification...")
    try:
        if not input:
            return False

        parts = [p.strip() for p in str(input).split(",")]

        url = None
        expected_score = None

        for part in parts:
            if part.startswith("http"):
                url = part
            else:
                expected_score = int(part)

        if expected_score is None:
            return False

        # Navigate only if URL is provided
        if url:
            driver.get(url)

        # -------- SEO readiness checks (page-level) --------
        checks = {
            # HTTPS is mandatory for SEO
            "https": driver.current_url.startswith("https"),

            # Title tag exists and not empty
            "title_present": driver.execute_script(
                "return document.title && document.title.trim().length > 0"
            ),

            # Meta description exists
            "meta_description": driver.execute_script(
                "var m=document.querySelector('meta[name=\"description\"]');"
                "return m && m.content && m.content.trim().length > 0"
            ),

            # Canonical link exists
            "canonical": driver.execute_script(
                "return !!document.querySelector('link[rel=\"canonical\"]')"
            ),

            # Page is indexable (no noindex)
            "indexable": driver.execute_script(
                "var r=document.querySelector('meta[name=\"robots\"]');"
                "return !r || !/noindex/i.test(r.content)"
            ),

            # At least one H1 exists
            "h1_present": driver.execute_script(
                "return document.querySelectorAll('h1').length > 0"
            ),
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        actual_score = int((passed / total) * 100)

        logger.info(
            f"[SEO SCORE] URL={driver.current_url}, "
            f"Passed={passed}/{total}, "
            f"Score={actual_score}, "
            f"Expected={expected_score}"
        )

        return actual_score >= expected_score

    except Exception as e:
        logger.error(f"[ERROR] SEO verification failed: {e}")
        return False

def execute_verify_pwa_score(driver, element, input, xpath_js):
    """
    Verify PWA readiness score for a page.
    Input formats supported:
      - '60,https://example.com'
      - 'https://example.com,60'
      - '60'  (uses current page)
    """
    print("Starting PWA verification...")
    try:
        if not input:
            return False

        parts = [p.strip() for p in str(input).split(",")]

        url = None
        expected_score = None

        for part in parts:
            if part.startswith("http"):
                url = part
            else:
                expected_score = int(part)

        if expected_score is None:
            return False

        # Navigate only if URL is provided
        if url:
            driver.get(url)

        # -------- PWA readiness checks (page-level) --------
        checks = {
            "https": driver.current_url.startswith("https"),

            "service_worker_supported": driver.execute_script(
                "return 'serviceWorker' in navigator"
            ),

            "service_worker_registered": driver.execute_script(
                "return navigator.serviceWorker && navigator.serviceWorker.controller !== null"
            ),

            "manifest_present": driver.execute_script(
                "return !!document.querySelector('link[rel=\"manifest\"]')"
            ),
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        actual_score = int((passed / total) * 100)

        logger.info(
            f"[PWA SCORE] URL={driver.current_url}, "
            f"Passed={passed}/{total}, "
            f"Score={actual_score}, "
            f"Expected={expected_score}"
        )

        return actual_score >= expected_score

    except Exception as e:
        logger.error(f"[ERROR] PWA verification failed: {e}")
        return False



def execute_verify_hex_code_for_given_xy_coordinates(driver, element, input, xpath_js):
    """Verify hex color code at given X,Y coordinates. Input format: 'x,y,expected_hex'"""
    try:
        if not input:
            return False
        parts = str(input).split(",")
        if len(parts) < 3:
            return False
        
        x = int(parts[1].strip())
        y = int(parts[2].strip())
        expected_hex = parts[0].strip().upper()
        
        # Take screenshot and get color at coordinates
        from PIL import Image
        import io
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        pixel = image.getpixel((x, y))
        
        # Convert RGB to hex
        actual_hex = '#{:02x}{:02x}{:02x}'.format(pixel[0], pixel[1], pixel[2]).upper()
        
        return actual_hex == expected_hex.upper()
    except Exception as e:
        logger.error(f"[ERROR] Verification failed: {e}")
        return False


# Map NLP names to functions
EXECUTE_FUNCTIONS = {
    "VerifyElementIsDisplayed": execute_verify_element_is_displayed,
    "VerifyElementIsNotDisplayed": execute_verify_element_is_not_displayed,
    "VerifyAttributeValue": execute_verify_attribute_value,
    "VerifyPartialAttributeValue": execute_verify_partial_attribute_value,
    "VerifyTagName": execute_verify_tag_name,
    "VerifyTitleOfCurrentPage": execute_verify_title_of_current_page,
    "VerifyPartialTitleOfCurrentPage": execute_verify_partial_title_of_current_page,
    "VerifyNavigateURL": execute_verify_navigate_url,
    "VerifyValueOfElementIsString": execute_verify_value_of_element_is_string,
    "VerifyValueOfElementContainsString": execute_verify_value_of_element_contains_string,
    "VerifyValueOfElementIsCleared": execute_verify_value_of_element_is_cleared,
    "VerifyXLocationOfElement": execute_verify_x_location_of_element,
    "VerifyYLocationOfElement": execute_verify_y_location_of_element,
    "VerifyHeightOfWebElement": execute_verify_height_of_web_element,
    "VerifyWidthOfElement": execute_verify_width_of_element,
    "VerifyRadioButtonIsSelected": execute_verify_radio_button_is_selected,
    "VerifyRadioButtonIsNotSelected": execute_verify_radio_button_is_not_selected,
    "VerifyBrowserWindowWidth": execute_verify_browser_window_width,
    "VerifyBrowserWindowHeight": execute_verify_browser_window_height,
    "VerifyBrowserWindowXLocation": execute_verify_browser_window_x_location,
    "VerifyBrowserWindowYLocation": execute_verify_browser_window_y_location,
    "VerifyBrowserHtmlCodeContainsString": execute_verify_browser_html_code_contains_string,
    "VerifyIfCookieNameIsAdded": execute_verify_if_cookie_name_is_added,
    "VerifyIfCookieNameIsDeleted": execute_verify_if_cookie_name_is_deleted,
    "VerifyIfLinkIsBroken": execute_verify_if_link_is_broken,
    "VerifyCssAttributeValue": execute_verify_css_attribute_value,
    "VerifyIfVideoIsPlaying": execute_verify_if_video_is_playing,
    "VerifyNumberOfElementsByTagName": execute_verify_number_of_elements_by_tag_name,
    "VerifyNumberOfElementsByXpath": execute_verify_number_of_elements_by_xpath,
    "VerifyListBoxOptionsAreSorted": execute_verify_list_box_options_are_sorted,
    "VerifyIfOptionWithIndexIsSelectedInListBox": execute_verify_if_option_with_index_is_selected_in_list_box,
    "VerifyIfOptionWithIndexIsDeselectedInElement": execute_verify_if_option_with_index_is_deselected_in_element,
    "VerifyAllOptionsAreSelected": execute_verify_all_options_are_selected,
    "VerifyAllOptionsAreDeselected": execute_verify_all_options_are_deselected,
    "VerifyIfOptionWithValueIsSelected": execute_verify_if_option_with_value_is_selected,
    "VerifyIfOptionWithValueIsDeselected": execute_verify_if_option_with_value_is_deselected,
    "VerifyIfSpecifiedOptionIsSelected": execute_verify_if_specified_option_is_selected,
    "VerifyThatSpecifiedOptionIsNotSelected": execute_verify_that_specified_option_is_not_selected,
    "VerifyIfGivenOptionIsDuplicate": execute_verify_if_given_option_is_duplicate,
    "VerifyTitleInAllPage": execute_verify_title_in_all_page,
    "VerifyLinkNavigatesToTitle": execute_verify_link_navigates_to_title,
    
    "VerifyText": execute_verify_text,
    "VerifyPartialText": execute_verify_partial_text,
    "VerifyElementNotContainsText": execute_verify_element_not_contains_text,
    "VerifyElementIsClickable": execute_verify_element_is_clickable,
    "VerifyElementIsDisabled": execute_verify_element_is_disabled,
    "VerifyElementIsEnabled": execute_verify_element_is_enabled,
    "VerifyElementIsSelected": execute_verify_element_is_selected,
    "VerifyCheckBoxIsSelected": execute_verify_checkbox_is_selected,
    "VerifyCheckBoxIsNotSelected": execute_verify_checkbox_is_not_selected,
    "VerifyBrowserWindowUrlContainsExpectedUrl": execute_verify_browser_window_url_contains_expected_url,
    "VerifyBrowserWindowUrlIsString": execute_verify_browser_window_url_is_string,
    "VerifyBrowserWindowTitleContainsString": execute_verify_browser_window_title_contains_string,
    "VerifyBrowserWindowTitleIsString": execute_verify_browser_window_title_is_string,
    "VerifyIfBrowserWindowIsClosed": execute_verify_if_browser_window_is_closed,
    "VerifyAllBrowserWindowsClosed": execute_verify_all_browser_windows_closed,
    "VerifyIfAllCookiesAreDeleted": execute_verify_if_all_cookies_are_deleted,
    "VerifyIfCookieObjectIsPresent": execute_verify_if_cookie_object_is_present,
    "VerifyIfXAndYCoordinateOfElement": execute_verify_if_x_and_y_coordinate_of_element,
    "VerifyIfVideoIsMuted": execute_verify_if_video_is_muted,
    "VerifyIfVideoIsPaused": execute_verify_if_video_is_paused,
    "VerifyIfVideoEnded": execute_verify_if_video_ended,
    "VerifyIfVideoPlayingInMute": execute_verify_if_video_playing_in_mute,
    "VerifyIfVideoPlayingInUnmute": execute_verify_if_video_playing_in_unmute,
    "VerifyIfAudioIsPlaying": execute_verify_if_audio_is_playing,
    "VerifyIfAudioIsPaused": execute_verify_if_audio_is_paused,
    "VerifyIfAudioIsMuted": execute_verify_if_audio_is_muted,
    "VerifyIfAudioEnded": execute_verify_if_audio_ended,
    "VerifyIfLinkIsWorking": execute_verify_if_link_is_working,
    "VerifyIfLinksAreWorking": execute_verify_if_links_are_working,
    "VerifyIfLinksAreBroken": execute_verify_if_links_are_broken,
    "VerifyIfImageIsBroken": execute_verify_if_image_is_broken,
    "VerifyAllBrokenImages": execute_verify_all_broken_images,
    "VerifyIfStatusCodeOfALinkIsStatusCode": execute_verify_if_status_code_of_a_link_is_status_code,
    "VerifyIfStatusCodesOfLinks": execute_verify_if_status_codes_of_links,
    "VerifyIfOptionWithVisibleTextIsSelected": execute_verify_if_option_with_visible_text_is_selected,
    "VerifyIfOptionWithTextIsDeselected": execute_verify_if_option_with_text_is_deselected,
    "VerifyPerformanceScore": execute_verify_performance_score,
    "VerifyAccessibilityScore": execute_verify_accessibility_score,
    "VerifyBestPracticesScore": execute_verify_best_practices_score,
    "VerifySeoScore": execute_verify_seo_score,
    "VerifyPwaScore": execute_verify_pwa_score,
    "VerifyHexCodeForGivenXYCoordinates": execute_verify_hex_code_for_given_xy_coordinates,
}


def execute_verification(driver, annotated_dom, simplified_dom, step,element_name,server_host, filtered_steps, serviceProvider, model, apiKey,service_accounts, auto_healing=None):
    from agent import WebStepExecutor
    webstepexecutor = WebStepExecutor(driver)
    if auto_healing is None:
        from auto_healing import AutoHealing
        auto_healing = AutoHealing()
    
    ff_num, nlp_name, input_text, keyword, element_type = match_nlp_via_llm(
        simplified_dom, step, NLP_LIST, filtered_steps, serviceProvider, model, apiKey,service_accounts
    )
    xpath_path = ""
    xpath_js = ""
    iframe = [False,""]
    element = None
    if ff_num in [0,"0"]:
        logger.info(f"element not found for : {step}")
        # return False, ff_num, nlp_name, keyword, input_text, "", "", element_type, i_tok, o_tok, t_tok
    
    if not nlp_name or nlp_name not in EXECUTE_FUNCTIONS:
        logger.info(f"No matching NLP for step: {step}")
        return False, ff_num, nlp_name, keyword,element_type, input_text, xpath_path, xpath_js, iframe
    
    try:
        if annotated_dom:
            tree = html.fromstring(annotated_dom)
            target = tree.xpath(f"//*[@ff-inspect='Fire-Flink-{ff_num}']")
            if target:
                element = target[0]
                xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)

                element, xpath_js, iframe = webstepexecutor._resolve_element(xpath_path, ff_num)
                logger.info(f"Xpath: {xpath_js}")
            else:
                xpath_path = ""
        else:
            element = None
            xpath_path = ""
    except Exception as e:
        logger.error(f"Error extracting xpath: {e}")
        xpath_path = ""
    try:
        if element:
            pass
    except Exception as e:
        logger.warning(f"Element not found for verification: {e}")
        element = None

    if element:
        auto_healing.send_locator_request(annotated_dom, f"Fire-Flink-{ff_num}", element_name,server_host, source="primary")
    elif "shadow" in xpath_js:
        auto_healing.send_locator_request(annotated_dom, f"Fire-Flink-{ff_num}", element_name,server_host, source="shadow")
    
    # try:
    #     if xpath_js:
    #         logger.info(f"Using XPath: {xpath_js}")
    #         element = driver.find_element(By.XPATH, xpath_js)
    #     else:
    #         element = None
    # except Exception as e:
    #     logger.warning(f"Element not found for verification: {e}")
    #     element = None
    
    func = EXECUTE_FUNCTIONS[nlp_name]
    result = func(driver, element, input_text, xpath_js)
    if "shadow" in xpath_js:
        if nlp_name == "VerifyText":
            nlp_name = "ExecuteJavaScript"
            input_val = input_text 
            input_text = SHADOW_DOM_VERIFY_TEXT_JS.replace("const path = arguments[0];", f'const path = "{xpath_js}";')
            input_text = input_text.replace("const text = arguments[1];", f'const text = "{input_val}";')
        elif nlp_name == "VerifyPartialText":
            nlp_name = "ExecuteJavaScript"
            input_val = input_text 
            input_text = SHADOW_DOM_VERIFY_PARTIAL_TEXT_JS.replace("const path = arguments[0];", f'const path = "{xpath_js}";')
            input_text = input_text.replace("const text = arguments[1];", f'const text = "{input_val}";')
        
            
    logger.info(f"Verification result for {nlp_name}: {result}")

    
    return result, ff_num, nlp_name, keyword,element_type, input_text, xpath_path, xpath_js, iframe
 