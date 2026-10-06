import { describe, expect, it } from 'vitest';
import { clockOf, dayLabel, groupByDay, type AgendaEvent } from './agenda';

const ev = (start: string, extra: Partial<AgendaEvent> = {}): AgendaEvent => ({
  title: 't', start, end: start, all_day: false, source: 's', members: [], ...extra,
});

describe('agenda', () => {
  it('groups by household-local day and keeps order', () => {
    const groups = groupByDay([ev('2026-10-07T08:00:00+02:00'), ev('2026-10-07T23:30:00+02:00'), ev('2026-10-08T00:10:00+02:00')]);
    expect(groups.map((g) => [g.day, g.events.length])).toEqual([['2026-10-07', 2], ['2026-10-08', 1]]);
  });
  it('labels all-day events and times', () => {
    expect(clockOf(ev('2026-10-07T00:00:00', { all_day: true }))).toBe('All day');
    expect(clockOf(ev('2026-10-07T19:30:00+02:00'))).toBe('19:30');
  });
  it('labels today and tomorrow', () => {
    expect(dayLabel('2026-10-07', '2026-10-07')).toBe('Today');
    expect(dayLabel('2026-10-08', '2026-10-07')).toBe('Tomorrow');
  });
});
