import { motion } from 'motion/react';
import type { ManifestCard, ShellConfig, Slot } from '../api/types';
import { CardFrame, Empty } from '../ui/CardFrame';
import { HomeIcon } from '../ui/icons';
import { Link } from 'react-router-dom';
import { CardHost } from './CardHost';
import { TabbedPanel } from './TabbedPanel';

const COLUMNS: Slot[] = ['left', 'center', 'right'];
const titleCase = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);

function Column({ cards, index }: { cards: ManifestCard[]; index: number }) {
  const groups = new Map<string, ManifestCard[]>();
  const items: ({ kind: 'card'; card: ManifestCard } | { kind: 'group'; name: string; cards: ManifestCard[] })[] = [];
  for (const card of cards) {
    if (!card.group) { items.push({ kind: 'card', card }); continue; }
    let group = groups.get(card.group);
    if (!group) {
      group = [];
      groups.set(card.group, group);
      items.push({ kind: 'group', name: card.group, cards: group });
    }
    group.push(card);
  }
  return (
    <motion.div className="col" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.12 + index * 0.07, duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}>
      {items.map((item) => item.kind === 'card'
        ? <CardHost key={item.card.id} card={item.card} />
        : <TabbedPanel key={item.name} title={titleCase(item.name)} icon={<HomeIcon />} cards={item.cards} />)}
    </motion.div>
  );
}

/** Bands: the timeline (hero), then detail columns. Which cards exist is decided by /api/shell, never here. */
export function Dashboard({ shell }: { shell: ShellConfig }) {
  if (!shell.household) {
    return (
      <section className="card hero" aria-label="Welcome">
        <div className="eyebrow">Welcome</div>
        <h2>Let's set up your household</h2>
        <p>Add the people who live here, connect read-only calendars and choose what appears on your dashboard. Nothing is shown until you do.</p>
        <Link className="btn" to="/household">Start setup</Link>
      </section>
    );
  }
  const cards = shell.cards.filter((card) => card.slot !== 'topbar');
  if (cards.length === 0) {
    return (
      <CardFrame title="Nothing enabled" state="unconfigured">
        <Empty title="No cards are enabled for this view">
          Enable modules in household settings. Chit never shows what has not been switched on.
        </Empty>
      </CardFrame>
    );
  }
  const timeline = cards.filter((card) => card.slot === 'timeline');
  const columns = COLUMNS.map((slot) => cards.filter((card) => card.slot === slot)).filter((column) => column.length > 0);
  return (
    <div className="band">
      {timeline.map((card, index) => (
        <motion.div key={card.id} initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.07, duration: 0.5 }}>
          <CardHost card={card} />
        </motion.div>
      ))}
      {columns.length > 0 && (
        <div className="cols" data-n={columns.length} style={{ ['--n' as string]: columns.length }}>
          {columns.map((column, index) => <Column key={column[0]!.slot} cards={column} index={index} />)}
        </div>
      )}
    </div>
  );
}
