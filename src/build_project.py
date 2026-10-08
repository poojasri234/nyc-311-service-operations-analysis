#!/usr/bin/env python3
"""Build aggregate-only outputs for the NYC 311 service-operations case study.

The raw API snapshot is intentionally ignored by Git. This script uses only the
Python standard library and SQLite so the cleaning, validation, and aggregation
logic can be reviewed end to end.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_FIELDS = (
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


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * p
    low, high = int(index), min(int(index) + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (index - low)


def clean_label(value: str | None, fallback: str = "Unknown") -> str:
    cleaned = (value or "").strip()
    return cleaned if cleaned else fallback


def round_or_none(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)


def write_sqlite(rows: list[dict], db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            DROP TABLE IF EXISTS raw_311;
            CREATE TABLE raw_311 (
              unique_key TEXT,
              created_date TEXT,
              closed_date TEXT,
              agency TEXT,
              complaint_type TEXT,
              descriptor TEXT,
              borough TEXT,
              status TEXT,
              resolution_action_updated_date TEXT,
              open_data_channel_type TEXT
            );
            """
        )
        conn.executemany(
            """
            INSERT INTO raw_311 VALUES (
              :unique_key, :created_date, :closed_date, :agency,
              :complaint_type, :descriptor, :borough, :status,
              :resolution_action_updated_date, :open_data_channel_type
            )
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    parser.add_argument("--excel-dir", type=Path, default=Path("excel"))
    args = parser.parse_args()

    raw_bytes = args.input.read_bytes()
    source_rows = json.loads(raw_bytes)
    if not isinstance(source_rows, list):
        raise ValueError("Expected a JSON array from the NYC Open Data API")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.docs_dir.mkdir(parents=True, exist_ok=True)
    args.excel_dir.mkdir(parents=True, exist_ok=True)

    normalized_raw = []
    cleaned = []
    seen = set()
    duplicate_keys = 0
    missing_key = 0
    invalid_created = 0
    invalid_chronology = 0
    missing_borough = 0
    missing_agency = 0
    missing_complaint = 0
    missing_closed = 0

    for row in source_rows:
        normalized = {field: (row.get(field) or "").strip() for field in EXPECTED_FIELDS}
        normalized_raw.append(normalized)
        key = normalized["unique_key"]
        if not key:
            missing_key += 1
            continue
        if key in seen:
            duplicate_keys += 1
            continue
        seen.add(key)

        created = parse_time(normalized["created_date"])
        closed = parse_time(normalized["closed_date"])
        if created is None:
            invalid_created += 1
            continue
        if closed is not None and closed < created:
            invalid_chronology += 1
            continue

        if not normalized["borough"]:
            missing_borough += 1
        if not normalized["agency"]:
            missing_agency += 1
        if not normalized["complaint_type"]:
            missing_complaint += 1
        if closed is None:
            missing_closed += 1

        resolution_hours = None
        if closed is not None:
            resolution_hours = (closed - created).total_seconds() / 3600

        cleaned.append(
            {
                "unique_key": key,
                "created_at": created.isoformat(),
                "closed_at": closed.isoformat() if closed else None,
                "agency": clean_label(normalized["agency"]),
                "complaint_type": clean_label(normalized["complaint_type"]),
                "descriptor": clean_label(normalized["descriptor"]),
                "borough": clean_label(normalized["borough"]),
                "status": clean_label(normalized["status"]),
                "channel": clean_label(normalized["open_data_channel_type"]),
                "resolution_hours": resolution_hours,
            }
        )

    if not cleaned:
        raise ValueError("No valid records after validation")

    # Create a local SQLite copy so the project has a concrete SQL path for review.
    write_sqlite(normalized_raw, args.out_dir / "nyc_311_snapshot.sqlite")

    by_complaint = defaultdict(list)
    by_agency = defaultdict(list)
    by_borough = defaultdict(list)
    status_counts = Counter()
    channel_counts = Counter()
    for row in cleaned:
        by_complaint[row["complaint_type"]].append(row)
        by_agency[row["agency"]].append(row)
        by_borough[row["borough"]].append(row)
        status_counts[row["status"]] += 1
        channel_counts[row["channel"]] += 1

    def summarize(grouped: dict[str, list[dict]], min_rows: int = 1) -> list[dict]:
        summary = []
        for label, records in grouped.items():
            resolved = [r["resolution_hours"] for r in records if r["resolution_hours"] is not None]
            if len(records) < min_rows:
                continue
            summary.append(
                {
                    "label": label,
                    "requests": len(records),
                    "resolved_requests": len(resolved),
                    "closure_rate_percent": round(len(resolved) / len(records) * 100, 2),
                    "total_elapsed_resolution_hours": round_or_none(sum(resolved)),
                    "median_resolution_hours": round_or_none(
                        statistics.median(resolved) if resolved else None
                    ),
                    "p90_resolution_hours": round_or_none(percentile(resolved, 0.90)),
                }
            )
        return summary

    complaint_summary = summarize(by_complaint)
    agency_summary = summarize(by_agency)
    borough_summary = summarize(by_borough)
    complaint_by_volume = sorted(complaint_summary, key=lambda x: (-x["requests"], x["label"]))
    agency_by_volume = sorted(agency_summary, key=lambda x: (-x["requests"], x["label"]))
    borough_by_volume = sorted(borough_summary, key=lambda x: (-x["requests"], x["label"]))

    # Only compare resolution times for categories with enough records and closures.
    comparable = [
        row for row in complaint_summary
        if row["requests"] >= 100 and row["resolved_requests"] >= 50 and row["median_resolution_hours"] is not None
    ]
    slowest_comparable = sorted(
        comparable, key=lambda x: (-x["median_resolution_hours"], -x["requests"])
    )[:10]

    all_resolved = [r["resolution_hours"] for r in cleaned if r["resolution_hours"] is not None]
    top_complaint = complaint_by_volume[0]
    # Prioritise a category with enough volume for an operational pilot.  The
    # anomaly list above is deliberately separate: an extreme elapsed time can
    # reflect a closure-workflow convention instead of a service delay.
    pilot_candidates = [
        row for row in complaint_summary
        if row["requests"] >= 1000
        and row["resolved_requests"] >= 500
        and row["median_resolution_hours"] is not None
    ]
    primary_watchlist = (
        max(pilot_candidates, key=lambda x: x["median_resolution_hours"])
        if pilot_candidates else top_complaint
    )
    ten_percent_elapsed_reduction = (
        primary_watchlist["total_elapsed_resolution_hours"] * 0.10
        if primary_watchlist["total_elapsed_resolution_hours"] is not None else None
    )

    dq = {
        "raw_records": len(source_rows),
        "retained_records": len(cleaned),
        "valid_row_rate_percent": round(len(cleaned) / len(source_rows) * 100, 2),
        "duplicate_unique_keys_removed": duplicate_keys,
        "records_missing_unique_key": missing_key,
        "records_with_invalid_created_timestamp": invalid_created,
        "records_with_invalid_close_before_create": invalid_chronology,
        "records_missing_borough": missing_borough,
        "records_missing_agency": missing_agency,
        "records_missing_complaint_type": missing_complaint,
        "records_missing_closed_date": missing_closed,
    }

    snapshot = {
        "project": "NYC 311 Service Operations Analysis",
        "source": {
            "name": "NYC Open Data — 311 Service Requests from 2010 to Present",
            "dataset_url": "https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/about_data",
            "api_endpoint": "https://data.cityofnewyork.us/resource/erm2-nwe9.json",
            "scope": "All records created on 2025-01-02, queried by created_date with selected operational fields.",
            "raw_snapshot_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "local_snapshot_file_timestamp_utc": datetime.fromtimestamp(
                args.input.stat().st_mtime, tz=timezone.utc
            ).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        },
        "metrics": {
            "records_profiled": len(cleaned),
            "valid_row_rate_percent": dq["valid_row_rate_percent"],
            "closed_requests": len(all_resolved),
            "closure_rate_percent": round(len(all_resolved) / len(cleaned) * 100, 2),
            "median_resolution_hours": round_or_none(statistics.median(all_resolved)),
            "p90_resolution_hours": round_or_none(percentile(all_resolved, 0.90)),
            "top_complaint_type": top_complaint,
            "watchlist_category": primary_watchlist,
        },
        "data_quality": dq,
        "recommendation_scenario": {
            "category": primary_watchlist["label"],
            "selection_rule": "Highest median elapsed resolution time among complaint types with at least 1,000 requests and 500 resolved requests in this snapshot.",
            "resolved_requests": primary_watchlist["resolved_requests"],
            "recorded_elapsed_hours": primary_watchlist["total_elapsed_resolution_hours"],
            "assumption": "A 10% reduction in the sum of recorded created-to-closed elapsed hours for resolved requests in the selected high-volume category.",
            "illustrative_elapsed_hours_reduced": round_or_none(ten_percent_elapsed_reduction),
            "interpretation": "Illustrative reduction in recorded elapsed time, not staff-hours saved, a realised service gain, or a causal forecast.",
        },
        "top_complaint_types": complaint_by_volume[:12],
        "slowest_comparable_complaint_types": slowest_comparable,
        "agency_summary": agency_by_volume[:12],
        "borough_summary": borough_by_volume,
        "status_summary": [{"label": key, "requests": value} for key, value in status_counts.most_common()],
        "channel_summary": [{"label": key, "requests": value} for key, value in channel_counts.most_common()],
    }

    (args.out_dir / "summary_metrics.json").write_text(json.dumps(snapshot, indent=2))
    (args.docs_dir / "data.json").write_text(json.dumps(snapshot, indent=2))

    with (args.excel_dir / "311_operational_summary.csv").open("w", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                "dimension",
                "label",
                "requests",
                "resolved_requests",
                "closure_rate_percent",
                "total_elapsed_resolution_hours",
                "median_resolution_hours",
                "p90_resolution_hours",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for dimension, rows in (("complaint_type", complaint_by_volume), ("agency", agency_by_volume), ("borough", borough_by_volume)):
            for row in rows:
                writer.writerow({"dimension": dimension, **row})

    print(json.dumps({"metrics": snapshot["metrics"], "data_quality": dq, "scenario": snapshot["recommendation_scenario"]}, indent=2))


if __name__ == "__main__":
    main()
