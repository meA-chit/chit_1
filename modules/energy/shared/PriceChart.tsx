import { fmtHour, fmtKwh, fmtPct, fmtPrice, band, type HourPrice } from './energy';

interface Props {
  hours: HourPrice[]; average: number | null; tomorrow?: (number | null)[]; nowHour: number | null; currency?: string | null;
  selected: number; onSelect: (hour: number) => void;
}

const W = 480, TOP = 12, BOTTOM = 118, SLOT = W / 24, STRIP = BOTTOM + 6;

/**
 * 24 hourly slots. Bars (one colour) = consumption in kWh. Yellow line = hourly price, dashed line = the day's average
 * price. The thin strip under the bars colours each hour by price against the average (green below, pink above).
 * Hours without a reading have no bar: absence is never drawn as zero.
 */
export function PriceChart({ hours, average, tomorrow, nowHour, currency, selected, onSelect }: Props) {
  const prices = [...hours.map((h) => h.price), ...(tomorrow ?? [])].filter((p): p is number => p !== null);
  if (prices.length === 0) return null;
  const lo = Math.min(...prices), hi = Math.max(...prices), span = hi - lo || 1;
  const y = (price: number) => BOTTOM - 8 - ((price - lo) / span) * (BOTTOM - TOP - 16);
  const maxUse = Math.max(0.5, ...hours.map((h) => h.consumption ?? 0));
  const barHeight = (kwh: number) => Math.max(2, (kwh / maxUse) * (BOTTOM - TOP - 10));

  const line = hours.map((h, i) => (h.price === null ? null : `${i * SLOT},${y(h.price)} ${(i + 1) * SLOT},${y(h.price)}`)).filter(Boolean).join(' ');
  const ahead = (tomorrow ?? []).map((p, i) => (p === null ? null : `${i * SLOT},${y(p)} ${(i + 1) * SLOT},${y(p)}`)).filter(Boolean).join(' ');
  const chosen = hours[selected];
  const chosenTomorrow = tomorrow?.[selected] ?? null;

  return (
    <div className="pc">
      <svg viewBox={`0 0 ${W} 150`} role="img" aria-label="Hourly price and consumption for the day" preserveAspectRatio="none">
        {nowHour !== null && <rect className="pc__now" x={nowHour * SLOT} y={TOP - 6} width={SLOT} height={BOTTOM - TOP + 6} rx="4" />}
        {average !== null && (
          <g>
            <line className="pc__avg" x1="0" x2={W} y1={y(average)} y2={y(average)} />
          </g>
        )}
        {hours.map((h, i) => h.consumption !== null && (
          <rect key={h.hour} className="pc__bar" x={i * SLOT + 4} width={SLOT - 8} rx="2.5"
            y={BOTTOM - barHeight(h.consumption)} height={barHeight(h.consumption)} />
        ))}
        {hours.map((h, i) => <rect key={`band-${h.hour}`} className="pc__strip" data-band={band(h.price, average)} x={i * SLOT + 1} y={STRIP} width={SLOT - 2} height="6" rx="2" />)}
        <text className="pc__label" x="2" y="10">{fmtKwh(maxUse, 1)}</text>
        <text className="pc__label pc__label--price" x={W - 2} y="10" textAnchor="end">{fmtPrice(hi, currency)}</text>
        <text className="pc__label pc__label--price" x={W - 2} y={BOTTOM - 2} textAnchor="end">{fmtPrice(lo, currency)}</text>
        {ahead && <polyline className="pc__line pc__line--tomorrow" points={ahead} fill="none" />}
        <polyline className="pc__line" points={line} fill="none" />
        {[0, 6, 12, 18, 23].map((h) => <text key={h} className="pc__tick" x={h * SLOT + SLOT / 2} y="146" textAnchor="middle">{String(h).padStart(2, '0')}</text>)}
        {hours.map((h, i) => (
          <rect key={`hit-${h.hour}`} className="pc__hit" x={i * SLOT} y="0" width={SLOT} height={BOTTOM + 4} tabIndex={0} role="button"
            data-selected={selected === h.hour || undefined}
            aria-label={`${fmtHour(h.hour)}, ${fmtPrice(h.price, currency)}${h.consumption !== null ? `, ${fmtKwh(h.consumption, 2)}` : ''}`}
            onMouseEnter={() => onSelect(h.hour)} onFocus={() => onSelect(h.hour)} onClick={() => onSelect(h.hour)} />
        ))}
      </svg>
      {chosen && (
        <p className="pc__readout" aria-live="polite">
          <b className="mono">{fmtHour(chosen.hour)}</b>
          <span>{fmtPrice(chosen.price, currency)}{average && chosen.price !== null && <em data-band={band(chosen.price, average)}> {fmtPct((chosen.price - average) / average)} vs day avg</em>}</span>
          {chosenTomorrow !== null && <span className="pc__tomorrow">tomorrow {fmtPrice(chosenTomorrow, currency)}</span>}
          <span>{chosen.consumption !== null ? fmtKwh(chosen.consumption, 2) : 'no reading'}</span>
        </p>
      )}
    </div>
  );
}
