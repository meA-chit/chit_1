import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { Moment, MomentSource } from '@chit/core';
import { AGENDA_KEY, clockOf, fetchAgenda } from '../../../shared/agenda';

const GRACE_MS = 15 * 60_000;       // an event that began more than a quarter of an hour ago is no longer news
const HORIZON_MS = 3 * 60 * 60_000;   // only what starts within the next three hours is "just in time"

/**
 * The next timed calendar events. Chit has no commute data for calendar events, so this says when it starts, never when to leave.
 */
export function useCalendarMoments(now: Date): MomentSource {
  const query = useQuery({ queryKey: AGENDA_KEY, queryFn: fetchAgenda, refetchInterval: 5 * 60_000 });
  const data = query.data;
  const moments = useMemo<Moment[]>(() => {
    if (!data || (data.state !== 'available' && data.state !== 'partial' && data.state !== 'stale')) return [];
    return data.events
      .filter((event) => !event.all_day)
      .map((event) => ({ event, start: new Date(event.start), end: new Date(event.end) }))
      .filter(({ start, end }) => now.getTime() - start.getTime() <= GRACE_MS && end.getTime() > now.getTime() && start.getTime() - now.getTime() <= HORIZON_MS)
      .slice(0, 4)
      .map(({ event, start, end }) => ({
        id: `planner/event/${event.source}/${event.start}/${event.title}`,
        module: 'planner',
        kind: 'time' as const,
        title: event.title,
        reason: `${start.getTime() <= now.getTime() ? 'Started' : 'Starts'} ${clockOf(event)}${event.members.length ? ` · ${event.members.join(', ')}` : ''}`,
        at: start,
        until: end,
        state: data.state,
        source: `Calendar: ${event.source}`,
        checkedAt: data.checked_at,
        action: { label: 'Open agenda', to: '/' },
      }));
  }, [data, now]);
  return { moments, ready: !query.isPending };
}
