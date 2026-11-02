import re
import json
import time
import os
import codecs
from bs4 import BeautifulSoup
from lxml import html, etree
from LLMcall import call_grok_llm
from dump import INJECT_AND_SERIALIZE_DOM_JS
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
from rapidfuzz import fuzz
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
import logging

from auto_healing import AutoHealing

def is_editable(el):
    tag = safe_lower(el.tag)
    elem_type = safe_lower(el.attrib.get("type", ""))

    return (
        tag in ["input", "textarea", "select"]
        or el.attrib.get("contenteditable", "") == "true"
        # or elem_type in ["text", "email", "password", "search", "tel", "number"]
    )

def safe_lower(value):
    """Safely convert value to lowercase string, handling non-string types."""
    if value is None:
        return ""
    try:
        return str(value).lower()
    except Exception:
        return ""

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding="utf-8")

# ------------------------------
# Annotate DOM with FF-Inspecter
# ------------------------------
def annotate_dom_with_ff_inspecter_html(page_source):
    """Add Fire-Flink IDs (FF-inspecter attributes) to every HTML element."""
    try:
        parser = html.HTMLParser(encoding="utf-8")
        tree = html.fromstring(page_source, parser=parser)
    except Exception as e:
        raise ValueError(f"Unable to parse HTML DOM: {e}")

    annotated_html = etree.tostring(tree, encoding="unicode", pretty_print=True)
    return annotated_html

def is_probable_path(value: str) -> bool:
    if not value or not isinstance(value, str):
        return False

    value = value.strip()

    # Reject emails explicitly
    if "@" in value or value.startswith("http"):
        return False

    # Windows absolute path (C:\ or D:\)
    if re.match(r"^[a-zA-Z]:[\\/]", value):
        return True

    # UNC path (\\server\share)
    if value.startswith("\\\\"):
        return True

    # Unix absolute path
    if value.startswith("/"):
        return True

    # Relative path
    if value.startswith("./") or value.startswith("../"):
        return True

    # Path-like string must contain a slash
    if ("/" in value or "\\" in value) and re.search(r"\.[a-zA-Z0-9]{1,6}$", value):
        return True

    return False



def normalize_llm_path(path: str) -> str:
    try:
        path = codecs.decode(path, "unicode_escape")
    except Exception:
        pass
    return os.path.normpath(path)


def keyword_extractor(step_str,filtered_steps,serviceProvider,model,apiKey,service_accounts):
        
        action = ["enter","wait","verify","scroll","navigate","click","maximize","get","upload","close","open","drag_and_drop","switch","cleartext"]
        prompt = f"""
    You are an expert in Web application testing.
    From the step: "{step_str}", extract ONLY the meaningful keywords so that i can search for the element in the dom.
    Rules:
    - Only give response for the current step "{step_str}".
    - understand the step and context from the {filtered_steps}.and keywords should be from step. it should not be related to other steps.
    - 3 to 5 keywords maximum. don't give more than 5 keywords.
    - If the step is about entering text or Uploading file, Should NOT include input value from the step into keywords.
    - If the step has words like tag name audio, video, image,svg, checkbox etc, include them in the keywords.
    - If icon is metioned in step than 'svg' should add in keywords and for Upload action first keyword should be 'file'.
    - First keywords should be from step next Keywords must be distinct and based on the element's label meaning only.
    - If a keyword contains exactly two words, you MUST always include both the spaced and concatenated (no-space) versions; omission of either is invalid.
    - Do NOT split single-word keywords and do NOT include relation terms (above, below, next to, etc.) in keywords.
    - Treat each keyword independently—never merge different keywords or combine them with relation words.
    - Example: Click on Sign In above Create Account button → ["Sign In", "SignIn", "Create Account", "CreateAccount"]
    - Keywords can be string or number if the step contains a number ,add it also as keyword.
    - Do Not include any other unrelated keywords for step. 
    - **Do NOT include generic UI words (button, field, etc) and action words (tap, click, press, etc).**
    - Do NOT include status/technical words (displayed, enabled, authenticate, visible).
    - If an element label contains multiple words (e.g., "Sign In", "Add to Cart"), keep them together as ONE keyword and do not split them and also for keywords you generated, do not split them.
    - element_name: extract name of the element that mentioned in the the {step_str}.(eg:tap on x -> element_name:x) keep element_name as short as possible and make the first letter of first word of the element_name as capital. beacuse element_name is also used to find element in the dom. and if element_name is not mentioned in step than return action of the step as element_name.
    - action: click for taping, clicking or selecting, enter for entering input, wait for waiting or sleeping,scroll for scrolling and swiping, navigate for navigating to page using url or navigateing back to previous page, get for getting,fetching element,maximize for maximizing browser window, close for closing browser window,open for opening browser window, upload for uploading file using path, drag_and_drop for dragging and dropping element, switch is for switching to tab or window or frame,cleartext for clearing or removing text from element.
    - action must be one of from this list {action}.if not one of them, return '0'. if step about set or find action return '0'
    - For navigate action, keywords should contain only one keyword which is full url from the step and should not include any other text. and if step has another actions, including navigate action, don't return navigate action return another action witch is in the step. and element_name should be "URL".
    Navigate action is allowed only when the step intent is purely navigation (e.g., "Navigate to URL").
    If the step includes verification intent (verify/check/confirm/etc), you MUST return "verify" and MUST NOT return "navigate".
    only give navigate action if step has only navigate action.
         
    Output format only:
    {{
    "keywords": [key1,key2,key3,key4,key5],
    "element_name": "x",
    "action": "x"
    }}

    No other text.
        """
        try:
            # Call Groq LLM using your wrapper
            response = call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts)
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
            
            return keywords, element_name, action
        except ValidationError as e:
            logger.error(f"Validation Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in keyword_extractor: {str(e)}")
            raise

# ---  Define Enum for Actions ---
class ActionType(Enum):
    click = 'click'
    DOUBLE_CLICK = 'doubleclick'
    RIGHT_CLICK = 'rightclick'
    ENTER = 'enter'
    MAXIMIZE = 'maximize'
    WAIT = 'wait'
    VERIFY ='verify'
    SCROLL = 'scroll'
    SWITCH = 'switch'
    NAVIGATE = 'navigate'
    GET = 'get'
    UPLOAD = 'upload'
    OPEN = 'open'
    CLOSE = 'close'
    CLEARTEXT = 'cleartext'
    CLEARANDENTER = 'clearandenter'
    DRAG_AND_DROP = 'drag_and_drop'
    EnterDataToAlert = "EnterDataToAlert"
    ClickOkOnAlertPopup = "ClickOkOnAlertPopup"
    ClickCancelOnAlertPopup = "ClickCancelOnAlertPopup"

# --- Pydantic model for structured LLM output ---
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

# --- Pydantic model for structured LLM output ---
class FFInspecterResponse(BaseModel):
    attribute_value: str = Field(
        ...,
        description="The FF-inspecter value of the matched element.",
        examples=["Fire-Flink-x"]
    )
    action: ActionType = Field(
        ...,
        description="click for CLICK, enter for ENTERING INPUT,maximize for maximizing browser window  wait for WAITING,verify For VERIFING,scroll for SCROLLING",
        examples=['x']
    )
    input_text: str | int |None = Field(
         default=None,
        description="The text input provided (only if action=enter) and for waiting step.",
        examples=["x"],
       
    )
    # nlp_name: str = Field(
    #     ...,
    #     description="The nlp name of the step.",
    #     examples=["x"]
    # )
    element_type: str = Field(
        ...,
        description="The type of the element.",
        examples=["x"]
    )
    keyword: str = Field(
        "x",
        description="element keyword or field name identified from the step.",
        examples=[ "x","x"]
    )
    num_of_scrolls: str | None = Field(
        default=None,
        description="The number of times to scroll (only if action=scroll).",
        examples=[1, 2]
    )
    direction: str | None = Field(
        default=None,
        description="The direction of the scroll (only if action=scroll).",
        examples=["up", "down"]
    )

# HTML Extractor Class

class HtmlExtractor:
    def __init__(self, driver):
        self.driver = driver
        self.current_html = ""
        self.auto_healing = AutoHealing()

    
    # Annotate DOM + Convert to JSON using BeautifulSoup
    def annotate_and_simplify_dom(self, keywords, raw_dom, step_index):
        """Annotate DOM and build recursive JSON using BeautifulSoup."""
        try:
            printed_annotated_dom = annotate_dom_with_ff_inspecter_html(raw_dom)
        except ValueError as dom_error:
            raise ValueError(str(dom_error))

        # Save annotated HTML for debugging
        os.makedirs("dom_dumps", exist_ok=True)
        annotated_path = f"dom_dumps/annotated_html_step_{step_index}.html"
        with open(annotated_path, "w", encoding="utf-8") as f:
            f.write(printed_annotated_dom)

        annotated_dom = raw_dom

        # ---- Convert to JSON using BeautifulSoup ----
        soup = BeautifulSoup(annotated_dom, "html.parser")


        flat_nodes = []

        def simplify_and_flatten(soup):
            for el in soup.find_all(True):

                tag = el.name.lower()

                if tag == "meta":
                    continue

                if tag not in ("select", "option"):
                    if (
                        (el.get("element-visibility") == "hidden"
                        or el.get("element-covered") == "true") and el.get("element-covered-by-tag") != "iframe"
                    ):
                        continue
                

                simplified = {"tag": el.name}

                if el.has_attr("ff-inspect"):
                    simplified["FF-inspecter"] = el["ff-inspect"]

                if el.has_attr("ff-xpath"):
                    simplified["ff-xpath"] = el["ff-xpath"]

                # direct text only
                direct_text = "".join(
                    t.strip()
                    for t in el.find_all(string=True, recursive=False)
                    if t.strip()
                )

                clean_text = re.sub(r"[^a-zA-Z0-9\s]", " ", direct_text).strip()

                if clean_text:
                    simplified["text"] = clean_text[:200]

                for attr, val in el.attrs.items():
                    if attr.lower() not in {"style", "onclick", "onchange","href",
                                            "oninput", "onmouseover", "onfocus","ff-inspect","element-visibility",
                                            "element-pointer-events","element-zindex","element-covered"}:
                        simplified[attr] = val


                parts = set()
                if clean_text and len(clean_text) <= 70:
                    parts.add(clean_text.lower())

                EXCLUDED_ATTRS = {
                    "class", "style", "onclick", "onchange",
                    "oninput", "onmouseover", "onfocus",
                    "tabindex", "role", "href"
                }

                for key, value in simplified.items():
                    if not value:
                        continue
                    if key.lower() in EXCLUDED_ATTRS:
                        continue
                    if key in ("tag", "FF-inspecter", "search", "ff-xpath"):
                        continue

                    v = re.sub(r"[^a-zA-Z0-9\s]", " ", str(value)).strip().lower()
                    if v:
                        parts.add(v)

                simplified["search"] = " ".join(parts).strip()

                flat_nodes.append({
                    "node": simplified,
                    "search": simplified["search"]
                })


        simplify_and_flatten(soup)
        with open(f"dom_dumps/simple_{step_index}.json", "w", encoding="utf-8") as f:
            json.dump(flat_nodes, f, indent=2, ensure_ascii=False)

        def add_structure(nodes):
            ff_to_xpath = {
                n["FF-inspecter"]: n.get("ff-xpath")
                for n in nodes
                if n.get("FF-inspecter") and n.get("ff-xpath")
            }

            def parent_xpath(x):
                return x.rsplit("/", 1)[0] if "/" in x else None

            structured = []

            for node in nodes:
                ff = node.get("FF-inspecter")
                xp = node.get("ff-xpath")

                parent = None
                children = []
                siblings = []

                if ff and xp:
                    px = parent_xpath(xp)

                    for other_ff, other_xp in ff_to_xpath.items():
                        if other_ff == ff:
                            continue

                        if other_xp.startswith(xp + "/"):
                            children.append(other_ff)

                        elif px and parent_xpath(other_xp) == px:
                            siblings.append(other_ff)

                    for other_ff, other_xp in ff_to_xpath.items():
                        if other_xp == px:
                            parent = other_ff
                            break

                clean = dict(node)
                clean.pop("ff-xpath", None)

                clean["parent"] = parent
                clean["children"] = children[:3]
                clean["siblings"] = siblings[:3]
                clean["has_structure"] = bool(parent or children or siblings)

                structured.append(clean)

            return structured
 
        def search_best(nodes, keywords, top_n=5, threshold=60):

            # -----------------------------
            # Normalize keywords
            # -----------------------------
            if isinstance(keywords, str):
                keywords = keywords.strip("[] ")
                keywords = [k.strip() for k in keywords.split(",")]

            keywords = [
                re.sub(r"[^a-zA-Z0-9\s]", " ", kw).strip().lower()
                for kw in keywords
            ]
            # logger.info(keywords)

            # -----------------------------
            # Helpers
            # -----------------------------
            def get_xpath(node):
                return node.get("ff-xpath")

            def is_child(parent, child):
                return child.startswith(parent + "/")

            def is_sibling(x1, x2):
                return x1.rsplit("/", 1)[0] == x2.rsplit("/", 1)[0]

            def ff_number(val):
                if not val:
                    return 0
                m = re.search(r"(\d+)$", val)
                return int(m.group(1)) if m else 0

            # -----------------------------
            # Context expansion
            # -----------------------------
            def add_with_context(idx, total_len, idx_set):
                # prev, self, next
                for i in (idx - 1, idx, idx + 1):
                    if 0 <= i < total_len:
                        node_data = nodes[i]["node"]
                        if node_data.get("FF-inspecter"):   # ✅ only valid FF nodes
                            idx_set.append(i)

                current = nodes[idx]["node"]
                cx = get_xpath(current)
                if not cx:
                    return

                # one real child
                for j, item in enumerate(nodes):
                    nx = get_xpath(item["node"])
                    if nx and is_child(cx, nx):
                        if item["node"].get("FF-inspecter"):   # ✅ safe check
                            idx_set.append(j)
                        break

                # one real sibling
                for j, item in enumerate(nodes):
                    nx = get_xpath(item["node"])
                    if nx and is_sibling(cx, nx) and j != idx:
                        if item["node"].get("FF-inspecter"):   # ✅ safe check
                            idx_set.append(j)
                        break


            # -----------------------------
            # Matching phase
            # -----------------------------
            results = {}

            for kw in keywords:
                exact, strong, fuzzy_list, tag_matches = [], [], [], []
                total_len = len(nodes)

                for idx, item in enumerate(nodes):
                    node = item["node"]
                    search_text = node.get("search", "").lower()
                    tag_name = node.get("tag", "").lower()

                    matched = False

                    if search_text == kw:
                        exact.append(idx)
                        matched = True

                    if kw in search_text:
                        strong.append(idx)
                        matched = True

                    if not matched:
                        score = fuzz.token_set_ratio(search_text, kw)
                        if score >= threshold:
                            fuzzy_list.append((score, idx))

                    if kw == tag_name or kw in tag_name:
                        tag_matches.append(idx)

                collected_idxs = []

                for idx in exact:
                    add_with_context(idx, total_len, collected_idxs)
                    if len(collected_idxs) >= top_n * 4:
                        break

                for idx in strong:
                    add_with_context(idx, total_len, collected_idxs)
                    if len(collected_idxs) >= top_n * 4:
                        break

                if len(collected_idxs) < top_n * 4:
                    for _, idx in sorted(fuzzy_list, reverse=True):
                        add_with_context(idx, total_len, collected_idxs)
                        if len(collected_idxs) >= top_n * 4:
                            break

                if len(collected_idxs) < top_n * 4:
                    for idx in tag_matches:
                        add_with_context(idx, total_len, collected_idxs)
                        if len(collected_idxs) >= top_n * 4:
                            break

                collected_idxs = list(dict.fromkeys(collected_idxs))
                results[kw] = [nodes[i]["node"] for i in collected_idxs]

            # -----------------------------
            # Unique nodes
            # -----------------------------
            unique, seen = [], set()
            for lst in results.values():
                for n in lst:
                    key = n.get("FF-inspecter")
                    if key and key not in seen:
                        seen.add(key)
                        unique.append(n)

            unique.sort(key=lambda x: ff_number(x.get("FF-inspecter")))

            # -----------------------------
            # Build structure
            # -----------------------------
            ff_to_xpath = {
                n["FF-inspecter"]: n.get("ff-xpath")
                for n in unique
                if n.get("FF-inspecter") and n.get("ff-xpath")
            }

            def parent_xpath(x):
                return x.rsplit("/", 1)[0] if "/" in x else None

            structured = []

            for node in unique:
                ff = node.get("FF-inspecter")
                xp = node.get("ff-xpath")

                parent = None
                children = []
                siblings = []

                if ff and xp:
                    px = parent_xpath(xp)

                    for other_ff, other_xp in ff_to_xpath.items():
                        if other_ff == ff:
                            continue

                        if other_xp.startswith(xp + "/"):
                            children.append(other_ff)

                        elif px and parent_xpath(other_xp) == px:
                            siblings.append(other_ff)

                    for other_ff, other_xp in ff_to_xpath.items():
                        if other_xp == px:
                            parent = other_ff
                            break

                # -----------------------------
                # FINAL SLIM PAYLOAD
                # -----------------------------
                slim = {
                    k: v
                    for k, v in node.items()
                    if v and k not in {"search", "ff-xpath","href","src"}
                }


                # add minimal structure only if exists
                rel = {}
                ff_to_node = {n["FF-inspecter"]: n for n in unique}

                def mini(n):
                    return {
                        k: v
                        for k, v in n.items()
                        if v and k not in {"search", "ff-xpath","href","src"}
                    }

                # parent
                if parent and parent in ff_to_node:
                    rel["parent"] = mini(ff_to_node[parent])

                # children
                if children:
                    rel["children"] = [
                        mini(ff_to_node[c]) for c in children[:2]
                        if c in ff_to_node
                    ]

                # siblings
                if siblings:
                    rel["siblings"] = [
                        mini(ff_to_node[s]) for s in siblings[:2]
                        if s in ff_to_node
                    ]

                if rel:
                    slim["relationship"] = rel

                structured.append(slim)

            return structured 





        # Search for keywords in the DOM
        results = search_best(flat_nodes, keywords, top_n=20)
        # logger.info(f"Results: {json.dumps(results,indent=2,ensure_ascii=False)}")
        # logger.info(f"Results: {results}")
        
        # Save output
        with open(f"dom_dumps/filtered_{step_index}.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return annotated_dom, results




    # Extract FF-Inspecter number via LLM
    def ff_inspecter_num_extractor(self, step, step_action, simplified_json, annotated_dom,
                                   element_name, test_steps,server_host, serviceProvider, model, apiKey,service_accounts, isAlert=False, isDrag=False):
        """Use LLM to map test step → FF-inspecter element."""
        usage = 0

        element_type = ['link','textfield','icon','button','radioButton','text','textarea','image','dropdown','checkbox','tab','action overflow button','hamburger icon','toggle button','suggestion','time picker','date picker','toaster message','card','tooltip','option','calender','sliders','visual testing']

        # --- Token size check REMOVED (Tiktoken removed) ---
        # We now use the filtered simplified_json from RapidFuzz
        json_payload = simplified_json
        # logger.info(f"[INFO] Using filtered DOM from RapidFuzz.")

        NLP_DATA =  [ "DoubleClickAtSpecifiedLocationWithInElement", "ClickAtSpecifiedLocation", "DoubleClick", "Click", "ClickUsingJS", "RightClick", 
        "WaitUntilElementIsClickable", "ClickNTimesUsingJS", "MouseClickOnCurrentCursorPointNTimes", "ClickNTimes", "ClickOnListOfElements", 
        "WaitAndClick", "ClickOnCanvasPartition", "ClickOnRelativeElement","MouseClickOnCurrentCursorPoint", "MouseDoubleClickAtCursorPoint", "ClickOkOnAlertPopup", "ClickCancelOnAlertPopup",
        "SendKeys", "WaitAndSendKeys", "SendKeysToRelativeElement"]
        # enter = ["enter", "clearandenter"]
        click = ["click", "doubleclick", "rightclick"]
        alert = ["ClickOkOnAlertPopup", "ClickCancelOnAlertPopup","EnterDataToAlert","GetTextPresentOnAlertPopup","VerifyAlertPopupIsDisplayed","VerifyAlertPopUpMessageContainsString","WaitTillAlertIsPresent","VerifyTextPresentOnAlertPopup"]
        if isAlert:
            prompt = f"""
        You are given a Selenium test step that requires interaction with a browser alert popup.
        Step: {step}
        Based on the step, return the required alert element with input in the following JSON format only:
        {{
        "action": x,
        "input_text": "text to enter" | "None"
        }}
        Rules:
        - if the alert requires entering text inpt alert or for verification if we need compare text than extract that text and give as input_text.
        - If no input is needed, set "input_text" to "None".
        - if step is about verify text present than map to VerifyTextPresentOnAlertPopup.and if step is about verify text contains than map to VerifyAlertPopUpMessageContainsString.
        - Do not add explanations, comments, or extra text.
        - send one action from this list only {alert} witch is related to step.
        - Output must be valid JSON.
        """
        elif isDrag:
            prompt = f""" 
            -You are an intelligent assistant that extracts structured UI action data.
            -Given a structured UI JSON representation with uniquely identified elements (ff-inspect values like Fire-Flink-1, Fire-Flink-2, Fire-Flink-3... in DOM order), 
            -locate the most appropriate element for an automation step by performing keyword-based matching using exact, partial, and fuzzy strategies, and 
            return the identifier of the best match.
             Return **only valid JSON** in the following format:
            {{
            "drag": "Fire-Flink-x",
            "drop": "Fire-Flink-x",
            "action": "Builtin_DragAndDropToElement",
            "drag_element_name": "x",
            "drop_element_name": "x",
            "element_type_of_drag": "x",
            "element_type_of_drop": "x"
            }} 
            
            - **For Action "drag_and_drop":**
                - Step: {step}
                - Use the {simplified_json} to find the element.
                - Identify the **Source Element** (the element to be dragged) and return its FF-inspecter value in drag field.
                - Identify the **Destination Element** (where it should be dropped) and return its FF-inspecter value in drop field.
                - If you cannot find either, return Fire-Flink-0,Fire-Flink-0.
                - Extract drag_element_name and drop_element_name from the step. it u cant find return drag,drop.
                - Based on step give most relevant type of element for drag and drop. use this list to choose element_type: {element_type} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
            - send action as Builtin_DragAndDropToElement
            Respond with valid JSON only.do not give extra text or any other explanation. or dont give in list formate.
            """
        elif step_action in ["wait", "scroll"]:
            prompt = f"""
            -You are an intelligent assistant that extracts structured UI action data.
            -Given a structured UI JSON representation with uniquely identified elements (ff-inspect values like Fire-Flink-1, Fire-Flink-2, Fire-Flink-3... in DOM order), 
            -locate the most appropriate element for an automation step by performing keyword-based matching using exact, partial, and fuzzy strategies, and 
            `return the identifier of the best match.
            
            Return **only valid JSON** in the following format:
            {{
            "attribute_value": "Fire-Flink-x",
            "action": "x",
            "input_text": "x",
            "keyword": "x",
            "num_of_scrolls": "0",
            "direction": "down",
            "element_type": "x"
            }}

            Rules:
            You are an AI assistant. For the step: {step}, extract the element keyword from the step (the field name like 'Leaving from', 'Going To').
            - Use context from the {test_steps}, keyword and filtered dom to search for FF-inspecter. 
            - **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
            - If multiple matches exist, use the reference element and choose the closest match by ff-inspect distance.
            - Respect direction (up/down), default is down.
            - Do not return elements far away from the reference.
            - Select the closest semantic match to {step} and return only its attribute_value, else Fire-Flink-0.
            - Action: 'scroll' for scrolling or swipping, 'wait' for waiting or sleeping. 
            - For Action "scroll" extract which element to find as input text and num_of_scrolls and direction from step if they are available in step if not return num_of_scrolls as 0 and direction as down.
            - For Action "wait" extract wait time from step as input text and dont add any  sec or second or s in input_text.only return the number.
            - Based on step give most relevant type of element. use this list to choose element_type: {element_type} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
            - if u cant find any input_text or any other dont give null just return them "" empty.
            STEP: {step}
            Simplified JSON: {simplified_json}
        """
        else:
            prompt = f"""
            -You are an intelligent assistant that extracts structured UI action data.
            -Given a structured UI JSON representation with uniquely identified elements (ff-inspect values like Fire-Flink-1, Fire-Flink-2, Fire-Flink-3... in DOM order), 
            -locate the most appropriate element for an automation step by performing keyword-based matching using exact, partial, and fuzzy strategies, and 
            `return the identifier of the best match.
            
        Return **only valid JSON** in the following format:
        {{
        "attribute_value": "Fire-Flink-x",
        "action": "x",
        "input_text": "x",
        "keyword": "x",
        "num_of_scrolls": "0",
        "direction": "down",
        "element_type": "x"
        }} 

        Rules:
        You are an AI assistant. For the step: {step}, extract the element keyword from the step (the field name like 'Leaving from', 'Going To').
        - Use context from the {test_steps}, keyword and Simplified dom to search for FF-inspecter. 
        - **Find the FF-inspecter attribute value of the element in the Simplified JSON whose text or attributes best match the {step}.**
        - If multiple matches exist, use the reference element and choose the closest match by ff-inspect distance.
         **important example: step: "click on login below user login" 
                    simplified json: 
                                login - ff-inspect-300
                                user login - ff-inspect-790
                                login - ff-inspect-803
                                then should return login - ff-inspect-803 witch is near to user reference element user login - ff-inspect-790**
        - Respect direction (up/down), default is down.
        - Do not return elements far away from the reference.
        - Select the closest semantic match to {step} and return only its attribute_value, else Fire-Flink-0.
        - Action: {click} for clicking or selecting, enter for entering text,clearandenter for clearing text and than entering text,  'upload' for uploading file, 'drag_and_drop' for dragging and dropping, 'cleartext' for clearing text. 
        - For click action, if only step involving 'clicking on icon' then try to return related svg tags attribute_value, if they are available in simplified json.
        - For Action entering extract input text from step.
        - **For entering actions, never directly select a input tag if should be realted to step; if u can't find input tag related to step then prefer the closest label/span/div/b/i etc, it can be any tag related to the step.**
        - **For entering step if you can't find perfect matching element return attribute_value as Fire-Flink-0 for the step. it should be exact match for the step.**
        - For entering step, If the step implies autogenerated data or random data(email, phone, credentials, identifiers, etc.), generate a valid dummy input_text suitable for the field. 
        example: step: "Enter sss.@gmail.com in email field" and step : 
                you should check only for email in Simplified JSON and input_text should be "sss.@gmail.com" dont add any extra text.
        - For Action "upload" extract file path from step.
        - if u cant find any input_text or any other dont give null just return them "" empty.
        - Based on step give most relevant type of element. use this list to choose element_type: {element_type} and Never change syntax of element_type, follow the syntax of element_type in list.if element_type is not there in list return 'link'.
        STEP: {step}
        Simplified JSON: {simplified_json}
    """
# - for step send most relevant nlp_name of the step from the {NLP_DATA} list. for scroll give nlp_name as scroll and for wait give nlp_name as wait.
# - for clicking on Specified Location send coordinates as input first x and second y seperated by coma ex: input_text:30,40

        try:
            # Call the LLM
            response_text = call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts)

            # logger.info(response_text)

            raw = response_text.strip().replace("```json", "").replace("```", "")

            # Remove trailing commas before closing braces/brackets
            raw = re.sub(r",\s*([}\]])", r"\1", raw)

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.error("JSON parse failed even after cleanup: %s\nRaw text:\n%s", e, raw)
                raise
            log_data = {k: v for k, v in data.items() if k != "attribute_value"}

            logger.info(
                "[JSON Extraction Success]:\n%s",
                json.dumps(log_data, indent=2, ensure_ascii=False)
            )

            if not isAlert and not isDrag :
                # Validate with Pydantic
                validated = FFInspecterResponse(**data)
                num = validated.attribute_value.split('-')[-1]
                num = validated.attribute_value.split('-')[-1]
                action = safe_lower(validated.action.value)
                input_text = validated.input_text
                num_of_scrolls = validated.num_of_scrolls
                # nlp_name = validated.nlp_name
                direction = validated.direction
                keyword = validated.keyword
                element_type = validated.element_type
                xpath_path=""

                if isinstance(input_text, str) and is_probable_path(input_text):
                    normalized = normalize_llm_path(input_text)
                    logger.info(
                        "[Input Text] Detected file path. Original=%s | Normalized=%s",
                        input_text,
                        normalized
                    )
                    input_text = normalized
                if num == "0" and action not in  ["wait","enterdatatoalert","clickokonalertpopup","clickcancelonalertpopup"]:
                    return num, action, input_text, keyword, element_type, num_of_scrolls, direction, xpath_path

                if action not in ["maximize", "wait","enterdatatoalert","clickokonalertpopup","clickcancelonalertpopup"]:
                    tree = html.fromstring(annotated_dom)
                    target = tree.xpath(f"//*[@ff-inspect='Fire-Flink-{num}']")

                    if target:
                        element = target[0]
                    if target:
                        element = target[0]
                        tag = safe_lower(element.tag)
                        elem_type = safe_lower(element.attrib.get("type", ""))

                        # Action == "enter" → find editable node
                        if action == "enter" or action == "upload":
                            # Current element editable
                            if is_editable(element):
                                xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)

                            else:
                                # Search editable descendant
                                editable_child = None
                                for child in element.iter():
                                    if is_editable(child):
                                        editable_child = child
                                        break

                                if editable_child is not None:
                                    xpath_path = editable_child.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(editable_child)

                                else:
                                    # Try next 10 FF elements
                                    found = False
                                    for offset in range(1, 11):  # try +1 to +10
                                        num = int(num)
                                        next_num = num + offset
                                        next_target = tree.xpath(
                                            f"//*[@ff-inspect='Fire-Flink-{next_num}']"
                                        )

                                        if next_target and is_editable(next_target[0]):
                                            element = next_target[0]
                                            num = next_num            # update FF number
                                            logger.info(f"Found editable element with FF number {num}")
                                            xpath_path = (
                                                element.attrib.get("ff-xpath")
                                                or etree.ElementTree(tree).getpath(element)
                                            )
                                            found = True
                                            break

                                    # Final fallback
                                    if not found:
                                        xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)


                        else:
                            # For click/tap/navigation actions
                            xpath_path = element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element)

                    # logger.info(f"FF number: {num}")

                    # Fire parallel request for auto-healing
                    # logger.info(f"[Auto Healing] Triggering request for element: {element_name} (ID: Fire-Flink-{num})")
                    if action not in ["wait", "maximize","enterdatatoalert","clickokonalertpopup","clickcancelonalertpopup"] and str(num) != "0":
                        self.auto_healing.send_locator_request(annotated_dom, f"Fire-Flink-{num}", element_name,server_host, source="primary")
                    return num, action, input_text, keyword, element_type, num_of_scrolls, direction, xpath_path
                else:
                    
                    # Fire parallel request for auto-healing
                    # logger.info(f"[Auto Healing] Triggering request for element: {element_name} (ID: Fire-Flink-{num})")
                    if action not in ["wait", "maximize","enterdatatoalert","clickokonalertpopup","clickcancelonalertpopup"] and str(num) != "0":
                        self.auto_healing.send_locator_request(annotated_dom, f"Fire-Flink-{num}", element_name,server_host, source="primary")
                    
                    return num, action, input_text, keyword, element_type, num_of_scrolls, direction, xpath_path
            elif isDrag:
                action = safe_lower(data.get("action"))
                drag = data.get("drag").split("-")[-1]
                drop = data.get("drop").split("-")[-1]
                drag_element_name = data.get("drag_element_name")
                drop_element_name = data.get("drop_element_name")
                element_type_of_drag = data.get("element_type_of_drag")
                element_type_of_drop = data.get("element_type_of_drop")
                element_type = element_type_of_drag + "_" + element_type_of_drop
                attempt =[]
                attempt.append(drag)
                attempt.append(drop)
                xpath_path = [] 
                for idx, i in enumerate(attempt):
                    i_int = int(i)
                    tree = html.fromstring(annotated_dom)
                    target = tree.xpath(f"//*[@ff-inspect='Fire-Flink-{i_int}']")

                    if target:
                        element = target[0]
                        xpath_path.append(element.attrib.get("ff-xpath") or etree.ElementTree(tree).getpath(element))
                        
                        # Trigger auto-healing for each element
                        elem_name = element_name if idx == 0 else drop_element_name
                        self.auto_healing.send_locator_request(annotated_dom, f"Fire-Flink-{i_int}", elem_name, server_host, source="primary")
       
                return action, drag, drop, xpath_path , drag_element_name, drop_element_name, element_type
            elif step_action in ["wait", "scroll"]:

                action = data.get("action").lower()  
                input_text = data.get("input_text") or ""
                num_of_scrolls = data.get("num_of_scrolls") or ""
                direction = data.get("direction") or ""
                element_type = data.get("element_type")
                return action, input_text, num_of_scrolls, direction, element_type
            else:
                action = safe_lower(data.get("action"))  
                input_text = data.get("input_text") or "" 
                return action, input_text
        except ValidationError as e:
            logger.error(f"[Pydantic Validation Error]: {e}")
            raise e

        except Exception as e:
            logger.error(f"[ff_inspecter_num_extractor failed]: {e}")
            raise e