import { describe, expect, it } from 'vitest';
import { countdown, rankMoments } from './rank';
import type { Moment } from './types';

const now = new Date('2026-10-08T14:00:00');
const at = (hours: number, minutes = 0) => new Date(now.getTime() + (hours * 60 + minutes) * 60_000);
const moment = (over: Partial<Moment>): Moment => ({
  id: 'm', module: 'x', kind: 'info', title: 't', reason: 'r', at: at(1), state: 'available', source: 's', ...over,
});

describe('rankMoments', () => {
  it('orders by urgency and bounds the hero list', () => {
    const list = [moment({ id: 'late', at: at(9) }), moment({ id: 'soon', at: at(0, 20) }), moment({ id: 'mid', at: at(3) }), moment({ id: 'next', at: at(5) })];
    const { hero, quiet } = rankMoments(list, now);
    expect(hero.map((m) => m.id)).toEqual(['soon', 'mid', 'next']);
    expect(quiet.map((m) => m.id)).toEqual(['late']);
  });
  it('drops expired, hidden and unsupported moments', () => {
    const list = [
      moment({ id: 'over', at: at(-2), until: at(-1) }),
      moment({ id: 'snoozed' }),
      moment({ id: 'demo', state: 'demo' }),
      moment({ id: 'nodata', state: 'unavailable' }),
      moment({ id: 'ok' }),
    ];
    const { hero, quiet } = rankMoments(list, now, new Set(['snoozed']));
    expect([...hero, ...quiet].map((m) => m.id)).toEqual(['ok']);
  });
  it('keeps a moment that is already under way', () => {
    const { hero } = rankMoments([moment({ id: 'now', at: at(-0, -10), until: at(1) })], now);
    expect(hero.map((m) => m.id)).toEqual(['now']);
  });
  it('ranks forecast and stale evidence below live evidence at equal urgency', () => {
    const { hero } = rankMoments([moment({ id: 'f', state: 'forecast' }), moment({ id: 'a' }), moment({ id: 's', state: 'stale' })], now);
    expect(hero.map((m) => m.id)).toEqual(['a', 'f', 's']);
  });
  it('is stable on ties', () => {
    const list = [moment({ id: 'b' }), moment({ id: 'a' })];
    expect(rankMoments(list, now).hero.map((m) => m.id)).toEqual(['a', 'b']);
  });
});

describe('countdown', () => {
  it('reads naturally', () => {
    expect(countdown(moment({ at: at(0, 38) }), now)).toBe('in 38 min');
    expect(countdown(moment({ at: at(2, 5) }), now)).toBe('in 2 h 5 min');
    expect(countdown(moment({ at: at(-0, -5) }), now)).toBe('now');
  });
});
