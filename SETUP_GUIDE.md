# 🌤️ Windsor Weather Agent — Setup Guide

## What this does
Every day at 8am UK time, this agent:
1. Fetches today's actual weather for Windsor, England
2. Compares it against what was forecast 7 days ago
3. Rates the forecast: ✅ Success (≤2°C off) | 🟡 Average (≤5°C off) | ❌ Failure (>5°C off)
4. Builds a running accuracy tally over time
5. Posts everything to your Discord channel
6. Saves history to `weather_history.json` in your GitHub repo

---

## Step 1 — Create a GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **+** (top right) → **New repository**
3. Name it: `windsor-weather-agent`
4. Set it to **Private** (recommended)
5. Tick **"Add a README file"**
6. Click **Create repository**

---

## Step 2 — Upload the files

Upload these three files to your new repo:

| File | Where to put it |
|------|----------------|
| `weather_agent.py` | Root of repo |
| `weather_history.json` | Root of repo |
| `.github/workflows/weather.yml` | You must create the folders `.github/workflows/` first |

### How to upload:
1. On your repo page, click **Add file** → **Upload files**
2. Drag in `weather_agent.py` and `weather_history.json` → Commit
3. Click **Add file** → **Create new file**
4. In the filename box, type: `.github/workflows/weather.yml`
5. Paste the contents of `weather.yml` into the editor
6. Click **Commit new file**

---

## Step 3 — Add your Discord secrets

GitHub needs your Discord Bot Token and Channel ID stored securely as **Secrets**.

1. In your repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

| Secret Name | Value |
|-------------|-------|
| `DISCORD_TOKEN` | Your Discord bot token (regenerated one) |
| `DISCORD_CHANNEL_ID` | The channel ID where the bot should post |

### How to get your Channel ID:
1. In Discord: **Settings → Advanced → Enable Developer Mode**
2. Right-click the channel → **Copy Channel ID**
3. Paste it as the `DISCORD_CHANNEL_ID` secret

---

## Step 4 — Test it manually

1. In your repo, go to **Actions** tab
2. Click **Windsor Weather Agent** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Watch it run — check your Discord channel for the message!

---

## Step 5 — You're done! 🎉

From now on it runs automatically every day at 8am UK time.
The `weather_history.json` file in your repo will grow daily with all weather data and accuracy scores.

---

## Accuracy Rating System

| Rating | Criteria | Emoji |
|--------|----------|-------|
| Success | Forecast within ±2°C of actual | ✅ |
| Average | Forecast within ±3–5°C of actual | 🟡 |
| Failure | Forecast more than ±5°C off actual | ❌ |

Note: Accuracy comparisons only start appearing after **7 days** of data collection.

---

## Troubleshooting

**Bot not posting?**
- Make sure the bot has **Send Messages** permission in the channel
- Double-check `DISCORD_TOKEN` and `DISCORD_CHANNEL_ID` secrets are correct

**Actions not running?**
- Check the **Actions** tab for error logs
- Make sure the `.github/workflows/weather.yml` file is in exactly that folder path

**Wrong time?**
- The cron is set to `0 7 * * *` (7am UTC = 8am BST in summer, 7am GMT in winter)
- To always hit 8am GMT, change to `0 8 * * *`
