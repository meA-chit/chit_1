import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = {
  module: 'energy',
  cards: { 'energy-now': lazy(() => import('./EnergyNowCard')), 'energy-ribbon': lazy(() => import('./EnergyRibbonCard')) },
};
export default web;
