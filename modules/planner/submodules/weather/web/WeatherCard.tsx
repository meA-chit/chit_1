import { useQuery } from '@tanstack/react-query';
import { api, Link, type CardProps } from '@chit/core';

interface Weather {
  state: 'available' | 'stale' | 'unavailable' | 'unconfigured';
  reason?: string;
  temperature?: number; condition?: string; icon?: string; high?: number; low?: number; rain_pct?: number;
  observed_at?: string; source?: string;
}

function Glyph({ icon }: { icon?: string }) {
  const cloud = <path d="M17 36a7 7 0 011-13.8A9 9 0 0135 26a5 5 0 01-1 10z" fill="#c7d4f5" stroke="#05070d" strokeWidth="2" />;
  const sun = <><circle cx="19" cy="19" r="8" fill="#ffc857" /><g stroke="#ffc857" strokeWidth="2.2" strokeLinecap="round"><path d="M19 5v3M5 19h3M30 19h3M9 9l2 2M29 9l-2 2" /></g></>;
  return (
    <svg width="38" height="38" viewBox="0 0 48 48" fill="none" aria-hidden>
      {(icon === 'clear' || icon === 'partly') && sun}
      {icon !== 'clear' && cloud}
      {icon === 'rain' && <g stroke="#4df0ff" strokeWidth="2.2" strokeLinecap="round"><path d="M18 40l-1.5 4M25 40l-1.5 4M32 40l-1.5 4" /></g>}
      {icon === 'snow' && <g stroke="#e8eeff" strokeWidth="2.2" strokeLinecap="round"><path d="M18 41h.01M25 43h.01M32 41h.01" /></g>}
      {icon === 'storm' && <path d="M26 36l-4 7h5l-2 5" stroke="#ffc857" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />}
      {icon === 'fog' && <g stroke="#8d9bc2" strokeWidth="2.2" strokeLinecap="round"><path d="M12 40h24M16 44h18" /></g>}
    </svg>
  );
}

/** Weather in the top bar. Fetched by the hub from Open-Meteo; the browser never calls a provider. */
export default function WeatherCard(_: CardProps) {
  const { data, isPending } = useQuery({ queryKey: ['planner', 'weather', 'now'], queryFn: () => api<Weather>('/api/planner/weather/now'), refetchInterval: 15 * 60_000 });
  if (isPending || !data) return <div className="wx" aria-busy="true"><div className="skeleton" style={{ width: 120, margin: 0 }} /></div>;
  if (data.state === 'unconfigured') {
    return <div className="wx"><div><small style={{ color: 'var(--text)' }}>Weather</small><small>{data.reason === 'no_location' ? <Link to="/household" style={{ color: 'var(--accent)' }}>Add a location</Link> : 'Set up a household'}</small></div></div>;
  }
  if (data.state === 'unavailable') {
    return <div className="wx"><div><small style={{ color: 'var(--text)' }}>Weather unavailable</small><small>Could not reach the provider</small></div></div>;
  }
  const stale = data.state === 'stale';
  return (
    <div className="wx" title={`${data.source} · observed ${data.observed_at}${stale ? ' · provider unreachable, showing the last reading' : ''}`}>
      <Glyph icon={data.icon} />
      <div className="wx__temp">{data.temperature}°</div>
      <div>
        <small style={{ color: 'var(--text)' }}>{data.condition}{stale ? ' · stale' : ''}</small>
        <small>H {data.high}° · L {data.low}° · Rain {data.rain_pct}%</small>
      </div>
    </div>
  );
}
