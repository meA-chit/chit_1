import { useState } from 'react';
import { BoltIcon, CardFrame, Empty, Link, type CardProps, type DataState } from '@chit/core';
import { fmtHour, fmtKwh, fmtMoney, fmtPct, fmtPrice, usePriceDay } from '../../../shared/energy';
import { BestTimes } from '../../../shared/BestTimes';
import { PriceChart } from '../../../shared/PriceChart';
import { Loading } from '../../../shared/Loading';
import '../../../shared/energy.css';

const REASONS: Record<string, string> = {
  token_rejected: 'Tibber did not accept the saved token. Update it in the household energy settings.',
  rate_limited: "Tibber's request limit was reached. This refreshes on its own.",
  unavailable: 'Chit could not reach Tibber just now. Nothing is shown rather than a guess.',
};

/** Hourly consumption against the hourly price for the day, from the household's Tibber connection. */
export default function EnergyNowCard({ card, embedded }: CardProps) {
  const [picked, setPicked] = useState<number | null>(null);
  const { data, isPending, isError } = usePriceDay('today');
  const next = usePriceDay('tomorrow', data?.tomorrow_available === true);   // overlaid on the same chart once published
  const frame = { title: card.title, icon: <BoltIcon />, tone: '#ffc857', embedded } as const;

  if (isPending) return <Loading embedded={embedded} />;
  if (isError || !data) return <CardFrame {...frame} state="unavailable"><Empty title="Energy unavailable">The hub could not be reached.</Empty></CardFrame>;
  if (data.state === 'unconfigured') {
    return (
      <CardFrame {...frame} state="unconfigured" subtitle="Tibber prices and your consumption">
        <Empty title="Connect Tibber" action={<Link className="btn" to="/household#section-energy">Add your Tibber token</Link>}>
          {data.reason === 'no_household' ? 'Set up a household first.' : 'Add your Tibber API token in the household energy settings to see hourly prices and consumption.'}
        </Empty>
      </CardFrame>
    );
  }
  if (data.state === 'unavailable' || !data.hours) {
    return <CardFrame {...frame} state="unavailable"><Empty title="Prices unavailable">{REASONS[data.reason ?? 'unavailable']}</Empty></CardFrame>;
  }

  const hours = data.hours, cons = data.consumption;
  const selected = picked ?? data.now_hour ?? data.cheapest_hour ?? 12;
  const state: DataState = data.state;
  const cur = data.current;
  const tomorrow = next.data?.hours?.map((h) => h.price);
  const tomorrowAvg = next.data?.average_price;
  const totals = data.totals;
  const provenance = [`Tibber · checked ${new Date(data.checked_at ?? Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`, ...(state === 'stale' ? ['provider unreachable, showing the last reading'] : [])];

  return (
    <CardFrame {...frame} state={state} subtitle="Hourly use against price" provenance={provenance}>
      <div className="en-kpi">
        {cur ? (
          <>
            <b>{fmtPrice(cur.price, data.currency)}</b><span>now / kWh</span>
            {cur.vs_average !== null && <span className="en-vs" data-dir={cur.vs_average < 0 ? 'down' : 'up'}>{fmtPct(cur.vs_average)} vs day avg</span>}
          </>
        ) : (
          <><b>{fmtPrice(data.average_price, data.currency)}</b><span>average / kWh</span></>
        )}
        {cons?.state === 'available' && <span className="en-used mono">{fmtKwh(cons.total_kwh)} used so far</span>}
      </div>

      <PriceChart hours={hours} average={data.average_price ?? null} tomorrow={tomorrow} nowHour={data.now_hour ?? null} currency={data.currency}
        selected={selected} onSelect={setPicked} />

      <div className="en-legend">
        <span><i data-bar /> used per hour (kWh)</span><span><i data-line /> price per kWh</span>{tomorrow && <span><i data-tomorrow /> tomorrow’s price</span>}
        <span><i data-band="cheap" /><i data-band="normal" /><i data-band="pricey" /> strip: price below / about / above the day average</span>
      </div>

      <div className="en-price">
        <span>Day average <b className="mono">{fmtPrice(data.average_price, data.currency)}</b></span>
        {data.cheapest_hour !== null && data.cheapest_hour !== undefined && <span style={{ color: 'var(--lime)' }}>Cheapest {fmtHour(data.cheapest_hour)}</span>}
        {data.priciest_hour !== null && data.priciest_hour !== undefined && <span style={{ color: 'var(--magenta)' }}>Priciest {fmtHour(data.priciest_hour)}</span>}
      </div>
      {cons?.state === 'available' && cons.paid_average_price !== null && data.average_price ? (
        <p className="en-note">
          You paid <b className="mono">{fmtPrice(cons.paid_average_price, data.currency)}</b> per kWh on average today, {fmtPct((cons.paid_average_price - data.average_price) / data.average_price)} against the day’s average price.
        </p>
      ) : cons?.state === 'unavailable' ? (
        <p className="en-note">
          {cons.reason === 'provider_error' ? 'Consumption could not be read from Tibber just now.' : 'Tibber has no consumption readings for this home (it needs a Pulse or a smart-meter connection). Prices only.'}
        </p>
      ) : null}
      {tomorrowAvg ? <p className="en-note">Tomorrow’s average price is <b className="mono">{fmtPrice(tomorrowAvg, data.currency)}</b>, {fmtPct((tomorrowAvg - (data.average_price ?? tomorrowAvg)) / (data.average_price ?? tomorrowAvg))} against today.</p> : null}
      {totals?.state === 'available' && (
        <div className="en-totals" aria-label="Consumption cost so far">
          <div className="en-total"><small>Month to date</small><b>{totals.month ? fmtMoney(totals.month.cost, totals.currency) : '–'}</b><span>{totals.month ? fmtKwh(totals.month.kwh, 0) : 'no reading yet'}</span></div>
          <div className="en-total"><small>Year to date</small><b>{fmtMoney(totals.year.cost, totals.currency)}</b><span>{fmtKwh(totals.year.kwh, 0)}{totals.year_from ? ` · since ${totals.year_from}` : ''}</span></div>
        </div>
      )}
      <BestTimes />
    </CardFrame>
  );
}
