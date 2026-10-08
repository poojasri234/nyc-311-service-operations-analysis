-- Quality-check summary for stakeholder review.
SELECT
  COUNT(*) AS raw_records,
  SUM(CASE WHEN row_quality_status = 'valid' THEN 1 ELSE 0 END) AS valid_records,
  ROUND(100.0 * SUM(CASE WHEN row_quality_status = 'valid' THEN 1 ELSE 0 END) / COUNT(*), 2) AS valid_row_rate_percent,
  SUM(CASE WHEN borough = 'Unknown' THEN 1 ELSE 0 END) AS missing_borough_after_normalization,
  SUM(CASE WHEN agency = 'Unknown' THEN 1 ELSE 0 END) AS missing_agency_after_normalization,
  SUM(CASE WHEN complaint_type = 'Unknown' THEN 1 ELSE 0 END) AS missing_complaint_type_after_normalization,
  SUM(CASE WHEN closed_at IS NULL THEN 1 ELSE 0 END) AS records_without_close_timestamp
FROM stg_311;

SELECT row_quality_status, COUNT(*) AS records
FROM stg_311
GROUP BY row_quality_status
ORDER BY records DESC;
