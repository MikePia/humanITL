import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

download_directory = os.getenv("DOWNLOAD_DIRECTORY")
extension_path = os.getenv("EXTENSION_PATH")


def automate_browser_actions(url, numBtns):
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": download_directory,
            "download.prompt_for_download": False,  # Don't prompt for download
            "download.extensions_to_open": "applications/pdf",  # Attempts to open PDFs automatically; other files may still prompt
            "plugins.always_open_pdf_externally": True,  # Automatically download PDFs
        },
    )
    chrome_options.add_argument(f"--disable-extensions-except={extension_path}")
    chrome_options.add_argument(f"--load-extension={extension_path}")

    # Initialize the Chrome driver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    # Navigate to the specified URL
    try:
        success = []
        driver.get(url)
        # Place a 10  in the number input with the id batchSize
        driver.find_element(By.ID, "batchSize").send_keys(numBtns)
        
        # Click on the download button with the id downloadBtn
        driver.find_element(By.ID, "downloadBtn").click()
        
        for i in range(1, numBtns + 1):
            button_id = f"downloadBtn-{i}"
            try:
                button = driver.find_element(By.ID, button_id)
                button.click()
                print(f"Clicked on {button_id}")
                success.append(button_id)
            except Exception as e:
                print(f"Error clicking on {button_id}: {e}")
    except Exception:
        print(f"\nError navigating to {url}.  Is is  human-in-the-loop running?\n")

    # Keep the browser open for inspection (remove or modify as needed)

    # input("Press Enter to close browser...")
    # driver.quit()
    return success
