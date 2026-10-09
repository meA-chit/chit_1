import type { ComponentType } from 'react';
import type { MomentProvider } from '../moments/types';
import type { CardProps, ModuleWeb, SettingsSectionProps } from './types';

const cards = new Map<string, ComponentType<CardProps>>();
const views = new Map<string, ComponentType>();
const sections = new Map<string, ComponentType<SettingsSectionProps>>();
const providers: { module: string; key: string; provider: MomentProvider }[] = [];

export function registerModules(found: Record<string, unknown>): void {
  for (const [path, value] of Object.entries(found)) {
    const mod = value as ModuleWeb | undefined;
    if (!mod || typeof mod.module !== 'string' || (!mod.cards && !mod.views && !mod.settings && !mod.moments)) {
      throw new Error(`${path} must default-export a ModuleWeb`);
    }
    for (const [viewId, component] of Object.entries(mod.views ?? {})) {
      const key = `${mod.module}/${viewId}`;
      if (views.has(key)) throw new Error(`duplicate view registration ${key}`);
      views.set(key, component);
    }
    for (const [sectionId, component] of Object.entries(mod.settings ?? {})) {
      const key = `${mod.module}/${sectionId}`;
      if (sections.has(key)) throw new Error(`duplicate settings section registration ${key}`);
      sections.set(key, component);
    }
    for (const [providerId, provider] of Object.entries(mod.moments ?? {})) {
      const key = `${mod.module}/${providerId}`;
      if (providers.some((entry) => entry.key === key)) throw new Error(`duplicate moments registration ${key}`);
      providers.push({ module: mod.module, key, provider });
    }
    for (const [cardId, component] of Object.entries(mod.cards ?? {})) {
      const key = `${mod.module}/${cardId}`;
      if (cards.has(key)) throw new Error(`duplicate card registration ${key}`);
      cards.set(key, component);
    }
  }
}

export const getCardComponent = (module: string, cardId: string) => cards.get(`${module}/${cardId}`);
export const getViewComponent = (module: string, viewId: string) => views.get(`${module}/${viewId}`);
export const getSettingsSection = (module: string, id: string) => sections.get(`${module}/${id}`);

/** Registered once at start-up, so the list (and the hook order inside the panel) never changes while the app runs. */
export const getMomentProviders = () => providers;
