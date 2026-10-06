import { useQuery } from '@tanstack/react-query';
import { fetchShell } from '../api/client';
import { useSurface } from '../lib/useSurface';
import { useViewer } from './viewer';

/** The resolved shell for this surface and the member being viewed. Refetch it after saving settings. */
export function useShell() {
  const surface = useSurface();
  const { memberId } = useViewer();
  return useQuery({ queryKey: ['shell', surface, memberId], queryFn: () => fetchShell(surface, memberId), staleTime: 60_000 });
}
