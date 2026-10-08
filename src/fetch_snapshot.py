#!/usr/bin/env python3
"""Download the documented NYC Open Data snapshot used by this case study.

The resulting raw file stays local because the repository publishes only
aggregate outputs.  The official source remains NYC Open Data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


API_ENDPOINT = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
FIELDS = (
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "complaint_type",
    "descriptor",
    "borough",
    "status",
    "resolution_action_updated_date",
    "open_data_channel_type",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2025-01-02", help="YYYY-MM-DD")
    parser.add_argument(
        "--output", type=Path, default=Path("data/raw/nyc_311_2025-01-02.json")
    )
    args = parser.parse_args()

    next_date = str(date.fromisoformat(args.date) + timedelta(days=1))
    params = {
        "$select": ",".join(FIELDS),
        "$where": f"created_date >= '{args.date}T00:00:00' AND created_date < '{next_date}T00:00:00'",
        "$order": "unique_key ASC",
        "$limit": "50000",
    }
    url = API_ENDPOINT + "?" + urlencode(params)
    with urlopen(url, timeout=60) as response:
        payload = response.read()
    rows = json.loads(payload)
    if not isinstance(rows, list):
        raise ValueError("NYC Open Data response was not a JSON array")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(
        json.dumps(
            {
                "rows": len(rows),
                "output": str(args.output),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "source_url": url,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
