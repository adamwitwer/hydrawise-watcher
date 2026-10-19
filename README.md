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

Each zone displays with a unique emoji and custom name, set in `ZONE_CONFIG` in
`hydrawise_watcher.py`. Zones are keyed by their Hydrawise **relay ID** (e.g. `5533837`),
not by zone number. A relay that isn't listed falls back to its Hydrawise name with 💧.

- 🍅 Backyard Garden Drip
- ⚽ Backyard Turf
- 🧭 Right/Northern Side
- 🌸 Front Yard Garden Drip
- 🏠 Front Yard Against House Drip
- 🌳 Front Lawn

## ⚙️ Setup

1. Create a venv and install dependencies:
   ```bash
   python3 -m venv venv
   venv/bin/pip install -r requirements.txt
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

4. Check the Discord and email settings. This sends a **real** sample notification to both:
   ```bash
   venv/bin/python test_discord.py
   ```

5. Run the service:
   ```bash
   venv/bin/python hydrawise_watcher.py
   ```

## 🍓 Deployment (Raspberry Pi)

The watcher runs on the Pi as a systemd service from a git clone at
`~/Projects/hydrawise-watcher`, with its own `venv/` and `.env`. The unit file is in
`systemd/hydrawise-watcher.service`. To install it:

```bash
sudo cp systemd/hydrawise-watcher.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hydrawise-watcher
```

To deploy an update:

```bash
cd ~/Projects/hydrawise-watcher
git pull
venv/bin/pip install -q -r requirements.txt
sudo systemctl restart hydrawise-watcher
```

Check that it came back up:

```bash
systemctl is-active hydrawise-watcher
journalctl -u hydrawise-watcher -n 20 --no-pager
```

Completed runs are saved to `weekly_activity.json` (gitignored), which keeps the last
8 days for the Sunday summary.

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
