import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'planner', cards: { 'family-timeline': lazy(() => import('./TimelineCard')) } };
export default web;
