import { useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, ApiError, CardFrame, Empty, Field, Notice, Skeleton, TextField } from '@chit/core';
import { fmtLpd, fmtM3, fmtPct, useWater, type WaterInterval, type WaterUse, type WaterView } from '../../../shared/energy';
import './water.css';

const todayIso = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };

interface Row { read_on: string; total?: string; garden?: string; note?: string }

/** One reading per line: `date total garden`, separated by spaces, tabs, semicolons or commas. Use a dot for decimals; `-` or nothing skips a meter. */
export function parsePaste(text: string): { rows: Row[]; bad: number[] } {
  const rows: Row[] = [], bad: number[] = [];
  text.split(/\r?\n/).forEach((line, index) => {
    if (!line.trim()) return;
    const [day, total, garden] = line.trim().split(/[;\t,]\s*|\s+/);
    const ok = (v?: string) => v === undefined || v === '' || v === '-' || /^\d+([.]\d+)?$/.test(v);
    if (!day || !/^\d{4}-\d{2}-\d{2}$/.test(day) || !ok(total) || !ok(garden) || (!total || total === '-') && (!garden || garden === '-')) { bad.push(index + 1); return; }
    rows.push({ read_on: day, total: total === '-' ? undefined : total, garden: garden === '-' ? undefined : garden });
  });
  return { rows, bad };
}

function useSave(onDone: () => void, onError: (message: string) => void) {
  const queryClient = useQueryClient();
  const apply = (view: WaterView) => { queryClient.setQueryData(['energy', 'water'], view); void queryClient.invalidateQueries({ queryKey: ['energy', 'water'] }); };
  const fail = (e: unknown) => onError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');
  return {
    save: useMutation({ mutationFn: (readings: Row[]) => api<WaterView>('/api/energy/water/readings', { method: 'POST', body: JSON.stringify({ readings }) }), onSuccess: (v) => { apply(v); onDone(); }, onError: fail }),
    remove: useMutation({ mutationFn: (day: string) => api<WaterView>(`/api/energy/water/readings/${day}`, { method: 'DELETE' }), onSuccess: (v) => { apply(v); onDone(); }, onError: fail }),
  };
}

/** `~` marks a figure that rests on a boundary between two readings or on a clipped period (see the legend). */
const Use = ({ use }: { use: WaterUse | null }) => (use ? <>{fmtM3(use.value)}{(use.estimated || use.partial) && <sup title={use.partial ? `Only ${use.from} to ${use.to} is covered by readings` : 'A boundary falls between two readings and is estimated'}>~</sup>}</> : <>–</>);

const shortDay = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });

/** Average litres per day for each period between two readings: the height is the rate, so a 10-day and a 40-day period compare fairly. */
function Chart({ items, basis }: { items: WaterInterval[]; basis: 'household' | 'total' }) {
  const shown = items.slice(-14);
  const peak = Math.max(1, ...shown.map((i) => i.total.litres_per_day));
  return (
    <div className="wt-chart" role="img" aria-label="Average water use per day between readings">
      {shown.map((i) => {
        const hh = i.household?.litres_per_day, garden = i.garden?.litres_per_day ?? 0, total = i.total.litres_per_day;
        return (
          <div key={i.to} className="wt-col" title={`${shortDay(i.from)} to ${shortDay(i.to)} (${i.days} days): ${fmtLpd(total)} on the total meter${hh !== undefined ? `, garden ${fmtLpd(garden)}, household ${fmtLpd(hh)}` : ''}`}>
            <div className="wt-bar" style={{ height: `${(Math.max(total, 0) / peak) * 100}%` }}>
              {basis === 'household' && hh !== undefined ? <><i data-kind="garden" style={{ flexGrow: Math.max(garden, 0.0001) }} /><i data-kind="home" style={{ flexGrow: Math.max(hh, 0.0001) }} /></> : <i data-kind="total" style={{ flexGrow: 1 }} />}
            </div>
            <span className="mono">{shortDay(i.to)}</span>
          </div>
        );
      })}
    </div>
  );
}

function Entry({ view, editing, onClear, onSaved }: { view: WaterView; editing: Row | null; onClear: () => void; onSaved: () => void }) {
  const [day, setDay] = useState(editing?.read_on ?? todayIso());
  const [total, setTotal] = useState(editing?.total ?? '');
  const [garden, setGarden] = useState(editing?.garden ?? '');
  const [note, setNote] = useState(editing?.note ?? '');
  const [pasted, setPasted] = useState('');
  const [many, setMany] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reset = () => { setTotal(''); setGarden(''); setNote(''); setPasted(''); setError(null); onClear(); };
  const saved = () => { reset(); onSaved(); };
  const { save } = useSave(saved, setError);
  const parsed = useMemo(() => parsePaste(pasted), [pasted]);
  const last = view.rows?.[0];
  const lastTotal = view.rows?.find((r) => r.total), lastGarden = view.rows?.find((r) => r.garden);

  return (
    <div className="wt-entry">
      <div className="wt-entry__head">
        <b>{editing ? `Edit the reading of ${editing.read_on}` : 'Add a reading'}</b>
        <button type="button" className="wt-link" onClick={() => { setMany((v) => !v); setError(null); }}>{many ? 'One reading' : 'Paste many'}</button>
      </div>
      {many ? (
        <>
          <Field label="Readings, one per line" hint="date, total meter, garden meter. Dots for decimals; a dash skips a meter. Example: 2025-01-01 812.345 40.1" wide>
            <textarea className="input wt-paste" rows={6} value={pasted} onChange={(e) => setPasted(e.target.value)} placeholder={'2025-01-01 812.345 40.100\n2025-02-01 830.120 44.000\n2025-03-01 845.900 -'} spellCheck={false} />
          </Field>
          {pasted.trim() && <p className="en-note">{parsed.rows.length} reading{parsed.rows.length === 1 ? '' : 's'} understood{parsed.bad.length > 0 && <>; <b>line{parsed.bad.length > 1 ? 's' : ''} {parsed.bad.join(', ')} can’t be read</b> and will block saving</>}.</p>}
          <div className="row"><button type="button" className="btn" disabled={!parsed.rows.length || parsed.bad.length > 0 || save.isPending} onClick={() => save.mutate(parsed.rows)}>Save {parsed.rows.length || ''} readings</button></div>
        </>
      ) : (
        <>
          <div className="wt-entry__grid">
            <TextField label="Date" type="date" value={day} onChange={setDay} />
            <TextField label="Total meter (m³)" value={total} onChange={setTotal} placeholder={lastTotal?.total ? `last ${lastTotal.total.value}` : '812.345'} />
            <TextField label="Garden meter (m³)" value={garden} onChange={setGarden} placeholder={lastGarden?.garden ? `last ${lastGarden.garden.value}` : '40.100'} />
            <TextField label="Note (optional)" value={note} onChange={setNote} placeholder="e.g. after filling the pool" />
          </div>
          <div className="row">
            <button type="button" className="btn" disabled={save.isPending || (!total.trim() && !garden.trim())}
              onClick={() => save.mutate([{ read_on: day, total: total.trim().replace(',', '.') || undefined, garden: garden.trim().replace(',', '.') || undefined, note }])}>{editing ? 'Update reading' : 'Save reading'}</button>
            <button type="button" className="wt-link" onClick={() => { reset(); onSaved(); }}>Cancel</button>
            {last && !editing && <span className="field__hint">Last reading {last.read_on}. Read both meters the same day for a household figure.</span>}
          </div>
        </>
      )}
      {error && <Notice tone="error">{error}</Notice>}
    </div>
  );
}

function Readings({ view, onEdit }: { view: WaterView; onEdit: (row: Row) => void }) {
  const [all, setAll] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { remove } = useSave(() => setError(null), setError);
  const rows = view.rows ?? [];
  const shown = all ? rows : rows.slice(0, 8);
  const used = (r: NonNullable<typeof rows[number]['total']>) => r.since && <small>+{r.since.used.toFixed(3)} in {r.since.days} d</small>;
  return (
    <div className="wt-readings">
      <div className="wt-table" role="table" aria-label="Meter readings">
        <div className="wt-tr wt-tr--head" role="row"><span role="columnheader">Date</span><span role="columnheader">Total</span><span role="columnheader">Garden</span><span role="columnheader" /></div>
        {shown.map((r) => (
          <div key={r.read_on} className="wt-tr" role="row">
            <span role="cell" className="mono">{r.read_on}{r.note && <small>{r.note}</small>}</span>
            <span role="cell" className="mono">{r.total ? <>{r.total.value.toFixed(3)}{used(r.total)}</> : '–'}</span>
            <span role="cell" className="mono">{r.garden ? <>{r.garden.value.toFixed(3)}{used(r.garden)}</> : '–'}</span>
            <span role="cell" className="wt-acts">
              <button type="button" className="wt-link" onClick={() => onEdit({ read_on: r.read_on, total: r.total?.value.toString(), garden: r.garden?.value.toString(), note: r.note })}>Edit</button>
              <button type="button" className="wt-link wt-link--danger" onClick={() => { if (window.confirm(`Remove the readings of ${r.read_on}?`)) remove.mutate(r.read_on); }}>Remove</button>
            </span>
          </div>
        ))}
      </div>
      {rows.length > 8 && <button type="button" className="wt-link" onClick={() => setAll((v) => !v)}>{all ? 'Show recent only' : `Show all ${rows.length} readings`}</button>}
      {error && <Notice tone="error">{error}</Notice>}
    </div>
  );
}

/** Water by hand: total and garden meter readings; household use is total minus garden. A meter feed can replace the typing later. */
export default function WaterPanel() {
  const { data, isPending, isError, error } = useWater();
  const [editing, setEditing] = useState<Row | null>(null);
  const [adding, setAdding] = useState<boolean | null>(null);   // null: follow the data (open while there are no readings)
  const frame = { title: 'Water', tone: '#4df0ff' } as const;
  if (isPending) return <section className="card" aria-busy="true"><div className="card__body"><Skeleton lines={4} /></div></section>;
  if (isError || !data) {
    const old = error instanceof ApiError && error.status === 404;
    return <CardFrame {...frame} state="unavailable"><Empty title="Water unavailable">{old ? 'The hub is running without the water readings API. Restart the hub (npm run dev:all) and reload.' : 'The hub could not be reached.'}</Empty></CardFrame>;
  }
  if (data.reason === 'no_household') return <CardFrame {...frame} state="unconfigured"><Empty title="Set up a household first">Meter readings belong to a household.</Empty></CardFrame>;

  const manual = data.state === 'manual';
  const open = editing !== null || (adding ?? !manual);
  const years = data.years ?? [];
  const thisYear = years[years.length - 1];
  const iv = data.intervals, trend = iv?.trend ?? null;
  const readingDays = data.rows?.length ?? 0;
  const label = trend?.key === 'household' ? 'household' : 'total meter';
  const change = (ratio: number | null) => (ratio === null ? '–' : fmtPct(ratio) || '±0%');

  return (
    <CardFrame {...frame} icon={<svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 3s6 6.4 6 11a6 6 0 01-12 0c0-4.6 6-11 6-11z" /></svg>}
      state={data.state} subtitle="Meter readings by hand · household = total − garden"
      action={<button type="button" className="btn wt-add" aria-expanded={open} onClick={() => { setEditing(null); setAdding(!open); }}>{open ? 'Close' : '+ Add reading'}</button>}
      provenance={data.last ? [`entered by hand · ${readingDays} reading day${readingDays === 1 ? '' : 's'}, ${data.first} to ${data.last}`] : ['no readings yet']}>
      <div id="water" className="wt">
        {open && <Entry key={editing?.read_on ?? 'new'} view={data} editing={editing} onClear={() => setEditing(null)} onSaved={() => setAdding(false)} />}
        {manual ? (
          <>
            {trend ? (
              <div className="wt-stats">
                <div className="wt-stat"><small>Latest period · {shortDay(trend.from)} to {shortDay(trend.to)}</small><b className="mono">{fmtLpd(trend.litres_per_day)}</b><span>{label}, average per day</span></div>
                <div className="wt-stat"><small>Against the period before</small><b className="mono" data-dir={trend.vs_previous !== null && trend.vs_previous > 0.05 ? 'up' : trend.vs_previous !== null && trend.vs_previous < -0.05 ? 'down' : undefined}>{change(trend.vs_previous)}</b><span>was {fmtLpd(trend.previous)}</span></div>
                <div className="wt-stat"><small>Against your average</small><b className="mono" data-dir={trend.vs_baseline !== null && trend.vs_baseline > 0.05 ? 'up' : trend.vs_baseline !== null && trend.vs_baseline < -0.05 ? 'down' : undefined}>{change(trend.vs_baseline)}</b><span>average of earlier periods {fmtLpd(trend.baseline)}</span></div>
                {thisYear && (thisYear.household ?? thisYear.total) && <div className="wt-stat"><small>Year {thisYear.label} so far</small><b className="mono"><Use use={thisYear.household ?? thisYear.total} /></b><span>{thisYear.household ? 'household' : 'total meter'}{thisYear.garden ? <> · garden <Use use={thisYear.garden} /></> : ''}</span></div>}
              </div>
            ) : (
              <Notice tone="info">{iv && iv.items.length === 1 ? 'One period between two readings so far.' : 'One reading so far.'} The first trend appears with your next reading: it compares the average litres per day between readings.</Notice>
            )}
            {iv && iv.items.length > 0 && (
              <>
                <Chart items={iv.items} basis={iv.basis} />
                <div className="en-legend">
                  <span>each bar: average litres per day between two readings (hover for the dates)</span>
                  {iv.basis === 'household' ? <><span><i data-kind="home" /> household</span><span><i data-kind="garden" /> garden</span></> : <span><i data-kind="total" /> total meter (no garden readings on the same days yet)</span>}
                </div>
              </>
            )}
            {data.warnings?.map((w) => <Notice key={w} tone="error">{w}</Notice>)}
            <Readings view={data} onEdit={(row) => { setEditing(row); setAdding(true); }} />
          </>
        ) : (
          <Empty title="No readings yet">Use <b>Add reading</b> for the number on your total water meter and on the garden meter, or paste a whole history at once. The first trend needs three readings.</Empty>
        )}
      </div>
    </CardFrame>
  );
}
