import { Suspense, useEffect } from 'react';
import { Route, Routes } from 'react-router-dom';
import { ApiError } from '../api/client';
import { useSurface } from '../lib/useSurface';
import { initAppearance } from '../theme/appearance';
import { Shell } from './Shell';
import { useShell } from './useShell';
import { useViewer } from './viewer';

initAppearance();

export function App() {
  const surface = useSurface();
  const { memberId, setViewer } = useViewer();
  useEffect(() => {
    document.documentElement.dataset.surface = surface;
  }, [surface]);

  const shell = useShell();
  // A remembered "view as" member that no longer exists must not lock the app out.
  useEffect(() => {
    if (memberId && shell.error instanceof ApiError && shell.error.status === 400) setViewer(null);
  }, [memberId, shell.error, setViewer]);

  return (
    <>
      <div className="backdrop" aria-hidden />
      {shell.isPending ? (
        <div className="boot" role="status">
          <div>
            <div className="boot__ring" />
            <div className="eyebrow">Initialising hub</div>
          </div>
        </div>
      ) : shell.isError ? (
        <div className="boot" role="alert">
          <div>
            <div className="badge" data-state="unavailable" style={{ marginBottom: 16 }}>Hub unreachable</div>
            <h1 style={{ margin: 0 }}>Can't reach your Chit hub</h1>
            <p>Chit shows nothing rather than guess. Check that the hub is running on this network, then retry.</p>
            <button className="btn" style={{ marginTop: 18 }} onClick={() => shell.refetch()}>Retry</button>
          </div>
        </div>
      ) : (
        <Suspense fallback={<div className="boot"><div className="boot__ring" /></div>}>
          <Routes>
            <Route path="*" element={<Shell shell={shell.data} />} />
          </Routes>
        </Suspense>
      )}
    </>
  );
}
