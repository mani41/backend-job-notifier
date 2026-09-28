"""
================================================================================
SCRIPT: Frontend Job Alert Bot (scraper.py)
PURPOSE: Aggregates real-time Frontend & Web Development job postings across 
         5 remote job portals and dispatches instant alerts via Telegram.

JOB PORTALS CHECKED:
1. Himalayas (https://himalayas.app) - Search API endpoint for frontend roles.
2. Remotive (https://remotive.com) - Software development API category.
3. We Work Remotely (https://weworkremotely.com) - Front-End RSS feed.
4. Arbeitnow (https://www.arbeitnow.com) - European & Global remote job API.
5. Jobicy (https://jobicy.com) - Engineering remote job feed API.

TRACKED KEYWORDS:
- Positions: "frontend", "front-end", "front end", "ui", "web developer"
- Technologies: "angular", "react", "vue", "typescript", "javascript"

EXECUTION:
- Scheduled hourly via GitHub Actions workflow (.github/workflows/job_alert.yml)
- Environment Variables required: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
================================================================================
"""

import os
import requests
import feedparser

# Keywords to match relevant Frontend & Web Development roles
KEYWORDS = [
    "frontend", "front-end", "front end", "ui",
    "angular", "react", "vue", "typescript", "javascript", "web developer"
]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def log(msg):
    """Prints output immediately to stdout for real-time viewing in GitHub Actions logs."""
    print(msg, flush=True)


def send_telegram_alert(job_title, company, job_url, source):
    """Formats and dispatches notifications via Telegram Bot API."""
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


# ==============================================================================
# PORTAL 1: Himalayas (https://himalayas.app)
# Focus: Global Remote Job Board featuring tech, startup, and engineering roles.
# ==============================================================================
def fetch_himalayas():
    log("Checking Portal: Himalayas (Search API)...")
    url = "https://himalayas.app/jobs/api/search?q=frontend"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        log(f"Himalayas HTTP Status: {res.status_code}")
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            log(f"Himalayas returned {len(jobs)} raw job results.")
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


# ==============================================================================
# PORTAL 2: Remotive (https://remotive.com)
# Focus: Curated global remote software development positions.
# ==============================================================================
def fetch_remotive():
    log("Checking Portal: Remotive (Software Dev API)...")
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=30"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            log(f"Remotive returned {len(jobs)} software jobs.")
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


# ==============================================================================
# PORTAL 3: We Work Remotely (https://weworkremotely.com)
# Focus: One of the largest remote-only job boards in tech & engineering.
# ==============================================================================
def fetch_weworkremotely():
    log("Checking Portal: We Work Remotely (RSS Feed)...")
    feed_url = "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss"
    matched = []
    try:
        feed = feedparser.parse(feed_url)
        log(f"WeWorkRemotely returned {len(feed.entries)} feed items.")
        for entry in feed.entries:
            title = entry.title.lower()
            if any(kw in title for kw in KEYWORDS):
                matched.append({
                    "title": entry.title,
                    "company": getattr(entry, "author", "WeWorkRemotely"),
                    "url": entry.link,
                    "source": "We Work Remotely"
                })
    except Exception as e:
        log(f"WeWorkRemotely fetch error: {e}")
    return matched


# ==============================================================================
# PORTAL 4: Arbeitnow (https://www.arbeitnow.com)
# Focus: International and European remote engineering roles.
# ==============================================================================
def fetch_arbeitnow():
    log("Checking Portal: Arbeitnow (Public API)...")
    url = "https://www.arbeitnow.com/api/job-board-api"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("data", [])
            log(f"Arbeitnow returned {len(jobs)} jobs.")
            for job in jobs:
                title = job.get("title", "").lower()
                if any(kw in title for kw in KEYWORDS):
                    matched.append({
                        "title": job.get("title"),
                        "company": job.get("company_name"),
                        "url": job.get("url"),
                        "source": "Arbeitnow"
                    })
    except Exception as e:
        log(f"Arbeitnow fetch error: {e}")
    return matched


# ==============================================================================
# PORTAL 5: Jobicy (https://jobicy.com)
# Focus: Remote engineering and frontend positions worldwide.
# ==============================================================================
def fetch_jobicy():
    log("Checking Portal: Jobicy (Engineering API)...")
    url = "https://jobicy.com/api/v2/remote-jobs?count=20&industry=engineering"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            log(f"Jobicy returned {len(jobs)} jobs.")
            for job in jobs:
                title = job.get("jobTitle", "").lower()
                if any(kw in title for kw in KEYWORDS):
                    matched.append({
                        "title": job.get("jobTitle"),
                        "company": job.get("companyName"),
                        "url": job.get("url"),
                        "source": "Jobicy"
                    })
    except Exception as e:
        log(f"Jobicy fetch error: {e}")
    return matched


# ==============================================================================
# MAIN EXECUTOR & AGGREGATOR
# ==============================================================================
def fetch_and_notify():
    log("=== STARTING JOB FETCH ===")
    
    # Verify Secret Availability
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("❌ CRITICAL ERROR: Secret variables are missing in GitHub repository settings!")
        log(f"TOKEN Loaded: {bool(TELEGRAM_BOT_TOKEN)} | CHAT_ID Loaded: {bool(TELEGRAM_CHAT_ID)}")
        return

    log("✅ GitHub Secrets loaded successfully.")

    # Execute and aggregate all portal checks
    all_jobs = []
    all_jobs.extend(fetch_himalayas())
    all_jobs.extend(fetch_remotive())
    all_jobs.extend(fetch_weworkremotely())
    all_jobs.extend(fetch_arbeitnow())
    all_jobs.extend(fetch_jobicy())

    log(f"\n--- Total Matching Frontend Jobs Found: {len(all_jobs)} ---")

    if not all_jobs:
        log("No new jobs matched the keyword criteria in this run.")
        return

    # Dispatch alerts for up to the first 5 matches per run
    for job in all_jobs[:5]:
        log(f"Sending alert for: '{job['title']}' from [{job['source']}]")
        send_telegram_alert(job["title"], job["company"], job["url"], job["source"])

    log("=== JOB FETCH COMPLETE ===")


if __name__ == "__main__":
    fetch_and_notify()
