import os
import base64
import openai
from c_v import generate_annotated_screenshots
import httpx
import logging  

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding="utf-8")

_openai_total_tokens = 0
def track_tokens_openai(tokens=None):
    global _openai_total_tokens
    if tokens is not None:
        _openai_total_tokens += tokens
    return _openai_total_tokens
def get_total_tokens_openai():
    return track_tokens_openai()
def reset_tokens_openai():
    global _openai_total_tokens
    _openai_total_tokens = 0



class Vision:
    def __init__(self):
         pass
    urls = [
            "https://dev2.fireflink.com",
            "https://test3.fireflink.com",
            "https://test2.fireflink.com",
            "https://performance.fireflink.com"
            ]
        
    
    def generate_vision_code(self, step,context, driver, start_time,server_host):
        try:

            screenshot = driver.get_screenshot_as_base64()
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            screenshot_path = "screenshots/screenshot.png"
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot))
            
            generate_annotated_screenshots(driver, output_dir="screenshots")
            annotated_primary_path = "screenshots/annotated_primary.png"

            with open(annotated_primary_path, "rb") as f:
                annotated_primary = base64.b64encode(f.read()).decode("utf-8")
            
            
            server = server_host.strip().lower()
            if any(server.startswith(url.lower()) for url in self.urls):
                api_key = os.getenv("OPENAI_API_KEY")
            else:
                api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")

            # Create a custom httpx client to avoid proxy issues
            http_client = httpx.Client()

            client = openai.OpenAI(
                api_key=api_key,
                http_client=http_client
            )
            
            custom_prompt_text = f"""
            You are a precise automation assistant.
            Context: {context}
            - Use the context to understand the step and select the closest semantic match to {step} and return only its index, else Fire-Flink-0.
            - **If u can't find the element, return Fire-Flink-0. dont return any other elements index.**
            - Using the provided annotated screenshot and {step}, identify the correct element index from the image.
            - Match the index to the text or action described in {step} as accurately as possible.
            - Return only the Fire-Flink-xx for the target element.
            - Do not provide any additional text or explanation. The output must be strictly Fire-Flink-xx.
            Now, Analyze the step:
            Step: "{step}"
            """
            prompt = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": custom_prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{annotated_primary}"
                            }
                        }
                    ]
                }
            ]
            response = client.chat.completions.create(
                model="gpt-4.1",
                temperature=0.1,
                top_p=0.1,
                messages=prompt
            )
            content = response.choices[0].message.content.strip()
            call_tokens = response.usage.total_tokens
            track_tokens_openai(call_tokens)
            logger.info(f"Vision index for step '{step}': {content}")
            return content
        except Exception as e:
            logger.error(f"Vision index extraction failed: {e}")
            raise e

    def generate_vision_code_2(self, step,context, driver, start_time,server_host):
        try:

            screenshot = driver.get_screenshot_as_base64()
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            screenshot_path = "screenshots/screenshot.png"
            
            # with open(screenshot_path, "wb") as f:
            #     f.write(base64.b64decode(screenshot))
            
            # generate_annotated_screenshots(driver, output_dir="screenshots")
            annotated_primary_path = "screenshots/annotated_secondary.png"

            with open(annotated_primary_path, "rb") as f:
                annotated_primary = base64.b64encode(f.read()).decode("utf-8")
            
             
            server = server_host.strip().lower()
            if any(server.startswith(url.lower()) for url in self.urls):
                api_key = os.getenv("OPENAI_API_KEY")
            else:
                api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
                
            # Create a custom httpx client to avoid proxy issues
            http_client = httpx.Client()
            client = openai.OpenAI(api_key=api_key, http_client=http_client)
            # print(step)
            
            custom_prompt_text = f"""
            You are a precise automation assistant.
            Context: {context}
            - Use the context to understand the step and select the closest semantic match to {step} and return only its index, else Fire-Flink-0.
            - **If u can't find the element, return Fire-Flink-0. dont return any other elements index.**
            - Using the provided annotated screenshot and {step}, identify the correct element index from the image.
            - Match the index to the text or action described in {step} as accurately as possible.
            - Return only the Fire-Flink-xx for the target element.
            - Do not provide any additional text or explanation. The output must be strictly Fire-Flink-xx.
            Step: "{step}"
            """
            prompt = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": custom_prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{annotated_primary}"
                            }
                        }
                    ]
                }
            ]
            response = client.chat.completions.create(
                model="gpt-4.1",
                temperature=0.1,
                top_p=0.1,
                messages=prompt
            )
            content = response.choices[0].message.content.strip()
            call_tokens = response.usage.total_tokens
            track_tokens_openai(call_tokens)
            logger.info(f"Vision index for step '{step}': {content}")
            return content
        except Exception as e:
            logger.error(f"Vision index extraction failed: {e}")
            raise e