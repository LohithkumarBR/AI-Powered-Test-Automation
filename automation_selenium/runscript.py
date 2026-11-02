import json
import requests
from nlp_sanitize import *
from LLMcall import call_grok_llm, get_total_tokens,reset_tokens, reset_count
from vision import get_total_tokens_openai,reset_tokens_openai
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding="utf-8")

def call_fireflink_api(headers, body, url):
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        
        # Handle non-200 responses
        if response.status_code != 200:
            try:
                error_content = response.json()
            except Exception:
                error_content = response.text
            raise Exception(f"HTTP Error {response.status_code}: {error_content}")
        
        # Return JSON response
        return response.json()
    
    except requests.exceptions.Timeout as e:
        raise e
    
    except requests.exceptions.ConnectionError as ce:
        raise ce
    
    except requests.exceptions.RequestException as re:
        raise re
    
    except Exception as e:
        raise e
 
def run_script_from_payload(result, payload, total_time):
    try:
        step_data = json.loads(result) if isinstance(result, str) else result
        step_data = normalize_stepdata(step_data=step_data)
        step_data = sanitize_steps(steps=step_data)
        
        if not step_data or "openbrowser" not in step_data[0].get("nlpName", "").lower():
            open_browser_step = {
                "nlpName": "OpenBrowser",
                "elementsData": [],
                "stepInputs": []
            }
            step_data.insert(0, open_browser_step)
        
        # if not step_data or "closebrowser" not in step_data[-1].get("nlpName", "").lower():
        #     close_browser_step = {
        #         "nlpName": "CloseBrowser",
        #         "elementsData": [],
        #         "stepInputs": []
        #     }
        #     step_data.append(close_browser_step)

    except Exception as e:
        logger.info(f"Failed to parse final llm data: {e}")
        return
    
    total_tokens_ = get_total_tokens() + get_total_tokens_openai()

    logger.info("sending script payload to fireflink")
    body = {
        "stepData": step_data,
        "scriptName": payload.get("scriptName"),
        "scriptType": payload.get("scriptType"),
        #"pageId": payload.get("pageId"),
        #"pageName": payload.get("pageName"),
        "projectId": payload.get("projectId"),
        "testCaseId": payload.get("testCaseId"),
        "promptId": payload.get("promptId"),
        "pageDetails":payload.get("pageDetails"),
        "generatedBy": payload.get("generatedBy"),
        "webSocketId": payload.get("webSocketId"),
        "licenseType": payload.get("licenseType"),
        "licenseId": payload.get("licenseId"),
        "userId": payload.get("userId"),
        "topic": payload.get("topic"),
        "projectType":payload.get("projectType"),
        "tokensConsumed": total_tokens_,
    }

    # logger.info("Body for the payload is:\n%s", json.dumps(body, indent=2))
    logger.info(f"Total Tokens: {get_total_tokens()}")
    logger.info(f"OpenAI Total Tokens: {get_total_tokens_openai()}")
    logger.info(f"Total Time taken for script generation: {total_time} seconds")

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "projectId": payload.get("projectId"),
        "Authorization": f"Bearer {payload.get('token')}"
    }
    
    url = f"{payload.get('serverHost')}/project/optimize/v3/bulk/scripts/script-payload"
    
    reset_count()
    reset_tokens_openai()
    reset_tokens()
    try:
        final_result = call_fireflink_api(headers, body, url)
        logger.info("Successfully sent payload to FireFlink API")
        logger.info(final_result)
        return final_result
    except Exception as e:
        logger.error(f"Failed to send payload to FireFlink API: {e}")
        raise e

def error_message_payload(result, error, error_description,raw_error, payload, error_step=None):
    step_data = []
    try:
        step_data = json.loads(result) if isinstance(result, str) else result
        step_data = normalize_stepdata(step_data=step_data)
        step_data = sanitize_steps(steps=step_data)

        # logger.info(error_step)

        # Ensure error_step is a list for processing
        if error_step:
            # Normalize action name in error_step
            if error_step:
                ACTION_MAP = {
                    "click": "Click",
                    "doubleclick": "DoubleClick",
                    "rightclick": "RightClick",
                    "enter": "SendKeys",
                    "sendkeys": "SendKeys",
                    "upload": "UploadFilePathUsingRobot",
                    "wait": "Sleep",
                    "sleep": "Sleep",
                    "maximize": "MaximizeBrowser",
                    "maximizebrowser": "MaximizeBrowser",
                    "scroll": "ScrollToElement",
                    "scrolltoelement": "ScrollToElement",
                    "drag_and_drop": "Builtin_DragAndDropToElement",
                    "builtin_draganddroptoelement": "Builtin_DragAndDropToElement",
                    "navigate": "NavigateToURL",
                    "navigatetourl": "NavigateToURL",
                    "back": "NavigateBack",
                    "navigateback": "NavigateBack",
                    "open": "OpenBrowser",
                    "openbrowser": "OpenBrowser",
                    "close": "CloseBrowser",
                    "closebrowser": "CloseBrowser",
                    "enterdatatoalert": "EnterDataToAlert",
                    "clickokonalertpopup": "ClickOkOnAlertPopup",
                    "clickcancelonalertpopup": "ClickCancelOnAlertPopup",
                    "verifyalertpopupisplayed": "VerifyAlertPopupIsDisplayed",
                    "gettextpresentonalertpopup": "GetTextPresentOnAlertPopup",
                    "verifyalertpopupmessagecontainsstring": "VerifyAlertPopupMessageContainsString",
                    "verifytextpresentonalertpopup": "VerifyTextPresentOnAlertPopup"
                }
                
                nlp_name = error_step.get("nlpName", "")
                if nlp_name.lower() in ACTION_MAP:
                    error_step["nlpName"] = ACTION_MAP[nlp_name.lower()]
                
            if isinstance(error_step, dict):
                error_step_to_process = [error_step]
            elif isinstance(error_step, str):
                try:
                    error_step_to_process = json.loads(error_step)
                    if isinstance(error_step_to_process, dict):
                        error_step_to_process = [error_step_to_process]
                except:
                    error_step_to_process = []
            else:
                error_step_to_process = error_step
            
            error_step_to_process = normalize_stepdata(error_step_to_process)
            error_step_to_process = sanitize_steps(error_step_to_process)
            error_step = error_step_to_process[0] if error_step_to_process else None
                    
        else:
            error_step = None
        
        if not step_data or "openbrowser" not in step_data[0].get("nlpName", "").lower():
            open_browser_step = {
                "nlpName": "OpenBrowser",
                "elementsData": [],
                "stepInputs": []
            }
            step_data.insert(0, open_browser_step)

    except Exception as e:
        logger.info(f"Failed to parse final llm data: {e}")
        if not step_data:
             step_data = [{
                "nlpName": "OpenBrowser",
                "elementsData": [],
                "stepInputs": []
            }]
            

    logger.info("sending error message payload to fireflink")
    if not isinstance(payload, dict):
        payload = {}

    body = {
        "stepData": step_data,
        "scriptName": payload.get("scriptName"),
        "scriptType": payload.get("scriptType"),
        "projectId": payload.get("projectId"),
        "testCaseId": payload.get("testCaseId"),
        "promptId": payload.get("promptId"),
        "pageDetails":payload.get("pageDetails"),
        "generatedBy": payload.get("generatedBy"),
        "webSocketId": payload.get("webSocketId"),
        "licenseType": payload.get("licenseType"),
        "licenseId": payload.get("licenseId"),
        "userId": payload.get("userId"),
        "topic": payload.get("topic"),
        "projectType":payload.get("projectType"),
        "tokensConsumed": get_total_tokens() + get_total_tokens_openai(),
        "error":{
            "errorType":error,
            "aiErrorDescription": error_description,
            "rawError": raw_error,
            "failedStep": error_step if error_step else None
        }
    }
    # logger.info("Body for the error payload is:\n%s", json.dumps(body, indent=2))

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "projectId": payload.get("projectId"),
        "Authorization": f"Bearer {payload.get('token')}"
    }
    url = f"{payload.get('serverHost')}/project/optimize/v3/bulk/scripts/script-payload"
    reset_tokens_openai()
    reset_tokens()
    reset_count()
    try:
        final_result = call_fireflink_api(headers, body, url)
        logger.info("Successfully sent payload to FireFlink API")
        logger.info(final_result)
        return final_result
    except Exception as e:
        logger.error(f"Failed to send payload to FireFlink API: {e}")
        raise e




def sanitize_steps(steps, rules=nlp_sanitize_list):
    """
    Sanitize steps based on rules.
    - elementsData: 0 (empty list) | 1 (keep as-is)
    - stepInputs: 0 (empty list) | [types] (cast values accordingly)
    """

    type_casts = {
        "string": str,
        "int": int,
        "float": float,
        "boolean": lambda x: bool(x) if isinstance(x, bool) else str(x).lower() in ("true", "1", "yes")
    }

    sanitized = []
    for step in steps:
        nlp_name = step.get("nlpName", "").strip()
        rule = None
        for r in rules:
            if r.get("nlpName") == nlp_name:   #  fixed match
                rule = r
                break

        if rule:
            clean_step = {"nlpName": nlp_name}

            # Handle elementsData
            ed_rule = rule.get("elementsData", 0)
            clean_step["elementsData"] = [] if ed_rule == 0 else step.get("elementsData", [])

            # Handle stepInputs
            si_rule = rule.get("stepInputs", 1)
            if si_rule == 0:
                clean_step["stepInputs"] = []
            elif isinstance(si_rule, list):
                inputs = step.get("stepInputs", [])
                casted_inputs = []
                for i, typ in enumerate(si_rule):
                    val = inputs[i] if i < len(inputs) else "Null"
                    caster = type_casts.get(typ, str)
                    try:
                        casted_inputs.append(caster(val) if val is not None else None)
                    except Exception:
                        casted_inputs.append(val)
                clean_step["stepInputs"] = casted_inputs
            else:
                clean_step["stepInputs"] = step.get("stepInputs", [])

            sanitized.append(clean_step)
        else:
            sanitized.append(step)

    return sanitized


import re

# Allowed canonical keys
VALID_KEYS = {   #handling of other things
    "resourceid":"id",
    "id":"id",
    "name": "name",
    "xpath": "xpath",
    "text": "xpath",
    "classname": "className",
    "tagname": "tagName",
    "linktext": "linkText",
    "partiallinktext": "partialLinkText",
    "cssselector": "cssSelector",
    "contentdesc":"accessibilityId",
    "accessibilityid":"accessibilityId",
    "androiduiautomator":"androidUiAutomator" 
}
 
def normalize_key(key: str) -> str:
    """
    Normalize locator key to match the exact allowed set.
    Example: "Css Selectors" -> "cssSelector"
    """
    # Remove spaces, hyphens, underscores, make lowercase
    # cleaned = key.lower()
    cleaned = re.sub(r'[\s\-_]', '', key).lower()
    return VALID_KEYS.get(cleaned, key)  # fallback: keep original if  unknown

def normalize_stepdata(step_data: list) -> list:
    """
    Normalize all locator keys inside stepData.
    """
    if not step_data or not isinstance(step_data, list):
        return []
    for step in step_data:
        for element in step.get("elementsData", []):
            locators = element.get("locators", [])
            for locator in locators:
                if "name" in locator:
                    locator["name"] = normalize_key(locator["name"])
    return step_data