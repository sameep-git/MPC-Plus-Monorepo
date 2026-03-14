// API service for MPC Plus application
// All data access goes through the REST backend via NEXT_PUBLIC_API_URL.

import { UI_CONSTANTS } from '../constants';
import { getAuthToken } from './auth';
import type { Machine as MachineType } from '../models/Machine';
import type { UpdateModel as UpdateModelType } from '../models/Update';
import type { Beam as BeamType } from '../models/Beam';
import type { GeoCheck as GeoCheckType } from '../models/GeoCheck';

// Helper to convert object keys to camelCase
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const toCamelCase = (obj: any): any => {
  if (Array.isArray(obj)) {
    return obj.map(v => toCamelCase(v));
  } else if (obj !== null && obj.constructor === Object) {
    return Object.keys(obj).reduce(
      (result, key) => {
        // Handle snake_case to camelCase conversion
        const camelKey = key.replace(/_([a-z0-9])/g, (match, letter) => letter.toUpperCase());
        // Handle PascalCase to camelCase conversion
        const finalKey = camelKey.charAt(0).toLowerCase() + camelKey.slice(1);

        return {
          ...result,
          [finalKey]: toCamelCase(obj[key]),
        };
      },
      {}
    );
  }
  return obj;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';


/**
 * Construct a URL to fetch a beam check image.
 *
 * If the path is already a full URL (starts with http:// or https://),
 * it is returned as-is.
 *
 * Otherwise, serves from the backend's static files (wwwroot/images/).
 */
export const getImageUrl = (imagePath: string): string => {
  // Sanitize: trim whitespace and trailing backslashes (JSON escaping artifacts)
  const cleanPath = imagePath.trim().replace(/\\+$/, '');

  // If already a full URL, use directly
  if (cleanPath.startsWith('http://') || cleanPath.startsWith('https://')) {
    return cleanPath;
  }

  // Serve from backend static files (wwwroot/images/...)
  // API_BASE may include /api suffix (e.g. http://localhost:5132/api)
  // but static files are served at the server root, so strip /api
  const origin = API_BASE.replace(/\/api\/?$/, '');
  return `${origin}/${cleanPath.replace(/^\//, '')}`;
};

const safeFetch = async (input: RequestInfo, init?: RequestInit) => {
  const headers = new Headers(init?.headers as HeadersInit);

  // Add auth token if available
  const token = getAuthToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Prevent aggressive caching of dashboard data
  const mergedInit: RequestInit = {
    cache: 'no-store',
    ...init,
    headers
  };

  const res = await fetch(input, mergedInit);
  if (!res.ok) {
    // Handle expired / invalid token — clear auth and redirect to signin
    if (res.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        window.location.href = '/signin';
      }
      throw new Error('Session expired. Please sign in again.');
    }
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json().catch(() => null);
};

export const fetchMachines = async (): Promise<MachineType[]> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/machines`;
    return await safeFetch(url);
  } catch (err) {
    console.error('[fetchMachines] Error:', err);
    throw err;
  }
};

export const updateMachine = async (machine: MachineType): Promise<void> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/machines/${machine.id}`;
    await safeFetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(machine),
    });
  } catch (err) {
    console.error('[updateMachine] Error:', err);
    throw err;
  }
};

export const fetchUpdates = async (): Promise<UpdateModelType[]> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/updates`;
    return await safeFetch(url);
  } catch (err) {
    throw err;
  }
};

export const fetchResults = async (month: number, year: number, machineId: string) => {
  try {
    const url = new URL(`${API_BASE.replace(/\/$/, '')}/results`);
    url.searchParams.set('month', String(month));
    url.searchParams.set('year', String(year));
    url.searchParams.set('machineId', machineId);
    const result = await safeFetch(url.toString());
    return result;
  } catch (err) {
    console.error('[fetchResults] Error:', err);
    throw err;
  }
};

export const fetchUser = async (): Promise<{ id: string; name: string; role: string } | null> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/auth/me`;
    const response = await safeFetch(url);
    
    if (!response) {
      return null;
    }

    return {
      id: response.id,
      name: response.fullName || response.username || 'User',
      role: response.role || 'User',
    };
  } catch (err) {
    console.error('[fetchUser] Error:', err);
    return null;
  }
};

// Beams API
export const fetchBeamTypes = async (): Promise<string[]> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/beams/types`;
    return await safeFetch(url);
  } catch (err) {
    throw err;
  }
};

type FetchBeamsParams = {
  machineId: string;
  type?: string;
  date?: string; // YYYY-MM-DD
  startDate?: string; // YYYY-MM-DD
  endDate?: string; // YYYY-MM-DD
  range?: 'week' | 'month' | 'quarter';
};

import type { CheckGroup } from '../models/CheckGroup';

export const fetchBeams = async (params: FetchBeamsParams): Promise<CheckGroup[]> => {
  try {
    const url = new URL(`${API_BASE.replace(/\/$/, '')}/beams`);
    // Note: API spec uses machineId (camelCase) for /beams
    url.searchParams.set('machineId', params.machineId);
    if (params.type) url.searchParams.set('type', params.type);
    if (params.date) url.searchParams.set('date', params.date);
    if (params.startDate) url.searchParams.set('startDate', params.startDate);
    if (params.endDate) url.searchParams.set('endDate', params.endDate);
    const data = await safeFetch(url.toString());
    return toCamelCase(data);
  } catch (err) {
    throw err;
  }
};

export const approveBeams = async (beamIds: string[], approvedBy: string): Promise<{ approved: string[]; errors: string[] }> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/beams/accept`;
    const data = await safeFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ beamIds: beamIds, approvedBy: approvedBy })
    });
    return toCamelCase(data);
  } catch (err) {
    console.error('[approveBeams] Error:', err);
    throw err;
  }
};

export const approveGeoChecks = async (geoCheckIds: string[], approvedBy: string): Promise<{ approved: string[]; errors: string[] }> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/geochecks/accept`;
    const data = await safeFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ geoCheckIds: geoCheckIds, approvedBy: approvedBy })
    });
    return toCamelCase(data);
  } catch (err) {
    console.error('[approveGeoChecks] Error:', err);
    throw err;
  }
};

export type FetchGeoChecksParams = {
  machineId: string;
  type?: string;
  date?: string; // YYYY-MM-DD
  startDate?: string; // YYYY-MM-DD
  endDate?: string; // YYYY-MM-DD
  range?: 'week' | 'month' | 'quarter';
};

export const fetchGeoChecks = async (params: FetchGeoChecksParams): Promise<GeoCheckType[]> => {
  try {
    const url = new URL(`${API_BASE.replace(/\/$/, '')}/geochecks`);
    url.searchParams.set('machine-id', params.machineId);
    if (params.type) url.searchParams.set('type', params.type);
    if (params.date) url.searchParams.set('date', params.date);
    if (params.startDate) url.searchParams.set('start-date', params.startDate);
    if (params.endDate) url.searchParams.set('end-date', params.endDate);
    const data = await safeFetch(url.toString());
    return toCamelCase(data);
  } catch (err) {
    throw err;
  }
};

// Threshold API
export interface Threshold {
  id?: string;
  machineId: string;
  checkType: 'geometry' | 'beam';
  beamVariant?: string;           // legacy string name
  beamVariantId?: string;         // UUID FK → beam_variants.id
  metricType: string;
  value: number;
  lastUpdated?: string;
}

export const fetchThresholds = async (): Promise<Threshold[]> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/thresholds/all`;
    return toCamelCase(await safeFetch(url));
  } catch (err) {
    console.error('[fetchThresholds] Error:', err);
    throw err;
  }
};

export const saveThreshold = async (threshold: Threshold): Promise<Threshold> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/thresholds`;
    const data = await safeFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(threshold),
    });
    return toCamelCase(data);
  } catch (err) {
    console.error('[saveThreshold] Error:', err);
    throw err;
  }
};

// Report Generation API
export interface ReportRequest {
  startDate: string; // YYYY-MM-DD
  endDate: string;   // YYYY-MM-DD
  machineId: string;
  selectedChecks: string[];
  timeZone?: string;
}

export const generateReport = async (payload: ReportRequest): Promise<Blob> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/reports/generate`;

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }

    return await res.blob();
  } catch (err) {
    console.error('[generateReport] Error:', err);
    throw err;
  }
};

// Error handling wrapper
export const handleApiError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return UI_CONSTANTS.ERRORS?.UNEXPECTED_ERROR ?? 'Unexpected error';
};

// ============================================
// DOC Factor Types and API Functions
// ============================================

export interface DocFactor {
  id?: string;
  machineId: string;
  beamVariantId: string;
  beamVariantName?: string;
  beamId: string;
  msdAbs: number;
  mpcRel: number;
  docFactor: number;            // DB column: doc_factor → toCamelCase → docFactor
  measurementDate: string; // YYYY-MM-DD
  startDate: string;       // YYYY-MM-DD
  endDate?: string | null; // YYYY-MM-DD or null
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
}

export interface BeamCheckOption {
  id: string;
  timestamp: string;
  relOutput: number;
  type: string;
}

export interface BeamVariantWithId {
  id: string;
  variant: string;
}

/**
 * Normalizes a raw doc factor object to match the DocFactor interface.
 * Handles field name differences between different API responses.
 * Also parses numeric strings to proper numbers.
 */
const normalizeDocFactor = (raw: Record<string, unknown>): DocFactor => {
  const docFactorVal = raw.docFactor ?? raw.docFactorValue ?? raw.doc_factor ?? raw.DocFactorValue ?? raw.DocFactor;
  const msdAbsVal = raw.msdAbs ?? raw.msd_abs ?? raw.MsdAbs;
  const mpcRelVal = raw.mpcRel ?? raw.mpc_rel ?? raw.MpcRel;

  return {
    id: raw.id as string | undefined,
    machineId: (raw.machineId ?? raw.machine_id) as string,
    beamVariantId: (raw.beamVariantId ?? raw.beam_variant_id) as string,
    beamVariantName: (raw.beamVariantName ?? raw.beam_variant_name) as string | undefined,
    beamId: (raw.beamId ?? raw.beam_id) as string,
    msdAbs: typeof msdAbsVal === 'string' ? parseFloat(msdAbsVal) : (msdAbsVal as number) ?? 0,
    mpcRel: typeof mpcRelVal === 'string' ? parseFloat(mpcRelVal) : (mpcRelVal as number) ?? 0,
    docFactor: typeof docFactorVal === 'string' ? parseFloat(docFactorVal) : (docFactorVal as number) ?? 0,
    measurementDate: (raw.measurementDate ?? raw.measurement_date) as string,
    startDate: (raw.startDate ?? raw.start_date) as string,
    endDate: (raw.endDate ?? raw.end_date) as string | null | undefined,
    createdAt: (raw.createdAt ?? raw.created_at) as string | undefined,
    updatedAt: (raw.updatedAt ?? raw.updated_at) as string | undefined,
    createdBy: (raw.createdBy ?? raw.created_by) as string | undefined,
  };
};

/**
 * Fetch all DOC factors, optionally filtered by machine
 */
export const fetchDocFactors = async (machineId?: string): Promise<DocFactor[]> => {
  try {
    const url = machineId
      ? `${API_BASE.replace(/\/$/, '')}/docfactors?machineId=${encodeURIComponent(machineId)}`
      : `${API_BASE.replace(/\/$/, '')}/docfactors`;
    const raw = await safeFetch(url);
    const arr = Array.isArray(raw) ? raw : [raw];
    const factors = arr.map((d: Record<string, unknown>) => normalizeDocFactor(toCamelCase(d)));

    // C# API doesn't return variant names — resolve from beam_variants
    const missingNames = factors.some(f => !f.beamVariantName && f.beamVariantId);
    if (missingNames) {
      try {
        const variants = await fetchBeamVariantsWithIds();
        for (const f of factors) {
          if (!f.beamVariantName && f.beamVariantId) {
            const match = variants.find(v => v.id === f.beamVariantId);
            if (match) f.beamVariantName = match.variant;
          }
        }
      } catch (e) {
        console.warn('[fetchDocFactors] Could not resolve variant names:', e);
      }
    }

    return factors;
  } catch (err) {
    console.error('[fetchDocFactors] Error:', err);
    throw err;
  }
};

/**
 * Get the applicable DOC factor for a specific date
 */
export const fetchApplicableDocFactor = async (
  machineId: string,
  beamVariantId: string,
  date: string
): Promise<DocFactor | null> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/docfactors/applicable?machineId=${encodeURIComponent(machineId)}&beamVariantId=${encodeURIComponent(beamVariantId)}&date=${encodeURIComponent(date)}`;
    try {
      return await safeFetch(url);
    } catch (err) {
      // 404 means no applicable factor found
      if (err instanceof Error && err.message.includes('404')) {
        return null;
      }
      throw err;
    }
  } catch (err) {
    console.error('[fetchApplicableDocFactor] Error:', err);
    throw err;
  }
};

/**
 * Create a new DOC factor
 */
export const createDocFactor = async (docFactor: Omit<DocFactor, 'id' | 'docFactor' | 'createdAt' | 'updatedAt'>): Promise<DocFactor> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/docfactors`;
    return await safeFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(docFactor),
    });
  } catch (err) {
    console.error('[createDocFactor] Error:', err);
    throw err;
  }
};

/**
 * Update an existing DOC factor
 */
export const updateDocFactor = async (docFactor: DocFactor): Promise<DocFactor> => {
  try {
    if (!docFactor.id) throw new Error('DocFactor ID is required for update');

    const url = `${API_BASE.replace(/\/$/, '')}/docfactors/${docFactor.id}`;
    return await safeFetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(docFactor),
    });
  } catch (err) {
    console.error('[updateDocFactor] Error:', err);
    throw err;
  }
};

/**
 * Delete a DOC factor
 */
export const deleteDocFactor = async (id: string): Promise<void> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/docfactors/${id}`;
    await safeFetch(url, { method: 'DELETE' });
  } catch (err) {
    console.error('[deleteDocFactor] Error:', err);
    throw err;
  }
};

/**
 * Fetch beam checks for a specific date/machine/beam type (for DOC factor selection)
 */
export const fetchBeamChecksForDate = async (
  machineId: string,
  beamType: string,
  date: string
): Promise<BeamCheckOption[]> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/beams/by-date?machineId=${encodeURIComponent(machineId)}&beamType=${encodeURIComponent(beamType)}&date=${encodeURIComponent(date)}`;
    return await safeFetch(url);
  } catch (err) {
    console.error('[fetchBeamChecksForDate] Error:', err);
    throw err;
  }
};

/**
 * Fetch beam variants with their IDs
 */
export const fetchBeamVariantsWithIds = async (): Promise<BeamVariantWithId[]> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/beams/variants`;
    return toCamelCase(await safeFetch(url));
  } catch (err) {
    console.error('[fetchBeamVariantsWithIds] Error:', err);
    throw err;
  }
};

// ─── Timezone / App Settings ────────────────────────────────────────

/**
 * Fetch the configured IANA timezone (e.g. "America/Chicago").
 * Returns null if not yet set.
 */
export const fetchTimezone = async (): Promise<string | null> => {
  const url = `${API_BASE.replace(/\/$/, '')}/settings/timezone`;
  const data = await safeFetch(url);
  return data.timezone ?? null;
};

/**
 * Set the global timezone for the application.
 */
export const setTimezone = async (timezone: string): Promise<void> => {
  const url = `${API_BASE.replace(/\/$/, '')}/settings/timezone`;
  await safeFetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ timezone }),
  });
};

// Admin API functions

export interface UserDto {
  id: string;
  username: string;
  email?: string;
  fullName?: string;
  role: string;
  approvalStatus: string;
}

/**
 * Fetch all users (Admin only)
 */
export const fetchAllUsers = async (): Promise<UserDto[]> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/admin/users`;
    return await safeFetch(url);
  } catch (err) {
    console.error('[fetchAllUsers] Error:', err);
    throw err;
  }
};

/**
 * Fetch pending user approvals (Admin only)
 */
export const fetchPendingUsers = async (): Promise<UserDto[]> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/admin/users/pending`;
    return await safeFetch(url);
  } catch (err) {
    console.error('[fetchPendingUsers] Error:', err);
    throw err;
  }
};

/**
 * Approve a user (Admin only)
 */
export const approveUser = async (userId: string): Promise<void> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/admin/users/${userId}/approve`;
    await safeFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
  } catch (err) {
    console.error('[approveUser] Error:', err);
    throw err;
  }
};

/**
 * Deny a user (Admin only)
 */
export const denyUser = async (userId: string): Promise<void> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/admin/users/${userId}/deny`;
    await safeFetch(url, {
      method: 'POST',
    });
  } catch (err) {
    console.error('[denyUser] Error:', err);
    throw err;
  }
};

/**
 * Update user role (Admin only)
 */
export const updateUserRole = async (userId: string, role: string): Promise<void> => {
  try {
    const url = `${API_BASE.replace(/\/$/, '')}/admin/users/${userId}/role`;
    await safeFetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ Role: role }),
    });
  } catch (err) {
    console.error('[updateUserRole] Error:', err);
    throw err;
  }
};
