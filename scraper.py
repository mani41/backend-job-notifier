import os
import sys
import requests

KEYWORDS = [
    "frontend", "front-end", "front end", "ui",
    "angular", "react", "vue", "typescript", "javascript", "web developer"
]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def log(msg):
    """Force print output immediately to GitHub Actions stdout"""
    print(msg, flush=True)


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
        log(f"[{source}] Telegram delivery response: {res.status_code}")
        if res.status_code != 200:
            log(f"Telegram API Error Details: {res.text}")
    except Exception as e:
        log(f"Failed sending alert for {job_title}: {e}")


def fetch_himalayas_search():
    log("Checking Himalayas Search Endpoint...")
    url = "https://himalayas.app/jobs/api/search?q=frontend"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        log(f"Himalayas API response status: {res.status_code}")
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            log(f"Himalayas returned {len(jobs)} raw frontend jobs.")
            for job in jobs[:10]:
                matched.append({
                    "title": job.get("title"),
                    "company": job.get("companyName"),
                    "url": job.get("applicationUrl") or f"https://himalayas.app/jobs/{job.get('slug')}",
                    "source": "Himalayas"
                })
    except Exception as e:
        log(f"Himalayas fetch error: {e}")
    return matched


def fetch_remotive():
    log("Checking Remotive API...")
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=30"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        log(f"Remotive API response status: {res.status_code}")
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            log(f"Remotive returned {len(jobs)} software development jobs.")
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
        log(f"Remotive fetch error: {e}")
    return matched


def fetch_and_notify():
    log("=== STARTING JOB FETCH ===")
    
    # 1. Check if Secrets are loaded
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("❌ CRITICAL ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secrets are missing in GitHub settings!")
        log(f"TOKEN Loaded: {bool(TELEGRAM_BOT_TOKEN)} | CHAT_ID Loaded: {bool(TELEGRAM_CHAT_ID)}")
        return

    log("✅ GitHub Secrets loaded successfully.")

    # 2. Fetch jobs from APIs
    all_jobs = []
    all_jobs.extend(fetch_himalayas_search())
    all_jobs.extend(fetch_remotive())

    log(f"\n--- Total Matches Collected: {len(all_jobs)} ---")

    if not all_jobs:
        log("No jobs matched in this run.")
        return

    # 3. Send top 5 alerts to Telegram
    for job in all_jobs[:5]:
        log(f"Sending alert for: {job['title']} from {job['source']}")
        send_telegram_alert(job["title"], job["company"], job["url"], job["source"])

    log("=== JOB FETCH COMPLETE ===")


if __name__ == "__main__":
    fetch_and_notify()
