import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, Link, type CardProps } from '@chit/core';
import { Sky } from './Sky';
import './weather.css';

interface Weather {
  state: 'available' | 'stale' | 'unavailable' | 'unconfigured';
  reason?: string;
  temperature?: number; condition?: string; icon?: string; high?: number; low?: number; rain_pct?: number;
  observed_at?: string; source?: string;
  week?: Day[];
}
interface Day { date: string; condition: string; icon: string; high: number; low: number; rain_pct: number | null }

const dayName = (date: string) => new Date(`${date}T12:00:00`).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' });

function Glyph({ icon }: { icon?: string }) {
  const cloud = <path d="M17 36a7 7 0 011-13.8A9 9 0 0135 26a5 5 0 01-1 10z" fill="#c7d4f5" stroke="#05070d" strokeWidth="2" />;
  const sun = <><circle cx="19" cy="19" r="8" fill="#ffc857" /><g stroke="#ffc857" strokeWidth="2.2" strokeLinecap="round"><path d="M19 5v3M5 19h3M30 19h3M9 9l2 2M29 9l-2 2" /></g></>;
  return (
    <svg width="30" height="30" viewBox="0 0 48 48" fill="none" aria-hidden>
      {(icon === 'clear' || icon === 'partly') && sun}
      {icon !== 'clear' && cloud}
      {icon === 'rain' && <g stroke="#4df0ff" strokeWidth="2.2" strokeLinecap="round"><path d="M18 40l-1.5 4M25 40l-1.5 4M32 40l-1.5 4" /></g>}
      {icon === 'snow' && <g stroke="#e8eeff" strokeWidth="2.2" strokeLinecap="round"><path d="M18 41h.01M25 43h.01M32 41h.01" /></g>}
      {icon === 'storm' && <path d="M26 36l-4 7h5l-2 5" stroke="#ffc857" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />}
      {icon === 'fog' && <g stroke="#8d9bc2" strokeWidth="2.2" strokeLinecap="round"><path d="M12 40h24M16 44h18" /></g>}
    </svg>
  );
}

/**
 * Weather in the top bar: today, tomorrow, and a dropdown with the days after. Fetched by the hub from Open-Meteo; the browser never calls a provider.
 * The dropdown opens over the page like the "Viewing as" menu.
 */
export default function WeatherCard(_: CardProps) {
  const { data, isPending } = useQuery({ queryKey: ['planner', 'weather', 'now'], queryFn: () => api<Weather>('/api/planner/weather/now'), refetchInterval: 15 * 60_000 });
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const away = (event: MouseEvent) => { if (!box.current?.contains(event.target as Node)) setOpen(false); };
    const esc = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', away);
    document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', away); document.removeEventListener('keydown', esc); };
  }, [open]);

  if (isPending || !data) return <div className="wx bubble" aria-busy="true"><div className="skeleton" style={{ width: 120, margin: 0 }} /></div>;
  if (data.state === 'unconfigured') {
    return <div className="wx bubble"><div><small style={{ color: 'var(--text)' }}>Weather</small><small>{data.reason === 'no_location' ? <Link to="/household" style={{ color: 'var(--accent)' }}>Add a location</Link> : 'Set up a household'}</small></div></div>;
  }
  if (data.state === 'unavailable') {
    return <div className="wx bubble"><div><small style={{ color: 'var(--text)' }}>Weather unavailable</small><small>Could not reach the provider</small></div></div>;
  }
  const stale = data.state === 'stale';
  const week = data.week ?? [];
  const tomorrow = week[1];
  return (
    <div className="wx bubble" ref={box}>
      <div className="wx__now" title={`${data.source} · observed ${data.observed_at}${stale ? ' · provider unreachable, showing the last reading' : ''}`}>
        <Glyph icon={data.icon} />
        <div className="wx__temp">{data.temperature}°</div>
        <div>
          <small style={{ color: 'var(--text)' }}>{data.condition}{stale ? ' · stale' : ''}</small>
          <small>H {data.high}° · L {data.low}° · Rain {data.rain_pct}%</small>
        </div>
      </div>
      {tomorrow && (
        <div className="wx__next" aria-label={`Tomorrow: ${tomorrow.condition}, high ${tomorrow.high}, low ${tomorrow.low}`}>
          <span className="wx__nextlab">Tomorrow</span>
          <span className="wx__nextrow" data-sky={tomorrow.icon}><Sky icon={tomorrow.icon} size={20} /><b>{tomorrow.high}°</b><span>{tomorrow.low}°</span></span>
        </div>
      )}
      {week.length > 2 && (
        <button type="button" className="wx__more" aria-haspopup="true" aria-expanded={open} aria-label="Next days" onClick={() => setOpen(!open)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ transform: open ? 'rotate(180deg)' : undefined }}><path d="M6 9l6 6 6-6" /></svg>
        </button>
      )}
      {open && (
        <div className="wx__pop" role="region" aria-label="Weather for the next days">
          <ul className="wk">
            {week.slice(0, 6).map((day, index) => (
              <li key={day.date} className="wk__row" data-today={index === 0 || undefined} aria-current={index === 0 ? 'date' : undefined}>
                <span className="wk__day">{index === 0 ? 'Today' : dayName(day.date)}</span>
                <span className="wk__icon" data-sky={day.icon}><Sky icon={day.icon} /></span>
                <span className="wk__cond">{day.condition}{day.rain_pct != null && <small><span className="wk__drop" aria-hidden>●</span><span className="sr-only">Chance of rain </span>{day.rain_pct}%</small>}</span>
                <span className="wk__temp"><span className="sr-only">High </span><b>{day.high}°</b><span className="sr-only">, low </span><span>{day.low}°</span></span>
              </li>
            ))}
          </ul>
          <small className="wx__src">{data.source}{stale ? ' · stale' : ''}</small>
        </div>
      )}
    </div>
  );
}
