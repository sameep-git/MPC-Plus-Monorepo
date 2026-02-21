import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow, Button } from '../../components/ui';
import { LineChart as ChartIcon } from 'lucide-react';
import type { CheckMetric } from '../../models/CheckResult';
import { formatMetricValue } from '../../lib/transformers/resultTransformers';

interface MetricTableProps {
    metrics: CheckMetric[];
    selectedMetrics: Set<string>;
    onToggleMetric: (metricName: string) => void;
    showAbsolute?: boolean;
}

export const MetricTable: React.FC<MetricTableProps> = ({
    metrics,
    selectedMetrics,
    onToggleMetric,
    showAbsolute = false,
}) => {
    return (
        <div className="p-3 overflow-x-auto">
            <Table className="table-fixed w-full">
                <TableHeader>
                    <TableRow>
                        <TableHead className={showAbsolute ? 'w-[40%]' : 'w-1/2'}>Metric</TableHead>
                        <TableHead className={`${showAbsolute ? 'w-[20%]' : 'w-1/4'} text-right`}>Value</TableHead>
                        <TableHead className={`${showAbsolute ? 'w-[20%]' : 'w-1/4'} text-right`}>Threshold</TableHead>
                        {showAbsolute && <TableHead className="w-[20%] text-right">Abs</TableHead>}
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {metrics.map((m, idx) => (
                        <TableRow
                            key={m.name}
                            className={m.status === 'fail' ? 'bg-red-50 hover:bg-red-100' : m.status === 'warning' ? 'bg-yellow-50 hover:bg-yellow-100' : ''}
                        >
                            <TableCell className="font-medium">
                                <div className="flex items-center gap-2">
                                    {m.status === 'pass' && <div className="w-2 h-2 rounded-full bg-green-500" />}
                                    {m.status === 'fail' && <div className="w-2 h-2 rounded-full bg-red-500" />}
                                    {m.status === 'warning' && <div className="w-2 h-2 rounded-full bg-yellow-500" />}
                                    {m.name}
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-4 w-4"
                                        aria-label={`Toggle ${m.name} graph`}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onToggleMetric(m.name);
                                        }}
                                    >
                                        <ChartIcon
                                            className={`w-3 h-3 ${selectedMetrics.has(m.name) ? 'text-primary' : 'text-gray-400'}`}
                                        />
                                    </Button>
                                </div>
                            </TableCell>
                            <TableCell className="text-right">{formatMetricValue(m.name, m.value)}</TableCell>
                            <TableCell className="text-right text-muted-foreground text-sm">{m.thresholds || '-'}</TableCell>
                            {showAbsolute && <TableCell className="text-right">{m.absoluteValue || '-'}</TableCell>}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
};
