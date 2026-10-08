# Data dictionary

The project uses a selected subset of the NYC 311 API response. Text fields are trimmed during processing; blank agency, complaint, descriptor, borough, status, and channel values are shown as `Unknown` in the analytical layer. Missingness is still counted separately.

## Source fields

| Field | Type | Meaning | Project use |
|---|---|---|---|
| `unique_key` | Text identifier | NYC 311 request identifier | Uniqueness check and record key |
| `created_date` | Timestamp | Request creation timestamp | Start of elapsed-time calculation and scope filter |
| `closed_date` | Timestamp / nullable | Source-provided close timestamp | End of elapsed-time calculation; missing values are retained but excluded from time metrics |
| `agency` | Text | Responsible agency code | Agency-level operational summary |
| `complaint_type` | Text | High-level request category | Primary prioritisation dimension |
| `descriptor` | Text | More detailed request description | Retained for future diagnostic work; not used in published aggregate tables |
| `borough` | Text | Borough supplied by source | Borough-level operational summary |
| `status` | Text | Source workflow status | Context only; not used as the elapsed-time end event |
| `resolution_action_updated_date` | Timestamp / nullable | Latest source resolution-action update | Retained for audit; not used as the elapsed-time end event |
| `open_data_channel_type` | Text | Intake channel (for example, mobile or phone) | Channel mix summary |

## Derived fields and metrics

| Field / metric | Definition |
|---|---|
| `created_at` | Parsed ISO timestamp from `created_date` |
| `closed_at` | Parsed ISO timestamp from `closed_date`; null when the source value is blank or invalid |
| `resolution_hours` | `(closed_at − created_at)` in hours, only when both timestamps are valid and `closed_at >= created_at` |
| `row_quality_status` | `valid`, `missing_unique_key`, `duplicate_unique_key`, `invalid_created_timestamp`, or `close_before_create` |
| Valid row | A row with a populated, first-occurring `unique_key`, a parsable creation timestamp, and no close-before-create chronology error |
| Closed request for this analysis | A valid request with a non-null `closed_at`. This is a metric definition, not an assertion that the resident received a specific service outcome. |
| Closure-rate percentage | `requests with closed_at ÷ valid requests × 100` |
| Total recorded elapsed hours | Sum of non-null `resolution_hours` within a group; it is recorded timestamp duration, not staff time or a financial measure |
| Median resolution hours | The 50th percentile of non-null `resolution_hours` in a group |
| P90 resolution hours | The 90th percentile of non-null `resolution_hours` in a group, computed with linear interpolation in the build script |
| Pilot watchlist | Highest median elapsed time among complaint types with at least 1,000 total requests and 500 requests with a close timestamp |

## Validation rules

| Check | Treatment | Published result |
|---|---|---:|
| Missing `unique_key` | Excluded from valid-row metrics | 0 |
| Duplicate `unique_key` | Retain first occurrence; exclude later duplicates | 0 |
| Invalid `created_date` | Excluded from valid-row metrics | 0 |
| `closed_date` earlier than `created_date` | Excluded from valid-row metrics | 0 |
| Missing `closed_date` | Retained as a valid request but excluded from elapsed-time statistics | 111 |
| Blank descriptive field | Normalized to `Unknown`; missingness counted | 0 for agency, complaint type, and borough |
