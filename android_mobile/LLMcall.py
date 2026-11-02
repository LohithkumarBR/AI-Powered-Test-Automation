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
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

count = 0

def reset_count():
    global count
    count = 0

def call_grok_llm(prompt, serviceProvider, model, apiKey,service_accounts, seed=42):
    """
    Unified LLM caller for Groq, OpenAI, Anthropic, and Gemini.
    Tracks total tokens used across calls.
    """
    global count
    start_time = time.time()

    if serviceProvider == "DefaultFireFlink":
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {apiKey}',
            'Content-Type': 'application/json'
        }
        body = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1,
            'top_p': 0.1,
            # 'seed': seed
        }

    elif serviceProvider == "OpenAi":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {apiKey}',
            'Content-Type': 'application/json'
        }
        body = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1,
            'top_p': 0.1
        }

    elif serviceProvider == 'Gemini':
        genai.configure(api_key=apiKey)
        client = genai.GenerativeModel(model)
        if count == 0:
            count += 1
            # print("count---------------------------------->", count)
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
        input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
        output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
        total_tokens = getattr(response.usage_metadata, 'total_token_count', 0)
        logger.info(f"tokens used for {serviceProvider} call: {total_tokens}")
        elapsed_time = time.time() - start_time
        logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")
        return result, {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }

    elif serviceProvider == "Anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            'Authorization': f'Bearer {apiKey}',
            'Content-Type': 'application/json'
        }
        body = {
            'model': model,
            'max_tokens': 1024,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1,
            'top_p': 0.1
        }

    elif serviceProvider == "Groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {apiKey}',
            'Content-Type': 'application/json'
        }
        body = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1,
            'top_p': 0.1
        } 

    elif serviceProvider == "gemini_enterprise":
            sa_json = service_accounts
            PROJECT_ID = service_accounts["project_id"]
            LOCATION = "us-central1"
            credentials = service_account.Credentials.from_service_account_info(sa_json)
            vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
            client = GenerativeModel(model)
            if count == 0:
                count += 1
                # print("count---------------------------------->", count)
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
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            total_tokens = getattr(response.usage_metadata, 'total_token_count', 0)
            logger.info(f"tokens used for {serviceProvider} call: {total_tokens}")
            elapsed_time = time.time() - start_time
            logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")
            return result, {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }

    else:
        raise ValueError(f"Unsupported service provider: {serviceProvider}")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error calling {serviceProvider} API: {e}")
        raise Exception(f"Request to {serviceProvider} API timed out")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error calling {serviceProvider} API: {e}")
        raise Exception(f"Failed to connect to {serviceProvider} API")
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error calling {serviceProvider} API: {e}"
        if e.response is not None:
            error_msg += f"\nResponse: {e.response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error calling {serviceProvider} API: {e}")
        raise Exception(f"Request error calling {serviceProvider} API: {str(e)}")

    # Parse response safely
    try:
        data = response.json()

        # Extract result & token usage by provider
        if serviceProvider == "Gemini":
            result = data["candidates"][0]["content"]["parts"][0]["text"]
            usage_metadata = data.get("usageMetadata", {})

            input_tokens = usage_metadata.get("promptTokenCount", 0)
            output_tokens = usage_metadata.get("candidatesTokenCount", 0)
            total_tokens = usage_metadata.get("totalTokenCount", 0)

        elif serviceProvider == "Anthropic":
            result = data["content"][0]["text"]
            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens

        else:
            result = data["choices"][0]["message"]["content"]
            input_tokens = data.get("usage", {}).get("prompt_tokens", 0)
            output_tokens = data.get("usage", {}).get("completion_tokens", 0)
            total_tokens = data.get("usage", {}).get("total_tokens", 0)


    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse {serviceProvider} API response: {e}")
        logger.error(f"Full response: {response.text}")
        raise Exception(f"Invalid response format from {serviceProvider} API")

    elapsed_time = time.time() - start_time
    logger.info(f"Time taken for {serviceProvider} call: {elapsed_time:.2f} seconds")

    return result, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens
    }
