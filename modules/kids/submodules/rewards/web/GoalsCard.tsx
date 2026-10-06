import { CardFrame, Empty, PersonAvatar, Skeleton, StarIcon, useViewer, useShell, type CardProps } from '@chit/core';
import { useStars } from '../../../shared/kids';
import '../../../shared/kids.css';

/** Dashboard card: each child's star total and the goal they are closest to. A child's own view shows only their row. */
export default function GoalsCard({ card, embedded }: CardProps) {
  const { data, isPending, isError } = useStars();
  const { memberId } = useViewer();
  const shell = useShell();
  const frame = { title: card.title, icon: <StarIcon />, tone: '#8dffb0', embedded } as const;
  if (isPending) return <CardFrame {...frame} state="unconfigured"><Skeleton lines={3} /></CardFrame>;
  if (isError || !data) return <CardFrame {...frame} state="unavailable"><Empty title="Goals unavailable">The hub could not be reached.</Empty></CardFrame>;
  const viewer = shell.data?.members.find((m) => m.id === memberId);
  const kids = data.children.filter((child) => !viewer || viewer.role !== 'child' || child.member_id === viewer.id);
  if (kids.length === 0) return <CardFrame {...frame} state="unconfigured"><Empty title="No children yet">Add a child in the household settings.</Empty></CardFrame>;

  return (
    <CardFrame {...frame} state="manual" subtitle="Stars and goals" provenance={['stars granted by a parent in Kids']}>
      <div className="kd-card-kids">
        {kids.map((child) => {
          const next = child.goals.filter((g) => g.status === 'active').sort((a, b) => (b.pct - a.pct))[0];
          return (
            <div key={child.member_id} className="stack" style={{ gap: 8 }}>
              <div className="row" style={{ alignItems: 'center' }}>
                <PersonAvatar kind={child.avatar} color={child.color} size={34} />
                <b style={{ flex: 1 }}>{child.name.split(' ')[0]}</b>
                <span className="mono"><span className="kd-star"><StarIcon /></span> {child.stars_total}</span>
              </div>
              {next ? (
                <>
                  <div className="kd-bar" role="progressbar" aria-valuenow={next.pct} aria-valuemin={0} aria-valuemax={100} aria-label={next.title}><i style={{ width: `${next.pct}%` }} /></div>
                  <div className="kd-goal__foot"><span>{next.title}</span><span>{next.reached ? 'Reached, waiting for a parent' : `${next.have} / ${next.cost}`}</span></div>
                </>
              ) : <div className="field__hint">No goal set</div>}
            </div>
          );
        })}
      </div>
    </CardFrame>
  );
}
