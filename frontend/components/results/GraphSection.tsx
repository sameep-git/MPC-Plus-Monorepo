import React, { useMemo } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceArea,
    ReferenceLine
} from 'recharts';
import { ChevronDown, X, Eraser } from 'lucide-react';
import {
    Button,
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuTrigger,
    DropdownMenuCheckboxItem,
    Card,
} from '../../components/ui';
import { GRAPH_CONSTANTS } from '../../constants';
import { getSettings } from '../../lib/settings';
import { getDefaultDomainForMetric } from '../../lib/services/graphService';
import { getMetricKey } from '../../lib/transformers/resultTransformers';
import type { GraphDataPoint } from '../../models/Graph';
import { generateGraphData } from '../../lib/services/graphService';

interface GraphSectionProps {
    data: GraphDataPoint[];
    selectedMetrics: Set<string>;
    onToggleMetric: (metricName: string) => void;
    onClearMetrics: () => void;
    onClose: () => void;
    availableMetrics: string[];
}

export const GraphSection: React.FC<GraphSectionProps> = ({
    data,
    selectedMetrics,
    onToggleMetric,
    onClearMetrics,
    onClose,
    availableMetrics,
}) => {
    // Local state for settings provided here for simplicity, or passed as props if needed to shift up
    // In the original file, these were state in Page. For now, we'll read direct or use props.
    // To avoid prop drilling hell, reading settings directly here is acceptable if they are global/local storage based.
    // However, Page had effects on focus to refresh settings.
    // Let's assume settings don't change often while graph is open or simple read is enough.

    const graphThresholdSettings = useMemo(() => {
        const s = getSettings();
        return {
            topPercent: s.graphThresholdTopPercent ?? GRAPH_CONSTANTS.DEFAULT_THRESHOLD_PERCENT,
            bottomPercent: s.graphThresholdBottomPercent ?? GRAPH_CONSTANTS.DEFAULT_THRESHOLD_PERCENT,
            color: s.graphThresholdColor ?? GRAPH_CONSTANTS.DEFAULT_THRESHOLD_COLOR,
        };
    }, []);

    const baselineSettings = useMemo(() => getSettings().baseline, []);

    // Baseline Computation Logic (Migrated from Page)
    const baselineComputation = useMemo(() => {
        const valuesByMetric: Record<string, number | null> = {};
        let baselineDateInRange = false;
        let baselineDataPoint: GraphDataPoint | undefined;

        if (baselineSettings.mode === 'date' && baselineSettings.date) {
            baselineDataPoint = data.find((point) => point.fullDate === baselineSettings.date);
            baselineDateInRange = Boolean(baselineDataPoint);

            if (!baselineDataPoint && selectedMetrics.size > 0) {
                const baselineDate = new Date(baselineSettings.date);
                if (!Number.isNaN(baselineDate.getTime())) {
                    // Using generic generator if point missing
                    const fallbackData = generateGraphData(baselineDate, baselineDate, selectedMetrics);
                    baselineDataPoint = fallbackData[0];
                }
            }
        }

        const { manualValues } = baselineSettings;

        Array.from(selectedMetrics).forEach((metricName) => {
            const key = getMetricKey(metricName);
            let baselineValue: number | null = null;
            const lowerMetric = metricName.toLowerCase();

            if (baselineSettings.mode === 'manual') {
                if (lowerMetric.includes('output change')) baselineValue = manualValues.outputChange;
                else if (lowerMetric.includes('uniformity change')) baselineValue = manualValues.uniformityChange;
                else if (lowerMetric.includes('center shift')) baselineValue = manualValues.centerShift;
                else baselineValue = 0;
            } else if (baselineSettings.mode === 'date' && baselineDataPoint) {
                const candidate = baselineDataPoint[key];
                baselineValue = typeof candidate === 'number' ? candidate : null;
            }

            valuesByMetric[key] = baselineValue;
        });

        const hasNumericBaseline = Object.values(valuesByMetric).some(
            (value) => typeof value === 'number'
        );

        return {
            valuesByMetric,
            hasNumericBaseline,
            baselineDateInRange,
            requestedDate: baselineSettings.date,
        };
    }, [baselineSettings, data, selectedMetrics]);

    const chartData = useMemo(() => {
        if (!baselineComputation.hasNumericBaseline) {
            return data;
        }

        return data.map((point) => {
            const nextPoint: GraphDataPoint = { ...point };

            Object.entries(baselineComputation.valuesByMetric).forEach(([key, baselineValue]) => {
                if (typeof baselineValue === 'number') {
                    const rawValue = point[key];
                    if (typeof rawValue === 'number') {
                        nextPoint[key] = Number((rawValue - baselineValue).toFixed(3));
                    }
                }
            });

            return nextPoint;
        });
    }, [data, baselineComputation]);

    const yAxisDomain = useMemo<[number, number]>(() => {
        if (selectedMetrics.size === 0) return GRAPH_CONSTANTS.Y_AXIS_DOMAINS.DEFAULT as [number, number];

        const metrics = Array.from(selectedMetrics);
        let domainMin = Number.POSITIVE_INFINITY;
        let domainMax = Number.NEGATIVE_INFINITY;

        metrics.forEach((metricName) => {
            const [defaultMin, defaultMax] = getDefaultDomainForMetric(metricName);
            domainMin = Math.min(domainMin, defaultMin);
            domainMax = Math.max(domainMax, defaultMax);
        });

        if (!Number.isFinite(domainMin) || !Number.isFinite(domainMax)) {
            return GRAPH_CONSTANTS.Y_AXIS_DOMAINS.DEFAULT as [number, number];
        }

        chartData.forEach((point) => {
            metrics.forEach((metricName) => {
                const key = getMetricKey(metricName);
                const value = point[key];
                if (typeof value === 'number' && !Number.isNaN(value)) {
                    domainMin = Math.min(domainMin, value);
                    domainMax = Math.max(domainMax, value);
                }
            });
        });

        if (!Number.isFinite(domainMin) || !Number.isFinite(domainMax)) {
            return GRAPH_CONSTANTS.Y_AXIS_DOMAINS.DEFAULT as [number, number];
        }

        if (domainMin === domainMax) {
            const padding = Math.max(Math.abs(domainMin) * 0.1, 0.5);
            return [domainMin - padding, domainMax + padding];
        }

        return [domainMin, domainMax];
    }, [chartData, selectedMetrics]);


    const { topThreshold, bottomThreshold, min: thresholdMin, max: thresholdMax } = useMemo(() => {
        const [min, max] = yAxisDomain;
        const range = max - min;

        if (range <= 0) {
            return {
                topThreshold: max,
                bottomThreshold: min,
                min,
                max,
            };
        }

        const topThreshold = max - (range * graphThresholdSettings.topPercent) / 100;
        const bottomThreshold = min + (range * graphThresholdSettings.bottomPercent) / 100;

        return { topThreshold, bottomThreshold, min, max };
    }, [graphThresholdSettings.bottomPercent, graphThresholdSettings.topPercent, yAxisDomain]);

    const getMetricColor = (index: number): string => {
        return GRAPH_CONSTANTS.METRIC_COLORS[index % GRAPH_CONSTANTS.METRIC_COLORS.length];
    };

    const baselineSummary = useMemo(() => {
        if (baselineSettings.mode === 'date') {
            if (!baselineSettings.date) {
                return {
                    message: 'Select a baseline date in Settings to see changes relative to that day.',
                    tone: 'muted' as const,
                };
            }

            if (selectedMetrics.size > 0) {
                if (baselineComputation.baselineDateInRange) {
                    return {
                        message: `Baseline from ${baselineSettings.date}. Values display Δ relative to that day.`,
                        tone: 'info' as const,
                    };
                }

                return {
                    message: `Baseline from ${baselineSettings.date}. Values display Δ relative to that day even though it falls outside the visible range.`,
                    tone: 'info' as const,
                };
            }

            return {
                message: `Baseline from ${baselineSettings.date}. Select metrics to view deltas relative to that day.`,
                tone: 'muted' as const,
            };
        }

        const { manualValues } = baselineSettings;
        return {
            message: `Baseline uses manual values — Output ${manualValues.outputChange}, Uniformity ${manualValues.uniformityChange}, Center Shift ${manualValues.centerShift}.`,
            tone: 'info' as const,
        };
    }, [baselineSettings, baselineComputation.baselineDateInRange, selectedMetrics.size]);

    const getBaselineBannerClasses = () => {
        const tone = baselineSummary.tone as string;
        switch (tone) {
            case 'warning':
                return 'bg-amber-50 border-amber-200 text-amber-700';
            case 'info':
                return 'bg-blue-50 border-blue-200 text-blue-700';
            default:
                return 'bg-gray-50 border-gray-200 text-muted-foreground';
        }
    };

    return (
        <Card className="p-4 gap-4">
            {/* Graph Header */}
            <div className="mb-4 flex items-center gap-2">
                <div className="relative metric-dropdown-container">
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button
                                variant="outline"
                                className="w-64 flex items-center justify-between"
                            >
                                <span className="truncate">
                                    {selectedMetrics.size === 0
                                        ? 'Select metrics...'
                                        : `${selectedMetrics.size} metric${selectedMetrics.size > 1 ? 's' : ''} selected`}
                                </span>
                                <ChevronDown className="w-4 h-4 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-64 max-h-60 overflow-y-auto" align="start">
                            {availableMetrics.length > 0 ? (
                                availableMetrics.map((metric) => (
                                    <DropdownMenuCheckboxItem
                                        key={metric}
                                        checked={selectedMetrics.has(metric)}
                                        onCheckedChange={() => onToggleMetric(metric)}
                                        onSelect={(e) => e.preventDefault()}
                                    >
                                        {metric}
                                    </DropdownMenuCheckboxItem>
                                ))
                            ) : (
                                <div className="px-2 py-2 text-sm text-gray-500">No metrics available</div>
                            )}
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>

                {selectedMetrics.size > 0 && (
                    <Button
                        onClick={onClearMetrics}
                        variant="ghost"
                        size="sm"
                        className="text-muted-foreground hover:text-red-600 hover:bg-red-50"
                    >
                        <Eraser className="w-4 h-4 mr-2" />
                        Clear All Metrics
                    </Button>
                )}

                <div className="ml-auto">
                    <Button
                        onClick={onClose}
                        variant="ghost"
                        size="icon"
                        title="Close graph"
                        aria-label="Close graph"
                    >
                        <X className="w-5 h-5" />
                    </Button>
                </div>
            </div>

            {baselineSummary && (
                <div className={`mb-4 px-4 py-3 border rounded-lg text-sm ${getBaselineBannerClasses()}`}>
                    {baselineSummary.message}
                    {(baselineSummary.tone as string) === 'warning' && (
                        <span className="ml-1">
                            Adjust ranges or update the baseline in Settings.
                        </span>
                    )}
                </div>
            )}

            {/* Graph */}
            <div className="h-96 mb-4">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                            dataKey="date"
                            stroke="#6b7280"
                            style={{ fontSize: '12px' }}
                        />
                        <YAxis
                            domain={yAxisDomain}
                            stroke="#6b7280"
                            style={{ fontSize: '12px' }}
                            tickFormatter={(value: number) => value.toFixed(3)}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'white',
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px'
                            }}
                            formatter={(value: number) => value.toFixed(3)}
                        />
                        <>
                            {/* Top threshold shading */}
                            <ReferenceArea
                                y1={topThreshold}
                                y2={thresholdMax}
                                fill={graphThresholdSettings.color}
                                fillOpacity={0.3}
                            />
                            {/* Bottom threshold shading */}
                            <ReferenceArea
                                y1={thresholdMin}
                                y2={bottomThreshold}
                                fill={graphThresholdSettings.color}
                                fillOpacity={0.3}
                            />
                        </>
                        {baselineComputation.hasNumericBaseline && (
                            <ReferenceLine
                                y={0}
                                stroke="#1f2937"
                                strokeWidth={2}
                                strokeDasharray="4 4"
                                label={{
                                    value: 'Baseline',
                                    position: 'right',
                                    fill: '#1f2937',
                                    fontSize: 12,
                                }}
                            />
                        )}
                        {Array.from(selectedMetrics).map((metricName, index) => {
                            const dataKey = getMetricKey(metricName);
                            const color = getMetricColor(index);
                            return (
                                <Line
                                    key={metricName}
                                    type="monotone"
                                    dataKey={dataKey}
                                    stroke={color}
                                    strokeWidth={3}
                                    dot={{ r: 5 }}
                                    name={metricName}
                                    activeDot={{ r: 7 }}
                                />
                            );
                        })}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </Card>
    );
};
