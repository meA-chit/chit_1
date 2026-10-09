/** The Chit mark: five stars traced into a lowercase c, the newest one lit. Nodes follow the text colour; the lit star is the amber signal colour. */
export function ChitMark({ size = 28 }: { size?: number }) {
  return (
    <svg className="chit-mark" viewBox="0 0 100 100" width={size} height={size} aria-hidden>
      <polyline points="70.6,25.5 34,22.3 18,50 34,77.7 70.6,74.5" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
      <g fill="currentColor">
        <circle cx="34" cy="22.3" r="6" />
        <circle cx="18" cy="50" r="6" />
        <circle cx="34" cy="77.7" r="6" />
        <circle cx="70.6" cy="74.5" r="6" />
      </g>
      <circle cx="70.6" cy="25.5" r="17" fill="none" stroke="var(--amber)" strokeWidth="3" opacity="0.55" />
      <circle cx="70.6" cy="25.5" r="10" fill="var(--amber)" />
    </svg>
  );
}
