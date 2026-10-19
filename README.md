# 🌿 Hydrawise Watcher

A lightweight Python service that runs on a Raspberry Pi and sends Discord and email notifications when a Hydrawise ([API docs](https://www.hunterirrigation.com/support/hydrawise-api-information)) irrigation zone completes its watering cycle.

## 🔧 Features

* Polls Hydrawise API for all zones
* Detects when a zone has finished watering
* Sends rich Discord webhook notifications with zone-specific emojis
* Sends email notifications to additional recipients
* **📊 Weekly summaries**: Automatic weekly irrigation reports every Sunday at 3 PM
* Custom zone names and unique emojis for each irrigation area
* Persistent activity tracking with automatic data cleanup
* Runs only during a configurable time window (default: 4:30am–9:00am)
* Seasonal shutoff: sleeps through winter and resumes on its own in spring
* Built for low-power devices like Raspberry Pi 5

## 🎨 Zone Configuration

Each zone displays with a unique emoji and custom name:
- 🍅 Zone 1: Backyard Garden Drip
- ⚽ Zone 2: Backyard Turf
- 🧭 Zone 3: Northern Side
- 🌸 Zone 4: Front Yard Garden Drip
- 🏠 Zone 5: Front Yard Against House Drip
- 🌳 Zone 6: Front Lawn

## ⚙️ Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your configuration:
   ```bash
   HYDRAWISE_API_KEY=your_hydrawise_api_key
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   
   # Email notifications (optional)
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_gmail_app_password
   EMAIL_TO=recipient@example.com

   # Irrigation season (optional, MM-DD inclusive; unset = always on)
   SEASON_START=04-01
   SEASON_END=10-15
   ```

3. Set up Discord webhook:
   - Go to your Discord server → Settings → Integrations → Webhooks
   - Create a new webhook for your irrigation channel
   - Copy the webhook URL to your `.env` file

4. Run the service:
   ```bash
   python hydrawise_watcher.py
   ```

## ❄️ Winter / Off Season

Set `SEASON_START` and `SEASON_END` in `.env` to match when the system is running.
Outside that window the watcher makes no API calls and sleeps until the next
`SEASON_START`. It posts a 💤 message to Discord when it goes dormant and a 🌱
message when it resumes. A window that wraps the new year (e.g. `10-01` to `03-31`) also works.

After changing the dates, restart the service to apply them:

```bash
sudo systemctl restart hydrawise-watcher
```

To stop it outright instead: `sudo systemctl disable --now hydrawise-watcher`.
Remember to `enable --now` it again in spring.
