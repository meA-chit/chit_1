import { useState } from 'react';
import { ApiError, BookIcon, CardFrame, ChipGroup, Empty, Notice, PlusIcon, SelectField, Skeleton, TextField } from '@chit/core';
import { GRADE_STEPS, gradeLabel, num, useGrades, useSend, type Subject } from '../../../shared/kids';

const tone = (avg: number | null) => (avg === null ? {} : avg <= 2.4 ? { 'data-good': true } : avg < 3.5 ? { 'data-mid': true } : { 'data-bad': true });
const cell = (value: number | null) => <span className="mono" style={{ fontSize: '0.85rem', color: value === null ? 'var(--text-faint)' : 'var(--text-dim)' }}>{value === null ? 'none' : value.toFixed(1)}</span>;
const TREND: Record<string, { mark: string; text: string; color: string }> = {
  better: { mark: '↑', text: 'better', color: 'var(--lime)' }, worse: { mark: '↓', text: 'worse', color: 'var(--amber)' }, steady: { mark: '→', text: 'steady', color: 'var(--text-dim)' },
};

function SubjectRows({ title, subjects }: { title: string; subjects: Subject[] }) {
  if (subjects.length === 0) return null;
  return (
    <div>
      <div className="kd-grade kd-grade--head"><span>{title}</span><span>Written</span><span>Oral</span><span>Avg</span><span>Trend</span></div>
      {subjects.map((subject) => (
        <div key={subject.id} className="kd-grade">
          <span style={{ fontWeight: 500 }}>{subject.name}</span>{cell(subject.written)}{cell(subject.oral)}
          <span className="kd-avg" {...tone(subject.average)}>{subject.average === null ? '–' : subject.average.toFixed(1)}</span>
          {subject.trend ? <span style={{ fontSize: '0.78rem', color: TREND[subject.trend]!.color }} title={`Trend: ${TREND[subject.trend]!.text}`}>{TREND[subject.trend]!.mark} {TREND[subject.trend]!.text}</span> : <span />}
        </div>
      ))}
    </div>
  );
}

/** The grade overview for one child: average and trend per subject, with adding a grade inline. Grades are private to parents. */
export default function GradesOverview({ memberId, name }: { memberId: string; name: string }) {
  const grades = useGrades(memberId);
  const send = useSend();
  const today = new Date().toLocaleDateString('en-CA');
  const [adding, setAdding] = useState(false);
  const [entry, setEntry] = useState({ subject_id: '', grade_type: 'written', grade: '2', date: today, note: '' });
  const [error, setError] = useState<string | null>(null);
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');
  const frame = { title: 'Grades', icon: <BookIcon />, tone: '#8b7bff' } as const;

  if (grades.isPending) return <CardFrame {...frame} state="unconfigured"><Skeleton lines={5} /></CardFrame>;
  if (grades.isError) return <CardFrame {...frame} state="unavailable"><Empty title="Grades unavailable">The hub could not be reached.</Empty></CardFrame>;
  const data = grades.data;
  const chosen = entry.subject_id || data.subjects[0]?.id || '';
  const main = data.subjects.filter((s) => s.kind === 'main');
  const other = data.subjects.filter((s) => s.kind === 'other');

  return (
    <CardFrame {...frame} state="manual" subtitle={`${name} · scale 1 (best) to 6 · weighted per subject type`} provenance={['grades entered in Chit, visible to parents only']}>
      <div className="stack">
        {data.subjects.length === 0 ? <Empty title="No subjects yet">Add the first subject under Manage, below.</Empty> : <div className="kd-grades"><SubjectRows title="Main subjects" subjects={main} /><SubjectRows title="Other subjects" subjects={other} /></div>}
        {adding ? (
          <div className="subcard">
            <div className="form-grid">
              <SelectField label="Subject" value={chosen} options={data.subjects.length ? data.subjects.map((s): [string, string] => [s.id, s.name]) : [['', 'Add a subject first']]} onChange={(subject_id) => setEntry({ ...entry, subject_id })} />
              <SelectField label="Grade" value={entry.grade} options={GRADE_STEPS.map(([v, l]): [string, string] => [String(v), l])} onChange={(grade) => setEntry({ ...entry, grade })} />
              <TextField label="Date" type="date" value={entry.date} onChange={(date) => setEntry({ ...entry, date })} />
              <TextField label="Note" value={entry.note} placeholder="Optional, parents only" onChange={(note) => setEntry({ ...entry, note })} />
            </div>
            <ChipGroup single label="Type of grade" selected={[entry.grade_type]} onChange={(v) => v[0] && setEntry({ ...entry, grade_type: v[0] })}
              options={[{ value: 'written', label: 'Written exam' }, { value: 'oral', label: 'Oral / short test' }]} />
            {error && <Notice tone="error">{error}</Notice>}
            <div className="row">
              <button type="button" className="btn" disabled={!chosen || send.isPending}
                onClick={() => send.mutate({ method: 'POST', path: '/api/kids/grades', body: { subject_id: chosen, grade_type: entry.grade_type, grade: num(entry.grade), date: entry.date, note: entry.note || null } },
                  { onSuccess: () => { setEntry({ ...entry, note: '' }); setError(null); setAdding(false); }, onError: fail })}>Save grade</button>
              <button type="button" className="btn btn--ghost" onClick={() => { setAdding(false); setError(null); }}>Cancel</button>
            </div>
          </div>
        ) : <div><button type="button" className="btn" disabled={data.subjects.length === 0} onClick={() => setAdding(true)}><PlusIcon />Add a grade</button></div>}
      </div>
    </CardFrame>
  );
}

/** Grade management for the bottom of the Kids page: latest entries, the subject list and how the average is weighted. */
export function GradesSettings({ memberId }: { memberId: string }) {
  const grades = useGrades(memberId);
  const send = useSend();
  const [subject, setSubject] = useState<{ name: string; kind: string } | null>(null);
  const [weights, setWeights] = useState<{ main: string; other: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');

  if (grades.isPending) return <CardFrame title="Grade settings" state="unconfigured"><Skeleton lines={4} /></CardFrame>;
  if (grades.isError) return <CardFrame title="Grade settings" state="unavailable"><Empty title="Grades unavailable">The hub could not be reached.</Empty></CardFrame>;
  const data = grades.data;

  return (
    <>
      <CardFrame title="Subjects" state="manual" tone="#8b7bff" subtitle="Main (German, Maths, English) or other (Geography, Biology, Music, Sport)">
        <div className="stack">
          {data.subjects.map((s) => (
            <div key={s.id} className="kd-row"><div className="kd-row__main"><div className="kd-row__title">{s.name}</div><div className="kd-row__sub">{s.kind === 'main' ? 'Main subject' : 'Other subject'} · {s.count} grade{s.count === 1 ? '' : 's'}</div></div>
              <button type="button" className="btn btn--ghost kd-small" onClick={() => send.mutate({ method: 'PUT', path: `/api/kids/grades/subjects/${s.id}`, body: { name: s.name, kind: s.kind === 'main' ? 'other' : 'main' } })}>Make {s.kind === 'main' ? 'other' : 'main'}</button>
              <button type="button" className="btn btn--ghost kd-small" onClick={() => send.mutate({ method: 'DELETE', path: `/api/kids/grades/subjects/${s.id}` })}>Remove</button></div>
          ))}
          {subject ? (
            <div className="subcard">
              <div className="form-grid">
                <TextField label="Subject" value={subject.name} placeholder="Geography" onChange={(n) => setSubject({ ...subject, name: n })} />
                <SelectField label="Kind" value={subject.kind} options={[['main', 'Main subject'], ['other', 'Other subject']]} onChange={(kind) => setSubject({ ...subject, kind })} />
              </div>
              {error && <Notice tone="error">{error}</Notice>}
              <div className="row">
                <button type="button" className="btn" disabled={!subject.name.trim()} onClick={() => send.mutate({ method: 'POST', path: '/api/kids/grades/subjects', body: { member_id: memberId, name: subject.name, kind: subject.kind } }, { onSuccess: () => { setSubject(null); setError(null); }, onError: fail })}>Add subject</button>
                <button type="button" className="btn btn--ghost" onClick={() => setSubject(null)}>Cancel</button>
              </div>
            </div>
          ) : <div><button type="button" className="btn" onClick={() => setSubject({ name: '', kind: 'main' })}><PlusIcon />Add a subject</button></div>}
        </div>
      </CardFrame>
      <CardFrame title="Latest grade entries" state="manual" tone="#8b7bff" subtitle="Newest first">
        {data.entries.length === 0 ? <p className="field__hint" style={{ margin: 0 }}>No grades yet.</p> : data.entries.map((g) => (
          <div key={g.id} className="kd-row">
            <span className="mono" style={{ width: 84, fontSize: '0.75rem', color: 'var(--text-dim)' }}>{g.given_on}</span>
            <div className="kd-row__main"><div className="kd-row__title">{g.subject}</div><div className="kd-row__sub">{g.grade_type === 'written' ? 'Written exam' : 'Oral / short test'}{g.note ? ` · ${g.note}` : ''}</div></div>
            <b style={{ fontSize: '1.05rem', color: g.grade <= 2.4 ? 'var(--lime)' : g.grade < 3.5 ? 'var(--amber)' : 'var(--magenta)' }}>{gradeLabel(g.grade)}</b>
            <button type="button" className="btn btn--ghost kd-small" onClick={() => send.mutate({ method: 'DELETE', path: `/api/kids/grades/${g.id}` })}>Delete</button>
          </div>
        ))}
      </CardFrame>
      <CardFrame title="How the average is worked out" state="manual" tone="#8b7bff" subtitle="Set once for the household">
        <div className="stack">
          <p className="field__hint" style={{ margin: 0 }}>Each type is averaged on its own, then combined with these weights. A subject with only one type uses it alone. Your school's rules decide the split.</p>
          {weights ? (
            <>
              <div className="form-grid">
                <TextField label="Main subjects: written %" type="number" min={0} value={weights.main} onChange={(main) => setWeights({ ...weights, main })} hint="Oral is the rest" />
                <TextField label="Other subjects: written %" type="number" min={0} value={weights.other} onChange={(other) => setWeights({ ...weights, other })} hint="Oral is the rest" />
              </div>
              <div className="row">
                <button type="button" className="btn" onClick={() => send.mutate({ method: 'PUT', path: '/api/kids/grades/weights', body: { main_written_pct: num(weights.main), other_written_pct: num(weights.other) } }, { onSuccess: () => setWeights(null), onError: fail })}>Save</button>
                <button type="button" className="btn btn--ghost" onClick={() => setWeights(null)}>Cancel</button>
              </div>
            </>
          ) : (
            <div className="row" style={{ alignItems: 'center' }}>
              <span style={{ flex: 1, fontSize: '0.85rem' }}>Main: written <b>{data.weights.main_written_pct}%</b> · oral <b>{100 - data.weights.main_written_pct}%</b><br />Other: written <b>{data.weights.other_written_pct}%</b> · oral <b>{100 - data.weights.other_written_pct}%</b></span>
              <button type="button" className="btn btn--ghost" onClick={() => setWeights({ main: String(data.weights.main_written_pct), other: String(data.weights.other_written_pct) })}>Edit weights</button>
            </div>
          )}
        </div>
      </CardFrame>
    </>
  );
}
