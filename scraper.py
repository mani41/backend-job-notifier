import os
import requests

# Expanded keywords covering Titles, Tech Stack, Frameworks & Libraries
KEYWORDS = [
    # Job Titles
    "frontend", "front-end", "front end", 
    "ui engineer", "ui developer", "web engineer", "web developer",
    
    # Primary Frameworks & Libraries (Nivedita's Stack + Standard FE)
    "angular", "rxjs", "ngrx", "react", "vue", "next.js", "nuxt", "svelte",
    
    # Languages & Core Standards
    "typescript", "javascript", "es6", "html5", "css3",
    
    # CSS Frameworks & Architecture
    "tailwind", "bootstrap", "material ui", "angular material",
    "micro-frontend", "microfrontend", "bff", "single page application", "spa"
]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram_alert(job_title, company, job_url):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    message_text = (
        f"🚨 *New Frontend Job Alert!*\n\n"
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

    res = requests.post(telegram_url, json=payload)
    print(f"Telegram alert sent for '{job_title}' (Status: {res.status_code})")


def fetch_jobs_from_remotive():
    url = "https://remotive.com/api/remote-jobs?limit=50"
    print("Fetching jobs from Remotive...")
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Remotive API error: {response.status_code}")
        return []

    jobs = response.json().get("jobs", [])
    matched_jobs = []

    for job in jobs:
        # Check both title and description tags for matching keywords
        title = job.get("title", "").lower()
        tags = [t.lower() for t in job.get("tags", [])]
        
        # Match if title or any tag contains one of our keywords
        title_match = any(kw in title for kw in KEYWORDS)
        tag_match = any(kw in " ".join(tags) for kw in KEYWORDS)
        
        if title_match or tag_match:
            matched_jobs.append({
                "title": job.get("title"),
                "company": job.get("company_name"),
                "url": job.get("url")
            })

    return matched_jobs


def fetch_and_notify():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
        return

    matched_jobs = fetch_jobs_from_remotive()
    print(f"Total matching frontend roles found: {len(matched_jobs)}")

    # Limit to top 5 per run so Telegram doesn't get flooded
    for job in matched_jobs[:5]:
        send_telegram_alert(job["title"], job["company"], job["url"])


if __name__ == "__main__":
    fetch_and_notify()
