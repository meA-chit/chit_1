import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, type DataState, type Person } from '@chit/core';

/** Data hooks and types shared by the kids panels. Everything comes from the hub's /api/kids endpoints. */

export interface Goal {
  id: string; member_id: string; title: string; note: string | null; cost: number; have: number; pct: number;
  reached: boolean; status: 'active' | 'approved'; started_on: string;
}
export interface StarChore { id: string; title: string; weekdays: string[]; day_part: string | null; star: boolean }
export interface TodayChore { id: string; title: string; done: boolean; star: boolean; outcome: 'well' | 'again' | null }
export interface StarChild {
  member_id: string; name: string; avatar: string | null; color: string | null; stars_total: number; stars_week: number;
  week: { day: string; stars: number }[]; goals: Goal[]; chores: StarChore[]; today: TodayChore[];
}
export interface StarsOverview { state: DataState; date?: string; children: StarChild[] }

export interface Subject {
  id: string; name: string; kind: 'main' | 'other'; count: number; latest: number | null; trend: 'better' | 'worse' | 'steady' | null;
  written: number | null; oral: number | null; average: number | null;
}
export interface GradeEntry { id: string; subject: string; subject_id: string; grade_type: 'written' | 'oral'; grade: number; given_on: string; note: string | null }
export interface GradesOverview {
  state: DataState; member_id?: string; weights: { main_written_pct: number; other_written_pct: number }; subjects: Subject[]; entries: GradeEntry[]; scale?: string;
}

export interface Slot { id: string; weekday: number; start: string; end: string; title: string; kind: 'lesson' | 'break' | 'meal' | 'care'; note: string | null }
export interface SchoolPlanData { state: DataState; member_id?: string; today_weekday?: number; now?: string; slots: Slot[] }

export type DoseStatus = 'given' | 'missed' | null;
export interface Med {
  id: string; name: string; dose: string | null; time: string; weekdays: string[]; remind_member_id: string | null; supply: number | null;
  days_left: number | null; refill_soon: boolean; today: { due: boolean; status: DoseStatus };
  week: { day: string; due: boolean; status: DoseStatus }[];
}
export interface MedsOverview { state: DataState; member_id?: string; date?: string; now?: string; meds: Med[] }

export const GRADE_STEPS: [number, string][] = [[1, '1'], [1.3, '1-'], [1.7, '2+'], [2, '2'], [2.3, '2-'], [2.7, '3+'], [3, '3'], [3.3, '3-'], [3.7, '4+'], [4, '4'], [4.3, '4-'], [4.7, '5+'], [5, '5'], [5.3, '5-'], [6, '6']];
export const gradeLabel = (value: number) => GRADE_STEPS.find(([v]) => Math.abs(v - value) < 0.05)?.[1] ?? value.toFixed(1);
export const WEEKDAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
export const dayShort = (name: string) => name.slice(0, 3).replace(/^./, (c) => c.toUpperCase());

const get = <T,>(path: string) => api<T>(path);
export const useStars = () => useQuery({ queryKey: ['kids', 'stars'], queryFn: () => get<StarsOverview>('/api/kids/stars/overview') });
export const useGrades = (member: string) => useQuery({ queryKey: ['kids', 'grades', member], queryFn: () => get<GradesOverview>(`/api/kids/grades/overview?member=${member}`) });
export const useSchoolPlan = (member: string) => useQuery({ queryKey: ['kids', 'school', member], queryFn: () => get<SchoolPlanData>(`/api/kids/school/plan?member=${member}`) });
export const useMeds = (member: string) => useQuery({ queryKey: ['kids', 'health', member], queryFn: () => get<MedsOverview>(`/api/kids/health/meds?member=${member}`) });

/** A change anywhere in kids refreshes every kids panel; chores are planner data, so planner views refresh too. */
export function useSend(onDone?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ method, path, body }: { method: 'POST' | 'PUT' | 'DELETE'; path: string; body?: unknown }) =>
      api<unknown>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) }),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ['kids'] }); void queryClient.invalidateQueries({ queryKey: ['planner'] }); onDone?.(); },
  });
}

export const firstName = (person: Pick<Person, 'name'>) => person.name.split(' ')[0] ?? person.name;
export const num = (value: string) => (value.trim() === '' ? null : Number(value));
