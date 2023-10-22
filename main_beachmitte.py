"""
Telegram bot for checking slots at BeachMitte
"""


### PACKAGES

#!pip install selenium
import json
import os
import ssl
import time
import urllib.request

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

### PARAMS

CHECK_EVERY_N_SECONDS = 60

DATE = os.getenv("DATE")
SLOT = os.getenv("SLOT")

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_BOT_CHAT_ID = os.getenv("CHAT_ID")


### HELPERS


def find_slots(url: str, locations: list, date: str, slot: str, sleep_time: float = 1):
    """
    Finds slots at BeachMitte

    Parameters
    ----------
    url : str
        URL of the court booking
    locations : list
        List of locations to book at
    date : str
        Court date, DD.MM.YYYY
    slot : str
        Court time, HH:MM
    sleep_time : float, optional
        Time to sleep between page switches, by default 1
    """

    LOCATION_MAP = {
        "Winterstand (7)": "location_1",
        "Winterstand (6)": "location_19",
        "Mare Beach": "location_2",
    }

    slots = []

    # open browser
    driver = webdriver.Firefox()
    driver.get(url)

    # find week
    for _ in range(2):
        time.sleep(sleep_time)
        driver.find_element(By.ID, "next").click()

    # find slot in selected locations
    for location in locations:
        location_code = LOCATION_MAP[location]
        location_tab = driver.find_element(By.ID, location_code)
        parent_element = location_tab.find_element(By.XPATH, "./parent::label")
        location_btn = parent_element.find_element(By.CLASS_NAME, "btn-price")
        location_btn.click()
        time.sleep(sleep_time)

        try:
            button = driver.find_element(
                By.CSS_SELECTOR, f'button[data-date="{date}"][data-time="{slot}"]'
            )
            button_jsdate = button.get_attribute("data-jsdate")
            print(f"Found free slot on {button_jsdate} at {location}")
            slots.append({f"{location}": f"{button_jsdate}"})
        except NoSuchElementException:
            print(f"No slots available at {location}")

    driver.quit()

    return slots


def send_telegram_message(token: str, chat_id: str, message: str):
    """
    Send message to Telegram

    Parameters
    ----------
    token : str
        Telegram bot token
    chat_id : str
        Telegram chat ID
    message : str
        Bot message

    Returns
    -------
    str
        message
    """

    ssl._create_default_https_context = ssl._create_unverified_context

    headers = {"Content-Type": "application/json", "Accept": "     application/json"}

    data = {"chat_id": TELEGRAM_BOT_CHAT_ID, "parse_mode": "Markdown", "text": message}

    request_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    request = urllib.request.Request(
        request_url, data=json.dumps(data).encode(), headers=headers
    )
    response = urllib.request.urlopen(request)

    return response.read().decode("utf-8")


def run_bot(date: str, slot: str):
    """
    Run the bot

    Parameters
    ----------
    date : str
        Court date, DD.MM.YYYY
    slot : str
        Court time, HH:MM
    """

    BASE_URL = "https://mycourt.berlin/indoor"

    slots = []

    while not slots:
        slots = find_slots(
            url=BASE_URL,
            locations=["Winterstand (7)", "Winterstand (6)", "Mare Beach"],
            date=DATE,
            slot=SLOT,
        )
        print("=" * 50)
        time.sleep(CHECK_EVERY_N_SECONDS)

    message = f"Found {len(slots)} slots:\n"
    for slot in slots:
        message += f"- {list(slot)[0]}: {slot[list(slot)[0]]}\n"
    message += f"\nBook at {BASE_URL}"
    send_telegram_message(token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_BOT_CHAT_ID)


### MAIN
if __name__ == "__main__":
    run_bot(date=DATE, slot=SLOT)
