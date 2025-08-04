import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

API_KEY = os.getenv("HYDRAWISE_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Email configuration
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

# CONFIG
API_URL = f"https://api.hydrawise.com/api/v1/statusschedule.php?api_key={API_KEY}"

POLL_WINDOW_START = 4  # 4:30 AM to 9:00 AM
POLL_WINDOW_END = 9
POLL_INTERVAL = 60  # in seconds

tracked_runs = {}  # relay_id -> end_time

# Zone mappings with custom names and emojis
ZONE_CONFIG = {
    1: {"name": "Backyard Garden Drip", "emoji": "🍅"},
    2: {"name": "Backyard Turf", "emoji": "🌱"},
    3: {"name": "Northern Side", "emoji": "🌲"},
    4: {"name": "Front Yard Garden Drip", "emoji": "🌺"},
    5: {"name": "Front Yard Against House Drip", "emoji": "🏡"},
    6: {"name": "Front Lawn", "emoji": "🌿"}
}


def send_discord_notification(zone_name, zone_number, completion_time, completion_datetime):
    zone_config = ZONE_CONFIG.get(zone_number, {"name": zone_name, "emoji": "💧"})
    zone_display_name = zone_config["name"]
    zone_emoji = zone_config["emoji"]
    
    payload = {
        "embeds": [{
            "title": f"{zone_emoji} Irrigation Complete",
            "description": f"**{zone_display_name}** finished watering",
            "color": 0x00ff00,
            "fields": [
                {
                    "name": "Zone",
                    "value": f"Zone {zone_number}",
                    "inline": True
                },
                {
                    "name": "Completion Time",
                    "value": completion_time,
                    "inline": True
                }
            ],
            "timestamp": completion_datetime.isoformat()
        }]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"[{datetime.now()}] Discord notification sent: {zone_emoji} {zone_display_name}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Failed to send Discord notification: {e}")
        return False


def send_email_notification(zone_name, zone_number, completion_time, completion_datetime):
    if not all([EMAIL_SMTP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO]):
        print(f"[{datetime.now()}] Email configuration incomplete, skipping email notification")
        return False
        
    zone_config = ZONE_CONFIG.get(zone_number, {"name": zone_name, "emoji": "💧"})
    zone_display_name = zone_config["name"]
    zone_emoji = zone_config["emoji"]
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"{zone_emoji} Irrigation Complete - {zone_display_name}"
    
    body = f"""
{zone_emoji} Irrigation Complete

{zone_display_name} finished watering

Zone: Zone {zone_number}
Completion Time: {completion_time}
Date: {completion_datetime.strftime('%B %d, %Y')}

--
Hydrawise Watcher
"""
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USERNAME, EMAIL_TO, text)
        server.quit()
        print(f"[{datetime.now()}] Email notification sent: {zone_emoji} {zone_display_name}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Failed to send email notification: {e}")
        return False


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
                    completion_time = tracked_runs[relay_id]
                    completion_time_str = completion_time.strftime('%H:%M:%S')
                    
                    # Send both Discord and email notifications
                    send_discord_notification(zone_name, relay_id, completion_time_str, completion_time)
                    send_email_notification(zone_name, relay_id, completion_time_str, completion_time)
                    
                    del tracked_runs[relay_id]

    except Exception as e:
        print(f"[{datetime.now()}] Error polling Hydrawise: {e}")


if __name__ == "__main__":
    print(f"Hydrawise watcher started at {datetime.now()}")
    while True:
        if is_in_poll_window():
            poll_hydrawise()
        time.sleep(POLL_INTERVAL)