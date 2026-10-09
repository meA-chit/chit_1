import { useEffect, useState, type ReactNode } from 'react';
import { CardFrame, ClockIcon, Empty, PersonAvatar, Skeleton, StarIcon, SunIcon, useSearchParams, useShell, useViewer } from '@chit/core';
import { firstName, useStars } from '../../../shared/kids';
import GradesOverview, { GradesSettings } from '../../learning/web/GradesPanel';
import HomeworkPanel from '../../learning/web/HomeworkPanel';
import MedsWeek from '../../health/web/HealthPanel';
import { GoalList } from '../../rewards/web/GoalList';
import { StarsSettings, StarsSummary, TodayStars } from '../../rewards/web/StarsPanel';
import BagPanel from '../../school/web/BagPanel';
import SchoolPlan, { SchoolToday, SchoolWeek } from '../../school/web/SchoolPlan';
import KidPhoneSettings from './KidPhoneSettings';
import '../../../shared/kids.css';

/**
 * The Kids page. One way in: the left rail picks the module, then the child, then the topic (tab).
 * Looking and changing are the same tab: parents press Edit to change the timetable, chores or subjects where they see them.
 * A child viewing as themselves gets their own day, stars and homework, with no tabs and no Edit.
 */
const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'school', label: 'School', editable: true },
  { id: 'stars', label: 'Stars & chores', editable: true },
  { id: 'homework', label: 'Homework' },
  { id: 'grades', label: 'Grades', editable: true },
  { id: 'health', label: 'Health' },
  { id: 'phone', label: 'Phone & privacy' },
] as const;
type TabId = (typeof TABS)[number]['id'];

export default function KidsView() {
  const shell = useShell();
  const { memberId } = useViewer();
  const stars = useStars();
  const [params, setParams] = useSearchParams();
  const [picked, setPicked] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const viewer = shell.data?.members.find((m) => m.id === memberId);
  const adultView = !viewer || viewer.role === 'adult';
  const kids = (shell.data?.members ?? []).filter((m) => m.role === 'child' && (adultView || m.id === viewer?.id));
  const adults = (shell.data?.members ?? []).filter((m) => m.role === 'adult');
  const current = kids.find((k) => k.id === picked) ?? kids[0];
  const wanted = params.get('tab');
  const tab: TabId = adultView ? (TABS.find((t) => t.id === wanted)?.id ?? 'overview') : 'overview';
  const tabInfo = TABS.find((t) => t.id === tab)!;
  const canEdit = adultView && 'editable' in tabInfo;
  useEffect(() => { if (picked && !kids.some((k) => k.id === picked)) setPicked(null); }, [picked, kids]);
  useEffect(() => { setEditing(false); }, [tab, current?.id]);

  if (shell.isPending || stars.isPending) return <Skeleton lines={5} />;
  if (!current) return <Empty title="No children in this household">Add a child in the household settings to use Kids.</Empty>;
  const child = stars.data?.children.find((c) => c.member_id === current.id);
  const name = firstName(current);
  const go = (next: TabId) => setParams(next === 'overview' ? {} : { tab: next }, { replace: true });
  const banner = (text: string): ReactNode => editing && <div className="kd-banner" role="status">{text}</div>;

  return (
    <div className="kd">
      <header className="kd-head">
        <div className="kd-kids" role="group" aria-label="Child">
          {kids.length > 1 ? kids.map((kid) => (
            <button key={kid.id} type="button" aria-pressed={kid.id === current.id} onClick={() => setPicked(kid.id)}>
              <PersonAvatar kind={kid.avatar} color={kid.color} size={36} selected={kid.id === current.id} />{firstName(kid)}
            </button>
          )) : (
            <span className="kd-kids__one"><PersonAvatar kind={current.avatar} color={current.color} size={36} selected />{name}</span>
          )}
        </div>
        {canEdit && (
          <button type="button" className={`btn${editing ? ' btn--primary' : ''}`} aria-pressed={editing} onClick={() => setEditing(!editing)}>
            {editing ? 'Done editing' : 'Edit'}
          </button>
        )}
      </header>

      {adultView && (
        <nav className="kd-nav" aria-label={`${name}'s sections`}>
          {TABS.map((item) => (
            <button key={item.id} type="button" aria-current={item.id === tab ? 'page' : undefined} onClick={() => go(item.id)}>{item.label}</button>
          ))}
        </nav>
      )}

      {tab === 'overview' && (
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
          {!adultView && <div className="kd-board__homework"><HomeworkPanel memberId={current.id} name={name} /></div>}
        </div>
      )}

      {tab === 'school' && (
        <div className="kd">
          {banner(`Editing ${name}'s school. Changes save as you go and show on ${name}'s phone straight away.`)}
          {editing ? (
            <div className="kd">
              <SchoolPlan memberId={current.id} name={name} adult />
              <p className="field__hint" style={{ margin: 0 }}>Subject types, codes and merging duplicates are under Grades, then Edit.</p>
            </div>
          ) : (
            <CardFrame title="School week" state="manual" icon={<ClockIcon />} tone="#8b7bff" subtitle={`${name}'s timetable`}>
              <SchoolWeek memberId={current.id} />
            </CardFrame>
          )}
        </div>
      )}

      {tab === 'stars' && child && (
        <div className="kd">
          {banner(`Editing ${name}'s star chores and goals.`)}
          {editing ? <StarsSettings child={child} /> : (
            <div className="kd-board">
              <div className="kd-board__today"><CardFrame title="Chores today" state="manual" icon={<SunIcon />} tone="#ffc857" subtitle="Morning and after school">
                <div className="kd-day">
                  <section><h3 className="kd-h"><SunIcon />Morning routine</h3><TodayStars child={child} adult part="morning" empty="No morning routine today." /></section>
                  <section><h3 className="kd-h"><StarIcon />After school</h3><TodayStars child={child} adult part="after" empty="No chores after school." /></section>
                </div>
              </CardFrame></div>
              <div className="kd-board__stars"><CardFrame title="Stars & goals" state="manual" icon={<StarIcon />} tone="#8dffb0" subtitle="This week">
                <div className="stack"><StarsSummary child={child} /><GoalList goals={child.goals} memberId={current.id} name={name} adult /></div>
              </CardFrame></div>
            </div>
          )}
        </div>
      )}
      {tab === 'stars' && !child && <Skeleton lines={4} />}

      {tab === 'homework' && (
        <div className="kd-cols">
          <HomeworkPanel memberId={current.id} name={name} />
          <BagPanel memberId={current.id} name={name} />
        </div>
      )}

      {tab === 'grades' && (
        <div className="kd">
          {banner(`Editing ${name}'s subjects. Subjects come from the school plan; here you set type, code and merge duplicates.`)}
          {editing ? <GradesSettings memberId={current.id} /> : <GradesOverview memberId={current.id} name={name} />}
        </div>
      )}

      {tab === 'health' && <MedsWeek memberId={current.id} name={name} adults={adults} />}

      {tab === 'phone' && (
        <div className="kd" style={{ maxWidth: 860 }}>
          <KidPhoneSettings memberId={current.id} />
        </div>
      )}
    </div>
  );
}
