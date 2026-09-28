import os
import requests

URL = "https://remotive.com/api/remote-jobs?category=software-dev&limit=10"
KEYWORDS = ["frontend", "react", "vue", "next.js", "typescript"]

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

    requests.post(telegram_url, json=payload)


def fetch_and_notify():
    response = requests.get(URL)
    if response.status_code != 200:
        print("Failed to fetch jobs")
        return

    jobs = response.json().get("jobs", [])

    for job in jobs:
        title = job.get("title", "").lower()
        if any(kw in title for kw in KEYWORDS):
            job_title = job.get("title")
            company = job.get("company_name")
            job_url = job.get("url")

            send_telegram_alert(job_title, company, job_url)


if __name__ == "__main__":
    fetch_and_notify()
