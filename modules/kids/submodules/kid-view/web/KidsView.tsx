import { useEffect, useState } from 'react';
import { CardFrame, ClockIcon, Empty, PersonAvatar, Skeleton, StarIcon, SunIcon, useShell, useViewer } from '@chit/core';
import { firstName, useStars } from '../../../shared/kids';
import { GradesSettings } from '../../learning/web/GradesPanel';
import GradesOverview from '../../learning/web/GradesPanel';
import HomeworkPanel from '../../learning/web/HomeworkPanel';
import MedsWeek from '../../health/web/HealthPanel';
import { GoalList } from '../../rewards/web/GoalList';
import { StarsSummary, StarsSettings, TodayStars } from '../../rewards/web/StarsPanel';
import BagPanel from '../../school/web/BagPanel';
import SchoolPlan, { SchoolToday, SchoolWeek } from '../../school/web/SchoolPlan';
import '../../../shared/kids.css';

/**
 * The Kids page: one board per child, no sub-navigation.
 *   Row 1: today (morning routine, school timetable, after school) 2/3 | stars and goals 1/3
 *   Row 2: week and medication 1/3 | grades 2/3
 *   Bottom: management (school day, star chores, subjects) for parents.
 * A child viewing as themselves sees row 1 only: their own stars, goals and school day.
 */
export default function KidsView() {
  const shell = useShell();
  const { memberId } = useViewer();
  const stars = useStars();
  const [picked, setPicked] = useState<string | null>(null);
  const viewer = shell.data?.members.find((m) => m.id === memberId);
  const adultView = !viewer || viewer.role === 'adult';
  const kids = (shell.data?.members ?? []).filter((m) => m.role === 'child' && (adultView || m.id === viewer?.id));
  const adults = (shell.data?.members ?? []).filter((m) => m.role === 'adult');
  const current = kids.find((k) => k.id === picked) ?? kids[0];
  useEffect(() => { if (picked && !kids.some((k) => k.id === picked)) setPicked(null); }, [picked, kids]);

  if (shell.isPending || stars.isPending) return <Skeleton lines={5} />;
  if (!current) return <Empty title="No children in this household">Add a child in the household settings to use Kids.</Empty>;
  const child = stars.data?.children.find((c) => c.member_id === current.id);
  const name = firstName(current);

  return (
    <div className="kd">
      {kids.length > 1 && (
        <header className="kd-kids">
          {kids.map((kid) => (
            <button key={kid.id} type="button" aria-pressed={kid.id === current.id} onClick={() => setPicked(kid.id)}>
              <PersonAvatar kind={kid.avatar} color={kid.color} size={36} selected={kid.id === current.id} />{firstName(kid)}
            </button>
          ))}
        </header>
      )}

      <div className="kd-board">
        <div className="kd-board__today"><CardFrame title={adultView ? `${name}'s day` : `Hi ${name}`} state="manual" icon={<SunIcon />} tone="#ffc857" subtitle="Today">
          <div className="kd-day">
            <section><h3 className="kd-h"><SunIcon />Morning routine</h3>{child ? <TodayStars child={child} adult={adultView} part="morning" empty="No morning routine today." /> : <Skeleton lines={2} />}</section>
            <section><h3 className="kd-h"><ClockIcon />School week</h3><SchoolWeek memberId={current.id} /></section>
            <section>
              <h3 className="kd-h"><StarIcon />After school</h3>
              <div className="stack" style={{ gap: 10 }}>
                <SchoolToday memberId={current.id} after />
                {child && <TodayStars child={child} adult={adultView} part="after" empty="No chores after school." />}
              </div>
            </section>
          </div>
        </CardFrame></div>

        <div className="kd-board__stars"><CardFrame title="Stars & goals" state="manual" icon={<StarIcon />} tone="#8dffb0" subtitle="This week">
          {child ? (
            <div className="stack">
              <StarsSummary child={child} />
              <GoalList goals={child.goals} memberId={current.id} name={name} adult={adultView} />
            </div>
          ) : <Skeleton lines={4} />}
        </CardFrame></div>

        <div className="kd-board__homework"><HomeworkPanel memberId={current.id} name={name} /></div>

        {adultView && (
          <>
            <div className="kd-board__week"><MedsWeek memberId={current.id} name={name} adults={adults} /></div>
            <div className="kd-board__grades"><GradesOverview memberId={current.id} name={name} /></div>
          </>
        )}
      </div>

      {adultView && (
        <section className="kd-manage" aria-label="Manage">
          <div className="kd-manage__head"><div className="eyebrow">Manage</div><h2>{name}: school, stars and grades</h2></div>
          <div className="kd-manage__cols">
            <div className="kd"><SchoolPlan memberId={current.id} name={name} adult />{child && <StarsSettings child={child} />}</div>
            <div className="kd"><BagPanel memberId={current.id} name={name} /><GradesSettings memberId={current.id} /></div>
          </div>
        </section>
      )}
    </div>
  );
}
