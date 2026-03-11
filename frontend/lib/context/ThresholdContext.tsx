'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { fetchThresholds, fetchBaselines, Threshold, Baseline } from '../api';

interface ThresholdContextType {
    thresholds: Threshold[];
    baselines: Baseline[];
    loading: boolean;
    error: string | null;
    getThreshold: (machineId: string, checkType: 'geometry' | 'beam', metricType: string, beamVariant?: string) => number | null;
    getBaseline: (machineId: string, checkType: string, metricType: string, beamVariant?: string) => Baseline | null;
    refreshThresholds: () => Promise<void>;
}

const ThresholdContext = createContext<ThresholdContextType | undefined>(undefined);

export function ThresholdProvider({ children }: { children: React.ReactNode }) {
    const [thresholds, setThresholds] = useState<Threshold[]>([]);
    const [baselines, setBaselines] = useState<Baseline[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Fetch once on mount
        const loadData = async () => {
            try {
                const [thresholdData, baselineData] = await Promise.all([
                    fetchThresholds(),
                    fetchBaselines().catch(() => [] as Baseline[]), // Gracefully handle if baselines endpoint isn't available
                ]);
                setThresholds(thresholdData);
                setBaselines(baselineData);
            } catch (err) {
                console.error('Failed to load thresholds', err);
                setError('Failed to load thresholds');
            } finally {
                setLoading(false);
            }
        };

        loadData();
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

    const getBaseline = (
        machineId: string,
        checkType: string,
        metricType: string,
        beamVariant?: string
    ): Baseline | null => {
        const normalizedMetric = metricType.toLowerCase();

        let match = baselines.find(b =>
            b.machineId === machineId &&
            b.checkType === checkType &&
            b.metricType.toLowerCase() === normalizedMetric &&
            (!beamVariant || b.beamVariant === beamVariant)
        );

        if (!match && !beamVariant) {
            match = baselines.find(b =>
                b.machineId === machineId &&
                b.checkType === checkType &&
                b.metricType.toLowerCase() === normalizedMetric
            );
        }

        return match ?? null;
    };

    const refreshThresholds = async () => {
        setLoading(true);
        try {
            const [thresholdData, baselineData] = await Promise.all([
                fetchThresholds(),
                fetchBaselines().catch(() => [] as Baseline[]),
            ]);
            setThresholds(thresholdData);
            setBaselines(baselineData);
            setError(null);
        } catch (err) {
            console.error('Failed to refresh thresholds', err);
            setError('Failed to refresh thresholds');
        } finally {
            setLoading(false);
        }
    };

    return (
        <ThresholdContext.Provider value={{ thresholds, baselines, loading, error, getThreshold, getBaseline, refreshThresholds }}>
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
