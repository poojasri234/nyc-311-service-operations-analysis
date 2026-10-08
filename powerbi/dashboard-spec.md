# Dashboard specification

## Purpose

Help an operations stakeholder decide which service category merits a request-lifecycle review, while showing the data-quality and metric limitations that affect the decision.

## Page 1: Service operations overview

**Header**
- Title: `NYC 311 Service Operations Analysis`
- Scope text: `Requests created on 2025-01-02 | 13,811 records profiled | public-source snapshot`
- Source link to NYC Open Data

**KPI cards**
1. Requests profiled: **13,811**
2. Valid-row rate: **100.0%**
3. Requests with close timestamp: **99.20%**
4. Overall median elapsed time: **10.52 hours**
5. Overall P90 elapsed time: **332.87 hours**

**Core visuals**
- Horizontal bar chart: request volume by complaint type, top 12
- Scatter or matrix: complaint type by request volume and median elapsed hours
- Table: complaint type, requests, resolved requests, closure-rate percentage, group median, group P90
- Bar chart: agency request volume and median elapsed hours
- Bar chart: borough request volume and median elapsed hours

**Filters**
- `dimension`
- `label`
- Use the filters for comparison, not to recompute global percentiles from aggregates.

## Page 2: Pilot decision and quality checks

**Pilot card**
- Recommended category: **HEAT/HOT WATER**
- Selection rule: highest median elapsed time among categories with at least 1,000 requests and 500 requests with a close timestamp
- Snapshot metrics: **1,704** requests; **29.03** median hours; **54.03** P90 hours
- Action: validate timestamp semantics, map escalation path, and review 24-hour exceptions before a broader change

**Scenario card**
- Assumption: 10% reduction in the sum of recorded created-to-closed elapsed time
- Calculation: `53,929.88 × 10% = 5,392.99`
- Label: `Illustrative recorded elapsed-hours reduction`
- Required footnote: `Not staff-hours saved, a monetary saving, a realised benefit, or a causal forecast.`

**Data-quality panel**
- Duplicate IDs removed: 0
- Missing IDs: 0
- Invalid creation timestamps: 0
- Close-before-create errors: 0
- Missing close timestamps: 111
- Show the note that status and close timestamps should be reconciled with the data owner.

## Design guidance

- Use a neutral white background, charcoal text, and one restrained accent colour for the selected watchlist.
- Keep the group-level metric label visible: `median elapsed hours within selected group`.
- Avoid traffic-light colour as a proxy for public-service performance until service-level targets have been confirmed.
- Put the source, scope, extraction hash, and limitations in a footer or information panel.
