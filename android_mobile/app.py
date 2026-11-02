from flask import Flask, jsonify, request
from groq import Groq
import json
import subprocess
import time
import requests
import socket
from LLMcall import call_grok_llm
import base64
import argparse
from runscript import run_script_from_payload,mobile_error_message_payload
from xml_extractor import Extractor,keyword_extractor
from executor import create_driver, AppiumStepExecutor
from finding_nlp import convert_memory_to_clean_json
import json
from werkzeug.serving import run_simple
app = Flask(__name__)
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ACTIVE_SESSIONS = {}
TERMINATE_FLAGS = {}
driver = None
error_sent = False

def is_appium_running(url="http://127.0.0.1:4723/wd/hub/status"):
    try:
        res = requests.get(url, timeout=2)
        return res.status_code == 200
    except:
        return False
    
def is_local_appium_running(host="127.0.0.1", port=4723):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)

    try:
        sock.connect((host, port))
        sock.close()
    except:
        return False

    try:
        res = requests.get(f"http://{host}:{port}/status", timeout=1)
        return res.status_code == 200
    except:
        return True  
    
def extract_user_story_steps_from_raw(user_story_raw,serviceProvider,model,apiKey,service_accounts):
    """
    Use LLM to extract structured steps (tuples or strings) from userStory.
    Returns (steps, error_response, status_code)
    """
    try:
        prompt = f"""
You are a precise assistant.  
Extract **step data** from the following mobile {user_story_raw}.

Rules:
Dont take text from one step and use it in another step.
1. If the step is about luanching an app, like (action, param1, param2) or(action,'param1,param2') then wrap them into a tuple.
and also give them in the format (launch app, 'com.app.android', 'com.app.activity') like first package name and second activity name. if any separator exists (- / | :), split on it.
If they mention package:com.app.android and activity:com.app.activity remove variable name and then convert them into (launch app, 'com.app.android, 'com.app.activity')
2.Dont remove parameters from the step. and never combine or merge steps and dont create any extra steps.
step may be any formate for enter if input is give seperatly with comma use this
 example:'enter username in text field','testuser' → ('enter username in text field','testuser').
if not given seperatly with comma use and mention in step it self than this
 example:'enter testuser in text field' → ('enter testuser in text field','testuser').
3. If it's just a single string value, keep it as a string.
4. Always output a **Always output a valid list of strings.** containing strings or tuples only. 
 - Do not add explanations, reasoning, or extra text outside the list.
 - Do not make any assumption if step inputs are missing in user_story_raw
 - **Dont change the order of steps from user story**
5. If the step is tuple keep it as tuple like this (step). if not just keep it as a string like this 'step'.
**strictly follow the output format**
    ('Launch  Mobile App','com.app.android','com.app.activity'),
    'Tap on cancel button',
    'Tap on signin with email',
    ('enter username in text field','testuser'),
    ('enter testuser in text field','testuser'),
    'verify element is displayed'
"""

        response, usage = call_grok_llm(
            prompt,
            serviceProvider, 
            model,
            apiKey,
            service_accounts

        )
        import re
        import ast
        import json

        try:
            steps = json.loads(response)   # Try parsing as JSON
        except Exception:
            # Clean extra data outside the list
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if not match:
                raise ValueError("No valid list found in response")

            cleaned_response = match.group(0)

            # Safe replacement for eval
            steps = ast.literal_eval(cleaned_response)

                    # Fallback if it's a Python-style list

        if not steps:
            raise Exception("No valid steps found in userStory")
 
        # Return steps along with token usage
        return steps, usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]

    except Exception as e:
        raise Exception(f"Error parsing userStory: {str(e)}")


@app.route("/execute-mobile-steps", methods=["POST"])
def execute():
    global driver,error_sent
    driver = None  # Reset driver for each request
    error_sent = False 



    try:
        data = request.get_json()
        required_fields = [
            "userStory", "scriptName", "scriptType","pageDetails",
            "projectId", "testCaseId", "promptId", "licenseType",
            "licenseId", "userId", "real_device_id", "platform_version"
        ]
        session_id = data.get("testCaseId")
        TERMINATE_FLAGS[session_id] = False
        serviceProvider = data.get("serviceProvider")
        model = data.get("model")
        apiKey = data.get("apiKey")
        if apiKey:
            apiKey = base64.b64decode(apiKey).decode("utf-8")
        service_accounts= data.get("service_accounts", None)
        missing = [field for field in required_fields if field not in data]
        if missing: 
            raise Exception(f"Missing fields: {missing}")


        user_story_raw = data["userStory"]
        steps, extract_input_tokens, extract_output_tokens, extract_total_tokens = extract_user_story_steps_from_raw(
            user_story_raw, serviceProvider, model, apiKey,service_accounts
        )
        logger.info(f"Extracted steps: {steps}"
        )
        logger.info(f"User Story Extraction — Input: {extract_input_tokens}, Output: {extract_output_tokens}, Total: {extract_total_tokens} tokens")

        filtered_steps = steps

        real_device_id = data.get("real_device_id")
        platform_version = data.get("platform_version")
        
        
        # Track total time at app level (includes ALL operations per step)
        app_total_time = 0.0

        if not real_device_id:
            raise Exception("Missing Device Id")


        executor = None
        extractor = None
        app_package = None
        app_activity = None
        used_element_names = []

        for i, step in enumerate(filtered_steps, 1):
            
            if session_id:
                ACTIVE_SESSIONS[session_id] = driver
                logger.info(f"Registered session {session_id} in ACTIVE_SESSIONS")
            if session_id and TERMINATE_FLAGS.get(session_id,False):
                logger.info("Execution stopped by API termination after launch.")
                break
            step_str = ",".join(step) if isinstance(step, tuple) else step

            if isinstance(step, tuple) and any(
                word.lower() in ["launch", "open"] for s in step for word in s.split()
            ):
                app_package, app_activity = step[1], step[2]
                logger.info(f"Launching app: {app_package}/{app_activity}")

                if not is_appium_running():
                    logger.info("[ERROR] Appium server is not running.")
                    error_sent = True
                    mobile_error_message_payload(
                        "Appium cloud server is not running at http://127.0.0.1:4723",
                        500,
                        data
                    )  
                    raise Exception("Appium is not running")
                    
                # if not is_local_appium_running():
                #     logger.info("[ERROR] Appium server is not running.")
                #     error_sent = True
                #     mobile_error_message_payload(
                #         "Appium local server is not running at http://127.0.0.1:4723",
                #         500,
                #         data
                #     )
                    
                #     raise Exception(f"Appium is not running: {str(e)}")

                try:
                    if driver is not None:
                        try:
                            current_package = driver.current_package
                            if current_package == app_package:
                                logger.info("[INFO] App already launched → continue to next step.")
                                continue
                            else:
                                logger.info(f"[INFO] Different app running ({current_package}) — launching new app.")
                        except:
                            logger.info("[INFO] Could not verify current app — launching fresh.")

                    driver, launch_error = create_driver(real_device_id, platform_version, app_package, app_activity)

                    if driver is None:
                        error_sent = True
                        final_error = launch_error if launch_error else f"Invalid appPackage or appActivity: {app_package}/{app_activity}"
                        
                        mobile_error_message_payload(
                            final_error,
                            500,
                            data
                        )
                        
                        return jsonify({
                            "status": "failed",
                            "error_message": final_error
                        }), 500
                    

                    executor = AppiumStepExecutor(driver, app_package, real_device_id,filtered_steps)
                    extractor = Extractor(driver)


                    executor.memory.append({
                        "step": "Launch Mobile App",
                        "app_package": app_package,
                        "app_activity": app_activity,
                        "action": "Open Android App"
                    })
                    continue

                except Exception as e:
                    logger.error(f"[ERROR] Failed to launch app via Appium: {e}")

            if not driver or not executor:
                raise Exception("App was not launched before performing steps")

            if any(word in step_str.lower() for word in ["close", "quit"]) and any(word in step_str.lower() for word in ["app", "application"]):
                if app_package:
                    logger.info(f"Closing app: {app_package}")
                    executor.execute_close_app()
                    executor.memory.append({
                        "step": "Closing Mobile App",
                        "action": "MOB_CloseApp"
                    })
                continue

            if executor.has_been_force_closed():
                logger.info("App force-closed after step execution")
                break
            
            # Start timing for this step (includes ALL operations)
            raw_dom = None
            annotated_dom = None
            simplified_json = None
            step_start_time = time.time()

            logger.info(f"Executing... step {i}: {step_str}")

            

            # Extract keywords and Element Name
            keywords,element_name,step_action,input_tokens,output_tokens,total_tokens = keyword_extractor(step_str,filtered_steps,serviceProvider,model,apiKey,service_accounts)
            if element_name:
                base_name = element_name
                new_name = base_name
                count = 0
                while new_name in used_element_names:
                    count += 1
                    new_name = f"{base_name}_{count}"
                element_name = new_name
                used_element_names.append(element_name)

            logger.info(f"Keywords: {keywords} Input Tokens: {input_tokens} Output Tokens: {output_tokens} Total Tokens: {total_tokens}")
            if step_action.lower() not in ["scroll", "navigation"]:
    
                raw_dom = None
                annotated_dom = None
                simplified_json = None

                try:
                    raw_dom = extractor.get_ui_dump()
                    annotated_dom, simplified_json = extractor.annotate_and_simplify_dom(keywords,raw_dom,i)
                except ValueError as dom_error:
                    raise Exception(str(dom_error))
            else:
                annotated_dom = ''
                simplified_json = ''
                input_tokens = 0
                output_tokens = 0
                total_tokens = 0
            
            
            # COMBINED_KEYWORDS = [
            #     "uninstall", "install", "wifi", "airplane", "gps", "orientation", "lock",
            #     "notification", "chrome", "reset", "restart", "keyboard", "clipboard", "long press",
            #     "double tap", "press key", "context", "capability", "url", "emulator", "press",
            #     "messageonemulator", "script", "javascript", "enter key", "find", "times", "pinch",
            #     "backspace","back space", "space key", "background", "switch", "timeout", "activity",
            #     "compare", "native", "view", "implicit", "location", "clear"
            # ]

            try:
                
                if step_action == "combined":
                    action = "combined"
                    annotated_dom = annotated_dom
                    simplified_json = simplified_json
                    serviceProvider, model, apiKey
                    success = executor.execute_step_files(
                action,i,element_name, annotated_dom, simplified_json, step_str, serviceProvider, model, apiKey,service_accounts,
                initial_input_tokens=input_tokens, initial_output_tokens=output_tokens, initial_total_tokens=total_tokens
                )
                    # Log step completion time
                    step_end_time = time.time()
                    step_elapsed = step_end_time - step_start_time
                    app_total_time += step_elapsed 
                    logger.info(f"✓ Step {i} completed in {step_elapsed:.2f}s")
                    

                elif step_action == "verify":
                    action = "verification"
                    annotated_dom = annotated_dom
                    simplified_json = simplified_json
                    serviceProvider, model, apiKey
                    success = executor.execute_step_files(
                action,i,element_name, annotated_dom, simplified_json, step_str, serviceProvider, model, apiKey,service_accounts,
                initial_input_tokens=input_tokens, initial_output_tokens=output_tokens, initial_total_tokens=total_tokens
                )
                    # Log step completion time
                    step_end_time = time.time()
                    step_elapsed = step_end_time - step_start_time
                    app_total_time += step_elapsed  # Accumulate real step time
                    logger.info(f"✓ Step {i} completed in {step_elapsed:.2f}s")
                    logger.info(f"{'='*60}\n")

                elif step_action == "wait":
                    action = "wait"
                    annotated_dom = annotated_dom
                    simplified_json = simplified_json
                    serviceProvider, model, apiKey
                    success = executor.execute_step_files(
                action,i,element_name, annotated_dom, simplified_json, step_str, serviceProvider, model, apiKey,service_accounts,
                initial_input_tokens=input_tokens, initial_output_tokens=output_tokens, initial_total_tokens=total_tokens
                )
                    # Log step completion time
                    step_end_time = time.time()
                    step_elapsed = step_end_time - step_start_time
                    app_total_time += step_elapsed  # Accumulate real step time
                    logger.info(f"✓ Step {i} completed in {step_elapsed:.2f}s")
                    logger.info(f"{'='*60}\n")

                elif step_action == "get":
                    action = "get"
                    annotated_dom = annotated_dom
                    simplified_json = simplified_json
                    serviceProvider, model, apiKey
                    success = executor.execute_step_files(
                action,i,element_name, annotated_dom, simplified_json, step_str, serviceProvider, model, apiKey,service_accounts,
                initial_input_tokens=input_tokens, initial_output_tokens=output_tokens, initial_total_tokens=total_tokens
                )
                    # Log step completion time
                    step_end_time = time.time()
                    step_elapsed = step_end_time - step_start_time
                    app_total_time += step_elapsed  # Accumulate real step time
                    logger.info(f"✓ Step {i} completed in {step_elapsed:.2f}s")
                    logger.info(f"{'='*60}\n")

                elif step_action == "scroll":
                    action = "scroll"
                    annotated_dom = annotated_dom
                    simplified_json = simplified_json
                    serviceProvider, model, apiKey
                    success = executor.execute_step_files(
                action,i,element_name, annotated_dom, simplified_json, step_str, serviceProvider, model, apiKey,service_accounts,
                initial_input_tokens=input_tokens, initial_output_tokens=output_tokens, initial_total_tokens=total_tokens
                )
                    # Log step completion time
                    step_end_time = time.time()
                    step_elapsed = step_end_time - step_start_time
                    app_total_time += step_elapsed  # Accumulate real step time
                    logger.info(f"✓ Step {i} completed in {step_elapsed:.2f}s")
                    logger.info(f"{'='*60}\n")

                    if not success:
                        if app_package:
                            logger.info(f"Closing app: {app_package}")
                            executor.execute_close_app()
                            if not executor.memory or executor.memory[-1].get("action") != "MOB_CloseApp":
                                executor.memory.append({
                                "step": "Closing Mobile App",
                                "action": "MOB_CloseApp"
                            })
                        break
                elif step_action in ["enter", "tap"]:

                    (ff_inspecter_num, action, input_text, keyword, element_type, xpath_path,
                        step_input_tokens, step_output_tokens, step_total_tokens) = extractor.ff_inspecter_num_extractor(
                        step_str, simplified_json, annotated_dom, filtered_steps,
                        serviceProvider, model, apiKey,service_accounts
                    )
                    logger.info(
                        f"FF-inspecter number: {ff_inspecter_num}, Action: {action}, "
                        f"Input: {input_text}, type:{element_type}, XPath: {xpath_path}"
                    )
                    success = executor.execute_step(filtered_steps,
                    raw_dom, i, action,element_type,element_name, ff_inspecter_num, xpath_path, input_text, step_str,simplified_json,serviceProvider, model, apiKey,
                    step_input_tokens + input_tokens, step_output_tokens + output_tokens, step_total_tokens + total_tokens,keyword
                    )
                    # Log step completion time
                    step_end_time = time.time()
                    step_elapsed = step_end_time - step_start_time
                    app_total_time += step_elapsed  # Accumulate real step time
                    logger.info(f"✓ Step {i} completed in {step_elapsed:.2f}s")
                    logger.info(f"{'='*60}\n")

                    if not success:
                        if app_package:
                            logger.info(f"Closing app: {app_package}")
                            executor.execute_close_app()
                            if not executor.memory or executor.memory[-1].get("action") != "MOB_CloseApp":
                                executor.memory.append({
                                "step": "Closing Mobile App",
                                "action": "MOB_CloseApp"
                            })
                        break

                else:
                    ff_inspecter_num = 1000000
                    action = "navigation"
                    input_text = ""
                    element_type = "Button"
                    keyword = ""
                    xpath_path = ""
                    simplified_json = ""
                    step_input_tokens = step_output_tokens = step_total_tokens = 0
                    input_tokens = output_tokens = total_tokens = 0
                    
                    success = executor.execute_step(filtered_steps,
                        raw_dom, i, action,element_type, element_name, ff_inspecter_num, xpath_path, input_text, step_str,simplified_json,serviceProvider, model, apiKey,
                        step_input_tokens + input_tokens, step_output_tokens + output_tokens, step_total_tokens + total_tokens,keyword
                    )
                    # Log step completion time
                    step_end_time = time.time()
                    step_elapsed = step_end_time - step_start_time
                    app_total_time += step_elapsed  # Accumulate real step time
                    logger.info(f"✓ Step {i} completed in {step_elapsed:.2f}s")
                    logger.info(f"{'='*60}\n")

                    if not success:
                        if app_package:
                            logger.info(f"Closing app: {app_package}")
                            executor.execute_close_app()
                            # Note: executor already adds close app to memory in has_been_force_closed()
                        break
            except Exception as e:
                logger.error(f"Error: {str(e)}")
                raise Exception(str(e))
                

        error_sent = False
        if executor:

            # logger.info(executor.execution_steps)
            
            # Token aggregation from step execution
            step_exec_input = sum(step.get("input_tokens", 0) for step in executor.execution_steps)
            step_exec_output = sum(step.get("output_tokens", 0) for step in executor.execution_steps)
            step_exec_tokens = sum(step.get("total_tokens", 0) for step in executor.execution_steps)

            # Add extraction tokens to get grand total
            total_input = step_exec_input + extract_input_tokens
            total_output = step_exec_output + extract_output_tokens
            total_tokens = step_exec_tokens + extract_total_tokens

            openai_total_input = sum(step.get("openai_input_tokens", 0) for step in executor.execution_steps)
            openai_total_output = sum(step.get("openai_output_tokens", 0) for step in executor.execution_steps)
            openai_total_tokens = sum(step.get("openai_total_tokens", 0) for step in executor.execution_steps)

            logger.info("=" * 60)
            logger.info("TOKEN BREAKDOWN:")
            # logger.info(f"  User Story Extraction — Input: {extract_input_tokens}, Output: {extract_output_tokens}, Total: {extract_total_tokens}")
            # logger.info(f"  Step Execution (incl. keywords) — Input: {step_exec_input}, Output: {step_exec_output}, Total: {step_exec_tokens}")
            logger.info(f"  GROQ GRAND TOTAL — Input: {total_input}, Output: {total_output}, Total: {total_tokens} tokens")
            logger.info(f"  OpenAI Total — Input: {openai_total_input}, Output: {openai_total_output}, Total: {openai_total_tokens} tokens")
            logger.info("=" * 60)
            
            logger.info("TIME BREAKDOWN:")
            logger.info(f"  Total Steps Executed: {len(executor.execution_steps)}")
            logger.info(f"  TOTAL EXECUTION TIME: {app_total_time:.2f}s")
            logger.info("=" * 60)
            memory_storage = executor.memory
            json_memory = json.dumps(memory_storage)
            cleaned_memory = convert_memory_to_clean_json(json_memory)

            total_time = app_total_time  # Use app-level total time (accurate)
        try:
            
            final_result = run_script_from_payload(cleaned_memory, data,total_input,total_output,total_tokens,
            openai_total_input,openai_total_output,openai_total_tokens,total_time)
            if driver:
                driver.quit()
                logger.info("Appium driver session ended.")
            return jsonify({
                "status": "success",
                "message": "Payload sent to FireFlink",
                "fireflinkResponse": final_result
            })
            

        except Exception as e:
            return jsonify({
                "status": "failed",
                "message": "Error while sending payload",
                "error": str(e)
            }), 500
        

    # =============== GLOBAL EXCEPTION HANDLER ===============
    except Exception as e:
        if app_package:
            logger.info(f"Closing app: {app_package}")
            executor.execute_close_app()
            if not executor.memory or executor.memory[-1].get("action") != "MOB_CloseApp":
                executor.memory.append({
                "step": "Closing Mobile App",
                "action": "MOB_CloseApp"
            })

        step_exec_input = sum(step.get("input_tokens", 0) for step in executor.execution_steps)
        step_exec_output = sum(step.get("output_tokens", 0) for step in executor.execution_steps)
        step_exec_tokens = sum(step.get("total_tokens", 0) for step in executor.execution_steps)

        # Add extraction tokens to get grand total
        total_input = step_exec_input + extract_input_tokens
        total_output = step_exec_output + extract_output_tokens
        total_tokens = step_exec_tokens + extract_total_tokens
        memory_storage = executor.memory
        json_memory = json.dumps(memory_storage)
        cleaned_memory = convert_memory_to_clean_json(json_memory)
        
        if driver:
            try:
                driver.quit()
                logger.info("Appium driver session ended.")
            except Exception as quit_error:
                logger.error(f"Error while quitting driver: {quit_error}")

        try:
            body = request.get_json(silent=True) or {}
        except:
            body = {}
        
        error_message = "Unknown error occurred"
        try:
            raw_error = str(e).strip()
            clean_error = raw_error.split("\n")[0].strip()
            clean_error = (
                clean_error.replace("Message:", "")
                            .replace("Error:", "")
                            .replace("Exception:", "")
                            .strip()
            )

            error_message = clean_error
            error_code = 500
            logger.error(f"[GLOBAL ERROR] {error_message}")
            ff_response = mobile_error_message_payload(cleaned_memory,total_tokens,
                error_message,
                error_code,
                body
            )
        except Exception as ff_error:
            ff_response = {"status": "failed", "error": str(ff_error)}

        return jsonify({
                "status": "success",
                "message": "Payload sent to FireFlink",
                "fireflinkResponse": ff_response
            })
    
@app.route("/terminate", methods=["POST"])
def terminate_session():
    data = request.get_json()
    session_id = data.get("testCaseId")

    TERMINATE_FLAGS[session_id] = True

    return jsonify({
        "status": "terminated",
        "message": "App closed successfully"
    })

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=50504)
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7890, help="Port to run the server on")
    args = parser.parse_args()
    app.run(
        host="0.0.0.0",
        port=args.port,
        debug=False,
        use_reloader=False
    )