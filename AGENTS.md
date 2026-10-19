# AGENTS.md

Guidance for AI agents (Claude Code and others) working in this repo. Setup, deployment and
the seasonal shutoff are covered in `README.md`. This file holds where things stand and what
is easy to get wrong.

## Project

One file, `hydrawise_watcher.py`. It's a polling loop that watches the Hydrawise v1
`statusschedule` API between 4:30 and 9:00 AM. When a zone finishes, it posts to Discord
and emails a second recipient, and it sends a summary every Sunday at 3 PM. Dependencies
are `requests` and `python-dotenv`. There is no test suite or linter.

## Where we left off (2026-10-19)

**Dormant on the Pi until April 1, 2027.** The Pi's `.env` sets `SEASON_START=04-01` and
`SEASON_END=10-15`. On restart in the off season, the watcher sends the 💤 Discord message
again. That is expected and not a bug. If nothing arrives in spring, check
`journalctl -u hydrawise-watcher` for the 🌱 "Resuming monitoring" line.

## Deployment

- **Raspberry Pi 5** (`raspberrypi`), Debian 12, Python 3.11.2. Reach it over Tailscale at
  `adam@100.107.81.122`. The LAN name only works when the Mac is at home. The Pi also runs
  nudge, watchlog, one-click-cnn and crits-fumbles, so restart only this unit.
- The repo is cloned at `~/Projects/hydrawise-watcher` with a `venv/` and `.env` alongside
  it. The unit is `systemd/hydrawise-watcher.service`, copied to `/etc/systemd/system/`. If
  you change the repo copy, re-copy it and run `daemon-reload`.
- Deploy: `ssh adam@100.107.81.122 'cd ~/Projects/hydrawise-watcher && git pull &&
  venv/bin/pip install -q -r requirements.txt && sudo systemctl restart hydrawise-watcher'`.
  A deploy is done only after `systemctl is-active` and a fresh journal line both check out.
- `.env` exists only on the Pi and is gitignored. Edit it in place and back it up first
  (`cp .env .env.bak`).

## Conventions and gotchas

- **Zones are keyed by relay ID, not zone number.** `ZONE_CONFIG` uses the API's `relay_id`
  (e.g. `5533837`). Keying by 1–6 compiles, but every zone silently falls back to 💧. The
  zone number shown in notifications and stored in `weekly_activity.json` is the API's
  `relay` field (1–6). The send functions take both `relay_id` and `zone_number`.
- **Env config is read at import.** `SEASON_START`/`SEASON_END` are parsed into
  `(month, day)` tuples when the module loads, so a malformed value fails at startup, not
  months later. Any date change needs a restart.
- **No local venv on the Mac.** To check logic without installing anything, stub `requests`
  and `dotenv` in `sys.modules` before importing `hydrawise_watcher`. The module has no
  import-time side effects beyond `load_dotenv()`.
- **`test_discord.py` sends real messages** to the Discord channel and the email
  recipient. Don't run it without asking. It imports the send functions from
  `hydrawise_watcher.py`, so keep it that way rather than copying them back in.
- `weekly_activity.json` is runtime state on the Pi (last 8 days of completed runs). It's
  gitignored. Don't delete it, or the next Sunday summary is lost.

## Waiting on spring 2027

The zone-number fix (2026-10-19) has been checked only offline, with `requests` and
`smtplib` stubbed. It hasn't run against a real watering yet. After the first run in
April, confirm that Discord shows `Zone 1`–`Zone 6` (not `Zone 5533837`) and that the
first Sunday summary looks right.
