import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { fetchBeams, fetchGeoChecks, handleApiError } from '../lib/api';
import { mapBeamsToResults, mapGeoCheckToResults } from '../lib/transformers/resultTransformers';
import type { CheckResult } from '../models/CheckResult';

export const useResultDetailData = () => {
    const router = useRouter();
    const searchParams = useSearchParams();

    // Initialize state from URL params
    const [selectedDate, setSelectedDate] = useState<Date>(() => {
        const dateParam = searchParams.get('date');
        if (dateParam) {
            const [y, m, d] = dateParam.split('-').map(Number);
            if (y && m && d) return new Date(y, m - 1, d);
        }
        // Fallback to current date if not specified
        return new Date();
    });

    const [machineId] = useState<string>(() => {
        // Priority: URL Param -> Session Storage (Legacy) -> Local Storage (Global)
        return searchParams.get('machineId') ||
            (typeof window !== 'undefined' ? sessionStorage.getItem('resultDetailMachineId') : null) ||
            (typeof window !== 'undefined' ? localStorage.getItem('selectedMachineId') : null) ||
            '';
    });

    const updateDate = (newDate: Date) => {
        setSelectedDate(newDate);
        // Update URL
        const dateStr = [
            newDate.getFullYear(),
            String(newDate.getMonth() + 1).padStart(2, '0'),
            String(newDate.getDate()).padStart(2, '0')
        ].join('-');

        // Use new URLSearchParams to merge
        const params = new URLSearchParams(searchParams);
        params.set('date', dateStr);

        router.push(`?${params.toString()}`);
    };

    return {
        selectedDate,
        updateDate,
    };
};
