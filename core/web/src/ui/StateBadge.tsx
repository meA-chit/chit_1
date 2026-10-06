import type { DataState } from '../api/types';

const LABEL: Record<DataState, string> = {
  available: 'Live',
  stale: 'Stale',
  partial: 'Partial',
  unavailable: 'Unavailable',
  unconfigured: 'Not set up',
  demo: 'Demo data',
  manual: 'Manual',
  forecast: 'Forecast',
};

/** Every card shows its data state. Forecast, manual and demo values must never read as measured. */
export function StateBadge({ state }: { state: DataState }) {
  return (
    <span className="badge" data-state={state} role="status">
      {LABEL[state]}
    </span>
  );
}
