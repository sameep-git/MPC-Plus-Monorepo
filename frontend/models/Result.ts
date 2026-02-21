export interface Result {
  id: string;
  month?: number;
  year?: number;
  beamCheck?: Record<string, unknown> | null;
  status?: string;
}

export default Result;
