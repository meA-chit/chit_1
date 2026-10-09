import { useAppearance } from '../theme/appearance';
import type { Mode } from '../theme/appearance';
import { MoonIcon, SunIcon, ThemeAutoIcon } from '../ui/icons';

const MODES: { mode: Mode; label: string; Icon: () => JSX.Element }[] = [
  { mode: 'light', label: 'Light theme', Icon: SunIcon },
  { mode: 'dark', label: 'Dark theme', Icon: MoonIcon },
  { mode: 'auto', label: 'Match this device', Icon: ThemeAutoIcon },
];

/** Three icon buttons: light, dark, match the device. The full choice (with the palette) is in the household settings. */
export function ThemeSwitch({ orientation = 'vertical' }: { orientation?: 'vertical' | 'horizontal' }) {
  const { mode, setMode } = useAppearance();
  return (
    <div className="themeswitch" data-orientation={orientation} role="group" aria-label="Theme">
      {MODES.map(({ mode: value, label, Icon }) => (
        <button key={value} type="button" aria-label={label} title={label} aria-pressed={mode === value} onClick={() => setMode(value)}><Icon /></button>
      ))}
    </div>
  );
}
