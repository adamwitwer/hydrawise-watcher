import requests
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("HYDRAWISE_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# CONFIG
API_URL = f"https://api.hydrawise.com/api/v1/statusschedule.php?api_key={API_KEY}"

POLL_WINDOW_START = 4  # 4:30 AM to 9:00 AM
POLL_WINDOW_END = 9
POLL_INTERVAL = 60  # in seconds

tracked_runs = {}  # relay_id -> end_time


def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"[{datetime.now()}] Email sent: {subject}")
    except Exception as e:
        print(f"[{datetime.now()}] Failed to send email: {e}")


def is_in_poll_window():
    now = datetime.now()
    return POLL_WINDOW_START <= now.hour < POLL_WINDOW_END


def poll_hydrawise():
    try:
        resp = requests.get(API_URL)
        data = resp.json()
        now = datetime.now()

        for zone in data.get("relays", []):
            relay_id = zone["relay_id"]
            zone_name = zone["name"]
            seconds_until_next_run = zone["time"]
            run_duration = zone["run"]

            if seconds_until_next_run == 1:
                # Zone is actively running
                end_time = now + timedelta(seconds=run_duration)
                tracked_runs[relay_id] = end_time
                print(f"[{now}] {zone_name} is running. Ends at {end_time.strftime('%H:%M:%S')}.")

            elif relay_id in tracked_runs:
                if now >= tracked_runs[relay_id]:
                    send_email(
                        f"Zone Finished: {zone_name}",
                        f"{zone_name} completed its watering cycle at {now.strftime('%H:%M:%S')}."
                    )
                    del tracked_runs[relay_id]

    except Exception as e:
        print(f"[{datetime.now()}] Error polling Hydrawise: {e}")


if __name__ == "__main__":
    print(f"Hydrawise watcher started at {datetime.now()}")
    while True:
        if is_in_poll_window():
            poll_hydrawise()
        time.sleep(POLL_INTERVAL)