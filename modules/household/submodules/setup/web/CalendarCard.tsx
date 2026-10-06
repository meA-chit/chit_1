import { ChipGroup, SelectField, StateBadge, TextField, Toggle, type DataState } from '@chit/core';
import { CATEGORIES, type Calendar, type HouseholdDocument } from './model';

const STATE: Record<string, DataState> = { available: 'available', stale: 'stale', unavailable: 'unavailable' };

export function CalendarCard({ calendar, doc, onChange, onRemove }: {
  calendar: Calendar; doc: HouseholdDocument; onChange: (calendar: Calendar) => void; onRemove: () => void;
}) {
  const people = doc.members.map((m) => ({ value: m.client_id, label: m.name || 'Unnamed' }));
  const set = (patch: Partial<Calendar>) => onChange({ ...calendar, ...patch });
  return (
    <div className="subcard">
      <div className="subcard__head">
        <div className="row">
          <span className="subcard__title">{calendar.name || 'New calendar'}</span>
          <span className="eyebrow">read only</span>
          {calendar.connection_state && STATE[calendar.connection_state] && <StateBadge state={STATE[calendar.connection_state]!} />}
        </div>
        <button type="button" className="btn btn--danger" onClick={onRemove}>Remove</button>
      </div>
      <div className="form-grid">
        <TextField label="Name" value={calendar.name} onChange={(name) => set({ name })} required />
        <SelectField label="Type" value={calendar.category} options={CATEGORIES} onChange={(category) => set({ category })} />
        <TextField label="Feed link (https:// or webcal://)" type="url" wide value={calendar.subscription_url}
          placeholder="https://…/calendar.ics" hint="Chit only reads this feed. It is stored on this hub and never shown on shared screens."
          onChange={(subscription_url) => set({ subscription_url })} />
      </div>
      <ChipGroup label="Whose calendar is it?" options={people} selected={calendar.member_client_ids} onChange={(member_client_ids) => set({ member_client_ids })} />
      {calendar.category === 'waste_collection' && (
        <div className="stack">
          <Toggle label="Create a chore for each collection" checked={calendar.chore_enabled} onChange={(chore_enabled) => set({ chore_enabled })} />
          {calendar.chore_enabled && (
            <>
              <TextField label="Chore title" value={calendar.chore_title} placeholder={`Prepare for ${calendar.name || 'collection'}`} onChange={(chore_title) => set({ chore_title })} />
              <ChipGroup label="Who does it?" options={people} selected={calendar.chore_assignee_client_ids} onChange={(chore_assignee_client_ids) => set({ chore_assignee_client_ids })} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
