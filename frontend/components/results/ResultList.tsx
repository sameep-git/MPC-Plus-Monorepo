import React from 'react';
import { Button } from '../ui';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { CheckGroup } from './CheckGroup';
import { MetricTable } from './MetricTable';
import type { CheckResult } from '../../models/CheckResult';
import type { CheckGroup as CheckGroupModel } from '../../models/CheckGroup';

interface ResultListProps {
    beamResults: CheckResult[];
    geoResults: CheckResult[];
    expandedChecks: Set<string>;
    toggleCheckExpand: (id: string) => void;
    selectedMetrics: Set<string>;
    toggleMetric: (metricName: string) => void;
    dataLoading: boolean;
    onViewBeamImages?: (checkId: string) => void;
}

export const ResultList: React.FC<ResultListProps> = ({
    beamResults,
    geoResults,
    expandedChecks,
    toggleCheckExpand,
    selectedMetrics,
    toggleMetric,
    dataLoading,
    onViewBeamImages
}) => {

    const renderBeamSection = () => (
        <CheckGroup
            id="group-beam-checks"
            title="Beam Checks"
            isExpanded={expandedChecks.has('group-beam-checks')}
            onToggle={toggleCheckExpand}
            className="border border-gray-200 rounded-lg overflow-hidden bg-white"
        >
            <div className="p-2 space-y-2">
                {dataLoading ? (
                    <div className="flex justify-center items-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    <>
                        {beamResults.map(check => (
                            <CheckGroup
                                key={check.id}
                                id={check.id}
                                title={check.name}
                                status={check.status}
                                isExpanded={expandedChecks.has(check.id)}
                                onToggle={toggleCheckExpand}
                                hasImages={!!(check.imagePaths && Object.keys(check.imagePaths).length > 0)}
                                onViewImages={onViewBeamImages}
                            >
                                <MetricTable
                                    metrics={check.metrics}
                                    selectedMetrics={selectedMetrics}
                                    onToggleMetric={toggleMetric}
                                    showAbsolute={true}
                                />
                            </CheckGroup>
                        ))}
                        {beamResults.length === 0 && <div className="p-4 text-muted-foreground text-sm">No beam checks found.</div>}
                    </>
                )}
            </div>
        </CheckGroup>
    );

    const renderGeoSection = () => (
        <CheckGroup
            id="group-geo-checks"
            title="Geometry Checks"
            isExpanded={expandedChecks.has('group-geo-checks')}
            onToggle={toggleCheckExpand}
            className="border border-gray-200 rounded-lg overflow-hidden bg-white"
        >
            <div className="p-2 space-y-2">
                {dataLoading ? (
                    <div className="flex justify-center items-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    <>
                        {geoResults.length === 0 ? (
                            <div className="p-4 text-muted-foreground text-sm text-center">
                                No geometry checks available for this timestamp.
                            </div>
                        ) : (
                            <>
                                {/* Simple Groups */}
                                {['geo-isocenter', 'geo-collimation', 'geo-gantry', 'geo-couch', 'geo-jaws', 'geo-jaws-parallelism', 'geo-mlc-offsets'].map(id => {
                                    const check = geoResults.find(c => c.id === id);
                                    if (!check) return null;
                                    return (
                                        <CheckGroup
                                            key={check.id}
                                            id={check.id}
                                            title={check.name}
                                            status={check.status}
                                            isExpanded={expandedChecks.has(check.id)}
                                            onToggle={toggleCheckExpand}
                                        >
                                            <MetricTable
                                                metrics={check.metrics}
                                                selectedMetrics={selectedMetrics}
                                                onToggleMetric={toggleMetric}
                                            />
                                        </CheckGroup>
                                    );
                                })}

                                {/* Nested Groups: MLC Leaves */}
                                {geoResults.some(c => c.id.includes('geo-mlc-')) && (
                                    <CheckGroup
                                        id="geo-mlc-leaves-group"
                                        title="MLC Leaves"
                                        isExpanded={expandedChecks.has('geo-mlc-leaves-group')}
                                        onToggle={toggleCheckExpand}
                                    >
                                        <div className="pl-2 space-y-2 pt-2">
                                            {['geo-mlc-a', 'geo-mlc-b'].map(id => {
                                                const check = geoResults.find(c => c.id === id);
                                                if (!check) return null;
                                                return (
                                                    <CheckGroup
                                                        key={check.id}
                                                        id={check.id}
                                                        title={check.name}
                                                        status={check.status}
                                                        isExpanded={expandedChecks.has(check.id)}
                                                        onToggle={toggleCheckExpand}
                                                    >
                                                        <MetricTable metrics={check.metrics} selectedMetrics={selectedMetrics} onToggleMetric={toggleMetric} />
                                                    </CheckGroup>
                                                );
                                            })}
                                        </div>
                                    </CheckGroup>
                                )}

                                {/* Nested Groups: Backlash Leaves */}
                                {geoResults.some(c => c.id.includes('geo-backlash-')) && (
                                    <CheckGroup
                                        id="geo-backlash-group"
                                        title="Backlash Leaves"
                                        isExpanded={expandedChecks.has('geo-backlash-group')}
                                        onToggle={toggleCheckExpand}
                                    >
                                        <div className="pl-2 space-y-2 pt-2">
                                            {['geo-backlash-a', 'geo-backlash-b'].map(id => {
                                                const check = geoResults.find(c => c.id === id);
                                                if (!check) return null;
                                                return (
                                                    <CheckGroup
                                                        key={check.id}
                                                        id={check.id}
                                                        title={check.name}
                                                        status={check.status}
                                                        isExpanded={expandedChecks.has(check.id)}
                                                        onToggle={toggleCheckExpand}
                                                    >
                                                        <MetricTable metrics={check.metrics} selectedMetrics={selectedMetrics} onToggleMetric={toggleMetric} />
                                                    </CheckGroup>
                                                );
                                            })}
                                        </div>
                                    </CheckGroup>
                                )}
                            </>
                        )}
                    </>
                )}
            </div>
        </CheckGroup>
    );

    return (
        <div className="space-y-4">
            {renderBeamSection()}
            {renderGeoSection()}
        </div>
    );
};
