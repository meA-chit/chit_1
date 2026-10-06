import type { ReactNode } from 'react';

/** Form primitives for module setup screens. Styling lives in theme/ui.css (tokens only). */

export function Section({ id, eyebrow, title, actions, children }: { id?: string; eyebrow?: string; title: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section id={id} className="card form-section" aria-label={title}>
      <span className="card__scan" aria-hidden />
      <header className="card__head">
        <div>
          {eyebrow && <div className="eyebrow">{eyebrow}</div>}
          <h2 className="card__title" style={{ fontSize: '1.1rem', marginTop: 2 }}>{title}</h2>
        </div>
        {actions}
      </header>
      <div className="card__body">{children}</div>
    </section>
  );
}

export function Field({ label, hint, wide, children }: { label: string; hint?: string; wide?: boolean; children: ReactNode }) {
  return (
    <label className="field" data-wide={wide || undefined}>
      <span className="field__label">{label}</span>
      {children}
      {hint && <span className="field__hint">{hint}</span>}
    </label>
  );
}

interface TextProps {
  label: string;
  value: string | number | null | undefined;
  onChange: (value: string) => void;
  type?: 'text' | 'time' | 'date' | 'number' | 'url' | 'password';
  placeholder?: string;
  hint?: string;
  list?: string;
  min?: number;
  wide?: boolean;
  required?: boolean;
}
export function TextField({ label, value, onChange, type = 'text', placeholder, hint, list, min, wide, required }: TextProps) {
  return (
    <Field label={label} hint={hint} wide={wide}>
      <input className="input" type={type} value={value ?? ''} autoComplete={type === 'password' ? 'off' : undefined} spellCheck={type === 'password' ? false : undefined} placeholder={placeholder} list={list} min={min} required={required}
        onChange={(event) => onChange(event.target.value)} />
    </Field>
  );
}

export function SelectField({ label, value, onChange, options, hint, disabled }: {
  label: string; value: string; onChange: (value: string) => void; options: [string, string][]; hint?: string; disabled?: boolean;
}) {
  return (
    <Field label={label} hint={hint}>
      <select className="input" value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
      </select>
    </Field>
  );
}

export interface ChipOption { value: string; label: string; disabled?: boolean; note?: string }

export function ChipGroup({ label, options, selected, onChange, hint, single }: {
  label: string; options: ChipOption[]; selected: string[]; onChange: (next: string[]) => void; hint?: string; single?: boolean;
}) {
  const toggle = (value: string) => {
    if (single) return onChange(selected.includes(value) ? [] : [value]);
    onChange(selected.includes(value) ? selected.filter((item) => item !== value) : [...selected, value]);
  };
  return (
    <fieldset className="field" data-wide>
      <legend className="field__label">{label}</legend>
      <div className="chips">
        {options.length === 0 && <span className="field__hint">Nothing to choose yet.</span>}
        {options.map((option) => (
          <button key={option.value} type="button" className="chip" aria-pressed={selected.includes(option.value)}
            disabled={option.disabled} title={option.note} onClick={() => toggle(option.value)}>
            {option.label}
          </button>
        ))}
      </div>
      {hint && <span className="field__hint">{hint}</span>}
    </fieldset>
  );
}

export function Toggle({ label, checked, onChange, disabled, hint }: {
  label: string; checked: boolean; onChange: (checked: boolean) => void; disabled?: boolean; hint?: string;
}) {
  return (
    <label className="toggle" data-disabled={disabled || undefined}>
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(event) => onChange(event.target.checked)} />
      <span className="toggle__track" aria-hidden />
      <span>
        {label}
        {hint && <span className="field__hint" style={{ display: 'block' }}>{hint}</span>}
      </span>
    </label>
  );
}

export function Notice({ tone = 'info', children }: { tone?: 'info' | 'error' | 'ok'; children: ReactNode }) {
  return <div className="notice" data-tone={tone} role={tone === 'error' ? 'alert' : 'status'}>{children}</div>;
}

export const WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const;

/** Mon-Sun chips. Nothing selected is meaningful to the caller (usually "every day"), so say so in `hint`. */
export function WeekdayChips({ label, selected, onChange, hint }: {
  label: string; selected: string[]; onChange: (days: string[]) => void; hint?: string;
}) {
  return (
    <ChipGroup label={label} hint={hint} selected={selected}
      options={WEEKDAYS.map((day) => ({ value: day, label: day.slice(0, 3).replace(/^./, (c) => c.toUpperCase()) }))}
      onChange={(days) => onChange(WEEKDAYS.filter((day) => days.includes(day)))} />
  );
}
