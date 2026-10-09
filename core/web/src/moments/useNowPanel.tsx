import { useEffect, useMemo, useState, type ReactNode } from 'react';
import type { ShellConfig } from '../api/types';
import { useClock } from '../lib/useClock';
import { getMomentProviders } from '../registry';
import { NowPanel } from './NowPanel';
import { useNowPrefs } from './prefs';
import { minutesUntil, rankMoments } from './rank';
import { useMoments } from './useMoments';

const WIDE = '(min-width: 1100px)';
const SURFACES = new Set(['web', 'tablet', 'mobile-adult']);

function useWide(): boolean {
  const [wide, setWide] = useState(() => (typeof matchMedia === 'function' ? matchMedia(WIDE).matches : true));
  useEffect(() => {
    if (typeof matchMedia !== 'function') return;
    const query = matchMedia(WIDE);
    const onChange = () => setWide(query.matches);
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);
  return wide;
}

export interface NowPanelHandle {
  /** False on shared/TV/kid surfaces, before household setup, or when no enabled module publishes moments. */
  available: boolean;
  wide: boolean;
  count: number;
  /** A moment is within the hour. */
  urgent: boolean;
  toggle: () => void;
  /** Render once in the shell body (runners plus the panel). */
  node: ReactNode;
}

export function useNowPanel(shell: ShellConfig): NowPanelHandle {
  const now = useClock(30_000);
  const wide = useWide();
  const enabled = useMemo(() => new Set(shell.modules.map((module) => module.id)), [shell.modules]);
  const allowed = shell.interactive && !!shell.household && !shell.screen_safe && SURFACES.has(shell.surface);
  const { moments, ready, runners } = useMoments(now, allowed ? enabled : new Set());
  const prefs = useNowPrefs(now, true);
  const [drawer, setDrawer] = useState(false);
  const ranked = useMemo(() => rankMoments(moments, now, prefs.hidden), [moments, now, prefs.hidden]);
  const available = allowed && getMomentProviders().some((entry) => enabled.has(entry.module));
  const open = wide ? prefs.open : drawer;
  const first = ranked.hero[0];
  return {
    available, wide, count: ranked.hero.length,
    urgent: !!first && minutesUntil(first, now) <= 60,
    toggle: () => (wide ? prefs.setOpen(!prefs.open) : setDrawer(!drawer)),
    node: !available ? null : (
      <>
        {runners}
        <NowPanel ranked={ranked} ready={ready} now={now} mode={wide ? 'docked' : 'drawer'} open={open}
          onOpenChange={(value) => (wide ? prefs.setOpen(value) : setDrawer(value))}
          snoozedCount={moments.filter((moment) => prefs.hidden.has(moment.id)).length} onHide={prefs.hide} onRestore={prefs.restore} />
      </>
    ),
  };
}
