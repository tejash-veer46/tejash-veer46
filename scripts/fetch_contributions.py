"""Fetch the public contribution calendar for a GitHub user (no token needed).

Usage: python scripts/fetch_contributions.py [username]
Writes data/contributions.json.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "tejash-veer46"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def parse_count(text):
    """'No contributions on ...' -> 0, '3 contributions on ...' -> 3."""
    m = re.match(r"\s*([\d,]+)\s+contribution", text or "")
    return int(m.group(1).replace(",", "")) if m else 0


def main():
    url = f"https://github.com/users/{USERNAME}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-art-bot"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip") if t.get("for")}

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        days.append({
            "date": date,
            "level": int(td.get("data-level", 0)),
            "count": parse_count(tips.get(td.get("id"), "")),
        })
    days.sort(key=lambda d: d["date"])
    if not days:
        sys.exit("no contribution cells found; GitHub markup may have changed")

    total = None
    h2 = soup.find(id="js-contribution-activity-description")
    if h2:
        m = re.search(r"([\d,]+)\s+contributions?", h2.get_text(" ", strip=True))
        if m:
            total = int(m.group(1).replace(",", ""))
    if total is None:
        total = sum(d["count"] for d in days)

    if OUT.exists():
        prev = json.loads(OUT.read_text())
        if prev.get("total") == total and prev.get("days") == days:
            print(f"{USERNAME}: unchanged ({total} contributions), leaving {OUT.name} as is")
            return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": total,
        "days": days,
    }, indent=1))
    print(f"{USERNAME}: {len(days)} days, {total} contributions -> {OUT}")


if __name__ == "__main__":
    main()
