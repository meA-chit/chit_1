import { useClock } from '../lib/useClock';
import { DAY_PART_LABEL, dayPart, offsetFrom, setSecondClock, timeIn, useSecondClock, zoneCode, CLOCK_ZONES, type DayPart } from '../lib/secondClock';
import { Section, SelectField, Toggle } from '../ui/form';
import { MoonIcon, SunIcon, SunriseIcon, SunsetIcon } from '../ui/icons';

const ICON: Record<DayPart, () => JSX.Element> = { night: MoonIcon, morning: SunriseIcon, day: SunIcon, evening: SunsetIcon };

/**
 * A clock bubble: a sun or moon for the part of the day there, the time and the zone code. The home clock is the primary one
 * (accent colour and an underline); the second clock is the quieter one beside it.
 */
function ClockBubble({ zone, now, home, primary, flag }: { zone: string; now: Date; home: string; primary?: boolean; flag?: string }) {
  const { hour, text } = timeIn(now, zone);
  const part = dayPart(hour);
  const Icon = ICON[part];
  const label = CLOCK_ZONES.find((item) => item.zone === zone)?.label ?? zone;
  const away = primary ? 'your time here' : `${offsetFrom(now, zone, home)} from here`;
  return (
    <div className="clock2 bubble" data-part={part} data-primary={primary || undefined} title={`${label}: ${DAY_PART_LABEL[part].toLowerCase()}, ${away}${flag ? `, ${flag}` : ''}`}>
      <span className="clock2__icon"><Icon /></span>
      <span className="clock2__time" aria-label={`${text} in ${label}, ${DAY_PART_LABEL[part].toLowerCase()}`}>{text}</span>
      <span className="clock2__code">{zoneCode(zone)}</span>
      {flag && <span className="clock2__flag">{flag}</span>}
    </div>
  );
}

/** The home clock, always shown: the more relevant of the two, so it is highlighted. `now` ticks in the shell. */
export function HomeClock({ now, screenSafe }: { now: Date; screenSafe?: boolean }) {
  const home = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return <ClockBubble zone={home} now={now} home={home} primary flag={screenSafe ? 'screen-safe' : undefined} />;
}

/** The optional second clock, for another place. Nothing when off. */
export function SecondClockView({ homeZone }: { homeZone?: string }) {
  const { enabled, zone } = useSecondClock();
  const now = useClock(15_000);
  if (!enabled) return null;
  return <ClockBubble zone={zone} now={now} home={homeZone ?? Intl.DateTimeFormat().resolvedOptions().timeZone} />;
}

/** Settings > Visibility. Per device, like Appearance: applies at once and is not part of the household's saved data. */
export function SecondClockSettings() {
  const { enabled, zone } = useSecondClock();
  const known = CLOCK_ZONES.some((item) => item.zone === zone);
  const options: [string, string][] = [...(known ? [] : [[zone, zone] as [string, string]]), ...CLOCK_ZONES.map((item): [string, string] => [item.zone, `${item.label} · ${item.code}`])];
  return (
    <Section id="section-second-clock" title="Second clock"
      actions={<span className="badge" data-state="available" title="Applies at once and is remembered on this device">Saved instantly</span>}>
      <div className="stack">
        <Toggle label="Show a second clock in the top bar" checked={enabled} onChange={(checked) => setSecondClock({ enabled: checked })}
          hint="Stay in touch with family or home abroad. Off unless you turn it on." />
        {enabled && (
          <SelectField label="Time zone" value={zone} options={options} onChange={(value) => setSecondClock({ zone: value })}
            hint="Shows the time there, the zone code, and a sun or moon for the part of the day." />
        )}
      </div>
    </Section>
  );
}
