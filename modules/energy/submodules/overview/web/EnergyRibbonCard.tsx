import { Link, type CardProps } from '@chit/core';
import '../../../shared/energy.css';
import { fmtKwh, fmtMoney, fmtPrice, usePriceDay } from '../../../shared/energy';

/**
 * Today's electricity cost in the top bar: what the hours Tibber has reported so far cost, plus the price right now.
 * Hours without a reading are left out, so the figure only ever counts consumption that was measured.
 */
export default function EnergyRibbonCard(_: CardProps) {
  const { data, isPending } = usePriceDay('today');
  if (isPending || !data) return <div className="en-rib bubble" aria-busy="true"><div className="skeleton" style={{ width: 90, margin: 0 }} /></div>;
  if (data.state === 'unconfigured') return null;   // no Tibber connection: the Grid page explains how to add it
  if (data.state === 'unavailable' || !data.hours) {
    return <Link className="en-rib bubble" to="/grid" title="Tibber could not be reached"><small>Power today</small><b>–</b></Link>;
  }
  const measured = data.hours.filter((hour) => hour.consumption !== null && hour.price !== null);
  const kwh = measured.reduce((sum, hour) => sum + (hour.consumption ?? 0), 0);
  const cost = measured.reduce((sum, hour) => sum + (hour.consumption ?? 0) * (hour.price ?? 0), 0);
  const stale = data.state === 'stale';
  return (
    <Link className="en-rib bubble" to="/grid" title={`Tibber consumption so far today${stale ? ' · provider unreachable, showing the last reading' : ''}`}>
      <small>Power today{stale ? ' · stale' : ''}</small>
      <span className="en-rib__row">
        <b>{measured.length ? fmtMoney(cost, data.currency) : '–'}</b>
        <span>{measured.length ? fmtKwh(kwh) : 'no reading yet'}{data.current ? ` · ${fmtPrice(data.current.price, data.currency)} now` : ''}</span>
      </span>
    </Link>
  );
}
