import type { Beam } from './Beam';

export interface CheckGroup {
    timestamp: string; // ISO string
    beams: Beam[];
}
