import './setup.css';
import { useState } from 'react';
import { AVATARS, Avatar, ChipGroup, Field, PERSON_COLORS, PersonAvatar, SelectField, TextField, Toggle, type ChipOption } from '@chit/core';
import { COMMUTE_MODES, DAYS, dayLabel, newActivity, type Activity, type CatalogModule, type HouseholdDocument, type Member, type Profile } from './model';

interface Props {
  member: Member;
  doc: HouseholdDocument;
  catalog: CatalogModule[];
  isOwner: boolean;
  canRemove: boolean;
  onChange: (member: Member) => void;
  onRemove: () => void;
  onMakeOwner: () => void;
}

const AVAILABILITY: [string, string][] = [['not_set', 'Not set'], ['available', 'Usually available'], ['unavailable', 'Usually unavailable'], ['varies', 'Varies']];
const NOTICE: [string, string][] = [['not_set', 'Not set'], ['same_day', 'Same day'], ['one_day', '1 day'], ['two_days', '2 days'], ['one_week', '1 week']];
const AFTER_CARE: [string, string][] = [['not_set', 'Not set'], ['yes', 'Yes'], ['no', 'No'], ['varies', 'Varies']];
const SUPERVISION: [string, string][] = [['not_set', 'Not set'], ['always', 'Always supervised'], ['sometimes', 'Sometimes'], ['independent', 'Independent']];
const LOCATION: [string, string][] = [['', 'Not set'], ['office', 'Office'], ['home', 'Home'], ['off', 'Off']];
const SCHOOL_MODES: [string, string][] = [['', 'Not set'], ...COMMUTE_MODES.map(([v, l]): [string, string] => [v, v === 'car' ? 'By car (a parent drives)' : v === 'walk' ? 'Walks on their own' : 'Cycles on their own'])];
const ACTIVITY_MODES: [string, string][] = [['', 'Not set'], ...COMMUTE_MODES];
const ESCORT: [string, string][] = [['independent', 'On their own'], ['parent', 'With a parent']];
const num = (value: string) => (value === '' ? null : Number(value));

export function MemberCard({ member, doc, catalog, isOwner, canRemove, onChange, onRemove, onMakeOwner }: Props) {
  const [open, setOpen] = useState(!member.name);
  const profile = member.profile;
  const set = (patch: Partial<Profile>) => onChange({ ...member, profile: { ...profile, ...patch } });
  const adults: ChipOption[] = doc.members.filter((m) => m.role === 'adult').map((m) => ({ value: m.client_id, label: m.name || 'Unnamed adult' }));
  const householdModules = new Set(doc.modules ?? catalog.map((module) => module.id));
  const available = catalog.filter((module) => householdModules.has(module.id) && module.audiences.includes(member.role));

  const subtitle = member.role === 'adult' ? (isOwner ? 'Adult · household owner' : 'Adult') : 'Child';

  return (
    <div className="subcard">
      <div className="subcard__head">
        <div className="row">
          <PersonAvatar kind={member.avatar} color={member.color} size={48} />
          <div>
          <div className="subcard__title">{member.name || (member.role === 'adult' ? 'New adult' : 'New child')}</div>
          <div className="eyebrow">{subtitle}</div>
          </div>
        </div>
        <div className="row">
          {member.role === 'adult' && !isOwner && doc.members.filter((m) => m.role === 'adult').length > 1 && (
            <button type="button" className="btn btn--ghost" onClick={onMakeOwner}>Make owner</button>
          )}
          <button type="button" className="btn btn--ghost" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? 'Collapse' : 'Details'}</button>
          {canRemove && <button type="button" className="btn btn--danger" onClick={onRemove}>Remove</button>}
        </div>
      </div>

      <div className="form-grid">
        <TextField label="Name" value={member.name} onChange={(name) => onChange({ ...member, name })} required />
        <TextField label="Birth date" type="date" value={profile.birth_date} onChange={(value) => set({ birth_date: value })} />
      </div>

      {open && (
        <div className="stack">
          <div className="stack" role="group" aria-label={`Avatar for ${member.name || 'this member'}`}>
            {Array.from(new Set(AVATARS[member.role].map((option) => option.group))).map((group) => (
              <div key={group} className="picks__group" role="group" aria-label={group}>
                <span className="eyebrow">{group}</span>
                <div className="picks">
                  {AVATARS[member.role].filter((option) => option.group === group).map((option) => (
                    <button key={option.kind} type="button" className="pick" aria-pressed={member.avatar === option.kind}
                      style={{ ['--c' as string]: member.color ?? 'var(--accent)' }} aria-label={option.label} onClick={() => onChange({ ...member, avatar: option.kind })}>
                      <Avatar kind={option.kind} size={64} />
                      <span>{option.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <Field label="Colour on the dashboard" wide hint="Illustrations only, never photos. The colour follows this person on the timeline, calendar and chores.">
            <div className="swatches" role="group" aria-label="Colour">
              {PERSON_COLORS.map((color) => (
                <button key={color} type="button" className="swatch" aria-pressed={member.color === color} aria-label={color}
                  onClick={() => onChange({ ...member, color })}><i style={{ background: color }} /></button>
              ))}
            </div>
          </Field>
        </div>
      )}

      {open && member.role === 'adult' && (
        <div className="stack">
          <div className="form-grid">
            <TextField label="Work starts" type="time" value={profile.work_start} onChange={(value) => set({ work_start: value })} />
            <TextField label="Work ends" type="time" value={profile.work_end} onChange={(value) => set({ work_end: value })} />
            <TextField label="Commute (min)" type="number" min={0} value={profile.commute_minutes} onChange={(value) => set({ commute_minutes: num(value) })} />
            <SelectField label="Evenings & weekends" value={profile.evening_weekend_availability ?? 'not_set'} options={AVAILABILITY}
              onChange={(value) => set({ evening_weekend_availability: value })} />
            <TextField label="Focus time from" type="time" value={profile.focus_start} onChange={(value) => set({ focus_start: value })} />
            <TextField label="Focus time until" type="time" value={profile.focus_end} onChange={(value) => set({ focus_end: value })} />
            <TextField label="Babysitting evenings / week" type="number" min={0} value={profile.babysitting_max_evenings}
              onChange={(value) => set({ babysitting_max_evenings: num(value) })} />
            <SelectField label="Babysitting notice" value={profile.babysitting_notice ?? 'not_set'} options={NOTICE}
              onChange={(value) => set({ babysitting_notice: value })} />
          </div>
          <Field label="Usual work location by day" wide>
            <div className="weekdays">
              {DAYS.map((day) => (
                <SelectField key={day} label={dayLabel(day)} value={profile.work_days?.[day] ?? ''} options={LOCATION}
                  onChange={(value) => {
                    const next = { ...(profile.work_days ?? {}) };
                    if (value) next[day] = value; else delete next[day];
                    set({ work_days: next });
                  }} />
              ))}
            </div>
          </Field>
        </div>
      )}

      {open && member.role === 'child' && (
        <div className="stack">
          <div className="form-grid">
            <TextField label="School or care" value={profile.school_or_care_name} onChange={(value) => set({ school_or_care_name: value })} />
            <TextField label="Year / type" value={profile.school_type_or_year} placeholder="e.g. Year 4" onChange={(value) => set({ school_type_or_year: value })} />
            <SelectField label="After-school care" value={profile.after_school_care ?? 'not_set'} options={AFTER_CARE} onChange={(value) => set({ after_school_care: value })} />
            <TextField label="Usual drop-off time" type="time" value={profile.dropoff_time} onChange={(value) => set({ dropoff_time: value })} />
            <TextField label="Usual pick-up time" type="time" value={profile.pickup_time} onChange={(value) => set({ pickup_time: value })} />
            <SelectField label="Supervision" value={profile.supervision_policy ?? 'not_set'} options={SUPERVISION} onChange={(value) => set({ supervision_policy: value })} />
            <SelectField label="Getting to school" value={profile.commute_mode ?? ''} options={SCHOOL_MODES}
              onChange={(value) => set({ commute_mode: (value || null) as Profile['commute_mode'] })} />
            <TextField label="Travel time (min)" type="number" min={0} value={profile.travel_minutes} onChange={(value) => set({ travel_minutes: num(value) })} />
          </div>
          <ChipGroup label="Care / school days" selected={profile.care_days ?? []} onChange={(care_days) => set({ care_days })}
            options={DAYS.map((day) => ({ value: day, label: dayLabel(day) }))} />
          {profile.commute_mode === 'walk' || profile.commute_mode === 'cycle' ? (
            <p className="field__hint" style={{ margin: 0 }}>{member.name || 'This child'} travels on their own, so no drop-off or pick-up is planned for a parent.</p>
          ) : (
            <>
              <ChipGroup label="Drop-off adults" selected={profile.dropoff_adult_client_ids ?? []} options={adults}
                hint={adults.length ? 'The first one listed is planned for each trip.' : 'Add an adult first.'} onChange={(dropoff_adult_client_ids) => set({ dropoff_adult_client_ids })} />
              <ChipGroup label="Pick-up adults" selected={profile.pickup_adult_client_ids ?? []} options={adults}
                onChange={(pickup_adult_client_ids) => set({ pickup_adult_client_ids })} />
            </>
          )}
          <ActivityList activities={profile.activities ?? []} adults={adults} onChange={(activities) => set({ activities })} />
        </div>
      )}

      {open && (
        <div className="stack">
          <Toggle label="Uses the same modules as the household" checked={member.modules === null}
            hint="Turn off to limit which enabled modules this person sees. Children never see modules that are not open to them."
            onChange={(same) => onChange({ ...member, modules: same ? null : available.map((module) => module.id) })} />
          {member.modules !== null && (
            <ChipGroup label={`Modules for ${member.name || 'this member'}`} selected={member.modules}
              options={available.map((module) => ({ value: module.id, label: module.title }))}
              onChange={(modules) => onChange({ ...member, modules })} />
          )}
        </div>
      )}
    </div>
  );
}

function ActivityList({ activities, adults, onChange }: { activities: Activity[]; adults: ChipOption[]; onChange: (next: Activity[]) => void }) {
  const patch = (index: number, change: Partial<Activity>) => onChange(activities.map((a, i) => (i === index ? { ...a, ...change } : a)));
  const days = DAYS.map((day) => ({ value: day, label: dayLabel(day) }));
  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="field__label">Regular activities</span>
        <button type="button" className="btn btn--ghost" onClick={() => onChange([...activities, newActivity(adults[0]?.value ?? null)])}>
          Add activity
        </button>
      </div>
      {activities.map((activity, index) => {
        const byCar = activity.commute_mode === 'car';
        const withParent = byCar || activity.escort === 'parent';
        return (
          <div key={index} className="subcard">
            <div className="form-grid">
              <TextField label="Activity" value={activity.name} placeholder="Swimming" onChange={(name) => patch(index, { name })} />
              <TextField label="Where" value={activity.location} onChange={(location) => patch(index, { location })} />
              <TextField label="From" type="time" value={activity.start_time} onChange={(start_time) => patch(index, { start_time })} />
              <TextField label="Until" type="time" value={activity.end_time} onChange={(end_time) => patch(index, { end_time })} />
              <SelectField label="Getting there" value={activity.commute_mode ?? ''} options={ACTIVITY_MODES}
                onChange={(value) => patch(index, { commute_mode: (value || null) as Activity['commute_mode'] })} />
              <TextField label="Travel time (min)" type="number" min={0} value={activity.travel_minutes}
                onChange={(value) => patch(index, { travel_minutes: num(value) })} />
              <SelectField label="Who goes along" value={withParent ? 'parent' : 'independent'} options={ESCORT} disabled={byCar}
                onChange={(value) => patch(index, { escort: value as Activity['escort'], escort_adult_client_id: value === 'parent' ? activity.escort_adult_client_id ?? adults[0]?.value ?? null : null })} />
              {withParent && (
                <SelectField label="Which parent" value={activity.escort_adult_client_id ?? ''}
                  options={[['', 'Choose'], ...adults.map((a): [string, string] => [a.value, a.label])]}
                  onChange={(value) => patch(index, { escort: 'parent', escort_adult_client_id: value || null })} />
              )}
            </div>
            <p className="field__hint" style={{ margin: 0 }}>
              {activity.commute_mode && activity.travel_minutes
                ? withParent ? 'Trips there and back are planned on the parent\'s timeline.' : 'Trips there and back are planned on their own timeline.'
                : 'Add how they get there and the travel time to plan the trips on the timeline. Nothing is assumed.'}
            </p>
            <ChipGroup label="Days" selected={activity.days} options={days} onChange={(next) => patch(index, { days: next })} />
            <div><button type="button" className="btn btn--danger" onClick={() => onChange(activities.filter((_, i) => i !== index))}>Remove activity</button></div>
          </div>
        );
      })}
    </div>
  );
}
