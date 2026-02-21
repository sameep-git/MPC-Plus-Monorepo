import { fetchBeams, fetchGeoChecks } from '../../lib/api';
import { GRAPH_CONSTANTS } from '../../constants';
import type { GraphDataPoint } from '../../models/Graph';
import { createBeamSpecificMetricName, getMetricKey } from '../transformers/resultTransformers';

const DEFAULT_Y_AXIS_DOMAIN = GRAPH_CONSTANTS.Y_AXIS_DOMAINS.DEFAULT as [number, number];

/**
 * Gets the default Y-axis domain for a given metric.
 */
export const getDefaultDomainForMetric = (metricName: string): [number, number] => {
    const lowerMetric = metricName.toLowerCase();

    if (lowerMetric.includes('output change')) {
        return GRAPH_CONSTANTS.Y_AXIS_DOMAINS.OUTPUT_CHANGE as [number, number];
    }

    if (lowerMetric.includes('uniformity change')) {
        return GRAPH_CONSTANTS.Y_AXIS_DOMAINS.UNIFORMITY_CHANGE as [number, number];
    }

    if (lowerMetric.includes('center shift')) {
        return GRAPH_CONSTANTS.Y_AXIS_DOMAINS.CENTER_SHIFT as [number, number];
    }

    return DEFAULT_Y_AXIS_DOMAIN;
};

// Helper to format date for API input
const formatDateForInput = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

/**
 * Generates mock graph data or fallback structure when data is missing.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const generateGraphData = (startDate: Date, endDate: Date, _metrics: Set<string>): GraphDataPoint[] => {
    const data: GraphDataPoint[] = [];
    const currentDate = new Date(startDate);
    const end = new Date(endDate);

    const iterDate = new Date(currentDate);
    iterDate.setHours(0, 0, 0, 0);
    end.setHours(0, 0, 0, 0);

    while (iterDate <= end) {
        const isoDate = iterDate.toISOString().split('T')[0];
        const displayDate = iterDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

        const point: GraphDataPoint = {
            date: displayDate,
            fullDate: isoDate,
        };

        data.push(point);
        iterDate.setDate(iterDate.getDate() + 1);
    }
    return data;
};

/**
 * Fetches and aggregates graph data from backend APIs.
 */
export const fetchGraphData = async (startDate: Date, endDate: Date, machineId: string): Promise<{
    graphData: GraphDataPoint[];
    beams: any[]; // Using any[] temporarily, should be Beam[] but import might be circular or missing. 
    // Actually Beam and GeoCheck interfaces are likely in models.
    // I can import them if I view models. 
    // For now, I'll use explicit 'any[]' in signature to be safe or just infer it?
    // Better to return type-safe if possible.
    geoChecks: any[];
}> => {
    try {
        if (!machineId) return { graphData: [], beams: [], geoChecks: [] };

        const startStr = formatDateForInput(startDate);
        const endStr = formatDateForInput(endDate);

        const [groupedBeams, geoChecks] = await Promise.all([
            fetchBeams({ machineId, startDate: startStr, endDate: endStr }),
            fetchGeoChecks({ machineId, startDate: startStr, endDate: endStr })
        ]);

        // Flatten groups to beams for graph data
        const beams = groupedBeams.flatMap(g => g.beams);

        const data: GraphDataPoint[] = [];
        const currentDate = new Date(startDate);

        while (currentDate <= endDate) {
            const isoDate = currentDate.toISOString().split('T')[0];
            const displayDate = currentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            const dataPoint: GraphDataPoint = {
                date: displayDate,
                fullDate: isoDate,
            };

            // Map Beams - check both date and timestamp fields
            const dayBeams = beams.filter(b => {
                const dateMatch = b.date && b.date.startsWith(isoDate);
                const tsMatch = b.timestamp && b.timestamp.startsWith(isoDate);
                return dateMatch || tsMatch;
            });
            dayBeams.forEach(b => {
                if (b.type) {
                    const type = b.type;
                    if (b.relOutput !== undefined && b.relOutput !== null) {
                        const key = getMetricKey(createBeamSpecificMetricName('Relative Output', type));
                        dataPoint[key] = b.relOutput;
                    }
                    if (b.relUniformity !== undefined && b.relUniformity !== null) {
                        const key = getMetricKey(createBeamSpecificMetricName('Relative Uniformity', type));
                        dataPoint[key] = b.relUniformity;
                    }
                    if (b.centerShift !== undefined && b.centerShift !== null) {
                        const key = getMetricKey(createBeamSpecificMetricName('Center Shift', type));
                        dataPoint[key] = b.centerShift;
                    }
                }
            });

            // Map Geo Checks (assuming one per day)
            // Use timestamp first, fallback to date
            const dayGeo = geoChecks.find(g => {
                const dateMatch = g.date && g.date.startsWith(isoDate);
                const tsMatch = g.timestamp && g.timestamp.startsWith(isoDate);
                return dateMatch || tsMatch;
            });
            if (dayGeo) {
                // IsoCenter
                if (dayGeo.isoCenterSize !== undefined) dataPoint[getMetricKey('Iso Center Size')] = dayGeo.isoCenterSize;
                if (dayGeo.isoCenterMVOffset !== undefined) dataPoint[getMetricKey('Iso Center MV Offset')] = dayGeo.isoCenterMVOffset;
                if (dayGeo.isoCenterKVOffset !== undefined) dataPoint[getMetricKey('Iso Center KV Offset')] = dayGeo.isoCenterKVOffset;

                // Geo Beam Group (Generic)
                if (dayGeo.relativeOutput !== undefined) dataPoint[getMetricKey('Relative Output')] = dayGeo.relativeOutput;
                if (dayGeo.relativeUniformity !== undefined) dataPoint[getMetricKey('Relative Uniformity')] = dayGeo.relativeUniformity;
                if (dayGeo.centerShift !== undefined) dataPoint[getMetricKey('Center Shift')] = dayGeo.centerShift;

                // Collimation
                if (dayGeo.collimationRotationOffset !== undefined) dataPoint[getMetricKey('Collimation Rotation Offset')] = dayGeo.collimationRotationOffset;

                // Gantry
                if (dayGeo.gantryAbsolute !== undefined) dataPoint[getMetricKey('Gantry Absolute')] = dayGeo.gantryAbsolute;
                if (dayGeo.gantryRelative !== undefined) dataPoint[getMetricKey('Gantry Relative')] = dayGeo.gantryRelative;

                // Couch
                if (dayGeo.couchLat !== undefined) dataPoint[getMetricKey('Couch Lat')] = dayGeo.couchLat;
                if (dayGeo.couchLng !== undefined) dataPoint[getMetricKey('Couch Lng')] = dayGeo.couchLng;
                if (dayGeo.couchVrt !== undefined) dataPoint[getMetricKey('Couch Vrt')] = dayGeo.couchVrt;
                if (dayGeo.couchRtnFine !== undefined) dataPoint[getMetricKey('Couch Rtn Fine')] = dayGeo.couchRtnFine;
                if (dayGeo.couchRtnLarge !== undefined) dataPoint[getMetricKey('Couch Rtn Large')] = dayGeo.couchRtnLarge;
                if (dayGeo.couchMaxPositionError !== undefined) dataPoint[getMetricKey('Max Position Error')] = dayGeo.couchMaxPositionError;
                if (dayGeo.rotationInducedCouchShiftFullRange !== undefined) dataPoint[getMetricKey('Rotation Induced Shift')] = dayGeo.rotationInducedCouchShiftFullRange;

                // Jaws
                if (dayGeo.jawX1 !== undefined) dataPoint[getMetricKey('Jaw X1')] = dayGeo.jawX1;
                if (dayGeo.jawX2 !== undefined) dataPoint[getMetricKey('Jaw X2')] = dayGeo.jawX2;
                if (dayGeo.jawY1 !== undefined) dataPoint[getMetricKey('Jaw Y1')] = dayGeo.jawY1;
                if (dayGeo.jawY2 !== undefined) dataPoint[getMetricKey('Jaw Y2')] = dayGeo.jawY2;

                // Jaws Parallelism
                if (dayGeo.jawParallelismX1 !== undefined) dataPoint[getMetricKey('Parallelism X1')] = dayGeo.jawParallelismX1;
                if (dayGeo.jawParallelismX2 !== undefined) dataPoint[getMetricKey('Parallelism X2')] = dayGeo.jawParallelismX2;
                if (dayGeo.jawParallelismY1 !== undefined) dataPoint[getMetricKey('Parallelism Y1')] = dayGeo.jawParallelismY1;
                if (dayGeo.jawParallelismY2 !== undefined) dataPoint[getMetricKey('Parallelism Y2')] = dayGeo.jawParallelismY2;

                // MLC Offsets
                if (dayGeo.meanOffsetA !== undefined) dataPoint[getMetricKey('Mean Offset A')] = dayGeo.meanOffsetA;
                if (dayGeo.maxOffsetA !== undefined) dataPoint[getMetricKey('Max Offset A')] = dayGeo.maxOffsetA;
                if (dayGeo.meanOffsetB !== undefined) dataPoint[getMetricKey('Mean Offset B')] = dayGeo.meanOffsetB;
                if (dayGeo.maxOffsetB !== undefined) dataPoint[getMetricKey('Max Offset B')] = dayGeo.maxOffsetB;

                // Leaves - handle both Record<string, number> and [{leafNumber, value}] array format
                const normalizeMlc = (data: any): Record<string, number> | null => {
                    if (!data) return null;
                    if (Array.isArray(data)) {
                        const record: Record<string, number> = {};
                        data.forEach((entry: { leafNumber?: number; leaf_number?: number; value?: number; leaf_value?: number; backlash_value?: number }) => {
                            const key = String(entry.leafNumber ?? entry.leaf_number);
                            const val = entry.value ?? entry.leaf_value ?? entry.backlash_value;
                            if (val !== undefined) record[key] = val;
                        });
                        return Object.keys(record).length > 0 ? record : null;
                    }
                    return data;
                };

                const leavesA = normalizeMlc(dayGeo.mlcLeavesA);
                if (leavesA) {
                    Object.entries(leavesA).forEach(([key, val]) => {
                        dataPoint[getMetricKey(`MLC A Leaf ${key}`)] = val as number;
                    });
                }
                const leavesB = normalizeMlc(dayGeo.mlcLeavesB);
                if (leavesB) {
                    Object.entries(leavesB).forEach(([key, val]) => {
                        dataPoint[getMetricKey(`MLC B Leaf ${key}`)] = val as number;
                    });
                }
                const backlashA = normalizeMlc(dayGeo.mlcBacklashA);
                if (backlashA) {
                    Object.entries(backlashA).forEach(([key, val]) => {
                        dataPoint[getMetricKey(`Backlash A Leaf ${key}`)] = val as number;
                    });
                }
                const backlashB = normalizeMlc(dayGeo.mlcBacklashB);
                if (backlashB) {
                    Object.entries(backlashB).forEach(([key, val]) => {
                        dataPoint[getMetricKey(`Backlash B Leaf ${key}`)] = val as number;
                    });
                }
            }

            data.push(dataPoint);
            currentDate.setDate(currentDate.getDate() + 1);
        }

        return { graphData: data, beams: groupedBeams, geoChecks };
    } catch (err) {
        console.error('Failed to fetch graph data', err);
        return { graphData: [], beams: [], geoChecks: [] };
    }
};
