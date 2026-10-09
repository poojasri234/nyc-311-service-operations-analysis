# NYC 311 Service Operations Analysis

[Open the live dashboard](https://poojasri234.github.io/nyc-311-service-operations-analysis/)

I analysed a one-day snapshot of NYC 311 requests to identify a practical starting point for investigating long resolution times. The project uses public operational data, publishes the cleaning rules and aggregate results, and keeps the raw API response local.

**Tools:** SQL (SQLite) · Python (standard library) · Excel-ready CSV · Power BI dashboard specification  
**Scope:** 13,811 requests created on **2 January 2025**. The repository includes the SQL, validation logic, aggregate outputs, documentation, and dashboard handoff.

## The question

Which high-volume request type should an operations team review first, and what evidence is needed before testing a change?

## Data and method

- Queried selected operational fields from the [official NYC 311 API](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/about_data) for requests created from `2025-01-02T00:00:00` up to, but not including, `2025-01-03T00:00:00`.
- Normalised blank text and checked request IDs and timestamps. A row was excluded only for a missing or duplicate request key, an invalid creation timestamp, or a close time before creation. All **13,811** source records passed those checks.
- Calculated request volume, close-timestamp coverage, median elapsed time, and 90th-percentile elapsed time by complaint type, agency, and borough.
- Limited the shortlist to complaint types with at least **1,000 requests** and **500 requests with a close timestamp**, then selected the category with the highest median elapsed time.
- Published aggregate-only output for the dashboard and Excel review. The raw snapshot stays out of Git; its SHA-256 is recorded in the data notes.

The main files are [`sql/`](sql/), [`src/build_project.py`](src/build_project.py), [`excel/311_operational_summary.csv`](excel/311_operational_summary.csv), and [`docs/data.json`](docs/data.json).

## What I found

| Measure | Result |
|---|---:|
| Requests profiled | 13,811 |
| Rows retained after validation | 13,811 (100.0%) |
| Requests with a close timestamp | 13,700 (99.20%) |
| Overall median elapsed time | 10.52 hours |
| Overall 90th percentile | 332.87 hours |
| Highest-volume complaint type | Noise - Residential: 4,945 requests; 5.45-hour median |
| Review candidate | HEAT/HOT WATER: 1,704 requests; 29.03-hour median; 54.03-hour P90 |

**HEAT/HOT WATER** is the strongest category to review first. It has enough requests for a useful pilot and the highest median elapsed time in the documented high-volume shortlist. Its 1,704 resolved requests add up to **53,929.88 recorded created-to-closed hours**.

One result needs extra care: `Noise - Helicopter` has a 3,333.48-hour median elapsed time, but all 129 records are assigned to EDC and their close dates cluster around 21 May 2025. That pattern could reflect a closure workflow or timestamp definition rather than a resident wait. I would validate it with the data owner before treating it as service performance.

## Recommended next step

Start with a small HEAT/HOT WATER request-lifecycle review:

1. Confirm with the service owner what `created_date`, `closed_date`, and `status` represent for a sample of these requests.
2. Map the routing and escalation path, then review requests still open after 24 hours each day.
3. Compare any pilot with a similar baseline by borough and day of week. Track median elapsed time, P90, and the percentage without a close timestamp.
4. Expand only after the metric definitions and pilot results have been checked.

### Sizing the opportunity

A 10% scenario against the **53,929.88 recorded elapsed hours** is:

```
53,929.88 × 10% = 5,392.99 recorded elapsed hours
```

This is a way to size the operational metric for this snapshot. It is not staff time saved, a financial estimate, or a prediction that a pilot will achieve the reduction.

## What this project cannot show

- One intake day is not enough to estimate seasonal or long-run service performance.
- The public dataset can change over time; the original local response is identified by SHA-256 for traceability.
- `closed_date` may represent different workflow events across agencies and complaint types.
- 111 requests had no `closed_date`, so they are not included in elapsed-time calculations.
- The extract has no staffing, cost, satisfaction, repeat-contact, or experimental data. It cannot show a causal service improvement or a monetary benefit.
- The repository intentionally publishes aggregates rather than case-level records.

## Repository guide

| Path | Purpose |
|---|---|
| [`data/`](data/) | Source, extract scope, field dictionary, and reproducibility notes |
| [`sql/`](sql/) | SQLite schema reference, cleaning/validation views, operational analysis, and data-quality checks |
| [`src/build_project.py`](src/build_project.py) | Standard-library build script that writes aggregate outputs from a local API snapshot |
| [`outputs/summary_metrics.json`](outputs/summary_metrics.json) | Aggregate metrics used in this README |
| [`excel/311_operational_summary.csv`](excel/311_operational_summary.csv) | Excel-ready summary by complaint type, agency, and borough |
| [`powerbi/`](powerbi/) | Dashboard specification and DAX measure definitions; no `.pbix` file is included |
| [`docs/`](docs/) | Aggregate JSON and stakeholder memo for the static dashboard |

## Re-run the project

[`data/README.md`](data/README.md) has the API request and build commands. Running the fetch command today will return the current public-source response; reproducing these exact outputs requires the original local snapshot identified there.
