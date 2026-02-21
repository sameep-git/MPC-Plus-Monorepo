
export interface GraphDataPoint {
    date: string;
    fullDate: string;
    [key: string]: string | number; // Allow dynamic metric keys
}
