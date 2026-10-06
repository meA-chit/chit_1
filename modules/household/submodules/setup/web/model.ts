/** The household document: identical to the API, seed fixtures and exports (ADR-0010). */

export type Role = 'adult' | 'child';
export const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const;
export type Day = (typeof DAYS)[number];
export const dayLabel = (day: string) => day.slice(0, 3).replace(/^./, (c) => c.toUpperCase());

export interface Activity {
  name: string;
  location: string | null;
  start_time: string | null;
  end_time: string | null;
  days: string[];
  commute_mode: CommuteMode | null;
  travel_minutes: number | null;
  escort: 'independent' | 'parent';
  escort_adult_client_id: string | null;
}

export type CommuteMode = 'walk' | 'cycle' | 'car';
export const COMMUTE_MODES: [CommuteMode, string][] = [['walk', 'Walks'], ['cycle', 'Cycles'], ['car', 'By car']];

export const newActivity = (escortAdult: string | null = null): Activity => ({
  name: '', location: null, start_time: null, end_time: null, days: [],
  commute_mode: null, travel_minutes: null, escort: 'independent', escort_adult_client_id: escortAdult,
});

export interface Profile {
  birth_date?: string | null;
  // adult
  work_start?: string | null;
  work_end?: string | null;
  commute_minutes?: number | null;
  evening_weekend_availability?: string;
  focus_start?: string | null;
  focus_end?: string | null;
  babysitting_max_evenings?: number | null;
  babysitting_notice?: string;
  work_days?: Record<string, string>;
  // child
  school_or_care_name?: string | null;
  school_type_or_year?: string | null;
  after_school_care?: string;
  dropoff_time?: string | null;
  pickup_time?: string | null;
  supervision_policy?: string;
  travel_minutes?: number | null;
  commute_mode?: CommuteMode | null;
  care_days?: string[];
  pickup_adult_client_ids?: string[];
  dropoff_adult_client_ids?: string[];
  activities?: Activity[];
}

export interface Member {
  client_id: string;
  role: Role;
  name: string;
  avatar: string | null; // predefined illustration (a1-a4 adults, k1-k4 children)
  color: string | null; // the person's colour on every card
  profile: Profile;
  modules: string[] | null; // null = same as the household
}

export interface Calendar {
  client_id: string;
  name: string;
  category: string;
  subscription_url: string;
  member_client_ids: string[];
  chore_enabled: boolean;
  chore_title: string | null;
  chore_assignee_client_ids: string[];
  connection_state?: string;
}

export interface HouseholdDocument {
  id?: string;
  household: { name: string; timezone: string; country_code: string | null; region: string | null; latitude: number | null; longitude: number | null };
  owner_client_id: string;
  modules: string[] | null;
  members: Member[];
  calendars: Calendar[];
}

export const CATEGORIES: [string, string][] = [
  ['waste_collection', 'Waste collection'],
  ['school_care', 'School / care'],
  ['sport_activity', 'Sport / activity'],
  ['work', 'Work'],
  ['family', 'Family'],
  ['other', 'Other'],
];

export const uid = (prefix: string) => `${prefix}-${Math.random().toString(36).slice(2, 9)}`;

const ADULT_KINDS = ['a2', 'a1', 'a3', 'a4'];
const CHILD_KINDS = ['k2', 'k3', 'k1', 'k4'];
const COLORS = ['#b79cff', '#4df0ff', '#ff8fb8', '#ffc857', '#8dffb0', '#ff9d5c'];

/** First avatar of the role and first colour nobody in the household uses yet. */
export function nextIdentity(members: Member[], role: Role): { avatar: string; color: string } {
  const kinds = role === 'adult' ? ADULT_KINDS : CHILD_KINDS;
  const avatar = kinds.find((kind) => !members.some((m) => m.avatar === kind)) ?? kinds[members.length % kinds.length]!;
  const color = COLORS.find((c) => !members.some((m) => m.color === c)) ?? COLORS[members.length % COLORS.length]!;
  return { avatar, color };
}

export function newAdult(name = '', taken: Member[] = []): Member {
  return {
    client_id: uid('adult'), role: 'adult', name, modules: null, ...nextIdentity(taken, 'adult'),
    profile: { evening_weekend_availability: 'not_set', babysitting_notice: 'not_set', work_days: {} },
  };
}

export function newChild(name = '', taken: Member[] = []): Member {
  return {
    client_id: uid('child'), role: 'child', name, modules: null, ...nextIdentity(taken, 'child'),
    profile: {
      after_school_care: 'not_set', supervision_policy: 'not_set', care_days: [],
      pickup_adult_client_ids: [], dropoff_adult_client_ids: [], activities: [],
    },
  };
}

export function newCalendar(): Calendar {
  return {
    client_id: uid('cal'), name: '', category: 'family', subscription_url: '', member_client_ids: [],
    chore_enabled: false, chore_title: null, chore_assignee_client_ids: [],
  };
}

export function emptyDocument(modules: string[] | null): HouseholdDocument {
  const first = newAdult();
  return {
    household: { name: '', timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Berlin', country_code: null, region: null, latitude: null, longitude: null },
    owner_client_id: first.client_id,
    modules,
    members: [first],
    calendars: [],
  };
}

/** Remove a member everywhere it is referenced, so the server never sees a dangling id. */
export function removeMember(doc: HouseholdDocument, clientId: string): HouseholdDocument {
  const without = (ids?: string[]) => (ids ?? []).filter((id) => id !== clientId);
  return {
    ...doc,
    members: doc.members
      .filter((member) => member.client_id !== clientId)
      .map((member) => member.role === 'child'
        ? { ...member, profile: { ...member.profile,
            pickup_adult_client_ids: without(member.profile.pickup_adult_client_ids),
            dropoff_adult_client_ids: without(member.profile.dropoff_adult_client_ids),
            activities: (member.profile.activities ?? []).map((activity) => activity.escort_adult_client_id === clientId
              ? { ...activity, escort: 'independent' as const, escort_adult_client_id: null } : activity) } }
        : member),
    calendars: doc.calendars.map((calendar) => ({
      ...calendar,
      member_client_ids: without(calendar.member_client_ids),
      chore_assignee_client_ids: without(calendar.chore_assignee_client_ids),
    })),
  };
}

/** Switch a household module on/off, keeping dependencies and member narrowing consistent. */
export function toggleModule(
  doc: HouseholdDocument, catalog: CatalogModule[], moduleId: string, on: boolean,
): HouseholdDocument {
  const all = catalog.map((module) => module.id);
  let next = new Set(doc.modules ?? all);
  const byId = new Map(catalog.map((module) => [module.id, module]));
  if (on) {
    const add = (id: string) => {
      next.add(id);
      byId.get(id)?.depends_on.forEach((dependency) => !next.has(dependency) && add(dependency));
    };
    add(moduleId);
  } else {
    const drop = (id: string) => {
      next.delete(id);
      catalog.filter((module) => module.depends_on.includes(id) && next.has(module.id)).forEach((module) => drop(module.id));
    };
    drop(moduleId);
  }
  next.add('household');
  next = new Set([...next].filter((id) => byId.has(id)));
  return {
    ...doc,
    modules: [...next],
    members: doc.members.map((member) => member.modules
      ? { ...member, modules: member.modules.filter((id) => next.has(id)) } : member),
  };
}

export interface CatalogModule {
  id: string;
  title: string;
  status: string;
  privacy_class: string;
  audiences: string[];
  depends_on: string[];
  submodules: string[];
  required: boolean;
}

export function validate(doc: HouseholdDocument): string[] {
  const problems: string[] = [];
  if (!doc.household.name.trim()) problems.push('Give the household a name.');
  if (!doc.household.timezone.trim()) problems.push('Choose a time zone.');
  const { latitude: lat, longitude: lon } = doc.household;
  if (lat !== null && (Number.isNaN(lat) || lat < -90 || lat > 90)) problems.push('Latitude must be between -90 and 90.');
  if (lon !== null && (Number.isNaN(lon) || lon < -180 || lon > 180)) problems.push('Longitude must be between -180 and 180.');
  if ((lat === null) !== (lon === null)) problems.push('Enter both latitude and longitude, or neither.');
  if (!doc.members.some((member) => member.role === 'adult')) problems.push('Add at least one adult.');
  doc.members.forEach((member, index) => {
    if (!member.name.trim()) problems.push(`Member ${index + 1} needs a name.`);
  });
  const owner = doc.members.find((member) => member.client_id === doc.owner_client_id);
  if (!owner || owner.role !== 'adult') problems.push('The household owner must be an adult.');
  doc.members.filter((member) => member.role === 'child').forEach((child) => {
    for (const activity of child.profile.activities ?? []) {
      if (!activity.name.trim()) continue;
      const who = `${child.name.trim() || 'Child'}'s ${activity.name.trim()}`;
      if (activity.start_time && activity.end_time && activity.end_time <= activity.start_time) problems.push(`${who}: the end time must be after the start.`);
      if (activity.commute_mode && !activity.travel_minutes) problems.push(`${who}: enter the travel time, or clear how they get there.`);
      if ((activity.commute_mode === 'car' || activity.escort === 'parent') && !activity.escort_adult_client_id) problems.push(`${who}: choose which parent goes along.`);
    }
  });
  doc.calendars.forEach((calendar, index) => {
    const label = calendar.name.trim() || `Calendar ${index + 1}`;
    if (!calendar.name.trim()) problems.push(`${label} needs a name.`);
    if (!/^(https:|webcal:)\/\/\S+$/i.test(calendar.subscription_url.trim())) problems.push(`${label}: use an https:// or webcal:// link.`);
  });
  return problems;
}

const blank = <T,>(value: T | null | undefined | '') => (value === '' || value === undefined ? null : value);

/** Normalise form state to the API document: empty strings become null, strings are trimmed. */
export function toPayload(doc: HouseholdDocument): HouseholdDocument {
  const trim = (value?: string | null) => blank(value?.trim());
  return {
    ...doc,
    household: {
      name: doc.household.name.trim(), timezone: doc.household.timezone.trim(),
      country_code: blank(doc.household.country_code), region: trim(doc.household.region),
      latitude: doc.household.latitude, longitude: doc.household.longitude,
    },
    members: doc.members.map((member) => ({
      ...member,
      name: member.name.trim(),
      profile: {
        ...member.profile,
        birth_date: blank(member.profile.birth_date),
        dropoff_time: blank(member.profile.dropoff_time),
        pickup_time: blank(member.profile.pickup_time),
        school_or_care_name: trim(member.profile.school_or_care_name),
        school_type_or_year: trim(member.profile.school_type_or_year),
        commute_mode: blank(member.profile.commute_mode),
        activities: member.profile.activities?.filter((activity) => activity.name.trim()).map((activity) => {
          const escort = activity.commute_mode === 'car' ? 'parent' : activity.escort;   // a car trip always has a parent
          return {
            ...activity, name: activity.name.trim(), location: trim(activity.location),
            start_time: blank(activity.start_time), end_time: blank(activity.end_time),
            commute_mode: blank(activity.commute_mode), escort,
            escort_adult_client_id: escort === 'parent' ? blank(activity.escort_adult_client_id) : null,
          };
        }),
      },
    })),
    calendars: doc.calendars.map((calendar) => ({
      ...calendar, name: calendar.name.trim(), subscription_url: calendar.subscription_url.trim(),
      chore_title: calendar.chore_enabled ? trim(calendar.chore_title) : null,
    })),
  };
}
