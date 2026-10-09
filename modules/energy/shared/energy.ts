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

export const ENERGY_KEYS = { price: ['energy', 'pricing'], solar: ['energy', 'solar'], windows: ['energy', 'suggestions'], connections: ['energy', 'connections'], water: ['energy', 'water'] } as const;

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

/** Water from hand-entered meter readings (state `manual`). Household use is total minus garden; periods between readings are flagged. */
export interface WaterUse { value: number; from: string; to: string; estimated: boolean; partial: boolean }
export interface WaterPeriod { label: string; total: WaterUse | null; garden: WaterUse | null; household: WaterUse | null }
export interface WaterReading { value: number; since: { from: string; days: number; used: number } | null }
export interface WaterAmount { m3: number; litres_per_day: number }
export interface WaterInterval { from: string; to: string; days: number; total: WaterAmount; garden?: WaterAmount; household?: WaterAmount }
export interface WaterTrend { key: 'household' | 'total'; from: string; to: string; litres_per_day: number; previous: number; baseline: number; overall: number; vs_previous: number | null; vs_baseline: number | null; periods: number }
export interface WaterView {
  /** Average use per day between consecutive readings. `trend` appears only once there are two periods (three readings). */
  intervals?: { basis: 'household' | 'total'; items: WaterInterval[]; trend: WaterTrend | null };
  state: DataState; reason?: 'no_household' | 'no_readings'; unit: 'm3';
  months?: WaterPeriod[]; years?: WaterPeriod[]; warnings?: string[]; first?: string; last?: string;
  rows?: { read_on: string; note: string; total: WaterReading | null; garden: WaterReading | null }[];
}
export const useWater = () => useQuery({ queryKey: ENERGY_KEYS.water, queryFn: () => api<WaterView>('/api/energy/water/readings') });
export const fmtM3 = (value: number | null | undefined) => (value === null || value === undefined ? '–' : `${value.toFixed(Math.abs(value) < 100 ? 2 : 1)} m³`);
/** The newest month that the readings cover completely (so a few days after the last reading never headlines); falls back to the newest month. */
export const latestFullMonth = (months: WaterPeriod[]): WaterPeriod | undefined =>
  [...months].reverse().find((m) => m.total && !m.total.partial && (!m.household || !m.household.partial)) ?? months[months.length - 1];
export const fmtLpd = (value: number | null | undefined) => (value === null || value === undefined ? '–' : `${Math.round(value)} L/day`);
