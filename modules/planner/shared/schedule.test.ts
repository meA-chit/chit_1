import { describe, expect, it } from 'vitest';
import { describeDays, describePart } from './schedule';

const parts = [{ id: 'morning', label: 'Morning', start: '07:00', end: '09:00' }];

describe('schedule wording', () => {
  it('describes day sets in words', () => {
    expect(describeDays([])).toBe('Every day');
    expect(describeDays(['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])).toBe('Weekdays');
    expect(describeDays(['sunday', 'saturday'])).toBe('Weekends');
    expect(describeDays(['tuesday', 'friday'])).toBe('Tue, Fri');
  });
  it('describes a zone with its hours and falls back to any time', () => {
    expect(describePart('morning', parts)).toBe('Morning (07:00 to 09:00)');
    expect(describePart(null, parts)).toBe('Any time');
    expect(describePart('unknown', parts)).toBe('Any time');
  });
});
