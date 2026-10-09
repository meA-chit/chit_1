import type { CSSProperties } from 'react';
import { useAppearance } from '../theme/appearance';
import type { Mode, Palette } from '../theme/appearance';
import { Section } from '../ui/form';
import { MoonIcon, SunIcon, ThemeAutoIcon } from '../ui/icons';

const MODES: { value: Mode; label: string; note: string; Icon: () => JSX.Element }[] = [
  { value: 'dark', label: 'Dark', note: 'The default. Easy on the eyes in the evening and on a wall tablet.', Icon: MoonIcon },
  { value: 'light', label: 'Light', note: 'Bright rooms and daytime.', Icon: SunIcon },
  { value: 'auto', label: 'Match device', note: 'Follows the light or dark setting of this device.', Icon: ThemeAutoIcon },
];

const PALETTES: { value: Palette; label: string; note: string; colors: string[] }[] = [
  { value: 'classic', label: 'Classic', note: 'One cyan accent.', colors: ['var(--cyan)', 'var(--violet)'] },
  { value: 'spectrum', label: 'Spectrum', note: 'Multi-colour: every module has its own colour.', colors: ['var(--cyan)', 'var(--lime)', 'var(--amber)', 'var(--magenta)', 'var(--violet)'] },
];

/**
 * Household settings > Appearance. The choice is remembered on this device (a wall tablet and a phone may differ)
 * and applies at once; it is not part of the household's saved data, so it does not use the Save button.
 */
export function AppearanceSettings({ eyebrow }: { eyebrow?: string }) {
  const { mode, palette, setMode, setPalette } = useAppearance();
  return (
    <Section id="section-appearance" eyebrow={eyebrow} title="Appearance"
      actions={<span className="badge" data-state="available" title="Applies at once and is remembered on this device">Saved instantly</span>}>
      <div className="stack">
        <fieldset className="field" data-wide>
          <legend className="field__label">Colour mode</legend>
          <div className="picks" role="group" aria-label="Colour mode">
            {MODES.map(({ value, label, note, Icon }) => (
              <button key={value} type="button" className="pick" aria-pressed={mode === value} title={note} style={{ '--c': 'var(--accent)' } as CSSProperties} onClick={() => setMode(value)}>
                <Icon />{label}
              </button>
            ))}
          </div>
          <span className="field__hint">{MODES.find((m) => m.value === mode)?.note}</span>
        </fieldset>

        <fieldset className="field" data-wide>
          <legend className="field__label">Palette</legend>
          <div className="picks" role="group" aria-label="Palette">
            {PALETTES.map(({ value, label, note, colors }) => (
              <button key={value} type="button" className="pick" aria-pressed={palette === value} title={note} style={{ '--c': 'var(--accent)' } as CSSProperties} onClick={() => setPalette(value)}>
                <span className="pick__dots" aria-hidden>{colors.map((color) => <i key={color} style={{ background: color }} />)}</span>{label}
              </button>
            ))}
          </div>
          <span className="field__hint">{PALETTES.find((p) => p.value === palette)?.note} Works with every colour mode.</span>
        </fieldset>
      </div>
    </Section>
  );
}
