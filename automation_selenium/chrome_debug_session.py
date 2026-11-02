import os
import tempfile
import shutil
import platform
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    encoding="utf-8")

class BrowserDebugSession:
    _instance = None

    def __init__(self, browser_name= None, driver_path=None):

        if BrowserDebugSession._instance is not None:
            raise Exception("Use get_instance() instead of creating a new object.")

        # logger.info(f"Detected OS: {platform.system()} ({os.name})")
        self.browser_name = browser_name
        self.driver = None
        self.driver_path = driver_path




        # try:
        #     self.driver = self._start_browser()
        # except Exception as e:
        #     logger.error(f"Failed to start or connect to {self.browser_name}: {e}")
        #     raise



    def _get_default_profile(self):
        if os.name == 'nt':  # Windows
            return r"C:\tmp\chrome-profile"
        elif os.name == 'posix' or platform.system() == "Darwin":  # Linux / MacOS
            return "/tmp/chrome-profile"
        else:
            raise Exception(f"Unsupported OS: {os.name}")

    
    def _start_browser(self):
        browser_lower = self.browser_name.lower()
        if browser_lower not in ["chrome", "edge", "firefox", "safari"]:
            raise ValueError(f"Unsupported browser: {self.browser_name}. Supported: chrome, edge, firefox")

        # if not self.cloud:

        if browser_lower == "chrome":
            options = Options()
            
            driver_path = self.driver_path if self.driver_path and os.path.exists(self.driver_path) else ChromeDriverManager().install()
            
            # Fix: webdriver-manager sometimes returns wrong file, ensure we get chromedriver.exe
            if not driver_path.endswith('chromedriver.exe'):
                import pathlib
                driver_dir = pathlib.Path(driver_path).parent
                actual_driver = driver_dir / 'chromedriver.exe'
                if actual_driver.exists():
                    driver_path = str(actual_driver)
                    logger.info(f"Corrected ChromeDriver path to: {driver_path}")
            
            service = Service(driver_path)

            driver = webdriver.Chrome(service=service, options=options)

        # -------------------- EDGE --------------------
        elif browser_lower == "edge":
            options = EdgeOptions()


            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option("detach", True)
            

            service = Service(
                self.driver_path if self.driver_path and os.path.exists(self.driver_path)
                else EdgeChromiumDriverManager().install()
            )

            driver = webdriver.Edge(service=service, options=options)

        # -------------------- FIREFOX --------------------
        elif browser_lower == "firefox":
            options = FirefoxOptions()

            # Firefox uses preferences, NOT Chrome flags
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("dom.push.enabled", False)
            options.set_preference("geo.enabled", False)
            options.set_preference("signon.rememberSignons", False)
            options.set_preference("browser.download.manager.showWhenStarting", False)
            options.set_preference("acceptInsecureCerts", True)
            


            service = FirefoxService(
                self.driver_path if self.driver_path and os.path.exists(self.driver_path)
                else GeckoDriverManager().install()
            )

            driver = webdriver.Firefox(service=service, options=options)
        
        elif browser_lower == "safari":
            from selenium.webdriver.safari.options import Options as SafariOptions
            from selenium.webdriver.safari.service import Service as SafariService
            options = SafariOptions()
            # Safari does NOT support Chrome-style flags
            # Most settings must be enabled manually in Safari
            service = SafariService()  # Uses system safaridriver
            driver = webdriver.Safari(service=service, options=options)

        # logger.info(f"Started local {self.browser_name} session")

        return driver

    def has_been_force_closed(self):
        if not self.driver:
            return True
        try:
            # Check if the session is still active by trying to access a property
            _ = self.driver.current_url
            return False
        except Exception:
            return True
