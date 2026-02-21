'use client';

import { useEffect } from 'react';
import { getSettings, applyTheme } from '../lib/settings';

interface ThemeProviderProps {
  children: React.ReactNode;
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
  useEffect(() => {
    // Initialize theme immediately on mount
    applyTheme();
  }, []);

  return <>{children}</>;
}
