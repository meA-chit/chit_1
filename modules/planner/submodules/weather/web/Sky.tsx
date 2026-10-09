/** Small stroke icons, one per condition. The condition is always also written out, so colour and shape are never the only cue. */
export function Sky({ icon, size = 26 }: { icon: string; size?: number }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true } as const;
  const cloud = 'M7 15h10a4 4 0 000-8 5.5 5.5 0 00-10.6 1.5A3.3 3.3 0 007 15z';
  if (icon === 'clear') return <svg {...common}><circle cx="12" cy="12" r="4" /><path d="M12 2.5V5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M18.7 5.3l-1.8 1.8M7.1 16.9l-1.8 1.8" /></svg>;
  if (icon === 'partly') return <svg {...common}><circle cx="9" cy="8" r="3.2" /><path d="M9 2v1.2M3 8h1.2M4.8 3.8l.9.9M13.2 3.8l-.9.9" /><path d="M8 20h9a3.6 3.6 0 000-7.2 4.8 4.8 0 00-9.3 1.3A3 3 0 008 20z" /></svg>;
  if (icon === 'rain') return <svg {...common}><path d={cloud} /><path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3" /></svg>;
  if (icon === 'snow') return <svg {...common}><path d={cloud} /><path d="M8 19h.01M12 21h.01M16 19h.01" /></svg>;
  if (icon === 'storm') return <svg {...common}><path d={cloud} /><path d="M12 16l-2.5 4h4L11 23" /></svg>;
  if (icon === 'fog') return <svg {...common}><path d={cloud} /><path d="M6 19h12M8 22h8" /></svg>;
  return <svg {...common}><path d="M7 19h10a4 4 0 000-8 5.5 5.5 0 00-10.6 1.5A3.3 3.3 0 007 19z" /></svg>;
}
