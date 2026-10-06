import { describe, expect, it } from 'vitest';
import { detectSurface } from './useSurface';

describe('detectSurface', () => {
  it('infers from width', () => {
    expect(detectSurface('', 390)).toBe('mobile-adult');
    expect(detectSurface('', 900)).toBe('tablet');
    expect(detectSurface('', 1440)).toBe('web');
  });
  it('honours a valid override and ignores junk', () => {
    expect(detectSurface('?surface=tv', 390)).toBe('tv');
    expect(detectSurface('?surface=admin', 1440)).toBe('web');
  });
});
