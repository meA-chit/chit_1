import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'devices', cards: { 'climate-now': lazy(() => import('./ClimateNowCard')) } };
export default web;
