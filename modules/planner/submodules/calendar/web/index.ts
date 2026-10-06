import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'planner', cards: { 'calendar-agenda': lazy(() => import('./AgendaCard')) } };
export default web;
