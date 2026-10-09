import { useEffect, useRef, useState } from 'react';
import type { ShellConfig } from '../api/types';
import { HouseholdMark, PersonAvatar } from '../ui/Avatar';
import { ThemeSwitch } from './ThemeSwitch';
import { useViewer } from './viewer';

/**
 * "Viewing as": whose enablement the shell applies (a convenience until identity exists, ADR-0007).
 * Lives in the top bar so the left rail can be the one place for module navigation.
 */
export function ViewerMenu({ shell }: { shell: ShellConfig }) {
  const { memberId, setViewer } = useViewer();
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const current = shell.members.find((m) => m.id === memberId);
  const adults = shell.members.filter((m) => m.role === 'adult').length;
  const kids = shell.members.filter((m) => m.role === 'child').length;

  useEffect(() => {
    if (!open) return;
    const away = (event: MouseEvent) => { if (!box.current?.contains(event.target as Node)) setOpen(false); };
    const esc = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', away);
    document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', away); document.removeEventListener('keydown', esc); };
  }, [open]);

  const choose = (id: string | null) => { setViewer(id); setOpen(false); };

  return (
    <div className="vmenu" ref={box}>
      <button type="button" className="vmenu__btn bubble" aria-haspopup="true" aria-expanded={open} onClick={() => setOpen(!open)}>
        {current ? <PersonAvatar kind={current.avatar} color={current.color} size={30} /> : <HouseholdMark adults={adults} kids={kids} size={30} />}
        <span className="vmenu__text"><small>Viewing as</small>{current ? current.name.split(' ')[0] : 'Everyone'}</span>
      </button>
      {open && (
        <div className="vmenu__pop" role="menu" aria-label="View as">
          <button type="button" role="menuitemradio" aria-checked={!current} onClick={() => choose(null)}>
            <HouseholdMark adults={adults} kids={kids} size={30} />Everyone
          </button>
          {shell.members.map((person) => (
            <button key={person.id} type="button" role="menuitemradio" aria-checked={memberId === person.id} onClick={() => choose(person.id)}>
              <PersonAvatar kind={person.avatar} color={person.color} size={30} />{person.name.split(' ')[0]}
            </button>
          ))}
          <div className="vmenu__theme"><span className="eyebrow">Theme</span><ThemeSwitch orientation="horizontal" /></div>
        </div>
      )}
    </div>
  );
}
