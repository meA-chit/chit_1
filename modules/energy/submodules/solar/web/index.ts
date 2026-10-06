import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'energy', cards: { 'energy-solar': lazy(() => import('./SolarCard')) } };
export default web;
