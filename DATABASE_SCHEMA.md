# Database Schema

This document outlines the database schema for **MPC Plus**, running on **PostgreSQL**.

## Tables

### `machines`
Stores linear accelerator definitions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `varchar` | No | - | Primary Key |
| `name` | `varchar` | Yes | - | Name of the machine |
| `location` | `varchar` | Yes | - | Physical location |
| `type` | `varchar` | Yes | - | Machine type |
| `created_at` | `timestamp` | Yes | `now()` | |
| `updated_at` | `timestamp` | Yes | `now()` | |

### `beam_variants`
Lookup table for different beam types/energies (e.g., "6X", "10X FFF").

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | No | `gen_random_uuid()` | Primary Key |
| `variant` | `text` | Yes | - | Unique beam variant name |

### `beams`
Stores daily beam check results.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | No | `gen_random_uuid()` | Primary Key |
| `machine_id` | `varchar` | Yes | - | FK to `machines.id` |
| `typeID` | `uuid` | Yes | - | FK to `beam_variants.id` |
| `type` | `text` | Yes | - | Legacy type string (use typeID) |
| `date` | `date` | Yes | - | Date of check |
| `timestamp` | `timestamptz` | Yes | - | Exact time of check |
| `rel_output` | `float4` | Yes | - | Relative output |
| `rel_uniformity` | `float4` | Yes | - | Relative uniformity |
| `center_shift` | `float4` | Yes | - | Center shift measurement |
| `hori_flatness` | `float4` | Yes | - | Horizontal flatness |
| `vert_flatness` | `float4` | Yes | - | Vertical flatness |
| `hori_symmetry` | `float4` | Yes | - | Horizontal symmetry |
| `vert_symmetry` | `float4` | Yes | - | Vertical symmetry |
| `path` | `text` | Yes | - | Unique file path |
| `approved_by` | `varchar` | Yes | - | User who approved the result |
| `approved_date` | `timestamp` | Yes | - | Approval timestamp |

### `geochecks`
Stores geometry check results (isocenter, couch, MLCs).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | No | `gen_random_uuid()` | Primary Key |
| `machine_id` | `text` | Yes | - | FK to `machines.id` (loose ref) |
| `beam_variant_id` | `uuid` | Yes | - | FK to `beam_variants.id` |
| `date` | `date` | Yes | - | Date of check |
| `timestamp` | `timestamptz` | Yes | `now()` | Exact time |
| `iso_center_size` | `numeric` | Yes | - | Isocenter size |
| `iso_center_mv_offset`| `numeric` | Yes | - | MV offset |
| `iso_center_kv_offset`| `numeric` | Yes | - | kV offset |
| `couch_lat` | `numeric` | Yes | - | Couch Lateral |
| `couch_lng` | `numeric` | Yes | - | Couch Longitudinal |
| `couch_vrt` | `numeric` | Yes | - | Couch Vertical |
| `approved_by` | `text` | Yes | - | User who approved |
| `approved_date` | `timestamptz` | Yes | - | Approval timestamp |

### `doc` (DocFactors)
Dose Output Correction factors for absolute output calculation.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | No | `gen_random_uuid()` | Primary Key |
| `machine_id` | `varchar` | Yes | - | FK to `machines.id` |
| `beam_variant_id` | `uuid` | Yes | - | FK to `beam_variants.id` |
| `beam_id` | `uuid` | Yes | - | FK to `beams.id` (reference measurement) |
| `doc_factor` | `numeric` | Yes | - | Calculated DOC factor |
| `msd_abs` | `numeric` | Yes | - | Measured Absolute Dose |
| `mpc_rel` | `numeric` | Yes | - | MPC Relative Output |
| `measurement_date` | `date` | Yes | - | Date of measurement |
| `start_date` | `date` | Yes | - | Effective start date |
| `end_date` | `date` | Yes | - | Effective end date (nullable) |

### `thresholds`
Configurable Pass/Fail thresholds.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | No | `gen_random_uuid()` | Primary Key |
| `machine_id` | `varchar` | Yes | - | FK to `machines.id` |
| `beam_variant_id` | `uuid` | Yes | - | FK to `beam_variants.id` |
| `check_type` | `varchar` | Yes | - | 'geometry' or 'beam' |
| `metric_type` | `varchar` | Yes | - | Specific metric name |
| `value` | `numeric` | Yes | - | Threshold value |

### `results`
Aggregated daily results.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | No | `gen_random_uuid()` | Primary Key |
| `machine_id` | `varchar` | Yes | - | FK to `machines.id` |
| `month` | `int4` | Yes | - | Month (1-12) |
| `year` | `int4` | Yes | - | Year |
| `status` | `varchar` | Yes | - | Overall status |
| `beam_check` | `jsonb` | Yes | - | JSON summary of checks |

### `updates`
System updates and notifications.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | No | `gen_random_uuid()` | Primary Key |
| `machine_id` | `varchar` | Yes | - | FK to `machines.id` |
| `info` | `text` | Yes | - | Update message |
| `type` | `varchar` | Yes | - | Update type |

### `baselines`
Baseline values for metrics.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | No | `gen_random_uuid()` | Primary Key |
| `machine_id` | `varchar` | Yes | - | FK to `machines.id` |
| `typeID` | `uuid` | Yes | - | FK to `beam_variants.id` |
| `metric_type` | `varchar` | Yes | - | Metric name |
| `value` | `numeric` | Yes | - | Baseline value |

### MLC Tables
Detailed MLC (Multi-Leaf Collimator) data linked to `geochecks`.
*   `geocheck_mlc_leaves_a`
*   `geocheck_mlc_leaves_b`
*   `geocheck_mlc_backlash_a`
*   `geocheck_mlc_backlash_b`

## Relationships

*   **Machines** are the central entity.
*   **Beams** and **GeoChecks** belong to a Machine and often linked to a **BeamVariant**.
*   **Thresholds** and **Baselines** are configured per Machine and BeamVariant.
*   **DocFactors** link a Machine and BeamVariant to a specific reference Beam.
