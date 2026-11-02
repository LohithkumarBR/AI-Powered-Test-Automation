import requests
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

class AutoHealing:
    """Service to call AI Locator API in parallel thread for auto-healing"""
    
    def __init__(self):

        self.url = "https://test3.fireflink.com/ailocator/api/locators"
        self.results = {}
        self.lock = threading.Lock()
        
    def send_locator_request(self, html: str, element_id: str, element_name: str,server_host: str, source: str = "primary") -> None:
        
        def _make_request():
            try:
                # if "dev2" in server_host:
                #     self.url = "https://dev2.fireflink.com/ailocator/api/locators"
                # elif "test3" in server_host:
                #     self.url = "https://test3.fireflink.com/ailocator/api/locators"
                # elif "app" in server_host:
                #     self.url = "https://app.v3.fireflink.com/ailocator/api/locators"
                # else:
                #     self.url = "https://test3.fireflink.com/ailocator/api/locators"
                payload = {
                    "html": html,
                    "elementId": element_id,
                    "elementName": element_name
                }
                
                # logger.info(f"[Auto Healing] Sending request for element: {element_name} (ID: {element_id}, Source: {source})")
                
                # Verify if element_id actually exists in the provided HTML
                # if element_id not in html:
                #     logger.warning(f"[Auto Healing] CRITICAL: elementId '{element_id}' NOT FOUND in the provided HTML string! (HTML length: {len(html)})")
                # else:
                #     logger.info(f"[Auto Healing] Confirmed: elementId '{element_id}' exists in the HTML.")
                
                response = requests.post(self.url, json=payload, timeout=30)
                
                logger.info(f"[Auto Healing] Status: {response.status_code}")
                
                if response.status_code == 200:
                    resp_json = response.json()
                    # logger.info(f"[Auto Healing] Response JSON: {resp_json}")
                    with self.lock:
                        # Remove existing entries with the same element name
                        keys_to_remove = [k for k, v in self.results.items() if v.get("name") == element_name]
                        for k in keys_to_remove:
                            del self.results[k]
                            
                        # Store both name, locator data and source
                        self.results[element_id] = {
                            "name": element_name,
                            "data": resp_json,
                            "source": source
                        }
                else:
                    logger.warning(f"[Auto Healing] Request failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.error("[Auto Healing] Request timed out")
            except requests.exceptions.RequestException as e:
                logger.error(f"[Auto Healing] Request failed: {e}")
            except Exception as e:
                logger.error(f"[Auto Healing] Unexpected error: {e}")
        
        # Start the request in a separate thread
        thread = threading.Thread(target=_make_request, daemon=True)
        thread.start()
        logger.info("[Auto Healing] Request sent in parallel thread")

    
        
    def get_result(self, element_id: str) -> Optional[dict]:
        """Retrieve stored result for a specific element ID"""
        with self.lock:
            return self.results.get(element_id)

    def get_all_results(self) -> dict:
        """Retrieve all stored results"""
        with self.lock:
            return dict(self.results)

    def clear_results(self):
        """Clear all stored results"""
        with self.lock:
            self.results.clear()
