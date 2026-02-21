export interface Baseline {
  machineId: string;
  checkType: 'geometry' | 'beam';
  beamVariant?: string;
  metricType: string;
  date: string; // ISO date
  value?: number;
}

export default Baseline;
