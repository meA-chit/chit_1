/**
 * Predefined avatar illustrations (never photos). Adults a1-a8, children k1-k8, plus `home` for the whole household.
 * Odd adults are men, even adults women; k1 k3 k5 k7 are boys, k2 k4 k6 k8 girls. The set varies skin tone, hair and headwear.
 * Kept in core so every module draws a person the same way. `AVATARS` lists the choices per role for pickers.
 */
export type AvatarKind = 'a1' | 'a2' | 'a3' | 'a4' | 'a5' | 'a6' | 'a7' | 'a8' | 'k1' | 'k2' | 'k3' | 'k4' | 'k5' | 'k6' | 'k7' | 'k8' | 'home';

export interface AvatarOption { kind: AvatarKind; label: string; group: 'Men' | 'Women' | 'Boys' | 'Girls' }
export const AVATARS: Record<'adult' | 'child', AvatarOption[]> = {
  adult: [
    { kind: 'a1', label: 'Man', group: 'Men' }, { kind: 'a3', label: 'Man, beard', group: 'Men' }, { kind: 'a5', label: 'Man, grey hair and glasses', group: 'Men' }, { kind: 'a7', label: 'Man, short hair', group: 'Men' },
    { kind: 'a2', label: 'Woman', group: 'Women' }, { kind: 'a4', label: 'Woman, bun', group: 'Women' }, { kind: 'a6', label: 'Woman, headscarf', group: 'Women' }, { kind: 'a8', label: 'Woman, curly hair', group: 'Women' },
  ],
  child: [
    { kind: 'k1', label: 'Boy', group: 'Boys' }, { kind: 'k3', label: 'Boy, cap', group: 'Boys' }, { kind: 'k5', label: 'Boy, short hair', group: 'Boys' }, { kind: 'k7', label: 'Boy, glasses', group: 'Boys' },
    { kind: 'k2', label: 'Girl, pigtails', group: 'Girls' }, { kind: 'k4', label: 'Girl, glasses', group: 'Girls' }, { kind: 'k6', label: 'Girl, hair puffs', group: 'Girls' }, { kind: 'k8', label: 'Girl, braids', group: 'Girls' },
  ],
};

export const PERSON_COLORS = ['#b79cff', '#4df0ff', '#ff8fb8', '#ffc857', '#8dffb0', '#ff9d5c'];

const A11Y: Record<AvatarKind, string> = {
  a1: 'man, short hair', a2: 'woman, long hair', a3: 'man with a beard', a4: 'woman with a bun',
  a5: 'man with grey hair and glasses', a6: 'woman with a headscarf', a7: 'man with short hair', a8: 'woman with short curly hair',
  k5: 'boy with short hair', k6: 'girl with hair puffs', k7: 'boy with a bowl cut and glasses', k8: 'girl with braids',
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
    case 'a5': return <><rect width="64" height="64" fill="#3b2f4a" /><path d="M6 66 C6 52 18 47 32 47 C46 47 58 52 58 66Z" fill="#94a3b8" /><rect x="27.5" y="38" width="9" height="11" rx="3" fill="#d39a74" /><circle cx="32" cy="29" r="12" fill="#eec3a0" /><path d="M20 27 C20 17 26 14 32 14 C38 14 44 17 44 27 C43 22 40 19 32 19 C25 19 21 22 20 27Z" fill="#cbd5e1" /><path d="M20 28 C19 31 20 34 21 35 L21 29Z M44 28 C45 31 44 34 43 35 L43 29Z" fill="#cbd5e1" /><circle cx="27" cy="30" r="3.4" fill="none" stroke="#334155" strokeWidth="1.2" /><circle cx="37" cy="30" r="3.4" fill="none" stroke="#334155" strokeWidth="1.2" /><path d="M30.4 30 L33.6 30" stroke="#334155" strokeWidth="1.2" /><circle cx="27" cy="30" r="1.1" fill="#2a1d16" /><circle cx="37" cy="30" r="1.1" fill="#2a1d16" /><path d="M28 36.5 Q32 38.5 36 36.5" stroke="#9a5a43" strokeWidth="1.4" fill="none" strokeLinecap="round" /></>;
    case 'a6': return <><rect width="64" height="64" fill="#1f3a45" /><path d="M6 66 C6 52 18 47 32 47 C46 47 58 52 58 66Z" fill="#14b8a6" /><path d="M13 52 C13 30 18 10 32 10 C46 10 51 30 51 52 C45 46 40 45 32 45 C24 45 19 46 13 52Z" fill="#7c3aed" /><circle cx="32" cy="30" r="11" fill="#c68b62" /><path d="M21.5 27 C24 17 40 17 42.5 27 C38 22.5 26 22.5 21.5 27Z" fill="#7c3aed" /><circle cx="27.5" cy="31" r="1.3" fill="#2a1d16" /><circle cx="36.5" cy="31" r="1.3" fill="#2a1d16" /><path d="M28.5 36 Q32 38.5 35.5 36" stroke="#9a3f35" strokeWidth="1.5" fill="none" strokeLinecap="round" /></>;
    case 'a7': return <><rect width="64" height="64" fill="#2b3a1f" /><path d="M6 66 C6 52 18 47 32 47 C46 47 58 52 58 66Z" fill="#f97316" /><rect x="27.5" y="38" width="9" height="11" rx="3" fill="#4a2f22" /><circle cx="32" cy="29" r="12" fill="#5b3a29" /><path d="M20.5 26 C20 17 26 15 32 15 C38 15 44 17 43.5 26 C41 22 37 21 32 21 C27 21 23 22 20.5 26Z" fill="#0f0b09" /><circle cx="27.5" cy="30" r="1.3" fill="#0f0b09" /><circle cx="36.5" cy="30" r="1.3" fill="#0f0b09" /><path d="M28 35 Q32 38 36 35" stroke="#1d0f0a" strokeWidth="1.5" fill="none" strokeLinecap="round" /></>;
    case 'a8': return <><rect width="64" height="64" fill="#4a2a2a" /><path d="M6 66 C6 52 18 47 32 47 C46 47 58 52 58 66Z" fill="#8b5cf6" /><rect x="27.5" y="38" width="9" height="11" rx="3" fill="#7a4a32" /><g fill="#120d0b"><circle cx="21" cy="21" r="6" /><circle cx="27" cy="15" r="6.5" /><circle cx="35" cy="14.5" r="6.5" /><circle cx="42" cy="20" r="6.5" /><circle cx="19.5" cy="28" r="4.5" /><circle cx="44.5" cy="28" r="4.5" /></g><circle cx="32" cy="29" r="11.5" fill="#8a5a3c" /><path d="M21 25 C24 19 40 19 43 25 C38 22 26 22 21 25Z" fill="#120d0b" /><circle cx="27.5" cy="30" r="1.3" fill="#120d0b" /><circle cx="36.5" cy="30" r="1.3" fill="#120d0b" /><path d="M28.3 35 Q32 38 35.7 35" stroke="#7a2e24" strokeWidth="1.6" fill="none" strokeLinecap="round" /></>;
    case 'k5': return <><rect width="64" height="64" fill="#3a2a4a" /><path d="M10 66 C10 56 20 52 32 52 C44 52 54 56 54 66Z" fill="#22c55e" /><rect x="28" y="43" width="8" height="9" rx="3" fill="#5b3a29" /><circle cx="32" cy="32" r="13" fill="#6b4430" /><path d="M19 30 C19 18 45 18 45 30 C41 25 23 25 19 30Z" fill="#0f0b09" /><circle cx="27" cy="33" r="1.5" fill="#0f0b09" /><circle cx="37" cy="33" r="1.5" fill="#0f0b09" /><path d="M27.5 38.5 Q32 42 36.5 38.5" stroke="#2a110c" strokeWidth="1.6" fill="none" strokeLinecap="round" /></>;
    case 'k6': return <><rect width="64" height="64" fill="#1c3a4a" /><circle cx="17" cy="18" r="7.5" fill="#0f0b09" /><circle cx="47" cy="18" r="7.5" fill="#0f0b09" /><path d="M10 66 C10 56 20 52 32 52 C44 52 54 56 54 66Z" fill="#f472b6" /><rect x="28" y="43" width="8" height="9" rx="3" fill="#4a2f22" /><circle cx="32" cy="32" r="13" fill="#5b3a29" /><path d="M19 29 C19 17 45 17 45 29 C41 23 23 23 19 29Z" fill="#0f0b09" /><circle cx="27" cy="33" r="1.5" fill="#0f0b09" /><circle cx="37" cy="33" r="1.5" fill="#0f0b09" /><path d="M27.5 38.5 Q32 42 36.5 38.5" stroke="#2a110c" strokeWidth="1.6" fill="none" strokeLinecap="round" /></>;
    case 'k7': return <><rect width="64" height="64" fill="#3a2a16" /><path d="M10 66 C10 56 20 52 32 52 C44 52 54 56 54 66Z" fill="#38bdf8" /><rect x="28" y="43" width="8" height="9" rx="3" fill="#cf9d72" /><circle cx="32" cy="32" r="13" fill="#e0b48a" /><path d="M18.5 32 C17 15 47 15 45.5 32 L45.5 27 C40 24 24 24 18.5 27Z" fill="#0f0b09" /><circle cx="26.5" cy="34" r="3.6" fill="none" stroke="#1e293b" strokeWidth="1.3" /><circle cx="37.5" cy="34" r="3.6" fill="none" stroke="#1e293b" strokeWidth="1.3" /><path d="M30 34 L34 34" stroke="#1e293b" strokeWidth="1.3" /><circle cx="26.5" cy="34" r="1.2" fill="#0f0b09" /><circle cx="37.5" cy="34" r="1.2" fill="#0f0b09" /><path d="M28 39.5 Q32 42.5 36 39.5" stroke="#b5503f" strokeWidth="1.6" fill="none" strokeLinecap="round" /></>;
    case 'k8': return <><rect width="64" height="64" fill="#2a3a16" /><path d="M20 30 C16 40 17 52 20 58 M44 30 C48 40 47 52 44 58" stroke="#3a2415" strokeWidth="6" fill="none" strokeLinecap="round" /><circle cx="20" cy="59" r="2.6" fill="#ec4899" /><circle cx="44" cy="59" r="2.6" fill="#ec4899" /><path d="M10 66 C10 56 20 52 32 52 C44 52 54 56 54 66Z" fill="#fb7185" /><rect x="28" y="43" width="8" height="9" rx="3" fill="#b5784f" /><circle cx="32" cy="32" r="13" fill="#c68b62" /><path d="M18.5 31 C18 16 46 16 45.5 31 C41 24 23 24 18.5 31Z" fill="#3a2415" /><circle cx="27" cy="33" r="1.5" fill="#2a1d16" /><circle cx="37" cy="33" r="1.5" fill="#2a1d16" /><path d="M27.5 38.5 Q32 42 36.5 38.5" stroke="#9a3f35" strokeWidth="1.6" fill="none" strokeLinecap="round" /></>;
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

/**
 * The "Everyone" mark: a roof (inverted V) over one small figure per member, adults taller than children.
 * Figures shrink to fit, so a household of two and a household of six both read at a glance.
 */
export function HouseholdMark({ adults, kids, size = 40, selected = true, color = 'var(--cyan)' }: {
  adults: number; kids: number; size?: number; selected?: boolean; color?: string;
}) {
  const people = [...Array(Math.max(0, adults)).fill('adult'), ...Array(Math.max(0, kids)).fill('child')] as ('adult' | 'child')[];
  const widths = people.map((kind) => (kind === 'adult' ? 11 : 8));
  const gap = 3;
  const total = widths.reduce((sum, w) => sum + w, 0) + gap * Math.max(0, people.length - 1);
  const scale = total > 40 ? 40 / total : 1;
  let x = 32 - (total * scale) / 2;
  const figures = people.map((kind, i) => {
    const w = widths[i]! * scale;
    const cx = x + w / 2;
    x += w + gap * scale;
    const head = (kind === 'adult' ? 4.2 : 3.1) * Math.max(scale, 0.6);
    const bodyTop = kind === 'adult' ? 40 : 45.5;
    return (
      <g key={i} fill={kind === 'adult' ? '#4df0ff' : '#ffc857'}>
        <circle cx={cx} cy={bodyTop - head - 1.2} r={head} />
        <path d={`M${cx - w / 2} 55 V${bodyTop + 4} a${w / 2} ${w / 2} 0 0 1 ${w} 0 V55Z`} />
      </g>
    );
  });
  return (
    <span className="person-ring" style={{ background: selected ? color : 'transparent', padding: size >= 40 ? 2 : 1.5 }}>
      <svg viewBox="0 0 64 64" width={size} height={size} role="img" aria-label={`Whole household: ${adults} adult${adults === 1 ? '' : 's'}, ${kids} child${kids === 1 ? '' : 'ren'}`} style={{ display: 'block', flex: 'none' }}>
        <circle cx="32" cy="32" r="32" fill="#1b2745" />
        <path d="M10 31 L32 11 L54 31" fill="none" stroke="#4df0ff" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
        {figures}
      </svg>
    </span>
  );
}
