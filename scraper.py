"""
================================================================================
SCRIPT: Frontend & Full Stack Job Alert Bot (scraper.py)
PURPOSE: Aggregates real-time Frontend, Angular, and Full Stack job postings 
         across 7 job portals and dispatches instant alerts via Telegram.

JOB PORTALS CHECKED:
1. Himalayas (https://himalayas.app) - Search API endpoint for tech roles.
2. Remotive (https://remotive.com) - Software development API category.
3. We Work Remotely (https://weworkremotely.com) - Front-End RSS feed.
4. Arbeitnow (https://www.arbeitnow.com) - European & Global remote job API.
5. Jobicy (https://jobicy.com) - Engineering remote job feed API.
6. Hacker News (https://news.ycombinator.com) - Real-time official Firebase API.
7. LinkedIn (https://linkedin.com) - Public Guest API (Bengaluru & Remote roles).
8. GREENHOUSE_SEARCH_URL = "https://my.greenhouse.io/jobs/search"
FILTERS & STATE MANAGEMENT:
- Age Limit: Only notifies jobs posted within the last 7 days (CUTOFF_DAYS = 7).
- Duplicate Prevention: Tracks processed job URLs inside 'seen_jobs.json'.

EXECUTION:
- Scheduled hourly via GitHub Actions workflow (.github/workflows/job_alert.yml)
- Environment Variables required: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
================================================================================
"""

import json
import os
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

SEEN_JOBS_FILE = "seen_jobs.json"
CUTOFF_DAYS = 2  # Maximum job age in days

# Keywords to match relevant Frontend & Full Stack roles
KEYWORDS = [
    "backend", "back-end", "back end",
    "java", "springboot", "system design", "spring boot", "javascript", "cloud", "saas", "ai integration", "ai assisted development", "spec driven development",
    "distributed system", "RAG", "LLM", "Langchain", "claude", "workflow", "agentic ai", "ai tool", "API Gateway", "Circuit Breaker", "Retry", "Dead Letter Queue (DLQ)", "Concurrency",
"Databases", "PostgreSQL", "Spring Batch", "Microservices", "AWS",
    "fullstack", "full-stack", "full stack"
]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def log(msg):
    """Prints output immediately to stdout for real-time viewing in GitHub Actions logs."""
    print(msg, flush=True)


def is_within_last_days(date_val, max_days=CUTOFF_DAYS):
    """
    Checks if a job posting date/timestamp is within max_days (7 days) from now.
    Supports ISO strings, epoch timestamps, and feedparser struct_time tuples.
    """
    if not date_val:
        return True  # If portal provides no date metadata, default to keep

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_days)

    try:
        # Handle Unix epoch timestamp (int, float, or numeric string)
        if isinstance(date_val, (int, float)) or (isinstance(date_val, str) and date_val.isdigit()):
            ts = float(date_val)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt >= cutoff

        # Handle struct_time tuple from RSS feeds (feedparser)
        if isinstance(date_val, time.struct_time):
            ts = time.mktime(date_val)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt >= cutoff

        # Handle ISO formatted date strings
        if isinstance(date_val, str):
            clean_str = date_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt >= cutoff
    except Exception:
        pass

    return True


def load_seen_jobs():
    """Loads previously notified job URLs/IDs from JSON file."""
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            log(f"Error loading seen jobs file: {e}")
    return set()


def save_seen_jobs(seen_jobs):
    """Saves updated set of notified job URLs/IDs back to JSON file."""
    try:
        with open(SEEN_JOBS_FILE, "w") as f:
            json.dump(list(seen_jobs), f, indent=2)
        log("Updated seen_jobs.json successfully.")
    except Exception as e:
        log(f"Error saving seen jobs file: {e}")


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
# ==============================================================================
def fetch_himalayas():
    log("Checking Portal: Himalayas (Search API)...")
    url = "https://himalayas.app/jobs/api/search?q=frontend"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            for job in jobs[:15]:
                pub_date = job.get("pubDate") or job.get("createdAt") or job.get("publishedAt")
                if is_within_last_days(pub_date):
                    job_url = job.get("applicationUrl") or f"https://himalayas.app/jobs/{job.get('slug')}"
                    matched.append({
                        "id": job_url,
                        "title": job.get("title"),
                        "company": job.get("companyName"),
                        "url": job_url,
                        "source": "Himalayas"
                    })
    except Exception as e:
        log(f"Himalayas fetch error: {e}")
    return matched


# ==============================================================================
# PORTAL 2: Remotive (https://remotive.com)
# ==============================================================================
def fetch_remotive():
    log("Checking Portal: Remotive (Software Dev API)...")
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=30"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            for job in jobs:
                title = job.get("title", "").lower()
                pub_date = job.get("publication_date")
                if any(kw in title for kw in KEYWORDS) and is_within_last_days(pub_date):
                    matched.append({
                        "id": job.get("url"),
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
# ==============================================================================
def fetch_weworkremotely():
    log("Checking Portal: We Work Remotely (RSS Feed)...")
    feed_url = "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss"
    matched = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title.lower()
            pub_date = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
            if any(kw in title for kw in KEYWORDS) and is_within_last_days(pub_date):
                matched.append({
                    "id": entry.link,
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
# ==============================================================================
def fetch_arbeitnow():
    log("Checking Portal: Arbeitnow (Public API)...")
    url = "https://www.arbeitnow.com/api/job-board-api"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("data", [])
            for job in jobs:
                title = job.get("title", "").lower()
                pub_date = job.get("created_at")
                if any(kw in title for kw in KEYWORDS) and is_within_last_days(pub_date):
                    matched.append({
                        "id": job.get("url"),
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
# ==============================================================================
def fetch_jobicy():
    log("Checking Portal: Jobicy (Engineering API)...")
    url = "https://jobicy.com/api/v2/remote-jobs?count=20&industry=engineering"
    matched = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            for job in jobs:
                title = job.get("jobTitle", "").lower()
                pub_date = job.get("pubDate")
                if any(kw in title for kw in KEYWORDS) and is_within_last_days(pub_date):
                    matched.append({
                        "id": job.get("url"),
                        "title": job.get("jobTitle"),
                        "company": job.get("companyName"),
                        "url": job.get("url"),
                        "source": "Jobicy"
                    })
    except Exception as e:
        log(f"Jobicy fetch error: {e}")
    return matched


# ==============================================================================
# PORTAL 6: Hacker News (https://news.ycombinator.com)
# ==============================================================================
def fetch_hacker_news():
    log("Checking Portal: Hacker News (Firebase API)...")
    matched = []
    try:
        res = requests.get("https://hacker-news.firebaseio.com/v0/jobstories.json", timeout=10)
        if res.status_code == 200:
            story_ids = res.json()[:15]
            for s_id in story_ids:
                item_res = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{s_id}.json", timeout=10)
                if item_res.status_code == 200:
                    item = item_res.json()
                    title = item.get("title", "").lower()
                    pub_date = item.get("time")  # Unix epoch timestamp
                    if any(kw in title for kw in KEYWORDS) and is_within_last_days(pub_date):
                        job_url = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}"
                        matched.append({
                            "id": str(item.get("id")),
                            "title": item.get("title"),
                            "company": "Hacker News Startup",
                            "url": job_url,
                            "source": "Hacker News"
                        })
    except Exception as e:
        log(f"Hacker News fetch error: {e}")
    return matched


# ==============================================================================
# PORTAL 7: LinkedIn Guest Search API (https://linkedin.com)
# ==============================================================================
def fetch_linkedin(search_query="Frontend", location="Bengaluru"):
    log(f"Checking Portal: LinkedIn Guest API ('{search_query}' in '{location}')...")
    encoded_query = urllib.parse.quote(search_query)
    encoded_loc = urllib.parse.quote(location)
    
    # f_TPR=r604800 enforces a 7-day server-side date filter (604,800 seconds)
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_query}&location={encoded_loc}&f_TPR=r604800&start=0"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    matched = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        log(f"LinkedIn HTTP Status: {res.status_code}")
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            job_cards = soup.find_all("li")
            
            for card in job_cards:
                title_elem = card.find("h3", class_="base-search-card__title")
                company_elem = card.find("h4", class_="base-search-card__subtitle")
                link_elem = card.find("a", class_="base-card__full-link")
                time_elem = card.find("time")
                
                pub_date = time_elem.get("datetime") if (time_elem and time_elem.has_attr("datetime")) else None
                
                if title_elem and link_elem and is_within_last_days(pub_date):
                    title = title_elem.text.strip()
                    company = company_elem.text.strip() if company_elem else "LinkedIn Listing"
                    job_url = link_elem["href"].split("?")[0]
                    
                    title_lower = title.lower()
                    if any(kw in title_lower for kw in KEYWORDS):
                        matched.append({
                            "id": job_url,
                            "title": title,
                            "company": company,
                            "url": job_url,
                            "source": f"LinkedIn ({location})"
                        })
    except Exception as e:
        log(f"LinkedIn fetch error for '{search_query}' in '{location}': {e}")
        
    return matched


# ==============================================================================
# PORTAL 8: MyGreenhouse (https://my.greenhouse.io)
# ==============================================================================


# ==============================================================================
# PORTAL 8: MyGreenhouse Search + Public Job Board API
# ==============================================================================

GREENHOUSE_SEARCH_PARAMS = {
    "query": "Software",
    "location": "Bengaluru, Karnataka, India",
    "lat": "12.97194",
    "lon": "77.59369",
    "location_type": "locality",
    "country_short_name": "IN",
    "state_short_name": "KA",
    "date_posted": "past_five_days",
    "employment_type[]": "full_time",
}

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


def greenhouse_board_token(company_name):
    """Convert a company name into a candidate board token."""
    import re
    token = company_name.lower().strip()
    token = re.sub(r"[^a-z0-9]+", "-", token)
    return token.strip("-")


def fetch_greenhouse():
    log("Checking Portal: MyGreenhouse (Bengaluru)...")

    matched = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/json",
    })

    try:
        # Step 1: Request the filtered MyGreenhouse search page.
        response = session.get(
            GREENHOUSE_SEARCH_URL,
            params=GREENHOUSE_SEARCH_PARAMS,
            timeout=20,
        )

        log(f"MyGreenhouse HTTP Status: {response.status_code}")
        log(f"MyGreenhouse Final URL: {response.url}")

        if "/users/sign_in" in response.url:
            log(
                "MyGreenhouse search redirected to sign-in. "
                "Cannot discover companies from this response. "
                "Check for an accessible search endpoint or "
                "provide an authenticated session."
            )
            return matched

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Step 2: Extract company names and candidate board tokens.
        # These selectors must be adjusted if the live HTML uses
        # a different structure.
        companies = {}

        for card in soup.select(
            '[data-testid*="job"], '
            '[class*="job-card"], '
            '[class*="JobCard"]'
        ):
            company_elem = card.select_one(
                '[class*="company"], '
                '[data-testid*="company"]'
            )

            if not company_elem:
                continue

            company = company_elem.get_text(" ", strip=True)
            if company:
                companies[company] = greenhouse_board_token(company)

        # Fallback: inspect structured JSON embedded in the page.
        # This is useful only if the response actually contains it.
        if not companies:
            log(
                "No company names found in search HTML. "
                "Inspect the response for embedded JSON or "
                "the actual search API used by the browser."
            )
            return matched

        log(f"Discovered {len(companies)} company names.")

        # Step 3: Fetch each candidate public job board.
        for company, token in companies.items():
            api_url = f"{GREENHOUSE_API_BASE}/{token}/jobs"

            try:
                board_response = session.get(
                    api_url,
                    params={"content": "true"},
                    timeout=15,
                )

                if board_response.status_code == 404:
                    log(
                        f"Board token not found for {company}: "
                        f"{token}"
                    )
                    continue

                board_response.raise_for_status()
                payload = board_response.json()
                jobs = payload.get("jobs", [])

                # Use the board's own name when available.
                board_name_response = session.get(
                    f"{GREENHOUSE_API_BASE}/{token}",
                    timeout=10,
                )

                board_company = company
                if board_name_response.ok:
                    board_company = (
                        board_name_response.json().get("name")
                        or company
                    )

                for job in jobs:
                    title = job.get("title", "")
                    location = (
                        job.get("location") or {}
                    ).get("name", "")

                    description = BeautifulSoup(
                        job.get("content", ""),
                        "html.parser",
                    ).get_text(" ", strip=True)

                    searchable_text = (
                        f"{title} {description}"
                    ).lower()

                    # Relevant engineering/software roles.
                    if not any(
                        keyword.lower() in searchable_text
                        for keyword in KEYWORDS
                    ):
                        continue

                    # Keep Bengaluru roles; optionally include
                    # India-remote jobs if their location says so.
                    location_lower = location.lower()
                    if not any(term in location_lower for term in [
                        "bengaluru",
                        "bangalore",
                        "india remote",
                        "remote - india",
                    ]):
                        continue

                    published = (
                        job.get("first_published")
                        or job.get("updated_at")
                    )

                    if not is_within_last_days(published, 5):
                        continue

                    job_url = job.get("absolute_url")
                    if not job_url:
                        continue

                    matched.append({
                        "id": job_url,
                        "title": title,
                        "company": board_company,
                        "url": job_url,
                        "source": "Greenhouse",
                    })

            except (requests.RequestException, ValueError) as exc:
                log(
                    f"Greenhouse board error "
                    f"[{company}/{token}]: {exc}"
                )

    except requests.RequestException as exc:
        log(f"MyGreenhouse search request failed: {exc}")

    log(f"Greenhouse matching jobs found: {len(matched)}")
    return matched




# ==============================================================================
# MAIN EXECUTOR & AGGREGATOR
# ==============================================================================
def fetch_and_notify():
    log("=== STARTING JOB FETCH ===")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("❌ CRITICAL ERROR: Secret variables are missing in GitHub repository settings!")
        return

    log("✅ GitHub Secrets loaded successfully.")

    seen_jobs = load_seen_jobs()
    log(f"Loaded {len(seen_jobs)} previously notified job IDs.")

    all_jobs = []
    #all_jobs.extend(fetch_himalayas())
    #all_jobs.extend(fetch_remotive())
    #all_jobs.extend(fetch_weworkremotely())
    # all_jobs.extend(fetch_arbeitnow())
    #all_jobs.extend(fetch_jobicy())
    #all_jobs.extend(fetch_hacker_news())
    all_jobs.extend(fetch_greenhouse())
    
    # LinkedIn Targeted Searches (Bengaluru & Remote)
    target_locations = ["Bengaluru", "Remote"]
    target_queries = [
        "Senior Backend Developer",
        "Lead Backend Engineer",
        "Full Stack Developer",
        "Full Stack Engineer",
        "Staff Backend Engineer",
        "Technical Consultant"
    ]

    for loc in target_locations:
        for query in target_queries:
            all_jobs.extend(fetch_linkedin(search_query=query, location=loc))

    # Filter out jobs that have already been sent in previous runs
    new_jobs = [j for j in all_jobs if j["id"] not in seen_jobs]
    log(f"\n--- Total Matches (<2 Days Old): {len(all_jobs)} | New Unseen Matches: {len(new_jobs)} ---")

    if not new_jobs:
        log("No new unseen jobs found in this run.")
        return

    # Dispatch alerts for new jobs only (up to 5 per run)
    for job in new_jobs[:15]:
        log(f"Sending NEW alert for: '{job['title']}' from [{job['source']}]")
        send_telegram_alert(job["title"], job["company"], job["url"], job["source"])
        seen_jobs.add(job["id"])

    save_seen_jobs(seen_jobs)
    log("=== JOB FETCH COMPLETE ===")


if __name__ == "__main__":
    fetch_and_notify()
