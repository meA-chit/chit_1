import { useSyncExternalStore } from 'react';

/**
 * "View as": which household member's enablement the shell applies. This is a convenience until
 * identity exists (ADR-0007 / open decision 2); it is NOT access control.
 */
const KEY = 'chit.viewAs';
const listeners = new Set<() => void>();
const read = () => {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
};

export function setViewer(memberId: string | null) {
  try {
    if (memberId) localStorage.setItem(KEY, memberId);
    else localStorage.removeItem(KEY);
  } catch {
    /* private mode: ignore */
  }
  listeners.forEach((listener) => listener());
}

export function useViewer() {
  const memberId = useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    read,
    () => null,
  );
  return { memberId, setViewer };
}
