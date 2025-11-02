import re
import requests
from bs4 import BeautifulSoup

OSCAR_BASE = "https://oscar.gatech.edu/bprod"
DETAIL_PATH = "bwckschd.p_disp_detail_sched"

class SectionStatus:
    def __init__(self, crn, seats_remaining=None, wait_remaining=None, url=None):
        self.crn = crn
        self.seats_remaining = seats_remaining
        self.wait_remaining = wait_remaining
        self.url = url

def fetch_section_html(crn: str, term: str) -> str:
    url = f"{OSCAR_BASE}/{DETAIL_PATH}?crn_in={crn}&term_in={term}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text, url

def parse_remaining_from_detail(html: str):
    """
    Handles the common Banner patterns:
      - 'Seats: Maximum: X Actual: Y Remaining: Z'
      - 'Waitlist Seats: Maximum: A Actual: B Remaining: C'
    Falls back to looser regex on raw text if table layout changes.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try the robust table approach first
    text = " ".join(soup.stripped_strings)

    # Seats remaining
    seats_rem = None
    m = re.search(r"Seats:\s*Maximum:\s*\d+\s*Actual:\s*\d+\s*Remaining:\s*(\d+)", text, re.IGNORECASE)
    if m:
        seats_rem = int(m.group(1))
    else:
        # Loose fallback: "Remaining Seats: 3" or "Seats Remaining: 3"
        m2 = re.search(r"(remaining seats|seats remaining)\s*:\s*(\d+)", text, re.IGNORECASE)
        if m2:
            seats_rem = int(m2.group(2))

    # Waitlist remaining
    wait_rem = None
    w = re.search(r"Waitlist Seats:\s*Maximum:\s*\d+\s*Actual:\s*\d+\s*Remaining:\s*(\d+)", text, re.IGNORECASE)
    if w:
        wait_rem = int(w.group(1))
    else:
        w2 = re.search(r"(waitlist remaining|waitlist seats)\s*:\s*(\d+)", text, re.IGNORECASE)
        if w2:
            wait_rem = int(w2.group(2))

    return seats_rem, wait_rem

def get_status(crn: str, term: str) -> SectionStatus:
    html, url = fetch_section_html(crn, term)
    seats, wait = parse_remaining_from_detail(html)
    return SectionStatus(crn=crn, seats_remaining=seats, wait_remaining=wait, url=url)

