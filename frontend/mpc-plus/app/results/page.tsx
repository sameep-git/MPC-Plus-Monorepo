'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

import { fetchMachines, fetchUser, fetchResults, handleApiError, fetchBeamTypes, generateReport } from '../../lib/api';
import type { Machine as MachineType } from '../../models/Machine';
import {
  Navbar,
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  // Dialog, // Handled by shared component
  // DialogContent,
  // DialogHeader,
  // DialogTitle,
  // DialogFooter,
  // Label,
  // Checkbox,
  // DatePicker,
  // DateRangePicker
} from '../../components/ui';
import { ReportGenerationModal } from '../../components/results/ReportGenerationModal';
import { DateRange } from 'react-day-picker';
import { UI_CONSTANTS, CALENDAR_CONSTANTS } from '../../constants';

// API response types
interface DayCheckStatus {
  date: string;
  beamCheckStatus: 'pass' | 'warning' | 'fail' | null;
  geometryCheckStatus: 'pass' | 'warning' | 'fail' | null;
  beamApproved?: boolean;
  geometryApproved?: boolean;
  beamCount?: number;
  geometryCheckCount?: number;
}


interface MonthlyResults {
  month: number;
  year: number;
  machineId: string;
  checks: DayCheckStatus[];
}

export default function MPCResultPage() {

  const router = useRouter();
  const [machines, setMachines] = useState<MachineType[]>([]);
  const [user, setUser] = useState<{ id: string; name?: string } | null>(null);
  const [selectedMachine, setSelectedMachine] = useState<MachineType | null>(null);
  const today = new Date();
  const [selectedMonth, setSelectedMonth] = useState<number>(today.getMonth()); // 0-11
  const [selectedYear, setSelectedYear] = useState<number>(today.getFullYear());
  const [monthlyResults, setMonthlyResults] = useState<MonthlyResults | null>(null);

  // Cache for monthly results: Key = "machineId-year-month", Value = MonthlyResults
  const [resultsCache, setResultsCache] = useState<Record<string, MonthlyResults>>({});
  const fetchingRef = useRef<Set<string>>(new Set());

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  // Report Generation Modal State
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportStartDate, setReportStartDate] = useState<Date>(() => new Date());
  const [reportEndDate, setReportEndDate] = useState<Date>(() => new Date());
  const [reportSelectedChecks, setReportSelectedChecks] = useState<Set<string>>(new Set());
  const [availableReportChecks, setAvailableReportChecks] = useState<{ id: string; name: string; type: 'beam' | 'geo' }[]>([]);

  // Initialize available checks
  useEffect(() => {
    const loadChecks = async () => {
      // Static Geometry Checks
      const geoChecks = [
        { id: 'geo-isocenter', name: 'IsoCenter Group', type: 'geo' },
        { id: 'geo-beam', name: 'Beam Group', type: 'geo' },
        { id: 'geo-collimation', name: 'Collimation Group', type: 'geo' },
        { id: 'geo-gantry', name: 'Gantry Group', type: 'geo' },
        { id: 'geo-couch', name: 'Enhanced Couch Group', type: 'geo' },
        { id: 'geo-mlc-a', name: 'MLC Leaves A', type: 'geo' },
        { id: 'geo-mlc-b', name: 'MLC Leaves B', type: 'geo' },
        { id: 'geo-mlc-offsets', name: 'MLC Offsets', type: 'geo' },
        { id: 'geo-backlash-a', name: 'Backlash Leaves A', type: 'geo' },
        { id: 'geo-backlash-b', name: 'Backlash Leaves B', type: 'geo' },
        { id: 'geo-jaws', name: 'Jaws Group', type: 'geo' },
        { id: 'geo-jaws-parallelism', name: 'Jaws Parallelism', type: 'geo' },
      ] as const;

      // Fetch Beam Types to build dynamic beam list
      let beamChecks: { id: string; name: string; type: 'beam' }[] = [];
      try {
        const types = await fetchBeamTypes();
        if (types && types.length > 0) {
          beamChecks = types.map(t => ({
            id: `beam-${t}`,
            name: `Beam Check (${t})`,
            type: 'beam'
          }));
        } else {
          // Fallback default
          const defaults = ['6x', '6xFFF', '10x', '10xFFF', '15x', '6e', '9e', '12e', '16e', '20e'];
          beamChecks = defaults.map(t => ({ id: `beam-${t}`, name: `Beam Check (${t})`, type: 'beam' }));
        }
      } catch (e) {
        console.error('Failed to fetch beam types for report:', e);
        // Fallback default on error
        const defaults = ['6x', '6xFFF', '10x', '10xFFF', '15x', '6e', '9e', '12e', '16e', '20e'];
        beamChecks = defaults.map(t => ({ id: `beam-${t}`, name: `Beam Check (${t})`, type: 'beam' }));
      }

      setAvailableReportChecks([...beamChecks, ...geoChecks]);
      // Default select all
      setReportSelectedChecks(new Set([...beamChecks, ...geoChecks].map(c => c.id)));
    };

    if (isReportModalOpen) {
      loadChecks();
    }
  }, [isReportModalOpen]);

  const toggleReportCheck = (checkId: string) => {
    setReportSelectedChecks(prev => {
      const next = new Set(prev);
      if (next.has(checkId)) {
        next.delete(checkId);
      } else {
        next.add(checkId);
      }
      return next;
    });
  };

  const toggleAllReportChecks = (checked: boolean) => {
    if (checked) {
      setReportSelectedChecks(new Set(availableReportChecks.map(c => c.id)));
    } else {
      setReportSelectedChecks(new Set());
    }
  };

  const isAllChecksSelected = availableReportChecks.length > 0 && reportSelectedChecks.size === availableReportChecks.length;
  const handleSaveReport = async () => {
    // console.log('Generating report', { start: reportStartDate, end: reportEndDate, checks: Array.from(reportSelectedChecks) });
    if (!selectedMachine) return;

    try {
      // Create a local date string YYYY-MM-DD
      const formatDate = (d: Date) => {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      const start = formatDate(reportStartDate);
      const end = formatDate(reportEndDate);

      const blob = await generateReport({
        startDate: start,
        endDate: end,
        machineId: selectedMachine.id,
        selectedChecks: Array.from(reportSelectedChecks)
      });

      // Determine file extension based on response content type
      const isZip = blob.type === 'application/zip' || blob.type === 'application/x-zip-compressed';
      const ext = isZip ? 'zip' : 'pdf';
      const machineSafe = selectedMachine.name.replace(/\s+/g, '_');
      const fileName = isZip
        ? `MPC_Reports_${machineSafe}_${start}_to_${end}.${ext}`
        : `MPC_Report_${machineSafe}_${start}_to_${end}.${ext}`;

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setIsReportModalOpen(false);
    } catch (err) {
      console.error('Failed to generate report', err);
      // Ideally show a toast here
      setError('Failed to generate report: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        setError(null);
        const [machinesData, userData] = await Promise.all([
          fetchMachines(),
          fetchUser()
        ]);
        setMachines(machinesData);
        setUser(userData);

        // Set machine from localStorage or default to first machine
        if (machinesData.length > 0) {
          const savedMachineId = typeof window !== 'undefined' ? localStorage.getItem('selectedMachineId') : null;
          const machineToSelect = savedMachineId
            ? machinesData.find(m => m.id === savedMachineId) || machinesData[0]
            : machinesData[0];
          setSelectedMachine(machineToSelect);

          // Update localStorage to ensure it's set
          if (typeof window !== 'undefined') {
            localStorage.setItem('selectedMachineId', machineToSelect.id);
          }
        }

        // Month and year default to current via initial state
      } catch (error) {
        const errorMessage = handleApiError(error);
        setError(errorMessage);
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  useEffect(() => {
    if (selectedMachine) {
      const loadResults = async () => {
        const machineId = selectedMachine.id;
        const currentKey = `${machineId}-${selectedYear}-${selectedMonth}`;

        // 1. Check Cache for Current Month
        let currentData = resultsCache[currentKey];

        if (currentData) {
          setMonthlyResults(currentData); // Show cached data immediately while fetching fresh
          setError(null);
        }

        // Always fetch fresh data for the current view to ensure approval status is up to date
        if (!fetchingRef.current.has(currentKey)) {
          try {
            fetchingRef.current.add(currentKey);
            setError(null);
            // Fetch current month
            const data = await fetchResults(selectedMonth + 1, selectedYear, machineId);

            setMonthlyResults(data);
            setResultsCache(prev => ({
              ...prev,
              [currentKey]: data
            }));
          } catch (err) {
            // If fetch fails but we have cache, keep showing cache but maybe show a toast (omitted for now)
            // If no cache, show error
            if (!currentData) {
              const errorMessage = handleApiError(err);
              setError(errorMessage);
              setMonthlyResults(null);
            }
            console.error('Error loading results:', err);
          } finally {
            fetchingRef.current.delete(currentKey);
          }
        }

        // 2. Prefetch Neighboring Months (+/- 3 months) in background
        const neighbors: { m: number, y: number }[] = [];
        for (let i = 1; i <= 3; i++) {
          // Future
          let nextM = selectedMonth + i;
          let nextY = selectedYear;
          if (nextM > 11) {
            nextM -= 12;
            nextY += 1;
          }
          neighbors.push({ m: nextM, y: nextY });

          // Past
          let prevM = selectedMonth - i;
          let prevY = selectedYear;
          if (prevM < 0) {
            prevM += 12;
            prevY -= 1;
          }
          neighbors.push({ m: prevM, y: prevY });
        }

        neighbors.forEach(async ({ m, y }) => {
          const key = `${machineId}-${y}-${m}`;
          // Check if already in cache OR currently fetching
          if (!resultsCache[key] && !fetchingRef.current.has(key)) {
            try {
              fetchingRef.current.add(key);
              const data = await fetchResults(m + 1, y, machineId);
              setResultsCache(prev => ({
                ...prev,
                [key]: data
              }));
            } catch (e) {
              console.warn(`Failed to prefetch ${key}`, e);
            } finally {
              fetchingRef.current.delete(key);
            }
          }
        });
      };

      loadResults();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMachine, selectedMonth, selectedYear]);

  const handleGenerateReport = () => {
    setIsReportModalOpen(true);
  };

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }

    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push({ day, month, year });
    }

    return days;
  };

  const getResultsForDate = (dayObj: { day: number; month: number; year: number }): DayCheckStatus[] => {
    if (!monthlyResults) return [];

    const dateStr = `${dayObj.year}-${String(dayObj.month + 1).padStart(2, '0')}-${String(dayObj.day).padStart(2, '0')}`;
    return monthlyResults.checks.filter((check: DayCheckStatus) => {
      // Extract just the date portion (YYYY-MM-DD) from the API response which may include timestamps
      const checkDate = check.date.split('T')[0];
      return checkDate === dateStr;
    });
  };

  const handleDateClick = (dayObj: { day: number; month: number; year: number }) => {
    const results = getResultsForDate(dayObj);
    if (results) {
      const dateStr = `${dayObj.year}-${String(dayObj.month + 1).padStart(2, '0')}-${String(dayObj.day).padStart(2, '0')}`;

      const params = new URLSearchParams();
      params.set('date', dateStr);
      if (selectedMachine) {
        params.set('machineId', selectedMachine.id);
      }

      router.push(`/result-detail?${params.toString()}`);
    }
  };

  // Format helpers not needed; using month/year state directly

  const weekDays = CALENDAR_CONSTANTS.WEEK_DAYS;

  if (loading) {
    return (
      <div className="min-h-screen bg-background transition-colors">
        <Navbar user={user} />
        <main className="p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-8"></div>
            <div className="h-10 bg-gray-200 rounded w-48 mb-6"></div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background transition-colors">
      <Navbar user={user} />

      <main className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-4">
              {UI_CONSTANTS.TITLES.MPC_RESULTS}
            </h1>
            <p className="text-muted-foreground mb-6 max-w-2xl">
              {UI_CONSTANTS.PLACEHOLDERS.MPC_RESULTS_DESCRIPTION}
            </p>
          </div>
          <Button onClick={handleGenerateReport} size="lg">
            {UI_CONSTANTS.BUTTONS.GENERATE_REPORT}
          </Button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{UI_CONSTANTS.ERRORS.LOADING_DATA} {error}</p>
            <Button
              onClick={() => window.location.reload()}
              variant="ghost"
              className="mt-2 text-red-600 hover:text-red-800"
            >
              {UI_CONSTANTS.BUTTONS.RETRY}
            </Button>
          </div>
        )}

        {/* Controls */}
        <div className="mb-8 space-y-6">
          {/* Machine Selection */}
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-muted-foreground">{UI_CONSTANTS.LABELS.MACHINE}</label>
            <div className="relative">
              <Select
                value={selectedMachine?.id || ''}
                onValueChange={(val) => {
                  const machine = machines.find(m => m.id === val);
                  setSelectedMachine(machine || null);
                }}
              >
                <SelectTrigger className="w-[200px] bg-primary text-primary-foreground border-primary">
                  <SelectValue placeholder="Select Machine" />
                </SelectTrigger>
                <SelectContent>
                  {machines.map((machine) => (
                    <SelectItem key={machine.id} value={machine.id}>
                      {machine.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Month/Year Selection */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-muted-foreground">Month</label>
              <div className="relative">
                <Select
                  value={selectedMonth.toString()}
                  onValueChange={(val) => setSelectedMonth(Number(val))}
                >
                  <SelectTrigger className="w-[140px] bg-white text-foreground border-gray-300">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {monthNames.map((name, idx) => (
                      <SelectItem key={name} value={idx.toString()}>
                        {name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-muted-foreground">Year</label>
              <div className="relative">
                <Select
                  value={selectedYear.toString()}
                  onValueChange={(val) => setSelectedYear(Number(val))}
                >
                  <SelectTrigger className="w-[120px] bg-white text-foreground border-gray-300">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.from({ length: 6 }).map((_, i) => {
                      const y = today.getFullYear() - 5 + i;
                      return (
                        <SelectItem key={y} value={y.toString()}>
                          {y}
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </div>

        {/* Calendar View */}
        <div className="bg-card text-card-foreground border border-border rounded-lg p-6">
          {/* Month/Year Heading with Navigation */}
          <div className="flex justify-between items-center mb-6 px-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                if (selectedMonth === 0) {
                  setSelectedMonth(11);
                  setSelectedYear(prev => prev - 1);
                } else {
                  setSelectedMonth(prev => prev - 1);
                }
              }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-muted-foreground" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </Button>
            <h2 className="text-xl font-semibold text-foreground">
              {monthNames[selectedMonth]} {selectedYear}
            </h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                if (selectedMonth === 11) {
                  setSelectedMonth(0);
                  setSelectedYear(prev => prev + 1);
                } else {
                  setSelectedMonth(prev => prev + 1);
                }
              }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-muted-foreground" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            </Button>
          </div>

          {/* Calendar Grid or Empty State */}
          {(() => {
            const hasDataForMonth = monthlyResults && monthlyResults.checks && monthlyResults.checks.length > 0;

            if (loading && !hasDataForMonth) {
              return (
                <div className="flex items-center justify-center p-12 min-h-[400px]">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              );
            }

            if (!hasDataForMonth) {
              return (
                <div className="flex flex-col items-center justify-center p-12 min-h-[400px]">
                  <p className="text-xl text-gray-400 font-bold italic text-center">
                    No data available for this month
                  </p>
                </div>
              );
            }

            return (
              <div className="grid grid-cols-7 gap-1">
                {/* Week day headers */}
                {weekDays.map((day) => (
                  <div key={day} className="p-2 text-center text-sm font-medium text-gray-500">
                    {day}
                  </div>
                ))}

                {/* Calendar days */}
                {getDaysInMonth(new Date(selectedYear, selectedMonth, 1)).map((dayObj, index) => {
                  if (dayObj === null) {
                    return <div key={`empty-${index}`} className="p-2"></div>;
                  }

                  const results = getResultsForDate(dayObj);
                  const uniqueKey = `${dayObj.year}-${dayObj.month}-${dayObj.day}`;
                  const hasResults = results && results.length > 0;

                  return (
                    <div
                      key={uniqueKey}
                      onClick={() => hasResults && handleDateClick(dayObj)}
                      className={`p-2 min-h-[${CALENDAR_CONSTANTS.MIN_CALENDAR_HEIGHT}px] border border-gray-100 transition-colors ${hasResults
                        ? 'hover:bg-gray-50 cursor-pointer hover:border-primary'
                        : ''
                        }`}
                    >
                      <div className="text-sm font-medium text-foreground mb-1">
                        {dayObj.day}
                      </div>

                      {hasResults && (
                        <div className="space-y-1">
                          {results.map((result, rIndex) => {
                            return (
                              <div key={`${uniqueKey}-${rIndex}`} className="space-y-1 mb-1 border-b border-gray-100 last:border-0 pb-1 last:pb-0">
                                {result.geometryCheckStatus && (
                                  <div className={`text-xs px-2 py-1 rounded mb-1 ${result.geometryCheckStatus.toLowerCase() === 'fail'
                                    ? 'bg-red-100 text-red-800'
                                    : result.geometryCheckStatus.toLowerCase() === 'warning'
                                      ? 'bg-yellow-100 text-yellow-800'
                                      : result.geometryApproved
                                        ? 'bg-green-100 text-green-800'
                                        : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                    {UI_CONSTANTS.CHECKS.GEOMETRY_CHECK}
                                  </div>
                                )}
                                {result.beamCheckStatus && (
                                  <div className={`text-xs px-2 py-1 rounded ${result.beamCheckStatus.toLowerCase() === 'fail'
                                    ? 'bg-red-100 text-red-800'
                                    : result.beamCheckStatus.toLowerCase() === 'warning'
                                      ? 'bg-yellow-100 text-yellow-800'
                                      : result.beamApproved
                                        ? 'bg-green-100 text-green-800'
                                        : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                    {UI_CONSTANTS.CHECKS.BEAM_CHECK}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })()}
        </div>

        {/* Results Summary */}
        {selectedMachine && monthlyResults && (
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {UI_CONSTANTS.TITLES.RESULTS_SUMMARY} {selectedMachine.name}
            </h3>
            <div className="grid grid-cols-3 gap-4 text-sm mb-4">
              <div>
                <span className="text-muted-foreground">{UI_CONSTANTS.SUMMARY.TOTAL_CHECKS}</span>
                <span className="ml-2 font-medium">
                  {monthlyResults.checks.filter(c => c.beamCheckStatus || c.geometryCheckStatus).length}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">{UI_CONSTANTS.SUMMARY.GEOMETRY_CHECKS}</span>
                <span className="ml-2 font-medium">
                  {monthlyResults.checks.filter((c: DayCheckStatus) => c.geometryCheckStatus).length}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">{UI_CONSTANTS.SUMMARY.BEAM_CHECKS}</span>
                <span className="ml-2 font-medium">
                  {monthlyResults.checks.filter((c: DayCheckStatus) => c.beamCheckStatus).length}
                </span>
              </div>
            </div>

            {/* Legend */}
            <div className="border-t pt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Status Legend</h4>
              <div className="flex items-center space-x-6 text-sm">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                  <span>Passed & Signed Off</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                  <span>Pending Sign Off / Warning</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
                  <span>Failed</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Report Generation Modal */}
      <ReportGenerationModal
        open={isReportModalOpen}
        onOpenChange={setIsReportModalOpen}
        onSave={handleSaveReport}
        dateRange={{ from: reportStartDate, to: reportEndDate }}
        onDateRangeChange={(range) => {
          if (range?.from) {
            setReportStartDate(range.from);
            setReportEndDate(range.to || range.from);
          }
        }}
        availableChecks={availableReportChecks}
        selectedChecks={reportSelectedChecks}
        onToggleCheck={toggleReportCheck}
        onToggleAll={toggleAllReportChecks}
        onToggleGroup={(type, checked) => {
          const checksOfType = availableReportChecks.filter(c => c.type === type).map(c => c.id);
          setReportSelectedChecks(prev => {
            const next = new Set(prev);
            checksOfType.forEach(id => {
              if (checked) next.add(id);
              else next.delete(id);
            });
            return next;
          });
        }}
      />
    </div>
  );
}
