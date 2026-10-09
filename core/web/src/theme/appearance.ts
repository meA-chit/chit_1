import { useSyncExternalStore } from 'react';

/**
 * Appearance: colour mode (dark / light / match the device) and palette (classic cyan, or "spectrum", the
 * multi-colour one where each module has its own colour). A convenience per device, not household data:
 * a wall tablet and a phone can look different. Applied as `data-theme` and `data-palette` on <html>.
 */
export type Mode = 'dark' | 'light' | 'auto';
export type Palette = 'classic' | 'spectrum';
export interface Appearance { mode: Mode; palette: Palette }

const KEY = 'chit.appearance';
const DEFAULT: Appearance = { mode: 'dark', palette: 'classic' };
const listeners = new Set<() => void>();
let current: Appearance = load();

function load(): Appearance {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? 'null');
    const mode: Mode = raw?.mode === 'light' || raw?.mode === 'auto' ? raw.mode : 'dark';
    const palette: Palette = raw?.palette === 'spectrum' ? 'spectrum' : 'classic';
    return { mode, palette };
  } catch {
    return DEFAULT;
  }
}

const systemDark = () => (typeof window !== 'undefined' && typeof window.matchMedia === 'function' ? window.matchMedia('(prefers-color-scheme: dark)').matches : true);
export const resolveMode = (mode: Mode): 'dark' | 'light' => (mode === 'auto' ? (systemDark() ? 'dark' : 'light') : mode);

export function applyAppearance(value: Appearance = current) {
  if (typeof document === 'undefined') return;   // tests and server-side imports have no page
  const root = document.documentElement;
  const theme = resolveMode(value.mode);
  root.dataset.theme = theme;
  root.dataset.palette = value.palette;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#05070d' : '#eef2fb');
}

export function setAppearance(patch: Partial<Appearance>) {
  current = { ...current, ...patch };
  try {
    localStorage.setItem(KEY, JSON.stringify(current));
  } catch {
    /* private mode: the choice lasts for this visit only */
  }
  applyAppearance();
  listeners.forEach((listener) => listener());
}

/** Call once at start-up: applies the saved choice and follows the device while the mode is "auto". */
export function initAppearance() {
  applyAppearance();
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (current.mode === 'auto') applyAppearance(); });
  }
}

export function useAppearance() {
  const value = useSyncExternalStore(
    (listener) => { listeners.add(listener); return () => listeners.delete(listener); },
    () => current,
    () => DEFAULT,
  );
  return { ...value, setMode: (mode: Mode) => setAppearance({ mode }), setPalette: (palette: Palette) => setAppearance({ palette }) };
}
