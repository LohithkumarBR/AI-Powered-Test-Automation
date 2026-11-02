import json
from get import GET_SKIP_LIST
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
def convert_memory_to_clean_json(memory):

    memory = json.loads(memory)
    clean_json_list = []


    
    LONG_NEEDED_ACTION =["MOB_VerifyElementIsEnabled","MOB_VerifyElementIsSelected","MOB_VerifyElementIsDisplayed"]
    for item in memory:
        step = item["step"]
        action = item["action"]
        xpath = item.get("xpath", "") 
        input_text = item.get("input", "")  
        element_type = item.get("type", "")
        num_of_scrolls = item.get("num_of_scrolls", 0)
        direction = item.get("direction", "")
        package = item.get("app_package","")
        activity = item.get("app_activity","")
        result = item.get("result",False)
        keyword = item.get("keyword", "")
        attribiute_type=item.get("attribute_type","")
        locator_type=item.get("locator_type","")
        keycode=item.get("keycode","")
        element_name=item.get("element_name","")
        ref_xpath=item.get("ref_xpath","")

        step_inputs = []
        element_data = []
        
        if action== "MOB_VerifyElementIsEnabledInSpecifiedTime" :
            action = "MOB_VerifyElementIsEnabled"
        elif action== "MOB_VerifyElementIsSelectedInSpecifiedTime" :
            action = "MOB_VerifyElementIsSelected"
        elif action== "MOB_VerifyElementIsDisplayedInSpecifiedTime" :
            action = "MOB_VerifyElementIsDisplayed"
        elif action== "MOB_VerifyElementIsEnabled":
            action = "MOB_IsEnabled"
        elif action== "MOB_VerifyElementIsSelected":
            action = "MOB_IsSelected"
        elif action== "MOB_VerifyElementIsDisplayed":
            action = "MOB_IsDisplayed"

     

        if input_text == "":
            input_text = item.get("keyword", "")
            
        if action == "MOB_SwipeUsingReferenceElement":
            locators = [{"name": "xpath", "value": ref_xpath}]
        elif xpath != "":
            locators = [{"name": "xpath", "value": xpath}]
        else:
            locators = [{"name": "xpath", "value": "No locators Found"}]

            

            

        if action == "Open Android App":
            clean_item = {
                "nlpName": "Open Android App",
                "elementsData": [],         
                "stepInputs": [package,activity]  
            }
            clean_json_list.append(clean_item)
            continue 
        elif action == "MOB_SwipeDirectionNTimes":
            clean_item = {
                "nlpName": "MOB_SwipeDirectionNTimes",
                "elementsData": [],         
                "stepInputs": ["up" if direction == "none" else direction, num_of_scrolls if num_of_scrolls else 30]  
            }
            clean_json_list.append(clean_item)
            continue
        

        element_data.append({
            "name": element_name if element_name else step,
            "type": element_type,
            "locators": locators,
            "platform": "Android"
        })

        if action in LONG_NEEDED_ACTION:
            try:
                if input_text:
                    print("input_text",input_text)
                    input_text = input_text.split(",")
                    print("input_text",input_text)
                    input_text = input_text[1]
                    step_inputs.append(input_text)
            except:
                step_inputs.append(5)
            
        elif action in ["MOB_SwipeUpToElement","MOB_SwipeDownToElement","MOB_SwipeLeftToElement","MOB_SwipeRightToElement"]:
            step_inputs=["xpath",xpath,num_of_scrolls if num_of_scrolls else 30]
        elif action=="MOB_EnterDataAndPressKey":
            step_inputs.append(input_text)
            step_inputs.append(keycode)
        elif action=="MOB_SwipeUsingReferenceElement":
            # step_inputs.append(element_data[0]["locators"])
            step_inputs.append(direction)
            step_inputs.append("xpath")
            step_inputs.append(ref_xpath)
            step_inputs.append(num_of_scrolls if num_of_scrolls else 30)
        elif action=="MOB_PressAnyKey":
            step_inputs.append(keycode)
        elif action in["MOB_FindElement","MOB_FindElements"]:
            step_inputs.append("xpath")
            step_inputs.append(xpath)
        elif action in["MOB_VerifyText","MOB_VerifyElementNotContainsText","MOB_VerifyPartialText"]:
            step_inputs.append(input_text)
            step_inputs.append(False)
        elif action in["MOB_GetTextFromListOfWebElements","MOB_GetListOfElementsFromLocatorTypeLocatorValue","MOB_GetAttributeValueFromListOfWebElements"]:
            step_inputs.append("xpath")
            step_inputs.append(xpath)
            step_inputs.append(attribiute_type)
        elif action in ["MOB_VerifyAttributeValue","MOB_VerifyPartialAttributeValue"]:
            step_inputs.append(attribiute_type)
            step_inputs.append(input_text)
            step_inputs.append(False)
        elif action=="MOB_VerifyIfXAndYCoordinateOfElement":
            int1=input_text[0]
            int2=input_text[1]
            step_inputs.append(int1)
            step_inputs.append(int2)
        else:
            step_inputs.append(input_text)
        
        


        clean_item = {
            "nlpName": action,
            "elementsData": element_data,
            "stepInputs": step_inputs
        }

        clean_json_list.append(clean_item)

    return clean_json_list