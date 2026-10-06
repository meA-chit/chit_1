import { Suspense } from 'react';
import type { ManifestCard } from '../api/types';
import { getCardComponent } from '../registry';
import { CardFrame, Empty, Skeleton } from '../ui/CardFrame';

/** Renders a registered card with a loading shell and a clear message when the build has no renderer. */
export function CardHost({ card, embedded }: { card: ManifestCard; embedded?: boolean }) {
  const Component = getCardComponent(card.module, card.id);
  if (!Component) {
    return (
      <CardFrame title={card.title} state="unavailable" embedded={embedded}>
        <Empty title="Card not installed">
          The manifest lists <span className="mono">{card.module}/{card.id}</span> but this build has no renderer.
        </Empty>
      </CardFrame>
    );
  }
  return (
    <Suspense fallback={<CardFrame title={card.title} state="unavailable" embedded={embedded}><Skeleton /></CardFrame>}>
      <Component card={card} embedded={embedded} />
    </Suspense>
  );
}
