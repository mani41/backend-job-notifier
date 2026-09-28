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
        requests.post(telegram_url, json=payload, timeout=10)
        print(f"[{source}] Alert sent: {job_title}")
    except Exception as e:
        print(f"Failed to send alert for {job_title}: {e}")


# --- 1. We Work Remotely (RSS Feed) ---
def fetch_weworkremotely():
    print("Checking We Work Remotely...")
    feed_url = "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss"
    matched = []
    try:
        feed = feedparser.parse(feed_url)
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
        print(f"WWR Error: {e}")
    return matched


# --- 2. Remote OK (JSON API) ---
def fetch_remoteok():
    print("Checking Remote OK...")
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0"}
    matched = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for job in data[1:30]:  # Skip index 0 (legal header)
                title = job.get("position", "").lower()
                tags = [t.lower() for t in job.get("tags", [])]
                if any(kw in title for kw in KEYWORDS) or any(kw in " ".join(tags) for kw in KEYWORDS):
                    matched.append({
                        "title": job.get("position"),
                        "company": job.get("company"),
                        "url": job.get("url"),
                        "source": "Remote OK"
                    })
    except Exception as e:
        print(f"RemoteOK Error: {e}")
    return matched


# --- 3. Himalayas (JSON API) ---
def fetch_himalayas():
    print("Checking Himalayas...")
    url = "https://himalayas.app/jobs/api?limit=30"
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


# --- 4. Remotive (JSON API) ---
def fetch_remotive():
    print("Checking Remotive...")
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=30"
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


# --- 5. Arbeitnow (JSON API) ---
def fetch_arbeitnow():
    print("Checking Arbeitnow...")
    url = "https://www.arbeitnow.com/api/job-board-api"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("data", [])
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
        print(f"Arbeitnow Error: {e}")
    return matched


# --- 6. Jobicy (JSON API) ---
def fetch_jobicy():
    print("Checking Jobicy...")
    url = "https://jobicy.com/api/v2/remote-jobs?count=20&industry=engineering"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
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
        print(f"Jobicy Error: {e}")
    return matched


# --- 7. JustRemote (RSS Feed) ---
def fetch_justremote():
    print("Checking JustRemote...")
    feed_url = "https://justremote.co/remote-developer-jobs.rss"
    matched = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title.lower()
            if any(kw in title for kw in KEYWORDS):
                matched.append({
                    "title": entry.title,
                    "company": "JustRemote",
                    "url": entry.link,
                    "source": "JustRemote"
                })
    except Exception as e:
        print(f"JustRemote Error: {e}")
    return matched


def fetch_and_notify():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("CRITICAL ERROR: Secrets TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
        return

    all_jobs = []
    all_jobs.extend(fetch_weworkremotely())
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_himalayas())
    all_jobs.extend(fetch_remotive())
    all_jobs.extend(fetch_arbeitnow())
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_justremote())

    print(f"\n--- Total Matches Across Sources: {len(all_jobs)} ---")

    # Send up to 5 matching alerts per run
    for job in all_jobs[:5]:
        send_telegram_alert(job["title"], job["company"], job["url"], job["source"])


if __name__ == "__main__":
    fetch_and_notify()
