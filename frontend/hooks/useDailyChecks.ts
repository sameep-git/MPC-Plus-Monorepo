import { useState, useEffect, useCallback } from 'react';
import { fetchBeams, fetchGeoChecks } from '../lib/api';
import { formatLocalYYYYMMDD } from '../lib/dateUtils';
import type { CheckGroup } from '../models/CheckGroup';

export const useDailyChecks = (date: Date, machineId: string) => {
    const [beams, setBeams] = useState<CheckGroup[]>([]);
    const [geoChecks, setGeoChecks] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        if (!machineId || !date) return;
        setLoading(true);
        try {
            const dateStr = formatLocalYYYYMMDD(date);
            
            // Use Promise.all for concurrent fetching, passing the specific exact date
            const [fetchedBeams, fetchedGeoChecks] = await Promise.all([
                fetchBeams({ machineId, date: dateStr }),
                fetchGeoChecks({ machineId, date: dateStr })
            ]);

            setBeams(fetchedBeams || []);
            setGeoChecks(fetchedGeoChecks || []);
            setError(null);
        } catch (err) {
            console.error('Failed to load daily checks:', err);
            setError('Failed to load daily checks');
        } finally {
            setLoading(false);
        }
    }, [date, machineId]);

    useEffect(() => {
        load();
    }, [load]);

    return {
        beams,
        geoChecks,
        loading,
        error,
        refresh: load
    };
};
