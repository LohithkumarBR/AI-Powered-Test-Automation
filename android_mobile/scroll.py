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
from xml_extractor import Extractor
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Helper function to check if app is force-closed
# def is_app_force_closed(driver): ... # Removed duplicate logic

class nlp_name(Enum):
    MOB_SwipeToElement = "MOB_SwipeToElement"
    MOB_SwipeUpToElement = "MOB_SwipeUpToElement"
    MOB_SwipeDownToElement = "MOB_SwipeDownToElement"
    MOB_SwipeLeftToElement = "MOB_SwipeLeftToElement"
    MOB_SwipeRightToElement = "MOB_SwipeRightToElement"
    MOB_SwipeNTimes = "MOB_SwipeNTimes"
    MOB_Builtin_Swipe = "MOB_Builtin_Swipe"
    MOB_SwipeToElementForMWeb = "MOB_SwipeToElementForMWeb"
    MOB_SwipeDirectionNTimes = "MOB_SwipeDirectionNTimes"
    MOB_SwipeUsingReferenceElement = "MOB_SwipeUsingReferenceElement"

class FFInspecterResponse(BaseModel):
    attribute_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element. Return Fire-Flink-0 if not applicable.",
        examples=["Fire-Flink-x"]
    )
    nlpName: nlp_name = Field(..., description="The selected NLP name.", examples=["x"])
    
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
    type: str = Field(
        ...,
        description="The type of the UI element (e.g.Button,Link,Text Field,Text,Image,Checkbox,Radio Button,Icon,Toggle Button).",
        examples=["x"]
    )
    num_of_scrolls: int = Field(
        0,
        description="The number of scrolls to perform.",
        examples=["x"]
    )
    direction: str = Field(
        "",
        description="The direction of the scroll (up, down, left, right).",
        examples=["x"]
    )

# NLP List from nlp_sanitize.py related to scroll/swipe
NLP_STRING = (
    "MOB_SwipeToElement,MOB_SwipeUpToElement,MOB_SwipeDownToElement,"
    "MOB_SwipeLeftToElement,MOB_SwipeRightToElement,MOB_SwipeNTimes,"
    "MOB_Builtin_Swipe,MOB_SwipeToElementForMWeb,MOB_SwipeDirectionNTimes,MOB_SwipeUsingReferenceElement"
)
NLP_LIST = NLP_STRING.split(",")

def match_scroll_nlp_via_llm(simplified_dom, step, nlp_list, filtered_steps, serviceProvider, model, apiKey):
    prompt = f"""
You are an intelligent assistant that extracts structured mobile scroll/swipe action data.
Given the step: "{step}", the simplified DOM (optional for scroll context): {json.dumps(simplified_dom, ensure_ascii=False)}, and the list of NLP names: {nlp_list}.

Select the perfect matching NLP name from the list that best fits the step's intent.

Return **only valid JSON** in the following format:
{{
  "attribute_value": "Fire-Flink-x", 
  "nlpName": "x",
  "input_text": "x",
  "keyword": "x",
  "type": "x",
  "num_of_scrolls": "x",
  "direction": "x"
}}

Rules:
- nlpName must be exactly one from the provided list.
- Use context from the steps : {filtered_steps}, keyword and json to search for FF-inspecter.
- If direction is not specified, then match to "MOB_SwipeToElement".
- If direction is Not specified and element is not specified, then match to "MOB_SwipeNTimes".
- If direction is specified and element is not specified, then match to "MOB_SwipeDirectionNTimes".
- If step has a reference element, then match to "MOB_SwipeUsingReferenceElement". and give input_text: "reference element -> <next element>"
example: swipe up to "Contact Us" using "Settings" as reference.
        input_text: "Settings -> Contact Us"
- If the step is saying 'up to' or 'till' element, then return the number of scrolls as 0. and also don't take 'up' as direction in this case, give direction as "none" ".
- **Extraction**:
    - **`input_text`: The target element in the step.e.g., "swipe to submit text",then input text must be "submit",Dont include its type in input_text like text,button,icon etc...Leave empty if just swiping N times.**
    - `keyword`: Crucial keyword from step (e.g., "Settings").
    - `num_of_scrolls`: Extract count if specified (e.g., "scroll 3 times"). Default to 0 if not specified but action implies generic scroll.
    - `direction`: "up", "down", "left", "right". Infer from step (e.g., "Scroll down" -> "down"). If direction is not specified, default direction to "none".
    - `attribute_value`: If an element is visible and matches the target, provide its FF-inspecter. Otherwise "Fire-Flink-0".
    - `type`: Element type (Text, Button, etc.).

- Respond with valid JSON only.
"""
    usage = {}
    try:
        # Call Groq LLM using your wrapper
        response_text, usage = call_grok_llm(prompt, serviceProvider, model, apiKey)

        # Parse JSON safely
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try cleaning or fallback extraction
            cleaned = response_text.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
        
        logger.info("[JSON Scroll Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))

        # Validate with Pydantic model
        validated = FFInspecterResponse(**data)

        ff_num = validated.attribute_value.split("-")[-1]
        nlpName = validated.nlpName.value
        input_text = validated.input_text
        keyword = validated.keyword
        element_type = validated.type
        num_of_scrolls = validated.num_of_scrolls
        direction = validated.direction

        return ff_num, nlpName, input_text, keyword, element_type, num_of_scrolls, direction, usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]

    except ValidationError as e:
        logger.error(f"[Pydantic Validation Error]: {e}")
        return -1, None, "", "", "", 0, "", usage.get("input_tokens",0), usage.get("output_tokens",0), usage.get("total_tokens",0)

    except Exception as e:
        logger.error(f"[Error in match_scroll_nlp_via_llm]: {e}")
        return -1, None, "", "", "", 0, "", usage.get("input_tokens",0), usage.get("output_tokens",0), usage.get("total_tokens",0)


def hide_keyboard_ios(driver):
    # 1. Try Done
    try:
        driver.hide_keyboard(strategy="pressKey", key="Return")
        time.sleep(0.3)
        logger.info("Keyboard hidden using Done key")
        return
    except Exception:
        pass


def _perform_swipe(driver, direction, duration=800):
    window = driver.get_window_size()
    width = window["width"]
    height = window["height"]

    mid_x = width * 0.5

    if direction == "up":   # show lower elements → swipe from bottom to top
        start_x = mid_x
        start_y = height * 0.6
        end_x   = mid_x
        end_y   = height * 0.1

    elif direction == "down":   # show upper elements → swipe from top to bottom
        start_x = mid_x
        start_y = height * 0.4
        end_x   = mid_x
        end_y   = height * 0.8

    elif direction == "left":
        start_x = width * 0.8
        start_y = height * 0.5
        end_x   = width * 0.2
        end_y   = height * 0.5

    elif direction == "right":
        start_x = width * 0.2
        start_y = height * 0.5
        end_x   = width * 0.8
        end_y   = height * 0.5

    else:
        start_x = mid_x
        start_y = height * 0.8
        end_x   = mid_x
        end_y   = height * 0.2

    driver.swipe(int(start_x), int(start_y), int(end_x), int(end_y), duration)

# def _perform_swipe(driver, direction):
#     try:
#         size = driver.get_window_size()
#         width = size["width"]
#         height = size["height"]

#         driver.execute_script(
#             "mobile: scrollGesture",
#             {
#                 "left": 0,
#                 "top": int(height * 0.40),      # main content area
#                 "width": width,
#                 "height": int(height * 0.70),
#                 "direction": direction,        # "up" or "down"
#                 "percent": 0.85,               # scroll length
#                 "avoidChildWait": True         # 💥 prevent animation wait
#             }
#         )

#     except Exception as e:
#         print(f"[Scroll Error] {e}")




        


def find_element_in_dom(driver, text, attempt):
    """
    Helper to search for text in the current DOM using Extractor and finding logic.
    Returns (element, xpath) or (None, "")
    """

    extractor = Extractor(driver)
    raw_dom = extractor.get_ui_dump()
    keywords = text.lower().split()
    
    # We use a simplified version of logic from executor.scroll_until_element
    try:
        annotated_dom, simplified_json = extractor.annotate_and_simplify_dom(keywords, raw_dom, attempt+100) # 999 as dummy step index
    except ValueError as e:
        return None, ""

    def exact_sequence_match(value, words):
        v = value.lower()
        pattern = r"\b" + r"\b\s*".join(re.escape(w) for w in words) + r"\b"
        return re.search(pattern, v) is not None

    def match_node(node, words):
        text = (node.get("label") or "").lower()
        desc = (node.get("name") or "").lower()
        value=(node.get("value") or "").lower()

        if exact_sequence_match(text, words):
            return True

        if exact_sequence_match(desc, words):
            return True
        if exact_sequence_match(value, words):
            return True

        return False



    matches = []

    for group in simplified_json:          # each group is a list
        for node in group:                 # iterate inside the group
            if match_node(node, words=keywords):
                matches.append(node)      # add full group
                break  
             
    if not matches:
        return None, "",raw_dom
    
    # Found match
    logger.info("Found match: %s", matches[0])
    num = matches[0]["FF-inspecter"].split("-")[-1]
    tree = etree.fromstring(annotated_dom.encode('utf-8'))
    target = tree.xpath(f"//*[@FF-inspecter='Fire-Flink-{num}']")
    if target:
        ele = target[0]
        xpath = etree.ElementTree(tree).getpath(ele)
        xpath= xpath.replace("/AppiumAUT", "")
        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            return element, xpath,raw_dom
        except:
             return None, "",raw_dom
    return None, "",raw_dom


def scroll_until_element(executor,driver, text, max_scrolls, direction):
    # If text is empty, just scroll once? No, this function purpose is to find something.
    if not text:
        return False, ""
    prev_page_source = ""
    curr_page_source = "a"
    # 2. Loop scroll
    for attempt in range(1, max_scrolls + 1):
        # Check if app was force-closed before each scroll attempt
        if executor.has_been_force_closed():
            logger.info("App force-closed after back action")
            success = False
            return success, ""
        
        logger.info(f"Scroll attempt {attempt} for '{text}' (direction: {direction})")
        if direction.lower() in ["up","down"]:
            _perform_swipe(driver, direction)
            time.sleep(1)
        elif direction.lower() in ["left","right"]:
            try:
                hsv = driver.find_element(
                    AppiumBy.CLASS_NAME,
                    "android.widget.HorizontalScrollView"
                )
                rect = hsv.rect
                y = rect["y"] + rect["height"] // 2
                if direction == "left":
                    start_x = rect["x"] + int(rect["width"] * 0.8)
                    end_x   = rect["x"] + int(rect["width"] * 0.2)
                elif direction == "right":
                    start_x = rect["x"] + int(rect["width"] * 0.2)
                    end_x   = rect["x"] + int(rect["width"] * 0.8)
                else:
                    raise ValueError("direction must be 'left' or 'right'")
                driver.swipe(
                    int(start_x),
                    int(y),
                    int(end_x),
                    int(y),
                    800
                )
                logger.info(f"Performed horizontal swipe on HorizontalScrollView")
            except Exception as e:
                _perform_swipe(driver, direction)
                time.sleep(1)
        
        
        el, xpath,curr_page_source = find_element_in_dom(driver, text, attempt)
        if el:
            logger.info(f"Found '{text}' after {attempt} scrolls")
            return el, xpath

        if prev_page_source == curr_page_source:
            logger.info("No DOM change detected, stopping scroll")
            break

        prev_page_source = curr_page_source
        # time.sleep(1)
        
        # el, xpath,curr_page_source = find_element_in_dom(driver, text, attempt)
        # if el:
        #     logger.info(f"Found '{text}' after {attempt} scrolls")
        #     return el, xpath
            
    return False, ""

def execute_swipe_n_times(executor,driver, input_text, num_of_scrolls, direction):
    # This just swipes N times.
    count = num_of_scrolls 
    # If direction not set, default to "up" (scroll down)
    d = direction if direction.lower() != "none" else "up"
    
    for i in range(count):
        # Check if app was force-closed before each swipe
        if executor.has_been_force_closed():
            logger.info(f"App force-closed during swipe {i+1}/{count}")
            return False, ""
        logger.info(f"Swiping {d} ({i+1}/{count})")
        if d.lower() in ["up","down"]:
            _perform_swipe(driver, d)
            time.sleep(1)
        elif d.lower() in ["left","right"]:
            try:
                hsv = driver.find_element(
                    AppiumBy.CLASS_NAME,
                    "android.widget.HorizontalScrollView"
                )
                rect = hsv.rect
                y = rect["y"] + rect["height"] // 2
                if d == "left":
                    start_x = rect["x"] + int(rect["width"] * 0.8)
                    end_x   = rect["x"] + int(rect["width"] * 0.2)
                elif d == "right":
                    start_x = rect["x"] + int(rect["width"] * 0.2)
                    end_x   = rect["x"] + int(rect["width"] * 0.8)
                else:
                    raise ValueError("direction must be 'left' or 'right'")
                driver.swipe(
                    int(start_x),
                    int(y),
                    int(end_x),
                    int(y),
                    800
                )
                logger.info(f"Performed horizontal swipe on HorizontalScrollView")
            except Exception as e:
                _perform_swipe(driver, d)
                time.sleep(1)
    return True, ""

def execute_swipe_to_element(executor,driver, input_text, num_of_scrolls, direction):
    # Generic swipe to element. Default direction "up" (scroll down) if not provided.
    d = direction if direction.lower() != "none" else "up"
    max_s = num_of_scrolls
    res, xpath = scroll_until_element(executor,driver, input_text, max_s, d)
    return bool(res),xpath

def execute_swipe_up_to_element(executor,driver, input_text, num_of_scrolls, direction):
    # Specifically swipe UP (scroll down)
    max_s = num_of_scrolls
    nlp_name = "MOB_SwipeUpToElement"
    res, xpath = scroll_until_element(executor,driver, input_text, max_s, "up")
    return bool(res),xpath

def execute_swipe_down_to_element(executor,driver, input_text, num_of_scrolls, direction):
    # Specifically swipe DOWN (scroll up)
    max_s = num_of_scrolls
    res, xpath = scroll_until_element(executor,driver, input_text, max_s, "down")
    return bool(res),xpath

def execute_swipe_left_to_element(executor,driver, input_text, num_of_scrolls, direction):
    max_s = num_of_scrolls
    res, xpath = scroll_until_element(executor,driver, input_text, max_s, "left")
    return bool(res),xpath

def execute_swipe_right_to_element(executor,driver, input_text, num_of_scrolls, direction):
    max_s = num_of_scrolls
    res, xpath = scroll_until_element(executor,driver, input_text, max_s, "right")
    return bool(res),xpath

def execute_swipe_using_reference_element(executor,driver, input_text, num_of_scrolls, direction):
    try:
        reference, target = map(str.strip, input_text.split("->"))
    except:
        logger.error("Input for MOB_SwipeUsingReferenceElement must be in 'Reference -> Target' format")
        return False,""

    logger.info(f"[SwipeUsingReference] Reference: '{reference}'  Target: '{target}'")

    d = direction if direction.lower() != "none" else "down"

    ref_found_once = False

    for attempt in range(1, num_of_scrolls + 1):
        logger.info(f"Swipe attempt {attempt} to find Target '{target}' (direction={d})")

        # After swipe refresh UI
        _perform_swipe(driver, d)
        time.sleep(1)

        # Check if target visible
        target_el, _ ,_= find_element_in_dom(driver, target,attempt)
        if target_el:
            logger.info(f"Target '{target}' found after {attempt} swipes")
            return True

        # If not target, check reference (for direction confirmation)
        if not ref_found_once:
            ref_el, _ = find_element_in_dom(driver, reference,attempt)
            if ref_el:
                ref_found_once = True
                logger.info(f"Reference '{reference}' is visible — continuing swipes to find target")

    logger.info(f"Target '{target}' NOT FOUND after {num_of_scrolls} swipes")
    return False,""


# Mapping
EXECUTE_FUNCTIONS = {
    "MOB_SwipeNTimes": execute_swipe_n_times,
    "MOB_Builtin_Swipe": execute_swipe_n_times, 
    "MOB_SwipeToElement": execute_swipe_up_to_element,
    "MOB_SwipeUpToElement": execute_swipe_up_to_element,
    "MOB_SwipeDownToElement": execute_swipe_down_to_element,
    "MOB_SwipeLeftToElement": execute_swipe_left_to_element,
    "MOB_SwipeRightToElement": execute_swipe_right_to_element,
    "MOB_SwipeToElementForMWeb": execute_swipe_to_element, 
    "MOB_SwipeDirectionNTimes": execute_swipe_n_times,
    "MOB_SwipeUsingReferenceElement": execute_swipe_using_reference_element,
}


def execute_scroll(executor,driver, annotated_dom, simplified_dom, step, filtered_steps, serviceProvider, model, apiKey):
    ff_num, nlp_name, input_text, keyword, element_type, num_of_scrolls, direction, in_tok, out_tok, tot_tok = match_scroll_nlp_via_llm(
     simplified_dom, step, NLP_LIST, filtered_steps, serviceProvider, model, apiKey
    )
    if nlp_name =="MOB_SwipeToElement":
        nlp_name ="MOB_SwipeUpToElement"
    elif nlp_name == "MOB_SwipeNTimes":
        nlp_name="MOB_SwipeDirectionNTimes"
    num_of_scrolls = int(num_of_scrolls)
    if num_of_scrolls == 0:
        num_of_scrolls = 30

    xpath_path = ""
    
    if not nlp_name or nlp_name not in EXECUTE_FUNCTIONS:
        logger.info(f"nlp_name: {nlp_name} No matching Scroll NLP for step: {step}")
        return False, ff_num, nlp_name, keyword, input_text, xpath_path, element_type, num_of_scrolls, direction, in_tok, out_tok, tot_tok

    func = EXECUTE_FUNCTIONS[nlp_name]
    
    try:
        result,xpath_path = func(executor, driver, input_text, num_of_scrolls, direction)
    except Exception as e:
        logger.error(f"Error executing scroll action {nlp_name}: {e}")
        result = False
        
    return result, ff_num, nlp_name, keyword, input_text, xpath_path, element_type, num_of_scrolls, direction, in_tok, out_tok, tot_tok
