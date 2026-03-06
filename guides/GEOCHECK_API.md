# GeoCheck API Implementation

This document describes the GeoCheck (Geometry Check) API implementation for the MPC-Plus backend.

## Overview

The GeoCheck API provides endpoints for managing geometry check data from radiation therapy machines. Geometry checks include measurements for:
- **IsoCenterGroup**: ISO center size and offsets (MV/KV)
- **BeamGroup**: Relative output, uniformity, and center shift
- **CollimationGroup**: Collimation rotation offset
- **GantryGroup**: Gantry absolute and relative measurements
- **EnhancedCouchGroup**: Couch position errors and movements
- **MLCGroup**: Multi-Leaf Collimator (MLC) positions for 40 leaves (banks A & B)
- **MLCBacklashGroup**: MLC backlash measurements for 40 leaves (banks A & B)
- **JawsGroup**: Jaw positions (X1, X2, Y1, Y2)
- **JawsParallelismGroup**: Jaw parallelism measurements

## Architecture

The implementation follows the repository pattern used throughout the API:

```
Models/
  └── GeoCheck.cs              # Domain model
Repositories/
  ├── Abstractions/
  │   └── IGeoCheckRepository.cs    # Repository interface
  ├── Entities/
  │   └── GeoCheckEntity.cs         # Database entity with Supabase attributes
  └── Supabase/
      └── SupabaseGeoCheckRepository.cs  # Supabase implementation
Controllers/
  └── GeoCheckController.cs     # REST API endpoints
Extensions/
  └── ServiceCollectionExtensions.cs  # DI configuration
```

## API Endpoints

All endpoints are prefixed with `/api/geocheck`

### GET /api/geocheck
Get all geometry checks with optional filtering.

**Query Parameters:**
- `type` (string): Filter by beam type (e.g., "6xff")
- `machine-id` (string): Filter by machine ID
- `date` (string): Filter by specific date (YYYY-MM-DD)
- `start-date` (string): Filter by date range start
- `end-date` (string): Filter by date range end

**Response:** `200 OK`
```json
[
  {
    "id": "geo-001",
    "type": "6xff",
    "date": "2025-01-15",
    "machineId": "NDS-WKS-SN6543",
    "path": "/data/geochecks/...",
    "isoCenterSize": 0.5,
    "relativeOutput": 1.002,
    "mlcLeavesA": {
      "Leaf11": 0.1,
      "Leaf12": 0.15,
      ...
    },
    "mlcLeavesB": { ... },
    ...
  }
]
```

### GET /api/geocheck/{id}
Get a specific geometry check by ID.

**Response:** `200 OK` or `404 Not Found`

### POST /api/geocheck
Create a new geometry check.

**Request Body:**
```json
{
  "id": "geo-002",
  "type": "6xff",
  "date": "2025-01-15",
  "machineId": "NDS-WKS-SN6543",
  "relativeOutput": 1.001,
  "relativeUniformity": 0.998,
  "mlcLeavesA": {
    "Leaf11": 0.1,
    "Leaf12": 0.12,
    ...
  },
  ...
}
```

**Response:** `201 Created` with Location header

### PUT /api/geocheck/{id}
Update an existing geometry check.

**Response:** `204 No Content` or `404 Not Found`

### DELETE /api/geocheck/{id}
Delete a geometry check.

**Response:** `204 No Content` or `404 Not Found`

## Data Model

### GeoCheck Model Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| Id | string | Yes | Unique identifier |
| Type | string | Yes | Beam type (e.g., "6xff") |
| Date | DateOnly | Yes | Check date |
| MachineId | string | Yes | Associated machine ID |
| Path | string | No | File path to raw data |
| IsoCenterSize | double? | No | ISO center size |
| IsoCenterMVOffset | double? | No | MV offset |
| IsoCenterKVOffset | double? | No | KV offset |
| RelativeOutput | double? | No | Relative output |
| RelativeUniformity | double? | No | Relative uniformity |
| CenterShift | double? | No | Center shift |
| CollimationRotationOffset | double? | No | Collimation rotation |
| GantryAbsolute | double? | No | Gantry absolute position |
| GantryRelative | double? | No | Gantry relative position |
| CouchMaxPositionError | double? | No | Max couch position error |
| CouchLat | double? | No | Couch lateral position |
| CouchLng | double? | No | Couch longitudinal position |
| CouchVrt | double? | No | Couch vertical position |
| CouchRtnFine | double? | No | Fine couch rotation |
| CouchRtnLarge | double? | No | Large couch rotation |
| RotationInducedCouchShiftFullRange | double? | No | Rotation-induced shift |
| MLCLeavesA | Dictionary<string, double>? | No | MLC bank A positions (40 leaves) |
| MLCLeavesB | Dictionary<string, double>? | No | MLC bank B positions (40 leaves) |
| MaxOffsetA | double? | No | Max offset bank A |
| MaxOffsetB | double? | No | Max offset bank B |
| MeanOffsetA | double? | No | Mean offset bank A |
| MeanOffsetB | double? | No | Mean offset bank B |
| MLCBacklashA | Dictionary<string, double>? | No | MLC backlash bank A (40 leaves) |
| MLCBacklashB | Dictionary<string, double>? | No | MLC backlash bank B (40 leaves) |
| MLCBacklashMaxA | double? | No | Max backlash bank A |
| MLCBacklashMaxB | double? | No | Max backlash bank B |
| MLCBacklashMeanA | double? | No | Mean backlash bank A |
| MLCBacklashMeanB | double? | No | Mean backlash bank B |
| JawX1 | double? | No | Jaw X1 position |
| JawX2 | double? | No | Jaw X2 position |
| JawY1 | double? | No | Jaw Y1 position |
| JawY2 | double? | No | Jaw Y2 position |
| JawParallelismX1 | double? | No | Jaw X1 parallelism |
| JawParallelismX2 | double? | No | Jaw X2 parallelism |
| JawParallelismY1 | double? | No | Jaw Y1 parallelism |
| JawParallelismY2 | double? | No | Jaw Y2 parallelism |
| Note | string | No | Additional notes |

### MLC Leaves Structure

Both `MLCLeavesA/B` and `MLCBacklashA/B` use dictionaries with keys `"Leaf11"` through `"Leaf50"` (40 leaves total):

```json
{
  "Leaf11": 0.1,
  "Leaf12": 0.12,
  "Leaf13": 0.11,
  ...
  "Leaf50": 0.09
}
```

## Database Schema

The `geochecks` table uses JSONB columns for MLC leaf data to avoid column explosion (40 leaves × 4 groups = 160 potential columns).

### Table: geochecks

```sql
CREATE TABLE geochecks (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    machine_id VARCHAR(255) NOT NULL,
    path TEXT,
    
    -- IsoCenterGroup
    iso_center_size DOUBLE PRECISION,
    iso_center_mv_offset DOUBLE PRECISION,
    iso_center_kv_offset DOUBLE PRECISION,
    
    -- BeamGroup
    relative_output DOUBLE PRECISION,
    relative_uniformity DOUBLE PRECISION,
    center_shift DOUBLE PRECISION,
    
    -- CollimationGroup
    collimation_rotation_offset DOUBLE PRECISION,
    
    -- GantryGroup
    gantry_absolute DOUBLE PRECISION,
    gantry_relative DOUBLE PRECISION,
    
    -- EnhancedCouchGroup
    couch_max_position_error DOUBLE PRECISION,
    couch_lat DOUBLE PRECISION,
    couch_lng DOUBLE PRECISION,
    couch_vrt DOUBLE PRECISION,
    couch_rtn_fine DOUBLE PRECISION,
    couch_rtn_large DOUBLE PRECISION,
    rotation_induced_couch_shift_full_range DOUBLE PRECISION,
    
    -- MLCGroup (JSONB for 40 leaves each)
    mlc_leaves_a JSONB,
    mlc_leaves_b JSONB,
    max_offset_a DOUBLE PRECISION,
    max_offset_b DOUBLE PRECISION,
    mean_offset_a DOUBLE PRECISION,
    mean_offset_b DOUBLE PRECISION,
    
    -- MLCBacklashGroup (JSONB for 40 leaves each)
    mlc_backlash_a JSONB,
    mlc_backlash_b JSONB,
    mlc_backlash_max_a DOUBLE PRECISION,
    mlc_backlash_max_b DOUBLE PRECISION,
    mlc_backlash_mean_a DOUBLE PRECISION,
    mlc_backlash_mean_b DOUBLE PRECISION,
    
    -- JawsGroup
    jaw_x1 DOUBLE PRECISION,
    jaw_x2 DOUBLE PRECISION,
    jaw_y1 DOUBLE PRECISION,
    jaw_y2 DOUBLE PRECISION,
    
    -- JawsParallelismGroup
    jaw_parallelism_x1 DOUBLE PRECISION,
    jaw_parallelism_x2 DOUBLE PRECISION,
    jaw_parallelism_y1 DOUBLE PRECISION,
    jaw_parallelism_y2 DOUBLE PRECISION,
    
    note TEXT,
    
    CONSTRAINT fk_machine FOREIGN KEY (machine_id) 
        REFERENCES machines(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_geochecks_machine_id ON geochecks(machine_id);
CREATE INDEX idx_geochecks_date ON geochecks(date);
CREATE INDEX idx_geochecks_type ON geochecks(type);
CREATE INDEX idx_geochecks_machine_date ON geochecks(machine_id, date);
CREATE INDEX idx_geochecks_machine_type ON geochecks(machine_id, type);
```

## Configuration

The GeoCheck repository is registered in `Program.cs`:

```csharp
builder.Services.AddGeoCheckDataAccess(builder.Configuration);
```

This uses Supabase as the data store and requires valid Supabase credentials in the `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

## Implementation Details

### JSON Serialization for MLC Leaves

The entity uses JSON serialization to store MLC leaf dictionaries in the database:

```csharp
// In GeoCheckEntity.cs
[Column("mlc_leaves_a")]
public string? MLCLeavesAJson { get; set; }

private static Dictionary<string, double>? DeserializeLeaves(string? json)
{
    if (string.IsNullOrWhiteSpace(json))
        return null;
    return JsonSerializer.Deserialize<Dictionary<string, double>>(json);
}

private static string? SerializeLeaves(Dictionary<string, double>? leaves)
{
    if (leaves == null || leaves.Count == 0)
        return null;
    return JsonSerializer.Serialize(leaves);
}
```

### Error Handling

The controller includes comprehensive error handling:
- `400 Bad Request` for invalid date formats or mismatched IDs
- `404 Not Found` when geometry check doesn't exist
- `409 Conflict` for duplicate IDs
- `500 Internal Server Error` for unexpected errors

All errors are logged using `ILogger`.

### Filtering

The repository supports filtering by:
- Machine ID
- Beam type
- Specific date
- Date range (start/end dates)

Results are ordered by date (descending) and type.

## Testing

To test the GeoCheck endpoints:

```bash
# Get all geometry checks
curl http://localhost:5000/api/geocheck

# Get geometry checks for a specific machine
curl "http://localhost:5000/api/geocheck?machine-id=NDS-WKS-SN6543"

# Get geometry checks by type
curl "http://localhost:5000/api/geocheck?type=6xff"

# Get geometry check by ID
curl http://localhost:5000/api/geocheck/geo-001

# Create a new geometry check
curl -X POST http://localhost:5000/api/geocheck \
  -H "Content-Type: application/json" \
  -d '{
    "id": "geo-001",
    "type": "6xff",
    "date": "2025-01-15",
    "machineId": "NDS-WKS-SN6543",
    "relativeOutput": 1.002,
    "mlcLeavesA": {
      "Leaf11": 0.1,
      "Leaf12": 0.12
    }
  }'
```

## Integration with Python Pipeline

The Python data extraction pipeline (`Geo6xfffModel.py`) maps to this C# model. The `Uploader.py` should be updated to upload to the `geochecks` table:

```python
# In Uploader.py or data extraction
geo_check_data = {
    "id": f"geo-{timestamp}",
    "type": "6xff",
    "date": check_date,
    "machine_id": machine_id,
    "mlc_leaves_a": {f"Leaf{i}": value for i in range(11, 51)},
    "mlc_leaves_b": {f"Leaf{i}": value for i in range(11, 51)},
    # ... other fields
}

# Upload to Supabase
response = supabase.table("geochecks").insert(geo_check_data).execute()
```

## Future Enhancements

1. **Thresholds**: Add threshold checking for geometry measurements
2. **Alerts**: Notify when measurements exceed acceptable ranges
3. **Trending**: API endpoints for trending analysis over time
4. **Comparison**: Compare geometry checks across dates
5. **Validation**: Add stricter validation for MLC leaf ranges (11-50)
6. **Batch Operations**: Support bulk upload/update for multiple checks

## Related Documentation

- See `api.yaml` for OpenAPI specification
- See `Geo6xfffModel.py` for Python model structure
- See `create_geochecks_table.sql` for database migration
