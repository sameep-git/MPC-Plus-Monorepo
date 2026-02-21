import React from 'react';
import { Button } from '../ui';
import { UI_CONSTANTS } from '../../constants';
import { ChevronLeft, ChevronRight, LineChart as ChartIcon, Image as ImageIcon } from 'lucide-react';
import type { CheckResult } from '../../models/CheckResult';

interface ResultHeaderProps {
    selectedDate: Date;
    onGenerateReport: () => void;
    onApprove: () => void;
    onToggleGraph: () => void;
    showGraph: boolean;
    onToggleImages: () => void;
    showImages: boolean;
    hasImages: boolean;
    availableReportChecks: { id: string; name: string; type: string }[];
    beamResults: CheckResult[];
    // Pagination Props
    checkCount: number;
    currentCheckIndex: number;
    onPrevCheck: () => void;
    onNextCheck: () => void;
    currentCheckTimestamp?: string;
}

export const ResultHeader: React.FC<ResultHeaderProps> = ({
    selectedDate,
    onGenerateReport,
    onApprove,
    onToggleGraph,
    showGraph,
    onToggleImages,
    showImages,
    hasImages,
    availableReportChecks,
    beamResults,
    checkCount,
    currentCheckIndex,
    onPrevCheck,
    onNextCheck,
    currentCheckTimestamp
}) => {
    const formatDate = (date: Date): string => {
        if (!date || isNaN(date.getTime())) return '';
        return date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
    };

    return (
        <div className="mb-6">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h1 className="text-4xl font-bold text-foreground">
                        MPC Results for {formatDate(selectedDate)}
                    </h1>
                    <p className="text-muted-foreground mt-2 max-w-2xl">
                        {UI_CONSTANTS.PLACEHOLDERS.MPC_RESULTS_DESCRIPTION}
                    </p>
                </div>


            </div>

            <div className="flex items-center w-full gap-4 flex-wrap">
                <Button
                    variant="outline"
                    size="lg"
                    onClick={onGenerateReport}
                    className="text-muted-foreground border-gray-300 hover:bg-primary/10 hover:text-primary hover:border-primary/30"
                >
                    {UI_CONSTANTS.BUTTONS.GENERATE_DAILY_REPORT}
                </Button>



                {(() => {
                    // Check if ALL displayed beams are accepted
                    const hasBeams = beamResults.length > 0;
                    const allAccepted = hasBeams && beamResults.every(b => !!b.approvedBy);

                    if (allAccepted) {
                        const firstAccepted = beamResults[0];
                        const formatTime = (d?: string) => {
                            if (!d) return '';
                            const utc = d.endsWith('Z') ? d : `${d}Z`;
                            return new Date(utc).toLocaleString();
                        };
                        const timestamp = formatTime(firstAccepted?.approvedDate);
                        return (
                            <div className="flex items-center px-4 py-2 bg-green-50 text-green-700 border border-green-200 rounded-md text-sm italic h-11">
                                Approved by {firstAccepted?.approvedBy} on {timestamp}
                            </div>
                        );
                    }

                    return (
                        <Button
                            onClick={onApprove}
                            size="lg"
                            variant="default"
                        >
                            Approve Results
                        </Button>
                    );
                })()}

                <Button
                    onClick={onToggleGraph}
                    size="lg"
                    variant={showGraph ? "secondary" : "outline"}
                    className={showGraph
                        ? "bg-primary/10 text-primary border-primary/20 hover:bg-primary/20"
                        : "text-muted-foreground border-gray-300 hover:bg-gray-50 hover:text-primary hover:border-primary/30"}
                >
                    Graph
                    <ChartIcon className={`ml-2 h-5 w-5 ${showGraph ? 'text-primary' : 'text-gray-500 group-hover:text-primary'}`} />
                </Button>

                {hasImages && (
                    <Button
                        onClick={onToggleImages}
                        size="lg"
                        variant={showImages ? "secondary" : "outline"}
                        className={showImages
                            ? "bg-primary/10 text-primary border-primary/20 hover:bg-primary/20"
                            : "text-muted-foreground border-gray-300 hover:bg-gray-50 hover:text-primary hover:border-primary/30"}
                    >
                        Images
                        <ImageIcon className={`ml-2 h-5 w-5 ${showImages ? 'text-primary' : 'text-gray-500 group-hover:text-primary'}`} />
                    </Button>
                )}
                {/* Pagination Controls */}
                {checkCount > 1 && (
                    <div className="flex items-center bg-white border rounded-lg p-0.5 shadow-sm h-10">
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            disabled={currentCheckIndex === 0}
                            onClick={onPrevCheck}
                            className="h-9 w-9"
                        >
                            <ChevronLeft className="w-4 h-4" />
                        </Button>
                        <div className="flex flex-col items-center px-2 min-w-[100px] leading-tight">
                            <span className="font-semibold text-xs">
                                Check {currentCheckIndex + 1} of {checkCount}
                            </span>
                            {currentCheckTimestamp && (
                                <span className="text-[10px] text-muted-foreground">
                                    {(() => {
                                        const utc = currentCheckTimestamp.endsWith('Z') ? currentCheckTimestamp : `${currentCheckTimestamp}Z`;
                                        return new Date(utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                                    })()}
                                </span>
                            )}
                        </div>
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            disabled={currentCheckIndex === checkCount - 1}
                            onClick={onNextCheck}
                            className="h-9 w-9"
                        >
                            <ChevronRight className="w-4 h-4" />
                        </Button>
                    </div>
                )}
            </div>
        </div>

    );
};
