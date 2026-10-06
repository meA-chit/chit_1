import { Skeleton } from '@chit/core';

/** Placeholder while a card loads: no data-state badge yet, so a card never flashes "Not set up" before it knows. */
export function Loading({ embedded }: { embedded?: boolean }) {
  return embedded ? <Skeleton lines={4} /> : <section className="card" aria-busy="true"><div className="card__body"><Skeleton lines={4} /></div></section>;
}
