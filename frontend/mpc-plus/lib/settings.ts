// Settings management for MPC Plus application
// Handles theme and threshold settings with localStorage persistence

export type Theme = 'light' | 'dark';

export interface BeamThresholds {
  'beam-2.5x': {
    outputChange: { min: number; max: number };
    uniformityChange: { min: number; max: number };
    centerShift: { min: number; max: number };
  };
  'beam-6x': {
    outputChange: { min: number; max: number };
    uniformityChange: { min: number; max: number };
    centerShift: { min: number; max: number };
  };
  'beam-6xfff': {
    outputChange: { min: number; max: number };
    uniformityChange: { min: number; max: number };
    centerShift: { min: number; max: number };
  };
  'beam-10x': {
    outputChange: { min: number; max: number };
    uniformityChange: { min: number; max: number };
    centerShift: { min: number; max: number };
  };
}

export type BaselineMode = 'date' | 'manual';

export interface BaselineManualValues {
  outputChange: number;
  uniformityChange: number;
  centerShift: number;
}

export interface BaselineSettings {
  mode: BaselineMode;
  date?: string;
  manualValues: BaselineManualValues;
}

export interface AppSettings {
  theme: Theme;
  accentColor: string; // Hex color
  thresholds: BeamThresholds;
  graphThresholdTopPercent: number;
  graphThresholdBottomPercent: number;
  graphThresholdColor: string;
  baseline: BaselineSettings;
}

const DEFAULT_THRESHOLDS: BeamThresholds = {
  'beam-2.5x': {
    outputChange: { min: -3, max: 3 },
    uniformityChange: { min: -2.5, max: 2.5 },
    centerShift: { min: -2, max: 2 },
  },
  'beam-6x': {
    outputChange: { min: -3, max: 3 },
    uniformityChange: { min: -2.5, max: 2.5 },
    centerShift: { min: -2, max: 2 },
  },
  'beam-6xfff': {
    outputChange: { min: -3, max: 3 },
    uniformityChange: { min: -2.5, max: 2.5 },
    centerShift: { min: -2, max: 2 },
  },
  'beam-10x': {
    outputChange: { min: -3, max: 3 },
    uniformityChange: { min: -2.5, max: 2.5 },
    centerShift: { min: -2, max: 2 },
  },
};

const DEFAULT_BASELINE_SETTINGS: BaselineSettings = {
  mode: 'date',
  date: undefined,
  manualValues: {
    outputChange: 0,
    uniformityChange: 0,
    centerShift: 0,
  },
};

const getDefaultBaselineSettings = (): BaselineSettings => ({
  ...DEFAULT_BASELINE_SETTINGS,
  manualValues: { ...DEFAULT_BASELINE_SETTINGS.manualValues },
});

const getDefaultThresholds = (): BeamThresholds =>
  JSON.parse(JSON.stringify(DEFAULT_THRESHOLDS));

export const DEFAULT_ACCENT_COLOR = '#420039';

const getDefaultSettings = (): AppSettings => ({
  theme: 'light',
  accentColor: DEFAULT_ACCENT_COLOR,
  thresholds: getDefaultThresholds(),
  graphThresholdTopPercent: 16.67,
  graphThresholdBottomPercent: 16.67,
  graphThresholdColor: '#fef3c7',
  baseline: getDefaultBaselineSettings(),
});

const STORAGE_KEY = 'mpc-plus-settings';

export const getSettings = (): AppSettings => {
  const defaults = getDefaultSettings();

  if (typeof window === 'undefined') {
    return defaults;
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Merge with defaults to handle new settings fields
      const mergedBaseline: BaselineSettings = {
        ...defaults.baseline,
        ...parsed.baseline,
        manualValues: {
          ...defaults.baseline.manualValues,
          ...(parsed.baseline?.manualValues ?? {}),
        },
      };

      return {
        ...defaults,
        ...parsed,
        thresholds: {
          ...defaults.thresholds,
          ...parsed.thresholds,
        },
        baseline: mergedBaseline,
      };
    }
  } catch (error) {
    console.error('Error loading settings:', error);
  }

  return defaults;
};

export const saveSettings = (settings: AppSettings): void => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    // Apply theme and accent immediately
    applyTheme();
    applyAccentColor(settings.accentColor);
  } catch (error) {
    console.error('Error saving settings:', error);
  }
};

export const updateTheme = (theme: Theme): void => {
  const settings = getSettings();
  settings.theme = theme;
  saveSettings(settings);
  applyTheme();
};

export const updateAccentColor = (color: string): void => {
  const settings = getSettings();
  settings.accentColor = color;
  saveSettings(settings);
  applyAccentColor(color);
};

export const updateThresholds = (thresholds: Partial<BeamThresholds>): void => {
  const settings = getSettings();
  settings.thresholds = {
    ...settings.thresholds,
    ...thresholds,
  };
  saveSettings(settings);
};

export const updateGraphThresholds = (
  topPercent?: number,
  bottomPercent?: number,
  color?: string
): void => {
  const settings = getSettings();
  if (topPercent !== undefined) settings.graphThresholdTopPercent = topPercent;
  if (bottomPercent !== undefined) settings.graphThresholdBottomPercent = bottomPercent;
  if (color !== undefined) settings.graphThresholdColor = color;
  saveSettings(settings);
};

export const updateBaselineSettings = (baseline: Partial<BaselineSettings>): void => {
  const settings = getSettings();
  settings.baseline = {
    ...settings.baseline,
    ...baseline,
    manualValues: {
      ...settings.baseline.manualValues,
      ...(baseline.manualValues ?? {}),
    },
  };
  saveSettings(settings);
};

export const getDefaultAppSettings = (): AppSettings => getDefaultSettings();

export const applyTheme = (): void => {
  if (typeof window === 'undefined') {
    return;
  }

  const root = document.documentElement;
  // Force light mode
  root.classList.remove('dark');
};

export const applyAccentColor = (color: string): void => {
  if (typeof window === 'undefined') {
    return;
  }

  const root = document.documentElement;

  if (!color || color === DEFAULT_ACCENT_COLOR) {
    // If default or empty, remove overrides so CSS rules apply (handling dark/light mode automatically)
    root.style.removeProperty('--primary');
    root.style.removeProperty('--color-primary');
    root.style.removeProperty('--ring');
    return;
  }

  // Set CSS variables
  root.style.setProperty('--primary', color);
  root.style.setProperty('--color-primary', color);
  root.style.setProperty('--ring', color);
};
