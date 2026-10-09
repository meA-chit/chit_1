import { memo, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { getMomentProviders } from '../registry';
import type { Moment, MomentProvider, MomentSource } from './types';

interface RunnerProps { id: string; provider: MomentProvider; now: Date; report: (id: string, source: MomentSource) => void }

/** Each provider runs in its own component, so the set can change (another member, another module list) without breaking hook order. */
const Runner = memo(function Runner({ id, provider, now, report }: RunnerProps) {
  const source = provider(now);
  useEffect(() => { report(id, source); });   // memo: the parent's own updates do not re-run this, so no loop
  return null;
});

/** Collects moments from every registered provider whose module is enabled. Render `runners` once, anywhere. */
export function useMoments(now: Date, enabledModules: ReadonlySet<string>): { moments: Moment[]; ready: boolean; runners: ReactNode } {
  const [reports, setReports] = useState<Record<string, MomentSource>>({});
  const report = useCallback((id: string, source: MomentSource) => {
    setReports((old) => {
      const before = old[id];
      return before && before.ready === source.ready && before.moments === source.moments ? old : { ...old, [id]: source };
    });
  }, []);
  const active = getMomentProviders().filter((entry) => enabledModules.has(entry.module));
  const key = active.map((entry) => entry.key).join('|');
  const runners = useMemo(
    () => active.map((entry) => <Runner key={entry.key} id={entry.key} provider={entry.provider} now={now} report={report} />),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` stands for `active`
    [key, now, report],
  );
  const moments = active.flatMap((entry) => reports[entry.key]?.moments ?? []);
  const ready = active.every((entry) => reports[entry.key]?.ready === true);
  return { moments, ready, runners };
}
