# 🌿 Hydrawise Watcher

A lightweight Python service that runs on a Raspberry Pi and emails you when a Hydrawise ([API docs](https://www.hunterirrigation.com/support/hydrawise-api-information)) irrigation zone completes its watering cycle.

## 🔧 Features

* Polls Hydrawise API for all zones
* Detects when a zone has finished watering
* Sends an email alert with zone name and timestamp
* Runs only during a configurable time window (default: 4:30am–9:00am)
* Built for low-power devices like Raspberry Pi 5
