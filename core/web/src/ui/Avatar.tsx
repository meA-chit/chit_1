/**
 * Predefined avatar illustrations (never photos). Adults a1-a4, children k1-k4, plus `home` for the whole household.
 * Kept in core so every module draws a person the same way. `AVATARS` lists the choices per role for pickers.
 */
export type AvatarKind = 'a1' | 'a2' | 'a3' | 'a4' | 'k1' | 'k2' | 'k3' | 'k4' | 'home';

export const AVATARS: Record<'adult' | 'child', { kind: AvatarKind; label: string }[]> = {
  adult: [{ kind: 'a1', label: 'Man' }, { kind: 'a2', label: 'Woman' }, { kind: 'a3', label: 'Man, beard' }, { kind: 'a4', label: 'Woman, bun' }],
  child: [{ kind: 'k1', label: 'Boy' }, { kind: 'k2', label: 'Girl, pigtails' }, { kind: 'k3', label: 'Boy, cap' }, { kind: 'k4', label: 'Girl, glasses' }],
};

export const PERSON_COLORS = ['#b79cff', '#4df0ff', '#ff8fb8', '#ffc857', '#8dffb0', '#ff9d5c'];

const A11Y: Record<AvatarKind, string> = {
  a1: 'man, short hair', a2: 'woman, long hair', a3: 'man with a beard', a4: 'woman with a bun',
  k1: 'boy with messy hair', k2: 'girl with pigtails', k3: 'boy with a cap', k4: 'girl with a bob and glasses', home: 'whole household',
};

function Art({ kind }: { kind: AvatarKind }) {
  switch (kind) {
    case 'a1': return <><rect width="64" height="64" fill="#1f3a5f" /><path d="M6 66 C6 52 18 47 32 47 C46 47 58 52 58 66Z" fill="#3b82f6" /><rect x="27.5" y="38" width="9" height="11" rx="3" fill="#d39a74" /><circle cx="32" cy="29" r="12" fill="#e8b894" /><path d="M20 28 C19 16 28 13 33 13 C41 13 46 18 44 28 C42 23 38 21 32 21 C27 21 22 23 20 28Z" fill="#2a1d16" /><circle cx="27.5" cy="30" r="1.3" fill="#2a1d16" /><circle cx="36.5" cy="30" r="1.3" fill="#2a1d16" /><path d="M28.5 35 Q32 37.5 35.5 35" stroke="#8a4b2f" strokeWidth="1.4" fill="none" strokeLinecap="round" /></>;
    case 'a2': return <><rect width="64" height="64" fill="#4a2a63" /><path d="M17 36 C14 14 25 9 32 9 C40 9 51 14 47 36 L50 58 L14 58Z" fill="#6b3f2a" /><path d="M6 66 C6 52 18 47 32 47 C46 47 58 52 58 66Z" fill="#ec6aa8" /><rect x="27.5" y="38" width="9" height="11" rx="3" fill="#e2ad88" /><circle cx="32" cy="29" r="12" fill="#f1c9a8" /><path d="M20 28 C21 16 43 14 44 28 C40 22 26 21 20 28Z" fill="#6b3f2a" /><circle cx="27.5" cy="30" r="1.3" fill="#3a2418" /><circle cx="36.5" cy="30" r="1.3" fill="#3a2418" /><path d="M28.5 35 Q32 37.8 35.5 35" stroke="#b5503f" strokeWidth="1.5" fill="none" strokeLinecap="round" /></>;
    case 'a3': return <><rect width="64" height="64" fill="#143c38" /><path d="M6 66 C6 52 18 47 32 47 C46 47 58 52 58 66Z" fill="#2fbf8f" /><rect x="27.5" y="38" width="9" height="11" rx="3" fill="#9c6a47" /><circle cx="32" cy="29" r="12" fill="#b9805a" /><path d="M20 27 C19 15 28 12 33 12 C41 12 46 17 44 27 C42 21 38 19 32 19 C27 19 22 21 20 27Z" fill="#17110e" /><path d="M20.5 31 C20.5 44 27 47 32 47 C37 47 43.5 44 43.5 31 C41 37 37 38.5 32 38.5 C27 38.5 23 37 20.5 31Z" fill="#17110e" /><circle cx="27.5" cy="29.5" r="1.3" fill="#17110e" /><circle cx="36.5" cy="29.5" r="1.3" fill="#17110e" /><path d="M29 41.5 Q32 43 35 41.5" stroke="#b9805a" strokeWidth="1.4" fill="none" strokeLinecap="round" /></>;
    case 'a4': return <><rect width="64" height="64" fill="#3a3418" /><circle cx="32" cy="10" r="7" fill="#1a1210" /><path d="M6 66 C6 52 18 47 32 47 C46 47 58 52 58 66Z" fill="#f2a93b" /><rect x="27.5" y="38" width="9" height="11" rx="3" fill="#6b3f2a" /><circle cx="32" cy="29" r="12" fill="#7a4a32" /><path d="M19.5 28 C19 15 28 15 32 15 C37 15 45 16 44.5 28 C41 21 24 21 19.5 28Z" fill="#1a1210" /><circle cx="20" cy="33" r="1.6" fill="#f2c94c" /><circle cx="44" cy="33" r="1.6" fill="#f2c94c" /><circle cx="27.5" cy="30" r="1.3" fill="#1a1210" /><circle cx="36.5" cy="30" r="1.3" fill="#1a1210" /><path d="M28.5 35 Q32 38 35.5 35" stroke="#2a120c" strokeWidth="1.5" fill="none" strokeLinecap="round" /></>;
    case 'k1': return <><rect width="64" height="64" fill="#1c4a5c" /><path d="M10 66 C10 56 20 52 32 52 C44 52 54 56 54 66Z" fill="#ff8a3d" /><rect x="28" y="43" width="8" height="9" rx="3" fill="#dca37f" /><circle cx="32" cy="32" r="13" fill="#f0c3a0" /><path d="M18.5 31 L17 22 L23 25 L25 15 L30 21 L35 13 L38 21 L45 17 L45 27 L47 33 C45 26 40 24 32 24 C25 24 20 26 18.5 31Z" fill="#7a4a1d" /><circle cx="27" cy="33" r="1.5" fill="#2a1d16" /><circle cx="37" cy="33" r="1.5" fill="#2a1d16" /><path d="M27.5 38.5 Q32 42 36.5 38.5" stroke="#b5503f" strokeWidth="1.6" fill="none" strokeLinecap="round" /><circle cx="23.5" cy="37" r="2" fill="#f2a08a" opacity=".6" /><circle cx="40.5" cy="37" r="2" fill="#f2a08a" opacity=".6" /></>;
    case 'k2': return <><rect width="64" height="64" fill="#5a2a4a" /><circle cx="14" cy="36" r="6" fill="#2a1a14" /><circle cx="50" cy="36" r="6" fill="#2a1a14" /><path d="M10 66 C10 56 20 52 32 52 C44 52 54 56 54 66Z" fill="#7dd3fc" /><rect x="28" y="43" width="8" height="9" rx="3" fill="#e2ad88" /><circle cx="32" cy="32" r="13" fill="#f1c9a8" /><path d="M18.5 31 C18 17 46 17 45.5 31 C41 24 23 24 18.5 31Z" fill="#2a1a14" /><circle cx="19" cy="29" r="2.4" fill="#ff5fd2" /><circle cx="45" cy="29" r="2.4" fill="#ff5fd2" /><circle cx="27" cy="33" r="1.5" fill="#2a1d16" /><circle cx="37" cy="33" r="1.5" fill="#2a1d16" /><path d="M27.5 38.5 Q32 42 36.5 38.5" stroke="#b5503f" strokeWidth="1.6" fill="none" strokeLinecap="round" /></>;
    case 'k3': return <><rect width="64" height="64" fill="#3a3a16" /><path d="M10 66 C10 56 20 52 32 52 C44 52 54 56 54 66Z" fill="#a78bfa" /><rect x="28" y="43" width="8" height="9" rx="3" fill="#8a5a3c" /><circle cx="32" cy="32" r="13" fill="#a8704a" /><path d="M18 28 C18 14 46 14 46 28Z" fill="#ef4444" /><path d="M17 28 L49 28 C49 31 45 31 41 30 L17 30Z" fill="#b91c1c" /><circle cx="27" cy="34" r="1.5" fill="#1a1210" /><circle cx="37" cy="34" r="1.5" fill="#1a1210" /><path d="M27.5 39 Q32 42.5 36.5 39" stroke="#3a1a10" strokeWidth="1.6" fill="none" strokeLinecap="round" /></>;
    case 'k4': return <><rect width="64" height="64" fill="#1f3f57" /><path d="M15 44 C11 14 53 14 49 44 L49 46 L15 46Z" fill="#c2410c" /><path d="M10 66 C10 56 20 52 32 52 C44 52 54 56 54 66Z" fill="#facc15" /><rect x="28" y="43" width="8" height="9" rx="3" fill="#e2ad88" /><circle cx="32" cy="32" r="12.5" fill="#f1c9a8" /><path d="M19 30 C19 17 45 17 45 30 C40 24 24 24 19 30Z" fill="#c2410c" /><circle cx="26.5" cy="33" r="3.6" fill="none" stroke="#1a1a2e" strokeWidth="1.3" /><circle cx="37.5" cy="33" r="3.6" fill="none" stroke="#1a1a2e" strokeWidth="1.3" /><path d="M30 33 L34 33" stroke="#1a1a2e" strokeWidth="1.3" /><circle cx="26.5" cy="33" r="1.2" fill="#2a1d16" /><circle cx="37.5" cy="33" r="1.2" fill="#2a1d16" /><path d="M28 39 Q32 42 36 39" stroke="#b5503f" strokeWidth="1.6" fill="none" strokeLinecap="round" /></>;
    default: return <><rect width="64" height="64" fill="#1b2745" /><g transform="translate(14 14) scale(1.5)" fill="none" stroke="#4df0ff" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M3 11l9-8 9 8" /><path d="M5 10v10h14V10" /><path d="M10 20v-6h4v6" /></g></>;
  }
}

export function Avatar({ kind, size = 40, label }: { kind: string | null | undefined; size?: number; label?: string }) {
  const safe = (kind && kind in A11Y ? kind : 'home') as AvatarKind;
  const id = `avatar-clip-${safe}`;
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} role="img" aria-label={label ?? `Avatar: ${A11Y[safe]}`} style={{ display: 'block', flex: 'none' }}>
      <defs><clipPath id={id}><circle cx="32" cy="32" r="32" /></clipPath></defs>
      <g clipPath={`url(#${id})`}><Art kind={safe} /></g>
    </svg>
  );
}

/** Avatar with the person's colour ring: the identity used on rail, timeline, calendar and chores. */
export function PersonAvatar({ kind, color, size = 40, selected = true, label }: {
  kind: string | null | undefined; color: string | null | undefined; size?: number; selected?: boolean; label?: string;
}) {
  return (
    <span className="person-ring" style={{ background: selected ? (color ?? 'var(--line-strong)') : 'transparent', padding: size >= 40 ? 2 : 1.5 }}>
      <Avatar kind={kind} size={size} label={label} />
    </span>
  );
}
