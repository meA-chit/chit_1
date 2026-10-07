import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError, ArrowUpIcon, Empty, Field, Notice, Section, SelectField, SettingsSections, Skeleton, TextField, useNavigate, useSearchParams, useShell } from '@chit/core';
import { CalendarCard } from './CalendarCard';
import { MemberCard } from './MemberCard';
import { ModulesSection } from './ModulesSection';
import {
  emptyDocument, newAdult, newCalendar, newChild, removeMember, toPayload, validate,
  type CatalogModule, type HouseholdDocument,
} from './model';

interface Current { state: 'unconfigured' | 'configured'; document?: HouseholdDocument }

/** Floating "Top" jump, shown once the page is scrolled down. */
function useScrolledDown(threshold = 360) {
  const [down, setDown] = useState(false);
  useEffect(() => {
    const onScroll = () => setDown(window.scrollY > threshold);
    onScroll();
    addEventListener('scroll', onScroll, { passive: true });
    return () => removeEventListener('scroll', onScroll);
  }, [threshold]);
  return down;
}

const COUNTRIES: [string, string][] = [
  ['', 'Not set'], ['DE', 'Germany'], ['AT', 'Austria'], ['CH', 'Switzerland'], ['NL', 'Netherlands'], ['FR', 'France'],
  ['GB', 'United Kingdom'], ['IE', 'Ireland'], ['US', 'United States'], ['IN', 'India'],
];
const ZONES = ['Europe/Berlin', 'Europe/London', 'Europe/Paris', 'Europe/Amsterdam', 'Europe/Zurich', 'Europe/Vienna', 'America/New_York', 'America/Los_Angeles', 'Asia/Kolkata', 'UTC'];

/** Setup (no household yet, or `?new=1`) and edit (the latest household) share this one form. */
export default function HouseholdView() {
  const [params] = useSearchParams();
  const forceNew = params.get('new') === '1';
  const current = useQuery({ queryKey: ['household', 'current'], queryFn: () => api<Current>('/api/household/current'), staleTime: 0 });
  const catalog = useQuery({ queryKey: ['modules'], queryFn: () => api<{ modules: CatalogModule[] }>('/api/modules'), staleTime: Infinity });

  if (current.isPending || catalog.isPending) return <Skeleton lines={6} />;
  if (current.isError || catalog.isError) {
    return <Empty title="Household unavailable">The hub could not be reached, so nothing can be shown or saved.</Empty>;
  }
  const editing = !forceNew && current.data.state === 'configured' && current.data.document;
  const initial = editing ? current.data.document! : emptyDocument(catalog.data.modules.map((module) => module.id));
  // key: a different household (or create vs edit) must reset the draft
  return <HouseholdForm key={editing ? initial.id : 'new'} initial={initial} catalog={catalog.data.modules}
    mode={editing ? 'edit' : 'create'} hasExisting={current.data.state === 'configured'} />;
}

function HouseholdForm({ initial, catalog, mode, hasExisting }: {
  initial: HouseholdDocument; catalog: CatalogModule[]; mode: 'create' | 'edit'; hasExisting: boolean;
}) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(initial);
  const [problems, setProblems] = useState<string[]>([]);
  const scrolled = useScrolledDown();
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
      </div>

      <nav className="form-nav" aria-label="Sections">
        <a href="#section-household">Household</a>
        <a href="#section-calendars">Calendars</a>
        <a href="#section-modules">Modules</a>
        <a href="#section-members">Members</a>
        {extraSections.map((section) => <a key={section.id} href={`#section-${section.id}`}>{section.title}</a>)}
        {scrolled && <button type="button" className="form-nav__top" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}><ArrowUpIcon />Top</button>}
      </nav>

      <div className="form-cols">
        <div className="form-col">
          <Section id="section-household" eyebrow="01" title="Household">
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
          </Section>

          <Section id="section-calendars" eyebrow="02" title="Calendars"
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

          <Section id="section-modules" eyebrow="03" title="Dashboard modules">
            <ModulesSection doc={doc} catalog={catalog} onChange={setDoc} />
          </Section>

        </div>
        <div className="form-col">
          <Section id="section-members" eyebrow="04" title="Household members"
            actions={<div className="row">
              <button type="button" className="btn" onClick={() => update({ members: [...doc.members, newAdult('', doc.members)] })}>Add adult</button>
              <button type="button" className="btn" onClick={() => update({ members: [...doc.members, newChild('', doc.members)] })}>Add child</button>
            </div>}>
            <div className="stack">
              {doc.members.map((member) => (
                <MemberCard key={member.client_id} member={member} doc={doc} catalog={catalog}
                  isOwner={member.client_id === doc.owner_client_id}
                  canRemove={member.client_id !== doc.owner_client_id && (member.role === 'child' || adults.length > 1)}
                  onChange={(next) => update({ members: doc.members.map((m) => (m.client_id === next.client_id ? next : m)) })}
                  onRemove={() => setDoc(removeMember(doc, member.client_id))}
                  onMakeOwner={() => update({ owner_client_id: member.client_id })} />
              ))}
        </div>
          </Section>

          {/* Sections other modules contribute (chores, reminders). They save themselves, so they work on saved members only. */}
          <SettingsSections target="household" ready={mode === 'edit'} />

        </div>
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
