import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'planner', settings: { reminders: lazy(() => import('./RemindersSettings')) } };
export default web;
