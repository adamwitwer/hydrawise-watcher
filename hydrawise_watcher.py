import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

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
WEEKLY_SUMMARY_HOUR = 15  # 3 PM on Sunday
WEEKLY_DATA_FILE = "weekly_activity.json"

tracked_runs = {}  # relay_id -> end_time
weekly_activity = []  # List of completed irrigation events
last_weekly_summary = None  # Track when we last sent a weekly summary

# Zone mappings with custom names and emojis (using actual relay IDs from Hydrawise API)
ZONE_CONFIG = {
    5533837: {"name": "Backyard Garden Drip", "emoji": "🍅"},
    5533838: {"name": "Backyard Turf", "emoji": "⚽"},
    5533839: {"name": "Right/Northern Side", "emoji": "🧭"},
    5533842: {"name": "Front Yard Garden Drip", "emoji": "🌸"},
    5533846: {"name": "Front Yard Against House Drip", "emoji": "🏠"},
    5533847: {"name": "Front Lawn", "emoji": "🌳"}
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


def load_weekly_data():
    global weekly_activity, last_weekly_summary
    try:
        if os.path.exists(WEEKLY_DATA_FILE):
            with open(WEEKLY_DATA_FILE, 'r') as f:
                data = json.load(f)
                weekly_activity = data.get('activity', [])
                last_weekly_summary = data.get('last_summary')
                if last_weekly_summary:
                    last_weekly_summary = datetime.fromisoformat(last_weekly_summary)
    except Exception as e:
        print(f"[{datetime.now()}] Error loading weekly data: {e}")
        weekly_activity = []
        last_weekly_summary = None


def save_weekly_data():
    try:
        data = {
            'activity': weekly_activity,
            'last_summary': last_weekly_summary.isoformat() if last_weekly_summary else None
        }
        with open(WEEKLY_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[{datetime.now()}] Error saving weekly data: {e}")


def add_irrigation_event(zone_name, zone_number, completion_time, completion_datetime):
    zone_config = ZONE_CONFIG.get(zone_number, {"name": zone_name, "emoji": "💧"})
    event = {
        'zone_name': zone_config["name"],
        'zone_number': zone_number,
        'emoji': zone_config["emoji"],
        'completion_time': completion_time,
        'completion_datetime': completion_datetime.isoformat(),
        'date': completion_datetime.strftime('%A, %B %d')
    }
    weekly_activity.append(event)
    
    # Keep only events from the last 8 days (a bit more than a week for safety)
    cutoff_date = datetime.now() - timedelta(days=8)
    weekly_activity[:] = [
        event for event in weekly_activity 
        if datetime.fromisoformat(event['completion_datetime']) >= cutoff_date
    ]
    
    save_weekly_data()


def generate_weekly_summary():
    if not weekly_activity:
        return None
        
    # Get events from the past week
    one_week_ago = datetime.now() - timedelta(days=7)
    week_events = [
        event for event in weekly_activity 
        if datetime.fromisoformat(event['completion_datetime']) >= one_week_ago
    ]
    
    if not week_events:
        return None
    
    # Group by zone
    zone_stats = {}
    for event in week_events:
        zone_num = event['zone_number']
        if zone_num not in zone_stats:
            zone_stats[zone_num] = {
                'name': event['zone_name'],
                'emoji': event['emoji'],
                'count': 0,
                'dates': []
            }
        zone_stats[zone_num]['count'] += 1
        zone_stats[zone_num]['dates'].append(event['date'])
    
    return {
        'total_events': len(week_events),
        'zone_stats': zone_stats,
        'date_range': f"{one_week_ago.strftime('%B %d')} - {datetime.now().strftime('%B %d, %Y')}"
    }


def send_weekly_discord_summary(summary):
    if not summary:
        return False
        
    fields = []
    for zone_num, stats in sorted(summary['zone_stats'].items()):
        times_text = "time" if stats['count'] == 1 else "times"
        fields.append({
            "name": f"{stats['emoji']} {stats['name']}",
            "value": f"Watered {stats['count']} {times_text}",
            "inline": True
        })
    
    payload = {
        "embeds": [{
            "title": "📊 Weekly Irrigation Summary",
            "description": f"**{summary['total_events']} irrigation cycles completed**\n*{summary['date_range']}*",
            "color": 0x3498db,
            "fields": fields
        }]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"[{datetime.now()}] Weekly Discord summary sent")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Failed to send weekly Discord summary: {e}")
        return False


def send_weekly_email_summary(summary):
    if not summary or not all([EMAIL_SMTP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO]):
        return False
        
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"📊 Weekly Irrigation Summary - {summary['total_events']} cycles completed"
    
    body = f"""📊 Weekly Irrigation Summary

{summary['total_events']} irrigation cycles completed
{summary['date_range']}

Zone Activity:
"""
    
    for zone_num, stats in sorted(summary['zone_stats'].items()):
        times_text = "time" if stats['count'] == 1 else "times"
        body += f"{stats['emoji']} {stats['name']}: {stats['count']} {times_text}\n"
    
    body += f"""

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
        print(f"[{datetime.now()}] Weekly email summary sent")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Failed to send weekly email summary: {e}")
        return False


def check_and_send_weekly_summary():
    global last_weekly_summary
    now = datetime.now()
    
    # Check if it's Sunday afternoon (day 6 in weekday, where Monday is 0)
    if now.weekday() != 6 or now.hour != WEEKLY_SUMMARY_HOUR:
        return
    
    # Check if we already sent a summary today
    if last_weekly_summary and last_weekly_summary.date() == now.date():
        return
    
    summary = generate_weekly_summary()
    if summary:
        send_weekly_discord_summary(summary)
        send_weekly_email_summary(summary)
        last_weekly_summary = now
        save_weekly_data()


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
                    
                    # Add to weekly activity tracking
                    add_irrigation_event(zone_name, relay_id, completion_time_str, completion_time)
                    
                    del tracked_runs[relay_id]

    except Exception as e:
        print(f"[{datetime.now()}] Error polling Hydrawise: {e}")


if __name__ == "__main__":
    print(f"Hydrawise watcher started at {datetime.now()}")
    
    # Load existing weekly data
    load_weekly_data()
    print(f"[{datetime.now()}] Loaded {len(weekly_activity)} past irrigation events")
    
    while True:
        # Check for weekly summary (runs once per hour on Sunday at 3 PM)
        check_and_send_weekly_summary()
        
        if is_in_poll_window():
            poll_hydrawise()
        time.sleep(POLL_INTERVAL)