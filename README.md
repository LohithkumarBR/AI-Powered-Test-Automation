# AI-Powered Test Automation Platform

An AI-powered test automation platform that leverages Large Language Models (LLMs), Python, and automation frameworks to execute test scenarios using natural language instructions.

## Project Modules

### 1. Web Automation
Located in `automation_selenium/`

- Natural Language Processing for browser automation.
- DOM extraction and filtering.
- LLM-powered element identification.
- Selenium-based browser interaction.
- Vision-based element detection.
- Auto-healing and retry mechanisms.

### 2. Mobile Automation
Located in `android_mobile/`

- Natural language-based mobile test execution.
- UI hierarchy and XML extraction.
- LLM-powered element identification.
- Screenshot-based element detection.
- Automated mobile interactions.

## Technology Stack

- Python
- Selenium
- LLM APIs
- BeautifulSoup
- OpenCV
- Android Automation
- HTML / XML Processing

## Project Structure

- `automation_selenium/` – Web automation module.
- `android_mobile/` – Mobile automation module.

## Setup and Installation

Each module has its own `requirements.txt`.

Install dependencies from the respective module directory:

```bash
pip install -r requirements.txt
```

## Note

This repository contains separate modules for web and mobile automation. Configuration, environment variables, and execution requirements may differ between modules.