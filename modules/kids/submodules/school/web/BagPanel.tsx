import { useState } from 'react';
import { ApiError, CardFrame, Empty, Notice, PlusIcon, Skeleton, TextField } from '@chit/core';
import { useBag, useSend, type BagItem } from '../../../shared/kids';

/** One-tap starting points. Never added on their own: a person taps each one, so the list is always what someone chose. */
const SUGGESTIONS: Record<string, string[]> = {
  sport: ['Sports kit', 'Water bottle'], pe: ['Sports kit', 'Water bottle'], sportunterricht: ['Sportzeug', 'Trinkflasche'],
  music: ['Recorder'], musik: ['Flöte'], art: ['Apron', 'Paints'], kunst: ['Malkasten', 'Kittel'],
  maths: ['Geometry set'], mathe: ['Geodreieck'], swimming: ['Swim bag', 'Towel'], schwimmen: ['Badesachen', 'Handtuch'],
};
const suggestionsFor = (name: string) => SUGGESTIONS[name.trim().toLowerCase()] ?? [];

/** The bag checklist is derived on the phone from tomorrow's lessons, reminders, homework and activities plus these items. */
export default function BagPanel({ memberId, name }: { memberId: string; name: string }) {
  const bag = useBag(memberId);
  const send = useSend();
  const [draft, setDraft] = useState<{ subject: string; label: string }>({ subject: '', label: '' });
  const [error, setError] = useState<string | null>(null);
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');
  const frame = { title: 'Bag checklist', tone: '#7fe0c8' } as const;

  if (bag.isPending) return <CardFrame {...frame} state="unconfigured"><Skeleton lines={3} /></CardFrame>;
  if (bag.isError) return <CardFrame {...frame} state="unavailable"><Empty title="Bag list unavailable">The hub could not be reached.</Empty></CardFrame>;
  const { items, subjects, activities } = bag.data;
  const names = [...new Set([...subjects, ...activities, ...items.map((i) => i.subject)])];   // a name only an item uses (typed by the child) must still be visible to a parent
  const bySubject = new Map<string, BagItem[]>();
  for (const item of items) bySubject.set(item.subject, [...(bySubject.get(item.subject) ?? []), item]);
  const add = (subject: string, label: string, done?: () => void) =>
    send.mutate({ method: 'POST', path: '/api/kids/bag/items', body: { member_id: memberId, subject, label } }, { onSuccess: () => { setError(null); done?.(); }, onError: fail });
  const have = (subject: string, label: string) => items.some((i) => i.subject.toLowerCase() === subject.toLowerCase() && i.label.toLowerCase() === label.toLowerCase());

  return (
    <CardFrame {...frame} state="manual" subtitle={`${name} packs from these. Written by ${name} or a parent`} provenance={['bag items entered in Chit; the checklist itself is worked out on the phone each day']}>
      <div className="stack">
        {names.length === 0 ? <Empty title="No lessons or activities yet">Add the school day first, then attach bag items to each subject.</Empty> : names.map((subject) => {
          const own = bySubject.get(subject) ?? [];
          const ideas = suggestionsFor(subject).filter((label) => !have(subject, label));
          return (
            <div key={subject} className="kd-row" style={{ alignItems: 'flex-start' }}>
              <div className="kd-row__main">
                <div className="kd-row__title">{subject}</div>
                <div className="kd-row__sub" style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
                  {own.length === 0 && ideas.length === 0 && <span>Nothing to bring</span>}
                  {own.map((item) => (
                    <button key={item.id} type="button" className="btn btn--ghost kd-small" title={item.by === 'child' ? `Added by ${name}` : 'Added by a parent'}
                      onClick={() => send.mutate({ method: 'DELETE', path: `/api/kids/bag/items/${item.id}` })}>{item.label} ✕</button>
                  ))}
                  {ideas.map((label) => <button key={label} type="button" className="btn kd-small" onClick={() => add(subject, label)}>+ {label}</button>)}
                </div>
              </div>
            </div>
          );
        })}
        {error && <Notice tone="error">{error}</Notice>}
        <div className="subcard">
          <div className="form-grid">
            <TextField label="For (lesson or activity)" value={draft.subject} placeholder="Sport" onChange={(subject) => setDraft({ ...draft, subject })} />
            <TextField label="Item" value={draft.label} placeholder="Sports kit" onChange={(label) => setDraft({ ...draft, label })} />
          </div>
          <div className="row"><button type="button" className="btn" disabled={!draft.subject.trim() || !draft.label.trim() || send.isPending}
            onClick={() => add(draft.subject, draft.label, () => setDraft({ ...draft, label: '' }))}><PlusIcon />Add item</button></div>
        </div>
      </div>
    </CardFrame>
  );
}
