import json
import requests
from nlp_sanitize import *
from LLMcall import call_grok_llm, reset_count
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def call_fireflink_api(headers, body, url):
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        
        # Handle non-200 responses
        if response.status_code != 200:
            print("Response Status Code:", response.status_code)
            try:
                error_content = response.json()
            except Exception:
                error_content = response.text
            raise Exception(f"HTTP Error {response.status_code}: {error_content}")
        
        # Return JSON response
        return response.json()
    
    except requests.exceptions.Timeout:
        raise Exception("Request to FireFlink API timed out.")
    
    except requests.exceptions.ConnectionError as ce:
        raise Exception(f"Connection error while calling FireFlink API: {ce}")
    
    except requests.exceptions.RequestException as re:
        raise Exception(f"Request error while calling FireFlink API: {re}")
    
    except Exception as e:
        raise Exception(f"Unexpected error while calling FireFlink API: {e}")
 
def run_script_from_payload(result,payload,total_input,total_output,total_tokens,
    openai_total_input,openai_total_output,openai_total_tokens,total_time):
    try:
        step_data = json.loads(result) if isinstance(result, str) else result
        step_data = normalize_stepdata(step_data=step_data)
        step_data = sanitize_steps(steps=step_data)
        # step_data.append({
        #     "nlpName": "Close Android App",
        #     "elementsData": [],
        #     "stepInputs": []
        # })
    except Exception as e:
        logger.error("Failed to parse final llm data: %s", e)
        mobile_error_message_payload(f"Failed to parse final llm data: {e}", 500, payload)
        return

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
        "tokensConsumed": total_tokens,
    }

    # logger.info("Body for the payload is:\n%s", json.dumps(body, indent=2))
    logger.info(f"Total Tokens: {total_tokens}, Input Tokens: {total_input}, Output Tokens: {total_output}")
    logger.info(f"OpenAI Total Tokens: {openai_total_tokens}, Input Tokens: {openai_total_input}, Output Tokens: {openai_total_output}")
    logger.info(f"Total Time taken for script generation: {total_time} seconds")
    reset_count()
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "projectId": payload.get("projectId"),
        "Authorization": f"Bearer {payload.get('token')}"
    }
    
    url = f"{payload.get('serverHost')}/project/optimize/v3/bulk/scripts/script-payload"
    final_result = call_fireflink_api(headers, body, url)
    # logger.info(final_result)
    return final_result

def mobile_error_message_payload(result,total_tokens,error_message,error_code,payload):
    logger.info("sending error message payload to fireflink")
    if not isinstance(payload, dict):
        payload = {}
    try:
        step_data = json.loads(result) if isinstance(result, str) else result
        step_data = normalize_stepdata(step_data=step_data)
        step_data = sanitize_steps(steps=step_data)
        # step_data.append({
        #     "nlpName": "Close Android App",
        #     "elementsData": [],
        #     "stepInputs": []
        # })
    except Exception as e:
        logger.error("Failed to parse final llm data: %s", e)
        mobile_error_message_payload(f"Failed to parse final llm data: {e}", 500, payload)
        return

    # logger.info("Payload received:", payload)
    # logger.info("Error Message:", error_message)
    # logger.info("Error Code:", error_code)
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
        # "errorMessage": error_message,
        # "errorCode": error_code,
        "tokensConsumed": total_tokens
    }
    # logger.info("Body for the error payload is:\n%s", json.dumps(body, indent=2))


    reset_count()
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "projectId": payload.get("projectId"),
        "Authorization": f"Bearer {payload.get('token')}"
    }
    url = f"{payload.get('serverHost')}/project/optimize/v3/bulk/scripts/script-payload"
    final_result = call_fireflink_api(headers, body, url)
    # logger.info(final_result)
    return final_result




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
        nlp_name = (step.get("nlpName") or "").strip()
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
    return VALID_KEYS.get(cleaned, key)  # fallback: keep original if unknown

def normalize_stepdata(step_data: list) -> list:
    """
    Normalize all locator keys inside stepData.
    """
    for step in step_data:
        for element in step.get("elementsData", []):
            locators = element.get("locators", [])
            for locator in locators:
                if "name" in locator:
                    locator["name"] = normalize_key(locator["name"])
    return step_data