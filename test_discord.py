#!/usr/bin/env python3
from datetime import datetime

# Use the watcher's own send functions and ZONE_CONFIG so this test can't drift from them
from hydrawise_watcher import DISCORD_WEBHOOK_URL, send_discord_notification, send_email_notification

if __name__ == "__main__":
    print("🧪 Testing Discord notifications...")
    
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not found in .env file")
        exit(1)
    
    # Relay ID and zone number for Backyard Garden Drip (zone 1)
    test_completion_time = datetime.now().replace(hour=8, minute=45, second=30, microsecond=0)
    
    print("Testing Discord notification...")
    discord_success = send_discord_notification("Backyard Garden Drip", 5533837, 1, "08:45:30", test_completion_time)
    
    print("\nTesting email notification...")
    email_success = send_email_notification("Backyard Garden Drip", 5533837, 1, "08:45:30", test_completion_time)
    
    print(f"\n📊 Test Results:")
    print(f"Discord: {'✅ Success' if discord_success else '❌ Failed'}")
    print(f"Email: {'✅ Success' if email_success else '❌ Failed'}")
    
    if discord_success or email_success:
        print("🎉 At least one notification method worked!")
    else:
        print("💥 All notification methods failed. Check your configuration.")