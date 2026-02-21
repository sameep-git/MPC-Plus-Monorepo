'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { fetchUser, handleApiError, fetchThresholds, saveThreshold, fetchMachines, fetchBeamVariantsWithIds, type Threshold, type BeamVariantWithId } from '../../lib/api';
import DocFactorSettings from '../../components/settings/DocFactorSettings';
import MachineSettings from '../../components/settings/MachineSettings';
import type { Machine } from '../../models/Machine';
import {
  Navbar,
  Button,
  Input,
  Label,
  RadioGroup,
  RadioGroupItem,
  DatePicker,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter
} from '../../components/ui';
import { NAVIGATION } from '../../constants';
import { TEAM_COLORS } from '../../constants/teamColors';
import {
  getSettings,
  getDefaultAppSettings,
  saveSettings,
  updateTheme,
  updateAccentColor,
  updateGraphThresholds,
  updateBaselineSettings,
  type Theme,
  type AppSettings,
  type BaselineMode,
  type BaselineManualValues,
} from '../../lib/settings';
import { useThresholds } from '../../lib/context/ThresholdContext';

const BEAM_METRICS = {
  'Relative Output': 'Relative Output (%)',
  'Relative Uniformity': 'Relative Uniformity (%)',
  'Center Shift': 'Center Shift (mm)',
} as const;

const GEO_METRICS = {
  // IsoCenter
  'Iso Center Size': 'Iso Center Size (mm)',
  'Iso Center MV Offset': 'Iso Center MV Offset (mm)',
  'Iso Center KV Offset': 'Iso Center KV Offset (mm)',
  // Collimation
  'Collimation Rotation Offset': 'Collimation Rotation Offset (deg)',
  // Gantry
  'Gantry Absolute': 'Gantry Absolute (deg)',
  'Gantry Relative': 'Gantry Relative (deg)',
  // Couch
  'Couch Lat': 'Couch Lat (mm)',
  'Couch Lng': 'Couch Lng (mm)',
  'Couch Vrt': 'Couch Vrt (mm)',
  'Couch Rtn Fine': 'Couch Rtn Fine (deg)',
  'Couch Rtn Large': 'Couch Rtn Large (deg)',
  'Max Position Error': 'Max Position Error (mm)',
  'Rotation Induced Shift': 'Rotation Induced Shift (mm)',
  // MLC Offsets
  'Mean Offset A': 'Mean Offset A (mm)',
  'Max Offset A': 'Max Offset A (mm)',
  'Mean Offset B': 'Mean Offset B (mm)',
  'Max Offset B': 'Max Offset B (mm)',
  // Jaws
  'Jaw X1': 'Jaw X1 (mm)',
  'Jaw X2': 'Jaw X2 (mm)',
  'Jaw Y1': 'Jaw Y1 (mm)',
  'Jaw Y2': 'Jaw Y2 (mm)',
  // Jaws Parallelism
  'Parallelism X1': 'Parallelism X1 (deg)',
  'Parallelism X2': 'Parallelism X2 (deg)',
  'Parallelism Y1': 'Parallelism Y1 (deg)',
  'Parallelism Y2': 'Parallelism Y2 (deg)',
} as const;

const ITEMS_PER_PAGE = 6;

const MANUAL_BASELINE_FIELDS: Array<{ key: keyof BaselineManualValues; label: string; helper?: string }> = [
  {
    key: 'outputChange',
    label: 'Output Change (%)',
    helper: 'Baseline output delta for MPC comparisons.',
  },
  {
    key: 'uniformityChange',
    label: 'Uniformity Change (%)',
    helper: 'Baseline uniformity delta to compare day-to-day changes.',
  },
  {
    key: 'centerShift',
    label: 'Center Shift',
    helper: 'Baseline couch/beam center shift reference.',
  },
];

const SETTINGS_SECTIONS = [
  { id: 'theme-settings', label: 'Theme & Accent' },
  { id: 'machine-settings', label: 'Machine Management' },
  { id: 'beam-threshold-settings', label: 'Threshold Configuration' },
  // { id: 'graph-threshold-settings', label: 'Graph Threshold' },
  // { id: 'baseline-settings', label: 'Baseline' },
  { id: 'doc-settings', label: 'Dose Output Correction' },
] as const;

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: string; name?: string; role?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<AppSettings>(() => getSettings());
  const [saved, setSaved] = useState(false);

  // Threshold State
  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState<string>('default-machine');
  const [checkType, setCheckType] = useState<'beam' | 'geometry'>('beam');
  const [beamVariants, setBeamVariants] = useState<BeamVariantWithId[]>([]);
  const [beamVariant, setBeamVariant] = useState<string>('');  // stores UUID
  const [currentPage, setCurrentPage] = useState(1);
  const [loadingThresholds, setLoadingThresholds] = useState(false);
  const [savingThresholds, setSavingThresholds] = useState(false);
  const [thresholdSuccess, setThresholdSuccess] = useState<string | null>(null);

  // Geo-specific UI state
  const [geoInputMode, setGeoInputMode] = useState<'easy' | 'manual'>('easy');
  const [easyThresholdValue, setEasyThresholdValue] = useState<number>(2.0);

  useEffect(() => {
    const loadUser = async () => {
      try {
        setError(null);
        const userData = await fetchUser();
        setUser(userData);
      } catch (error) {
        const errorMessage = handleApiError(error);
        setError(errorMessage);
        console.error('Error loading user:', error);
      }
    };

    const loadData = async () => {
      try {
        setLoadingThresholds(true);
        const [machinesData, thresholdsData, beamVariantsData] = await Promise.all([
          fetchMachines(),
          fetchThresholds(),
          fetchBeamVariantsWithIds()
        ]);

        setMachines(machinesData);
        setBeamVariants(beamVariantsData);
        if (machinesData.length > 0 && selectedMachineId === 'default-machine') {
          setSelectedMachineId(machinesData[0].id);
        }
        if (beamVariantsData.length > 0 && !beamVariant) {
          setBeamVariant(beamVariantsData[0].id); // default to first variant UUID
        }

        setThresholds(thresholdsData);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setLoadingThresholds(false);
      }
    };

    loadUser();
    loadData();
  }, []);

  const { refreshThresholds } = useThresholds();

  // Handle browser back button to navigate to calendar (results) page
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handlePopState = (event: PopStateEvent) => {
      if (event.state?.fromSettings && !window.location.hash) {
        router.replace(NAVIGATION.ROUTES.MPC_RESULT);
      }
    };

    if (!window.location.hash) {
      window.history.pushState({ fromSettings: true }, '', window.location.href);
    }

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [router]);



  const handleAccentChange = (color: string) => {
    updateAccentColor(color);
    setSettings((prev) => ({ ...prev, accentColor: color }));
  };

  const handleGraphThresholdChange = (
    topPercent?: number,
    bottomPercent?: number,
    color?: string
  ) => {
    const newSettings = { ...settings };
    if (topPercent !== undefined) newSettings.graphThresholdTopPercent = topPercent;
    if (bottomPercent !== undefined) newSettings.graphThresholdBottomPercent = bottomPercent;
    if (color !== undefined) newSettings.graphThresholdColor = color;
    setSettings(newSettings);
    updateGraphThresholds(topPercent, bottomPercent, color);
  };

  const ensureIsoDate = (date: Date) => date.toISOString().split('T')[0];

  const handleBaselineModeChange = (mode: BaselineMode) => {
    const nextDate = settings.baseline.date ?? ensureIsoDate(new Date());
    const updatedBaseline = {
      ...settings.baseline,
      mode,
      date: mode === 'date' ? nextDate : settings.baseline.date,
    };

    setSettings((prev) => ({ ...prev, baseline: updatedBaseline }));
    updateBaselineSettings({
      mode,
      ...(mode === 'date' ? { date: nextDate } : {}),
    });
  };

  const handleBaselineDateChange = (dateString: string) => {
    const normalizedDate = dateString || undefined;
    setSettings((prev) => ({
      ...prev,
      baseline: {
        ...prev.baseline,
        date: normalizedDate,
        mode: 'date',
      },
    }));
    updateBaselineSettings({ date: normalizedDate, mode: 'date' });
  };

  const handleManualBaselineChange = (field: keyof BaselineManualValues, value: number) => {
    const updatedManualValues: BaselineManualValues = {
      ...settings.baseline.manualValues,
      [field]: value,
    };
    setSettings((prev) => ({
      ...prev,
      baseline: {
        ...prev.baseline,
        manualValues: updatedManualValues,
      },
    }));
    updateBaselineSettings({ manualValues: updatedManualValues });
  };

  const handleBaselineUseToday = () => {
    const today = ensureIsoDate(new Date());
    setSettings((prev) => ({
      ...prev,
      baseline: {
        ...prev.baseline,
        mode: 'date',
        date: today,
      },
    }));
    updateBaselineSettings({ mode: 'date', date: today });
  };

  const handleReset = () => {
    const defaultSettings = getDefaultAppSettings();
    saveSettings(defaultSettings);
    setSettings(defaultSettings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  // Threshold logic
  const activeMetrics = checkType === 'beam' ? BEAM_METRICS : GEO_METRICS;
  const activeMetricEntries = Object.entries(activeMetrics);
  const totalPages = Math.ceil(activeMetricEntries.length / ITEMS_PER_PAGE);

  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentMetrics = activeMetricEntries.slice(startIndex, endIndex);

  // Reset pagination when check type changes
  useEffect(() => {
    setCurrentPage(1);
  }, [checkType]);

  const getThresholdValue = (metric: string) => {
    const found = thresholds.find(
      (t) =>
        t.machineId === selectedMachineId &&
        t.checkType === checkType &&
        t.metricType === metric &&
        (checkType === 'beam' ? (t.beamVariantId === beamVariant || t.beamVariant === beamVariant) : true)
    );
    return found?.value ?? 0;
  };

  const updateThresholdValue = (metric: string, value: number) => {
    console.log('[updateThresholdValue] Called with:', { metric, value, selectedMachineId, checkType, beamVariant });
    setThresholds((prev) => {
      console.log('[updateThresholdValue] Current thresholds sample:', prev.slice(0, 3).map(t => ({ machineId: t.machineId, checkType: t.checkType, metricType: t.metricType, value: t.value })));
      const existingIndex = prev.findIndex(
        (t) =>
          t.machineId === selectedMachineId &&
          t.checkType === checkType &&
          t.metricType === metric &&
          (checkType === 'beam' ? (t.beamVariantId === beamVariant || t.beamVariant === beamVariant) : true)
      );
      console.log('[updateThresholdValue] Found existing at index:', existingIndex);

      const selectedVariant = beamVariants.find(v => v.id === beamVariant);
      const newItem: Threshold = {
        id: existingIndex >= 0 ? prev[existingIndex].id : undefined,
        machineId: selectedMachineId,
        checkType,
        metricType: metric,
        beamVariant: checkType === 'beam' ? selectedVariant?.variant : undefined,
        beamVariantId: checkType === 'beam' ? beamVariant : undefined,
        value,
        lastUpdated: new Date().toISOString(),
      };

      if (existingIndex >= 0) {
        const newArr = [...prev];
        newArr[existingIndex] = newItem;
        return newArr;
      } else {
        return [...prev, newItem];
      }
    });
  };

  const handleSaveThresholds = async () => {
    console.log('[handleSaveThresholds] Starting with thresholds count:', thresholds.length);
    setSavingThresholds(true);
    setThresholdSuccess(null);
    try {
      // In geometry easy mode, use easyThresholdValue for ALL geo metrics
      if (checkType === 'geometry' && geoInputMode === 'easy') {
        const metricsToSave = Object.keys(GEO_METRICS);
        for (const metric of metricsToSave) {
          console.log('[handleSaveThresholds] Easy mode - saving:', { metric, value: easyThresholdValue });
          const newItem: Threshold = {
            machineId: selectedMachineId,
            checkType: 'geometry',
            metricType: metric,
            beamVariant: undefined,
            value: easyThresholdValue,
          };
          await saveThreshold(newItem);
        }
      } else {
        // Normal mode - save individual thresholds from state
        const metricsToSave = Object.keys(activeMetrics);

        for (const metric of metricsToSave) {
          const threshold = thresholds.find(
            (t) =>
              t.machineId === selectedMachineId &&
              t.checkType === checkType &&
              t.metricType === metric &&
              (checkType === 'beam' ? (t.beamVariantId === beamVariant || t.beamVariant === beamVariant) : true)
          );

          if (threshold) {
            console.log('[handleSaveThresholds] Saving threshold:', { metric, value: threshold.value, id: threshold.id });
            await saveThreshold(threshold);
          } else {
            const val = getThresholdValue(metric);
            console.log('[handleSaveThresholds] Creating new threshold:', { metric, value: val });
            const selectedVariant = beamVariants.find(v => v.id === beamVariant);
            const newItem: Threshold = {
              machineId: selectedMachineId,
              checkType,
              metricType: metric,
              beamVariant: checkType === 'beam' ? selectedVariant?.variant : undefined,
              beamVariantId: checkType === 'beam' ? beamVariant : undefined,
              value: val,
            };
            await saveThreshold(newItem);
          }
        }
      }

      // Refresh thresholds from server to ensure UI is in sync
      await refreshThresholds();
      const updatedThresholds = await fetchThresholds();
      setThresholds(updatedThresholds);

      setThresholdSuccess('Thresholds updated successfully!');
      setTimeout(() => setThresholdSuccess(null), 3000);
    } catch (error) {
      console.error('Failed to save thresholds', error);
      setError('Failed to save thresholds');
    } finally {
      setSavingThresholds(false);
    }
  };

  // Save current metric values to ALL beam variants
  const handleSaveForAllBeams = async () => {
    setSavingThresholds(true);
    setThresholdSuccess(null);
    try {
      const metricsToSave = Object.keys(BEAM_METRICS);
      for (const variant of beamVariants) {
        for (const metric of metricsToSave) {
          // Use the value from the CURRENT beamVariant as the template
          const val = getThresholdValue(metric);
          const newItem: Threshold = {
            machineId: selectedMachineId,
            checkType: 'beam',
            metricType: metric,
            beamVariant: variant.variant,
            beamVariantId: variant.id,
            value: val,
          };
          await saveThreshold(newItem);
        }
      }
      // Refresh thresholds after bulk save
      await refreshThresholds();
      const updatedThresholds = await fetchThresholds();
      setThresholds(updatedThresholds);
      setThresholdSuccess('Thresholds applied to all beam variants!');
      setTimeout(() => setThresholdSuccess(null), 3000);
    } catch (error) {
      console.error('Failed to save thresholds for all beams', error);
      setError('Failed to save thresholds for all beams');
    } finally {
      setSavingThresholds(false);
    }
  };

  // Save current metric values to ALL geo metrics (no variants)
  // In easy mode, use easyThresholdValue for all metrics
  const handleSaveForAllGeoChecks = async () => {
    setSavingThresholds(true);
    setThresholdSuccess(null);
    try {
      const metricsToSave = Object.keys(GEO_METRICS);
      // In easy mode, use the single easyThresholdValue for all metrics
      const valueToSave = geoInputMode === 'easy' ? easyThresholdValue : null;

      for (const metric of metricsToSave) {
        const val = valueToSave !== null ? valueToSave : getThresholdValue(metric);
        const newItem: Threshold = {
          machineId: selectedMachineId,
          checkType: 'geometry',
          metricType: metric,
          beamVariant: undefined,
          value: val,
        };
        await saveThreshold(newItem);
      }
      // Refresh thresholds after bulk save
      await refreshThresholds();
      const updatedThresholds = await fetchThresholds();
      setThresholds(updatedThresholds);
      setThresholdSuccess('All geometry thresholds saved!');
      setTimeout(() => setThresholdSuccess(null), 3000);
    } catch (error) {
      console.error('Failed to save all geometry thresholds', error);
      setError('Failed to save all geometry thresholds');
    } finally {
      setSavingThresholds(false);
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 transition-colors">
      <Navbar user={user} />

      <main className="p-6 max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">Settings</h1>

        <nav
          aria-label="Settings sections"
          className="mb-8 flex flex-wrap gap-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-4 shadow-sm"
        >
          {SETTINGS_SECTIONS.map((section) => (
            <Button
              key={section.id}
              variant="outline"
              onClick={(e) => {
                e.preventDefault();
                const element = document.getElementById(section.id);
                if (element) {
                  element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
              }}
              className="text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 hover:bg-primary/10 hover:text-primary dark:hover:bg-primary/20 dark:hover:text-primary-foreground border-gray-200 dark:border-gray-700"
            >
              {section.label}
            </Button>
          ))}
        </nav>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-600 dark:text-red-400">Error: {error}</p>
          </div>
        )}

        {/* Theme Settings */}
        <section
          id="theme-settings"
          className="mb-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 scroll-mt-24"
        >
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Theme</h2>
          <div className="max-w-md">
            <Label className="mb-2 block">Accent Color</Label>
            <Select
              value={settings.accentColor}
              onValueChange={handleAccentChange}
            >
              <SelectTrigger className="w-full bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 h-12">
                <SelectValue placeholder="Select a team color" />
              </SelectTrigger>
              <SelectContent className="max-h-64">
                {TEAM_COLORS.map((team) => (
                  <SelectItem key={team.color} value={team.color}>
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded-full border border-gray-200 shadow-sm shrink-0"
                        style={{ backgroundColor: team.color }}
                      />
                      <span className="truncate">{team.name}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </section>

        {/* Machine Settings */}
        <section
          id="machine-settings"
          className="mb-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 scroll-mt-24"
        >
          <MachineSettings />
        </section>

        {/* Threshold Configuration */}
        <section
          id="beam-threshold-settings"
          className="mb-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 scroll-mt-24"
        >
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Threshold Configuration
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                Manage pass/fail tolerances for beam and geometry checks.
              </p>
            </div>
            {thresholdSuccess && (
              <span className="text-green-600 font-medium animate-pulse">{thresholdSuccess}</span>
            )}
          </div>

          <Card className="bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700">
            <CardHeader>
              <div className="flex flex-col md:flex-row gap-2 items-end">
                <div className="w-full md:w-[200px]">
                  <Label>Machine</Label>
                  <Select value={selectedMachineId} onValueChange={setSelectedMachineId}>
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select machine" />
                    </SelectTrigger>
                    <SelectContent>
                      {machines.map(m => (
                        <SelectItem key={m.id} value={m.id}>{m.name || m.id}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="w-full md:w-[200px]">
                  <Label>Check Type</Label>
                  <Select value={checkType} onValueChange={(val: 'beam' | 'geometry') => setCheckType(val)}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beam">Beam Check</SelectItem>
                      <SelectItem value="geometry">Geometry Check</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {checkType === 'beam' && (
                  <div className="w-full md:w-[200px]">
                    <Label>Beam Variant</Label>
                    <Select value={beamVariant} onValueChange={setBeamVariant}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {beamVariants.map(v => (
                          <SelectItem key={v.id} value={v.id}>{v.variant}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {/* Mode tabs for geometry */}
              {checkType === 'geometry' && (
                <div className="mb-6 flex gap-2">
                  <Button
                    variant={geoInputMode === 'easy' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setGeoInputMode('easy')}
                  >
                    Easy
                  </Button>
                  <Button
                    variant={geoInputMode === 'manual' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setGeoInputMode('manual')}
                  >
                    Manual
                  </Button>
                </div>
              )}

              {/* Easy mode for geometry */}
              {checkType === 'geometry' && geoInputMode === 'easy' && (
                <div className="p-6 border rounded-lg border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
                  <Label className="text-lg font-medium mb-4 block">Default Tolerance for All Geometry Checks</Label>
                  <p className="text-sm text-gray-500 mb-4">
                    This value will be applied to all geometry metrics when saved.
                  </p>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-500">Tolerance (±)</span>
                    <Input
                      type="number"
                      step="0.1"
                      className="w-32 bg-white dark:bg-gray-950"
                      value={easyThresholdValue || ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        setEasyThresholdValue(val === '' ? 0 : parseFloat(val));
                      }}
                      placeholder="2.0"
                    />
                  </div>
                </div>
              )}

              {/* Manual mode or Beam checks - show individual metrics */}
              {(checkType === 'beam' || (checkType === 'geometry' && geoInputMode === 'manual')) && (
                <>
                  <div className={`space-y-6 ${totalPages > 1 ? 'min-h-[400px]' : ''}`}>
                    {currentMetrics.map(([key, label]) => (
                      <div key={key} className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 border rounded-md border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/50">
                        <Label className="flex-1 text-base">{label}</Label>
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-gray-500">Tolerance (±)</span>
                          <Input
                            type="number"
                            step="0.1"
                            className="w-32 bg-white dark:bg-gray-950"
                            value={getThresholdValue(key) || ''}
                            onChange={(e) => {
                              const val = e.target.value;
                              updateThresholdValue(key, val === '' ? 0 : parseFloat(val));
                            }}
                            placeholder="0"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* Pagination Controls - only show in manual mode or for beams */}
              {(checkType === 'beam' || geoInputMode === 'manual') && totalPages > 1 && (
                <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100 dark:border-gray-800">
                  <div className="text-sm text-gray-500">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
            <CardFooter className="flex flex-wrap justify-end gap-3 pt-6">
              {checkType === 'beam' && (
                <Button
                  variant="outline"
                  onClick={handleSaveForAllBeams}
                  disabled={savingThresholds || loadingThresholds}
                >
                  {savingThresholds ? 'Saving...' : 'Save for All Beams'}
                </Button>
              )}
              <Button
                onClick={handleSaveThresholds}
                disabled={savingThresholds || loadingThresholds}
              >
                {savingThresholds ? 'Saving...' : 'Save Changes'}
              </Button>
            </CardFooter>
          </Card>
        </section>

        {/* Graph Threshold Settings — temporarily hidden
        <section
          id="graph-threshold-settings"
          className="mb-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 scroll-mt-24"
        >
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            Graph Threshold Settings
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="graph-threshold-top" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Top Threshold (%)
                </label>
                <Input
                  id="graph-threshold-top"
                  type="number"
                  step="0.01"
                  value={settings.graphThresholdTopPercent}
                  onChange={(e) =>
                    handleGraphThresholdChange(parseFloat(e.target.value) || 0, undefined, undefined)
                  }
                  className="bg-white dark:bg-gray-900"
                />
              </div>
              <div>
                <label htmlFor="graph-threshold-bottom" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Bottom Threshold (%)
                </label>
                <Input
                  id="graph-threshold-bottom"
                  type="number"
                  step="0.01"
                  value={settings.graphThresholdBottomPercent}
                  onChange={(e) =>
                    handleGraphThresholdChange(undefined, parseFloat(e.target.value) || 0, undefined)
                  }
                  className="bg-white dark:bg-gray-900"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Threshold Color
              </label>
              <div className="flex gap-4 items-center">
                <Input
                  type="color"
                  value={settings.graphThresholdColor}
                  onChange={(e) => handleGraphThresholdChange(undefined, undefined, e.target.value)}
                  className="w-16 h-10 p-1 cursor-pointer"
                />
                <Input
                  type="text"
                  value={settings.graphThresholdColor}
                  onChange={(e) => handleGraphThresholdChange(undefined, undefined, e.target.value)}
                  className="flex-1 bg-white dark:bg-gray-900"
                  placeholder="#fef3c7"
                />
              </div>
            </div>
          </div>
        </section>
        */}

        {/* Baseline Settings — temporarily hidden
        <section
          id="baseline-settings"
          className="mb-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 scroll-mt-24"
        >
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Baseline Settings</h2>
          <div className="space-y-6">
            <RadioGroup
              value={settings.baseline.mode}
              onValueChange={(val) => handleBaselineModeChange(val as BaselineMode)}
              className="flex flex-wrap gap-3"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="date" id="mode-date" />
                <Label htmlFor="mode-date">Use values from a specific date</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="manual" id="mode-manual" />
                <Label htmlFor="mode-manual">Set manual baseline values</Label>
              </div>
            </RadioGroup>

            {settings.baseline.mode === 'date' && (
              <div className="w-full md:w-auto">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Baseline Date
                </label>
                <div className="flex flex-row flex-wrap gap-3 items-center">
                  <DatePicker
                    date={settings.baseline.date ? new Date(settings.baseline.date) : undefined}
                    setDate={(date) => {
                      if (date) {
                        const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
                        const isoDate = offsetDate.toISOString().split('T')[0];
                        handleBaselineDateChange(isoDate);
                      }
                    }}
                    className="w-64"
                  />
                  <Button onClick={handleBaselineUseToday} className="flex-shrink-0">
                    Use Today
                  </Button>
                </div>
              </div>
            )}

            {settings.baseline.mode === 'manual' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {MANUAL_BASELINE_FIELDS.map(({ key, label, helper }) => (
                  <div key={key} className="p-4 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{label}</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={settings.baseline.manualValues[key]}
                      onChange={(e) => handleManualBaselineChange(key, parseFloat(e.target.value) || 0)}
                      className="bg-white dark:bg-gray-900"
                    />
                    {helper && <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{helper}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
        */}

        {/* DOC Factor Settings */}
        <DocFactorSettings />

        {/* Action Buttons */}
        <div className="flex gap-4 justify-end">
          <Button
            variant="ghost"
            onClick={handleReset}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
          >
            Reset to Defaults
          </Button>
          {saved && (
            <div className="flex items-center text-green-600 dark:text-green-400">
              <span className="text-sm font-medium">Settings saved!</span>
            </div>
          )}
        </div>
      </main >
    </div >
  );
}
