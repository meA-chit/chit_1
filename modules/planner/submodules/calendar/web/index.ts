import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';
import { useCalendarMoments } from './moments';

const web: ModuleWeb = { module: 'planner', cards: { 'calendar-agenda': lazy(() => import('./AgendaCard')) }, moments: { 'next-event': useCalendarMoments } };
export default web;
