export interface Beam {
  id: string;
  type: string;
  typeID?: string;
  date: string; // ISO date
  timestamp?: string; // ISO datetime
  path?: string;
  relUniformity?: number;
  relOutput?: number;
  centerShift?: number;
  machineId: string;
  note?: string;
  approvedBy?: string;
  approvedDate?: string;

  // Flatness & Symmetry (from image analysis)
  horiFlatness?: number;
  vertFlatness?: number;
  horiSymmetry?: number;
  vertSymmetry?: number;

  // Image storage
  imagePaths?: Record<string, string>;

  // Status fields from backend
  status?: string;
  relOutputStatus?: string;
  relUniformityStatus?: string;
  centerShiftStatus?: string;

  // Joined beam variant data (from beam_variants table via typeID FK)
  beamVariants?: { variant: string };
}

export default Beam;
