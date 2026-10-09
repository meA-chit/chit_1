import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'energy', views: { grid: lazy(() => import('./GridView')) } };
export default web;
