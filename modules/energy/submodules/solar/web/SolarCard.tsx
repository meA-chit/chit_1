import { CardFrame, Empty, Link, SunIcon, type CardProps } from '@chit/core';
import { fmtHour, fmtKwh, useSolarDay } from '../../../shared/energy';
import { Loading } from '../../../shared/Loading';
import '../../../shared/energy.css';

const REASONS: Record<string, string> = {
  key_rejected: 'SolarEdge did not accept the saved API key. Update it in the household energy settings.',
  rate_limited: 'SolarEdge’s daily request limit was reached. This recovers on its own.',
  unavailable: 'Chit could not reach SolarEdge just now.',
};
const W = 480, BOTTOM = 112, SLOT = W / 24;

/** Illustrative day shown until SolarEdge is connected: a clean bell curve, clearly labelled, never presented as the household's own data. */
function DemoSolar({ frame }: { frame: { title: string; icon: JSX.Element; tone: string; embedded?: boolean } }) {
  const demo = Array.from({ length: 24 }, (_, hour) => (hour >= 7 && hour <= 18 ? Math.sin((Math.PI * (hour - 6.5)) / 12) * 3.2 : 0));
  const top = 3.2;
  return (
    <CardFrame {...frame} state="demo" subtitle="Example day" provenance={['illustrative values, SolarEdge is not connected']}>
      <div className="en-kpi"><b>2.6 kW</b><span>producing now</span><span className="en-used mono">11.8 kWh today</span></div>
      <div className="pc">
        <svg viewBox={`0 0 ${W} 132`} role="img" aria-label="Example solar production by hour" preserveAspectRatio="none">
          {demo.map((kw, i) => kw > 0 && <rect key={i} className="sol__bar" x={i * SLOT + 4} width={SLOT - 8} rx="2.5" y={BOTTOM - (kw / top) * (BOTTOM - 10)} height={(kw / top) * (BOTTOM - 10)} />)}
          {[0, 6, 12, 18, 23].map((h) => <text key={h} className="pc__tick" x={h * SLOT + SLOT / 2} y="128" textAnchor="middle">{String(h).padStart(2, '0')}</text>)}
        </svg>
      </div>
      <p className="en-note">Example values. When you connect SolarEdge in the household energy settings, your own production appears here. Best times for heavy loads then also favour sunny hours.</p>
      <Link className="btn" to="/household#section-energy">Connect SolarEdge</Link>
    </CardFrame>
  );
}

/** Production from the household's SolarEdge plant. Measured hours are solid; the rest of today is an estimate and drawn hollow. */
export default function SolarCard({ card, embedded }: CardProps) {
  const { data, isPending, isError } = useSolarDay();
  const frame = { title: card.title, icon: <SunIcon />, tone: '#ffc857', embedded } as const;
  if (isPending) return <Loading embedded={embedded} />;
  if (isError || !data) return <CardFrame {...frame} state="unavailable"><Empty title="Solar unavailable">The hub could not be reached.</Empty></CardFrame>;
  if (data.state === 'unconfigured') return <DemoSolar frame={frame} />;
  if (data.state === 'unavailable' || !data.hours) {
    return <CardFrame {...frame} state="unavailable"><Empty title="Production unavailable">{REASONS[data.reason ?? 'unavailable'] ?? REASONS.unavailable}</Empty></CardFrame>;
  }

  const hours = data.hours;
  const top = Math.max(0.5, ...hours.map((h) => Math.max(h.kwh ?? 0, h.expected_kwh ?? 0)));
  const height = (kwh: number) => Math.max(2, (kwh / top) * (BOTTOM - 10));
  const expectedRest = hours.reduce((sum, h) => sum + (h.expected_kwh ?? 0), 0);
  const stamp = data.checked_at ? new Date(data.checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

  return (
    <CardFrame {...frame} state={data.state} subtitle={data.site_name ?? 'SolarEdge'}
      provenance={[`SolarEdge · checked ${stamp}`, ...(data.last_update ? [`plant reported ${data.last_update}`] : []), ...(data.state === 'stale' ? ['provider unreachable, showing the last reading'] : [])]}>
      <div className="en-kpi">
        <b>{data.current_kw === null || data.current_kw === undefined ? '–' : `${data.current_kw.toFixed(1)} kW`}</b><span>producing now</span>
        <span className="en-used mono">{fmtKwh(data.today_kwh)} today</span>
      </div>
      <div className="pc">
        <svg viewBox={`0 0 ${W} 132`} role="img" aria-label="Solar production by hour" preserveAspectRatio="none">
          {data.now_hour !== undefined && <rect className="pc__now" x={data.now_hour * SLOT} y="2" width={SLOT} height={BOTTOM} rx="4" />}
          {hours.map((h, i) => h.kwh !== null ? (
            <rect key={h.hour} className="sol__bar" x={i * SLOT + 4} width={SLOT - 8} rx="2.5" y={BOTTOM - height(h.kwh)} height={height(h.kwh)}><title>{`${fmtHour(h.hour)} · ${fmtKwh(h.kwh, 2)}`}</title></rect>
          ) : h.expected_kwh ? (
            <rect key={h.hour} className="sol__bar sol__bar--est" x={i * SLOT + 4} width={SLOT - 8} rx="2.5" y={BOTTOM - height(h.expected_kwh)} height={height(h.expected_kwh)}><title>{`${fmtHour(h.hour)} · about ${fmtKwh(h.expected_kwh, 2)} expected`}</title></rect>
          ) : null)}
          {[0, 6, 12, 18, 23].map((h) => <text key={h} className="pc__tick" x={h * SLOT + SLOT / 2} y="128" textAnchor="middle">{String(h).padStart(2, '0')}</text>)}
        </svg>
      </div>
      <div className="en-legend">
        <span><i data-sun /> measured</span>
        {data.expected_state === 'forecast' && <span><i data-sun="est" /> expected (estimate, about {fmtKwh(expectedRest, 0)} more today)</span>}
      </div>
      <div className="en-price">
        <span>Month <b className="mono">{fmtKwh(data.month_kwh, 0)}</b></span>
        <span>Lifetime <b className="mono">{data.lifetime_kwh === null || data.lifetime_kwh === undefined ? '–' : `${(data.lifetime_kwh / 1000).toFixed(1)} MWh`}</b></span>
        {data.peak_kw ? <span>Plant <b className="mono">{data.peak_kw} kWp</b></span> : null}
      </div>
      {data.expected_state === 'unavailable' && <p className="en-note">The sun estimate for the rest of today could not be loaded.</p>}
    </CardFrame>
  );
}
