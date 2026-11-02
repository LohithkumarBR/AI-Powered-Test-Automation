import json
from html_extractor import is_probable_path
from dump import SHADOW_DOM_CLICK_JS


def convert_memory_to_clean_json(memory, auto_healing_results=None):
    if auto_healing_results is None:
        auto_healing_results = {}
        
    memory = json.loads(memory)
    clean_json_list = []

    for item in memory:
        step = item.get("step", "")
        action = item.get("action", "")
        xpath = item.get("xpath", "")
        xpath_js = item.get("xpath_js", "")
        input_text = item.get("input", "")
        drag = item.get("drag_element_name","")
        drop = item.get("drop_element_name","")
        element_type = item.get("element_type","")
        element_name = item.get("element_name", "")
        result = item.get("result", "")
        iframe = item.get("iframe", "")
        
        case_sensitive_input = ["VerifyTitleInAllPage","VerifyText","VerifyPartialText","VerifyElementNotContainsText"]
        boolean_value =        ["VerifyAttributeValue","VerifyPartialAttributeValue","VerifyTitleOfCurrentPage","VerifyPartialTitleOfCurrentPage","VerifyValueOfElementIsString",
                                "VerifyValueOfElementContainsString"]
        # tow_to_one_input =     []
        two_input =            ["VerifyAttributeValue","VerifyPartialAttributeValue","VerifyNumberOfElementsByXpath","VerifyLinkNavigatesToTitle","GetTextFromListOfWebElements",
                                "GetListOfElementsFromLocatorTypeLocatorValue","GetSingleApiResponse","GetSingleApiRequestPayload","GetBestPracticesScore","GetPwaScore","GetSeoScore"]
        three_input =          ["GetDataFromApiResponseForJsonPath","GetDataFromApiRequestHeaderForJsonPath"]
        four_input =           ["GetTunnelIdentifier"]
 
        step_inputs = []
        element_data_list = []
        actual_name = element_name if element_name else step
        item_source = item.get("source")

        for eid, res_info in auto_healing_results.items():
            res_data = res_info.get("data", {})
            res_name = res_info.get("name")
            if not res_name and isinstance(res_data, dict):
                res_name = res_data.get("name")

            res_source = res_info.get("source")
            
            # Match both name and source (primary/vision)
            if res_name == actual_name and res_source == item_source:
                # Fetch locators list from response data robustly
                ext_locators = None
                if isinstance(res_data, dict):
                   
                    if "data" in res_data:
                        data_content = res_data["data"]
                        if isinstance(data_content, list):
                            ext_locators = data_content
                        
        
        def get_locators(elem_name, elem_xpath, item_source):
            locs = []
            if elem_xpath:
                locs.append({"name": "xpath", "value": elem_xpath})

            
            # Match and extract Auto-Healing locators
            for eid, res_info in auto_healing_results.items():
                res_data = res_info.get("data", {})
                res_name = res_info.get("name")
                if not res_name and isinstance(res_data, dict):
                    res_name = res_data.get("name")
                
                if res_name == elem_name and res_info.get("source") == item_source:
                    ext_locators = None
                    if isinstance(res_data, dict):
                        
                        if "locators" in res_data:
                            ext_locators = res_data["locators"]
                        elif "data" in res_data:
                            data_content = res_data["data"]
                            if isinstance(data_content, list):
                                ext_locators = data_content
                            elif isinstance(data_content, dict): 
                                if "locators" in data_content:
                                    ext_locators = data_content["locators"]
                               
                    
                    if ext_locators and isinstance(ext_locators, list):
                        for loc in ext_locators:
                            l_name = loc.get("name")
                            l_value = loc.get("value")
                            if l_name and l_value:
                                if not any(xl["value"] == l_value for xl in locs):
                                    locs.append({"name": l_name, "value": l_value})
            return locs


        if action == "VerifyElementIsDisplayed":
            action = "IsDisplayed"
        elif action == "VerifyElementIsEnabled":
            action = "IsEnabled"
        elif action == "VerifyElementIsSelected":
            action = "IsSelected"
        elif action.lower() == "drag_and_drop" or action.lower() == "builtin_draganddroptoelement":
            action = "Builtin_DragAndDropToElement"

        if action == "Builtin_DragAndDropToElement":
             # Handle Drag and Drop specifically: 2 elements
            input_parts = input_text.split("|||") if input_text else []
            source_xpath_val = input_parts[0] if len(input_parts) > 0 and input_parts[0] else (xpath_js if xpath_js else xpath)
            dest_xpath_val = input_parts[1] if len(input_parts) > 1 and input_parts[1] else ""
            dd_types = element_type.split("_") if element_type else []
            drag_element_type = dd_types[0] if len(dd_types) > 0 and dd_types[0] else "text"
            drop_element_type = dd_types[1] if len(dd_types) > 1 and dd_types[1] else "text"
            
            # Element 1: Drag (Source)
            element_data_list.append({
                "name": drag,
                "type": drag_element_type,
                "locators": get_locators(actual_name, source_xpath_val, item_source),
                "platform": "Web"
            })
            
            # Element 2: Drop (Destination)
            element_data_list.append({
                "name": drop,
                "type": drop_element_type,
                "locators": get_locators(drop, dest_xpath_val, item_source),
                "platform": "Web"
            })
            
        elif action != "CloseBrowser" and action != "OpenBrowser":
            # Normal locators logic
            locators = []
            # if result:
            if xpath_js:
                locators.append({"name": "xpath", "value": xpath_js})
            if xpath:
                if not any(l["value"] == xpath for l in locators):
                    locators.append({"name": "xpath", "value": xpath})
            
            # Add auto-healing for single element
            final_locators = get_locators(actual_name, "", item_source)
            for fl in final_locators:
                if not any(l["value"] == fl["value"] for l in locators):
                    locators.append(fl)

            element_data_list.append({
                "name": actual_name,
                "type": element_type,
                "locators": locators,
                "platform": "Web"
            })
        
        if action in two_input:
            parts = input_text.split(",") if isinstance(input_text, str) else []
            input_text_1 = parts[0] if len(parts) > 0 else ""
            input_text_2 = parts[1] if len(parts) > 1 else ""
            step_inputs.append(input_text_1) 
            step_inputs.append(input_text_2)
        # elif action in tow_to_one_input:
        #     parts = input_text.split(",") if isinstance(input_text, str) else []
        #     input_text_2 = parts[1] if len(parts) > 1 else (parts[0] if len(parts) > 0 else "")
        #     step_inputs.append(input_text_2)
        elif action in boolean_value:
            step_inputs.append(input_text)
            step_inputs.append(result)
        elif action in case_sensitive_input:
            step_inputs.append(input_text)
            result = True
        elif action in three_input:
            parts = input_text.split(",") if isinstance(input_text, str) else []
            input_text_1 = parts[0] if len(parts) > 0 else ""
            input_text_2 = parts[1] if len(parts) > 1 else ""
            input_text_3 = parts[2] if len(parts) > 2 else ""
            step_inputs.append(input_text_1) 
            step_inputs.append(input_text_2)
            step_inputs.append(input_text_3)
        elif action in four_input:
            parts = input_text.split(",") if isinstance(input_text, str) else []
            input_text_1 = parts[0] if len(parts) > 0 else ""
            input_text_2 = parts[1] if len(parts) > 1 else ""
            input_text_3 = parts[2] if len(parts) > 2 else ""
            input_text_4 = parts[3] if len(parts) > 3 else ""
            step_inputs.append(input_text_1) 
            step_inputs.append(input_text_2)
            step_inputs.append(input_text_3)
            step_inputs.append(input_text_4)
        elif action == "ExecuteJavaScript" and is_probable_path(input_text):
            step_inputs.append(SHADOW_DOM_CLICK_JS.replace("const path = arguments[0];", f'const path = "{xpath}";'))
        else:
            step_inputs.append(input_text)


        is_in_iframe = False
        iframe_chain = []
        if isinstance(iframe, list) and len(iframe) == 2:
            is_in_iframe = iframe[0]
            iframe_chain = iframe[1] if isinstance(iframe[1], list) else []
        elif isinstance(iframe, bool):
            is_in_iframe = iframe

        if is_in_iframe:
            # Handle iframe chain
            used_element_names = []
            for frame_xpath in iframe_chain:
                if element_name:
                    base_name = element_name
                    new_name = base_name
                    count = 0

                    while new_name in used_element_names:
                        count += 1
                        new_name = f"{base_name}_{count}"

                    element_name = new_name
                    used_element_names.append(element_name)
                frame_element_data = [{
                    "name": f"Iframe_{element_name}",
                    "type": "iframe",
                    "locators": [{"name": "xpath", "value": frame_xpath}],
                    "platform": "Web"
                }]
                frame_clean_item = {
                    "nlpName": "SwitchToFrameByFrameElement",
                    "elementsData": frame_element_data,
                    "stepInputs": []
                }
                clean_json_list.append(frame_clean_item)

            # Update action to JS versions for elements inside iframe
            if action == "Click":
                action = "ClickUsingJS"
            elif action == "SendKeys":
                action = "EnterInputUsingJS"
            
            clean_item = {
                "nlpName": action,
                "elementsData": element_data_list,
                "stepInputs": step_inputs
            }
            clean_json_list.append(clean_item)

        elif action == "ExecuteJavaScript" and is_probable_path(input_text):  
            # Execute JavaScript (opens file dialog usually)
            clean_json_list.append({
                "nlpName": "ExecuteJavaScript",
                "elementsData": [],
                "stepInputs": step_inputs
            })

            # AutoItSendkeys → send file path
            clean_json_list.append({
                "nlpName": "AutoItSendkeys",
                "elementsData": [],
                "stepInputs": [input_text]
            })

            # PressEnterKey
            clean_json_list.append({
                "nlpName": "PressEnterKey",
                "elementsData": [],
                "stepInputs": []
            })
        else:
            clean_item = {
                "nlpName": action,
                "elementsData": element_data_list,
                "stepInputs": step_inputs
            }
            clean_json_list.append(clean_item)

    # if auto_healing_results:
    #     print("\n" + "="*50)
    #     print("AUTO-HEALING RESULTS SUMMARY")
    #     print("="*50)
    #     print(json.dumps(auto_healing_results, indent=4))
    #     print("="*50 + "\n")

    return clean_json_list
