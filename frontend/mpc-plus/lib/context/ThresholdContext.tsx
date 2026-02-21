'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { fetchThresholds, Threshold } from '../api';

interface ThresholdContextType {
    thresholds: Threshold[];
    loading: boolean;
    error: string | null;
    getThreshold: (machineId: string, checkType: 'geometry' | 'beam', metricType: string, beamVariant?: string) => number | null;
    refreshThresholds: () => Promise<void>;
}

const ThresholdContext = createContext<ThresholdContextType | undefined>(undefined);

export function ThresholdProvider({ children }: { children: React.ReactNode }) {
    const [thresholds, setThresholds] = useState<Threshold[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Fetch once on mount
        const loadThresholds = async () => {
            try {
                const data = await fetchThresholds();
                setThresholds(data);
            } catch (err) {
                console.error('Failed to load thresholds', err);
                setError('Failed to load thresholds');
            } finally {
                setLoading(false);
            }
        };

        loadThresholds();
    }, []);

    const getThreshold = (
        machineId: string,
        checkType: 'geometry' | 'beam',
        metricType: string,
        beamVariant?: string
    ): number | null => {
        const normalizedMetric = metricType.toLowerCase();

        // 1. Try matching by beamVariantId (UUID) if the beamVariant looks like a UUID
        // or try string match on both beamVariantId and beamVariant
        let match = thresholds.find(t =>
            t.machineId === machineId &&
            t.checkType === checkType &&
            t.metricType.toLowerCase() === normalizedMetric &&
            (t.beamVariantId === beamVariant || t.beamVariant === beamVariant)
        );

        // 2. Fallback: geometry checks (no variant)
        if (!match && !beamVariant) {
            match = thresholds.find(t =>
                t.machineId === machineId &&
                t.checkType === checkType &&
                t.metricType.toLowerCase() === normalizedMetric
            );
        }

        return match ? match.value ?? null : null;
    };

    const refreshThresholds = async () => {
        setLoading(true);
        try {
            const data = await fetchThresholds();
            setThresholds(data);
            setError(null);
        } catch (err) {
            console.error('Failed to refresh thresholds', err);
            setError('Failed to refresh thresholds');
        } finally {
            setLoading(false);
        }
    };

    return (
        <ThresholdContext.Provider value={{ thresholds, loading, error, getThreshold, refreshThresholds }}>
            {children}
        </ThresholdContext.Provider>
    );
}

export function useThresholds() {
    const context = useContext(ThresholdContext);
    if (context === undefined) {
        throw new Error('useThresholds must be used within a ThresholdProvider');
    }
    return context;
}
