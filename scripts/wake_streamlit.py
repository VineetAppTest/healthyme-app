import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

APP_URL = os.environ.get("STREAMLIT_APP_URL", "").strip()

if not APP_URL:
    raise RuntimeError("STREAMLIT_APP_URL is missing. Add it as a GitHub Actions repository secret.")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1440,1200")

driver = webdriver.Chrome(options=chrome_options)

try:
    print(f"Opening Streamlit app: {APP_URL}")
    driver.get(APP_URL)
    time.sleep(10)

    page_text = driver.page_source.lower()

    wake_markers = [
        "yes, get this app back up",
        "this app has gone to sleep",
        "this app is asleep",
        "wake",
        "zzzz",
    ]

    if any(marker in page_text for marker in wake_markers):
        buttons = driver.find_elements(By.TAG_NAME, "button")
        clicked = False

        for button in buttons:
            text = (button.text or "").strip().lower()
            if "get this app back up" in text or "wake" in text:
                print(f"Clicking wake button: {button.text}")
                button.click()
                clicked = True
                time.sleep(30)
                break

        print("Wake button clicked:", clicked)
    else:
        print("App appears awake.")

    # Final lightweight confirmation
    print("Wake check completed.")

finally:
    driver.quit()
