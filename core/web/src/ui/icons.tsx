import type { ReactNode } from 'react';

const base = { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round' } as const;
const make = (path: ReactNode) => () => <svg {...base} aria-hidden>{path}</svg>;

export const HomeIcon = make(<><path d="M3 11l9-8 9 8" /><path d="M5 10v10h14V10" /><path d="M10 20v-6h4v6" /></>);
export const SettingsIcon = make(<><path d="M4 7h9M17 7h3M4 17h3M11 17h9" /><circle cx="15" cy="7" r="2" /><circle cx="9" cy="17" r="2" /></>);   // sliders: edit the household
export const ArrowUpIcon = make(<path d="M12 19V5M5 12l7-7 7 7" />);
export const GridIcon = make(<><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>);

export const CalendarIcon = make(<><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M8 3v4M16 3v4M3 10h18" /></>);
export const SmileIcon = make(<><circle cx="12" cy="12" r="9" /><path d="M8.5 14.5c1 1.4 2.2 2 3.5 2s2.5-.6 3.5-2" /><path d="M9 9.5h.01M15 9.5h.01" /></>);
export const BoltIcon = make(<path d="M13 2L4 14h7l-1 8 9-12h-7z" />);
export const ChipIcon = make(<><rect x="5" y="3" width="14" height="18" rx="3" /><circle cx="12" cy="14" r="3" /><path d="M9 7h6" /></>);
export const WalletIcon = make(<><path d="M3 7h15a3 3 0 013 3v7a3 3 0 01-3 3H6a3 3 0 01-3-3z" /><path d="M3 7l12-4v4" /><circle cx="17" cy="14" r="1.2" /></>);
export const BellIcon = make(<><path d="M6 8a6 6 0 1112 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 004 0" /></>);
export const PlusIcon = make(<path d="M12 5v14M5 12h14" />);
export const CheckIcon = make(<path d="M20 6L9 17l-5-5" />);
export const ClockIcon = make(<><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>);
export const FlameIcon = () => <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 2s5 4.5 5 10a5 5 0 01-10 0c0-2 1-3 1-3s1 2 2 2c0-3 0-5 2-9z" /></svg>;
export const ThermoIcon = make(<path d="M14 14.8V4a2 2 0 10-4 0v10.8a4 4 0 104 0z" />);
export const SunIcon = make(<><circle cx="12" cy="12" r="4" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2" /></>);
export const StarIcon = make(<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" />);
export const PillIcon = make(<><rect x="3" y="8.5" width="18" height="7" rx="3.5" transform="rotate(-35 12 12)" /><path d="M9.2 7.6l5.6 8.2" /></>);
export const BookIcon = make(<><path d="M4 5.5A2.5 2.5 0 016.5 3H20v16H6.5A2.5 2.5 0 004 21.5z" /><path d="M4 19V5.5" /></>);
export const TrashIcon = make(<><path d="M4 7h16" /><path d="M9 7V4.5h6V7" /><path d="M6 7l1 13h10l1-13" /><path d="M10 11v6M14 11v6" /></>);
export const XIcon = make(<path d="M6 6l12 12M18 6L6 18" />);
export const ListIcon = make(<><path d="M9 6h11M9 12h11M9 18h11" /><path d="M4 6h.01M4 12h.01M4 18h.01" /></>);
export const CardsIcon = make(<><rect x="3" y="3" width="8" height="8" rx="2" /><rect x="13" y="3" width="8" height="8" rx="2" /><rect x="3" y="13" width="8" height="8" rx="2" /><rect x="13" y="13" width="8" height="8" rx="2" /></>);
export const UndoIcon = make(<><path d="M9 14L4 9l5-5" /><path d="M4 9h10a6 6 0 010 12h-3" /></>);
export const MergeIcon = make(<><path d="M6 4v4a6 6 0 006 6h0a6 6 0 006-6V4" /><path d="M12 14v6" /><path d="M9 17l3 3 3-3" /></>);
export const SparkIcon = make(<path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z" />);

/** Module id -> nav icon. Unknown modules fall back to a grid. */
export const MODULE_ICONS: Record<string, () => JSX.Element> = {
  planner: CalendarIcon, kids: SmileIcon, energy: BoltIcon, devices: ChipIcon, finance: WalletIcon, household: SettingsIcon,
};
