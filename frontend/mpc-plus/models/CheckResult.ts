
export interface CheckMetric {
    name: string;
    value: string | number;
    thresholds: string;
    absoluteValue: string | number;
    status: 'pass' | 'fail' | 'warning';
}

export interface CheckResult {
    id: string;
    name: string;
    status: 'PASS' | 'FAIL' | 'WARNING';
    metrics: CheckMetric[];
    approvedBy?: string;
    approvedDate?: string;
    imagePaths?: Record<string, string>;
}
