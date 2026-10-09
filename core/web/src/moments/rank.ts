import type { Moment } from './types';

export const HERO_LIMIT = 3;
const MINUTE = 60_000;

/** Minutes until the moment is about (negative once it has started). A moment already under way counts as 0. */
export const minutesUntil = (moment: Moment, now: Date): number => (moment.at.getTime() - now.getTime()) / MINUTE;

/**
 * Deterministic urgency, 0 to 1: within 30 minutes it is at the top, then it falls off over about 12 hours.
 * Documented here so the "Why these?" note is true: urgency, then value, then confidence.
 */
export function urgency(moment: Moment, now: Date): number {
  const minutes = Math.max(0, minutesUntil(moment, now));
  if (minutes <= 30) return 1;
  return Math.max(0, 1 - (minutes - 30) / (12 * 60));
}

/** Measured or live evidence beats stale, forecast and demo evidence. */
export function confidence(moment: Moment): number {
  switch (moment.state) {
    case 'available': case 'manual': return 1;
    case 'forecast': return 0.8;
    case 'partial': return 0.6;
    case 'stale': return 0.5;
    default: return 0;   // unavailable, unconfigured, demo: never promoted to attention
  }
}

export const isLive = (moment: Moment, now: Date): boolean => !moment.until || moment.until.getTime() > now.getTime();

export interface Ranked { hero: Moment[]; quiet: Moment[] }

/**
 * Drop what is over or unsupported, order by urgency x confidence (money before info on a tie, then time, then id), and
 * split into a bounded hero list and the rest. `hidden` holds ids the person snoozed or marked done.
 */
export function rankMoments(moments: Moment[], now: Date, hidden: ReadonlySet<string> = new Set(), limit = HERO_LIMIT): Ranked {
  const kindRank = { time: 0, money: 1, info: 2 } as const;
  const scored = moments
    .filter((moment) => isLive(moment, now) && !hidden.has(moment.id) && confidence(moment) > 0)
    .map((moment) => ({ moment, score: urgency(moment, now) * confidence(moment) }))
    .sort((a, b) =>
      b.score - a.score
      || kindRank[a.moment.kind] - kindRank[b.moment.kind]
      || a.moment.at.getTime() - b.moment.at.getTime()
      || a.moment.id.localeCompare(b.moment.id))
    .map((entry) => entry.moment);
  // A card only earns a hero slot if it is actually soon or valuable; the rest wait in "quiet".
  const hero = scored.filter((moment) => minutesUntil(moment, now) <= 12 * 60 || moment.value).slice(0, limit);
  return { hero, quiet: scored.filter((moment) => !hero.includes(moment)) };
}

/** "in 38 min", "in 2 h", "now". */
export function countdown(moment: Moment, now: Date): string {
  const minutes = Math.round(minutesUntil(moment, now));
  if (minutes <= 0) return 'now';
  if (minutes < 60) return `in ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest === 0 || hours >= 6 ? `in ${hours} h` : `in ${hours} h ${rest} min`;
}
