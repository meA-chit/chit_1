import { useQuery } from '@tanstack/react-query';
import {
  CalendarIcon, CardFrame, Empty, Link, PersonAvatar, relativeTime, Skeleton, useShell, useViewer, type CardProps, type DataState, type Person,
} from '@chit/core';
import { AGENDA_KEY, clockOf, dayLabel, fetchAgenda, groupByDay } from '../../../shared/agenda';
import './calendar.css';

const MAX_ROWS = 6;

export default function AgendaCard({ card }: CardProps) {
  const { memberId } = useViewer();
  const shell = useShell();
  const { data, isPending, isError } = useQuery({ queryKey: AGENDA_KEY, queryFn: fetchAgenda, refetchInterval: 5 * 60_000 });
  const frame = { title: card.title, icon: <CalendarIcon />, tone: '#b79cff' } as const;

  if (isPending) return <CardFrame {...frame} state="unavailable"><Skeleton lines={4} /></CardFrame>;
  if (isError) return <CardFrame {...frame} state="unavailable"><Empty title="Calendar unavailable">The hub could not be reached. Nothing is shown rather than a guess.</Empty></CardFrame>;

  const state: DataState = data.reason === 'unconfigured' ? 'unconfigured' : data.state;
  if (state === 'unconfigured') {
    return (
      <CardFrame {...frame} state="unconfigured">
        <Empty title="No calendars connected" action={<Link className="btn" to="/household">Connect a calendar</Link>}>
          Connect read-only calendar feeds to see what is coming up. An empty agenda is never shown as "free".
        </Empty>
      </CardFrame>
    );
  }
  if (state === 'unavailable') {
    return (
      <CardFrame {...frame} state="unavailable" provenance={(data.sources ?? []).map((source) => `${source.name}: ${source.state}`)}>
        {/* Never present "could not read" as "nothing scheduled": absence is not availability. */}
        <Empty title="Can't read your calendars right now">
          None of the connected feeds responded, so Chit cannot say what is coming up. Check the feed links in household settings.
        </Empty>
      </CardFrame>
    );
  }

  const byName = new Map<string, Person>((shell.data?.members ?? []).map((person) => [person.name, person]));
  const viewer = shell.data?.members.find((person) => person.id === memberId);
  const events = viewer ? data.events.filter((event) => event.members.length === 0 || event.members.includes(viewer.name)) : data.events;
  const days = groupByDay(events, MAX_ROWS);
  const today = new Date().toLocaleDateString('en-CA');
  const nowStamp = new Date().toTimeString().slice(0, 5);
  let nextTaken = false;
  const failing = (data.sources ?? []).filter((source) => source.state !== 'available');
  const provenance = [
    `source: ${(data.sources ?? []).map((source) => source.name).join(', ') || 'calendar feeds'}`,
    data.checked_at ? `checked ${relativeTime(data.checked_at)}` : '',
    ...failing.map((source) => `${source.name}: ${source.state}`),
  ].filter(Boolean);

  return (
    <CardFrame {...frame} state={state} subtitle={`Read-only feeds · ${(data.sources ?? []).length} source${(data.sources ?? []).length === 1 ? '' : 's'}`} provenance={provenance}>
      {days.length === 0 ? (
        <Empty title={`Nothing scheduled in the next ${data.range_days ?? 21} days`}>Based on the connected feeds listed below.</Empty>
      ) : days.map((group) => (
        <div key={group.day}>
          <div className="eyebrow ev-day">{dayLabel(group.day, today)}</div>
          {group.events.map((event) => {
            const isToday = group.day === today;
            const past = isToday && !event.all_day && event.end.slice(11, 16) <= nowStamp;
            const isNext = !nextTaken && isToday && !event.all_day && event.start.slice(11, 16) > nowStamp;
            if (isNext) nextTaken = true;
            const people = event.members.map((name) => byName.get(name)).filter((p): p is Person => !!p);
            return (
              <div key={`${event.start}${event.title}`} className="ev" data-next={isNext} data-past={past}>
                <div className="ev__time">{clockOf(event)}{!event.all_day && <small>{event.end.slice(11, 16)}</small>}</div>
                <div style={{ minWidth: 0 }}>
                  <div className="ev__title">{event.icon && <span className="ev__icon" aria-hidden>{event.icon}</span>}{event.title}</div>
                  <div className="ev__meta"><span className="tag">{event.source}</span>{isNext && <span className="pill-next">Next</span>}</div>
                </div>
                <div className="person-stack">{people.map((p) => <PersonAvatar key={p.id} kind={p.avatar} color={p.color} size={24} />)}</div>
              </div>
            );
          })}
        </div>
      ))}
    </CardFrame>
  );
}
