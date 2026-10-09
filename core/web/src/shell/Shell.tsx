import type { CSSProperties } from 'react';
import { Link, NavLink, Route, Routes, useParams } from 'react-router-dom';
import type { ShellConfig } from '../api/types';

import { useClock } from '../lib/useClock';
import { getViewComponent } from '../registry';
import { Suspense } from 'react';
import { Empty, Skeleton } from '../ui/CardFrame';
import { useNowPanel } from '../moments/useNowPanel';
import { ChitMark } from '../ui/ChitMark';
import { BellIcon, GridIcon, HomeIcon, MODULE_ICONS, SettingsIcon } from '../ui/icons';
import { CardHost } from './CardHost';
import { Dashboard } from './Dashboard';
import { HomeClock, SecondClockView } from './SecondClock';
import { ThemeSwitch } from './ThemeSwitch';
import { ViewerMenu } from './ViewerMenu';

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

/** Module colours, used by the Spectrum palette (classic keeps the single accent). */
const MODULE_COLOR: Record<string, string> = {
  home: 'var(--cyan)', planner: 'var(--lime)', kids: 'var(--amber)', energy: 'var(--violet)', devices: 'var(--magenta)', finance: 'var(--red)',
};

/** The one place to move between modules: a floating dock at the foot of the screen. Who you are viewing as, and the theme, live in the ribbon. */
function Dock({ shell }: { shell: ShellConfig }) {
  const canEditHousehold = shell.views.some((view) => view.id === 'household'); // adult-only module
  const modules = shell.modules.filter((module) => module.id !== 'household' && module.nav !== false);
  const routedViews = shell.views.filter((view) => view.path);
  const item = (key: string, to: string, label: string, Icon: () => JSX.Element, end?: boolean) => (
    <NavLink key={key} to={to} end={end} className="navitem" style={{ '--mod': MODULE_COLOR[key] ?? 'var(--accent)' } as CSSProperties}>
      <Icon /><span>{label}</span>
    </NavLink>
  );
  return (
    <nav className="dock" aria-label="Modules">
      {shell.household && (
        <>
          {item('home', '/', 'Home', HomeIcon, true)}
          {modules.map((module) => {
            const page = routedViews.find((view) => view.module === module.id)?.path;   // a module with its own page links straight to it
            return item(module.id, page ?? `/m/${module.id}`, module.short_title, MODULE_ICONS[module.id] ?? GridIcon);
          })}
        </>
      )}
      {(canEditHousehold || !shell.household) && <span className="dock__sep" aria-hidden />}
      {(canEditHousehold || !shell.household) && (
        <NavLink to="/household" className="navitem navitem--settings" aria-label="Household settings" title="Household settings" style={{ '--mod': 'var(--text-dim)' } as CSSProperties}>
          <SettingsIcon /><span>Settings</span>
        </NavLink>
      )}
    </nav>
  );
}

export function Shell({ shell }: { shell: ShellConfig }) {
  const now = useClock();
  const hour = now.getHours();
  const greeting = hour < 5 ? 'Late night' : hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const who = shell.member?.name ?? shell.household?.name ?? 'home';
  const topbarCards = shell.cards.filter((card) => card.slot === 'topbar');
  const routedViews = shell.views.filter((view) => view.path);
  const panel = useNowPanel(shell);

  return (
    <div className="shell">
      <header className="ribbon">
        <Link to="/" className="brand" aria-label="Chit beta, home">
          <ChitMark size={40} /><span className="brand__word">chit</span><span className="brand__beta" title="Chit is in beta: features change and data may be reset">Beta</span>
        </Link>
        <span className="ribbon__div" aria-hidden />
        <div className="hello">
          <h1>{greeting}, <em>{who}</em></h1>
        </div>
        <div className="ribbon__right">
          {topbarCards.map((card) => <CardHost key={card.id} card={card} />)}
          {shell.interactive && shell.household && <ViewerMenu shell={shell} />}
          {shell.interactive && !shell.household && <ThemeSwitch orientation="horizontal" />}
          <SecondClockView />
          <HomeClock now={now} screenSafe={shell.screen_safe} />
          {shell.interactive && (panel.available && !panel.wide ? (
            <button className="iconbtn bell" data-urgent={panel.urgent || undefined} aria-label={`Now, ${panel.count} items`} onClick={panel.toggle}>
              <BellIcon />{panel.count > 0 && <span className="bell__count">{panel.count}</span>}
            </button>
          ) : (
            !panel.available && <button className="iconbtn rail__hide-mobile" aria-label="Notifications"><BellIcon /></button>
          ))}
        </div>
      </header>
      <div className="shell__body">
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard shell={shell} />} />
          <Route path="/m/:id" element={<ModulePage shell={shell} />} />
          {routedViews.map((view) => (
            <Route key={view.id} path={`${view.path}/*`} element={<ViewHost module={view.module} id={view.id} />} />
          ))}
          <Route path="*" element={<Empty title="Not found">That page is not enabled for this household or surface.</Empty>} />
        </Routes>
      </main>
      {panel.node}
      </div>
      {shell.interactive && <Dock shell={shell} />}
    </div>
  );
}
