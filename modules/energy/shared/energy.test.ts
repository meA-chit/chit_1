import { describe, expect, it } from 'vitest';
import { band, fmtHour, fmtPct, fmtPrice } from './energy';

describe('energy formatting', () => {
  it('shows euro prices as cents and other currencies as they are', () => {
    expect(fmtPrice(0.2513, 'EUR')).toBe('25.1 ct');
    expect(fmtPrice(1.234, 'NOK')).toBe('1.23 NOK');
    expect(fmtPrice(null, 'EUR')).toBe('–');
  });

  it('bands an hour against the day average (±10%)', () => {
    expect(band(0.2, 0.3)).toBe('cheap');
    expect(band(0.32, 0.3)).toBe('normal');
    expect(band(0.34, 0.3)).toBe('pricey');
    expect(band(null, 0.3)).toBe('normal');
    expect(band(0.2, null)).toBe('normal');
  });

  it('formats comparisons and hours', () => {
    expect(fmtPct(-0.213)).toBe('−21%');
    expect(fmtPct(0.04)).toBe('+4%');
    expect(fmtPct(0)).toBe('0%');
    expect(fmtHour(7)).toBe('07:00');
  });
});
