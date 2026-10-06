import { useQuery } from '@tanstack/react-query';
import { api, type DataState } from '@chit/core';

/** Data hooks and formatting shared by the energy cards. All numbers come from the hub (Tibber, SolarEdge); nothing is invented here. */

export interface HourPrice { hour: number; price: number | null; level: string | null; consumption: number | null }
export interface PriceDay {
  state: DataState; reason?: 'no_household' | 'no_tibber_token' | 'token_rejected' | 'rate_limited' | 'unavailable';
  currency?: string | null; date?: string; which?: 'today' | 'tomorrow'; now_hour?: number | null; checked_at?: string;
  tomorrow_available?: boolean; hours?: HourPrice[]; average_price?: number | null; cheapest_hour?: number | null; priciest_hour?: number | null;
  current?: { hour: number; price: number; vs_average: number | null; consumption: number | null } | null;
  totals?: { state: 'available'; currency?: string | null; month: { cost: number; kwh: number } | null; year: { cost: number; kwh: number }; year_from: string | null } | { state: 'unavailable'; reason: string };
  consumption?: { state: 'available'; total_kwh: number; hours_reported: number; paid_average_price: number | null } | { state: 'unavailable'; reason: string };
}

export interface SolarDay {
  state: DataState; reason?: string; site_name?: string | null; peak_kw?: number | null; current_kw?: number | null;
  today_kwh?: number | null; month_kwh?: number | null; lifetime_kwh?: number | null; last_update?: string | null; checked_at?: string;
  expected_state?: 'forecast' | 'unconfigured' | 'unavailable'; now_hour?: number;
  hours?: { hour: number; kwh: number | null; expected_kwh: number | null }[];
}

export interface BestWindow {
  start: string; end: string; day: 'today' | 'tomorrow'; average_price: number; solar_kw: number | null; saving_vs_average: number; worth_moving: boolean;
}
export interface Windows {
  state: DataState; reason?: string; basis?: 'price' | 'price_and_solar'; hours?: number; currency?: string | null; source?: string;
  tomorrow_included?: boolean; windows?: BestWindow[]; average_price?: number | null; checked_at?: string;
}

export const ENERGY_KEYS = { price: ['energy', 'pricing'], solar: ['energy', 'solar'], windows: ['energy', 'suggestions'], connections: ['energy', 'connections'] } as const;

const REFRESH = 5 * 60_000;
export const usePriceDay = (which: 'today' | 'tomorrow', enabled = true) =>
  useQuery({ queryKey: [...ENERGY_KEYS.price, which], queryFn: () => api<PriceDay>(`/api/energy/pricing/day?date=${which}`), refetchInterval: REFRESH, enabled });
export const useSolarDay = () => useQuery({ queryKey: ENERGY_KEYS.solar, queryFn: () => api<SolarDay>('/api/energy/solar/day'), refetchInterval: REFRESH });
export const useWindows = (hours = 2) =>
  useQuery({ queryKey: [...ENERGY_KEYS.windows, hours], queryFn: () => api<Windows>(`/api/energy/suggestions/windows?hours=${hours}`), refetchInterval: REFRESH });

/** Tibber prices are per kWh in the home's currency. Euro prices read better as cents. */
export function fmtPrice(value: number | null | undefined, currency?: string | null): string {
  if (value === null || value === undefined) return '–';
  if (!currency || currency === 'EUR') return `${(value * 100).toFixed(1)} ct`;
  return `${value.toFixed(2)} ${currency}`;
}
/** Amounts of money (not per-kWh prices): whole currency units with the right symbol. */
export const fmtMoney = (value: number, currency?: string | null) =>
  new Intl.NumberFormat(undefined, { style: 'currency', currency: currency ?? 'EUR', maximumFractionDigits: value >= 1000 ? 0 : 2 }).format(value);
export const fmtKwh = (value: number | null | undefined, digits = 1) => (value === null || value === undefined ? '–' : `${value.toFixed(digits)} kWh`);
export const fmtHour = (hour: number) => `${String(hour).padStart(2, '0')}:00`;
export const fmtPct = (ratio: number | null | undefined) => (ratio === null || ratio === undefined ? '' : `${ratio > 0 ? '+' : ratio < 0 ? '−' : ''}${Math.abs(Math.round(ratio * 100))}%`);

/** How an hour's price compares with the day's average: drives colour (cheap / normal / pricey). */
export type Band = 'cheap' | 'normal' | 'pricey';
export function band(price: number | null, average: number | null | undefined): Band {
  if (price === null || !average) return 'normal';
  const ratio = (price - average) / average;
  return ratio <= -0.1 ? 'cheap' : ratio >= 0.1 ? 'pricey' : 'normal';
}
