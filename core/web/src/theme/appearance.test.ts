import { describe, expect, it } from 'vitest';
import { resolveMode } from './appearance';

describe('appearance', () => {
  it('keeps an explicit mode as chosen', () => {
    expect(resolveMode('dark')).toBe('dark');
    expect(resolveMode('light')).toBe('light');
  });
  it('falls back to dark when the device cannot say (no window)', () => {
    expect(resolveMode('auto')).toBe('dark');
  });
});
