import base64
import openai
import os
import re
import json
import xml.etree.ElementTree as ET
from lxml import etree
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def find_element_index(driver,step,filtered_steps,centers,clickable_boxes,dom,keyword,action =None,input_value=None,element_type=None,element_name = None):
  
    screenshot_path = "img/numbered_boxes_final.png"  

    with open(screenshot_path, "rb") as f:
        screenshot = base64.b64encode(f.read()).decode("utf-8")
        
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    client = openai.OpenAI(api_key=api_key)

    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""
You are a precise automation assistant.
- You are given an image containing multiple elements outlined with Red bounding boxes.Each bounding box has a small black index number label drawn above it (like 1, 2, 3...).
- Do not treat numbers appearing in the step as index numbers.if any number appears in the step it is not an index number.
- Use the context from the all steps {filtered_steps}
- **Analyze the user's {step} and action done by that step {action} determine which UI element in the screenshot corresponds semantically to that action.
- for action enter check for edit text field and choose index number of that box.
- **pick the index number that is on the box where element present that best matches semantically or visually to that action of the given {step}.**
- Identify which element number (from the image) best matches that step.
- Return the **index** number as shown in the image (1-based).
- if there are two elements that match step and one have box and other doesn't have box then prefer the one with box and return that index number.
- if no correct element found or if none of correct elements has no box,then return 0.

Return ONLY raw JSON (no code block formatting, no ```json, no explanation).

{{
  "index": <number or 0>,
}}

Now, Analyze the step:
Step: "{step}"
"""
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot}"}
                }
            ]
        }
    ]

    response= client.chat.completions.create(
        model="gpt-4.1",
        temperature=0,
        messages=prompt,
    )
    try:
        content = response.choices[0].message.content.strip()
        usage = response.usage
        total_tokens = usage.total_tokens
        input_tokens=usage.prompt_tokens
        completion_tokens=usage.completion_tokens
        logger.info(f"total tokens :{total_tokens},completion_tokens:{completion_tokens},input_tokens:{input_tokens}")
    except (KeyError, IndexError) as e:
        raise Exception(f"Unexpected response format from Vision LLM: {response}")
    if content.startswith("```"):
        content = content.strip("`") 
        content = re.sub(r"^json\s*", "", content, flags=re.IGNORECASE)
        content = content.replace("```", "").strip()
    try:
        data = json.loads(content)
        logger.info(f"JSON response from LLM: {data}")
    except json.JSONDecodeError:
        raise Exception(f" Invalid JSON response from LLM: {content}")

    index = data.get("index")

    if index is None or index == "0" or index == 0:
        logger.info(" No matching element found.")
        memory={
            "step":step,
            "type":element_type,
            "action": action,
            "keyword": keyword,
            "result":False,
            "input": input_value,
            "xpath": "",
            "element_name":element_name
            
        }
        return False, memory,input_tokens,completion_tokens,total_tokens
    else:
        index = int(index)
        if index - 1 < 0 or index - 1 >= len(centers):
            raise Exception(f"Index {index} out of range for centers list size {len(centers)}")

        coords = centers[index - 1]
        bounds = clickable_boxes[index - 1]
        x1, y1, x2, y2 = map(int, bounds)
        x, y = map(int, coords)

        # Action
        
        if action == "tap" or "tap" in action.lower():
            try:
                driver.tap([(x, y)], 100)
                logger.info(f"Tap action on element index {index}")
                action = "MOB_Tap"
                result=True
            except Exception as e:
                logger.info(f"Error during tap action: {str(e)}")
                result=False

        elif action == "MOB_SendKeys" or "enter" in action.lower():
            try:
                driver.tap([(x, y)], 100)  # tap to focus input box
                driver.execute_script('mobile: type', {'text': input_value})
                logger.info(f" Input '{input_value}' sent to element index {index}")
                action = "MOB_SendKeys"
                result=True
            except Exception as e:
                logger.info(f"Error during send keys action: {str(e)}")
                result=False
        else:
            logger.info(f"Unsupported action in CV : {action}")
            result=False
        
        bounds_str = f"[{x1},{y1}][{x2},{y2}]"
        tree = etree.fromstring(dom.encode('utf-8'))
        target = tree.xpath(f"//*[@bounds='{bounds_str}']")
        xpath_path = None
        if target:
                element = target[0]
        xpath_path = etree.ElementTree(tree).getpath(element)

        memory={
            "step":step,
            "type":element_type,
            "action": action,
            "result":result,
            "input": input_value,
            "xpath": xpath_path,
            "element_name":element_name


        }
        return result,memory,input_tokens,completion_tokens,total_tokens
