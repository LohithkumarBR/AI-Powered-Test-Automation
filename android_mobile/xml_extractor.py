import re
from LLMcall import call_grok_llm
import json
import xml.etree.ElementTree as ET
from lxml import etree
import time
import os
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from rapidfuzz import fuzz
import subprocess

def keyword_extractor(step_str,filtered_steps,serviceProvider,model,apiKey,service_accounts):
    usage = {}
    action = ["tap","enter","wait","verify","scroll","navigation","get"]
    prompt = f"""
   You are an expert in mobile app testing.
From the step: "{step_str}", extract ONLY the meaningful keywords so that i can search for the element in the dom.
Rules:
- understand the step and context from the {filtered_steps}.and only extract keywords from current step and dont extract from all steps.
- 3 to 5 keywords maximum.
- If the step is about entering text, Do NOT include entered input values from the step.
- First keywords should be from step next Keywords must be distinct and based on the element's label meaning only.
- **Keywords can be string or number if the step contains a number it can be any number,must include that number in keywords.**
- Do Not include any other unrelated keywords for step.
- Do NOT include generic UI words (button, field, etc) and action words (tap, click, press, etc).
- Do NOT include status/technical words (displayed, enabled, authenticate, visible).
- If an element label contains multiple words (e.g., "Sign In", "Add to Cart"), keep them together as ONE keyword and do not split them and also for keywords you generated, do not split them.
-** element_name: extract name of the element that mentioned in the step {step_str} not from keywords or other steps.(eg:tap on x -> element_name:x).**
- action: tap for taping or selecting or clicking, enter for entering input, wait for waiting or sleeping, verify for verifying or checking,scroll for scrolling and swiping, navigation for mobile navigation buttons like back and home, get for getting,fetching element.
- action must be one of from this list {action}.if not one of them, return '0'. if step about set or find or press enter key action return '0'
Output format only:
{{
  "keywords": [key1,key2,key3,key4,key5],
  "element_name": "x",
  "action": "x"
}}
**Dont give any extra explanation or text.**
    """
    try:
        # Call Groq LLM using your wrapper
        response , usage= call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts)
        # print(response)
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try cleaning or fallback extraction
            cleaned = response.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
        logger.info("[JSON Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))
        if data.get("action") in ["0",0]:
            data["action"] = "combined"
        validated = KeywordResponse(**data)
        keywords = validated.keywords
        element_name = validated.element_name
        action = validated.action.value
        
        return keywords, element_name, action, usage["input_tokens"],usage["output_tokens"],usage["total_tokens"]
    except ValidationError as e:
        logger.error(f"Validation Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in keyword_extractor: {str(e)}")
        raise
 

def annotate_dom_with_ff_inspecter(page_source):
    try:
        root = ET.fromstring(page_source)
    except ET.ParseError as exc:
        raise ValueError(f"Unable to parse DOM: {exc}") from exc
    for index, element in enumerate(root.iter(), start=1):
        element.set("FF-inspecter", f"Fire-Flink-{index}")
    annotated_xml = ET.tostring(root, encoding="unicode")
    if page_source.lstrip().startswith("<?xml"):
        declaration_end = page_source.find("?>")
        if declaration_end != -1:
            declaration = page_source[:declaration_end + 2].strip()
            return f"{declaration}\n{annotated_xml}"
    return annotated_xml    

class ActionType(Enum):
    TAP = 'tap'
    INPUT = 'enter'
    WAIT = 'wait'
    VERIFY = 'verify'
    SCROLL = 'scroll'
    NAVIGATION = 'navigation'
    GET = 'get'
    COMBINED = 'combined'


class KeywordResponse(BaseModel):
    keywords: list[str] = Field(
        ...,
        description="The keywords extracted from the step.",
        examples=[["keyword1", "keyword2"]]
    )
    element_name: str = Field(
        "",
        description="element name or field name identified from the step.",
        examples=["element_name"]
    )
    action: ActionType = Field(
        ...,
        description="tap for TAP, enter for ENTERING INPUT.",
        examples=['x']
    )

class FFInspecterResponse(BaseModel):
    attribute_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element.",
        examples=["Fire-Flink-x"]
    )
    action: ActionType = Field(
        ...,
        description="tap for TAP, enter for ENTERING INPUT.",
        examples=['x']
    )
    input_text: str = Field(
        "",
        description="The input text provided for step.",
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
    nlp_name: str = Field(
        ...,
        description="The nlp name from the provided list if action is tap.",
        examples=["x"]
    )
    


class Extractor:
    def __init__(self, driver):
        self.driver = driver
        self.current_xml = ""
        self.animations_disabled = False

    def get_ui_dump(self):
        """Wait for DOM to stabilize before capturing page source."""
        self.current_xml == ""
        time.sleep(2)  
        self.current_xml  = self.driver.page_source
        logger.info("[INFO] Captured fresh DOM for step:")
        return self.current_xml


    def save_annotated_dom(self, annotated_dom):
        return annotated_dom

    def annotate_and_simplify_dom(self, keywords, raw_dom,step_index):
        try:
            annotated_dom = annotate_dom_with_ff_inspecter(raw_dom)
        except ValueError as dom_error:
            print(f"DOM Annotation Error: {dom_error}")
            raise ValueError(str(dom_error))

        # Save annotated DOM for debugging
        # folder_path = "Dom"
        # os.makedirs(folder_path, exist_ok=True)
        # with open(f"Dom/annotated_dom_step_{step_index}.xml", "w", encoding="utf-8") as f:
        #     f.write(annotated_dom)

        # Convert annotated DOM to simplified JSON
        root = ET.fromstring(annotated_dom)
        parent_map = {child: parent for parent in root.iter() for child in parent}
        def xml_to_tree(elem):
            return {
                "tag": elem.tag,
                "attributes": elem.attrib,
                "text": (elem.text or "").strip(),
                "_element": elem,            
                "children": [xml_to_tree(child) for child in elem]
            }

        xml_tree = xml_to_tree(root)

        flat_nodes = []  

        def simplify_and_flatten(node):
            simplified = {}
            attrs = node.get("attributes", {})
            simplified["tag"] = node.get("tag")

            skip_node = attrs.get("enabled") == "false"

            if "FF-inspecter" in attrs:
                simplified["FF-inspecter"] = attrs["FF-inspecter"]

            
            simplified["text"] = node.get("text", "") or attrs.get("text", "")
            

            important_attrs = [
                "resource-id", "content-desc", "pane-title", "clickable", "editable", "enabled","class","hint"
            ]
            for attr in important_attrs:
                if attr in attrs:
                    simplified[attr] = attrs[attr]

            search_parts = []
            if isinstance(simplified.get("text"), str) and simplified["text"].strip():
                search_parts.append(simplified["text"])

            for key in ["content-desc", "pane-title", "resource-id","hint"]:
                val = simplified.get(key)
                if isinstance(val, str) and val.strip():
                    search_parts.append(val)

            simplified["search"] = " ".join(search_parts).strip().lower()

            if not skip_node:
                flat_nodes.append({
                    "node": simplified,
                    "search": simplified["search"],
                    "element": node["_element"]   
                })


            children = []
            for child in node.get("children", []):
                simplified_child = simplify_and_flatten(child)
                if simplified_child and simplified_child.get("enabled") != "false":
                    children.append(simplified_child)

            if children:
                simplified["children"] = children

            return simplified

       

        simplified_json = simplify_and_flatten(xml_tree)
        # with open(f"Dom/simplified_nodes_step_{step_index}.json", "w", encoding="utf-8") as f:
        #     json.dump(simplified_json, f, indent=4, ensure_ascii=False) 


        def search_best(nodes, keywords, top_n=5, threshold=60):
            if isinstance(keywords, str):
                keywords = keywords.strip("[] ")
                keywords = [k.strip() for k in keywords.split(",")]
            keywords = [kw.lower() for kw in keywords]

            def slim(n):
                return {
                    k: n.get(k)
                    for k in [
                        "tag", "FF-inspecter", "text", "content-desc",
                        "resource-id", "class", "pane-title","hint",
                        "clickable", "editable", "enabled"
                    ]
                    if k in n
                }

            # 🔹 Build index for sibling lookup (DOM order)
            index_map = {}
            for i, item in enumerate(nodes):
                ff = item["node"].get("FF-inspecter")
                if ff:
                    index_map[ff] = i

            results = {}

            for kw in keywords:
                exact = []
                strong = []
                fuzzy = []

                for item in nodes:
                    node = item["node"]
                    text = item["search"].lower()
                    t  = (node.get("text") or "").lower()
                    cd = (node.get("content-desc") or "").lower()
                    rid = (node.get("resource-id") or "").lower()
                    hint = (node.get("hint") or "").lower()

                    # EXACT MATCH
                    if text == kw or t == kw or cd == kw or rid == kw or hint == kw:
                        exact.append(node)
                        continue

                    # STRONG PARTIAL MATCH
                    if kw in text or kw in t or kw in cd or kw in rid or kw in hint:
                        strong.append(node)
                        continue

                    # FUZZY MATCH
                    score = fuzz.partial_token_ratio(text, kw)
                    if score >= threshold:
                        fuzzy.append((score, node))

                # PRIORITY ORDER
                if exact:
                    selected = exact[:top_n]
                elif strong:
                    selected = strong[:top_n]
                else:
                    fuzzy = sorted(fuzzy, key=lambda x: x[0], reverse=True)
                    selected = [n for _, n in fuzzy[:top_n]]

                results[kw] = selected
            # 🔹 Grouping logic
            grouped_results = []
            used_nodes = set()

            def add_node_safe(node_dict, group, local_used):
                ff = node_dict.get("FF-inspecter")
                if not ff or ff in local_used:
                    return
                group.append(slim(node_dict))
                local_used.add(ff)


            for matched_nodes in results.values():
                for matched_node in matched_nodes:
                    selected_ff = matched_node.get("FF-inspecter")

                    if selected_ff not in index_map:
                        continue

                    if selected_ff in used_nodes:
                        continue

                    item = nodes[index_map[selected_ff]]
                    element = item["element"]
                    parent = parent_map.get(element)

                    group = []
                    local_used = set()

                    #  Always add selected node
                    add_node_safe(matched_node, group, local_used)

                    #  If selected is clickable → STOP
                    if matched_node.get("clickable") == "true":
                        grouped_results.append(group)
                        used_nodes.update(local_used)
                        continue

                    if parent is None:
                        grouped_results.append(group)
                        used_nodes.update(local_used)
                        continue

                    #  Parent check (unchanged)
                    if parent.attrib.get("clickable") == "true" and parent.attrib.get("enabled") != "false":
                        add_node_safe(parent.attrib, group, local_used)

                    siblings = list(parent)

                    try:
                        idx = siblings.index(element)
                    except ValueError:
                        idx = -1


                    # UPPER siblings logic 
                    if idx > 0:
                        for j in range(idx - 1, -1, -1):
                            upper = siblings[j]

                            # If upper sibling clickable → STOP
                            if upper.attrib.get("clickable") == "true" and upper.attrib.get("enabled") != "false":
                                add_node_safe(upper.attrib, group, local_used)
                                break

                            # Else check its immediate parent
                            upper_parent = parent_map.get(upper)
                            if upper_parent is not None and upper_parent.attrib.get("clickable") == "true" and upper_parent.attrib.get("enabled") != "false":
                                add_node_safe(upper_parent.attrib, group, local_used)
                                break


                    #  LOWER siblings logic 
                    if idx != -1:
                        for j in range(idx + 1, len(siblings)):
                            lower = siblings[j]

                            # If lower sibling clickable → STOP
                            if lower.attrib.get("clickable") == "true" and lower.attrib.get("enabled") != "false":
                                add_node_safe(lower.attrib, group, local_used)
                                break

                            # Else check its children
                            for child in lower:
                                if child.attrib.get("clickable") == "true" and child.attrib.get("enabled") != "false":
                                    add_node_safe(child.attrib, group, local_used)
                                    break
                            else:
                                continue  # no clickable child → try next lower sibling

                            break  # clickable child found → STOP

                    grouped_results.append(group)
                    used_nodes.update(local_used)



            # Step  find FIRST multi-node group index for each FF-inspecter
            first_multi_index = {}

            for i, group in enumerate(grouped_results):
                if len(group) > 1:
                    for node in group:
                        ff = node["FF-inspecter"]
                        if ff not in first_multi_index:
                            first_multi_index[ff] = i


            # Step  rebuild groups with strict rules
            final_results = []
            used_ff = set()

            for i, group in enumerate(grouped_results):
                new_group = []

                for node in group:
                    ff = node["FF-inspecter"]

                    if ff in used_ff:
                        continue

                    # single-node group but FF appears later in multi-node group
                    if len(group) == 1 and ff in first_multi_index:
                        continue

                    # FF belongs to a different (earlier) multi-node group
                    if ff in first_multi_index and first_multi_index[ff] != i:
                        continue

                    new_group.append(node)
                    used_ff.add(ff)

                if new_group:
                    final_results.append(new_group)

            grouped_results = final_results


            return grouped_results




        # Search for keywords in the DOM
        results = search_best(flat_nodes, keywords, top_n=5)
        logger.info(f"Results: {results}")

        # # Save for debugging
        # with open(f"Dom/filtered_{step_index}.json", "w", encoding="utf-8") as f:
        #     json.dump(results, f, indent=4, ensure_ascii=False)
        return annotated_dom, results
    
    def ff_inspecter_num_extractor(self, step, simplified_json, annotated_dom,filtered_steps, serviceProvider, model, apiKey,service_accounts):
        usage = {}
        nlp_list=("MOB_Tap","MOB_TapNTimes","MOB_DoubleTap","MOB_DoubleTapAtSpecifiedLocation","MOB_TapOnSpecifiedLocation",
        "MOB_Enter","MOB_EnterDataAndPressKey","MOB_EnterInputIntoElementFromClipBoard","MOB_EnterUrl","MOB_ClearThenEnterInput")
        # logger.info(f"Step: {simplified_json}")
        elementType = ["link","textfield","icon","button","radiobutton","checkbox","tab","action overflow button","hamburger menu","toggle button","steppers","sliders"]
        prompt = f"""
        You are an intelligent assistant that extracts structured UI action data.\n
Return **only valid JSON** in the following format:\n
**Dont give any extra explanation or text**
{{
  "attribute_value": "Fire-Flink-x",
  "action": "x",
  "input_text": "x",
  "keyword": "x",
  "element_type": "x",
  "nlp_name": "x"
}}

Rules:\n
You are an AI assistant. For the step: {step}, extract the element keyword from the step (the field name like 'Leaving from', 'Going To').
- Use context from all steps: {filtered_steps}, keyword and filtered dom to search for FF-inspecter. 
- **If step is tap on element of referenece element,if multiple elements are there ,choose element which is related to reference element.The element can be reference element's before or after sibling nodes in filtered dom json.**
- **For {step} if you can't find perfect matching element or no attribute in filtered dom JSON is related to {step} return attribute_value as Fire-Flink-0.**
- Don't think if type of element is found it is exact element, check with keyword and step.If it is not matched return Fire-Flink-0.
- **Find the FF-inspecter attribute value of the element in the filtered dom JSON whose text or content-desc or other attributes best or perfect match for the {step}.**
- Action: 'tap' for taping ,clicking and selecting, 'enter' for entering text. 
- For taping action dont take attribute_value of the node contining edittext in class, resource-id.
- Extract nlp_name from this list: {nlp_list} based on step. 
- For some steps you can see two inputs but you need to uderstand step and send the requred input_text. 
        ex:Double tap on the 30,50
        here  here input:30,50
- and for this MOB_TapNTimes nlps send number of times to tap as input_text.
- Extract input text from step for all actions,if input is not there give empty string "". 
- Based on step give most relevant type of element. use this list to choose element_type: {elementType} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
- Respond with valid JSON only.

STEP: {step}
filtered dom JSON: {simplified_json}
"""
        try:
            # Call Groq LLM using your wrapper
            response_text, usage = call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts)
            # print(response_text)

            # Parse JSON safely
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try cleaning or fallback extraction
                cleaned = response_text.strip().replace("```json", "").replace("```", "")
                data = json.loads(cleaned)
            logger.info("[JSON Extraction Success]:\n%s", json.dumps(data, indent=2, ensure_ascii=False))

            
            
            
            #  Validate with Pydantic model
            validated = FFInspecterResponse(**data)
            # logger.info(f"[Validation Success]: {validated}")

            num = validated.attribute_value.split('-')[-1]
            action = validated.action.value.lower() 
            input_text = validated.input_text
            element_type = validated.element_type
            keyword = validated.keyword
            nlp_name = validated.nlp_name
            
            if action == "tap" or action == "enter":
                action= nlp_name
            if num == 0:
                return -1, action, input_text,keyword, element_type,"",usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]
            

            tree = etree.fromstring(annotated_dom.encode('utf-8'))
            target = tree.xpath(f"//*[@FF-inspecter='Fire-Flink-{num}']")

            xpath_path = None

            if target:
                element = target[0]
                element_class = element.attrib.get("class", "").lower()

                # Check only if the action is 'enter'
                if action == "enter":
                    # Step 1: Check if current node is editable
                    if any(keyword in element_class for keyword in ["edittext","autocompletetextview"]):
                        xpath_path = etree.ElementTree(tree).getpath(element)
                        logger.info(f"[INFO] Current node is editable: Fire-Flink-{num}")
                    else:
                        # Step 2: If not editable, check immediate children
                        children = list(element)
                        editable_child = None
                        for child in children:
                            child_class = child.attrib.get("class", "").lower()
                            if any(keyword in child_class for keyword in ["edittext","autocompletetextview"]):
                                editable_child = child
                                break

                        if editable_child is not None:
                            xpath_path = etree.ElementTree(tree).getpath(editable_child)
                            # logger.info(f"[INFO] Found editable immediate child for Fire-Flink-{num}: {xpath_path}")
                        else:
                            # Step 3: Fallback to current node
                            xpath_path = etree.ElementTree(tree).getpath(element)
                            logger.info(f"[WARNING] No editable child found for Fire-Flink-{num}, using current node as fallback.")
                else:
                    # For non-input actions (tap/navigation)
                    xpath_path = etree.ElementTree(tree).getpath(element)
            else:
                logger.info(f"[ERROR] FF-inspecter node Fire-Flink-{num} not found in DOM.")


            return num, action, input_text,keyword, element_type , xpath_path, usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]

        except ValidationError as e:
            logger.info(f" Pydantic Validation Error]: {e}")
            return -1, None, "","","","",usage.get("input_tokens", 0), usage.get("output_tokens", 0), usage.get("total_tokens", 0)

        except Exception as e:
            logger.info(f"[ Error in ff_inspecter_num_extractor]: {e}")
            
            return -1, None, "", "","","",usage.get("input_tokens", 0), usage.get("output_tokens", 0), usage.get("total_tokens", 0)
        