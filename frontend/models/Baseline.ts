export interface Baseline {
  machineId: string;
  checkType: 'geometry' | 'beam';
  beamVariant?: string;
  metricType: string;
  date: string; // ISO datetime (UTC)
  value?: number;
}

export default Baseline;
