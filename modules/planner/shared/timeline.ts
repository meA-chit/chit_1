import type { AgendaEvent } from './agenda';

/** Pure helpers for the family timeline (shared by the timeline card and, later, the planner page). */
export const DAY_START = 6;
export const DAY_END = 22;
const SPAN = DAY_END - DAY_START;

export interface Block {
  id: string;
  title: string;
  kind: string;
  row?: number; // legacy server hint; rows are packed on the client now
  source: 'routine' | 'feed' | 'reminder';
  start: string | null; // HH:MM; null = start unknown (never invented)
  end: string;
}

export interface Lane {
  member_id: string;
  name: string;
  role: string;
  avatar: string | null;
  color: string | null;
  blocks: Block[];
}

export interface Zone { id: string; label: string; start: string; end: string }
export interface TimelineReminder { id: string; title: string; member_id: string | null; day_part: string | null }

export interface TimelinePayload {
  state: 'manual' | 'unconfigured';
  household?: string;
  date?: string;
  weekday?: string;
  timezone?: string;
  now?: string;
  is_today?: boolean;
  today?: string;
  max_days_ahead?: number;
  lanes: Lane[];
  reminders?: TimelineReminder[];
  zones?: Zone[];
  empty_reason?: string | null;
  source?: string;
}

export const toHours = (value: string): number => {
  const [h, m] = value.split(':');
  return Number(h) + Number(m) / 60;
};

export const fmt = (hours: number): string => {
  const total = Math.round(hours * 60);
  return `${String(Math.floor(total / 60) % 24).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
};

const clamp = (hours: number) => Math.max(DAY_START, Math.min(DAY_END, hours));
export const pct = (hours: number): number => ((clamp(hours) - DAY_START) / SPAN) * 100;

export interface Placed {
  block: Block;
  left: number; // %
  width: number; // %
  past: boolean;
  active: boolean;
  openStart: boolean;
}

/** Blocks wholly outside 06:00-22:00 are dropped; partly outside are clipped. */
export function place(blocks: Block[], now: number): Placed[] {
  const placed: Placed[] = [];
  for (const block of blocks) {
    const end = toHours(block.end);
    const openStart = block.start === null;
    const start = openStart ? DAY_START : toHours(block.start!);
    if (end <= DAY_START || start >= DAY_END) continue;
    const left = pct(start);
    placed.push({ block, left, width: Math.max(pct(end) - left, 1.2), past: end <= now, active: start <= now && now < end, openStart });
  }
  return placed;
}

export const ticks = (): { hour: number; left: number; label: string }[] =>
  Array.from({ length: (DAY_END - DAY_START) / 2 + 1 }, (_, i) => DAY_START + i * 2).map((hour) => ({ hour, left: pct(hour), label: fmt(hour) }));

const FAMILY: Lane = { member_id: 'family', name: 'Family', role: 'Shared', avatar: 'home', color: '#8d9bc2', blocks: [] };

/**
 * Add today's calendar-feed events as blocks. An event with exactly one known member goes to that
 * person's lane; any other (no member, several, unknown) goes to the shared Family lane.
 */
export function mergeFeedEvents(lanes: Lane[], events: AgendaEvent[], today: string): Lane[] {
  const byName = new Map(lanes.map((lane) => [lane.name, lane.member_id]));
  const merged = lanes.map((lane) => ({ ...lane, blocks: [...lane.blocks] }));
  const existingFamily = merged.find((lane) => lane.member_id === 'family');
  const family: Lane = existingFamily ?? { ...FAMILY, blocks: [] };
  events.forEach((event, index) => {
    if (event.start.slice(0, 10) !== today) return;
    const startH = event.all_day ? DAY_START : toHours(event.start.slice(11, 16));
    const endH = event.all_day ? DAY_END : toHours(event.end.slice(11, 16));
    if (!event.all_day && endH <= startH) return;
    const owners = event.members.map((name) => byName.get(name)).filter((id): id is string => !!id);
    const block: Block = {
      id: `feed-${index}`, title: event.title, kind: 'event', row: 1, source: 'feed',
      start: event.all_day ? fmt(DAY_START) : fmt(startH), end: event.all_day ? fmt(DAY_END) : fmt(endH),
    };
    const target = owners.length === 1 && event.members.length === 1 ? merged.find((lane) => lane.member_id === owners[0]) : family;
    target?.blocks.push(block);
  });
  return existingFamily || family.blocks.length === 0 ? merged : [...merged, family];
}

export interface UpNext {
  title: string;
  who: string;
  minutes: number;
}

const TASK_KINDS = new Set(['pickup', 'dropoff', 'activity', 'event', 'travel']);

/** The next *task-like* block (trips, activities, events) after now. Long blocks (work, school) are context, not "next". */
export function nextUp(lanes: Lane[], now: number): UpNext | null {
  let best: { start: number; title: string; who: string } | null = null;
  for (const lane of lanes) {
    for (const block of lane.blocks) {
      if (!TASK_KINDS.has(block.kind) || block.start === null) continue;
      const start = toHours(block.start);
      if (start > now && (!best || start < best.start)) best = { start, title: block.title, who: lane.name.split(' ')[0]! };
    }
  }
  return best ? { title: best.title, who: best.who, minutes: Math.round((best.start - now) * 60) } : null;
}

export const inText = (minutes: number): string => (minutes >= 60 ? `${Math.floor(minutes / 60)}h ${minutes % 60}m` : `${minutes}m`);

/** Hours since midnight in a time zone (the household's, not the viewer's). */
export function hoursIn(timeZone: string | undefined, date = new Date()): number {
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone, hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(date);
  const get = (type: string) => Number(parts.find((part) => part.type === type)?.value ?? 0);
  return (get('hour') % 24) + get('minute') / 60;
}

const TRAVEL_KINDS = new Set(['commute', 'pickup', 'dropoff']);
const MERGE_GAP_HOURS = 0.25;

/** "Drop off Mila" + "Drop off Leo" -> "Drop off Mila, Leo"; unlike titles are joined with " · ". */
export function joinTitles(titles: string[]): string {
  const byVerb = new Map<string, string[]>();
  for (const title of titles) {
    const match = /^(Drop off|Pick up) (.+)$/.exec(title);
    const [verb, name] = match ? [match[1]!, match[2]!] : [title, ''];
    const names = byVerb.get(verb) ?? [];
    if (name && !names.includes(name)) names.push(name);
    byVerb.set(verb, names);
  }
  return [...byVerb].map(([verb, names]) => (names.length ? `${verb} ${names.join(', ')}` : verb)).join(' · ');
}

/**
 * Travel (commute, drop-offs, pick-ups) that touches or sits within 15 minutes of other travel becomes ONE block,
 * so a school run is a single chip and the lane stays one row. Unknown starts are never merged.
 */
export function mergeTravel(blocks: Block[]): Block[] {
  const travel = blocks.filter((b) => TRAVEL_KINDS.has(b.kind) && b.start !== null).sort((a, b) => toHours(a.start!) - toHours(b.start!));
  const rest = blocks.filter((b) => !(TRAVEL_KINDS.has(b.kind) && b.start !== null));
  const merged: Block[] = [];
  for (const block of travel) {
    const last = merged[merged.length - 1];
    if (last && toHours(block.start!) - toHours(last.end) <= MERGE_GAP_HOURS) {
      const end = toHours(block.end) > toHours(last.end) ? block.end : last.end;
      merged[merged.length - 1] = { ...last, end, title: joinTitles([last.title, block.title]), kind: last.kind === block.kind ? last.kind : 'travel', id: `${last.id}+${block.id}` };
    } else merged.push(block);
  }
  return [...rest, ...merged];
}

export interface Row extends Placed { row: number }

/** Greedy interval packing: blocks that do not overlap share a row, so most lanes are one row tall. */
export function packRows(placed: Placed[]): { items: Row[]; rows: number } {
  const ends: number[] = [];
  const items = [...placed].sort((a, b) => a.left - b.left).map((item) => {
    let row = ends.findIndex((end) => end <= item.left + 0.01); // touching blocks share a row
    if (row === -1) { row = ends.length; ends.push(0); }
    ends[row] = item.left + item.width;
    return { ...item, row };
  });
  return { items, rows: Math.max(1, ends.length) };
}

export function layoutLane(blocks: Block[], now: number) {
  return packRows(place(mergeTravel(blocks), now));
}

export const zoneHours = (zone: Zone) => toHours(zone.end) - toHours(zone.start);

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function addDays(iso: string, days: number): string {
  const date = new Date(`${iso}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

export function dayTitle(iso: string, today: string): string {
  if (iso === today) return 'Today';
  if (iso === addDays(today, 1)) return 'Tomorrow';
  const date = new Date(`${iso}T12:00:00Z`);
  return `${DAYS[date.getUTCDay()]} ${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]}`;
}
