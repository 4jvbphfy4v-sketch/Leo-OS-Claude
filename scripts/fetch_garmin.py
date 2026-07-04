#!/usr/bin/env python3
"""
fetch_garmin.py — extrage date din Garmin Connect si scrie data.json pentru Leo OS.

Rulat automat de GitHub Actions (.github/workflows/daily-sync.yml):
  - zilnic, prin cron
  - manual, cand apesi butonul "Sync acum" din index.html (via Cloudflare Worker -> workflow_dispatch)

Foloseste tokenstore (nu user/parola de fiecare data) ca sa evite MFA la fiecare rulare.
Vezi SETUP.md pentru cum generezi tokenstore-ul initial.
"""
import os
import sys
import json
import base64
import io
import tarfile
from datetime import date, timedelta
from pathlib import Path

from garminconnect import Garmin

TOKENSTORE_DIR = Path.home() / ".garminconnect"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data.json"


def restore_tokenstore():
    """Decodeaza tokenstore-ul salvat ca GitHub Secret (base64 tar.gz) inainte de login."""
    b64 = os.environ.get("GARMIN_TOKENSTORE_B64")
    if not b64:
        print("[info] Nu exista GARMIN_TOKENSTORE_B64, incerc login cu user/parola.", file=sys.stderr)
        return
    TOKENSTORE_DIR.mkdir(parents=True, exist_ok=True)
    raw = base64.b64decode(b64)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
        tar.extractall(TOKENSTORE_DIR)


def login() -> Garmin:
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    restore_tokenstore()

    client = Garmin(email=email, password=password)
    client.login(str(TOKENSTORE_DIR))
    return client


def safe(fn, *args, **kwargs):
    """Nu lasa un singur endpoint picat (ex. HRV lipsa azi) sa opreasca tot scriptul."""
    name = getattr(fn, "__name__", str(fn))
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"[warn] {name} a esuat: {e}", file=sys.stderr)
        return None


def main():
    client = login()

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    data = {
        "generated_at_utc": f"{date.today().isoformat()}",
        "date": today,
        "activities": safe(client.get_activities, 0, 10),
        "hrv": safe(client.get_hrv_data, today),
        "sleep": safe(client.get_sleep_data, today),
        "training_readiness": safe(client.get_training_readiness, today),
        "body_battery": safe(client.get_body_battery, yesterday, today),
        "resting_hr": safe(client.get_rhr_day, today),
        "stats": safe(client.get_stats, today),
        "max_metrics": safe(client.get_max_metrics, today),  # VO2max e aici
    }

    OUTPUT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    print(f"OK -> scris {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
