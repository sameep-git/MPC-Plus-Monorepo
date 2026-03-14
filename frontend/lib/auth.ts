// Authentication service for JWT-based auth
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5132/api';

export interface AuthResponse {
  token: string;
  user: {
    id: string;
    username: string;
    email?: string;
    fullName?: string;
    role: string;
    approvalStatus: string;
  };
}

/**
 * Sign in with username and password
 */
export const signIn = async (username: string, password: string): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Login failed' }));
    throw new Error(error.message || 'Login failed');
  }

  const data = await response.json();
  
  // Store token in localStorage
  if (typeof window !== 'undefined') {
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }

  return data;
};

/**
 * Sign up / register a new account
 */
export const signUp = async (
  username: string,
  password: string,
  email?: string,
  fullName?: string
): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, email, fullName }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Registration failed' }));
    throw new Error(error.message || 'Registration failed');
  }

  const data = await response.json();
  
  // Store token in localStorage only if it's not empty (pending users don't get tokens)
  if (typeof window !== 'undefined' && data.token) {
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }

  return data;
};

/**
 * Sign out the current user
 */
export const signOut = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
  }
};

/**
 * Get the stored auth token
 */
export const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken');
  }
  return null;
};

/**
 * Get the stored user info
 */
export const getStoredUser = () => {
  if (typeof window !== 'undefined') {
    const userJson = localStorage.getItem('user');
    if (!userJson) {
      return null;
    }

    try {
      return JSON.parse(userJson);
    } catch {
      // Clear corrupted user data to avoid repeated parse failures
      localStorage.removeItem('user');
      return null;
    }
  }
  return null;
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return !!getAuthToken();
};

/**
 * Get fetch options with auth token included
 */
export const getFetchOptions = (init?: RequestInit): RequestInit => {
  const token = getAuthToken();
  const headers = new Headers(init?.headers || {});

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  return {
    ...init,
    headers,
  };
};
