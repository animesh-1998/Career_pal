import json
import re
import html

def format_tool_result(tool_name: str, content) -> str:
    """Format tool results into clean readable text for the frontend"""
    
    # extract raw text from list format
    if isinstance(content, list):
        raw = " ".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )
    else:
        raw = str(content) if content else ""

    if not raw.strip():
        return ""

    # route to specific formatter based on tool name
    formatters = {
        "search_emails":    format_search_emails,
        "read_email":       format_read_email,
        "send_email":       format_send_email,
        "draft_email":      format_draft_email,
        "delete_email":     format_delete_email,
        "search_jobs":      format_search_jobs,
        "get_job_details":  format_job_details,
    }

    formatter = formatters.get(tool_name)
    if formatter:
        try:
            return formatter(raw)
        except Exception:
            pass  # fall through to default

    # default — return raw text cleaned up
    return raw.strip()


# ── Email formatters ──────────────────────────────────────

def format_search_emails(raw: str) -> str:
    lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
    emails = []
    current = {}

    for line in lines:
        if line.startswith("ID:"):
            if current:
                emails.append(current)
            current = {"id": line.replace("ID:", "").strip()}
        elif line.startswith("Subject:"):
            current["subject"] = line.replace("Subject:", "").strip()
        elif line.startswith("From:"):
            current["from"] = line.replace("From:", "").strip()
        elif line.startswith("Date:"):
            current["date"] = line.replace("Date:", "").strip()

    if current:
        emails.append(current)

    if not emails:
        return raw

    result = f"📬 Found {len(emails)} email{'s' if len(emails) > 1 else ''}:\n\n"
    for i, email in enumerate(emails, 1):
        result += f"**{i}. {email.get('subject', 'No Subject')}**\n"
        result += f"   From: {email.get('from', 'Unknown')}\n"
        result += f"   Date: {email.get('date', '')}\n"
        result += f"   ID: `{email.get('id', '')}`\n\n"

    return result.strip()


def strip_html(raw: str) -> str:
    """Convert HTML email body to clean plain text"""

    # decode HTML entities FIRST — &#8199; → space, &amp; → & etc.
    text = html.unescape(raw)

    # remove style and script blocks entirely
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)

    # convert block tags to newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</tr>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</td>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>', '• ', text, flags=re.IGNORECASE)

    # remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # remove invisible unicode spacer characters used in marketing emails
    text = re.sub(r'[\u0020\u00a0\u034f\u061c\u115f\u1160\u17b4\u17b5'
                  r'\u180e\u2000-\u200f\u202f\u205f\u2060-\u2064'
                  r'\u206a-\u206f\u3000\ufeff\uffa0]+', ' ', text)

    # collapse multiple spaces and blank lines
    text = re.sub(r' {3,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # remove lines that are just whitespace or single chars
    lines = [l for l in text.split('\n') if len(l.strip()) > 2]

    return '\n'.join(lines).strip()


def format_read_email(raw: str) -> str:
    lines = raw.strip().split("\n")
    headers = {}
    body_start_idx = 0

    for i, line in enumerate(lines):
        if line.startswith("Thread ID:"):
            pass  # skip thread id
        elif line.startswith("Subject:"):
            headers["subject"] = line.replace("Subject:", "").strip()
        elif line.startswith("From:"):
            headers["from"] = line.replace("From:", "").strip()
        elif line.startswith("To:"):
            headers["to"] = line.replace("To:", "").strip()
        elif line.startswith("Date:"):
            headers["date"] = line.replace("Date:", "").strip()
        elif line.strip() == "" and headers:
            body_start_idx = i + 1
            break

    body = "\n".join(lines[body_start_idx:]).strip()

    # strip the HTML note if present
    body = re.sub(r'\[Note:.*?\]\n*', '', body).strip()

    # convert HTML to plain text if body contains HTML
    if "<html" in body.lower() or "<div" in body.lower() or "<p" in body.lower():
        body = strip_html(body)

    # truncate very long emails
    if len(body) > 10000:
        body = body[:10000] + "\n\n...[truncated]"

    result = f"📧 **{headers.get('subject', 'Email')}**\n\n"
    if headers.get("from"):
        result += f"**From:** {headers['from']}\n"
    if headers.get("to"):
        result += f"**To:** {headers['to']}\n"
    if headers.get("date"):
        result += f"**Date:** {headers['date']}\n"
    if body:
        result += f"\n---\n{body}"

    print(f"Formatted email content:\n{result}")  # Debug: print formatted email
    return result.strip()


def format_send_email(raw: str) -> str:
    if "successfully" in raw.lower():
        return "✅ Email sent successfully!"
    return raw


def format_draft_email(raw: str) -> str:
    if "successfully" in raw.lower():
        return "✅ Email draft saved successfully!"
    return raw


def format_delete_email(raw: str) -> str:
    if "successfully" in raw.lower():
        return "🗑️ Email deleted successfully."
    return raw


# ── Job formatters ────────────────────────────────────────

def format_search_jobs(raw: str) -> str:
    try:
        data = json.loads(raw)
        text = data.get("sections", {}).get("search_results", raw)
    except json.JSONDecodeError:
        text = raw

    jobs = parse_linkedin_jobs(text)

    if not jobs:
        return f"💼 **Jobs Found:**\n\n{text[:500]}"

    result = f"💼 **Found {len(jobs)} Jobs:**\n\n"
    for i, job in enumerate(jobs, 1):
        result += f"---\n"
        result += f"**{i}. {job['title']}**\n"
        result += f"🏢 {job['company']}\n"
        result += f"📍 {job['location']}\n"
        if job.get('meta'):
            result += f"ℹ️ {job['meta']}\n"
        result += "\n"

    return result.strip()


def parse_linkedin_jobs(text: str) -> list:
    """Parse raw LinkedIn job text into structured job objects"""

    # noise to remove
    NOISE = [
        "Set alert", "Set job alert", "Jump to active job details",
        "Jump to active search result", "Are these results helpful",
        "Are you finding what", "Job search faster", "Try Premium",
        "1-month free trial", "Promoted by hirer", "Easy Apply",
        "Save", "Show more options", "Assessing your job match",
        "About the job", "About the company", "show more", "Show more",
        "Follow", "Message", "Share", "Next", "Back",
        "Matches your job preferences", "Be an early applicant",
        "with verification", "No response insights available yet",
        "followers", "employees", "on LinkedIn",
    ]

    LOCATION_KEYWORDS = [
        "India", "Hybrid", "On-site", "Remote", "Delhi", "Mumbai",
        "Bengaluru", "Bangalore", "Hyderabad", "Chennai", "Pune",
        "Kolkata", "Noida", "Gurugram", "Greater"
    ]

    SKIP_PATTERNS = [
        r"^\d+$",                          # just a number
        r"^\d+,\d+\+ results$",            # "6,000+ results"
        r".*\d+ day[s]? ago.*",            # "1 day ago"
        r".*applicants.*",                  # "100+ applicants"
        r".*\d+ company alum.*",            # "1 company alum"
        r".*IT Services.*",                 # company description
        r".*next-generation.*",
        r".*committed to building.*",
        r".*event-driven.*",
        r"^\d+$",
    ]

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # clean lines
    cleaned = []
    for line in lines:
        if any(noise in line for noise in NOISE):
            continue
        if any(re.match(p, line, re.IGNORECASE) for p in SKIP_PATTERNS):
            continue
        cleaned.append(line)

    # parse jobs — pattern: title, company, location repeat
    jobs = []
    i = 0
    while i < len(cleaned):
        line = cleaned[i]

        # skip header lines like "AI engineering in India"
        if any(k in line for k in ["results", "in India", "engineering in"]):
            i += 1
            continue

        # check if next line is a company (not a location)
        if i + 1 < len(cleaned):
            next_line = cleaned[i + 1]
            after_next = cleaned[i + 2] if i + 2 < len(cleaned) else ""

            is_location = any(k in after_next for k in LOCATION_KEYWORDS)
            is_company = not any(k in next_line for k in LOCATION_KEYWORDS)

            if is_company and is_location:
                job = {
                    "title":    line,
                    "company":  next_line,
                    "location": after_next,
                    "meta":     ""
                }

                # grab extra meta if available (Full-time, On-site etc)
                meta_parts = []
                j = i + 3
                while j < len(cleaned) and j < i + 6:
                    m = cleaned[j]
                    if any(k in m for k in ["Full-time", "Part-time", "Contract", "On-site", "Remote", "Hybrid"]):
                        meta_parts.append(m)
                        j += 1
                    else:
                        break
                if meta_parts:
                    job["meta"] = " · ".join(meta_parts)

                # avoid duplicates
                if not any(
                    j["title"] == job["title"] and j["company"] == job["company"]
                    for j in jobs
                ):
                    jobs.append(job)

                i += 3
                continue

        i += 1

    return jobs


def format_job_details(raw: str) -> str:
    return f"📋 **Job Details:**\n\n{raw}"