import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, ApiError, Notice, Section, SelectField, Skeleton } from '@chit/core';
import { PRIVACY_KEY, usePrivacy, type PrivacySection } from '../../../shared/kids';
import { useState } from 'react';

const LABEL: Record<PrivacySection, string> = { grades: 'Grades', health: 'Medicine' };
const AGES: [string, string][] = Array.from({ length: 19 }, (_, age) => [String(age), age === 18 ? '18 (adult)' : `${age} ${age === 1 ? 'year' : 'years'}`]);

/**
 * Privacy between a child and their parents. Parents set the age from which a child may take grades or medicine private;
 * the child decides on their own phone. Parents see that a section is private, never what is in it. A medicine marked
 * safety-critical can never be hidden. A parent who raises the age takes the choice back, and the phone says so.
 */
export function KidPrivacy({ memberId }: { memberId?: string }) {
  const privacy = usePrivacy();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const save = useMutation({
    mutationFn: ({ section, min_age }: { section: PrivacySection; min_age: number }) => api('/api/kids/privacy/policy', { method: 'PUT', body: JSON.stringify({ section, min_age }) }),
    onSuccess: () => { setError(null); void queryClient.invalidateQueries({ queryKey: PRIVACY_KEY }); void queryClient.invalidateQueries({ queryKey: ['kids'] }); },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was changed.'),
  });
  if (privacy.isPending) return <Skeleton lines={3} />;
  if (privacy.isError || !privacy.data) return null;
  const { policy, children } = privacy.data;
  const shown = children.filter((child) => !memberId || child.member_id === memberId);

  return (
    <Section id="section-kid-privacy" title="Privacy from you"
      actions={<span className="badge" data-state="available" title="Applies at once">Saved instantly</span>}>
      <div className="stack">
        <p className="field__hint" style={{ margin: 0 }}>
          From the age you choose, a child can keep grades or medicine to themselves, on their own phone. You then see that it is private, never what is in it.
          Medicine you mark safety-critical always stays visible to you. If you raise an age, the child's choice stops applying and their phone says so.
        </p>
        <div className="form-grid">
          {(['grades', 'health'] as PrivacySection[]).map((section) => (
            <SelectField key={section} label={`${LABEL[section]}: a child may keep it private from`} value={String(policy[section])} options={AGES}
              disabled={save.isPending} onChange={(value) => save.mutate({ section, min_age: Number(value) })} />
          ))}
        </div>
        {error && <Notice tone="error">{error}</Notice>}
        <ul className="kp__devices" aria-label="Privacy status">
          {shown.map((child) => (
            <li key={child.member_id}>
              <div><strong>{child.name.split(' ')[0]}</strong></div>
              <div className="row">
                {(['grades', 'health'] as PrivacySection[]).map((section) => {
                  const info = child.sections[section];
                  return (
                    <span key={section} className="badge" data-state={info.private ? 'partial' : info.eligible ? 'available' : 'unconfigured'}
                      title={info.eligible ? undefined : `Can choose from age ${policy[section]}${info.age === null ? ' (no birth date entered)' : `, now ${info.age}`}`}>
                      {LABEL[section]}: {info.private ? 'private' : info.eligible ? 'open to you' : `from ${policy[section]}`}
                    </span>
                  );
                })}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
