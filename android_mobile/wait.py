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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class nlpWait_enum(Enum):
    MOB_WaitTillPresenceOfElement = "MOB_WaitTillPresenceOfElement"
    MOB_WaitTillElementIsSelected = "MOB_WaitTillElementIsSelected"
    MOB_WaitTillElementHasText = "MOB_WaitTillElementHasText"
    MOB_WaitTillElementIsEnabled = "MOB_WaitTillElementIsEnabled"
    MOB_WaitTillElementIsVisible = "MOB_WaitTillElementIsVisible"
    MOB_WaitTillElementContainsText = "MOB_WaitTillElementContainsText"
    MOB_WaitTillAttributeOfElementContainsString = "MOB_WaitTillAttributeOfElementContainsString"
    MOB_WaitTillAllElementsAreInvisible = "MOB_WaitTillAllElementsAreInvisible"
    MOB_WaitTillElementIsInvisible = "MOB_WaitTillElementIsInvisible"
    MOB_WaitTillElementIsClickable = "MOB_WaitTillElementIsClickable"
    MOB_WaitTillAttributeOfElementIsString = "MOB_WaitTillAttributeOfElementIsString"
    MOB_WaitTillPresenceOfAllElements = "MOB_WaitTillPresenceOfAllElements"
    MOB_WaitTillStalenessOfElement = "MOB_WaitTillStalenessOfElement"
    MOB_WaitAndSendKeys = "MOB_WaitAndSendKeys"
    MOB_WaitAndClick = "MOB_WaitAndClick"
    Sleep = "Sleep"


class FFInspecterResponse(BaseModel):
    attribute_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element.",
        examples=["Fire-Flink-x"]
    )

    nlpName:nlpWait_enum = Field(..., description="The selected NLP name.", examples=["x"])

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

# Parse NLP list from the string
WAIT_NLP_STRING = (
"MOB_WaitTillPresenceOfElement","MOB_WaitTillElementIsSelected","MOB_WaitTillElementHasText","MOB_WaitTillElementIsEnabled",
"MOB_WaitTillElementIsVisible","MOB_WaitTillElementContainsText","MOB_WaitTillAttributeOfElementContainsString","MOB_WaitTillAllElementsAreInvisible",
"MOB_WaitTillElementIsInvisible","MOB_WaitTillElementIsClickable","MOB_WaitTillAttributeOfElementIsString","MOB_WaitTillPresenceOfAllElements",
"MOB_WaitTillStalenessOfElement","MOB_WaitAndSendKeys","MOB_WaitAndClick","Sleep"
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
  "input_text":"x"
  "keyword": "x",
  "element_type": "x"
}}
Rules:
- nlpName must be exactly one from the provided list.
- For steps like wait for some time or wait for 5 secondes. give input in number only and nlpName should be "Sleep".
- Use context from the steps : {filtered_steps}, keyword and json to search for FF-inspecter.
- **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
- For some steps you can see two inputs but you need to uderstand step and send the requred input_text.
        ex: Wait until the flights has the flight text
        here keyword : "flights" , input : flight
- Extract input_text from the step, if you can't find any input text in the step, return keyword as input_text.
- Extract keyword from the step, if the step contains any keyword.
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
        logger.info("[JSON Wait Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))

        #  Validate with Pydantic model
        validated = FFInspecterResponse(**data)
        # logger.info(f"[Validation Success]: {validated}")

        ff_num = validated.attribute_value.split("-")[-1]
        nlpName = validated.nlpName.value
        input_text = validated.input_text
        keyword = validated.keyword
        element_type = validated.element_type

        return ff_num,nlpName,input_text,keyword, element_type,usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
    except ValidationError as e:
        logger.error(f" Pydantic Validation Error]: {e}")
        return -1, None, "", "","",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]

    except Exception as e:
        logger.error(f"[ Error in ff_inspecter_num_extractor]: {e}")
        return -1, None, "", "","",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
            

# ------------------- WAIT FUNCTIONS -------------------

def execute_wait_till_presence_of_element(driver, element, input):
    try:
        locator_type, locator_value = input
        value = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((locator_type, locator_value))
        )
        return True, value
    except:
        return False, None


def execute_wait_till_element_is_selected(driver, element, input):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_selected(element))
        return True, True
    except:
        return False, None


def execute_wait_till_element_has_text(driver, element, input):
    try:
        expected_text = input
        WebDriverWait(driver, 10).until(lambda d: element.text == expected_text)
        return True, element.text
    except:
        return False, None


def execute_wait_till_element_is_enabled(driver, element, input):
    try:
        WebDriverWait(driver, 10).until(lambda d: element.is_enabled())
        return True, True
    except:
        return False, None


def execute_wait_till_element_is_visible(driver, element, input):
    try:
        WebDriverWait(driver, 10).until(EC.visibility_of(element))
        return True, True
    except:
        return False, None


def execute_wait_till_element_contains_text(driver, element, input):
    try:
        expected_text = input
        WebDriverWait(driver, 10).until(lambda d: expected_text in element.text)
        return True, element.text
    except:
        return False, None


def execute_wait_till_attribute_of_element_contains_string(driver, element, input):
    try:
        attr, expected_value = input
        WebDriverWait(driver, 10).until(
            lambda d: expected_value in element.get_attribute(attr)
        )
        return True, element.get_attribute(attr)
    except:
        return False, None


def execute_wait_till_element_is_invisible(driver, element, input):
    try:
        WebDriverWait(driver, 10).until(EC.invisibility_of_element(element))
        return True, True
    except:
        return False, None


def execute_wait_till_element_is_clickable(driver, element, input):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element))
        return True, True
    except:
        return False, None


def execute_wait_till_attribute_of_element_is_string(driver, element, input):
    try:
        attr, expected_value = input
        WebDriverWait(driver, 10).until(
            lambda d: element.get_attribute(attr) == expected_value
        )
        return True, element.get_attribute(attr)
    except:
        return False, None


def execute_wait_till_presence_of_all_elements(driver, element, input):
    try:
        locator_type, locator_value = input
        value = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((locator_type, locator_value))
        )
        return True, value
    except:
        return False, None


def execute_wait_till_staleness_of_element(driver, element, input):
    try:
        WebDriverWait(driver, 10).until(EC.staleness_of(element))
        return True, True
    except:
        return False, None


def execute_wait_and_sendkeys(driver, element, input):
    try:
        text = input
        WebDriverWait(driver, 10).until(EC.visibility_of(element))
        element.send_keys(text)
        return True, text
    except:
        return False, None


def execute_wait_and_click(driver, element, input):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element))
        element.click()
        return True, True
    except:
        return False, None


def execute_sleep(driver, element, input):
    try:
        seconds = int(input)
        time.sleep(seconds)
        logger.info(f"Sleeping for {seconds} seconds.")
        return True, seconds
    except:
        return False, None



# Map NLP names to functions
EXECUTE_Wait_FUNCTIONS = {
    "MOB_WaitTillPresenceOfElement": execute_wait_till_presence_of_element,
    "MOB_WaitTillElementIsSelected": execute_wait_till_element_is_selected,
    "MOB_WaitTillElementHasText": execute_wait_till_element_has_text,
    "MOB_WaitTillElementIsEnabled": execute_wait_till_element_is_enabled,
    "MOB_WaitTillElementIsVisible": execute_wait_till_element_is_visible,
    "MOB_WaitTillElementContainsText": execute_wait_till_element_contains_text,
    "MOB_WaitTillAttributeOfElementContainsString": execute_wait_till_attribute_of_element_contains_string,
    "MOB_WaitTillElementIsInvisible": execute_wait_till_element_is_invisible,
    "MOB_WaitTillElementIsClickable": execute_wait_till_element_is_clickable,
    "MOB_WaitTillAttributeOfElementIsString": execute_wait_till_attribute_of_element_is_string,
    "MOB_WaitTillPresenceOfAllElements": execute_wait_till_presence_of_all_elements,
    "MOB_WaitTillStalenessOfElement": execute_wait_till_staleness_of_element,
    "MOB_WaitAndSendKeys": execute_wait_and_sendkeys,
    "MOB_WaitAndClick": execute_wait_and_click,
    "Sleep": execute_sleep
}



def execute_waitAction(driver ,annotated_dom, simplified_dom, step,filtered_steps, serviceProvider, model, apiKey,service_accounts):
    ff_num, nlp_name,input_text, keyword, element_type, input_tokens,output_tokens,total_tokens = match_nlp_via_llm(simplified_dom, step, WAIT_NLP_STRING,filtered_steps, serviceProvider, model, apiKey,service_accounts)
    xpath_path = ""
    if nlp_name == "MOB_WaitTillAllElementsAreInvisible":
        logger.info(f"Get result non-execution for {nlp_name}: {True}")
        return True, 0, nlp_name , input_text, xpath_path,keyword, element_type, input_tokens,output_tokens,total_tokens
    
    if not nlp_name or nlp_name not in EXECUTE_Wait_FUNCTIONS  :
        logger.info(f"No matching Execution NLP for step: {step} and nlp is {nlp_name}")
        return False, ff_num, nlp_name , input_text,keyword, xpath_path, element_type, input_tokens,output_tokens,total_tokens
    
    

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


    func = EXECUTE_Wait_FUNCTIONS[nlp_name]

    
    if nlp_name in ["MOB_WaitTillPresenceOfElement", "MOB_WaitTillPresenceOfAllElements"]:
        xpath = (AppiumBy.XPATH, xpath_path)
        result,value = func(driver, element, xpath)
    else:
        result,value = func(driver, element, input_text)

    logger.info(f"Wait result for {nlp_name}: {result}")

    action = nlp_name

    return result ,ff_num, action , input_text,keyword, xpath_path, element_type, input_tokens,output_tokens,total_tokens
