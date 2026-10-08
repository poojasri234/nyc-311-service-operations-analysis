# NYC 311 Service Operations Analysis

[Open the live dashboard](https://poojasri234.github.io/nyc-311-service-operations-analysis/)

A reproducible service-operations case study using a messy public-government dataset: [NYC Open Data — 311 Service Requests from 2010 to Present](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/about_data).

**Tools:** SQL (SQLite) · Python (standard library) · Excel-ready CSV · Power BI dashboard specification
**Scope:** 13,811 requests created on **2025-01-02**. The raw API snapshot is intentionally kept local; this repository publishes the SQL, validation logic, aggregate outputs, documentation, and dashboard handoff.

## Business question

For a one-day intake of NYC 311 requests, which service category should an operations team investigate first to reduce resident waiting time, and what evidence is strong enough to support a small operational pilot?

The analysis measures elapsed time from `created_date` to `closed_date`, checks basic data quality before aggregation, and avoids treating a source-system status alone as proof of service completion.

## Approach

1. Queried the NYC Open Data API for selected operational fields for requests created from `2025-01-02T00:00:00` through (but excluding) `2025-01-03T00:00:00`.
2. Normalized blank text, tested identifiers and timestamps, and excluded only rows with a missing/duplicate request key, invalid creation timestamp, or close time before creation. All **13,811** source records passed those row-validity rules.
3. Calculated request volume, close-timestamp rate, median elapsed resolution time, and 90th-percentile elapsed time by complaint type, agency, and borough.
4. Chose a pilot watchlist using a documented rule: complaint types with at least **1,000 requests** and **500 requests with a close timestamp**, then the highest median elapsed time among those candidates.
5. Published aggregate-only output for a lightweight dashboard and Excel review. The SQL source and build script make the cleaning and metric definitions inspectable end to end.

See [`sql/`](sql/), [`src/build_project.py`](src/build_project.py), [`excel/311_operational_summary.csv`](excel/311_operational_summary.csv), and [`docs/data.json`](docs/data.json).

## Findings

| Measure | Result | What it means |
|---|---:|---|
| Requests profiled | 13,811 | One day of created requests in the selected API snapshot |
| Valid rows retained | 100.0% | No duplicate keys, missing keys, invalid creation timestamps, or close-before-create records were found |
| Requests with a close timestamp | 13,700 (99.20%) | 111 rows did not have `closed_date` and are excluded from elapsed-time calculations |
| Overall median elapsed time | 10.52 hours | A median is less distorted by long-tail closure values than an average |
| Overall 90th percentile | 332.87 hours | The long tail needs workflow validation before it is read as a direct measure of field-service delay |
| Highest-volume complaint type | Noise - Residential: 4,945 requests | Median elapsed time was 5.45 hours |
| Pilot watchlist | HEAT/HOT WATER: 1,704 requests | All 1,704 had a close timestamp; median elapsed time was 29.03 hours, P90 was 54.03 hours, and summed recorded elapsed time was 53,929.88 hours |

The high-volume watchlist is **HEAT/HOT WATER** because it has enough records to make a useful operational pilot and the highest median elapsed time among the documented high-volume candidates.

An important metric-definition signal is `Noise - Helicopter`: its 129 records are all assigned to EDC, have a 3,333.48-hour median elapsed time, and their close dates cluster near 2025-05-21. It should be investigated with the data owner as a closure-workflow or timestamp-definition issue, not reported as a direct measure of resident wait time. This is why the recommendation uses a transparent high-volume rule rather than simply selecting the largest extreme value.

## Recommendation

Start with a short, reviewed **HEAT/HOT WATER request-lifecycle pilot**:

1. Validate how `created_date`, `closed_date`, and `status` are populated for a sample of HEAT/HOT WATER requests with the service owner. Confirm whether `closed_date` represents the customer-relevant completion event.
2. Map the queue and escalation path for these requests. Add an operational exception list for requests still open after 24 hours, reviewed daily with the appropriate owner.
3. Compare the pilot with a like-for-like baseline by borough and day of week. Track median elapsed time, P90 elapsed time, and the share of requests without a close timestamp. Do not use a raw closure rate alone as the success metric.
4. If the metric definitions are confirmed, evaluate whether a broader rollout is warranted.

**Illustrative value framing, not a realised benefit:** applying a 10% reduction to the **sum of recorded created-to-closed elapsed time** for the 1,704 resolved HEAT/HOT WATER requests produces:

```
53,929.88 recorded elapsed hours × 10% = 5,392.99 recorded elapsed hours
```

This is an **illustrative reduction in recorded elapsed time** for this snapshot. It is not staff-hours saved, a monetary saving, a causal forecast, or evidence that the proposed pilot will achieve the change. A credible financial valuation would need staffing, service-cost, resident-impact, and causal-comparison data that are not in this extract.

## Limitations

- The analysis covers requests **created on one day** only. It is not a seasonal or long-run performance estimate.
- NYC Open Data is mutable. Re-running the same query later can return changed records, so the local raw snapshot's SHA-256 is documented for traceability.
- `closed_date` may represent a workflow event rather than a uniform service-completion definition across agencies and complaint types. This is why unusually large elapsed values need source-owner validation.
- 111 records had no `closed_date`. Closure timing and status timing do not fully agree, so elapsed-time metrics use the timestamp rather than status text.
- The selected fields do not contain staffing, dispatch, repeat-contact, satisfaction, cost, or causal-treatment data. The project cannot claim money saved or a causal service improvement.
- Aggregated outputs are intentionally published instead of the raw snapshot. They support portfolio review but not case-level investigation.

## 3-minute interview walkthrough

**0:00–0:30 — Context.**

“I wanted a public-service example with imperfect operational data rather than another clean dashboard. I used NYC 311 requests created on 2 January 2025 and asked which high-volume request type should be investigated first for resident wait time.”

**0:30–1:20 — Data and method.**

“I pulled selected operational fields from the official API, retained 13,811 valid unique requests, and calculated elapsed time only when `closed_date` was present and not before `created_date`. I used SQL views for text normalization and quality flags, and a Python build script to create aggregate outputs. I deliberately kept the raw snapshot out of Git and recorded its SHA-256.”

**1:20–2:10 — Findings.**

“99.2% of records had a close timestamp, but the P90 was 332.87 hours, so I avoided assuming every long duration was a service delay. HEAT/HOT WATER had 1,704 requests, a 29.03-hour median, and was the slowest category among types with at least 1,000 requests and 500 closed requests. That made it a more defensible pilot candidate than a tiny extreme category.”

**2:10–3:00 — Decision and what I would improve.**

“My recommendation is to validate closure semantics with the service owner, create a 24-hour exception review, and compare a small pilot against a like-for-like baseline. A 10% scenario over 53,929.88 recorded elapsed hours equals 5,392.99 illustrative elapsed hours, but I label it neither savings nor a forecast. Next, I would add multiple intake dates, agency-defined service targets, staffing data, and a comparison design before making any causal or financial claim.”

## Repository guide

| Path | Purpose |
|---|---|
| [`data/`](data/) | Source, extract scope, field dictionary, and reproducibility notes |
| [`sql/`](sql/) | SQLite schema reference, cleaning/validation views, operational analysis, and data-quality checks |
| [`src/build_project.py`](src/build_project.py) | Standard-library build script that writes aggregate outputs from a local API snapshot |
| [`outputs/summary_metrics.json`](outputs/summary_metrics.json) | Auditable aggregate metrics used in this README |
| [`excel/311_operational_summary.csv`](excel/311_operational_summary.csv) | Excel-ready summary by complaint type, agency, and borough |
| [`powerbi/`](powerbi/) | Dashboard specification and DAX measure definitions; no `.pbix` file is claimed or included |
| [`docs/`](docs/) | Aggregate JSON and stakeholder decision memo for the static dashboard |

## Reproduce

See [`data/README.md`](data/README.md) for the exact API request and build commands. The command fetches the current public-source response; exact results require the original local snapshot whose SHA-256 is recorded there.
