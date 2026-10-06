import { useEffect, useState } from 'react';
import { CardFrame, Empty, PersonAvatar, Skeleton, StarIcon, useShell, useViewer } from '@chit/core';
import { firstName, useStars } from '../../../shared/kids';
import GradesPanel from '../../learning/web/GradesPanel';
import HealthPanel, { MedsToday } from '../../health/web/HealthPanel';
import { GoalList } from '../../rewards/web/GoalList';
import StarsPanel, { StarsSummary, TodayStars } from '../../rewards/web/StarsPanel';
import SchoolPlan from '../../school/web/SchoolPlan';
import '../../../shared/kids.css';

const TABS = ['Today', 'Stars', 'Grades', 'Health'] as const;
type Tab = (typeof TABS)[number];

/** The Kids page. Parents manage each child (Today, Stars, Grades, Health); a child viewing as themselves sees only their own stars, goals and school day. */
export default function KidsView() {
  const shell = useShell();
  const { memberId } = useViewer();
  const stars = useStars();
  const [picked, setPicked] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('Today');
  const viewer = shell.data?.members.find((m) => m.id === memberId);
  const adultView = !viewer || viewer.role === 'adult';
  const kids = (shell.data?.members ?? []).filter((m) => m.role === 'child' && (adultView || m.id === viewer?.id));
  const adults = (shell.data?.members ?? []).filter((m) => m.role === 'adult');
  const current = kids.find((k) => k.id === picked) ?? kids[0];
  useEffect(() => { if (!adultView) setTab('Today'); }, [adultView]);

  if (shell.isPending || stars.isPending) return <Skeleton lines={5} />;
  if (!current) return <Empty title="No children in this household">Add a child in the household settings to use Kids.</Empty>;
  const child = stars.data?.children.find((c) => c.member_id === current.id);
  const name = firstName(current);

  return (
    <div className="kd">
      <header className="kd-kids">
        {kids.map((kid) => (
          <button key={kid.id} type="button" aria-pressed={kid.id === current.id} onClick={() => setPicked(kid.id)}>
            <PersonAvatar kind={kid.avatar} color={kid.color} size={36} selected={kid.id === current.id} />{firstName(kid)}
          </button>
        ))}
        {adultView && (
          <div className="seg" role="tablist" aria-label="Kids sections" style={{ margin: '0 0 0 auto' }}>
            {TABS.map((t) => <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>{t}</button>)}
          </div>
        )}
      </header>

      {adultView && tab === 'Stars' && child && <StarsPanel child={child} />}
      {adultView && tab === 'Grades' && <GradesPanel memberId={current.id} name={name} />}
      {adultView && tab === 'Health' && <HealthPanel memberId={current.id} name={name} adults={adults} />}
      {(tab === 'Today' || !adultView) && (
        <div className="kd-cols">
          <SchoolPlan memberId={current.id} name={name} adult={adultView} />
          <div className="kd">
            {child && <CardFrame title={adultView ? 'Stars' : `Hi ${name}`} state="manual" icon={<StarIcon />} tone="#8dffb0" subtitle="This week"><StarsSummary child={child} /></CardFrame>}
            {child && <CardFrame title="Chores today" state="manual" tone="#8dffb0"><TodayStars child={child} adult={adultView} /></CardFrame>}
            {child && <CardFrame title="My goals" state="manual" tone="#8dffb0"><GoalList goals={child.goals} memberId={current.id} name={name} adult={false} /></CardFrame>}
            {adultView && <CardFrame title="Medication today" state="manual" tone="#4df0ff" subtitle="Parents only"><MedsToday memberId={current.id} /></CardFrame>}
          </div>
        </div>
      )}
    </div>
  );
}
