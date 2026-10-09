import { useMemo } from 'react';
import type { Moment, MomentSource } from '@chit/core';
import { fmtPrice, useWindows } from '../../../shared/energy';

const hhmm = (iso: string) => iso.slice(11, 16);

/**
 * A cheap window for heavy loads, from the same read as the Energy card's best windows. Naive local timestamps from the hub
 * are household time, which is also what the browser shows on a household screen.
 * The value is the price gap per kWh and as a share of the day average: Chit does not know the appliance's kWh, so it never states a total saving.
 */
export function useEnergyMoments(now: Date): MomentSource {
  const query = useWindows(2);
  const data = query.data;
  const moments = useMemo<Moment[]>(() => {
    if (!data || (data.state !== 'available' && data.state !== 'stale') || !data.windows) return [];
    const withSolar = data.basis === 'price_and_solar';
    return data.windows
      .filter((window) => window.worth_moving)
      .map((window) => {
        const start = new Date(window.start);
        const end = new Date(window.end);
        const share = window.saving_vs_average;   // a ratio of the day average (0.36 = 36 % cheaper), not a price
        const gap = data.average_price == null ? null : data.average_price - window.average_price;
        const underway = start.getTime() <= now.getTime();
        return {
          id: `energy/window/${window.start}`,
          module: 'energy',
          kind: 'money' as const,
          title: underway ? `Cheap power until ${hhmm(window.end)}` : `Cheap power ${hhmm(window.start)} to ${hhmm(window.end)}${window.day === 'tomorrow' ? ' tomorrow' : ''}`,
          reason: `Good time for the dishwasher or dryer: ${fmtPrice(window.average_price, data.currency)} per kWh against a day average of ${fmtPrice(data.average_price ?? null, data.currency)}${withSolar && window.solar_kw ? ', with sun expected' : ''}.`,
          at: start,
          until: end,
          value: gap !== null && gap > 0 ? { label: `${fmtPrice(gap, data.currency)} cheaper per kWh, ${Math.round(share * 100)}% under average`, estimated: withSolar } : undefined,
          state: data.state === 'stale' ? 'stale' as const : withSolar ? 'forecast' as const : 'available' as const,
          source: data.source ?? 'Tibber prices',
          checkedAt: data.checked_at,
          action: { label: 'See Grid', to: '/grid' },
        };
      });
  }, [data, now]);
  return { moments, ready: !query.isPending };
}
