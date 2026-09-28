import os
import requests
import feedparser

KEYWORDS = [
    "frontend", "front-end", "front end", "ui",
    "angular", "react", "vue", "typescript", "javascript", "web developer"
]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram_alert(job_title, company, job_url, source):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message_text = (
        f"🚨 *New Job Alert!* ({source})\n\n"
        f"📌 *Position:* {job_title}\n"
        f"🏢 *Company:* {company}\n"
        f"🔗 [Apply Here]({job_url})"
    )
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        res = requests.post(telegram_url, json=payload, timeout=10)
        print(f"[{source}] Telegram delivery status: {res.status_code}")
        if res.status_code != 200:
            print(f"Telegram error details: {res.text}")
    except Exception as e:
        print(f"Failed to send alert for {job_title}: {e}")


def fetch_remotive():
    print("Checking Remotive...")
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=50"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            for job in jobs:
                title = job.get("title", "").lower()
                if any(kw in title for kw in KEYWORDS):
                    matched.append({
                        "title": job.get("title"),
                        "company": job.get("company_name"),
                        "url": job.get("url"),
                        "source": "Remotive"
                    })
    except Exception as e:
        print(f"Remotive Error: {e}")
    return matched


def fetch_himalayas():
    print("Checking Himalayas...")
    url = "https://himalayas.app/jobs/api?limit=50"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            for job in jobs:
                title = job.get("title", "").lower()
                if any(kw in title for kw in KEYWORDS):
                    matched.append({
                        "title": job.get("title"),
                        "company": job.get("companyName"),
                        "url": job.get("applicationUrl") or f"https://himalayas.app/jobs/{job.get('slug')}",
                        "source": "Himalayas"
                    })
    except Exception as e:
        print(f"Himalayas Error: {e}")
    return matched


def fetch_and_notify():
    # Diagnostic Secret Verification
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ CRITICAL ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secrets are missing or not passed correctly!")
        print(f"TOKEN Present: {bool(TELEGRAM_BOT_TOKEN)} | CHAT_ID Present: {bool(TELEGRAM_CHAT_ID)}")
        return

    print("✅ Secrets found. Fetching jobs...")

    all_jobs = []
    all_jobs.extend(fetch_remotive())
    all_jobs.extend(fetch_himalayas())

    print(f"\n--- Total Matches Found Across Active APIs: {len(all_jobs)} ---")

    if not all_jobs:
        print("No job matches found in current API query window.")
        return

    # Send top 5 matching alerts
    for job in all_jobs[:5]:
        send_telegram_alert(job["title"], job["company"], job["url"], job["source"])


if __name__ == "__main__":
    fetch_and_notify()
