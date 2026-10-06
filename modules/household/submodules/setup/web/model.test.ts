import { describe, expect, it } from 'vitest';
import {
  emptyDocument, newActivity, newAdult, newCalendar, newChild, nextIdentity, removeMember, toggleModule, toPayload, validate, type CatalogModule,
} from './model';

const catalog: CatalogModule[] = [
  { id: 'household', title: 'Household', status: 'x', privacy_class: 'sensitive', audiences: ['adult'], depends_on: [], submodules: [], required: true },
  { id: 'planner', title: 'Planner', status: 'x', privacy_class: 'normal', audiences: ['adult', 'child'], depends_on: ['household'], submodules: [], required: false },
  { id: 'kids', title: 'Kids', status: 'x', privacy_class: 'strict', audiences: ['adult', 'child'], depends_on: ['household', 'planner'], submodules: [], required: false },
];

describe('household model', () => {
  it('validates the essentials', () => {
    const doc = emptyDocument(null);
    expect(validate(doc)).toEqual(expect.arrayContaining(['Give the household a name.', 'Member 1 needs a name.']));
    doc.household.name = 'Home';
    doc.members[0]!.name = 'Ada';
    expect(validate(doc)).toEqual([]);
  });

  it('rejects calendar links that are not https/webcal', () => {
    const doc = emptyDocument(null);
    doc.household.name = 'Home';
    doc.members[0]!.name = 'Ada';
    doc.calendars.push({ ...newCalendar(), name: 'Bins', subscription_url: 'http://insecure.example/a.ics' });
    expect(validate(doc).join()).toMatch(/https/);
  });

  it('activity commute: a car always has a parent, and missing details are called out', () => {
    const doc = emptyDocument(null);
    doc.household.name = 'Home';
    doc.members[0]!.name = 'Ada';
    const child = newChild('Cy');
    child.profile.activities = [{ ...newActivity('x'), name: 'Judo', commute_mode: 'car', travel_minutes: 12, escort: 'independent', escort_adult_client_id: doc.members[0]!.client_id }];
    doc.members.push(child);
    const activity = toPayload(doc).members[1]!.profile.activities![0]!;
    expect(activity.escort).toBe('parent');
    expect(activity.escort_adult_client_id).toBe(doc.members[0]!.client_id);
    child.profile.activities = [{ ...newActivity(), name: 'Judo', commute_mode: 'cycle', travel_minutes: null }];
    expect(validate(doc).join()).toMatch(/travel time/);
    child.profile.activities = [{ ...newActivity(), name: 'Judo', commute_mode: 'walk', travel_minutes: 5, escort: 'parent', escort_adult_client_id: null }];
    expect(validate(doc).join()).toMatch(/which parent/);
    child.profile.activities = [{ ...newActivity(), name: 'Judo', commute_mode: 'walk', travel_minutes: 5 }];
    expect(validate(doc)).toEqual([]);
  });

  it('removing the parent who goes along makes the activity independent', () => {
    const doc = emptyDocument(null);
    const second = newAdult('Bo');
    const child = newChild('Cy');
    child.profile.activities = [{ ...newActivity(second.client_id), name: 'Judo', escort: 'parent', commute_mode: 'walk', travel_minutes: 5 }];
    doc.members.push(second, child);
    const activity = removeMember(doc, second.client_id).members[1]!.profile.activities![0]!;
    expect([activity.escort, activity.escort_adult_client_id]).toEqual(['independent', null]);
  });

  it('removing a member cleans every reference', () => {
    const doc = emptyDocument(null);
    const second = newAdult('Bo');
    const child = { ...newChild('Cy'), profile: { pickup_adult_client_ids: [second.client_id], dropoff_adult_client_ids: [second.client_id] } };
    doc.members.push(second, child);
    doc.calendars.push({ ...newCalendar(), name: 'x', member_client_ids: [second.client_id], chore_assignee_client_ids: [second.client_id] });
    const next = removeMember(doc, second.client_id);
    expect(next.members.map((m) => m.client_id)).not.toContain(second.client_id);
    expect(next.members[1]!.profile.pickup_adult_client_ids).toEqual([]);
    expect(next.calendars[0]!.member_client_ids).toEqual([]);
    expect(next.calendars[0]!.chore_assignee_client_ids).toEqual([]);
  });

  it('module dependencies cascade both ways and narrow members', () => {
    let doc = { ...emptyDocument(['household']) };
    doc = toggleModule(doc, catalog, 'kids', true);
    expect(doc.modules?.sort()).toEqual(['household', 'kids', 'planner']);
    doc.members[0]!.modules = ['kids', 'planner'];
    doc = toggleModule(doc, catalog, 'planner', false);
    expect(doc.modules?.sort()).toEqual(['household']);
    expect(doc.members[0]!.modules).toEqual([]);
  });

  it('household can never be switched off', () => {
    const doc = toggleModule(emptyDocument(['household', 'planner']), catalog, 'household', false);
    expect(doc.modules).toContain('household');
  });

  it('payload turns blanks into nulls', () => {
    const doc = emptyDocument(null);
    doc.household.region = '  ';
    doc.members[0]!.profile.birth_date = '';
    const payload = toPayload(doc);
    expect(payload.household.region).toBeNull();
    expect(payload.members[0]!.profile.birth_date).toBeNull();
  });

  it('new members get an unused avatar of their role and an unused colour', () => {
    const first = newAdult('Ada');
    const second = newAdult('Bo', [first]);
    const kid = newChild('Cy', [first, second]);
    expect(second.avatar).not.toBe(first.avatar);
    expect(second.color).not.toBe(first.color);
    expect(['k1', 'k2', 'k3', 'k4']).toContain(kid.avatar);
    expect([first.color, second.color]).not.toContain(kid.color);
    expect(nextIdentity([], 'adult').avatar).toBe('a2');
  });

  it('validates the optional location as a pair in range', () => {
    const doc = emptyDocument(null);
    doc.household.name = 'Home';
    doc.members[0]!.name = 'Ada';
    doc.household.latitude = 48.1;
    expect(validate(doc).join()).toMatch(/both latitude and longitude/);
    doc.household.longitude = 11.6;
    expect(validate(doc)).toEqual([]);
    doc.household.latitude = 123;
    expect(validate(doc).join()).toMatch(/Latitude/);
  });
});
