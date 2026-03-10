'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getStoredUser, isAuthenticated } from './auth';

interface AuthContextType {
  user: any | null;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isAuthenticated: false,
});

// Public routes that don't require authentication
const PUBLIC_ROUTES = ['/signin', '/signup'];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Check if user is authenticated on mount
    const checkAuth = () => {
      const authenticated = isAuthenticated();
      
      if (authenticated) {
        const storedUser = getStoredUser();
        setUser(storedUser);
      } else {
        setUser(null);
        
        // Redirect to signin if accessing protected route
        if (!PUBLIC_ROUTES.includes(pathname)) {
          router.push('/signin');
        }
      }
      
      setLoading(false);
    };

    checkAuth();
  }, [router, pathname]);

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated: isAuthenticated() }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
