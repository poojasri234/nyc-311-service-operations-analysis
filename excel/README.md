# Excel-ready analysis handoff

[`311_operational_summary.csv`](311_operational_summary.csv) is a compact, aggregate-only output that opens directly in Excel.

## What the file contains

The file provides request counts and group-level elapsed-time metrics for three views:

- complaint type;
- agency;
- borough.

Use the `dimension` column as a report filter before comparing labels. For example, filter to `complaint_type` to compare HEAT/HOT WATER with Noise - Residential or Illegal Parking.

## Suggested Excel review

1. Open the CSV and format it as a table.
2. Insert a PivotTable with `label` in rows and `requests` in values, filtered to one `dimension`.
3. Add `median_resolution_hours`, `p90_resolution_hours`, and `total_elapsed_resolution_hours` as displayed source metrics for each category.
4. Create a bar chart for request volume and a second chart for group median elapsed hours.
5. Add a note from [`../data/data_dictionary.md`](../data/data_dictionary.md): group medians and P90s cannot be averaged to create an overall percentile.

## Important interpretation note

The CSV contains pre-aggregated metrics. It supports operational comparisons, but not row-level investigation or recalculation of the all-request median/P90. Those overall values are calculated from the local raw snapshot and documented in [`../outputs/summary_metrics.json`](../outputs/summary_metrics.json). `total_elapsed_resolution_hours` is the sum of recorded created-to-closed elapsed time for resolved records in a group; it is not staff time or a financial measure.

No `.xlsx` workbook is claimed or included. The CSV and documentation are the reproducible handoff.
