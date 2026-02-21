
// Types for MLC data from geochecks_full view (JSON arrays)
export interface MlcLeafEntry { leafNumber: number; value: number; }
export interface MlcBacklashEntry { leafNumber: number; value: number; }

export interface GeoCheck {
    id: string;
    type: string;
    date: string; // ISO date
    machineId: string;
    path?: string;
    timestamp?: string; // ISO date-time

    // IsoCenter
    isoCenterSize?: number;
    isoCenterMVOffset?: number;
    isoCenterKVOffset?: number;

    // Beam
    relativeOutput?: number;
    relativeUniformity?: number;
    centerShift?: number;

    // Collimation & Gantry
    collimationRotationOffset?: number;
    gantryAbsolute?: number;
    gantryRelative?: number;

    // Couch
    couchLat?: number;
    couchLng?: number;
    couchVrt?: number;
    couchRtnFine?: number;
    couchRtnLarge?: number;
    couchMaxPositionError?: number;
    rotationInducedCouchShiftFullRange?: number;

    // MLC Offsets
    meanOffsetA?: number;
    meanOffsetB?: number;
    maxOffsetA?: number;
    maxOffsetB?: number;

    // MLC Backlash Aggregates
    mlcBacklashMaxA?: number;
    mlcBacklashMaxB?: number;
    mlcBacklashMeanA?: number;
    mlcBacklashMeanB?: number;

    // Jaws
    jawX1?: number;
    jawX2?: number;
    jawY1?: number;
    jawY2?: number;

    // Jaw Parallelism
    jawParallelismX1?: number;
    jawParallelismX2?: number;
    jawParallelismY1?: number;
    jawParallelismY2?: number;

    // Detailed MLC Data — can arrive as Record<string, number> from direct table
    // or as array of {leafNumber, value} objects from geochecks_full view
    mlcLeavesA?: Record<string, number> | MlcLeafEntry[] | null;
    mlcLeavesB?: Record<string, number> | MlcLeafEntry[] | null;
    mlcBacklashA?: Record<string, number> | MlcBacklashEntry[] | null;
    mlcBacklashB?: Record<string, number> | MlcBacklashEntry[] | null;

    // Metric Statuses
    metricStatuses?: Record<string, string>;

    note?: string;
    approvedBy?: string;
    approvedDate?: string;
    createdAt?: string;
    updatedAt?: string;
}

export default GeoCheck;
