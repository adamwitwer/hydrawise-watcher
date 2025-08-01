#!/usr/bin/env python3
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Zone mappings with custom names and emojis
ZONE_CONFIG = {
    1: {"name": "Backyard Garden Drip", "emoji": "🍅"},
    2: {"name": "Backyard Turf", "emoji": "🌱"},
    3: {"name": "Northern Side", "emoji": "🌲"},
    4: {"name": "Front Yard Garden Drip", "emoji": "🌺"},
    5: {"name": "Front Yard Against House Drip", "emoji": "🏡"},
    6: {"name": "Front Lawn", "emoji": "🌿"}
}

def send_discord_notification(zone_name, zone_number, completion_time):
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
            "timestamp": datetime.now().isoformat()
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

if __name__ == "__main__":
    print("🧪 Testing Discord notifications...")
    
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not found in .env file")
        exit(1)
    
    # Test with Zone 1 (Backyard Garden Drip)
    success = send_discord_notification("Backyard Garden Drip", 1, "08:45:30")
    
    if success:
        print("🎉 Test successful! Check your Discord channel.")
    else:
        print("💥 Test failed. Check your webhook URL and try again.")