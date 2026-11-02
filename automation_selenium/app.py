from flask import Flask, jsonify, request
import json
import base64
from agent import Agent
from LLMcall import call_grok_llm
import logging
import traceback
from runscript import run_script_from_payload, error_message_payload
from nlp_sanitize import *

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding="utf-8"
)
logger = logging.getLogger(__name__)


#  Step 1: Extract structured test steps using LLM
def extract_user_story_steps_from_raw(user_story_raw, serviceProvider, model, apiKey, service_accounts):
    """
    Extract structured test steps from user story for web automation.
    Output: list of plain strings (no tuples).
    """
    try:
        prompt = f"""
You are a precise assistant.
Extract **step data** from the following user story for web automation.

Rules:
1. Each step must be a string — not a tuple.
2. Keep the wording the same except:
   - Do not add new steps, only rewrite existing ones.
   - Do not remove any steps.
   - Do not remove quotes from the step. if these quotes are present in the step, keep them as it is.
3. Output only a **valid Python list of strings**. No explanations, markdown, or code fences..
4. Please paste the “below example list” here, so I can make it dynamic and generic strictly in the same format.
Example:
[
  "Open browser",
  "Navigate to https://example.com",
  "Maximize the browser window",
  "Click on Login",
  "Enter email 'abc@gmail.com' in email text field",
  "Enter password '12345' in password field",
  "Click on Submit",
  "Close browser"
]
**Dont include any other text in the list. and also dont include example list in the response.**
User Story:
{user_story_raw}
"""

        response = call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts)

        # Cleanup common markdown code block markers
        # print(response)
        response = json.loads(response)   # ✅ convert string → dict
        try:
            response = response["steps"]      # ✅ now this works
        except Exception:
            pass
        
        # print(response)


        if isinstance(response, list):
            steps = response
        else:
            try:
                steps = json.loads(response)
            except Exception:
                import ast
                try:
                    steps = ast.literal_eval(response)
                except Exception as e:
                    if "unicodeescape" in str(e).lower():
                        # Try to escape backslashes if it's a path issue
                        fixed_response = response.replace('\\', '\\\\')
                        try:
                            steps = ast.literal_eval(fixed_response)
                        except:
                            raise e
                    else:
                        raise e

        if not isinstance(steps, list) or not steps:
            raise Exception("No valid steps extracted from user story")

        # Normalize steps
        normalized_steps = []
        for s in steps:
            if isinstance(s, tuple):
                normalized_steps.append(" ".join(map(str, s)))
            else:
                normalized_steps.append(str(s))
        try:
            logger.info("Normalized steps:\n%s", json.dumps(normalized_steps, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error("Error logging normalized steps: " + str(e))
        return normalized_steps, None, None

    except Exception as e:
        raise e


# ---- Execute Web Automation ----
@app.route("/automation", methods=["POST"])
def execute_web_steps():
    driver = None
    agent = None
    cleaned_memory = None
    error_sent = False
    try:
        data = request.get_json()
        required_fields = [
            "userStory", "scriptName", "scriptType", "pageDetails",
            "projectId", "testCaseId", "promptId", "licenseType",
            "licenseId", "userId", "browser"
        ]

        # Check required fields
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise Exception("Missing fields: " + ", ".join(missing))

        # LLM config
        serviceProvider = data.get("serviceProvider")
        model = data.get("model")
        apiKey = data.get("apiKey", "")
        if apiKey:
            # apiKey = base64.b64decode(apiKey).decode("utf-8")
            apiKey = apiKey
        service_accounts= data.get("service_accounts", None)
        user_story_raw = data["userStory"]
        server_host = data.get("serverHost", "")
        steps, error_response, status_code = extract_user_story_steps_from_raw(
            user_story_raw, serviceProvider, model, apiKey, service_accounts
        )
        if error_response:
            raise Exception(error_response)

        # Filter unnecessary steps
        filtered_steps = steps
        # logger.info(f"Extracted {len(filtered_steps)} actionable web steps")

        # Browser configuration
        browser_config = data["browser"]
        chrome_path = browser_config["browserPath"]
        browser_name = browser_config["browserName"]
        browser_version = browser_config["browserVersion"]
        browser_driver_path = browser_config["browserDriverPath"]
        hub_url = browser_config.get("hub_url", "")
        os_platform = browser_config.get("platform", "")
        cloud = browser_config.get("cloud", False)


        if browser_name.lower() == "microsoftedge":
            browser_name = "edge"

        # Initialize Selenium Agent
        logger.info("[INFO] Launching browser session...")
        agent = Agent(
            browser_name=browser_name,
            driver_path=browser_driver_path,
        )
        
        # Prevent GC of driver by registering it globally
        # Use testCaseId as session ID for persistence
        session_id = data.get("testCaseId", "default_session")
        
        # Execute steps using agent's logic
        cleaned_memory, exec_steps = agent.call_agent(filtered_steps,server_host, serviceProvider, model, apiKey,service_accounts,session_id=session_id)
        
        if agent.driver:
            from agent import ACTIVE_SESSIONS
            # ACTIVE_SESSIONS[session_id] = agent.driver
        # logger.info(cleaned_memory)
        logger.info("Web automation completed successfully")

        
        # Send payload to FireFlink
        try:
            final_result = run_script_from_payload(
                cleaned_memory, data, agent.total_time
            )
            return jsonify({
                "status": "success",
                "message": "Payload sent to FireFlink",
                "fireflinkResponse": final_result,
                "steps": filtered_steps,
                "executed_steps": exec_steps,
                "memory": cleaned_memory
            })

        except Exception as e:
            return jsonify({
                "status": "failed",
                "message": "Error while sending payload",
                "error": str(e)
            }), 500

    except Exception as e:
        logger.error(f"[ERROR] Execution failed: {e}")
        full_error = traceback.format_exc()
        # logger.error(f"Full traceback:\n{full_error}")
        
        # Global error handling and reporting to FireFlink
        try:
            body = request.get_json(silent=True) or {}
        except:
            body = {}
        
        error_message = "Unknown error occurred"
        try:
            raw_error = str(e).strip()
            clean_error = raw_error.split("\n")[0].strip()
            error_message = clean_error
            
            # Generate LLM error description here in app.py
            logger.info("Generating LLM error description...")
            serviceProvider = body.get("serviceProvider")
            model = body.get("model")
            apiKey = body.get("apiKey", "")
            if apiKey:
                apiKey = base64.b64decode(apiKey).decode("utf-8")
            service_accounts = body.get("service_accounts")
            
            # Use partial memory for context if available
            final_memory = cleaned_memory or (getattr(agent, 'cleaned_memory', None) if agent else None) or []
            
            description_prompt = f"""
            Internal Error Traceback:
            {full_error}
            
            Execution History (Last few steps):
            {json.dumps(final_memory[-5:] if isinstance(final_memory, list) else [], indent=2)}
            
            Analyze the error and execution history to provide diagnostics in JSON format.
            
            Return a JSON object with the following keys:
            1. "error": A concise, single-line, selenium type(error).__name__ (e.g., "InvalidSessionIdException", "InvalidElementStateException", "ElementNotInteractableException","NoSuchElementException" etc). 
            2. "errorDescription": A very simple, non-technical, and user-friendly explanation of why the automation might have failed.
               - Use plain English.
               - All the lines should contain FireFlink. example: "FireFlink was unable to find the element..."
               - Do not mention code, XPaths, or internal technical terms.
               - The output MUST be a single paragraph of exactly 2 to 5 lines of text.
               - Focus on potential real-world causes.
            
            Output ONLY the raw JSON object. No markdown, no backticks, no explanatory text.
            """
            
            error_description = "Could not generate detailed description."
            
            # Manual fallback for common technical errors
            if any(x in error_message for x in ["Invalid API Key", "Authentication", "401"]):
                error_message = "Invalid API Key"
                error_description = (
                    "The automation failed because the provided LLM API key is invalid or has expired. "
                    "This prevents FireFlink from analyzing the page. "
                    "Please check your API key configuration in FireFlink."
                )
            elif any(x in error_message.lower() for x in ["429", "quota", "rate limit"]):
                error_message = "RateLimitError"
                error_description = (
                    "FireFlink has exceeded the API quota or rate limit for the selected AI model. "
                    "This is common with free or low-tier API plans. "
                    "Please wait a moment before retrying or check your API usage limits."
                )
            else:
                try:
                    llm_response = call_grok_llm(description_prompt, serviceProvider, model, apiKey, service_accounts)

                    logger.info(f"LLM response: {llm_response}")
                    
                    # Attempt to parse JSON from LLM response
                    try:
                        # Strip any potential markdown or whitespace
                        clean_res = llm_response.strip()
                        if clean_res.startswith("```json"):
                            clean_res = clean_res.replace("```json", "", 1).replace("```", "", 1).strip()
                        elif clean_res.startswith("```"):
                            clean_res = clean_res.replace("```", "", 1).replace("```", "", 1).strip()
                        
                        parsed_res = json.loads(clean_res)
                        error_message = parsed_res.get("error", error_message)
                        error_description = parsed_res.get("errorDescription", error_description)
                    except Exception as parse_err:
                        logger.warning(f"Failed to parse LLM JSON response: {parse_err}. Using raw response as description.")
                        error_description = llm_response

                except Exception as llm_err:
                    logger.error(f"Failed to generate error description in app.py: {llm_err}")
                    if "Invalid API Key" in str(llm_err) or "401" in str(llm_err):
                        error_message = "Invalid API Key"
                        error_description = "The provided API key is invalid. Please check your FireFlink configuration."

            if not error_sent:
                failed_step = getattr(agent, 'failed_step', None)
                ff_response = error_message_payload(
                    final_memory,
                    error_message,
                    error_description,
                    full_error,
                    body,
                    error_step=failed_step
                )
        except Exception as ff_error:
            ff_response = {"status": "failed", "error": str(ff_error)}

        if driver:
            try:
                driver.quit()
            except:
                pass
                
        return jsonify({
            "status": "failed",
            "error_message": error_message,
            "fireflink_error": ff_response,
            "full_error": full_error
        }), 500

@app.route("/terminate", methods=["POST"])
def terminate_session():
    data = request.get_json()
    session_id = data.get("testCaseId")

    from agent import ACTIVE_SESSIONS, TERMINATE_FLAGS

    # 1. Signal agent to stop execution
    TERMINATE_FLAGS[session_id] = True

    # ACTIVE_SESSIONS.get(session_id)
    # 2. Close browser safely
    # if driver:
    #     try:
    #         driver.quit()
    #     except:
    #         pass

    # ACTIVE_SESSIONS.pop(session_id,None)

    return jsonify({
        "status": "terminated",
        "message": "Browser closed successfully"
    })


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765, help="Port to run the server on")
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)