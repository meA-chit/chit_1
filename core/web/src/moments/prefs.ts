import { useCallback, useEffect, useState } from 'react';

/** Per-viewer conveniences kept in this browser only: panel open/closed and what was snoozed or done. Never needed for correctness. */
const KEY = 'chit.now.v1';
interface Stored { open?: boolean; hidden?: Record<string, number> }   // hidden: moment id -> epoch ms until which it stays away

const read = (): Stored => {
  try { return JSON.parse(localStorage.getItem(KEY) ?? '{}') as Stored; } catch { return {}; }
};
const write = (value: Stored) => {
  try { localStorage.setItem(KEY, JSON.stringify(value)); } catch { /* private window: the panel still works, it just forgets */ }
};

export function useNowPrefs(now: Date, defaultOpen: boolean) {
  const [state, setState] = useState<Stored>(read);
  useEffect(() => { write(state); }, [state]);
  const open = state.open ?? defaultOpen;
  const setOpen = useCallback((value: boolean) => setState((old) => ({ ...old, open: value })), []);
  const hide = useCallback((id: string, until: number) => setState((old) => ({ ...old, hidden: { ...old.hidden, [id]: until } })), []);
  const restore = useCallback(() => setState((old) => ({ ...old, hidden: {} })), []);
  const hidden = new Set(Object.entries(state.hidden ?? {}).filter(([, until]) => until > now.getTime()).map(([id]) => id));
  return { open, setOpen, hidden, hide, restore };
}
