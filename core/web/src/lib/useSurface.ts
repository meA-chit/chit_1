import { useEffect, useState } from 'react';
import type { Surface } from '../api/types';

const VALID: Surface[] = ['tv', 'tablet', 'web', 'mobile-adult', 'mobile-kid'];

/**
 * Surface = what kind of screen this is. `?surface=tv` forces one (display devices, demos).
 * Otherwise inferred from width. Kid surfaces are never inferred: an adult provisions them.
 */
export function detectSurface(search: string, width: number): Surface {
  const forced = new URLSearchParams(search).get('surface') as Surface | null;
  if (forced && VALID.includes(forced)) return forced;
  if (width < 720) return 'mobile-adult';
  if (width < 1100) return 'tablet';
  return 'web';
}

export function useSurface(): Surface {
  const [surface, setSurface] = useState(() => detectSurface(location.search, innerWidth));
  useEffect(() => {
    const onResize = () => setSurface(detectSurface(location.search, innerWidth));
    addEventListener('resize', onResize);
    return () => removeEventListener('resize', onResize);
  }, []);
  return surface;
}
