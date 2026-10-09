import { describe, expect, it } from 'vitest';
import { parsePaste } from './WaterPanel';

describe('parsePaste', () => {
  it('reads date, total and garden separated by spaces, tabs, semicolons or commas', () => {
    const { rows, bad } = parsePaste('2025-01-01 812.345 40.1\n2025-02-01;830.12;44\n2025-03-01,845.9,-\n2025-04-01\t860\t');
    expect(bad).toEqual([]);
    expect(rows).toEqual([
      { read_on: '2025-01-01', total: '812.345', garden: '40.1' }, { read_on: '2025-02-01', total: '830.12', garden: '44' },
      { read_on: '2025-03-01', total: '845.9', garden: undefined }, { read_on: '2025-04-01', total: '860', garden: undefined }]);
  });
  it('skips blank lines and reports unreadable ones by line number instead of guessing', () => {
    const { rows, bad } = parsePaste('2025-01-01 10 1\n\nnot a date 5\n2025-02-01 abc\n2025-03-01 - -');
    expect(rows).toHaveLength(1);
    expect(bad).toEqual([3, 4, 5]);
  });
});
