# Stakeholder memo: where to investigate resident wait time first

**Decision requested:** approve a small HEAT/HOT WATER request-lifecycle review before changing operations citywide.

## What we observed

This case study profiles **13,811** NYC 311 requests created on **2 January 2025**. Basic quality checks retained all records as valid unique requests. **13,700 (99.20%)** had a `closed_date`, allowing elapsed-time calculations.

- Overall median elapsed time: **10.52 hours**
- Overall P90 elapsed time: **332.87 hours**
- HEAT/HOT WATER: **1,704 requests**, **29.03-hour median**, **54.03-hour P90**
- Noise - Residential: **4,945 requests**, **5.45-hour median**
- Illegal Parking: **1,474 requests**, **1.71-hour median**

HEAT/HOT WATER is the recommended first pilot because, among complaint types with at least 1,000 requests and 500 timestamp-closed requests, it has the highest median elapsed time. This selection rule is visible in [`docs/data.json`](data.json) and the build script.

`Noise - Helicopter` is deliberately **not** treated as the first operational action: its 129 records are all assigned to EDC, its median is 3,333.48 hours, and its close dates cluster near 2025-05-21. That pattern is a signal to validate closure workflow and timestamp definitions with the data owner before using it as a resident-wait metric.

## Recommendation

Run a focused request-lifecycle review with the service owner:

1. Inspect a representative sample of HEAT/HOT WATER requests to confirm that `closed_date` corresponds to the operational event that matters for residents.
2. Map intake, assignment, escalation, and closure steps. Identify whether requests that pass 24 hours have a common queue, ownership, or documentation pattern.
3. Trial a daily exception view for open HEAT/HOT WATER requests above 24 hours, with an agreed owner and escalation path.
4. Compare the pilot period with a like-for-like baseline by borough and weekday. Track median elapsed hours, P90 elapsed hours, and missing-close-timestamp rate.

## How to judge the pilot

A useful improvement target must be agreed after the timestamp definition is validated. The evaluation should include:

| Measure | Why it matters |
|---|---|
| Median elapsed hours | Typical request timeliness |
| P90 elapsed hours | Long-tail experience |
| Share without a close timestamp | Metric reliability and completion visibility |
| Volume by borough and day | Mix changes that can distort a before/after comparison |
| Reopen, satisfaction, or follow-up rate (if available) | Guardrail against closing requests earlier without resolving the underlying issue |

## Value framing

For scale only, a **10% reduction** in the **53,929.88 recorded created-to-closed elapsed hours** across the **1,704** resolved HEAT/HOT WATER requests equals **5,392.99 recorded elapsed hours** in this one-day snapshot.

That figure is a calculation of elapsed request time:

```text
53,929.88 recorded elapsed hours × 10% = 5,392.99 recorded elapsed hours
```

It is **not** staff capacity, a budget saving, a realised result, or a causal forecast. A financial value would require cost, staffing, and outcome data absent from this public extract.

## Risks to resolve before action

- This is one intake date, not a long-run or seasonal baseline.
- 111 records did not have a close timestamp; source status and close timestamp can disagree.
- Long elapsed values may reflect source-system workflow or delayed administrative closure. They should not be translated directly into resident impact without service-owner review.
- The data does not contain staffing, field-dispatch, satisfaction, or causal-comparison information.
