import { useSyncExternalStore } from 'react';

/**
 * An optional second clock in the top bar, for staying in touch with another place (family abroad, a home country).
 * A convenience per device, like Appearance: off by default, remembered in this browser, not household data.
 */
export interface SecondClock { enabled: boolean; zone: string }

/** Common zones with the code people say aloud. The code is written out because `Intl` only gives "GMT+5:30" for many zones. */
export const CLOCK_ZONES: { zone: string; label: string; code: string }[] = [
  { zone: 'Asia/Kolkata', label: 'India (Delhi, Mumbai)', code: 'IST' },
  { zone: 'Europe/London', label: 'United Kingdom', code: 'UK' },
  { zone: 'Europe/Dublin', label: 'Ireland', code: 'IE' },
  { zone: 'Europe/Berlin', label: 'Germany, Central Europe', code: 'CET' },
  { zone: 'Europe/Istanbul', label: 'Türkiye', code: 'TRT' },
  { zone: 'Europe/Moscow', label: 'Moscow', code: 'MSK' },
  { zone: 'Asia/Dubai', label: 'United Arab Emirates', code: 'GST' },
  { zone: 'Asia/Karachi', label: 'Pakistan', code: 'PKT' },
  { zone: 'Asia/Dhaka', label: 'Bangladesh', code: 'BST' },
  { zone: 'Asia/Colombo', label: 'Sri Lanka', code: 'SLST' },
  { zone: 'Asia/Bangkok', label: 'Thailand, Vietnam', code: 'ICT' },
  { zone: 'Asia/Singapore', label: 'Singapore, Malaysia', code: 'SGT' },
  { zone: 'Asia/Manila', label: 'Philippines', code: 'PHT' },
  { zone: 'Asia/Shanghai', label: 'China', code: 'CST' },
  { zone: 'Asia/Tokyo', label: 'Japan', code: 'JST' },
  { zone: 'Asia/Seoul', label: 'South Korea', code: 'KST' },
  { zone: 'Australia/Sydney', label: 'Sydney, Melbourne', code: 'AET' },
  { zone: 'Pacific/Auckland', label: 'New Zealand', code: 'NZT' },
  { zone: 'Africa/Cairo', label: 'Egypt', code: 'EET' },
  { zone: 'Africa/Lagos', label: 'Nigeria', code: 'WAT' },
  { zone: 'Africa/Nairobi', label: 'Kenya, East Africa', code: 'EAT' },
  { zone: 'Africa/Johannesburg', label: 'South Africa', code: 'SAST' },
  { zone: 'America/Sao_Paulo', label: 'Brazil (São Paulo)', code: 'BRT' },
  { zone: 'America/Argentina/Buenos_Aires', label: 'Argentina', code: 'ART' },
  { zone: 'America/Mexico_City', label: 'Mexico', code: 'CST' },
  { zone: 'America/New_York', label: 'US and Canada, Eastern', code: 'ET' },
  { zone: 'America/Chicago', label: 'US and Canada, Central', code: 'CT' },
  { zone: 'America/Denver', label: 'US and Canada, Mountain', code: 'MT' },
  { zone: 'America/Los_Angeles', label: 'US and Canada, Pacific', code: 'PT' },
];

export const isValidZone = (zone: string): boolean => {
  try { new Intl.DateTimeFormat('en', { timeZone: zone }); return true; } catch { return false; }
};

export const zoneCode = (zone: string): string =>
  CLOCK_ZONES.find((item) => item.zone === zone)?.code
  ?? new Intl.DateTimeFormat('en', { timeZone: zone, timeZoneName: 'short' }).formatToParts(new Date()).find((part) => part.type === 'timeZoneName')?.value
  ?? zone;

export type DayPart = 'night' | 'morning' | 'day' | 'evening';

/** 22 to 5 night, 5 to 8 early morning, 8 to 17 day, 17 to 22 evening. */
export const dayPart = (hour: number): DayPart => (hour >= 22 || hour < 5 ? 'night' : hour < 8 ? 'morning' : hour < 17 ? 'day' : 'evening');
export const DAY_PART_LABEL: Record<DayPart, string> = { night: 'Night', morning: 'Early morning', day: 'Daytime', evening: 'Evening' };

/** Hour (0 to 23) and "HH:MM" of an instant in a zone. */
export function timeIn(date: Date, zone: string): { hour: number; text: string } {
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone: zone, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(date);
  const hour = Number(parts.find((p) => p.type === 'hour')?.value ?? 0);
  const minute = parts.find((p) => p.type === 'minute')?.value ?? '00';
  return { hour, text: `${String(hour).padStart(2, '0')}:${minute}` };
}

/** "+3:30 h" or "same time": how far the other zone is ahead of (+) or behind (−) this one right now. */
export function offsetFrom(date: Date, zone: string, from: string): string {
  const minutesOf = (z: string) => {
    const { hour, text } = timeIn(date, z);
    return hour * 60 + Number(text.slice(3));
  };
  const day = (z: string) => new Intl.DateTimeFormat('en-CA', { timeZone: z }).format(date);
  let diff = minutesOf(zone) - minutesOf(from);
  const days = (Date.parse(day(zone)) - Date.parse(day(from))) / 86_400_000;
  diff += days * 1440;
  if (diff === 0) return 'same time';
  const abs = Math.abs(diff);
  return `${diff > 0 ? '+' : '−'}${Math.floor(abs / 60)}${abs % 60 ? `:${String(abs % 60).padStart(2, '0')}` : ''} h`;
}

const KEY = 'chit.secondClock';
const DEFAULT: SecondClock = { enabled: false, zone: 'Asia/Kolkata' };
const listeners = new Set<() => void>();
let current: SecondClock = load();

function load(): SecondClock {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? 'null');
    return { enabled: raw?.enabled === true, zone: typeof raw?.zone === 'string' && isValidZone(raw.zone) ? raw.zone : DEFAULT.zone };
  } catch {
    return DEFAULT;
  }
}

export function setSecondClock(patch: Partial<SecondClock>) {
  const next = { ...current, ...patch };
  current = { enabled: next.enabled, zone: isValidZone(next.zone) ? next.zone : current.zone };
  try { localStorage.setItem(KEY, JSON.stringify(current)); } catch { /* private mode: lasts for this visit only */ }
  listeners.forEach((listener) => listener());
}

export function useSecondClock(): SecondClock {
  return useSyncExternalStore((listener) => { listeners.add(listener); return () => { listeners.delete(listener); }; }, () => current, () => DEFAULT);
}
