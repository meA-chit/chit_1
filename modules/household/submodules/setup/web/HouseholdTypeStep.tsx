import { useState } from 'react';
import { Avatar } from '@chit/core';
import { HOUSEHOLD_TYPES, type HouseholdType } from './model';
import './setup.css';

/** The people drawn on each card come from the same illustrations as the members, so the choice previews who lives there. */
const ART: Record<HouseholdType, { kind: string; size: number }[]> = {
  shared: [{ kind: 'a1', size: 56 }, { kind: 'a6', size: 66 }, { kind: 'a7', size: 56 }],
  family: [{ kind: 'a5', size: 60 }, { kind: 'a2', size: 60 }, { kind: 'k5', size: 44 }],
  couple: [{ kind: 'a3', size: 62 }, { kind: 'a8', size: 62 }],
  single: [{ kind: 'a4', size: 70 }],
};

/** The four type cards. `blocked` maps a type to the reason it cannot be chosen right now (shown on the card, the card stays unselectable). */
export function HouseholdTypeCards({ value, onChange, blocked = {}, compact = false }: {
  value: HouseholdType; onChange: (type: HouseholdType) => void; blocked?: Partial<Record<HouseholdType, string>>; compact?: boolean;
}) {
  return (
    <div className="htype__grid" data-compact={compact || undefined} role="radiogroup" aria-label="Household type">
      {HOUSEHOLD_TYPES.map((item) => {
        const reason = value === item.id ? undefined : blocked[item.id];
        return (
          <button key={item.id} type="button" role="radio" aria-checked={value === item.id} aria-disabled={reason ? true : undefined}
            className="htype__card" data-blocked={reason ? true : undefined} title={reason}
            onClick={() => { if (!reason) onChange(item.id); }}>
            <span className="htype__art" aria-hidden>
              {ART[item.id].map((person, index) => <span key={index} className="htype__person"><Avatar kind={person.kind} size={compact ? Math.round(person.size * 0.62) : person.size} label="" /></span>)}
            </span>
            <span className="htype__label">{item.label}</span>
            <span className="htype__note">{reason ?? item.note}</span>
          </button>
        );
      })}
    </div>
  );
}

export default function HouseholdTypeStep({ onPick, hasExisting }: { onPick: (type: HouseholdType) => void; hasExisting: boolean }) {
  const [type, setType] = useState<HouseholdType>('family');
  return (
    <div className="form-page htype">
      <div>
        <div className="eyebrow">Step 1 of 2</div>
        <h2 style={{ margin: '4px 0 0', fontSize: '1.5rem' }}>Select your household type</h2>
        <p className="field__hint" style={{ fontSize: '0.9rem', maxWidth: '62ch' }}>
          Choose whether you live in a shared flat, with your family, as a couple or alone. We add the people to match, and what you can add later
          follows from it. You can change the type in the household settings.
          {hasExisting && ' A household already exists: saving creates a new one, which then becomes the household Chit shows.'}
        </p>
      </div>
      <HouseholdTypeCards value={type} onChange={setType} />
      <div className="row"><button type="button" className="btn btn--primary htype__next" onClick={() => onPick(type)}>Next</button></div>
    </div>
  );
}
