import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError, AppearanceSettings, Empty, Field, Notice, Section, SecondClockSettings, SelectField, SettingsSections, Skeleton, TextField, useNavigate, useSearchParams, useShell } from '@chit/core';
import { CalendarCard } from './CalendarCard';
import HouseholdTypeStep, { HouseholdTypeCards } from './HouseholdTypeStep';
import { MemberCard } from './MemberCard';
import { ModulesSection } from './ModulesSection';
import {
  allowsChildren, allowsMoreAdults, documentForType, newAdult, newCalendar, newChild, removeMember, toPayload, typeProblem, validate, withoutChildlessModules, HOUSEHOLD_TYPES,
  type CatalogModule, type HouseholdDocument, type HouseholdType,
} from './model';

interface Current { state: 'unconfigured' | 'configured'; document?: HouseholdDocument }

const COUNTRIES: [string, string][] = [
  ['', 'Not set'], ['DE', 'Germany'], ['AT', 'Austria'], ['CH', 'Switzerland'], ['NL', 'Netherlands'], ['FR', 'France'],
  ['GB', 'United Kingdom'], ['IE', 'Ireland'], ['US', 'United States'], ['IN', 'India'],
];
const ZONES = ['Europe/Berlin', 'Europe/London', 'Europe/Paris', 'Europe/Amsterdam', 'Europe/Zurich', 'Europe/Vienna', 'America/New_York', 'America/Los_Angeles', 'Asia/Kolkata', 'UTC'];

/** Setup (no household yet, or `?new=1`) and edit (the latest household) share this one form. */
export default function HouseholdView() {
  const [params] = useSearchParams();
  const forceNew = params.get('new') === '1';
  const [type, setType] = useState<HouseholdType | null>(null);
  const current = useQuery({ queryKey: ['household', 'current'], queryFn: () => api<Current>('/api/household/current'), staleTime: 0 });
  const catalog = useQuery({ queryKey: ['modules'], queryFn: () => api<{ modules: CatalogModule[] }>('/api/modules'), staleTime: Infinity });

  if (current.isPending || catalog.isPending) return <Skeleton lines={6} />;
  if (current.isError || catalog.isError) {
    return <Empty title="Household unavailable">The hub could not be reached, so nothing can be shown or saved.</Empty>;
  }
  const editing = !forceNew && current.data.state === 'configured' && current.data.document;
  const hasExisting = current.data.state === 'configured';
  const modules = catalog.data.modules.map((module) => module.id);
  // Creating a household starts with its type: it decides who is added to the draft.
  if (!editing && !type) return <HouseholdTypeStep hasExisting={hasExisting} onPick={setType} />;
  const initial = editing ? current.data.document! : withoutChildlessModules(documentForType(type!, modules), catalog.data.modules);
  // key: a different household (or create vs edit) must reset the draft
  return <HouseholdForm key={editing ? initial.id : `new-${type}`} initial={initial} catalog={catalog.data.modules}
    mode={editing ? 'edit' : 'create'} hasExisting={hasExisting} onChangeType={editing ? undefined : () => setType(null)} />;
}

function HouseholdForm({ initial, catalog, mode, hasExisting, onChangeType }: {
  initial: HouseholdDocument; catalog: CatalogModule[]; mode: 'create' | 'edit'; hasExisting: boolean; onChangeType?: () => void;
}) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(initial);
  const [problems, setProblems] = useState<string[]>([]);
  const [params, setParams] = useSearchParams();
  const dirty = useMemo(() => JSON.stringify(doc) !== JSON.stringify(initial), [doc, initial]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    addEventListener('beforeunload', warn);
    return () => removeEventListener('beforeunload', warn);
  }, [dirty]);

  const save = useMutation({
    mutationFn: () => {
      const payload = toPayload(doc);
      return mode === 'edit'
        ? api('/api/household/' + initial.id, { method: 'PUT', body: JSON.stringify(payload) })
        : api('/api/household/setup', { method: 'POST', body: JSON.stringify(payload) });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries(); // shell, summary, agenda: everything derives from the household
      navigate('/');
    },
    onError: (error) => setProblems([error instanceof ApiError ? error.message : 'Could not reach the hub. Nothing was saved.']),
  });

  const submit = () => {
    const found = validate(doc);
    setProblems(found);
    if (found.length === 0) save.mutate();
  };
  const update = (patch: Partial<HouseholdDocument>) => setDoc((previous) => ({ ...previous, ...patch }));
  const adults = doc.members.filter((member) => member.role === 'adult');
  const extraSections = useShell().data?.settings_sections.filter((section) => section.target === 'household') ?? [];
  // One topic at a time, as tabs (same pattern as the Kids page). The draft lives in this form, so switching tabs loses nothing.
  // Related sections share a tab and sit in two columns: modules with appearance, chores with reminders.
  const GROUP = ['chores', 'reminders'];
  const grouped = extraSections.filter((section) => GROUP.includes(section.id));
  const others = extraSections.filter((section) => !GROUP.includes(section.id));
  const tabs = [
    { id: 'household', label: 'Household' }, { id: 'members', label: 'Members' }, { id: 'calendars', label: 'Calendars' },
    ...(grouped.length ? [{ id: 'routines', label: grouped.map((section) => section.title).join(' & ') }] : []),
    ...others.map((section) => ({ id: section.id, label: section.title })),
  ];
  const tab = tabs.find((item) => item.id === params.get('tab'))?.id ?? 'household';
  const go = (id: string) => setParams((old) => { const next = new URLSearchParams(old); if (id === 'household') next.delete('tab'); else next.set('tab', id); return next; }, { replace: true });
  const type = doc.household.type;
  const typeInfo = HOUSEHOLD_TYPES.find((item) => item.id === type)!;
  const wide = tab === 'household' || (tab === 'members' && allowsChildren(type)) || tab === 'routines';
  // Changing the type is the only way to unlock who can be added; a type the current members do not fit stays blocked, with the reason.
  const blocked = Object.fromEntries(HOUSEHOLD_TYPES.map((item) => [item.id, typeProblem(item.id, doc)]).filter(([, reason]) => reason)) as Partial<Record<HouseholdType, string>>;
  const changeType = (next: HouseholdType) => setDoc((previous) => withoutChildlessModules({ ...previous, household: { ...previous.household, type: next } }, catalog));
  const setDocNormalised = (next: HouseholdDocument) => setDoc(withoutChildlessModules(next, catalog));
  const members = (role: 'adult' | 'child') => doc.members.filter((member) => member.role === role).map((member) => (
    <MemberCard key={member.client_id} member={member} doc={doc} catalog={catalog}
      isOwner={member.client_id === doc.owner_client_id}
      canRemove={member.client_id !== doc.owner_client_id && (member.role === 'child' || adults.length > 1)}
      onChange={(next) => update({ members: doc.members.map((m) => (m.client_id === next.client_id ? next : m)) })}
      onRemove={() => setDocNormalised(removeMember(doc, member.client_id))}
      onMakeOwner={() => update({ owner_client_id: member.client_id })} />
  ));

  return (
    <form className="form-page" onSubmit={(event) => { event.preventDefault(); submit(); }} noValidate>
      <div>
        <div className="eyebrow">{mode === 'edit' ? 'Editing the latest household' : 'New household'}</div>
        <h2 style={{ margin: '4px 0 0', fontSize: '1.5rem' }}>{mode === 'edit' ? 'Household settings' : 'Set up your household'}</h2>
        <p className="field__hint" style={{ fontSize: '0.9rem', maxWidth: '62ch' }}>
          {mode === 'edit'
            ? 'Changes apply to every surface as soon as you save.'
            : 'Add the people whose schedules matter, connect read-only calendars, then choose what appears on your dashboard. The newest household you save is the one Chit shows.'}
        </p>
        {mode === 'create' && hasExisting && <Notice>A household already exists. Saving creates a new one, which then becomes the household Chit shows.</Notice>}
        {onChangeType && <button type="button" className="btn btn--ghost" style={{ marginTop: 8 }} onClick={() => { if (!dirty || window.confirm('Go back and choose a different household type? Your draft is cleared.')) onChangeType(); }}>← Household type</button>}
      </div>

      <nav className="tabnav" aria-label="Settings sections">
        {tabs.map((item) => <button key={item.id} type="button" aria-current={item.id === tab ? 'page' : undefined} onClick={() => go(item.id)}>{item.label}</button>)}
      </nav>

      <div className={wide ? 'form-panel form-panel--wide' : 'form-panel'}>
        {tab === 'household' && (
          <div className="form-cols">
          <div className="form-col">
          <Section id="section-household" title="Household">
            <div className="stack">
              <div className="htype__current">
                <HouseholdTypeCards value={type} onChange={changeType} blocked={blocked} compact />
                <p className="field__hint" style={{ margin: 0 }}>{typeInfo.label}: {typeInfo.note} Change the type to unlock other members. A type your members do not fit stays unavailable until you remove the extras.</p>
              </div>
            <div className="form-grid">
              <TextField label="Household name" value={doc.household.name} placeholder="The Meyer family" required
                onChange={(name) => update({ household: { ...doc.household, name } })} />
              <Field label="Time zone">
                <input className="input" list="zones" value={doc.household.timezone}
                  onChange={(event) => update({ household: { ...doc.household, timezone: event.target.value } })} />
                <datalist id="zones">{ZONES.map((zone) => <option key={zone} value={zone} />)}</datalist>
              </Field>
              <SelectField label="Country" value={doc.household.country_code ?? ''} options={COUNTRIES}
                onChange={(country_code) => update({ household: { ...doc.household, country_code: country_code || null } })} />
              <TextField label="Region / state" value={doc.household.region} placeholder="e.g. Bayern"
                hint="Used for public holidays and school terms."
                onChange={(region) => update({ household: { ...doc.household, region } })} />
              <TextField label="Latitude" type="number" value={doc.household.latitude} placeholder="48.14"
                hint="Optional. Approximate is fine. Used for the weather."
                onChange={(value) => update({ household: { ...doc.household, latitude: value === '' ? null : Number(value) } })} />
              <TextField label="Longitude" type="number" value={doc.household.longitude} placeholder="11.58"
                onChange={(value) => update({ household: { ...doc.household, longitude: value === '' ? null : Number(value) } })} />
        </div>
            </div>
          </Section>
          </div>
          <div className="form-col">
            <Section id="section-modules" title="Dashboard modules">
              <ModulesSection doc={doc} catalog={catalog} onChange={setDocNormalised} />
            </Section>
            <AppearanceSettings eyebrow="Look and feel" />
            <SecondClockSettings />
          </div>
          </div>
        )}
        {tab === 'calendars' && (
          <Section id="section-calendars" title="Calendars"
            actions={<button type="button" className="btn" onClick={() => update({ calendars: [...doc.calendars, newCalendar()] })}>Add calendar</button>}>
            <div className="stack">
              {doc.calendars.length === 0 && <Empty title="No calendars yet">Connect school, waste collection, sport or work calendars. They are read-only.</Empty>}
              {doc.calendars.map((calendar) => (
                <CalendarCard key={calendar.client_id} calendar={calendar} doc={doc}
                  onChange={(next) => update({ calendars: doc.calendars.map((c) => (c.client_id === next.client_id ? next : c)) })}
                  onRemove={() => update({ calendars: doc.calendars.filter((c) => c.client_id !== calendar.client_id) })} />
              ))}
        </div>
          </Section>

        )}
        {tab === 'members' && (
          <div className={allowsChildren(type) ? 'form-cols' : 'form-col'}>
            <Section id="section-adults" title="Adults"
              actions={allowsMoreAdults(type, doc) ? <button type="button" className="btn" onClick={() => update({ members: [...doc.members, newAdult('', doc.members)] })}>Add adult</button> : undefined}>
              <div className="stack">
                {members('adult')}
                {!allowsMoreAdults(type, doc) && <p className="field__hint" style={{ margin: 0 }}>A {typeInfo.label.toLowerCase()} household has {type === 'single' ? 'one adult' : 'two adults'}. To add more people, change the household type under Household.</p>}
              </div>
            </Section>
            {allowsChildren(type) && (
              <Section id="section-children" title="Children"
                actions={<button type="button" className="btn" onClick={() => update({ members: [...doc.members, newChild('', doc.members)] })}>Add child</button>}>
                <div className="stack">
                  {doc.members.some((member) => member.role === 'child') ? members('child') : <Empty title="No children">Add a child to plan school, chores and stars.</Empty>}
                </div>
              </Section>
            )}
          </div>
        )}
        {tab === 'routines' && (
          <div className="form-cols">
            {grouped.map((section) => <div key={section.id}><SettingsSections target="household" ready={mode === 'edit'} only={section.id} /></div>)}
          </div>
        )}
        {others.some((section) => section.id === tab) && <SettingsSections target="household" ready={mode === 'edit'} only={tab} />}
      </div>

      {problems.length > 0 && (
        <Notice tone="error">
          {problems.length === 1 ? problems[0] : <>Please fix:<ul>{problems.map((problem) => <li key={problem}>{problem}</li>)}</ul></>}
        </Notice>
      )}

      <div className="savebar">
        <span className="eyebrow">{save.isPending ? 'Saving…' : dirty ? 'Unsaved changes' : mode === 'edit' ? 'All changes saved' : 'Draft'}</span>
        <div className="row">
          {mode === 'edit' && <button type="button" className="btn btn--ghost" onClick={() => navigate('/household?new=1')}>New household</button>}
          {dirty && <button type="button" className="btn btn--ghost" onClick={() => { setDoc(initial); setProblems([]); }}>Discard</button>}
          <button type="submit" className="btn btn--primary" disabled={save.isPending || (mode === 'edit' && !dirty)}>
            {mode === 'edit' ? 'Save changes' : 'Create household'}
          </button>
        </div>
      </div>
    </form>
  );
}
