import { CardFrame, ThermoIcon, type CardProps } from '@chit/core';
import './climate.css';

/** DEMO values: no thermostat or sensor connector yet (Home Assistant is a later story). Never presented as measured. */
const ZONES = [
  { name: 'Living room', temp: '21.5°', note: 'Humidity 45%' },
  { name: 'Kitchen', temp: '22.0°', note: 'Humidity 48%' },
  { name: 'Bedroom', temp: '19.0°', note: 'Humidity 42%' },
  { name: "Kids' room", temp: '23.5°', note: 'Humidity 50% · warm', warm: true },
];

export default function ClimateNowCard({ card, embedded }: CardProps) {
  return (
    <CardFrame title={card.title} state="demo" embedded={embedded} icon={<ThermoIcon />} tone="#4df0ff" subtitle="Rooms"
      provenance={['illustrative values, no sensors connected']}>
      <div className="zones">
        {ZONES.map((zone) => (
          <div key={zone.name} className="zone">
            <span className="eyebrow">{zone.name}</span>
            <b style={zone.warm ? { color: 'var(--amber)' } : undefined}>{zone.temp}</b>
            <small>{zone.note}</small>
          </div>
        ))}
      </div>
    </CardFrame>
  );
}
