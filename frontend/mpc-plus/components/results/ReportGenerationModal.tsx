import React, { useMemo } from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
    Button,
    Label,
    Checkbox
} from '../ui';
import { DateRangePicker } from '../ui/date-range-picker';
import { DateRange } from 'react-day-picker';

interface ReportGenerationModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSave: () => void;
    dateRange: { from: Date; to: Date };
    onDateRangeChange: (range: DateRange | undefined) => void;
    availableChecks: { id: string; name: string; type: 'beam' | 'geo' }[];
    selectedChecks: Set<string>;
    onToggleCheck: (id: string) => void;
    onToggleAll: (checked: boolean) => void;
    onToggleGroup: (type: 'beam' | 'geo', checked: boolean) => void;
    disableDateSelection?: boolean;
}

export const ReportGenerationModal: React.FC<ReportGenerationModalProps> = ({
    open,
    onOpenChange,
    onSave,
    dateRange,
    onDateRangeChange,
    availableChecks,
    selectedChecks,
    onToggleCheck,
    onToggleAll,
    onToggleGroup,
    disableDateSelection = false
}) => {
    const isAllSelected = availableChecks.length > 0 && selectedChecks.size === availableChecks.length;

    const renderCheckGroup = (type: 'beam' | 'geo', title: string) => {
        const checks = availableChecks.filter(c => c.type === type);
        if (checks.length === 0) return null;

        const isGroupSelected = checks.every(c => selectedChecks.has(c.id));
        const isGroupIndeterminate = checks.some(c => selectedChecks.has(c.id)) && !isGroupSelected;

        return (
            <div>
                <div className="flex items-center justify-between sticky top-0 bg-white z-10 py-1 px-2 border-b mb-2">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                        {title}
                    </div>
                    <div className="flex items-center space-x-2">
                        {/* Group Select Checkbox */}
                        <Checkbox
                            id={`group-select-${type}`}
                            checked={isGroupSelected ? true : isGroupIndeterminate ? 'indeterminate' : false}
                            onCheckedChange={(c) => onToggleGroup(type, c as boolean)}
                        />
                    </div>
                </div>
                <div className="space-y-1 px-2">
                    {checks.map((check) => (
                        <div key={check.id} className="flex items-center space-x-2 p-1 hover:bg-gray-50 rounded">
                            <Checkbox
                                id={`report-${check.id}`}
                                checked={selectedChecks.has(check.id)}
                                onCheckedChange={() => onToggleCheck(check.id)}
                            />
                            <label
                                htmlFor={`report-${check.id}`}
                                className="text-sm cursor-pointer w-full"
                            >
                                {check.name}
                            </label>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Generate Report</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    {/* Date Range Selection */}
                    <div className="space-y-2">
                        <Label>Date/Range</Label>
                        {disableDateSelection ? (
                            <div className="w-full p-2 border rounded-md bg-gray-50 text-sm text-gray-700">
                                {dateRange.from.toLocaleDateString()}
                            </div>
                        ) : (
                            <DateRangePicker
                                date={{ from: dateRange.from, to: dateRange.to }}
                                setDate={onDateRangeChange}
                                className="w-full"
                            />
                        )}
                    </div>

                    {/* Check Selection */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <Label>Select Checks</Label>
                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="select-all-checks-modal"
                                    checked={isAllSelected}
                                    onCheckedChange={(c) => onToggleAll(c as boolean)}
                                />
                                <label
                                    htmlFor="select-all-checks-modal"
                                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                                >
                                    Select All
                                </label>
                            </div>
                        </div>

                        <div className="border rounded-md h-[300px] overflow-y-auto space-y-4 relative [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                            {availableChecks.length > 0 ? (
                                <>
                                    {renderCheckGroup('beam', 'Beam Checks')}
                                    {renderCheckGroup('geo', 'Geometry Checks')}
                                    {availableChecks.length === 0 && <div className="text-sm text-gray-500 p-2 text-center">Loading checks...</div>}
                                </>
                            ) : (
                                <div className="text-sm text-gray-500 p-2 text-center">Loading checks...</div>
                            )}
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <Button onClick={onSave}>Save</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};
