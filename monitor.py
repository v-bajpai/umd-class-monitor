import os
import re
import requests
from bs4 import BeautifulSoup

USER_KEY = os.environ["PUSHOVER_USER_KEY"]
APP_TOKEN = os.environ["PUSHOVER_APP_TOKEN"]

URL = "https://app.testudo.umd.edu/soc/search?courseId=cmsc216&sectionId=&termId=202608&_openSectionsOnly=on&creditCompare=&credits=&courseLevelFilter=ALL&instructor=&_facetoface=on&_blended=on&_online=on&courseStartCompare=&courseStartHour=&courseStartMin=&courseStartAM=&courseEndHour=&courseEndMin=&courseEndAM=&teachingCenter=ALL&_classDay1=on&_classDay2=on&_classDay3=on&_classDay4=on&_classDay5=on"

TARGET_SECTIONS = {
    "0201",
    "0202",
    "0203",
    "0204",
    "0205",
}


def check_sections():
    response = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    open_sections = []

    for text_node in soup.find_all(string=True):

        section = text_node.strip()

        if section not in TARGET_SECTIONS:
            continue

        current = text_node.parent

        for _ in range(10):

            current = current.find_next()

            if current is None:
                break

            text = current.get_text(" ", strip=True)

            if "Seats" in text and "Open:" in text:

                match = re.search(r"Open:\s*(\d+)", text)

                if match:
                    seats = int(match.group(1))

                    print(
                        f"Section {section}: "
                        f"{seats} seat(s) open"
                    )

                    if seats > 0:
                        open_sections.append((section, seats))

                    break

    return open_sections


def send_notification(section, seats):

    message = (
        f"🚨 CMSC216 SECTION {section} IS OPEN!\n\n"
        f"Seats available: {seats}\n\n"
        f"Open Testudo NOW!"
    )

    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": APP_TOKEN,
            "user": USER_KEY,
            "title": "🚨 UMD CLASS OPEN",
            "message": message,
            "priority": 2,
            "retry": 30,
            "expire": 3600,
        },
        timeout=10,
    )

    response.raise_for_status()

    print(f"Notification sent for section {section}")


print("Checking UMD Testudo...")

open_sections = check_sections()

if open_sections:

    for section, seats in open_sections:
        send_notification(section, seats)

else:
    print("No target sections currently have open seats.")
