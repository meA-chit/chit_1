import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = {
  module: 'planner',
  cards: { 'todo-today': lazy(() => import('./TodoCard')) },
  settings: { chores: lazy(() => import('./ChoresSettings')) },
};
export default web;
