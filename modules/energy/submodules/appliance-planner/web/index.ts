import type { ModuleWeb } from '@chit/core';
import { useEnergyMoments } from './moments';

/** No cards of its own (the windows show inside the Energy card); it publishes candidates for the Now panel. */
const web: ModuleWeb = { module: 'energy', moments: { 'cheap-window': useEnergyMoments } };
export default web;
