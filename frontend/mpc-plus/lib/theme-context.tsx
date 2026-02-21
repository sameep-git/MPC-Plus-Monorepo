'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type Theme = 'light' | 'dark' | 'auto';

interface BeamThresholds {
  '2.5x': {
    outputChange: number;
    uniformityChange: number;
    centerShift: number;
  };
  '6x': {
    outputChange: number;
    uniformityChange: number;
    centerShift: number;
  };
  '6xFFF': {
    outputChange: number;
    uniformityChange: number;
    centerShift: number;
  };
  '10x': {
    outputChange: number;
    uniformityChange: number;
    centerShift: number;
  };
}

interface Settings {
  theme: Theme;
  beamThresholds: BeamThresholds;
  graphThresholdTop: number;
  graphThresholdBottom: number;
  notifications: {
    email: boolean;
    thresholdAlerts: boolean;
    dailyReports: boolean;
  };
}

interface ThemeContextType {
  settings: Settings;
  updateTheme: (theme: Theme) => void;
  updateBeamThreshold: (beam: keyof BeamThresholds, metric: keyof BeamThresholds['2.5x'], value: number) => void;
  updateGraphThreshold: (type: 'top' | 'bottom', value: number) => void;
  updateNotification: (key: keyof Settings['notifications'], value: boolean) => void;
  resetSettings: () => void;
}

const defaultSettings: Settings = {
  theme: 'light',
  beamThresholds: {
    '2.5x': {
      outputChange: 3.0,
      uniformityChange: 2.5,
      centerShift: 2.0,
    },
    '6x': {
      outputChange: 3.0,
      uniformityChange: 2.5,
      centerShift: 2.0,
    },
    '6xFFF': {
      outputChange: 3.0,
      uniformityChange: 2.5,
      centerShift: 2.0,
    },
    '10x': {
      outputChange: 3.0,
      uniformityChange: 2.5,
      centerShift: 2.0,
    },
  },
  graphThresholdTop: 16.67,
  graphThresholdBottom: 16.67,
  notifications: {
    email: true,
    thresholdAlerts: true,
    dailyReports: false,
  },
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(defaultSettings);
  const [mounted, setMounted] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    // eslint-disable-next-line
    setMounted(true);
    const savedSettings = localStorage.getItem('mpc-plus-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...defaultSettings, ...parsed });
      } catch (error) {
        console.error('Error loading settings:', error);
      }
    }
  }, []);

  // Apply theme to document
  useEffect(() => {
    if (!mounted) return;

    const root = document.documentElement;

    // Always apply light mode
    root.classList.remove('dark');
    root.style.setProperty('--color-background', '#ffffff');
    root.style.setProperty('--color-text', '#13070c');
    root.style.setProperty('--color-primary', '#420039');
  }, [settings.theme, mounted]);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    if (mounted) {
      localStorage.setItem('mpc-plus-settings', JSON.stringify(settings));
    }
  }, [settings, mounted]);

  const updateTheme = (theme: Theme) => {
    setSettings(prev => ({ ...prev, theme }));
  };

  const updateBeamThreshold = (
    beam: keyof BeamThresholds,
    metric: keyof BeamThresholds['2.5x'],
    value: number
  ) => {
    setSettings(prev => ({
      ...prev,
      beamThresholds: {
        ...prev.beamThresholds,
        [beam]: {
          ...prev.beamThresholds[beam],
          [metric]: value,
        },
      },
    }));
  };

  const updateGraphThreshold = (type: 'top' | 'bottom', value: number) => {
    setSettings(prev => ({
      ...prev,
      graphThresholdTop: type === 'top' ? value : prev.graphThresholdTop,
      graphThresholdBottom: type === 'bottom' ? value : prev.graphThresholdBottom,
    }));
  };

  const updateNotification = (key: keyof Settings['notifications'], value: boolean) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: value,
      },
    }));
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
  };

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider
      value={{
        settings,
        updateTheme,
        updateBeamThreshold,
        updateGraphThreshold,
        updateNotification,
        resetSettings,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

