from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import threading
import os
import base64

app = Flask(__name__)

# Update the ChromeDriver path according to your setup
CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'

def url_to_filename(url, extension):
    sanitized_url = "".join([c if c.isalnum() else "_" for c in url])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitized_url}_{timestamp}{extension}"

def process_webpage(url):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)
        driver.implicitly_wait(10)  # Wait for the page to load

        # Save a full-page screenshot
        screenshot_filename = f'screenshots/{url_to_filename(url, ".png")}'
        os.makedirs(os.path.dirname(screenshot_filename), exist_ok=True)
        driver.save_screenshot(screenshot_filename)

        # Generate a PDF
        pdf_result = driver.execute_cdp_cmd("Page.printToPDF", {
            "landscape": False,
            "printBackground": True,
            "preferCSSPageSize": True,
        })
        pdf_filename = f'screenshots/{url_to_filename(url, ".pdf")}'
        with open(pdf_filename, 'wb') as f:
            f.write(base64.b64decode(pdf_result['data']))

        # Save all text content
        text_content = driver.find_element(By.TAG_NAME, "body").text
        text_filename = f'screenshots/{url_to_filename(url, ".txt")}'
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(text_content)

    except Exception as e:
        print(f"Error processing webpage {url}: {e}")
    finally:
        driver.quit()

@app.route('/', methods=['POST'])
def index():
    data = request.json
    url = data.get('url')
    if url:
        threading.Thread(target=process_webpage, args=(url,)).start()
        return '', 204
    else:
        return 'No URL provided', 400

if __name__ == '__main__':
    app.run(port=8090, threaded=True)

