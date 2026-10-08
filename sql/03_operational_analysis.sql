-- Aggregate operational view. Run after 01_schema.sql and 02_clean_and_validate.sql.
-- SQLite has no native median or percentile aggregate. This SQL file provides
-- inspectable volume, close-timestamp, mean, and rank views; the standard-
-- library Python build script calculates the dashboard's median and P90 values.
WITH valid_requests AS (
  SELECT *
  FROM stg_311
  WHERE row_quality_status = 'valid'
)
SELECT
  complaint_type,
  COUNT(*) AS requests,
  SUM(CASE WHEN closed_at IS NOT NULL THEN 1 ELSE 0 END) AS closed_requests,
  ROUND(100.0 * SUM(CASE WHEN closed_at IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS closure_rate_percent,
  ROUND(AVG(resolution_hours), 2) AS mean_resolution_hours
FROM valid_requests
GROUP BY complaint_type
ORDER BY requests DESC, complaint_type;

-- A window-function example: place each complaint type in a volume rank.
WITH complaint_summary AS (
  SELECT complaint_type, COUNT(*) AS requests
  FROM stg_311
  WHERE row_quality_status = 'valid'
  GROUP BY complaint_type
)
SELECT
  complaint_type,
  requests,
  RANK() OVER (ORDER BY requests DESC) AS request_volume_rank
FROM complaint_summary
ORDER BY request_volume_rank, complaint_type;
