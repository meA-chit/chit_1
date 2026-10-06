import { describe, expect, it } from 'vitest';
import type { AgendaEvent } from './agenda';
import { addDays, dayTitle, fmt, hoursIn, inText, joinTitles, layoutLane, mergeFeedEvents, mergeTravel, nextUp, packRows, pct, place, type Block, type Lane } from './timeline';

const block = (over: Partial<Block>): Block => ({ id: 'b', title: 't', kind: 'work', source: 'routine', start: '08:00', end: '09:00', ...over });
const lane = (name: string, blocks: Block[]): Lane => ({ member_id: name.toLowerCase(), name, role: 'adult', avatar: 'a1', color: '#fff', blocks });

describe('timeline math', () => {
  it('maps 06:00-22:00 onto 0-100%', () => {
    expect(pct(6)).toBe(0);
    expect(pct(14)).toBe(50);
    expect(pct(22)).toBe(100);
    expect(pct(3)).toBe(0); // clipped
  });

  it('places, clips and drops blocks and flags past/active', () => {
    const placed = place([block({ start: '08:00', end: '10:00' }), block({ start: '05:00', end: '05:30' }), block({ start: '21:00', end: '23:30' })], 9);
    expect(placed).toHaveLength(2);
    expect(placed[0]).toMatchObject({ left: 12.5, width: 12.5, active: true, past: false });
    expect(placed[1]!.left + placed[1]!.width).toBe(100);
  });

  it('an unknown start is drawn from the day start and flagged, never invented', () => {
    const [placed] = place([block({ start: null, end: '15:30' })], 12);
    expect(placed).toMatchObject({ openStart: true, left: 0 });
  });

  it('next-up ignores long blocks and picks the earliest trip', () => {
    const lanes = [lane('Nina', [block({ start: '08:30', end: '16:30' }), block({ kind: 'pickup', start: '15:30', end: '15:45', title: 'Pick up Mila' }), block({ kind: 'pickup', start: '14:30', end: '14:40', title: 'Pick up Leo' })])];
    expect(nextUp(lanes, 12.4)).toEqual({ title: 'Pick up Leo', who: 'Nina', minutes: 126 });
    expect(nextUp(lanes, 17)).toBeNull();
  });

  it('formats', () => {
    expect(fmt(12.4)).toBe('12:24');
    expect(inText(126)).toBe('2h 6m');
    expect(inText(9)).toBe('9m');
  });

  it('hoursIn reads the household time zone, not the viewer', () => {
    const noonUtc = new Date('2026-10-06T12:00:00Z');
    expect(hoursIn('Europe/Berlin', noonUtc)).toBe(14);
    expect(hoursIn('UTC', noonUtc)).toBe(12);
  });
});

describe('feed events', () => {
  const ev = (over: Partial<AgendaEvent>): AgendaEvent => ({ title: 'e', start: '2026-10-06T17:00:00+02:00', end: '2026-10-06T18:00:00+02:00', all_day: false, source: 's', members: [], ...over });
  const lanes = [lane('Nina', []), lane('Jonas', [])];

  it('one member goes to their lane; none or several go to Family', () => {
    const merged = mergeFeedEvents(lanes, [ev({ members: ['Nina'] }), ev({ title: 'Dinner', members: [] }), ev({ title: 'Both', members: ['Nina', 'Jonas'] })], '2026-10-06');
    expect(merged.find((l) => l.name === 'Nina')!.blocks.map((b) => b.title)).toEqual(['e']);
    expect(merged.find((l) => l.name === 'Family')!.blocks.map((b) => b.title)).toEqual(['Dinner', 'Both']);
  });

  it('reuses a Family lane the server already provided (reminders)', () => {
    const withFamily = [...lanes, { ...lane('Family', [block({ id: 'rem', kind: 'reminder' })]), member_id: 'family' }];
    const merged = mergeFeedEvents(withFamily, [ev({ title: 'Dinner', members: [] })], '2026-10-06');
    expect(merged.filter((l) => l.member_id === 'family')).toHaveLength(1);
    expect(merged.find((l) => l.member_id === 'family')!.blocks.map((b) => b.title)).toEqual(['t', 'Dinner']);
  });

  it('ignores other days and does not add an empty Family lane', () => {
    const merged = mergeFeedEvents(lanes, [ev({ start: '2026-10-07T17:00:00+02:00' })], '2026-10-06');
    expect(merged).toHaveLength(2);
  });
});


describe('compact lanes', () => {
  it('joins pick-up and drop-off names', () => {
    expect(joinTitles(['Drop off Mila', 'Drop off Leo'])).toBe('Drop off Mila, Leo');
    expect(joinTitles(['Drop off Mila', 'Commute'])).toBe('Drop off Mila · Commute');
    expect(joinTitles(['Pick up Leo', 'Pick up Leo'])).toBe('Pick up Leo');
  });

  it('merges travel within 15 minutes into one block and leaves distant trips alone', () => {
    const merged = mergeTravel([
      block({ id: 'a', kind: 'dropoff', title: 'Drop off Mila', start: '07:45', end: '08:00' }),
      block({ id: 'b', kind: 'dropoff', title: 'Drop off Leo', start: '08:05', end: '08:15' }),
      block({ id: 'c', kind: 'pickup', title: 'Pick up Leo', start: '14:30', end: '14:40' }),
      block({ id: 'w', kind: 'work', title: 'Work', start: '08:30', end: '16:30' }),
    ]);
    expect(merged.filter((b) => b.kind === 'dropoff')).toHaveLength(1);
    expect(merged.find((b) => b.kind === 'dropoff')).toMatchObject({ title: 'Drop off Mila, Leo', start: '07:45', end: '08:15' });
    expect(merged).toHaveLength(3);
  });

  it('commute next to a school run becomes a single travel block', () => {
    const merged = mergeTravel([block({ kind: 'commute', title: 'Commute', start: '07:00', end: '07:30' }), block({ kind: 'dropoff', title: 'Drop off Mila', start: '07:35', end: '07:50' })]);
    expect(merged).toHaveLength(1);
    expect(merged[0]).toMatchObject({ kind: 'travel', start: '07:00', end: '07:50' });
  });

  it('never merges a block whose start is unknown', () => {
    expect(mergeTravel([block({ kind: 'commute', start: null, end: '09:00' }), block({ kind: 'commute', start: '09:00', end: '09:30' })])).toHaveLength(2);
  });

  it('packs non-overlapping blocks into one row and only stacks real overlaps', () => {
    const seq = layoutLane([block({ id: '1', start: '06:50', end: '07:30', kind: 'commute' }), block({ id: '2', start: '07:30', end: '15:30' }), block({ id: '3', start: '15:30', end: '16:10', kind: 'commute' })], 12);
    expect(seq.rows).toBe(1);
    const overlap = layoutLane([block({ id: '1', start: '08:30', end: '16:30' }), block({ id: '2', start: '14:30', end: '14:40', kind: 'pickup' })], 12);
    expect(overlap.rows).toBe(2);
    expect(packRows([]).rows).toBe(1);
  });

  it('titles days relative to today', () => {
    expect(addDays('2026-10-31', 1)).toBe('2026-11-01');
    expect(dayTitle('2026-10-06', '2026-10-06')).toBe('Today');
    expect(dayTitle('2026-10-07', '2026-10-06')).toBe('Tomorrow');
    expect(dayTitle('2026-10-09', '2026-10-06')).toBe('Fri 9 Oct');
  });
});
