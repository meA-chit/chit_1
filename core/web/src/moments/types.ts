import type { DataState } from '../api/types';

/**
 * A moment: one thing worth the household's attention right now, with the evidence for it.
 * Modules publish candidates through `ModuleWeb.moments`; the shell ranks and shows a few (docs/core/attention-and-insights.md).
 * Read-only: `action` only navigates, it never changes anything.
 */
export interface Moment {
  /** Stable across refreshes so snooze and done survive a refetch. Include the occurrence (e.g. the start time). */
  id: string;
  module: string;
  kind: 'time' | 'money' | 'info';
  title: string;
  /** Why this is shown. Required: no unexplained cards. */
  reason: string;
  /** The time the moment is about (start of an event or a price window). Urgency rises as it approaches. */
  at: Date;
  /** After this the moment is gone. */
  until?: Date;
  /** What it saves. Only when it can be computed; an estimate must say so. Never invented. */
  value?: { label: string; estimated?: boolean };
  /** Data state of the evidence. Forecast, manual and demo are never shown as measured. */
  state: DataState;
  /** Where the evidence came from, e.g. "Tibber prices". */
  source: string;
  checkedAt?: string;
  action?: { label: string; to: string };
}

export interface MomentSource {
  moments: Moment[];
  /** False while the first read is in flight; the panel shows a skeleton instead of "nothing needs you". */
  ready: boolean;
}

/** A hook a module exports to publish candidates. `now` ticks every 30 s. Called in a fixed order, so it may use hooks. */
export type MomentProvider = (now: Date) => MomentSource;
