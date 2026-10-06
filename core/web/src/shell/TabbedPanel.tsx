import { useState, type ReactNode } from 'react';
import type { ManifestCard } from '../api/types';
import { CardHost } from './CardHost';

/** Cards that share a slot and `group` become tabs of one calm panel (e.g. Energy | Climate | Suggestions). */
export function TabbedPanel({ title, icon, cards }: { title: string; icon: ReactNode; cards: ManifestCard[] }) {
  const [active, setActive] = useState(0);
  const current = cards[Math.min(active, cards.length - 1)]!;
  return (
    <section className="card" aria-label={title} style={{ ['--c' as string]: 'var(--amber)' }}>
      <header className="card__head">
        <div className="card__icon">{icon}</div>
        <div className="card__titles">
          <h2 className="card__title">{title}</h2>
          <p className="card__subtitle">{cards.map((card) => card.title).join(' · ')}</p>
        </div>
      </header>
      {cards.length > 1 && (
        <div className="seg" role="tablist" aria-label={`${title} sections`}>
          {cards.map((card, index) => (
            <button key={card.id} role="tab" aria-selected={index === active} onClick={() => setActive(index)}>{card.title}</button>
          ))}
        </div>
      )}
      <div className="card__body" role="tabpanel">
        <CardHost key={current.id} card={current} embedded />
      </div>
    </section>
  );
}
