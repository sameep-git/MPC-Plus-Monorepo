'use client';

import { useEffect } from 'react';
import { getSettings, applyTheme } from '../lib/settings';

export default function ThemeInitializer() {
  useEffect(() => {
    // Initialize theme on mount
    const settings = getSettings();
    applyTheme();
  }, []);

  return null;
}
