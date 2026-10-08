-- Stage text fields and document quality flags without silently deleting them.
DROP VIEW IF EXISTS stg_311;
CREATE VIEW stg_311 AS
WITH numbered AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY NULLIF(TRIM(unique_key), '') ORDER BY rowid) AS unique_key_row_number
  FROM raw_311
)
SELECT
  TRIM(unique_key) AS unique_key,
  datetime(created_date) AS created_at,
  datetime(closed_date) AS closed_at,
  COALESCE(NULLIF(TRIM(agency), ''), 'Unknown') AS agency,
  COALESCE(NULLIF(TRIM(complaint_type), ''), 'Unknown') AS complaint_type,
  COALESCE(NULLIF(TRIM(descriptor), ''), 'Unknown') AS descriptor,
  COALESCE(NULLIF(TRIM(borough), ''), 'Unknown') AS borough,
  COALESCE(NULLIF(TRIM(status), ''), 'Unknown') AS status,
  COALESCE(NULLIF(TRIM(open_data_channel_type), ''), 'Unknown') AS channel,
  CASE
    WHEN datetime(closed_date) IS NOT NULL
     AND datetime(created_date) IS NOT NULL
     AND julianday(closed_date) >= julianday(created_date)
    THEN (julianday(closed_date) - julianday(created_date)) * 24.0
  END AS resolution_hours,
  CASE
    WHEN NULLIF(TRIM(unique_key), '') IS NULL THEN 'missing_unique_key'
    WHEN unique_key_row_number > 1 THEN 'duplicate_unique_key'
    WHEN datetime(created_date) IS NULL THEN 'invalid_created_timestamp'
    WHEN datetime(closed_date) IS NOT NULL AND julianday(closed_date) < julianday(created_date) THEN 'close_before_create'
    ELSE 'valid'
  END AS row_quality_status
FROM numbered;

DROP VIEW IF EXISTS dq_exceptions;
CREATE VIEW dq_exceptions AS
SELECT * FROM stg_311 WHERE row_quality_status <> 'valid';
