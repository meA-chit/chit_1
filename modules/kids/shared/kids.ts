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

/** A subject is a lesson in the school-day plan (kids/school); it has one of three types. */
export type SubjectKind = 'core' | 'minor' | 'elective';
export const SUBJECT_KINDS: [SubjectKind, string][] = [['core', 'Core'], ['minor', 'Minor'], ['elective', 'Elective']];
export const SUBJECT_KIND_LABEL: Record<SubjectKind, string> = { core: 'Core', minor: 'Minor', elective: 'Elective' };
/** The letter shown as a superscript beside a subject's code: c, m or e. */
export const KIND_LETTER: Record<SubjectKind, string> = { core: 'c', minor: 'm', elective: 'e' };
const letters = (name: string) => name.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
const wordSet = (name: string) => [...new Set(name.toLowerCase().split(/[\s/_&.\-]+/).filter(Boolean))].sort().join('|');
const withinOne = (a: string, b: string) => {                       // at most one letter added, dropped or changed
  if (Math.abs(a.length - b.length) > 1) return false;
  let i = 0; let j = 0; let edits = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { i++; j++; continue; }
    if (++edits > 1) return false;
    if (a.length > b.length) i++; else if (b.length > a.length) j++; else { i++; j++; }
  }
  return edits + (a.length - i) + (b.length - j) <= 1;
};
/** Subjects that look like the same one typed twice (same words in another order, or one letter apart): id -> the other subject. */
export function findDuplicates<T extends { id: string; name: string }>(subjects: T[]): Map<string, T> {
  const found = new Map<string, T>();
  for (let i = 0; i < subjects.length; i++) {
    for (let j = i + 1; j < subjects.length; j++) {
      const a = subjects[i]!; const b = subjects[j]!;
      const la = letters(a.name); const lb = letters(b.name);
      if (wordSet(a.name) === wordSet(b.name) || (la.length >= 4 && lb.length >= 4 && withinOne(la, lb))) {
        if (!found.has(a.id)) found.set(a.id, b);
        if (!found.has(b.id)) found.set(b.id, a);
      }
    }
  }
  return found;
}

export interface SubjectInfo { name: string; code: string; kind: SubjectKind }
/** "Maths (Maths · Core)": how a subject is named in a picker, so nobody types a subject twice. */
export const subjectOption = (s: SubjectInfo): [string, string] => [s.name, `${s.name}  (${s.code}, ${SUBJECT_KIND_LABEL[s.kind]})`];

export interface Subject {
  id: string; name: string; code: string; kind: SubjectKind; lessons: number; count: number; latest: number | null; trend: 'better' | 'worse' | 'steady' | null;
  written: number | null; oral: number | null; average: number | null;
}
export interface GradeEntry { id: string; subject: string; subject_id: string; grade_type: 'written' | 'oral'; grade: number; given_on: string; note: string | null }
export interface GradesOverview {
  state: DataState; member_id?: string; weights: { core_written_pct: number; minor_written_pct: number; elective_written_pct: number }; subjects: Subject[]; entries: GradeEntry[]; scale?: string;
}

export interface Slot { id: string; weekday: number; start: string; end: string; title: string; kind: 'lesson' | 'break' | 'meal' | 'care'; note: string | null; subject_kind: SubjectKind | null; code: string | null }
export interface SchoolPlanData { state: DataState; member_id?: string; today_weekday?: number; now?: string; slots: Slot[] }

export type DoseStatus = 'given' | 'missed' | null;
export interface Med {
  id: string; name: string; dose: string | null; time: string; weekdays: string[]; remind_member_id: string | null; supply: number | null;
  days_left: number | null; refill_soon: boolean; today: { due: boolean; status: DoseStatus };
  week: { day: string; due: boolean; status: DoseStatus }[];
}
export interface MedsOverview { state: DataState; member_id?: string; date?: string; now?: string; meds: Med[] }

export interface HomeworkTask {
  id: string; kind: 'homework' | 'test'; subject: string | null; title: string; due_on: string; note: string | null;
  done: boolean; done_on: string | null; dismissed: boolean; by: 'parent' | 'child'; days: number;
}
export interface HomeworkSummary { due_tomorrow: number; tests_soon: number; overdue: number; done_this_week: number; week: { day: string; open: number; tests: number }[] }
export interface HomeworkOverview { state: DataState; member_id?: string; summary: HomeworkSummary; tasks: HomeworkTask[]; subjects: SubjectInfo[] }

export interface BagItem { id: string; subject: string; label: string; by: 'parent' | 'child' }
export interface BagOverview { state: DataState; member_id?: string; items: BagItem[]; subjects: string[]; activities: string[] }

export const GRADE_STEPS: [number, string][] = [[1, '1'], [1.3, '1-'], [1.7, '2+'], [2, '2'], [2.3, '2-'], [2.7, '3+'], [3, '3'], [3.3, '3-'], [3.7, '4+'], [4, '4'], [4.3, '4-'], [4.7, '5+'], [5, '5'], [5.3, '5-'], [6, '6']];
export const gradeLabel = (value: number) => GRADE_STEPS.find(([v]) => Math.abs(v - value) < 0.05)?.[1] ?? value.toFixed(1);
export const WEEKDAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
export const dayShort = (name: string) => name.slice(0, 3).replace(/^./, (c) => c.toUpperCase());

const get = <T,>(path: string) => api<T>(path);
export const useStars = () => useQuery({ queryKey: ['kids', 'stars'], queryFn: () => get<StarsOverview>('/api/kids/stars/overview') });
export const useGrades = (member: string) => useQuery({ queryKey: ['kids', 'grades', member], queryFn: () => get<GradesOverview>(`/api/kids/grades/overview?member=${member}`) });
export const useSchoolPlan = (member: string) => useQuery({ queryKey: ['kids', 'school', member], queryFn: () => get<SchoolPlanData>(`/api/kids/school/plan?member=${member}`) });
export const useHomework = (member: string) => useQuery({ queryKey: ['kids', 'homework', member], queryFn: () => get<HomeworkOverview>(`/api/kids/homework?member=${member}`) });
export const useBag = (member: string) => useQuery({ queryKey: ['kids', 'bag', member], queryFn: () => get<BagOverview>(`/api/kids/bag?member=${member}`) });
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
