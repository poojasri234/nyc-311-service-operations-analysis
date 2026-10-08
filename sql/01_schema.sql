-- SQLite schema for the public NYC 311 API snapshot.
-- Raw API data is local-only; it is not committed or redistributed.
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
