import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'kids', cards: { 'kids-goals': lazy(() => import('./GoalsCard')) } };
export default web;
