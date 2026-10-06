import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, type Person } from '@chit/core';
import type { DayPart } from './schedule';

/** Data hooks for chores and reminders, shared by the dashboard card and the household settings sections. */
export interface Chore {
  id: string; title: string; done: boolean; skipped?: boolean; streak: number; day_part: string | null;
  assignee_id: string | null; assignee: Person | null;
}
export interface ChoresToday {
  state: 'manual' | 'unconfigured'; chores: Chore[]; skipped: Chore[]; day_parts?: DayPart[];
  summary?: { done: number; total: number; best_streak: number };
}
export interface ChoreRow { id: string; title: string; assignee_id: string | null; weekdays: string[]; day_part: string | null }

export interface Reminder { id: string; title: string; member_id: string | null; on_date: string | null; weekdays: string[]; day_part: string | null }
export interface RemindersToday { state: string; date?: string; reminders: Reminder[]; skipped: Reminder[]; upcoming: Reminder[]; day_parts?: DayPart[] }

export const KEYS = {
  choresToday: ['planner', 'chores', 'today'],
  chores: ['planner', 'chores'],
  remindersToday: ['planner', 'reminders', 'today'],
  reminders: ['planner', 'reminders'],
  timeline: ['planner', 'timeline'],
} as const;

export const useChoresToday = () => useQuery({ queryKey: KEYS.choresToday, queryFn: () => api<ChoresToday>('/api/planner/chores/today') });
export const useRemindersToday = () => useQuery({ queryKey: KEYS.remindersToday, queryFn: () => api<RemindersToday>('/api/planner/reminders/today') });

/** Everything that shows planner data refreshes after any change here. */
export function usePlannerInvalidate() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ['planner'] });
}

export interface ChoreDraft { id: string | null; title: string; assignee_id: string; weekdays: string[]; day_part: string | null }
export interface ReminderDraft { id: string | null; title: string; member_id: string; on_date: string; day_part: string | null }

export const emptyChore = (assignee = ''): ChoreDraft => ({ id: null, title: '', assignee_id: assignee, weekdays: [], day_part: null });
export const localDate = (offsetDays = 0) => {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toLocaleDateString('en-CA');
};
export const emptyReminder = (member = '', onDate = localDate()): ReminderDraft => ({ id: null, title: '', member_id: member, on_date: onDate, day_part: null });

export function useSaveChore(onDone: () => void) {
  const invalidate = usePlannerInvalidate();
  return useMutation({
    mutationFn: (d: ChoreDraft) => {
      const body = JSON.stringify({ title: d.title, assignee_id: d.assignee_id || null, weekdays: d.weekdays, day_part: d.day_part });
      return d.id ? api(`/api/planner/chores/${d.id}`, { method: 'PUT', body }) : api('/api/planner/chores', { method: 'POST', body });
    },
    onSuccess: async () => { await invalidate(); onDone(); },
  });
}

export function useSaveReminder(onDone: () => void) {
  const invalidate = usePlannerInvalidate();
  return useMutation({
    mutationFn: (d: ReminderDraft) => {
      const body = JSON.stringify({ title: d.title, member_id: d.member_id || null, on_date: d.on_date, weekdays: [], day_part: d.day_part });
      return d.id ? api(`/api/planner/reminders/${d.id}`, { method: 'PUT', body }) : api('/api/planner/reminders', { method: 'POST', body });
    },
    onSuccess: async () => { await invalidate(); onDone(); },
  });
}

export function useRemove(kind: 'chores' | 'reminders') {
  const invalidate = usePlannerInvalidate();
  return useMutation({ mutationFn: (id: string) => api(`/api/planner/${kind}/${id}`, { method: 'DELETE' }), onSuccess: invalidate });
}

/** Skip (or restore) one occurrence for today. The item itself is untouched. */
export function useSkip(kind: 'chores' | 'reminders') {
  const invalidate = usePlannerInvalidate();
  return useMutation({
    mutationFn: ({ id, skipped }: { id: string; skipped: boolean }) =>
      api(`/api/planner/${kind}/${id}/skip`, { method: 'POST', body: JSON.stringify({ skipped }) }),
    onSuccess: invalidate,
  });
}
