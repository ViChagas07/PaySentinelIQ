"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemeMode = "dark" | "light" | "system";
export type PrimaryColor = "blue" | "green" | "purple" | "orange" | "red" | "teal";
export type BackgroundColor = "navy" | "charcoal" | "slate" | "midnight" | "espresso" | "forest";
export type FontSize = "small" | "medium" | "large" | "xlarge";
export type ElementSize = "compact" | "comfortable" | "spacious";
export type DigestFrequency = "daily" | "weekly" | "monthly" | "never";

export interface SettingsState {
  // Appearance
  theme: ThemeMode;
  primaryColor: PrimaryColor;
  backgroundColor: BackgroundColor;
  boldText: boolean;
  fontSize: FontSize;
  elementSize: ElementSize;

  // Language
  locale: string;

  // Accessibility
  highContrast: boolean;
  screenReaderOptimized: boolean;
  keyboardNav: boolean;
  focusIndicator: boolean;
  dyslexiaFont: boolean;
  reducedMotion: boolean;

  // Notifications
  emailAlerts: boolean;
  pushNotifications: boolean;
  desktopAlerts: boolean;
  soundAlerts: boolean;
  alertThreshold: number;
  fraudAlertEmail: string;
  digestFrequency: DigestFrequency;

  // Account
  timezone: string;

  // Developer
  developerMode: boolean;

  // Actions
  setTheme: (theme: ThemeMode) => void;
  setPrimaryColor: (color: PrimaryColor) => void;
  setBackgroundColor: (color: BackgroundColor) => void;
  setBoldText: (bold: boolean) => void;
  setFontSize: (size: FontSize) => void;
  setElementSize: (size: ElementSize) => void;
  setLocale: (locale: string) => void;
  setHighContrast: (on: boolean) => void;
  setScreenReaderOptimized: (on: boolean) => void;
  setKeyboardNav: (on: boolean) => void;
  setFocusIndicator: (on: boolean) => void;
  setDyslexiaFont: (on: boolean) => void;
  setReducedMotion: (on: boolean) => void;
  setEmailAlerts: (on: boolean) => void;
  setPushNotifications: (on: boolean) => void;
  setDesktopAlerts: (on: boolean) => void;
  setSoundAlerts: (on: boolean) => void;
  setAlertThreshold: (threshold: number) => void;
  setFraudAlertEmail: (email: string) => void;
  setDigestFrequency: (freq: DigestFrequency) => void;
  setTimezone: (tz: string) => void;
  setDeveloperMode: (on: boolean) => void;
  resetAll: () => void;
}

const DEFAULTS: Omit<SettingsState, keyof {
  setTheme: never; setPrimaryColor: never; setBackgroundColor: never; setBoldText: never;
  setFontSize: never; setElementSize: never; setLocale: never;
  setHighContrast: never; setScreenReaderOptimized: never;
  setKeyboardNav: never; setFocusIndicator: never;
  setDyslexiaFont: never; setReducedMotion: never;
  setEmailAlerts: never; setPushNotifications: never;
  setDesktopAlerts: never; setSoundAlerts: never;
  setAlertThreshold: never; setFraudAlertEmail: never;
  setDigestFrequency: never; setTimezone: never;
  setDeveloperMode: never; resetAll: never;
}> = {
  theme: "dark",
  primaryColor: "blue",
  backgroundColor: "navy",
  boldText: false,
  fontSize: "medium",
  elementSize: "comfortable",
  locale: "en",
  highContrast: false,
  screenReaderOptimized: false,
  keyboardNav: true,
  focusIndicator: true,
  dyslexiaFont: false,
  reducedMotion: false,
  emailAlerts: true,
  pushNotifications: false,
  desktopAlerts: false,
  soundAlerts: false,
  alertThreshold: 70,
  fraudAlertEmail: "",
  digestFrequency: "daily",
  timezone: "America/Sao_Paulo",
  developerMode: false,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULTS,
      setTheme: (theme) => set({ theme }),
      setPrimaryColor: (primaryColor) => set({ primaryColor }),
      setBackgroundColor: (backgroundColor) => set({ backgroundColor }),
      setBoldText: (boldText) => set({ boldText }),
      setFontSize: (fontSize) => set({ fontSize }),
      setElementSize: (elementSize) => set({ elementSize }),
      setLocale: (locale) => set({ locale }),
      setHighContrast: (highContrast) => set({ highContrast }),
      setScreenReaderOptimized: (screenReaderOptimized) => set({ screenReaderOptimized }),
      setKeyboardNav: (keyboardNav) => set({ keyboardNav }),
      setFocusIndicator: (focusIndicator) => set({ focusIndicator }),
      setDyslexiaFont: (dyslexiaFont) => set({ dyslexiaFont }),
      setReducedMotion: (reducedMotion) => set({ reducedMotion }),
      setEmailAlerts: (emailAlerts) => set({ emailAlerts }),
      setPushNotifications: (pushNotifications) => set({ pushNotifications }),
      setDesktopAlerts: (desktopAlerts) => set({ desktopAlerts }),
      setSoundAlerts: (soundAlerts) => set({ soundAlerts }),
      setAlertThreshold: (alertThreshold) => set({ alertThreshold }),
      setFraudAlertEmail: (fraudAlertEmail) => set({ fraudAlertEmail }),
      setDigestFrequency: (digestFrequency) => set({ digestFrequency }),
      setTimezone: (timezone) => set({ timezone }),
      setDeveloperMode: (developerMode) => set({ developerMode }),
      resetAll: () => set({ ...DEFAULTS }),
    }),
    {
      name: "psi-settings",
      version: 1,
    }
  )
);
