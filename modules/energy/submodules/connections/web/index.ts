import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'energy', settings: { energy: lazy(() => import('./EnergySettings')) } };
export default web;
