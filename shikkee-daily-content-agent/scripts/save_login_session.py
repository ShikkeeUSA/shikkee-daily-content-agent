#!/usr/bin/env python3
"""
One-time, interactive helper for persisting a logged-in browser session for
Reddit / Medium / a founder's LinkedIn+X, so the scheduled pipeline can later
check "am I still logged in?" without ever touching a password.

Usage:
    python scripts/save_login_session.py tal_reddit https://reddit.com/login
    python scripts/save_login_session.py shikkee_medium https://medium.com/m/signin
    python scripts/save_login_session.py tal_linkedin https://www.linkedin.com/login
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shikkee_agent.browser.playwright_session import save_login_session

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    save_login_session(account=sys.argv[1], start_url=sys.argv[2])
