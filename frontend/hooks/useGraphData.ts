import { useState, useEffect, useCallback } from 'react';
import { fetchGraphData } from '../lib/services/graphService';
import type { GraphDataPoint } from '../models/Graph';

export const useGraphData = (startDate: Date, endDate: Date, machineId: string) => {
    const [data, setData] = useState<GraphDataPoint[]>([]);
    const [beams, setBeams] = useState<any[]>([]);
    const [geoChecks, setGeoChecks] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        if (!machineId) return;
        setLoading(true);
        try {
            const result = await fetchGraphData(startDate, endDate, machineId);
            setData(result.graphData);
            setBeams(result.beams);
            setGeoChecks(result.geoChecks);
            setError(null);
        } catch {
            setError('Failed to load graph data');
        } finally {
            setLoading(false);
        }
    }, [startDate, endDate, machineId]);

    useEffect(() => {
        load();
    }, [load]);

    return { data, beams, geoChecks, loading, error, refresh: load };
};
