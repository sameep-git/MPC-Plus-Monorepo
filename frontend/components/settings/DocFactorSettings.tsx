'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, Trash2, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { DatePicker } from '../ui/date-picker';
import {
    fetchDocFactors,
    createDocFactor,
    deleteDocFactor,
    fetchBeamChecksForDate,
    fetchBeamVariantsWithIds,
    fetchMachines,
    type DocFactor,
    type BeamCheckOption,
    type BeamVariantWithId,
} from '../../lib/api';
import type { Machine } from '../../models/Machine';

// MSD Abs boundary constants
const MSD_ABS_MIN = 0.97;
const MSD_ABS_MAX = 1.03;

interface BeamEntry {
    beamCheck: BeamCheckOption | null; // The currently selected check
    allChecks: BeamCheckOption[];     // All checks available for this variant/date
    selectedCheckId: string | null;   // ID of the selected check
    msdAbs: string;
    loading: boolean;
}

export default function DocFactorSettings() {
    // Machine state
    const [machines, setMachines] = useState<Machine[]>([]);
    const [selectedMachineId, setSelectedMachineId] = useState<string>('');
    const [loadingMachines, setLoadingMachines] = useState(true);

    // Data states
    const [docFactors, setDocFactors] = useState<DocFactor[]>([]);
    const [beamVariants, setBeamVariants] = useState<BeamVariantWithId[]>([]);

    // UI states
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [saving, setSaving] = useState(false);

    // Modal form states
    const [measurementDate, setMeasurementDate] = useState<Date | undefined>(undefined);
    const [startDate, setStartDate] = useState<Date | undefined>(undefined);
    const [beamEntries, setBeamEntries] = useState<Record<string, BeamEntry>>({});
    const [loadingAllBeams, setLoadingAllBeams] = useState(false);

    const selectedMachineName = machines.find(m => m.id === selectedMachineId)?.name;

    // Load machines on mount
    useEffect(() => {
        const loadMachines = async () => {
            try {
                setLoadingMachines(true);
                const machinesData = await fetchMachines();
                setMachines(machinesData);
                if (machinesData.length > 0) {
                    setSelectedMachineId(machinesData[0].id);
                }
            } catch (err) {
                console.error('Failed to load machines:', err);
                setError('Failed to load machines');
            } finally {
                setLoadingMachines(false);
            }
        };
        loadMachines();
    }, []);

    // Load DOC factors when machine changes
    const loadDocFactors = useCallback(async () => {
        if (!selectedMachineId) return;
        try {
            setLoading(true);
            setError(null);
            const data = await fetchDocFactors(selectedMachineId);
            setDocFactors(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load DOC factors');
        } finally {
            setLoading(false);
        }
    }, [selectedMachineId]);

    // Load beam variants on mount
    useEffect(() => {
        const loadBeamVariants = async () => {
            try {
                const variants = await fetchBeamVariantsWithIds();
                setBeamVariants(variants);
            } catch (err) {
                console.error('Failed to load beam variants:', err);
            }
        };
        loadBeamVariants();
    }, []);

    // Load DOC factors when machine changes
    useEffect(() => {
        loadDocFactors();
    }, [loadDocFactors]);

    // Fetch beam checks for ALL variants when measurement date changes
    useEffect(() => {
        const loadAllBeamChecks = async () => {
            if (!measurementDate || !selectedMachineId || beamVariants.length === 0) {
                setBeamEntries({});
                return;
            }

            setLoadingAllBeams(true);

            // Format date as YYYY-MM-DD
            const year = measurementDate.getFullYear();
            const month = String(measurementDate.getMonth() + 1).padStart(2, '0');
            const day = String(measurementDate.getDate()).padStart(2, '0');
            const dateStr = `${year}-${month}-${day}`;

            const entries: Record<string, BeamEntry> = {};

            // Initialize all variants
            for (const v of beamVariants) {
                entries[v.id] = {
                    beamCheck: null,
                    allChecks: [],
                    selectedCheckId: null,
                    msdAbs: '',
                    loading: true
                };
            }
            setBeamEntries({ ...entries });

            // Fetch beam checks for each variant in parallel
            const results = await Promise.allSettled(
                beamVariants.map(async (v) => {
                    const checks = await fetchBeamChecksForDate(selectedMachineId, v.variant, dateStr);
                    return { variantId: v.id, checks };
                })
            );

            for (const result of results) {
                if (result.status === 'fulfilled') {
                    const { variantId, checks } = result.value;
                    // Default to the LATEST check (last in array usually, but let's be safe)
                    // API returns sorted by timestamp ascending, so last is latest.
                    const latestCheck = checks.length > 0 ? checks[checks.length - 1] : null;

                    entries[variantId] = {
                        beamCheck: latestCheck,
                        allChecks: checks,
                        selectedCheckId: latestCheck?.id || null,
                        msdAbs: '',
                        loading: false,
                    };
                } else {
                    console.error('Failed to fetch beam checks for a variant:', result.reason);
                }
            }

            // Mark any still-loading as done (in case of errors)
            for (const v of beamVariants) {
                if (entries[v.id].loading) {
                    entries[v.id] = { ...entries[v.id], loading: false };
                }
            }

            setBeamEntries({ ...entries });
            setLoadingAllBeams(false);
        };

        loadAllBeamChecks();
    }, [measurementDate, selectedMachineId, beamVariants]);

    // Helper: format date string
    const formatDateStr = (d: Date): string => {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    };

    // Helper: Format timestamp for dropdown
    const formatTime = (isoString?: string) => {
        if (!isoString) return '';
        const date = new Date(isoString.endsWith('Z') ? isoString : `${isoString}Z`);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Compute DOC factor for a beam entry
    const computeDocFactor = (entry: BeamEntry): number | null => {
        if (!entry.beamCheck || !entry.msdAbs) return null;
        const msd = parseFloat(entry.msdAbs);
        if (isNaN(msd)) return null;
        const rel = entry.beamCheck.relOutput;
        if (rel === null || rel === undefined || isNaN(rel)) return null;
        // Formula: DocFactor = MSD / (1 + RelOutput/100)
        // MPC Rel Output is a percentage change (e.g. 1.8%). 
        // We use (1 + 1.8/100) = 1.018 as the relative factor.
        const doc = msd / (1 + rel / 100);
        if (!isFinite(doc) || isNaN(doc)) return null;
        return doc;
    };

    // Check if MSD Abs value is within valid range (0.97 – 1.03)
    const isMsdAbsInRange = (value: string): boolean => {
        if (!value) return true; // Empty field, no error
        const num = parseFloat(value);
        if (isNaN(num)) return true;
        return num >= MSD_ABS_MIN && num <= MSD_ABS_MAX;
    };

    // Update MSD Abs for a specific variant
    const updateMsdAbs = (variantId: string, value: string) => {
        setBeamEntries(prev => ({
            ...prev,
            [variantId]: { ...prev[variantId], msdAbs: value },
        }));
    };

    // Update Selected Beam Check
    const updateSelectedCheck = (variantId: string, checkId: string) => {
        setBeamEntries(prev => {
            const entry = prev[variantId];
            if (!entry) return prev;
            const newCheck = entry.allChecks.find(c => c.id === checkId) || null;
            return {
                ...prev,
                [variantId]: {
                    ...entry,
                    selectedCheckId: checkId,
                    beamCheck: newCheck
                }
            };
        });
    };

    // Get rows that are ready to save (non-empty, valid DOC)
    const getSavableRows = () => {
        return beamVariants
            .filter(v => {
                const entry = beamEntries[v.id];
                if (!entry || !entry.beamCheck || !entry.msdAbs) return false;
                if (!isMsdAbsInRange(entry.msdAbs)) return false;
                const doc = computeDocFactor(entry);
                return doc !== null;
            })
            .map(v => ({
                variant: v,
                entry: beamEntries[v.id],
            }));
    };

    // Check if any row has an out-of-range DOC value
    const hasOutOfRangeValues = () => {
        return beamVariants.some(v => {
            const entry = beamEntries[v.id];
            if (!entry || !entry.msdAbs) return false;
            return !isMsdAbsInRange(entry.msdAbs);
        });
    };

    // Reset modal form
    const resetForm = () => {
        setMeasurementDate(undefined);
        setStartDate(undefined);
        setBeamEntries({});
        setError(null);
    };

    // Handle batch save
    const handleCreate = async () => {
        const savableRows = getSavableRows();
        if (savableRows.length === 0) {
            setError('No valid entries to save. Fill in MSD Abs values for at least one beam.');
            return;
        }
        if (!startDate) {
            setError('Please select a start date.');
            return;
        }
        if (!measurementDate) {
            setError('Please select a measurement date.');
            return;
        }

        try {
            setSaving(true);
            setError(null);

            const startDateStr = formatDateStr(startDate);
            const measurementDateStr = formatDateStr(measurementDate);

            // Create DOC factors for each valid row sequentially
            for (const { variant, entry } of savableRows) {
                await createDocFactor({
                    machineId: selectedMachineId,
                    beamVariantId: variant.id,
                    beamId: entry.beamCheck!.id,
                    msdAbs: parseFloat(entry.msdAbs),
                    mpcRel: entry.beamCheck!.relOutput,
                    measurementDate: measurementDateStr,
                    startDate: startDateStr,
                });
            }

            setSuccess(`${savableRows.length} DOC factor(s) created successfully`);
            setIsModalOpen(false);
            resetForm();
            await loadDocFactors();

            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create DOC factors');
        } finally {
            setSaving(false);
        }
    };

    // Handle delete DOC factor
    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this DOC factor?')) return;

        try {
            setError(null);
            await deleteDocFactor(id);
            setSuccess('DOC factor deleted successfully');
            await loadDocFactors();
            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete DOC factor');
        }
    };

    // Format date for display
    const formatDate = (dateStr: string | null | undefined) => {
        if (!dateStr) return 'Current';
        const [year, month, day] = dateStr.split('T')[0].split('-').map(Number);
        return new Date(year, month - 1, day).toLocaleDateString();
    };

    // Get beam variant name by ID
    const getBeamVariantName = (id: string) => {
        return beamVariants.find(v => v.id === id)?.variant || id;
    };

    if (loadingMachines) {
        return (
            <section id="doc-settings" className="mb-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 scroll-mt-24">
                <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                    <span className="ml-2 text-gray-500">Loading machines...</span>
                </div>
            </section>
        );
    }

    const savableCount = getSavableRows().length;
    const filledCount = beamVariants.filter(v => beamEntries[v.id]?.msdAbs).length;

    return (
        <section
            id="doc-settings"
            className="mb-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 scroll-mt-24"
        >
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                        Dose Output Correction
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Manage DOC factors to convert MPC relative output to absolute values.
                    </p>
                </div>
                <Button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2"
                    disabled={!selectedMachineId}
                >
                    <Plus className="w-4 h-4" />
                    Add DOC Factor
                </Button>
            </div>

            {/* Machine Selector */}
            <div className="mb-6">
                <Label className="mb-2 block">Select Machine</Label>
                <Select value={selectedMachineId} onValueChange={setSelectedMachineId}>
                    <SelectTrigger className="w-full max-w-xs bg-white dark:bg-gray-900">
                        <SelectValue placeholder="Select a machine" />
                    </SelectTrigger>
                    <SelectContent>
                        {machines.map((machine) => (
                            <SelectItem key={machine.id} value={machine.id}>
                                {machine.name || machine.id}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            {/* Error/Success Messages */}
            {error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                    <span className="text-red-700 dark:text-red-400">{error}</span>
                </div>
            )}
            {success && (
                <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                    <span className="text-green-700 dark:text-green-400">{success}</span>
                </div>
            )}

            {/* DOC Factors Table */}
            {loading ? (
                <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                </div>
            ) : docFactors.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No DOC factors configured for {selectedMachineName || 'this machine'}.
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200 dark:border-gray-700">
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">Beam Type</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">Msd Abs</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">MPC Rel</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">DOC Factor</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">Valid From</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">Valid Until</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {docFactors.map((doc) => (
                                <tr key={doc.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700/50">
                                    <td className="py-3 px-4 text-sm text-gray-900 dark:text-white font-medium">
                                        {doc.beamVariantName || getBeamVariantName(doc.beamVariantId)}
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">
                                        {doc.msdAbs?.toFixed(4) ?? '-'}
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">
                                        {doc.mpcRel?.toFixed(4) ?? '-'}
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300 font-medium">
                                        {doc.docFactor?.toFixed(4) ?? '-'}
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">
                                        {formatDate(doc.startDate)}
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">
                                        {formatDate(doc.endDate)}
                                    </td>
                                    <td className="py-3 px-4 text-right">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => handleDelete(doc.id!)}
                                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Add DOC Factor Modal — All Beams at Once */}
            <Dialog open={isModalOpen} onOpenChange={(open) => { setIsModalOpen(open); if (!open) resetForm(); }}>
                <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Add DOC Factors for {selectedMachineName}</DialogTitle>
                    </DialogHeader>

                    <div className="space-y-5 py-4">
                        {/* Step 1: Measurement Date */}
                        <div>
                            <Label>Measurement Date</Label>
                            <div className="mt-1">
                                <DatePicker
                                    date={measurementDate}
                                    setDate={setMeasurementDate}
                                    className="w-full"
                                />
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                                Select the date when the MSD measurements were taken
                            </p>
                        </div>

                        {/* Step 2: All Beam Variants Table */}
                        {measurementDate && (
                            <div>
                                <Label className="mb-2 block">Beam Measurements</Label>
                                {loadingAllBeams ? (
                                    <div className="flex items-center gap-2 py-6 justify-center text-gray-500">
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Loading beam checks for all variants...
                                    </div>
                                ) : (
                                    <div className="border rounded-lg overflow-hidden">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="bg-gray-100 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-600">
                                                    <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">Beam Type</th>
                                                    <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">MPC Rel Output</th>
                                                    <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">MSD Abs</th>
                                                    <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">DOC Factor</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {beamVariants.map((v) => {
                                                    const entry = beamEntries[v.id];
                                                    const hasCheck = entry?.beamCheck !== null && entry?.beamCheck !== undefined;
                                                    const doc = entry ? computeDocFactor(entry) : null;
                                                    const msdOutOfRange = entry?.msdAbs ? !isMsdAbsInRange(entry.msdAbs) : false;
                                                    const isLoading = entry?.loading;
                                                    const hasMultipleChecks = entry && entry.allChecks.length > 1;

                                                    return (
                                                        <tr
                                                            key={v.id}
                                                            className={`border-b border-gray-100 dark:border-gray-800 ${!hasCheck && !isLoading
                                                                ? 'opacity-40'
                                                                : ''
                                                                }`}
                                                        >
                                                            <td className="py-2.5 px-3 font-medium text-gray-900 dark:text-white">
                                                                {v.variant}
                                                            </td>
                                                            <td className="py-2.5 px-3 text-gray-600 dark:text-gray-400 font-mono">
                                                                {isLoading ? (
                                                                    <Loader2 className="w-3 h-3 animate-spin" />
                                                                ) : hasCheck ? (
                                                                    hasMultipleChecks ? (
                                                                        <Select
                                                                            value={entry.selectedCheckId || ''}
                                                                            onValueChange={(val) => updateSelectedCheck(v.id, val)}
                                                                        >
                                                                            <SelectTrigger className="h-8 w-30 text-xs">
                                                                                <SelectValue placeholder="Select check" />
                                                                            </SelectTrigger>
                                                                            <SelectContent>
                                                                                {entry.allChecks.map(check => (
                                                                                    <SelectItem key={check.id} value={check.id}>
                                                                                        {formatTime(check.timestamp)} - {check.relOutput.toFixed(4)}
                                                                                    </SelectItem>
                                                                                ))}
                                                                            </SelectContent>
                                                                        </Select>
                                                                    ) : (
                                                                        <span>{entry.beamCheck!.relOutput.toFixed(4)}</span>
                                                                    )
                                                                ) : (
                                                                    <span className="text-gray-400 italic text-xs">No data</span>
                                                                )}
                                                            </td>
                                                            <td className="py-2.5 px-3">
                                                                <Input
                                                                    type="number"
                                                                    step="0.0001"
                                                                    min="0"
                                                                    value={entry?.msdAbs ?? ''}
                                                                    onChange={(e) => updateMsdAbs(v.id, e.target.value)}
                                                                    placeholder={hasCheck ? '0.0000' : '—'}
                                                                    disabled={!hasCheck || isLoading}
                                                                    className={`h-8 w-28 text-sm ${msdOutOfRange
                                                                        ? 'border-red-400 focus:border-red-500 focus:ring-red-500'
                                                                        : ''
                                                                        }`}
                                                                />
                                                                {msdOutOfRange && (
                                                                    <span className="text-xs text-red-500 mt-0.5 block">{MSD_ABS_MIN}–{MSD_ABS_MAX}</span>
                                                                )}
                                                            </td>
                                                            <td className="py-2.5 px-3 font-mono">
                                                                {doc !== null ? (
                                                                    <span className="text-gray-900 dark:text-white">
                                                                        {doc.toFixed(4)}
                                                                    </span>
                                                                ) : (
                                                                    <span className="text-gray-300 dark:text-gray-600">—</span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}

                                {/* Boundary warning */}
                                {hasOutOfRangeValues() && (
                                    <div className="mt-2 p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2">
                                        <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                                        <p className="text-xs text-red-700 dark:text-red-400">
                                            MSD Abs values must be between <strong>{MSD_ABS_MIN}</strong> and <strong>{MSD_ABS_MAX}</strong>. Out-of-range entries will not be saved.
                                        </p>
                                    </div>
                                )}

                                {/* Info hint */}
                                <p className="text-xs text-gray-500 mt-2">
                                    Fill in MSD Abs values for the beams you want. Leave others empty — only filled rows will be saved.
                                </p>
                            </div>
                        )}

                        {/* Step 3: Start Date */}
                        {measurementDate && filledCount > 0 && (
                            <div>
                                <Label>Valid From (Start Date)</Label>
                                <div className="mt-1">
                                    <DatePicker
                                        date={startDate}
                                        setDate={setStartDate}
                                        className="w-full"
                                    />
                                </div>
                                <p className="text-xs text-gray-500 mt-1">
                                    DOC factors will apply to results from this date onwards
                                </p>
                            </div>
                        )}
                    </div>

                    <DialogFooter className="flex items-center justify-between sm:justify-between">
                        <span className="text-xs text-gray-500">
                            {savableCount > 0
                                ? `${savableCount} beam(s) ready to save`
                                : 'Fill in MSD Abs values to save'}
                        </span>
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                                Cancel
                            </Button>
                            <Button
                                onClick={handleCreate}
                                disabled={savableCount === 0 || !startDate || saving}
                            >
                                {saving ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Saving...
                                    </>
                                ) : (
                                    `Save ${savableCount > 0 ? `(${savableCount})` : ''}`
                                )}
                            </Button>
                        </div>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </section>
    );
}
