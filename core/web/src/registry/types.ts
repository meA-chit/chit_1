import type { ComponentType } from 'react';
import type { ManifestCard, Person } from '../api/types';
import type { MomentProvider } from '../moments/types';

export interface CardProps {
  card: ManifestCard;
  /** True when rendered as a tab inside a grouped panel: pass it to CardFrame. */
  embedded?: boolean;
}

/**
 * What a submodule's `web/index.ts` default-exports. Keys are the card ids declared in the module's
 * `module.manifest.yaml`. The manifest decides whether a card shows; this only supplies the renderer.
 */
export interface SettingsSectionProps {
  /** Saved household members (a section can only reference people that already exist). */
  members: Person[];
}

export interface ModuleWeb {
  module: string;
  cards?: Record<string, ComponentType<CardProps>>;
  /** Full-screen views, keyed by the view ids in the manifest (which also give the route `path`). */
  views?: Record<string, ComponentType>;
  /** Sections contributed to another module's settings screen, keyed by the manifest's `settings_sections` ids. */
  settings?: Record<string, ComponentType<SettingsSectionProps>>;
  /** Candidates for the Now panel, keyed by a provider id. The panel runs them only while the module is enabled. */
  moments?: Record<string, MomentProvider>;
}
