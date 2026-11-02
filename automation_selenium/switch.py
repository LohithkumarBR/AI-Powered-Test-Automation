import json
from LLMcall import call_grok_llm
import re
from lxml import etree, html 
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, NoSuchFrameException
import time
from pydantic import BaseModel, Field, ValidationError
from enum import Enum
import logging
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding="utf-8")

class nlpName_enum(Enum):
    SwitchToParentWindow = "SwitchToParentWindow"
    SwitchToNewWindowIfUrlContainsString = "SwitchToNewWindowIfUrlContainsString"
    SwitchToWindowBasedOnURL = "SwitchToWindowBasedOnURL"
    SwitchToNewTabBasedOnTitle = "SwitchToNewTabBasedOnTitle"
    SwitchToTabBasedOnUrl = "SwitchToTabBasedOnUrl"
    SwitchToNewWindowBasedOnTitle = "SwitchToNewWindowBasedOnTitle"
    SwitchToWindowIfTitleContainsString = "SwitchToWindowIfTitleContainsString"
    SwitchToFrameByFrameIndex = "SwitchToFrameByFrameIndex"
    SwitchToDefaultContent = "SwitchToDefaultContent"
    SwitchToParentOfTheFrame = "SwitchToParentOfTheFrame"
    SwitchToFrameByFrameElement = "SwitchToFrameByFrameElement"
    SwitchToFrameByFrameName = "SwitchToFrameByFrameName"
    SwitchToWindowByHandle = "SwitchToWindowByHandle"
    SwitchToWindowBasedOnElement = "SwitchToWindowBasedOnElement"
    SwitchToWindowBasedOnTitle = "SwitchToWindowBasedOnTitle"

class FFInspecterResponse(BaseModel):
    attribute_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element.",
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
        examples=["x", "x"]
    )
    

# Parse NLP list from the string
NLP_LIST = [
    "SwitchToParentWindow",
    "SwitchToNewWindowIfUrlContainsString",
    "SwitchToWindowBasedOnURL",
    "SwitchToNewTabBasedOnTitle",
    "SwitchToTabBasedOnUrl",
    "SwitchToNewWindowBasedOnTitle",
    "SwitchToWindowIfTitleContainsString",
    "SwitchToFrameByFrameIndex",
    "SwitchToDefaultContent",
    "SwitchToParentOfTheFrame",
    "SwitchToFrameByFrameElement",
    "SwitchToFrameByFrameName",
    "SwitchToWindowByHandle",
    "SwitchToWindowBasedOnElement",
    "SwitchToWindowBasedOnTitle"
]

def match_nlp_via_llm(simplified_dom, step, nlp_list, filtered_steps, serviceProvider, model, apiKey, service_accounts):
    prompt = f"""
You are an intelligent assistant that extracts structured UI action data.
Given the step: "{step}", the simplified DOM: {json.dumps(simplified_dom, ensure_ascii=False)}, and the list of NLP names: {nlp_list}.

Select the perfect matching NLP name from the list that best fits the step's intent.
**The NLP name must match exactly one value from the approved NLP list. Do not generate or suggest any new NLP names under any condition.**
{{
  "attribute_value": "Fire-Flink-x",
  "nlpName": "x",
  "input_text": "x",
  "keyword": "x"
}}

Rules:
- nlpName must be exactly one from the provided list.
- Use context from the steps : {filtered_steps}, keyword and json to search for FF-inspecter.
- **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
- Extract input_text from the step that represents the target window URL, Title, Frame Name, Frame Index, etc.
- if step consist of keyword like title and url than map to that matched nlp.
- If a step contains a full URL (for example, https://example.com), map it using URL-based NLP matching.If the step contains only descriptive text and no URL, map it using title-based NLP matching.
    example: "Switch to the new tab based on https://example.com" -> input_text: "https://example.com", nlpName: "SwitchToNewTabBasedOnUrl"
    example: "Switch to the tab based on Title" -> input_text: "Title", nlpName: "SwitchToNewTabBasedOnTitle"
- step may some times have 'new' keyword in it, dont consider it just map th nlps. never get confused by title and url.
- If step is about switching to frame by index, input_text should be the index number.
- If step is about switching to frame by name, input_text should be the frame name.
- If step is about switching to window by URL or Title, input_text should be the url or title string.
- If no explicit input is found, attempt to infer it or leave empty if the NLP implies a specific action without input (e.g. SwitchToParentWindow).
- **Respond with valid JSON only. don't return any other text or don't return response in list format**
"""
    try:
        # Call Groq LLM using your wrapper
        response_text = call_grok_llm(prompt, serviceProvider, model, apiKey, service_accounts)
        
        # Parse JSON safely
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try cleaning or fallback extraction
            cleaned = response_text.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
        
        log_data = {k: v for k, v in data.items() if k != "attribute_value"}

        logger.info(
            "[JSON Switch Extraction Success]:\n%s",
            json.dumps(log_data, indent=2, ensure_ascii=False)
        )
        # Validate with Pydantic model
        validated = FFInspecterResponse(**data)

        ff_num = validated.attribute_value.split("-")[-1]
        nlpName = validated.nlpName.value
        input_text = validated.input_text
        keyword = validated.keyword
        if nlpName == "SwitchToWindowBasedOnTitle":
            nlpName = "SwitchToNewWindowBasedOnTitle"
        return ff_num, nlpName, input_text, keyword
    except ValidationError as e:
        logger.error(f"Pydantic Validation Error]: {e}")
        return -1, "None", "", ""
    except Exception as e:
        logger.error(f"[Error in match_nlp_via_llm]: {e}")
        return -1, "None", "", ""


# ---------------- SWITCH EXECUTION FUNCTIONS ---------------- #

def execute_switch_to_parent_window(driver, element, input, xpath_js):
    """Switch to the main/parent window (usually index 0)"""
    try:
        handles = driver.window_handles
        if handles:
            driver.switch_to.window(handles[0])
            logger.info("Successfully switched to parent window (Index 0)")
            return True
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch to parent window failed: {e}")
        return False

def execute_switch_to_new_window_if_url_contains_string(driver, element, input, xpath_js):
    """Switch to window if its URL contains string"""
    try:
        if not input:
            return False
        
        target = str(input).strip()
        current_handle = driver.current_window_handle
        
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if target in driver.current_url:
                logger.info(f"Switched to window with URL containing '{target}'")
                return True
        
        # Revert if not found
        driver.switch_to.window(current_handle)
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_window_based_on_url(driver, element, input, xpath_js):
    """Switch to window with robust URL matching"""
    try:
        if not input:
            return False
        
        target = str(input).strip()
        # Normalize target: strip protocols and trailing slashes
        match_target = target.lower().replace("https://", "").replace("http://", "").rstrip("/")
        
        current_handle = driver.current_window_handle
        handles = driver.window_handles
        
        for handle in handles:
            try:
                driver.switch_to.window(handle)
                url = driver.current_url.lower()
                # Use flexible matching
                if match_target in url:
                    logger.info(f"Successfully switched to window with URL: {url}")
                    time.sleep(1) # Focus stability
                    return True
            except Exception as e:
                logger.warning(f"Error inspecting handle {handle}: {e}")
                continue
        
        driver.switch_to.window(current_handle)
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_new_tab_based_on_title(driver, element, input, xpath_js):
    """Switch to tab based on Title with robust matching"""
    try:
        if not input:
            return False
        
        target = str(input).strip().lower()
        current_handle = driver.current_window_handle
        handles = driver.window_handles

        for handle in handles:
            try:
                driver.switch_to.window(handle)
                title = driver.title.lower()
                if target in title:
                    logger.info(f"Successfully switched to tab with Title: {title}")
                    time.sleep(1) # Focus stability
                    return True
            except Exception as e:
                logger.warning(f"Error inspecting handle {handle}: {e}")
                continue
        
        driver.switch_to.window(current_handle)
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_tab_based_on_url(driver, element, input, xpath_js):
    """Switch to tab based on URL with robust matching"""
    try:
        if not input:
            return False
        
        target = str(input).strip()
        # Normalize target: strip protocols and trailing slashes
        match_target = target.lower().replace("https://", "").replace("http://", "").rstrip("/")
        
        current_handle = driver.current_window_handle
        handles = driver.window_handles
        
        for handle in handles:
            try:
                driver.switch_to.window(handle)
                url = driver.current_url.lower()
                # Use flexible matching
                if match_target in url:
                    logger.info(f"Successfully switched to tab with URL: {url}")
                    time.sleep(1) # Focus stability
                    return True
            except Exception as e:
                logger.warning(f"Error inspecting handle {handle}: {e}")
                continue
        
        driver.switch_to.window(current_handle)
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_new_window_based_on_title(driver, element, input, xpath_js):
    """Switch to window with robust Title matching"""
    try:
        if not input:
            return False
        
        target = str(input).strip().lower()
        current_handle = driver.current_window_handle
        handles = driver.window_handles

        for handle in handles:
            try:
                driver.switch_to.window(handle)
                title = driver.title.lower()
                if target in title:
                    logger.info(f"Successfully switched to window with Title: {title}")
                    time.sleep(1) # Focus stability
                    return True
            except Exception as e:
                logger.warning(f"Error inspecting handle {handle}: {e}")
                continue
        
        driver.switch_to.window(current_handle)
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_window_if_title_contains_string(driver, element, input, xpath_js):
    """Switch to window if Title contains string"""
    try:
        if not input:
            return False
        
        target_partial = str(input).strip()
        current_handle = driver.current_window_handle

        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if target_partial in driver.title:
                logger.info(f"Switched to window with Title containing '{target_partial}'")
                return True
        
        driver.switch_to.window(current_handle)
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_frame_by_frame_index(driver, element, input, xpath_js):
    """Switch to frame by index"""
    try:
        if input is None or str(input).strip() == "":
            return False
        
        index = int(input)
        driver.switch_to.frame(index)
        logger.info(f"Switched to frame index {index}")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Switch frame failed: {e}")
        return False

def execute_switch_to_default_content(driver, element, input, xpath_js):
    """Switch to default content"""
    try:
        driver.switch_to.default_content()
        logger.info("Switched to default content")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_parent_of_the_frame(driver, element, input, xpath_js):
    """Switch to parent frame"""
    try:
        driver.switch_to.parent_frame()
        logger.info("Switched to parent frame")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_frame_by_frame_element(driver, element, input, xpath_js):
    """Switch to frame using the resolved web element"""
    try:
        if element:
            driver.switch_to.frame(element)
            logger.info("Switched to frame by element")
            return True
        logger.error("Element not provided for frame switch")
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch frame failed: {e}")
        return False

def execute_switch_to_frame_by_frame_name(driver, element, input, xpath_js):
    """Switch to frame by name or ID"""
    try:
        if not input:
            return False
        
        name_or_id = str(input).strip()
        driver.switch_to.frame(name_or_id)
        logger.info(f"Switched to frame '{name_or_id}'")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Switch frame failed: {e}")
        return False

def execute_switch_to_window_by_handle(driver, element, input, xpath_js):
    """Switch to window by handle"""
    try:
        if not input:
            return False
        
        handle = str(input).strip()
        driver.switch_to.window(handle)
        logger.info(f"Switched to window handle '{handle}'")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

def execute_switch_to_window_based_on_element(driver, element, input, xpath_js):
    """
    Experimental: Switch to window that contains this element.
    This is expensive as it requires checking all windows.
    """
    try:
        if not xpath_js:
            return False
        
        current_handle = driver.current_window_handle
        
        for handle in driver.window_handles:
            try:
                driver.switch_to.window(handle)
                # Check if element exists in this window
                if driver.find_elements(By.XPATH, xpath_js):
                    logger.info("Found window containing element")
                    return True
            except:
                continue
                
        # Revert if not found
        try:
            driver.switch_to.window(current_handle)
        except:
            pass
        return False
    except Exception as e:
        logger.error(f"[ERROR] Switch failed: {e}")
        return False

# Map NLP names to functions
EXECUTE_FUNCTIONS = {
    "SwitchToParentWindow": execute_switch_to_parent_window,
    "SwitchToNewWindowIfUrlContainsString": execute_switch_to_new_window_if_url_contains_string,
    "SwitchToWindowBasedOnURL": execute_switch_to_window_based_on_url,
    "SwitchToNewTabBasedOnTitle": execute_switch_to_new_tab_based_on_title,
    "SwitchToTabBasedOnUrl": execute_switch_to_tab_based_on_url,
    "SwitchToNewWindowBasedOnTitle": execute_switch_to_new_window_based_on_title,
    "SwitchToWindowIfTitleContainsString": execute_switch_to_window_if_title_contains_string,
    "SwitchToFrameByFrameIndex": execute_switch_to_frame_by_frame_index,
    "SwitchToDefaultContent": execute_switch_to_default_content,
    "SwitchToParentOfTheFrame": execute_switch_to_parent_of_the_frame,
    "SwitchToFrameByFrameElement": execute_switch_to_frame_by_frame_element,
    "SwitchToFrameByFrameName": execute_switch_to_frame_by_frame_name,
    "SwitchToWindowByHandle": execute_switch_to_window_by_handle,
    "SwitchToWindowBasedOnElement": execute_switch_to_window_based_on_element,
}

def execute_switch(driver, annotated_dom, simplified_dom, step, element_name, server_host, filtered_steps, serviceProvider, model, apiKey, service_accounts, auto_healing=None):
    from agent import WebStepExecutor
    webstepexecutor = WebStepExecutor(driver)
    
    # Locate AutoHealing if needed, though mostly for locator updates
    if auto_healing is None:
        from auto_healing import AutoHealing
        auto_healing = AutoHealing()
    
    ff_num, nlp_name, input_text, keyword = match_nlp_via_llm(
        simplified_dom, step, NLP_LIST, filtered_steps, serviceProvider, model, apiKey, service_accounts
    )
    
    xpath_path = ""
    xpath_js = ""
    iframe = [False,""]
    element = None
    
    # 1. Attempt to resolve element if NLP implies interaction with an element (e.g. frame by element)
    if ff_num not in [0, "0", -1, "-1"]:
        try:
            if annotated_dom:
                tree = html.fromstring(annotated_dom)
                target = tree.xpath(f"//*[@ff-inspect='Fire-Flink-{ff_num}']")
                if target:
                    element = target[0]
                    xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)
                    element, xpath_js, iframe = webstepexecutor._resolve_element(xpath_path, ff_num)
                    logger.info(f"Switch: Resolved element xpath: {xpath_js}")
                else:
                    xpath_path = ""
        except Exception as e:
            logger.error(f"Error extracting xpath in switch: {e}")
            xpath_path = ""

    # 2. Check match validity
    if not nlp_name or nlp_name not in EXECUTE_FUNCTIONS:
        logger.info(f"No matching Switch NLP for step: {step}")
        return False, ff_num, nlp_name, keyword, input_text, xpath_path, xpath_js, iframe
    
    # 3. Heal locator if element was found
    if element:
        try:
            auto_healing.send_locator_request(annotated_dom, f"Fire-Flink-{ff_num}", element_name, server_host, source="switch")
        except:
            pass

    # 4. Execute the switch function
    func = EXECUTE_FUNCTIONS[nlp_name]
    
    result = func(driver, element, input_text, xpath_js)
    logger.info(f"Executing Switch Function: {nlp_name}, success: {result}")
    
    return result, ff_num, nlp_name, keyword, input_text, xpath_path, xpath_js, iframe
