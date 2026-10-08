import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError, Empty, Notice, PersonAvatar, Skeleton, Toggle, useShell, type SettingsSectionProps } from '@chit/core';
import './phone.css';

type ShareKey = 'timetable' | 'stars' | 'reminders' | 'homework' | 'activities' | 'bag' | 'grades' | 'health';
interface Device { id: string; label: string | null; paired_at: string; last_seen_at: string | null }
interface ChildPhone {
  member_id: string; name: string; enabled: boolean; share: Record<ShareKey, boolean>; devices: Device[];
  pairing: { expires_at: string; attempts_left: number } | null;
}
interface PhoneSettings { gateway: boolean; phone_url: string | null; children: ChildPhone[] }
interface Pairing { member_id: string; url: string; code: string; link_code: string; expires_at: string; devicesBefore: number }

const SHARES: { key: ShareKey; label: string; hint: string }[] = [
  { key: 'timetable', label: 'Timetable and school day', hint: 'Lessons, rooms, breaks' },
  { key: 'reminders', label: 'Reminders', hint: 'Things to bring and remember' },
  { key: 'homework', label: 'Homework and tests', hint: 'The child can add their own and tick them off' },
  { key: 'activities', label: 'Activities and calendar events', hint: 'Training times and when to leave, from the child\'s own calendars' },
  { key: 'bag', label: 'Bag checklist', hint: 'What to pack for tomorrow; needs the timetable' },
  { key: 'stars', label: 'Stars, goals and chores', hint: 'The child can tick a chore; a parent still gives the star' },
  { key: 'grades', label: 'Grades', hint: 'Sensitive: off unless you choose' },
  { key: 'health', label: 'Medicine', hint: 'Strictest class: off unless you choose' },
];
const KEY = ['kids', 'phone'];
const spaced = (code: string) => `${code.slice(0, 3)} ${code.slice(3)}`;
const ago = (iso: string | null) => {
  if (!iso) return 'not yet';
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  return minutes < 2 ? 'just now' : minutes < 90 ? `${minutes} min ago` : minutes < 2880 ? `${Math.round(minutes / 60)} h ago` : `${Math.round(minutes / 1440)} days ago`;
};

/**
 * Household settings, "Kids' phones" (ADR-0012). The parent turns the phone view on per child, chooses what it may show,
 * and pairs a phone: the phone scans the QR code, then the 6 digits shown here are typed on the phone. The code is never
 * in the QR, so a photographed or shoulder-surfed QR alone does not pair anything.
 */
export default function KidPhoneSettings(_: SettingsSectionProps) {
  const queryClient = useQueryClient();
  const shell = useShell();
  const [pairing, setPairing] = useState<Pairing | null>(null);
  const [message, setMessage] = useState<{ tone: 'ok' | 'error'; text: string } | null>(null);
  const settings = useQuery({
    queryKey: KEY, queryFn: () => api<PhoneSettings>('/api/kids/phone/settings'),
    refetchInterval: (query) => (pairing || query.state.data?.children.some((c) => c.pairing) ? 2000 : false),
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: KEY });
  const failed = (e: unknown) => setMessage({ tone: 'error', text: e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was changed.' });

  const save = useMutation({
    mutationFn: ({ id, body }: { id: string; body: object }) => api(`/api/kids/phone/settings/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    onSuccess: () => { setMessage(null); void refresh(); }, onError: failed,
  });
  const start = useMutation({
    mutationFn: (member: ChildPhone) => api<{ url: string; code: string; link_code: string; expires_at: string }>('/api/kids/phone/pairings', { method: 'POST', body: JSON.stringify({ member_id: member.member_id }) })
      .then((p) => ({ ...p, member_id: member.member_id, devicesBefore: member.devices.length })),
    onSuccess: (p) => { setMessage(null); setPairing(p); void refresh(); }, onError: failed,
  });
  const cancel = useMutation({
    mutationFn: (member: string) => api(`/api/kids/phone/pairings/${member}`, { method: 'DELETE' }),
    onSuccess: () => { setPairing(null); void refresh(); },
  });
  const revoke = useMutation({
    mutationFn: (device: string) => api(`/api/kids/phone/devices/${device}`, { method: 'DELETE' }),
    onSuccess: () => void refresh(), onError: failed,
  });

  // When the server no longer has the open pairing, it was used, locked, cancelled or it expired: say which.
  const children = settings.data?.children;
  const mine = pairing && children?.find((c) => c.member_id === pairing.member_id);
  const sawOpen = useRef<string | null>(null);   // the cached settings predate the pairing: wait until the server has shown it open once
  useEffect(() => {
    if (!pairing || !mine) return;
    if (mine.pairing) { sawOpen.current = pairing.code; return; }
    if (sawOpen.current !== pairing.code) return;
    if (mine.devices.length > pairing.devicesBefore) setMessage({ tone: 'ok', text: `${mine.name}'s phone is paired.` });
    else setMessage({ tone: 'error', text: 'That pairing ended before a phone connected: it expired or too many wrong codes were typed. Start again.' });
    setPairing(null);
  }, [pairing, mine]);

  if (settings.isPending) return <Skeleton lines={3} />;
  if (settings.isError || !settings.data) return <Empty title="Kids' phones unavailable">The hub could not be reached.</Empty>;
  const kids = settings.data.children.filter((c) => shell.data?.members.some((m) => m.id === c.member_id));
  if (kids.length === 0) return <Empty title="No children yet">Add a child to the household first.</Empty>;

  return (
    <div className="stack">
      <p className="field__hint" style={{ margin: 0 }}>
        Give a child their own view on their phone: school day, stars, reminders and, if you choose, grades and medicine. The phone can only look at this
        child's data and tick off their chores. Switch it off to sign out every phone at once.
      </p>
      {!settings.data.gateway && (
        <Notice tone="info">
          Phones connect through a separate, opt-in gateway so the rest of Chit stays off the network. Start the hub with <span className="mono">CHIT_PHONE=1</span> (for example{' '}
          <span className="mono">CHIT_PHONE=1 npm run dev:all</span>) and reload this page. Details: apps/kid-app/README.md.
        </Notice>
      )}
      {message && <Notice tone={message.tone}>{message.text}</Notice>}

      {kids.map((kid) => {
        const person = shell.data?.members.find((m) => m.id === kid.member_id);
        const open = pairing?.member_id === kid.member_id ? pairing : null;
        return (
          <div className="subcard kp" key={kid.member_id}>
            <div className="subcard__head">
              <div className="kp__who">
                <PersonAvatar kind={person?.avatar} color={person?.color} size={36} />
                <div>
                  <div className="subcard__title">{kid.name}</div>
                  <div className="eyebrow">{kid.enabled ? `${kid.devices.length} phone${kid.devices.length === 1 ? '' : 's'} paired` : 'Phone view is off'}</div>
                </div>
              </div>
              <Toggle label="Phone view" checked={kid.enabled} disabled={save.isPending}
                onChange={(checked) => {
                  if (!checked && kid.devices.length > 0 && !window.confirm(`Switch off ${kid.name}'s phone view? Every paired phone is signed out.`)) return;
                  if (!checked) setPairing(null);
                  save.mutate({ id: kid.member_id, body: { enabled: checked } });
                }} />
            </div>

            {kid.enabled && (
              <>
                <div className="kp__shares" role="group" aria-label={`What ${kid.name}'s phone shows`}>
                  {SHARES.map((share) => (
                    <Toggle key={share.key} label={share.label} hint={share.hint} checked={kid.share[share.key]} disabled={save.isPending}
                      onChange={(checked) => save.mutate({ id: kid.member_id, body: { share: { [share.key]: checked } } })} />
                  ))}
                </div>

                {kid.devices.length > 0 && (
                  <ul className="kp__devices" aria-label="Paired phones">
                    {kid.devices.map((device) => (
                      <li key={device.id}>
                        <div><strong>{device.label ?? 'Phone'}</strong><span className="field__hint"> · paired {ago(device.paired_at)} · last seen {ago(device.last_seen_at)}</span></div>
                        <button type="button" className="btn btn--danger" disabled={revoke.isPending} onClick={() => revoke.mutate(device.id)}>Remove</button>
                      </li>
                    ))}
                  </ul>
                )}

                {open ? <PairPanel pairing={open} attemptsLeft={kid.pairing?.attempts_left} name={kid.name} onCancel={() => cancel.mutate(kid.member_id)} />
                  : (
                    <div className="row">
                      <button type="button" className="btn" disabled={!settings.data.gateway || start.isPending} onClick={() => start.mutate(kid)}>
                        {start.isPending ? 'Preparing…' : kid.devices.length ? 'Pair another phone' : 'Pair a phone'}
                      </button>
                      {kid.pairing && <span className="field__hint">A pairing is open on another screen.</span>}
                    </div>
                  )}
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

function PairPanel({ pairing, attemptsLeft, name, onCancel }: { pairing: Pairing; attemptsLeft?: number; name: string; onCancel: () => void }) {
  const [qr, setQr] = useState<string | null>(null);
  const [left, setLeft] = useState(() => Math.max(0, Math.round((new Date(pairing.expires_at).getTime() - Date.now()) / 1000)));
  const url = useRef(pairing.url);
  useEffect(() => {
    let live = true;
    void import('qrcode').then((qrcode) => qrcode.toDataURL(url.current, { margin: 2, width: 260, errorCorrectionLevel: 'M' })).then((data) => { if (live) setQr(data); });
    return () => { live = false; };
  }, []);
  useEffect(() => {
    const timer = setInterval(() => setLeft(Math.max(0, Math.round((new Date(pairing.expires_at).getTime() - Date.now()) / 1000))), 1000);
    return () => clearInterval(timer);
  }, [pairing.expires_at]);
  return (
    <div className="kp__pair" role="region" aria-label="Pair a phone">
      <ol className="kp__steps">
        <li>On {name}'s phone, open the <strong>Camera</strong> and point it at this QR code. Tap the link that appears.</li>
        <li>When asked, type this code on the phone:</li>
      </ol>
      <div className="kp__grid">
        {qr ? <img className="kp__qr" src={qr} width={200} height={200} alt={`QR code that opens Chit Kids on ${name}'s phone`} /> : <Skeleton lines={4} />}
        <div className="kp__codebox">
          <div className="kp__code" aria-label={`Code ${pairing.code.split('').join(' ')}`}>{spaced(pairing.code)}</div>
          <div className="field__hint">{left > 0 ? `Valid for ${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}` : 'Expired'}{attemptsLeft !== undefined && attemptsLeft < 5 ? ` · ${attemptsLeft} tries left` : ''}</div>
          <div className="field__hint">Works once. The code is not in the QR, so show or read it out only to {name}.</div>
          <div className="kp__link">
            <div className="field__hint">Already added to the Home Screen? Open that app instead and type this link code, then the 6 digits:</div>
            <div className="kp__linkcode" aria-label={`Link code ${pairing.link_code.split('').join(' ')}`}>{pairing.link_code}</div>
          </div>
        </div>
      </div>
      <div className="row"><button type="button" className="btn btn--ghost" onClick={onCancel}>Cancel pairing</button><span className="field__hint">Waiting for the phone…</span></div>
    </div>
  );
}
