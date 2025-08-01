# 🌿 Hydrawise Watcher

A lightweight Python service that runs on a Raspberry Pi and sends Discord notifications when a Hydrawise ([API docs](https://www.hunterirrigation.com/support/hydrawise-api-information)) irrigation zone completes its watering cycle.

## 🔧 Features

* Polls Hydrawise API for all zones
* Detects when a zone has finished watering
* Sends rich Discord webhook notifications with zone-specific emojis
* Custom zone names and unique emojis for each irrigation area
* Runs only during a configurable time window (default: 4:30am–9:00am)
* Built for low-power devices like Raspberry Pi 5

## 🎨 Zone Configuration

Each zone displays with a unique emoji and custom name:
- 🍅 Zone 1: Backyard Garden Drip
- 🌱 Zone 2: Backyard Turf
- 🌲 Zone 3: Northern Side
- 🌺 Zone 4: Front Yard Garden Drip
- 🏡 Zone 5: Front Yard Against House Drip
- 🌿 Zone 6: Front Lawn

## ⚙️ Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your configuration:
   ```bash
   HYDRAWISE_API_KEY=your_hydrawise_api_key
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   ```

3. Set up Discord webhook:
   - Go to your Discord server → Settings → Integrations → Webhooks
   - Create a new webhook for your irrigation channel
   - Copy the webhook URL to your `.env` file

4. Run the service:
   ```bash
   python hydrawise_watcher.py
   ```
