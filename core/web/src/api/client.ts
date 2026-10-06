import type { ShellConfig, Surface } from './types';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/**
 * The single place the client learns where the hub lives. Today: same origin (served by, or proxied
 * to, the loopback hub). Mobile apps will inject a base URL per paired hub (see ADR-0009).
 */
let baseUrl = '';
export const setHubBaseUrl = (url: string) => {
  baseUrl = url.replace(/\/$/, '');
};

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(baseUrl + path, {
    ...init,
    headers: { Accept: 'application/json', ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, (body as { error?: string }).error ?? response.statusText);
  return body as T;
}

export const fetchShell = (surface: Surface, memberId?: string | null) =>
  api<ShellConfig>(`/api/shell?surface=${surface}${memberId ? `&member=${encodeURIComponent(memberId)}` : ''}`);
