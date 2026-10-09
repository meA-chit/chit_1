import { Suspense } from 'react';
import { getSettingsSection } from '../registry';
import { Empty, Skeleton } from '../ui/CardFrame';
import { Section } from '../ui/form';
import { useShell } from './useShell';

/**
 * Renders the sections other modules contribute to a settings screen (manifest `settings_sections`, target = this screen).
 * The host screen never imports module code; what appears is decided by the shell (module enabled for the household).
 * `ready` is false until the host entity exists (e.g. household not created yet): sections need saved members to refer to.
 */
export function SettingsSections({ target, ready, only }: { target: string; ready: boolean; /** Render just this section id (a tabbed host shows one at a time). */ only?: string }) {
  const shell = useShell();
  const sections = (shell.data?.settings_sections ?? []).filter((section) => section.target === target && (!only || section.id === only));
  if (sections.length === 0) return null;
  return (
    <>
      {sections.map((section) => {
        const Component = getSettingsSection(section.module, section.id);
        return (
          <div key={`${section.module}/${section.id}`}>
            <Section id={`section-${section.id}`} title={section.title}
              actions={<span className="badge" data-state="available" title="These save as you go, separately from the Save changes button">Saved instantly</span>}>
              {!ready ? (
                <Empty title="Available after you create the household">Save the household first, then add {section.title.toLowerCase()} for its members.</Empty>
              ) : Component ? (
                <Suspense fallback={<Skeleton />}><Component members={shell.data?.members ?? []} /></Suspense>
              ) : (
                <Empty title="Section not installed">This build has no renderer for <span className="mono">{section.module}/{section.id}</span>.</Empty>
              )}
            </Section>
          </div>
        );
      })}
    </>
  );
}
