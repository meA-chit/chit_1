import { ChipGroup, Notice, Toggle } from '@chit/core';
import { toggleModule, type CatalogModule, type HouseholdDocument } from './model';

export function ModulesSection({ doc, catalog, onChange }: {
  doc: HouseholdDocument; catalog: CatalogModule[]; onChange: (doc: HouseholdDocument) => void;
}) {
  const enabled = new Set(doc.modules ?? catalog.map((module) => module.id));
  return (
    <div className="stack">
      <p className="field__hint" style={{ margin: 0 }}>
        The dashboard is built from what you switch on here. Modules that depend on others switch them on too.
      </p>
      {catalog.map((module) => (
        <Toggle key={module.id} label={module.title} checked={enabled.has(module.id)} disabled={module.required}
          hint={[
            module.required ? 'Always on: the foundation of every household.' : undefined,
            module.depends_on.length ? `Needs ${module.depends_on.join(', ')}.` : undefined,
            module.privacy_class !== 'normal' ? `${module.privacy_class} data: hidden on shared screens.` : undefined,
            module.status === 'structure-only' ? 'Coming soon: nothing to show yet.' : undefined,
          ].filter(Boolean).join(' ')}
          onChange={(on) => onChange(toggleModule(doc, catalog, module.id, on))} />
      ))}
      {doc.members.some((member) => member.modules !== null) && (
        <Notice>Some members use a narrower set of modules; change that on their card in Household members.</Notice>
      )}
    </div>
  );
}
