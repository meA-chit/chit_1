/** Mirrors docs/core/specifications/data-states.yaml. Never invent states. */
export type DataState = 'available' | 'stale' | 'partial' | 'unavailable' | 'unconfigured' | 'demo' | 'manual' | 'forecast';
export type Surface = 'tv' | 'tablet' | 'web' | 'mobile-adult' | 'mobile-kid';
export type CardSize = 's' | 'm' | 'l' | 'xl';
export type Slot = 'topbar' | 'timeline' | 'left' | 'center' | 'right';

export interface ManifestCard {
  id: string;
  module: string;
  submodule: string;
  title: string;
  slot: Slot;
  group?: string;
  order?: number;
  sizes: CardSize[];
  surfaces: Surface[];
  permissions: string[];
  data_states: DataState[];
}

export interface ManifestView {
  id: string;
  module: string;
  submodule: string;
  title: string;
  surfaces: Surface[];
  path?: string;
  legacy_url?: string;
}

/** Response of GET /api/shell: what this household/surface may show. Configured, never coded. */
export interface ShellConfig {
  surface: Surface;
  preset: string | null;
  screen_safe: boolean;
  interactive: boolean;
  household: { id: string; name: string } | null;
  member: Person | null;
  members: Person[];
  modules: { id: string; title: string; short_title: string; privacy_class: string }[];
  cards: ManifestCard[];
  views: ManifestView[];
  settings_sections: SettingsSection[];
}

/** A household member as the shell knows them. Colour and avatar identify the person on every card. */
export interface Person {
  id: string;
  name: string;
  role: 'adult' | 'child' | string;
  avatar: string | null;
  color: string | null;
}

/** A section one module contributes to another module's settings screen (e.g. planner chores in the household screen). */
export interface SettingsSection {
  id: string;
  module: string;
  submodule: string;
  title: string;
  target: string;
  order?: number;
  surfaces: Surface[];
}
