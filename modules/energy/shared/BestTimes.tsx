import { useState } from 'react';
import { fmtPrice, useWindows, type BestWindow } from './energy';

const time = (iso: string) => iso.slice(11, 16);

function describe(window: BestWindow) {
  if (window.solar_kw) return `about ${window.solar_kw.toFixed(1)} kW of your own solar expected`;
  if (!window.worth_moving) return 'prices are flat, no real saving';
  return `${Math.round(window.saving_vs_average * 100)}% below the average price`;
}

/** The two best windows for heavy loads (washing, drying, dishwasher, EV). Read-only: Chit never switches a device. */
export function BestTimes() {
  const [hours, setHours] = useState(2);
  const { data, isPending } = useWindows(hours);
  if (isPending || !data || data.state === 'unconfigured' || data.state === 'unavailable') return null;
  const windows = data.windows ?? [];

  return (
    <section className="bt" aria-label="Best times for heavy loads">
      <div className="bt__head">
        <h3>Best times for heavy loads</h3>
        <div className="seg seg--mini" role="tablist" aria-label="Run length">
          {[1, 2, 3, 4].map((h) => <button key={h} role="tab" aria-selected={hours === h} onClick={() => setHours(h)}>{h} h</button>)}
        </div>
      </div>
      {windows.length === 0 ? (
        <p className="en-note">No {hours}-hour stretch of known prices is left. Tomorrow’s prices arrive around 13:00.</p>
      ) : windows.map((window, index) => (
        <div key={window.start} className="sug">
          <span className="sug__rank" data-first={index === 0 || undefined}>{index + 1}</span>
          <div>
            <b>{window.day === 'today' ? 'Today' : 'Tomorrow'} {time(window.start)} to {time(window.end)}</b>
            <small>{fmtPrice(window.average_price, data.currency)} on average · {describe(window)}</small>
          </div>
        </div>
      ))}
      <p className="en-note">Ranked by the cheapest average price{data.basis === 'price_and_solar' ? ', with sunny hours counted cheaper (solar is an estimate)' : ''}. Chit only suggests; it never switches devices.</p>
    </section>
  );
}
