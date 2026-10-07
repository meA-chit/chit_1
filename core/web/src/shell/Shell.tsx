import { NavLink, Route, Routes, useParams } from 'react-router-dom';
import type { ShellConfig } from '../api/types';
import { hhmm } from '../lib/time';
import { useClock } from '../lib/useClock';
import { getViewComponent } from '../registry';
import { HouseholdMark, PersonAvatar } from '../ui/Avatar';
import { Suspense } from 'react';
import { Empty, Skeleton } from '../ui/CardFrame';
import { BellIcon, GridIcon, MODULE_ICONS, PlusIcon, SettingsIcon } from '../ui/icons';
import { CardHost } from './CardHost';
import { Dashboard } from './Dashboard';
import { useViewer } from './viewer';

function ViewHost({ module, id }: { module: string; id: string }) {
  const Component = getViewComponent(module, id);
  return Component ? (
    <Suspense fallback={<Skeleton lines={5} />}><Component /></Suspense>
  ) : (
    <Empty title="View not installed">The manifest lists <span className="mono">{module}/{id}</span> but this build has no renderer.</Empty>
  );
}

function ModulePage({ shell }: { shell: ShellConfig }) {
  const { id } = useParams();
  const module = shell.modules.find((item) => item.id === id);
  return (
    <section className="card hero">
      <div className="eyebrow">Module</div>
      <h2>{module?.title ?? 'Not found'}</h2>
      <p>{module ? 'Its cards appear on Home. A dedicated page for this module has not been built yet.' : 'That module is not enabled for this household.'}</p>
    </section>
  );
}

function Rail({ shell }: { shell: ShellConfig }) {
  const { memberId, setViewer } = useViewer();
  const canEditHousehold = shell.views.some((view) => view.id === 'household'); // adult-only module
  return (
    <nav className="rail" aria-label="Household members">
      <div className="rail__logo" aria-hidden>C</div>
      {shell.household && (
        <>
          <button className="who" aria-pressed={!shell.member} onClick={() => setViewer(null)} aria-label="Whole household">
            <HouseholdMark adults={shell.members.filter((m) => m.role === 'adult').length} kids={shell.members.filter((m) => m.role === 'child').length} size={44} selected={!shell.member} />
            <span className="who__name">Everyone</span>
          </button>
          <div className="rail__sep" />
          {shell.members.map((person) => (
            <button key={person.id} className="who" aria-pressed={memberId === person.id} onClick={() => setViewer(person.id)} aria-label={`View as ${person.name}`}>
              <PersonAvatar kind={person.avatar} color={person.color} size={44} selected={memberId === person.id} />
              <span className="who__name">{person.name.split(' ')[0]}</span>
            </button>
          ))}
          {canEditHousehold && <NavLink to="/household?new=1" className="iconbtn rail__hide-mobile" aria-label="Add a household" title="New household"><PlusIcon /></NavLink>}
        </>
      )}
      <div className="rail__spacer" />
      {(canEditHousehold || !shell.household) && <NavLink to="/household" className="iconbtn" aria-label="Household settings" title="Household settings"><SettingsIcon /></NavLink>}
    </nav>
  );
}

export function Shell({ shell }: { shell: ShellConfig }) {
  const now = useClock();
  const hour = now.getHours();
  const greeting = hour < 5 ? 'Late night' : hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const who = shell.member?.name ?? shell.household?.name ?? 'home';
  const modules = shell.modules.filter((module) => module.id !== 'household');
  const topbarCards = shell.cards.filter((card) => card.slot === 'topbar');
  const routedViews = shell.views.filter((view) => view.path);

  return (
    <div className="shell">
      {shell.interactive && <Rail shell={shell} />}
      <main className="main">
        <header className="topbar">
          <div className="hello">
            <div className="eyebrow">{now.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}</div>
            <h1>{greeting}, <em>{who}</em></h1>
          </div>
          {shell.interactive && shell.household && (
            <nav className="modnav" aria-label="Modules">
              <NavLink to="/" end><GridIcon />Home</NavLink>
              {modules.map((module) => {
                const Icon = MODULE_ICONS[module.id] ?? GridIcon;
                const page = routedViews.find((view) => view.module === module.id)?.path;   // a module with its own page links straight to it
                return <NavLink key={module.id} to={page ?? `/m/${module.id}`}><Icon />{module.short_title}</NavLink>;
              })}
            </nav>
          )}
          <div className="topbar__right">
            {topbarCards.map((card) => <CardHost key={card.id} card={card} />)}
            <div className="clock">
              <div className="clock__time" aria-label="Current time">{hhmm(now)}</div>
              {shell.screen_safe && <div className="eyebrow">screen-safe</div>}
            </div>
            {shell.interactive && <button className="iconbtn rail__hide-mobile" aria-label="Notifications"><BellIcon /></button>}
          </div>
        </header>
        <Routes>
          <Route path="/" element={<Dashboard shell={shell} />} />
          <Route path="/m/:id" element={<ModulePage shell={shell} />} />
          {routedViews.map((view) => (
            <Route key={view.id} path={`${view.path}/*`} element={<ViewHost module={view.module} id={view.id} />} />
          ))}
          <Route path="*" element={<Empty title="Not found">That page is not enabled for this household or surface.</Empty>} />
        </Routes>
      </main>
    </div>
  );
}
