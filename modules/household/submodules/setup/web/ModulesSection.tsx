import { Notice, Toggle } from '@chit/core';
import { toggleModule, type CatalogModule, type HouseholdDocument } from './model';

/**
 * The master list of modules. `household` is always on, so it is not listed. A module that needs children (the manifest says which)
 * is off and cannot be switched on until the household is a family with a child.
 */
export function ModulesSection({ doc, catalog, onChange }: {
  doc: HouseholdDocument; catalog: CatalogModule[]; onChange: (doc: HouseholdDocument) => void;
}) {
  const enabled = new Set(doc.modules ?? catalog.map((module) => module.id));
  const hasChildren = doc.members.some((member) => member.role === 'child');
  return (
    <div className="stack">
      <p className="field__hint" style={{ margin: 0 }}>
        The dashboard is built from what you switch on here. Modules that depend on others switch them on too.
      </p>
      {catalog.filter((module) => !module.required).map((module) => {
        const locked = !!module.needs_children && !hasChildren;
        return (
          <Toggle key={module.id} label={module.title} checked={enabled.has(module.id) && !locked} disabled={locked}
            hint={[
              locked ? (doc.household.type === 'family' ? 'Needs at least one child: add a child under Members.' : 'Needs at least one child. Change the household type to Family to add children.') : undefined,
              module.depends_on.filter((id) => id !== 'household').length ? `Needs ${module.depends_on.filter((id) => id !== 'household').join(', ')}.` : undefined,
              module.privacy_class !== 'normal' ? `${module.privacy_class} data: hidden on shared screens.` : undefined,
              module.status === 'structure-only' ? 'Coming soon: nothing to show yet.' : undefined,
            ].filter(Boolean).join(' ')}
            onChange={(on) => onChange(toggleModule(doc, catalog, module.id, on))} />
        );
      })}
      {doc.members.some((member) => member.modules !== null) && (
        <Notice>Some members use a narrower set of modules; change that on their card under Members.</Notice>
      )}
    </div>
  );
}
