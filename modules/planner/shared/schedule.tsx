import { useQuery } from '@tanstack/react-query';
import { api, ChipGroup, WeekdayChips } from '@chit/core';

/** A named zone of the day (1-2 hours), never an exact time. The server owns the hours (planner/shared/dayparts.py). */
export interface DayPart {
  id: string;
  label: string;
  start: string;
  end: string;
}

export const useDayParts = () =>
  useQuery({
    queryKey: ['planner', 'options'],
    queryFn: () => api<{ day_parts: DayPart[]; weekdays: string[] }>('/api/planner/chores/options'),
    staleTime: Infinity,
  });

const cap = (day: string) => day.slice(0, 3).replace(/^./, (c) => c.toUpperCase());
const sameSet = (a: string[], b: string[]) => a.length === b.length && b.every((day) => a.includes(day));

export function describeDays(weekdays: string[]): string {
  if (weekdays.length === 0 || weekdays.length === 7) return 'Every day';
  if (sameSet(weekdays, ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])) return 'Weekdays';
  if (sameSet(weekdays, ['saturday', 'sunday'])) return 'Weekends';
  return weekdays.map(cap).join(', ');
}

export function describePart(part: string | null, parts: DayPart[]): string {
  const found = parts.find((p) => p.id === part);
  return found ? `${found.label} (${found.start} to ${found.end})` : 'Any time';
}

/** Weekday chips + day-part chips: how both chores and reminders choose "when", without exact times. */
export function WhenFields({ weekdays, onWeekdays, dayPart, onDayPart, parts, daysLabel = 'Repeats on', daysHint, showDays = true }: {
  weekdays: string[]; onWeekdays: (days: string[]) => void;
  dayPart: string | null; onDayPart: (part: string | null) => void;
  parts: DayPart[]; daysLabel?: string; daysHint?: string; showDays?: boolean;
}) {
  return (
    <>
      {showDays && <WeekdayChips label={daysLabel} selected={weekdays} onChange={onWeekdays} hint={daysHint ?? 'Leave all unselected for every day.'} />}
      <ChipGroup label="Time of day" single selected={dayPart ? [dayPart] : []}
        options={parts.map((part) => ({ value: part.id, label: `${part.label} · ${part.start} to ${part.end}` }))}
        hint="A rough zone, not an exact time. Leave unselected for any time."
        onChange={(selected) => onDayPart(selected[0] ?? null)} />
    </>
  );
}
