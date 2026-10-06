import type { ModuleWeb } from '@chit/core';

/** Grades are a panel of the Kids page (kid-view composes it); the submodule has no dashboard card, on purpose: grades are private. */
const web: ModuleWeb = { module: 'kids', views: {} };
export default web;
