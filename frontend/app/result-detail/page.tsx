
'use client';

import { Suspense, useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { ChevronLeft, ChevronRight, CheckCircle2, XCircle } from 'lucide-react';
import { fetchUser, handleApiError, approveBeams, approveGeoChecks, fetchDocFactors, fetchBeamTypes, generateReport, getImageUrl, type DocFactor } from '../../lib/api';
import {
  Navbar,
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  // Label, // Handled by shared component
  // Checkbox, // Handled by shared component
} from '../../components/ui';
import { UI_CONSTANTS } from '../../constants';
// Hooks
import { useResultDetailData } from '../../hooks/useResultDetailData';
import { useGraphData } from '../../hooks/useGraphData';
import { mapBeamsToResults, mapGeoCheckToResults } from '../../lib/transformers/resultTransformers';
// Components
import { DateRangePicker } from '../../components/ui/date-range-picker';
import { ReportGenerationModal } from '../../components/results/ReportGenerationModal'; // Import Shared Modal
import { MetricTable } from '../../components/results/MetricTable';
import { GraphSection } from '../../components/results/GraphSection';
import { ImageViewer, type BeamImage } from '../../components/results/ImageViewer';
import { ResultHeader } from '../../components/results/ResultHeader';
import { ResultList } from '../../components/results/ResultList';
import type { CheckGroup as CheckGroupModel } from '../../models/CheckGroup';
import type { DateRange } from "react-day-picker";
import { useThresholds } from '../../lib/context/ThresholdContext';

function ResultDetailPageContent() {
  // --- State & Hooks ---
  const [user, setUser] = useState<{ id: string; name?: string; role?: string } | null>(null);
  const { thresholds } = useThresholds();
  const [docFactors, setDocFactors] = useState<DocFactor[]>([]);

  // Data Hook
  const {
    selectedDate,
    updateDate,
  } = useResultDetailData();

  // const router = useRouter(); // Unused
  const searchParams = useSearchParams();

  // Ensure machineId is available for graph (hook handles it too, but we need it here for graph hook)
  const machineId = searchParams.get('machineId') ||
    (typeof window !== 'undefined' ? sessionStorage.getItem('resultDetailMachineId') : '') || '';

  // Graph State
  const [showGraph, setShowGraph] = useState<boolean>(false);
  const [showImages, setShowImages] = useState<boolean>(false);
  const [activeBeamFilter, setActiveBeamFilter] = useState<string | null>(null);
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set());
  const [graphDateRange, setGraphDateRange] = useState<{ start: Date; end: Date }>(() => {
    // Initial range: 14 days ending on selected date
    const end = new Date(selectedDate);
    const start = new Date(selectedDate);
    start.setDate(start.getDate() - 14);
    return { start, end };
  });

  // Sync graph range end to selected date when page loads/changes
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setGraphDateRange(prev => {
      const end = new Date(selectedDate);
      const start = new Date(selectedDate);
      start.setDate(start.getDate() - 14);
      if (prev.end.getTime() === end.getTime() && prev.start.getTime() === start.getTime()) return prev;
      return { start, end };
    });
  }, [selectedDate]);

  // Graph Data (Visualization only)
  const { data: graphData } = useGraphData(graphDateRange.start, graphDateRange.end, machineId);

  // Table Data (Locked to selected date)
  const {
    beams: allBeams,
    geoChecks: allGeoChecks,
    loading: dataLoading,
    error: dataError,
    refresh
  } = useGraphData(selectedDate, selectedDate, machineId);

  // Fetch DOC factors for this machine
  useEffect(() => {
    const loadDocFactors = async () => {
      if (!machineId) return;
      try {
        const factors = await fetchDocFactors(machineId);
        setDocFactors(factors);
      } catch (err) {
        console.error('Failed to load DOC factors:', err);
      }
    };
    loadDocFactors();
  }, [machineId]);

  // Pagination State
  const [activeCheckIndex, setActiveCheckIndex] = useState(0);

  // Reset pagination when date changes
  useEffect(() => {
    setActiveCheckIndex(0);
  }, [selectedDate]);

  // Filter groups for the *selected date*
  const dailyGroups = useMemo(() => {
    if (!allBeams || allBeams.length === 0) return [];

    // allBeams is CheckGroup[] from the updated API/Hook pipe
    const groups = allBeams as unknown as CheckGroupModel[];

    const isoDate = [
      selectedDate.getFullYear(),
      String(selectedDate.getMonth() + 1).padStart(2, '0'),
      String(selectedDate.getDate()).padStart(2, '0')
    ].join('-');
    // Filter by timestamp matching the date
    return groups
      .filter(g => g.timestamp.startsWith(isoDate))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [allBeams, selectedDate]);

  // Collect images from the current check group's beams
  const currentImages: BeamImage[] = useMemo(() => {
    if (dailyGroups.length === 0) return [];
    const group = dailyGroups[activeCheckIndex];
    if (!group) return [];

    const images: BeamImage[] = [];
    for (const beam of group.beams) {
      if (beam.imagePaths && typeof beam.imagePaths === 'object') {
        for (const [label, path] of Object.entries(beam.imagePaths)) {
          images.push({
            label,
            url: getImageUrl(path),
            beamType: beam.type,
          });
        }
      }
    }
    return images;
  }, [dailyGroups, activeCheckIndex]);

  const hasImages = currentImages.length > 0;

  // Filter images for the active beam (when clicked from per-row icon)
  const displayedImages = useMemo(() => {
    if (!activeBeamFilter) return currentImages;
    // activeBeamFilter is the CheckResult id like "beam-<uuid>" or "beam-<type>-<index>"
    // Find the matching beam in the current group to get its type
    const group = dailyGroups[activeCheckIndex];
    if (!group) return currentImages;

    // Extract the beam identifier: strip "beam-" prefix
    const beamIdPart = activeBeamFilter.replace(/^beam-/, '');
    const matchingBeam = group.beams.find(b => b.id === beamIdPart || `${b.type}` === beamIdPart);
    if (!matchingBeam) return currentImages;

    return currentImages.filter(img => img.beamType === matchingBeam.type);
  }, [currentImages, activeBeamFilter, dailyGroups, activeCheckIndex]);

  // Handler for per-beam image button clicks
  const handleViewBeamImages = (checkId: string) => {
    setActiveBeamFilter(checkId);
    setShowImages(true);
    setShowGraph(false);
  };

  // Map results for the CURRENT active check group
  const beamResults = useMemo(() => {
    if (dailyGroups.length === 0) return [];
    const group = dailyGroups[activeCheckIndex];
    // fallback to first if index out of bounds (safety)
    const beams = group ? group.beams : dailyGroups[0].beams;
    return mapBeamsToResults(beams, thresholds, docFactors);
  }, [dailyGroups, activeCheckIndex, thresholds, docFactors]);


  // Determine the timestamp of the currently selected beam check group
  const activeBeamTimestamp = useMemo(() => {
    if (dailyGroups.length > 0 && dailyGroups[activeCheckIndex]) {
      // Prefer timestamp field, fallback to date if needed
      const ts = dailyGroups[activeCheckIndex].timestamp;
      return ts ? new Date(ts).getTime() : null;
    }
    return null;
  }, [dailyGroups, activeCheckIndex]);


  const dayGeoChecks = useMemo(() => {
    if (!allGeoChecks || allGeoChecks.length === 0) return [];
    const targetDateStr = [
      selectedDate.getFullYear(),
      String(selectedDate.getMonth() + 1).padStart(2, '0'),
      String(selectedDate.getDate()).padStart(2, '0')
    ].join('-');
    return allGeoChecks.filter(g =>
      (g.date && g.date.startsWith(targetDateStr)) ||
      (g.timestamp && g.timestamp.startsWith(targetDateStr))
    ).sort((a, b) => {
      const timeA = new Date(a.timestamp || a.date).getTime();
      const timeB = new Date(b.timestamp || b.date).getTime();
      return timeA - timeB;
    });
  }, [allGeoChecks, selectedDate]);

  const geoResults = useMemo(() => {
    if (dayGeoChecks.length === 0) return [];

    // 2. Sequential Matching: activeCheckIndex maps directly to the index in dayGeoChecks
    const selectedGeoCheck = dayGeoChecks[activeCheckIndex];

    if (!selectedGeoCheck) return [];

    // 3. Map the selected GeoCheck to results
    return mapGeoCheckToResults(selectedGeoCheck, thresholds);
  }, [dayGeoChecks, thresholds, activeCheckIndex]);

  // Combine for approval modal
  const reviewableItems = useMemo(() => [...beamResults, ...geoResults], [beamResults, geoResults]);

  // UI State
  const [expandedChecks, setExpandedChecks] = useState<Set<string>>(new Set(['group-beam-checks']));
  const [isSignOffModalOpen, setIsSignOffModalOpen] = useState(false);
  // Removed signOffSelectedChecks as we now approve all after viewing
  const [isApproving, setIsApproving] = useState(false);
  const [approvalCurrentIndex, setApprovalCurrentIndex] = useState(0);
  const [approvalVisitedIndices, setApprovalVisitedIndices] = useState<Set<number>>(new Set([0]));

  // Report Modal State
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportStartDate, setReportStartDate] = useState<Date>(() => new Date());
  const [reportEndDate, setReportEndDate] = useState<Date>(() => new Date());
  const [reportSelectedChecks, setReportSelectedChecks] = useState<Set<string>>(new Set());
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  // --- Effects ---
  useEffect(() => {
    fetchUser().then(setUser).catch(console.error);
    // Thresholds now handled by context
  }, []);

  // --- Handlers ---
  const toggleCheckExpand = (checkId: string) => {
    setExpandedChecks(prev => {
      const next = new Set(prev);
      if (next.has(checkId)) next.delete(checkId);
      else next.add(checkId);
      return next;
    });
  };

  const toggleMetric = (metricName: string) => {
    setSelectedMetrics(prev => {
      const next = new Set(prev);
      if (next.has(metricName)) next.delete(metricName);
      else next.add(metricName);
      return next;
    });
    setShowGraph(true);
  };

  // Graph Date Helpers
  const handleDateRangeChange = (range: DateRange | undefined) => {
    if (range?.from) {
      setGraphDateRange({
        start: range.from,
        end: range.to || range.from
      });
    }
  };

  const handleQuickDateRange = (range: string) => {
    const today = new Date(selectedDate);
    let start: Date;
    let end = new Date(today);

    switch (range) {
      case 'today': start = today; end = today; break;
      case 'yesterday':
        start = new Date(today); start.setDate(start.getDate() - 1); end = new Date(start); break;
      case 'lastWeek': start = new Date(today); start.setDate(start.getDate() - 7); break;
      case 'lastMonth': start = new Date(today); start.setMonth(start.getMonth() - 1); break;
      case 'lastQuarter': start = new Date(today); start.setMonth(start.getMonth() - 3); break;
      default: return;
    }
    setGraphDateRange({ start, end });
  };

  // --- Report Helpers ---
  // Build available report checks using type-based IDs (matching calendar page & backend)
  const [availableReportChecks, setAvailableReportChecks] = useState<{ id: string; name: string; type: 'beam' | 'geo' }[]>([]);

  useEffect(() => {
    const loadChecks = async () => {
      // Static geometry checks (same as calendar page)
      const geoChecks: { id: string; name: string; type: 'geo' }[] = [
        { id: 'geo-isocenter', name: 'IsoCenter Group', type: 'geo' },
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
      ];

      // Dynamic beam checks from API
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
          const defaults = ['6x', '6xFFF', '10x', '10xFFF', '15x', '6e', '9e', '12e', '16e', '20e'];
          beamChecks = defaults.map(t => ({ id: `beam-${t}`, name: `Beam Check (${t})`, type: 'beam' }));
        }
      } catch (e) {
        console.error('Failed to fetch beam types for report:', e);
        const defaults = ['6x', '6xFFF', '10x', '10xFFF', '15x', '6e', '9e', '12e', '16e', '20e'];
        beamChecks = defaults.map(t => ({ id: `beam-${t}`, name: `Beam Check (${t})`, type: 'beam' }));
      }

      const allChecks = [...beamChecks, ...geoChecks];
      setAvailableReportChecks(allChecks);
      setReportSelectedChecks(new Set(allChecks.map(c => c.id)));
    };

    if (isReportModalOpen) {
      loadChecks();
    }
  }, [isReportModalOpen]);

  // Helpers for Select All
  const isAllChecksSelected = availableReportChecks.length > 0 && reportSelectedChecks.size === availableReportChecks.length;

  const toggleAllReportChecks = (checked: boolean) => {
    if (checked) {
      setReportSelectedChecks(new Set(availableReportChecks.map(c => c.id)));
    } else {
      setReportSelectedChecks(new Set());
    }
  };

  const toggleReportCheck = (id: string) => {
    setReportSelectedChecks(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // --- Approval Modal Handlers ---
  const openApprovalModal = () => {
    setApprovalCurrentIndex(0);
    setApprovalVisitedIndices(new Set([0]));
    setIsSignOffModalOpen(true);
  };

  const handleNextBeam = () => {
    const nextIndex = approvalCurrentIndex + 1;
    // Iterate through reviewableItems
    if (nextIndex < reviewableItems.length) {
      setApprovalCurrentIndex(nextIndex);
      setApprovalVisitedIndices(prev => {
        const next = new Set(prev);
        next.add(nextIndex);
        return next;
      });
    }
  };

  const handlePrevBeam = () => {
    if (approvalCurrentIndex > 0) {
      setApprovalCurrentIndex(approvalCurrentIndex - 1);
    }
  };

  const handleApproveAll = async () => {
    try {
      if (!user) {
        alert("User not authenticated.");
        return;
      }

      setIsApproving(true);

      // 1. Approve Beams
      const beamsToApprove = beamResults
        .filter(b => !b.approvedBy)
        .map(b => b.id.replace('beam-', ''));

      if (beamsToApprove.length > 0) {
        await approveBeams(beamsToApprove, user.name || user.id);
      }

      // 2. Approve ALL Geo Checks for the current day
      const geoIdsToApprove = dayGeoChecks
        .filter(gc => !gc.approvedBy)
        .map(gc => gc.id);
      if (geoIdsToApprove.length > 0) {
        await approveGeoChecks(geoIdsToApprove, user.name || user.id);
      }

      setIsSignOffModalOpen(false);
      refresh();
    } catch (err) {
      console.error("Approve failed", err);
      alert(handleApiError(err));
    } finally {
      setIsApproving(false);
    }
  };

  const handleGenerateReport = () => {
    setReportStartDate(new Date(selectedDate));
    setReportEndDate(new Date(selectedDate));
    setIsReportModalOpen(true);
  };

  const handleSaveReport = async () => {
    if (!machineId) return;

    try {
      setIsGeneratingReport(true);

      // Create a local date string YYYY-MM-DD
      const formatDateStr = (d: Date) => {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      // Single day — use selectedDate for both start and end
      const dateStr = formatDateStr(selectedDate);

      const blob = await generateReport({
        startDate: dateStr,
        endDate: dateStr,
        machineId: machineId,
        selectedChecks: Array.from(reportSelectedChecks)
      });

      // Determine correct extension based on response content type
      const isZip = blob.type === 'application/zip' || blob.type === 'application/x-zip-compressed';
      const ext = isZip ? 'zip' : 'pdf';
      const fileName = `MPC_Report_${machineId}_${dateStr}.${ext}`;

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
      alert('Failed to generate report: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const getAllAvailableMetrics = (): string[] => {
    const metricsSet = new Set<string>();
    [...beamResults, ...geoResults].forEach(check => {
      check.metrics.forEach(metric => {
        if (!metric.name.includes('Leaf')) metricsSet.add(metric.name);
      });
    });
    return Array.from(metricsSet).sort();
  };

  // --- Render Helpers ---


  const formatDate = (date: Date): string => {
    if (!date || isNaN(date.getTime())) return '';
    return date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
  };



  return (
    <div className="min-h-screen bg-background transition-colors">
      <Navbar user={user} />
      <main className="p-6 max-w-7xl mx-auto">
        <ResultHeader
          selectedDate={selectedDate}
          onGenerateReport={handleGenerateReport}
          onApprove={openApprovalModal}
          onToggleGraph={() => {
            setShowGraph(prev => {
              const next = !prev;
              if (next) setShowImages(false);
              return next;
            });
          }}
          showGraph={showGraph}
          onToggleImages={() => {
            setShowImages(prev => {
              const next = !prev;
              if (next) {
                setShowGraph(false);
                setActiveBeamFilter(null); // Show all images when toggled from header
              }
              return next;
            });
          }}
          showImages={showImages}
          hasImages={true}
          availableReportChecks={availableReportChecks}
          beamResults={beamResults}
          // Pagination
          checkCount={dailyGroups.length}
          currentCheckIndex={activeCheckIndex}
          onPrevCheck={() => setActiveCheckIndex(prev => Math.max(0, prev - 1))}
          onNextCheck={() => setActiveCheckIndex(prev => Math.min(dailyGroups.length - 1, prev + 1))}
          currentCheckTimestamp={dailyGroups[activeCheckIndex]?.timestamp}
        />

        {dataError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
            {UI_CONSTANTS.ERRORS.LOADING_DATA} {dataError}
          </div>
        )}

        <div className={`grid gap-8 mt-8 ${(showGraph || showImages) ? 'grid-cols-1 lg:grid-cols-[30%_70%]' : 'grid-cols-1'}`}>
          <ResultList
            beamResults={beamResults}
            geoResults={geoResults}
            expandedChecks={expandedChecks}
            toggleCheckExpand={toggleCheckExpand}
            selectedMetrics={selectedMetrics}
            toggleMetric={toggleMetric}
            dataLoading={dataLoading}
            onViewBeamImages={handleViewBeamImages}
          />

          {/* Graph Column */}
          {showGraph && (
            <div className="space-y-6">
              <GraphSection
                data={graphData}
                selectedMetrics={selectedMetrics}
                onToggleMetric={toggleMetric}
                onClearMetrics={() => setSelectedMetrics(new Set())}
                onClose={() => setShowGraph(false)}
                availableMetrics={getAllAvailableMetrics()}
              />
              {/* Quick Dates */}
              <div className="mb-4 border border-gray-200 rounded-lg p-4">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex gap-2">
                    {['lastWeek', 'lastMonth', 'lastQuarter'].map((rangeType) => (
                      <Button
                        key={rangeType}
                        variant="ghost"
                        size="sm"
                        onClick={() => handleQuickDateRange(rangeType)}
                        className="hover:text-primary hover:bg-primary/10"
                      >
                        {rangeType.replace('last', 'Last ')}
                      </Button>
                    ))}
                  </div>
                  <DateRangePicker
                    date={{ from: graphDateRange.start, to: graphDateRange.end }}
                    setDate={handleDateRangeChange}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Images Column */}
          {showImages && (
            <div className="space-y-6">
              <ImageViewer
                images={displayedImages}
                onClose={() => {
                  setShowImages(false);
                  setActiveBeamFilter(null);
                }}
              />
            </div>
          )}
        </div>
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
        disableDateSelection={true}
      />

      {/* Sign Off Modal (Paginated) */}
      <Dialog open={isSignOffModalOpen} onOpenChange={setIsSignOffModalOpen}>
        <DialogContent className="sm:max-w-[700px] h-[600px] flex flex-col">
          <DialogHeader>
            <DialogTitle>Approve Results ({approvalCurrentIndex + 1} of {reviewableItems.length})</DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto py-4">
            {reviewableItems.length > 0 && (() => {
              const currentItem = reviewableItems[approvalCurrentIndex];
              // Safe check for data consistency during updates/modal transitions
              if (!currentItem) return null;

              const isPass = currentItem.status === 'PASS';
              return (
                <div className="space-y-6">
                  <div className="flex items-center justify-between border-b pb-4">
                    <div>
                      <h3 className="text-xl font-semibold">{currentItem.name}</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        Review data carefully before approving.
                      </p>
                    </div>
                    <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${isPass ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {isPass ? <CheckCircle2 className="w-4 h-4 mr-1.5" /> : <XCircle className="w-4 h-4 mr-1.5" />}
                      {currentItem.status}
                    </div>
                  </div>

                  {/* Reusing MetricTable logic but inline or we can just render the component */}
                  <div className="border rounded-lg overflow-hidden">
                    <MetricTable
                      metrics={currentItem.metrics}
                      selectedMetrics={new Set()}
                      onToggleMetric={() => { }} // No graphing in modal
                      showAbsolute={currentItem.id.startsWith('beam-')}
                    />
                  </div>
                </div>
              );
            })()}
            {reviewableItems.length === 0 && <div className="text-center text-muted-foreground mt-10">No results to show.</div>}
          </div>

          <DialogFooter className="flex items-center justify-between sm:justify-between w-full mt-auto border-t pt-4">
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handlePrevBeam}
                disabled={approvalCurrentIndex === 0}
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Previous
              </Button>
              <Button
                variant="outline"
                onClick={handleNextBeam}
                disabled={approvalCurrentIndex === reviewableItems.length - 1}
              >
                Next
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>

            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setIsSignOffModalOpen(false)}>Cancel</Button>
              <Button
                onClick={handleApproveAll}
                disabled={isApproving || approvalVisitedIndices.size < reviewableItems.length}
                variant={approvalVisitedIndices.size < reviewableItems.length ? "secondary" : "default"}
              >
                {isApproving ? 'Approving...' : 'Approve All'}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function ResultDetailPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading...</div>}>
      <ResultDetailPageContent />
    </Suspense>
  );
}
