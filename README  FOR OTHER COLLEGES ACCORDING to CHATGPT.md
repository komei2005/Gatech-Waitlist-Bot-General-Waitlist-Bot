Awesome idea. Make the bot **pluggable** so you can drop in a “profile” for any school. Here’s a clean, minimal way to do it.

---

# 1) Make the bot configurable by school

## Add these new files

### `watcher/providers.py`

```python
# Simple provider interface + two implementations:
# - Ellucian Banner (most common in the US)
# - PeopleSoft (common too, but HTML varies; you’ll tweak selectors/regex)

import re
import requests
from bs4 import BeautifulSoup

class SectionStatus:
    def __init__(self, course_id, seats_remaining=None, wait_remaining=None, url=None):
        self.course_id = course_id
        self.seats_remaining = seats_remaining
        self.wait_remaining = wait_remaining
        self.url = url

# ---------------------------
# Ellucian Banner (public pages)
# ---------------------------
class BannerProvider:
    def __init__(self, base, detail_path, crn_param, term_param,
                 regex_seats, regex_wait):
        self.base = base.rstrip("/")
        self.detail_path = detail_path.lstrip("/")
        self.crn_param = crn_param
        self.term_param = term_param
        self.regex_seats = re.compile(regex_seats, re.I)
        self.regex_wait  = re.compile(regex_wait,  re.I)

    def _detail_url(self, course_id, term):
        # course_id = CRN for Banner
        return f"{self.base}/{self.detail_path}?{self.crn_param}={course_id}&{self.term_param}={term}"

    def get_status(self, course_id, term):
        url = self._detail_url(course_id, term)
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = " ".join(soup.stripped_strings)

        seats = None
        wait  = None

        m = self.regex_seats.search(text)
        if m:
            seats = int(m.group(1))

        w = self.regex_wait.search(text)
        if w:
            wait = int(w.group(1))

        return SectionStatus(course_id, seats, wait, url)

# ---------------------------
# PeopleSoft (public class search)
# ---------------------------
class PeopleSoftProvider:
    """
    PeopleSoft layouts differ by school. Most have a public
    "Class Search" result page where:
      - course_id = "Class Number" (like CRN)
      - term is passed as a numeric code
    You must set:
      base, detail_path, course_param, term_param, and regexes.

    Example params (you MUST inspect your school’s HTML):
      - regex_seats: r"Available Seats(?:\s*|\s*:\s*)(\d+)"
      - regex_wait : r"(?:Wait List|Waitlist) Seats(?:\s*|\s*:\s*)(\d+)"
    """
    def __init__(self, base, detail_path, course_param, term_param,
                 regex_seats, regex_wait):
        self.base = base.rstrip("/")
        self.detail_path = detail_path.lstrip("/")
        self.course_param = course_param
        self.term_param = term_param
        self.regex_seats = re.compile(regex_seats, re.I)
        self.regex_wait  = re.compile(regex_wait,  re.I)

    def _detail_url(self, course_id, term):
        return f"{self.base}/{self.detail_path}?{self.course_param}={course_id}&{self.term_param}={term}"

    def get_status(self, course_id, term):
        url = self._detail_url(course_id, term)
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = " ".join(soup.stripped_strings)

        seats = None
        wait  = None

        m = self.regex_seats.search(text)
        if m:
            seats = int(m.group(1))

        w = self.regex_wait.search(text)
        if w:
            wait = int(w.group(1))

        return SectionStatus(course_id, seats, wait, url)

def make_provider(system, **kwargs):
    system = (system or "").lower()
    if system == "banner":
        return BannerProvider(**kwargs)
    if system == "peoplesoft":
        return PeopleSoftProvider(**kwargs)
    raise ValueError(f"Unknown SYSTEM '{system}'")
```

### `watcher/config.py` (replace your old one)

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Common
SYSTEM = os.getenv("SYSTEM", "banner").strip()     # banner | peoplesoft
TERM   = os.getenv("TERM", "").strip()
COURSE_IDS = [c.strip() for c in os.getenv("COURSE_IDS", "").split(",") if c.strip()]  # CRNs for Banner, Class Numbers for PeopleSoft
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "10"))

# Provider-specific (with sensible defaults for Banner)
BASE_URL   = os.getenv("BASE_URL", "https://oscar.gatech.edu/bprod")
DETAIL_PATH= os.getenv("DETAIL_PATH", "bwckschd.p_disp_detail_sched")

# Param names
CRN_PARAM   = os.getenv("CRN_PARAM", "crn_in")        # Banner default
TERM_PARAM  = os.getenv("TERM_PARAM", "term_in")      # Banner default
COURSE_PARAM= os.getenv("COURSE_PARAM", CRN_PARAM)    # PeopleSoft may differ

# Regex (defaults for Banner’s common wording)
REGEX_SEATS = os.getenv("REGEX_SEATS", r"Seats:\s*Maximum:\s*\d+\s*Actual:\s*\d+\s*Remaining:\s*(\d+)")
REGEX_WAIT  = os.getenv("REGEX_WAIT",  r"Waitlist Seats:\s*Maximum:\s*\d+\s*Actual:\s*\d+\s*Remaining:\s*(\d+)")

# Notifications (optional)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "").strip()
EMAIL_SMTP_PORT = os.getenv("EMAIL_SMTP_PORT", "587").strip()
EMAIL_USERNAME  = os.getenv("EMAIL_USERNAME", "").strip()
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD", "").strip()
EMAIL_TO        = os.getenv("EMAIL_TO", "").strip()
```

### `watcher/main.py` (tiny change to use provider)

```python
import time
from datetime import datetime
from config import (
    SYSTEM, TERM, COURSE_IDS, POLL_SECONDS,
    BASE_URL, DETAIL_PATH, CRN_PARAM, TERM_PARAM, COURSE_PARAM,
    REGEX_SEATS, REGEX_WAIT,
    DISCORD_WEBHOOK_URL,
    EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO
)
from providers import make_provider
from notify import discord, email

def alert(msg: str):
    print(msg)
    discord(DISCORD_WEBHOOK_URL, msg)
    email(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO,
          subject="[Seat Watcher] Alert", body=msg)

def main():
    if not TERM or not COURSE_IDS:
        raise SystemExit("TERM and COURSE_IDS must be set in .env")

    provider = make_provider(
        SYSTEM,
        base=BASE_URL,
        detail_path=DETAIL_PATH,
        crn_param=CRN_PARAM,           # used by Banner
        term_param=TERM_PARAM,
        course_param=COURSE_PARAM,     # used by PeopleSoft
        regex_seats=REGEX_SEATS,
        regex_wait=REGEX_WAIT
    )

    print(f"[{datetime.now()}] SYSTEM={SYSTEM} TERM={TERM} watching {COURSE_IDS} every {POLL_SECONDS}s")
    while True:
        for cid in COURSE_IDS:
            try:
                s = provider.get_status(cid, TERM)
                if s.seats_remaining is not None and s.seats_remaining > 0:
                    alert(f"🟢 OPEN SEAT — {cid}: {s.seats_remaining} remaining\n{s.url}")
                elif s.wait_remaining is not None and s.wait_remaining > 0:
                    alert(f"🟡 OPEN WAITLIST — {cid}: {s.wait_remaining} remaining\n{s.url}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {cid}: no seats yet")
            except Exception as e:
                print(f"{cid}: error {e}")
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
```

> You can keep your existing `notify.py` and `requirements.txt` (requests, beautifulsoup4, python-dotenv).

---

# 2) One `.env` per school

Create a `.env` in the repo root for each school (or keep one and edit when you switch).

### Example A — **Any Banner school**

```env
# Which system?
SYSTEM=banner

# Term + course list (CRNs)
TERM=202602
COURSE_IDS=28693,93228

# Where to fetch
BASE_URL=https://oscar.gatech.edu/bprod
DETAIL_PATH=bwckschd.p_disp_detail_sched
CRN_PARAM=crn_in
TERM_PARAM=term_in

# How to parse (default Banner wording)
REGEX_SEATS=Seats:\s*Maximum:\s*\d+\s*Actual:\s*\d+\s*Remaining:\s*(\d+)
REGEX_WAIT=Waitlist Seats:\s*Maximum:\s*\d+\s*Actual:\s*\d+\s*Remaining:\s*(\d+)

# Polling
POLL_SECONDS=10
```

If another Banner school uses a slightly different label (e.g., “Seats Remaining: 3”), just change the regex:

```env
REGEX_SEATS=(?:Remaining Seats|Seats Remaining)\s*:\s*(\d+)
REGEX_WAIT=(?:Waitlist Remaining|Wait List Remaining)\s*:\s*(\d+)
```

### Example B — **A PeopleSoft school**

You must:

1. Open their **public class detail page** in a browser,
2. Note the **URL parameter names** (often `class_nbr` for “Class Number”, not “CRN”),
3. Copy **exact wording** around seats/waitlist and make regex.

```env
SYSTEM=peoplesoft

TERM=1252                      # your school’s numeric term code
COURSE_IDS=12345,67890         # PeopleSoft “Class Number”

BASE_URL=https://classes.yourschool.edu/psp/ps
DETAIL_PATH=public_detail_page  # the exact path you see
COURSE_PARAM=class_nbr
TERM_PARAM=term

# Tune these to the page text you see
REGEX_SEATS=Available Seats(?:\s*|\s*:\s*)(\d+)
REGEX_WAIT=(?:Wait List|Waitlist) Seats(?:\s*|\s*:\s*)(\d+)

POLL_SECONDS=15
```

> If the detail page doesn’t expose numbers plainly, switch to scraping the **list row** or use a different PeopleSoft endpoint that shows per-section availability without login (many schools have one).

---

# 3) How to “discover” what to put in `.env` for a new school

1. Google: “`<Your University>` class search schedule”
2. Click the **public** class search (no login).
3. Find a **detail page** for a specific section.
4. Copy:

   * Base URL up to the app root → `BASE_URL`
   * Path after the domain → `DETAIL_PATH`
   * Parameter name for class/CRN → `CRN_PARAM` or `COURSE_PARAM`
   * Parameter name for term → `TERM_PARAM`
   * The visible text around seats/waitlist → build `REGEX_SEATS` / `REGEX_WAIT`
5. Put a **known course id** and term into `COURSE_IDS`/`TERM` and test:

   ```bash
   python watcher/main.py
   ```

   If it prints numbers or “no seats yet” without errors, you’re good.

---

# 4) Quick-switch between schools

Keep multiple env files and swap:

```
.env.banner_gt
.env.banner_other
.env.peoplesoft_stateu
```

Activate one by copying:

```bash
cp .env.banner_other .env
python watcher/main.py
```

---

# 5) FAQ

**Q: My school uses Banner but “CRN” isn’t in the URL.**
A: Some pages accept search IDs differently. Use the **detail page** that has `crn_in=`. If not, search result pages often link to `p_disp_detail_sched` with CRN—copy that.

**Q: The page shows a table instead of “Seats: Maximum/Actual/Remaining.”**
A: No problem—regex doesn’t care about tables. Right-click → “View page source,” copy a few lines around the numbers, and adjust `REGEX_SEATS`/`REGEX_WAIT`.

**Q: PeopleSoft page is JS-heavy.**
A: Many schools still render numbers server-side. If yours doesn’t, look for an **alternate “classic” search** or an `?ICAction=` detail URL. Worst case, you can use the **list row** text (the HTML still contains the numbers).

---

If you tell me the **school name** and paste a sample **public class detail URL**, I’ll hand you a ready-made `.env` profile (regex included) that works out of the box.
