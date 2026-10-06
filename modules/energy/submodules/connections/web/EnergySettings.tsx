import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError, Empty, Notice, Skeleton, TextField, type SettingsSectionProps } from '@chit/core';
import { ENERGY_KEYS } from '../../../shared/energy';

interface Status {
  tibber: { connected: boolean; hint?: string; homes?: number | null };
  solaredge: { connected: boolean; hint?: string; site_id?: string; site_name?: string | null; peak_kw?: number | null };
}

/** Energy connections in the household settings. Keys are checked with the provider before they are stored and are never shown again. */
export default function EnergySettings(_: SettingsSectionProps) {
  const queryClient = useQueryClient();
  const status = useQuery({ queryKey: ENERGY_KEYS.connections, queryFn: () => api<Status>('/api/energy/connections') });
  const [tibberToken, setTibberToken] = useState('');
  const [siteId, setSiteId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState<{ provider: string; message: string } | null>(null);

  const done = () => queryClient.invalidateQueries({ queryKey: ['energy'] });
  const failed = (provider: string) => (e: unknown) => setError({ provider, message: e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.' });
  const saveTibber = useMutation({
    mutationFn: () => api('/api/energy/connections/tibber', { method: 'PUT', body: JSON.stringify({ token: tibberToken }) }),
    onSuccess: () => { setTibberToken(''); setError(null); void done(); }, onError: failed('tibber'),
  });
  const saveSolar = useMutation({
    mutationFn: () => api('/api/energy/connections/solaredge', { method: 'PUT', body: JSON.stringify({ site_id: siteId, api_key: apiKey }) }),
    onSuccess: () => { setSiteId(''); setApiKey(''); setError(null); void done(); }, onError: failed('solaredge'),
  });
  const disconnect = useMutation({
    mutationFn: (provider: string) => api(`/api/energy/connections/${provider}`, { method: 'DELETE' }),
    onSuccess: () => { setError(null); void done(); },
  });

  if (status.isPending) return <Skeleton lines={3} />;
  if (status.isError) return <Empty title="Energy settings unavailable">The hub could not be reached.</Empty>;
  const { tibber, solaredge } = status.data;
  const shown = (provider: string) => (error?.provider === provider ? <Notice tone="error">{error.message}</Notice> : null);

  return (
    <div className="stack">
      <p className="field__hint" style={{ margin: 0 }}>
        Keys are checked with the provider, then stored on this hub only. They are never sent to the browser again, never exported and never part of the sample data.
        The unencrypted development database stores them as plain text, so use a key you can revoke.
      </p>

      <div className="subcard">
        <div className="subcard__head">
          <div>
            <div className="subcard__title">Tibber</div>
            <div className="eyebrow">Hourly prices and consumption</div>
          </div>
          {tibber.connected && <span className="badge" data-state="available">Connected · …{tibber.hint}</span>}
        </div>
        {tibber.connected ? (
          <div className="row">
            <span className="field__hint">{tibber.homes && tibber.homes > 1 ? `Using the first running home of ${tibber.homes}.` : 'Prices for your Tibber home are on the dashboard.'}</span>
            <button type="button" className="btn btn--danger" onClick={() => disconnect.mutate('tibber')}>Disconnect</button>
          </div>
        ) : (
          <>
            <TextField label="API token" type="password" value={tibberToken} onChange={setTibberToken} wide
              hint="Create a personal token at developer.tibber.com (sign in with your Tibber account). Consumption needs a Tibber Pulse or smart-meter connection." />
            <div className="row">
              <button type="button" className="btn" disabled={!tibberToken.trim() || saveTibber.isPending} onClick={() => saveTibber.mutate()}>
                {saveTibber.isPending ? 'Checking…' : 'Save and check'}
              </button>
            </div>
          </>
        )}
        {shown('tibber')}
      </div>

      <div className="subcard">
        <div className="subcard__head">
          <div>
            <div className="subcard__title">SolarEdge</div>
            <div className="eyebrow">Solar production</div>
          </div>
          {solaredge.connected && <span className="badge" data-state="available">Connected · {solaredge.site_name ?? `site ${solaredge.site_id}`}</span>}
        </div>
        {solaredge.connected ? (
          <div className="row">
            <span className="field__hint">Site {solaredge.site_id}{solaredge.peak_kw ? ` · ${solaredge.peak_kw} kWp` : ''} · key …{solaredge.hint}</span>
            <button type="button" className="btn btn--danger" onClick={() => disconnect.mutate('solaredge')}>Disconnect</button>
          </div>
        ) : (
          <>
            <div className="form-grid">
              <TextField label="Site id" value={siteId} onChange={setSiteId} placeholder="e.g. 1234567" hint="The number in your monitoring portal's web address." />
              <TextField label="API key" type="password" value={apiKey} onChange={setApiKey} hint="Monitoring portal: Admin, Site Access, API Access. Turn on API access and copy the key." />
            </div>
            <div className="row">
              <button type="button" className="btn" disabled={!siteId.trim() || !apiKey.trim() || saveSolar.isPending} onClick={() => saveSolar.mutate()}>
                {saveSolar.isPending ? 'Checking…' : 'Save and check'}
              </button>
            </div>
          </>
        )}
        {shown('solaredge')}
      </div>
    </div>
  );
}
