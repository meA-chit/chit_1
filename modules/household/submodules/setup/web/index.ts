import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = {
  module: 'household',
  views: { household: lazy(() => import('./HouseholdView')) },
};
export default web;
