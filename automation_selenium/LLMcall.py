import logging
import requests
import json
import time
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
import warnings
warnings.simplefilter('ignore', FutureWarning)
import google.generativeai as genai
from anthropic import Anthropic
import openai
import httpx
from groq import Groq

  
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding="utf-8")

_llm_total_tokens = 0
def track_tokens(tokens=None):
    global _llm_total_tokens
    if tokens is not None:
        _llm_total_tokens += tokens
    return _llm_total_tokens
def get_total_tokens():
    return track_tokens()
def reset_tokens():
    global _llm_total_tokens
    _llm_total_tokens = 0

count = 0

def reset_count():
    global count
    count = 0

def call_grok_llm(prompt, serviceProvider, model, apiKey, service_accounts, seed=42):
    """
    Unified LLM caller for Groq, OpenAI, Anthropic, and Gemini.
    Tracks total tokens used across calls.
    """
    start_time = time.time()
    global count
    try:
        if serviceProvider == "DefaultFireFlink":
            client = Groq(api_key=apiKey)
            # Groq requires 'json' in the prompt for json_object mode
            groq_prompt = prompt if "json" in prompt.lower() else prompt + "\n\nRespond in JSON format."
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": groq_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                stream=False
            )
            result = response.choices[0].message.content
            total_tokens = getattr(response.usage, 'total_tokens', 0)
            track_tokens(total_tokens)
            logger.info(f"tokens used for {serviceProvider} call: {total_tokens}")
            elapsed_time = time.time() - start_time
            logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")
            return result

        # elif serviceProvider == 'OpenAi':
        #     client = OpenAI(api_key=apiKey)
        #     response = client.chat.completions.create(
        #         model=model,
        #         messages=[{"role": "user", "content": prompt}],
        #         # temperature=0.1
        #     )
        #     result = response.choices[0].message.content
        #     total_tokens = getattr(response.usage, 'total_tokens', 0)
        #     track_tokens(total_tokens)
        #     logger.info(f"tokens used for {serviceProvider} call: {total_tokens}")
        #     elapsed_time = time.time() - start_time
        #     logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")
        #     return result
        elif serviceProvider == 'OpenAi':
            http_client = httpx.Client()
            client = openai.OpenAI(api_key=apiKey, http_client=http_client)

            prompt = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            response = client.chat.completions.create(
                model=model,
                # temperature=0.1,
                # top_p=0.1,
                messages=prompt
            )
            result = response.choices[0].message.content.strip()
            call_tokens = response.usage.total_tokens
            track_tokens(call_tokens)
            logger.info(f"tokens used for {serviceProvider} call: {call_tokens}")

            elapsed_time = time.time() - start_time
            logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")

            return result


        elif serviceProvider == 'Gemini':
            genai.configure(api_key=apiKey)
            client = genai.GenerativeModel(model)
            if count == 0:
                count += 1
                print("count---------------------------------->", count)
                response = client.generate_content(
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    generation_config={"temperature": 0.1}
                )
            else:
                response = client.generate_content(
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
                )
            result = response.text
            total_tokens = getattr(response.usage_metadata, 'total_token_count', 0)
            track_tokens(total_tokens)
            logger.info(f"tokens used for {serviceProvider} call: {total_tokens}")
            elapsed_time = time.time() - start_time
            logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")
            return result

        elif serviceProvider == 'Anthropic':
            client = Anthropic(api_key=apiKey)
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
            total_tokens = getattr(response.usage, 'input_tokens', 0) + getattr(response.usage, 'output_tokens', 0)
            track_tokens(total_tokens)
            logger.info(f"tokens used for {serviceProvider} call: {total_tokens}")
            elapsed_time = time.time() - start_time
            logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")
            return result
            
        elif serviceProvider == "gemini_enterprise":
            sa_json = service_accounts
            PROJECT_ID = service_accounts["project_id"]
            LOCATION = "us-central1"
            credentials = service_account.Credentials.from_service_account_info(sa_json)
            vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
            client = GenerativeModel(model)
            
            if count == 0:
                count += 1
                print("count---------------------------------->", count)
                response = client.generate_content(
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    generation_config={"temperature": 0.1}
                )
            else:
                response = client.generate_content(
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
                )
            
            result = response.text
            total_tokens = getattr(response.usage_metadata, 'total_token_count', 0)
            track_tokens(total_tokens)
            logger.info(f"tokens used for {serviceProvider} call: {total_tokens}")
            elapsed_time = time.time() - start_time
            logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")
            return result

        elif serviceProvider == 'Groq':
            client = Groq(api_key=apiKey)
            # Groq requires 'json' in the prompt for json_object mode
            groq_prompt = prompt if "json" in prompt.lower() else prompt + "\n\nRespond in JSON format."
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": groq_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                stream=False
            )
            result = response.choices[0].message.content
            total_tokens = getattr(response.usage, 'total_tokens', 0)
            track_tokens(total_tokens)
            logger.info(f"tokens used for {serviceProvider} call: {total_tokens}")
            elapsed_time = time.time() - start_time
            logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")
            return result

        else:
            raise ValueError(f"Unsupported service provider: {serviceProvider}")

    except Exception as e:
        error_msg = f"Error during {serviceProvider} LLM call: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Re-raise to let caller handle it in their error payload
        raise Exception(error_msg)
