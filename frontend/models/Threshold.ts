export interface Threshold {
  id?: string;
  machineId: string;
  checkType: 'geometry' | 'beam';
  beamVariant?: string;           // legacy string name (kept for backward compat)
  beamVariantId?: string;         // UUID FK → beam_variants.id
  metricType: 'output_change' | 'uniformity_change' | 'center_shift' | string;
  lastUpdated: string; // ISO date-time
  value?: number;
}

export default Threshold;
