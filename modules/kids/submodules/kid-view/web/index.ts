import { lazy } from 'react';
import type { ModuleWeb } from '@chit/core';

const web: ModuleWeb = { module: 'kids', views: { kids: lazy(() => import('./KidsView')) } };
export default web;
