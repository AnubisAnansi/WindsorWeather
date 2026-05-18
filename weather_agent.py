import json
import os
import datetime
import urllib.request
import urllib.parse

# ── CONFIG ──────────────────────────────────────────────────────────────────
LATITUDE  = 51.4839  # Windsor, England
LONGITUDE = -0.6044
LOCATION  = "Windsor, England"
HISTORY_FILE = "weather_history.json"

# Loaded from GitHub Secrets (set these in your repo settings)
DISCORD_TOKEN      = os.environ["DISCORD_TOKEN"]
DISCORD_CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]

# Accuracy thresholds (°C)
SUCCESS_THRESHOLD = 2
AVERAGE_THRESHOLD = 5

# ── HELPERS ──────────────────────────────────────────────────────────────────

def fetch_url(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode())

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"daily": {}, "tally": {"success": 0, "average": 0, "failure": 0, "total": 0}}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def rating(diff):
    if diff is None:
        return None
    if diff <= SUCCESS_THRESHOLD:
        return "success"
    elif diff <= AVERAGE_THRESHOLD:
        return "average"
    else:
        return "failure"

def rating_emoji(r):
    return {"success": "✅", "average": "🟡", "failure": "❌"}.get(r, "❓")

def rating_label(r):
    return {"success": "Success", "average": "Average", "failure": "Failure"}.get(r, "N/A")

# ── WEATHER FETCH ─────────────────────────────────────────────────────────────

def fetch_weather():
    """Fetch today's actual weather AND 7-day forecast from Open-Meteo (free, no key)."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&forecast_days=8"
        f"&timezone=Europe%2FLondon"
    )
    data = fetch_url(url)
    daily = data["daily"]

    results = {}
    for i, date in enumerate(daily["time"]):
        results[date] = {
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "temp_avg": round((daily["temperature_2m_max"][i] + daily["temperature_2m_min"][i]) / 2, 1),
            "weathercode": daily["weathercode"][i],
        }
    return results

def weathercode_to_desc(code):
    codes = {
        0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
        45: "Foggy 🌫️", 48: "Icy fog 🌫️",
        51: "Light drizzle 🌦️", 53: "Moderate drizzle 🌦️", 55: "Dense drizzle 🌧️",
        61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
        71: "Slight snow 🌨️", 73: "Moderate snow 🌨️", 75: "Heavy snow ❄️",
        77: "Snow grains 🌨️",
        80: "Slight showers 🌦️", 81: "Moderate showers 🌧️", 82: "Violent showers ⛈️",
        85: "Snow showers 🌨️", 86: "Heavy snow showers ❄️",
        95: "Thunderstorm ⛈️", 96: "Thunderstorm w/ hail ⛈️", 99: "Thunderstorm w/ heavy hail ⛈️",
    }
    return codes.get(code, f"Unknown ({code})")

# ── DISCORD ───────────────────────────────────────────────────────────────────

def send_discord_message(message):
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    payload = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "WeatherAgent/1.0"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    today = datetime.date.today().isoformat()
    seven_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    history = load_history()
    weather = fetch_weather()

    # 1. Save today's actual weather
    if today in weather:
        history["daily"].setdefault(today, {})
        history["daily"][today]["actual"] = weather[today]

    # 2. Save forecasts for the next 7 days (keyed by target date, stored under forecast_made_on)
    for date, data in weather.items():
        if date != today:
            history["daily"].setdefault(date, {})
            history["daily"][date]["forecast"] = {
                "made_on": today,
                **data
            }

    # 3. Check accuracy: compare today's actual vs forecast made 7 days ago
    accuracy_result = None
    diff = None
    forecast_7d = None

    today_data = history["daily"].get(today, {})
    actual = today_data.get("actual")
    forecast_entry = today_data.get("forecast")

    if actual and forecast_entry and forecast_entry.get("made_on") == seven_days_ago:
        forecast_7d = forecast_entry
        diff = round(abs(actual["temp_avg"] - forecast_7d["temp_avg"]), 1)
        accuracy_result = rating(diff)

        # Update tally
        history["tally"][accuracy_result] += 1
        history["tally"]["total"] += 1
        history["daily"][today]["accuracy"] = {
            "diff": diff,
            "result": accuracy_result
        }

    save_history(history)

    # 4. Build Discord message
    tally = history["tally"]
    total = tally["total"]

    lines = []
    lines.append(f"# 🌤️ Windsor Weather Report")
    lines.append(f"📅 **{datetime.date.today().strftime('%A, %d %B %Y')}**")
    lines.append("")

    if actual:
        desc = weathercode_to_desc(actual["weathercode"])
        lines.append(f"## Today's Actual Weather")
        lines.append(f"🌡️ **Avg:** {actual['temp_avg']}°C  |  ▲ {actual['temp_max']}°C  ▼ {actual['temp_min']}°C")
        lines.append(f"🌥️ **Conditions:** {desc}")
    else:
        lines.append("⚠️ No actual weather data available yet for today.")

    lines.append("")

    if forecast_7d:
        f_desc = weathercode_to_desc(forecast_7d["weathercode"])
        lines.append(f"## 7-Day Forecast vs Reality")
        lines.append(f"🔮 **Forecast (made {seven_days_ago}):** {forecast_7d['temp_avg']}°C — {f_desc}")
        lines.append(f"📊 **Difference:** {diff}°C  →  {rating_emoji(accuracy_result)} **{rating_label(accuracy_result)}**")
    else:
        lines.append("📭 *No 7-day forecast comparison yet — check back in a week!*")

    lines.append("")

    # 5-day forecast preview
    lines.append(f"## 📆 5-Day Forecast")
    for i in range(1, 6):
        fdate = (datetime.date.today() + datetime.timedelta(days=i)).isoformat()
        if fdate in weather:
            fd = weather[fdate]
            fdesc = weathercode_to_desc(fd["weathercode"])
            label = datetime.date.fromisoformat(fdate).strftime("%a %d %b")
            lines.append(f"**{label}** — {fd['temp_avg']}°C ({fd['temp_min']}–{fd['temp_max']}°C) {fdesc}")

    lines.append("")

    # Accuracy tally
    lines.append(f"## 📈 Forecast Accuracy Tally")
    if total > 0:
        success_pct = round(tally['success'] / total * 100)
        avg_pct     = round(tally['average'] / total * 100)
        fail_pct    = round(tally['failure'] / total * 100)
        lines.append(f"✅ Success (≤2°C off): **{tally['success']}** ({success_pct}%)")
        lines.append(f"🟡 Average (3–5°C off): **{tally['average']}** ({avg_pct}%)")
        lines.append(f"❌ Failure (>5°C off): **{tally['failure']}** ({fail_pct}%)")
        lines.append(f"📊 Total comparisons: **{total}**")
    else:
        lines.append("*No comparisons yet — data builds up after 7 days!*")

    message = "\n".join(lines)
    send_discord_message(message)
    print("✅ Message sent to Discord!")
    print(message)

if __name__ == "__main__":
    main()
