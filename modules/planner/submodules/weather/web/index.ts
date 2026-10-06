import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'planner', cards: { 'weather-now': lazy(() => import('./WeatherCard')) } };
export default web;
