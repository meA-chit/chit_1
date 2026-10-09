import { describe, expect, it } from 'vitest';
import { dayPart, isValidZone, offsetFrom, timeIn, zoneCode } from './secondClock';

// 21:45 in Germany (CEST, UTC+2) is 01:15 the next day in India (IST, UTC+5:30)
const instant = new Date('2026-10-08T19:45:00Z');

describe('second clock', () => {
  it('tells the time in another zone', () => {
    expect(timeIn(instant, 'Europe/Berlin')).toEqual({ hour: 21, text: '21:45' });
    expect(timeIn(instant, 'Asia/Kolkata')).toEqual({ hour: 1, text: '01:15' });
  });
  it('maps the hour to a part of the day', () => {
    expect([2, 6, 12, 19, 23].map(dayPart)).toEqual(['night', 'morning', 'day', 'evening', 'night']);
    expect(dayPart(5)).toBe('morning');
    expect(dayPart(8)).toBe('day');
    expect(dayPart(17)).toBe('evening');
    expect(dayPart(22)).toBe('night');
  });
  it('gives the offset across a date line', () => {
    expect(offsetFrom(instant, 'Asia/Kolkata', 'Europe/Berlin')).toBe('+3:30 h');
    expect(offsetFrom(instant, 'America/New_York', 'Europe/Berlin')).toBe('−6 h');
    expect(offsetFrom(instant, 'Europe/Berlin', 'Europe/Berlin')).toBe('same time');
  });
  it('knows codes and rejects unknown zones', () => {
    expect(zoneCode('Asia/Kolkata')).toBe('IST');
    expect(isValidZone('Asia/Kolkata')).toBe(true);
    expect(isValidZone('Mars/Olympus')).toBe(false);
  });
});
