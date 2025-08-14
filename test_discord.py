#!/usr/bin/env python3
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Email configuration
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

# Zone mappings with custom names and emojis
ZONE_CONFIG = {
    1: {"name": "Backyard Garden Drip", "emoji": "🍅"},
    2: {"name": "Backyard Turf", "emoji": "⚽"},
    3: {"name": "Northern Side", "emoji": "🧭"},
    4: {"name": "Front Yard Garden Drip", "emoji": "🌸"},
    5: {"name": "Front Yard Against House Drip", "emoji": "🏠"},
    6: {"name": "Front Lawn", "emoji": "🌳"}
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
        print(f"✅ Discord notification sent: {zone_emoji} {zone_display_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to send Discord notification: {e}")
        return False


def send_email_notification(zone_name, zone_number, completion_time, completion_datetime):
    if not all([EMAIL_SMTP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO]):
        print("⚠️  Email configuration incomplete, skipping email notification")
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
        print(f"✅ Email notification sent: {zone_emoji} {zone_display_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email notification: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Discord notifications...")
    
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not found in .env file")
        exit(1)
    
    # Test with actual relay ID for Backyard Garden Drip
    test_completion_time = datetime.now().replace(hour=8, minute=45, second=30, microsecond=0)
    
    print("Testing Discord notification...")
    discord_success = send_discord_notification("Backyard Garden Drip", 5533837, "08:45:30", test_completion_time)
    
    print("\nTesting email notification...")
    email_success = send_email_notification("Backyard Garden Drip", 5533837, "08:45:30", test_completion_time)
    
    print(f"\n📊 Test Results:")
    print(f"Discord: {'✅ Success' if discord_success else '❌ Failed'}")
    print(f"Email: {'✅ Success' if email_success else '❌ Failed'}")
    
    if discord_success or email_success:
        print("🎉 At least one notification method worked!")
    else:
        print("💥 All notification methods failed. Check your configuration.")