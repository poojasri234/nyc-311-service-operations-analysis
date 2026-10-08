# Data source and reproducibility

## Source

- **Dataset:** [NYC Open Data — 311 Service Requests from 2010 to Present](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/about_data)
- **Socrata API endpoint:** `https://data.cityofnewyork.us/resource/erm2-nwe9.json`
- **Dataset identifier:** `erm2-nwe9`
- **Project scope:** requests with `created_date` on 2025-01-02, using only the operational fields listed in [`data_dictionary.md`](data_dictionary.md).

The source is a live public dataset. It can change after an extract is taken, including corrections to historical rows.

## Why the raw snapshot is not committed

`data/raw/nyc_311_2025-01-02.json` is a local working input and is excluded by [`.gitignore`](../.gitignore). The repository instead includes:

- the exact field list and time filter;
- the transformation and validation code;
- the SQL used to inspect the local SQLite copy;
- aggregate-only JSON and CSV outputs;
- a SHA-256 fingerprint of the local source snapshot.

The published snapshot file was last written locally at **2026-10-08T06:27:29Z**. This is a local extract-file timestamp, not a claim about when the upstream source was last updated.

This keeps the repository small, avoids redistributing a mutable raw extract, and makes the original public dataset the source of record. The query intentionally excludes address, ZIP-code, coordinates, and incident-location fields.

## Exact extraction query

Run the following from the repository root to create a local snapshot:

```bash
mkdir -p data/raw

curl --fail --get "https://data.cityofnewyork.us/resource/erm2-nwe9.json" \
  --data-urlencode "\$select=unique_key,created_date,closed_date,agency,complaint_type,descriptor,borough,status,resolution_action_updated_date,open_data_channel_type" \
  --data-urlencode "\$where=created_date >= '2025-01-02T00:00:00.000' AND created_date < '2025-01-03T00:00:00.000'" \
  --data-urlencode "\$order=unique_key ASC" \
  --data-urlencode "\$limit=50000" \
  -o data/raw/nyc_311_2025-01-02.json
```

Then build the aggregate outputs:

```bash
python3 src/build_project.py \
  --input data/raw/nyc_311_2025-01-02.json \
  --out-dir outputs \
  --docs-dir docs \
  --excel-dir excel
```

The build uses Python's standard library and SQLite only. It creates a local SQLite database at `outputs/nyc_311_snapshot.sqlite`, which is also ignored by Git.

## Snapshot fingerprint

The local snapshot used for the published aggregate outputs had:

```text
Rows:    13,811
SHA-256: e92b487d84031dafb2ecfe56a483e3ab620204e93968074c40ed3655b256fb3a
Local snapshot file timestamp (UTC): 2026-10-08T06:27:29Z
```

Check a newly downloaded file with:

```bash
shasum -a 256 data/raw/nyc_311_2025-01-02.json
```

A different hash or row count is expected if the live source has been updated. Do not treat refreshed output as directly comparable without documenting the new extract time and hash.

## SQL review path

The build script creates the local `raw_311` table. Then create the staging views and run the checks:

```bash
sqlite3 outputs/nyc_311_snapshot.sqlite < sql/02_clean_and_validate.sql
sqlite3 -header -column outputs/nyc_311_snapshot.sqlite < sql/04_dq_checks.sql
sqlite3 -header -column outputs/nyc_311_snapshot.sqlite < sql/03_operational_analysis.sql
```

[`sql/01_schema.sql`](../sql/01_schema.sql) is a schema reference for a manual load. Do not run it after the build script unless you intend to recreate and reload `raw_311`, because it drops and recreates that table.
