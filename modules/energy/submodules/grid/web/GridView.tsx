import { useState, type ReactNode } from 'react';
import { BoltIcon, CardsIcon, CheckIcon, ChipIcon, ClockIcon, Link, SparkIcon, StateBadge, SunIcon, ThermoIcon, useClock, type DataState } from '@chit/core';
import { fmtHour, fmtKwh, fmtLpd, fmtMoney, fmtPct, fmtPrice, usePriceDay, useSolarDay, useWater, useWindows, type HourPrice } from '../../../shared/energy';
import WaterPanel from '../../water/web/WaterPanel';
import { PriceChart } from '../../../shared/PriceChart';
import { DEMO_AUTOMATIONS, DEMO_DEVICES, DEMO_METER, DEMO_ROOMS, DEMO_WATER, FALLBACK_PRICE_EUR_PER_KWH, HMIP_MAPPING, type DemoAutomation, type DemoDevice } from './grid.demo';
import '../../../shared/energy.css';
import './grid.css';

/**
 * The Grid: energy prices, solar, and the devices that use the power, on one page.
 * Order is deliberate: what Chit expects to happen (insights), what it costs, what uses it, what is scheduled, how devices connect.
 * Prices, solar and totals are real once Tibber/SolarEdge are connected. Everything that comes from HomematicIP is DEMO
 * (no connector yet) and wears a demo badge; a tile that mixes the two says which part is which.
 */

const WaterIcon = () => <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 3s6 6.4 6 11a6 6 0 01-12 0c0-4.6 6-11 6-11z" /></svg>;
const KIND_COLOR: Record<DemoAutomation['kind'], string> = { heating: 'var(--amber)', ventilation: 'var(--cyan)', appliance: 'var(--lime)', ev: 'var(--violet)', lighting: 'var(--magenta)' };

/** Best and worst run of `len` consecutive priced hours, by average price. */
function runs(hours: HourPrice[], len: number) {
  type Run = { start: number; avg: number };
  let best: Run | null = null, worst: Run | null = null;
  for (let start = 0; start + len <= hours.length; start++) {
    const slice = hours.slice(start, start + len);
    if (slice.some((h) => h.price === null)) continue;
    const avg = slice.reduce((sum, h) => sum + (h.price as number), 0) / len;
    if (!best || avg < best.avg) best = { start, avg };
    if (!worst || avg > worst.avg) worst = { start, avg };
  }
  return { best, worst };
}
const span = (start: number, len: number) => `${fmtHour(start)} to ${fmtHour((start + len) % 24)}`;

interface Insight { id: string; icon: ReactNode; tone: string; lead: string; headline: ReactNode; detail: string; basis: DataState; source: string }

function Tile({ label, value, sub, state, icon, tone, jump }: { label: string; value: string; sub?: string; state: DataState; icon?: ReactNode; tone?: string; /** id of the card on this page to scroll to */ jump?: string }) {
  return (
    <div className="gr-stat" data-jump={jump ? true : undefined} onClick={jump ? () => document.getElementById(jump)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) : undefined} role={jump ? 'link' : undefined} tabIndex={jump ? 0 : undefined} onKeyDown={jump ? (e) => { if (e.key === 'Enter') document.getElementById(jump)?.scrollIntoView({ behavior: 'smooth' }); } : undefined} style={tone ? ({ '--c': tone } as React.CSSProperties) : undefined}>
      <div className="gr-stat__top"><span className="gr-stat__label">{icon}{label}</span><StateBadge state={state} /></div>
      <b className="gr-stat__value mono">{value}</b>
      {sub && <small>{sub}</small>}
    </div>
  );
}

function Spark({ values }: { values: number[] }) {
  const max = Math.max(...values, 0.01);
  return (
    <svg className="gr-spark" viewBox={`0 0 ${values.length * 6} 24`} preserveAspectRatio="none" aria-hidden>
      {values.map((v, i) => <rect key={i} x={i * 6} width={4.4} rx={1.2} y={24 - Math.max(v > 0 ? 2 : 0.6, (v / max) * 22)} height={Math.max(v > 0 ? 2 : 0.6, (v / max) * 22)} />)}
    </svg>
  );
}

function DeviceRow({ device, price, rank, max }: { device: DemoDevice; price: number; rank: number; max: number }) {
  const cost = device.todayKwh * price;
  return (
    <li className="gr-dev" data-mode={device.mode}>
      <span className="gr-dev__rank mono">{rank}</span>
      <div className="gr-dev__main">
        <div className="gr-dev__name"><b>{device.name}</b><small>{device.room} · {device.model}</small></div>
        <div className="gr-dev__bar" aria-hidden><i style={{ width: `${Math.max(3, (device.todayKwh / max) * 100)}%` }} /></div>
        {device.note && <small className="gr-dev__note">{device.note}</small>}
      </div>
      <Spark values={device.hourly} />
      <div className="gr-dev__nums mono">
        <span data-on={device.watts > 20 || undefined}>{device.watts > 0 ? `${device.watts} W` : 'off'}</span>
        <b>{device.todayKwh.toFixed(1)} kWh</b>
        <small>{fmtMoney(cost)}</small>
      </div>
    </li>
  );
}

function Automations({ now }: { now: string }) {
  const items = [...DEMO_AUTOMATIONS].sort((a, b) => a.at.localeCompare(b.at));
  const nextId = items.find((a) => a.at >= now)?.id ?? items[0]!.id;   // after the last one today, the next is tomorrow's first
  return (
    <ol className="gr-auto">
      {items.map((a) => (
        <li key={a.id} data-next={a.id === nextId || undefined} data-past={a.at < now && a.id !== nextId || undefined} style={{ '--c': KIND_COLOR[a.kind] } as React.CSSProperties}>
          <span className="gr-auto__time mono">{a.at}{a.until && <small>to {a.until}</small>}</span>
          <i className="gr-auto__dot" aria-hidden />
          <div className="gr-auto__body">
            <b>{a.title}</b>
            <small>{a.device} · {a.why}</small>
            <span className="gr-auto__src" data-src={a.source === 'Chit suggestion' ? 'chit' : 'hmip'}>{a.source}</span>
          </div>
          {a.id === nextId && <span className="gr-auto__next mono">Next</span>}
        </li>
      ))}
    </ol>
  );
}

function Integration() {
  return (
    <section className="card gr-int" aria-label="HomematicIP integration preview">
      <header className="card__head">
        <div className="card__icon"><ChipIcon /></div>
        <div className="card__titles"><h2 className="card__title">Bring in your HomematicIP devices</h2><p className="card__subtitle">What a connection would add to this page</p></div>
        <StateBadge state="demo" />
      </header>
      <div className="card__body">
        <ol className="gr-flow" aria-label="Connection path">
          <li><span className="gr-flow__n mono">1</span><b>HomematicIP Access Point</b><small>Your HmIP-HAP already pairs every sensor and actuator.</small></li>
          <li><span className="gr-flow__n mono">2</span><b>Home Assistant</b><small>Reads the Access Point through its Homematic IP integration (local or cloud). Read-only token for Chit.</small></li>
          <li><span className="gr-flow__n mono">3</span><b>Chit Grid</b><small>Picks up power meters, thermostats, sensors and schedules, keeps who/when it was read, and shows them here.</small></li>
        </ol>
        <div className="gr-map" role="table" aria-label="What each device type adds">
          <div className="gr-map__row gr-map__row--head" role="row"><span role="columnheader">Device</span><span role="columnheader">What it is</span><span role="columnheader">Shown on the Grid</span><span role="columnheader">Found</span></div>
          {HMIP_MAPPING.map((m) => (
            <div key={m.model} className="gr-map__row" role="row">
              <b className="mono" role="cell">{m.model}</b><span role="cell">{m.what}</span><span role="cell">{m.shows}</span><span className="mono" role="cell">{m.count}</span>
            </div>
          ))}
        </div>
        <p className="en-note">
          Demo: 16 devices found, 9 of them measure power. Chit marks the biggest users as key devices and lets the household unpin any of them.
          Read-only in the pilot: Chit reads states and schedules and never switches a device or edits a profile. The connection itself is the Home Assistant story (US-104); until then the HomematicIP numbers above are examples. Water is typed in by hand in the Water card; a meter on a pulse counter would feed the same readings.
        </p>
      </div>
    </section>
  );
}

export default function GridView() {
  const clock = useClock();
  const nowHm = `${String(clock.getHours()).padStart(2, '0')}:${String(clock.getMinutes()).padStart(2, '0')}`;
  const price = usePriceDay('today');
  const solar = useSolarDay();
  const windows = useWindows(2);
  const water = useWater().data;
  const [picked, setPicked] = useState<number | null>(null);
  const [showAll, setShowAll] = useState(false);

  const day = price.data;
  const hasPrices = day?.state === 'available' || day?.state === 'stale';
  const hours = hasPrices ? day?.hours ?? [] : [];
  const currency = day?.currency ?? 'EUR';
  const live: DataState = day?.state === 'stale' ? 'stale' : 'available';
  const avgPrice = hasPrices ? day?.average_price ?? null : null;
  const paid = day?.consumption?.state === 'available' ? day.consumption.paid_average_price : null;
  const unitPrice = paid ?? avgPrice ?? FALLBACK_PRICE_EUR_PER_KWH;

  /* ---- insights, led by what prices and sun say, applied to the household's own devices ---- */
  const insights: Insight[] = [];
  const cheap3 = hours.length ? runs(hours, 3) : null;
  const pricey3 = cheap3;
  if (cheap3?.best && avgPrice) {
    insights.push({
      id: 'heating', icon: <ThermoIcon />, tone: 'var(--amber)', lead: 'Your heating',
      headline: <>will pre-heat the house <b>{span(cheap3.best.start, 3)}</b>, then coast</>,
      detail: `${fmtPrice(cheap3.best.avg, currency)} per kWh then, ${fmtPct((cheap3.best.avg - avgPrice) / avgPrice)} against today’s average. Rooms hold their target through the evening.`,
      basis: 'demo', source: 'Tibber prices · heating plan is a demo',
    });
  } else {
    insights.push({ id: 'heating', icon: <ThermoIcon />, tone: 'var(--amber)', lead: 'Your heating', headline: <>will pre-heat the house <b>02:00 to 05:00</b>, then coast</>, detail: 'Example plan: the cheapest night hours charge the buffer; the evening peak is skipped. Connect Tibber to base it on your real prices.', basis: 'demo', source: 'demo' });
  }
  const sunnyHour = solar.data?.hours?.reduce<{ hour: number; kwh: number } | null>((best, h) => (h.kwh !== null && (!best || h.kwh > best.kwh) ? { hour: h.hour, kwh: h.kwh } : best), null);
  insights.push(sunnyHour && sunnyHour.kwh > 0.5 && solar.data?.state !== 'unconfigured' ? {
    id: 'vent', icon: <SunIcon />, tone: 'var(--cyan)', lead: 'Your ventilation',
    headline: <>will blow hard <b>{span(Math.max(0, sunnyHour.hour - 1), 3)}</b> while the sun covers it</>,
    detail: `Your plant makes about ${sunnyHour.kwh.toFixed(1)} kWh in the sunniest hour. Quiet mode overnight and while you are out.`, basis: solar.data?.state === 'stale' ? 'stale' : 'available', source: 'SolarEdge · schedule is a demo',
  } : {
    id: 'vent', icon: <SunIcon />, tone: 'var(--cyan)', lead: 'Your ventilation', headline: <>will blow hard <b>11:00 to 15:00</b> when solar peaks</>,
    detail: 'Example: boosts at midday on free sun power, runs quiet overnight and while nobody is home.', basis: 'demo', source: 'demo',
  });
  const best = windows.data?.state === 'available' || windows.data?.state === 'stale' ? windows.data.windows?.[0] : undefined;
  insights.push(best ? {
    id: 'appliances', icon: <BoltIcon />, tone: 'var(--lime)', lead: 'Your dishwasher, dryer and washer',
    headline: <>should run <b>{best.start.slice(11, 16)} to {best.end.slice(11, 16)}</b> {best.day === 'tomorrow' ? 'tomorrow' : 'today'}</>,
    detail: best.worth_moving ? `${Math.round(best.saving_vs_average * 100)}% below the average price. Chit only suggests; it never starts a machine.` : 'Prices are flat, so timing makes little difference today.',
    basis: windows.data?.state === 'stale' ? 'stale' : 'available', source: 'Tibber prices',
  } : {
    id: 'appliances', icon: <BoltIcon />, tone: 'var(--lime)', lead: 'Your dishwasher, dryer and washer', headline: <>should run <b>13:00 to 15:00</b> today</>,
    detail: 'Example. Once Tibber is connected this is the cheapest stretch of real prices.', basis: 'demo', source: 'demo',
  });
  if (pricey3?.worst && avgPrice) {
    insights.push({
      id: 'peak', icon: <ClockIcon />, tone: 'var(--magenta)', lead: 'Your peak to avoid',
      headline: <>is <b>{span(pricey3.worst.start, 3)}</b>, the priciest stretch</>,
      detail: `${fmtPrice(pricey3.worst.avg, currency)} per kWh, ${fmtPct((pricey3.worst.avg - avgPrice) / avgPrice)} against today’s average. Heavy loads wait.`, basis: live, source: 'Tibber prices',
    });
  } else if (water?.state !== 'manual') {
    const used = DEMO_WATER.todayLitres - DEMO_WATER.usualTodayLitres;
    insights.push({ id: 'water', icon: <WaterIcon />, tone: 'var(--cyan)', lead: 'Your water', headline: <>is <b>{Math.round((used / DEMO_WATER.usualTodayLitres) * 100)}% above</b> a usual day so far</>, detail: `${DEMO_WATER.todayLitres} litres against about ${DEMO_WATER.usualTodayLitres}. No overnight flow, so no sign of a leak.`, basis: 'demo', source: 'demo' });
  }
  /* Water insight from the entered meter readings: litres per day between readings, and only once there are two periods to compare. */
  const trend = water?.state === 'manual' ? water.intervals?.trend ?? null : null;
  if (trend) {
    const who = trend.key === 'household' ? 'household water' : 'water';
    const day = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
    insights.push({
      id: 'water', icon: <WaterIcon />, tone: 'var(--cyan)', lead: `Your ${who}`,
      headline: <>averaged <b>{fmtLpd(trend.litres_per_day)}</b> since {day(trend.from)}</>,
      detail: `${trend.vs_previous === null ? '' : `${fmtPct(trend.vs_previous) || '±0%'} against the period before (${fmtLpd(trend.previous)}). `}Your average over earlier readings is ${fmtLpd(trend.baseline)}.${trend.key === 'household' ? ' Household is total minus garden.' : ''}`,
      basis: 'manual', source: `meter readings ${day(trend.from)} to ${day(trend.to)}`,
    });
  }

  /* ---- costs ---- */
  const cons = hours.reduce((sum, h) => sum + (h.consumption ?? 0), 0);
  const todayCost = hours.reduce((sum, h) => sum + (h.consumption !== null && h.price !== null ? h.consumption * h.price : 0), 0);
  const haveToday = hasPrices && day?.consumption?.state === 'available' && cons > 0;
  const totals = day?.totals?.state === 'available' ? day.totals : null;
  const waterCostDay = (DEMO_WATER.todayLitres / 1000) * DEMO_WATER.pricePerM3;
  const sol = solar.data;

  const devices = [...DEMO_DEVICES].sort((a, b) => b.todayKwh - a.todayKwh);
  const keyDevices = devices.filter((d) => d.important);
  const shown = showAll ? devices : keyDevices;
  const maxKwh = Math.max(...devices.map((d) => d.todayKwh));
  const attributed = devices.reduce((s, d) => s + d.todayKwh, 0);
  const selected = picked ?? day?.now_hour ?? day?.cheapest_hour ?? 12;
  const lowBattery = DEMO_ROOMS.filter((r) => r.battery === 'low');

  return (
    <div className="gr">
      <section className="gr-insights" aria-label="Key insights">
        <div className="gr-insights__head">
          <div><div className="eyebrow">Today on the grid</div><h2>What your home will do</h2></div>
          <span className="gr-insights__mix mono"><SparkIcon /> {insights.every((i) => i.basis === 'demo') ? 'all examples until Tibber and HomematicIP are connected' : 'prices and sun are live, device plans are examples'}</span>
        </div>
        <div className="gr-insights__grid">
          {insights.map((i) => (
            <article key={i.id} className="gr-insight" style={{ '--c': i.tone } as React.CSSProperties}>
              <div className="gr-insight__top"><span className="gr-insight__icon">{i.icon}</span><StateBadge state={i.basis} /></div>
              <p className="gr-insight__lead">{i.lead}</p>
              <h3>{i.headline}</h3>
              <p className="gr-insight__detail">{i.detail}</p>
              <small className="gr-insight__src">{i.source}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="gr-stats" aria-label="Costs and usage">
        {haveToday ? <Tile label="Cost today" value={fmtMoney(todayCost, currency)} sub={`${fmtKwh(cons)} so far`} state={live} icon={<BoltIcon />} tone="var(--violet)" />
          : <Tile label="Cost today" value={fmtMoney(DEMO_METER.todayKwh * unitPrice)} sub={`${fmtKwh(DEMO_METER.todayKwh)} on the meter (example)`} state="demo" icon={<BoltIcon />} tone="var(--violet)" />}
        {totals?.month ? <Tile label="This month" value={fmtMoney(totals.month.cost, totals.currency)} sub={fmtKwh(totals.month.kwh, 0)} state={live} tone="var(--violet)" />
          : <Tile label="This month" value={fmtMoney(DEMO_METER.todayKwh * 8 * unitPrice)} sub="example" state="demo" tone="var(--violet)" />}
        {totals ? <Tile label="This year" value={fmtMoney(totals.year.cost, totals.currency)} sub={`${fmtKwh(totals.year.kwh, 0)}${totals.year_from ? ` · since ${totals.year_from}` : ''}`} state={live} tone="var(--violet)" />
          : <Tile label="This year" value={fmtMoney(DEMO_METER.todayKwh * 281 * unitPrice, 'EUR')} sub="example" state="demo" tone="var(--violet)" />}
        {water?.state === 'manual' && (water.intervals?.items.length ?? 0) > 0 ? (() => {
          const items = water.intervals!.items, last = items[items.length - 1]!, t = water.intervals!.trend;
          const own = last.household ?? last.total;
          const day = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
          return <Tile label="Water per day" icon={<WaterIcon />} value={fmtLpd(own.litres_per_day)}
            sub={`${last.household ? 'household' : 'total meter'} · ${day(last.from)} to ${day(last.to)}${t && t.vs_previous !== null ? ` · ${fmtPct(t.vs_previous) || '±0%'} vs before` : ' · trend after the next reading'}`} state="manual" tone="var(--cyan)" jump="water" />;
        })() : water?.state === 'manual' ? <Tile label="Water per day" icon={<WaterIcon />} value="–" sub="needs two readings on different days" state="manual" tone="var(--cyan)" jump="water" />
        : <Tile label="Water today" icon={<WaterIcon />} value={`${DEMO_WATER.todayLitres} L`} sub={`${fmtMoney(waterCostDay)} · month ${(DEMO_WATER.monthLitres / 1000).toFixed(1)} m³ · year ${(DEMO_WATER.yearLitres / 1000).toFixed(1)} m³ · example, add readings in the Water card`} state="demo" tone="var(--cyan)" jump="water" />}
        {sol && sol.state !== 'unconfigured' && sol.state !== 'unavailable' && sol.today_kwh !== null && sol.today_kwh !== undefined
          ? <Tile label="Solar today" icon={<SunIcon />} value={fmtKwh(sol.today_kwh)} sub={sol.month_kwh ? `${fmtKwh(sol.month_kwh, 0)} this month` : undefined} state={sol.state} tone="var(--amber)" />
          : <Tile label="Solar today" icon={<SunIcon />} value="11.8 kWh" sub="example day" state="demo" tone="var(--amber)" />}
      </section>

      <div className="gr-cols">
        <section className="card gr-devices" aria-label="Key devices">
          <header className="card__head">
            <div className="card__icon"><ChipIcon /></div>
            <div className="card__titles"><h2 className="card__title">Key devices</h2><p className="card__subtitle">Biggest users first, from HomematicIP power meters</p></div>
            <button className="btn gr-toggle" onClick={() => setShowAll((v) => !v)} aria-pressed={showAll}>{showAll ? 'Key only' : `All ${devices.length}`}</button>
            <StateBadge state="demo" />
          </header>
          <div className="card__body">
            <ul className="gr-devlist">
              {shown.map((d) => <DeviceRow key={d.id} device={d} price={unitPrice} rank={devices.indexOf(d) + 1} max={maxKwh} />)}
            </ul>
            <div className="gr-meter">
              <span>Whole house <b className="mono">{fmtKwh(DEMO_METER.todayKwh)}</b> today · {DEMO_METER.watts} W now <small>({DEMO_METER.model})</small></span>
              <span>Devices above explain <b className="mono">{Math.round((attributed / DEMO_METER.todayKwh) * 100)}%</b>; the rest is lighting and unmetered loads.</span>
            </div>
            <div className="gr-rooms" aria-label="Rooms">
              {DEMO_ROOMS.map((r) => (
                <div key={r.room} className="gr-room" data-warn={r.temp - r.target >= 2 || undefined}>
                  <small>{r.room}</small>
                  <b>{r.temp.toFixed(1)}°</b>
                  <small>target {r.target}° · {r.humidity}%</small>
                  {r.battery === 'low' && <span className="gr-room__bat mono">low battery</span>}
                </div>
              ))}
            </div>
            {lowBattery.length > 0 && <p className="en-note">{lowBattery.map((r) => r.room).join(', ')}: radiator thermostat battery is low. It will stop heating control when empty.</p>}
          </div>
          <footer className="card__foot"><span>HomematicIP via Home Assistant, not connected: illustrative values</span></footer>
        </section>

        <section className="card gr-schedule" aria-label="Scheduled automations">
          <header className="card__head">
            <div className="card__icon"><ClockIcon /></div>
            <div className="card__titles"><h2 className="card__title">Coming up</h2><p className="card__subtitle">Scheduled and suggested automations</p></div>
            <StateBadge state="demo" />
          </header>
          <div className="card__body">
            <Automations now={nowHm} />
            <p className="en-note">HomematicIP profiles are read, not edited. Chit suggestions are advice; nothing starts unless you start it.</p>
          </div>
          <footer className="card__foot"><span>illustrative schedule, no HomematicIP connection yet</span></footer>
        </section>
      </div>

      <div className="gr-pair">
        {hasPrices && day?.hours && (
          <section className="card" aria-label="Today’s price and use">
            <header className="card__head">
              <div className="card__icon"><BoltIcon /></div>
              <div className="card__titles"><h2 className="card__title">Price and use by hour</h2><p className="card__subtitle">Why the plan above looks the way it does</p></div>
              <StateBadge state={live} />
            </header>
            <div className="card__body">
              <PriceChart hours={day.hours} average={day.average_price ?? null} nowHour={day.now_hour ?? null} currency={currency} selected={selected} onSelect={setPicked} />
              <p className="en-note">
                Average {fmtPrice(day.average_price, currency)} · cheapest {day.cheapest_hour != null ? fmtHour(day.cheapest_hour) : '–'} · priciest {day.priciest_hour != null ? fmtHour(day.priciest_hour) : '–'}.
                {' '}The strip under the bars is green where an hour is below the day’s average and pink where it is above.
              </p>
            </div>
            <footer className="card__foot"><span>Tibber · checked {new Date(day.checked_at ?? Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></footer>
          </section>
        )}
        <WaterPanel />
      </div>
      {day?.state === 'unconfigured' && (
        <section className="card gr-connect" aria-label="Connect Tibber">
          <div className="card__body">
            <b><CheckIcon /> Prices make the insights real.</b>
            <p className="en-note">Add your Tibber token and the insights, today’s cost, month and year switch from examples to your own numbers.</p>
            <Link className="btn" to="/household#section-energy">Add your Tibber token</Link>
          </div>
        </section>
      )}

      <Integration />
      <p className="demo-note"><CardsIcon /> Badges show where each number comes from: <b>live</b> from Tibber or SolarEdge, <b>demo</b> for HomematicIP examples.</p>
    </div>
  );
}
