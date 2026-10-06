import { api, type DataState } from '@chit/core';

export interface AgendaEvent {
  title: string;
  start: string; // ISO with offset, already in household time
  end: string;
  all_day: boolean;
  source: string;
  members: string[];
}

export interface Agenda {
  state: DataState;
  reason?: 'unconfigured';
  household?: string;
  checked_at?: string;
  range_days?: number;
  sources?: { name: string; state: DataState; event_count: number }[];
  events: AgendaEvent[];
}

export interface DayGroup {
  day: string; // YYYY-MM-DD, taken from the event's own offset so it matches household time
  events: AgendaEvent[];
}

/** Group by the calendar day written in the ISO string (household time), not the viewer's zone. */
export function groupByDay(events: AgendaEvent[], limit = Infinity): DayGroup[] {
  const groups: DayGroup[] = [];
  for (const event of events.slice(0, limit)) {
    const day = event.start.slice(0, 10);
    const last = groups[groups.length - 1];
    if (last && last.day === day) last.events.push(event);
    else groups.push({ day, events: [event] });
  }
  return groups;
}

export const clockOf = (event: AgendaEvent) => (event.all_day ? 'All day' : event.start.slice(11, 16));

export function dayLabel(day: string, today: string): string {
  const date = new Date(`${day}T12:00:00`);
  const diff = Math.round((date.getTime() - new Date(`${today}T12:00:00`).getTime()) / 86_400_000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  return date.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'short' });
}

export const AGENDA_KEY = ['planner', 'calendar', 'agenda'] as const;
export const fetchAgenda = () => api<Agenda>('/api/planner/calendar/agenda');
