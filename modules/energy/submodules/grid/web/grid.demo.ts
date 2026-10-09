/**
 * DEMO data for the Grid page. No HomematicIP connector exists yet (Home Assistant boundary, ADR-0002, is a later story),
 * so everything in this file is illustrative and every tile that uses it is labelled "demo". It mirrors what a real
 * Homematic IP Access Point would expose, so the page does not change shape when the connector arrives.
 */

export type DeviceRole = 'heating' | 'appliance' | 'cooling' | 'ventilation' | 'electronics' | 'meter';

export interface DemoDevice {
  id: string;
  name: string;
  room: string;
  /** Real Homematic IP model that would deliver this reading. */
  model: string;
  role: DeviceRole;
  /** Power right now in watts. */
  watts: number;
  /** kWh used today so far. */
  todayKwh: number;
  /** kWh per hour, midnight to now, for the sparkline. */
  hourly: number[];
  /** Always-on devices (fridge) versus ones that run in cycles. */
  mode: 'always' | 'cycle' | 'idle';
  note?: string;
  important: boolean;
}

const ramp = (values: number[]) => values;

export const DEMO_DEVICES: DemoDevice[] = [
  { id: 'heatpump', name: 'Heat pump', room: 'Utility room', model: 'HmIP-FSM16 + meter', role: 'heating', watts: 1180, todayKwh: 9.6, mode: 'cycle', important: true,
    hourly: ramp([0.9, 1.1, 1.3, 1.2, 0.8, 0.4, 0.3, 0.3, 0.4, 0.3, 0.3, 0.4, 0.5, 0.5, 0.4, 0.4, 0.3, 0.3]), note: 'Pre-heating on cheap power' },
  { id: 'dryer', name: 'Tumble dryer', room: 'Basement', model: 'HmIP-PSM-2', role: 'appliance', watts: 0, todayKwh: 2.1, mode: 'idle', important: true,
    hourly: ramp([0, 0, 0, 0, 0, 0, 0, 0, 0, 1.1, 1.0, 0, 0, 0, 0, 0, 0, 0]), note: 'Ran 09:00 to 11:00' },
  { id: 'washer', name: 'Washing machine', room: 'Basement', model: 'HmIP-PSM-2', role: 'appliance', watts: 420, todayKwh: 0.9, mode: 'cycle', important: true,
    hourly: ramp([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.4, 0, 0]), note: 'Rinse cycle, about 35 min left' },
  { id: 'dishwasher', name: 'Dishwasher', room: 'Kitchen', model: 'HmIP-PSM-2', role: 'appliance', watts: 0, todayKwh: 1.1, mode: 'idle', important: true,
    hourly: ramp([0, 0, 1.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), note: 'Ran overnight at 02:00' },
  { id: 'fridge', name: 'Fridge-freezer', room: 'Kitchen', model: 'HmIP-PSM-2', role: 'appliance', watts: 62, todayKwh: 0.9, mode: 'always', important: false,
    hourly: ramp([0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]) },
  { id: 'ventilation', name: 'Ventilation unit', room: 'Hallway', model: 'HmIP-BSM', role: 'ventilation', watts: 38, todayKwh: 0.7, mode: 'always', important: true,
    hourly: ramp([0.02, 0.02, 0.02, 0.02, 0.02, 0.03, 0.06, 0.06, 0.05, 0.04, 0.04, 0.04, 0.05, 0.05, 0.04, 0.04, 0.04, 0.04]), note: 'Level 2 of 4' },
  { id: 'office', name: 'Home office', room: 'Study', model: 'HmIP-PSM-2', role: 'electronics', watts: 145, todayKwh: 0.8, mode: 'cycle', important: false,
    hourly: ramp([0, 0, 0, 0, 0, 0, 0, 0.1, 0.18, 0.15, 0.15, 0.1, 0.1, 0.15, 0.15, 0.15, 0.15, 0.15]) },
  { id: 'tv', name: 'TV and media', room: 'Living room', model: 'HmIP-PSM-2', role: 'electronics', watts: 8, todayKwh: 0.3, mode: 'idle', important: false,
    hourly: ramp([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0, 0, 0, 0.1, 0.1]) },
];

/** Whole-house meter (HmIP-ESI reading the smart meter). The sum of the plugs above is never mistaken for this. */
export const DEMO_METER = { model: 'HmIP-ESI-LED', todayKwh: 18.4, watts: 2140 };

export interface DemoRoom { room: string; temp: number; target: number; humidity: number; valves: number; battery: 'ok' | 'low'; model: string }
export const DEMO_ROOMS: DemoRoom[] = [
  { room: 'Living room', temp: 21.5, target: 21, humidity: 45, valves: 2, battery: 'ok', model: 'HmIP-eTRV-2' },
  { room: 'Kitchen', temp: 22.0, target: 21, humidity: 48, valves: 1, battery: 'ok', model: 'HmIP-eTRV-2' },
  { room: 'Bedroom', temp: 19.0, target: 18, humidity: 42, valves: 1, battery: 'low', model: 'HmIP-eTRV-2' },
  { room: "Kids' room", temp: 23.5, target: 21, humidity: 50, valves: 1, battery: 'ok', model: 'HmIP-WTH-2' },
];

export interface DemoWater { todayLitres: number; monthLitres: number; yearLitres: number; usualTodayLitres: number; pricePerM3: number; model: string; leakNightLitres: number }
/** Water has no native Homematic IP meter; a pulse counter (HmIP-FCI1) on a mechanical meter is the usual route. */
export const DEMO_WATER: DemoWater = { todayLitres: 214, monthLitres: 3920, yearLitres: 41800, usualTodayLitres: 188, pricePerM3: 4.2, model: 'HmIP-FCI1 on water meter', leakNightLitres: 0 };

export type AutomationKind = 'heating' | 'ventilation' | 'appliance' | 'ev' | 'lighting';
export interface DemoAutomation {
  id: string; at: string; until?: string; title: string; device: string; kind: AutomationKind;
  /** Where the schedule lives. Chit shows it; it never creates or edits one (read-only pilot). */
  source: 'HomematicIP profile' | 'Chit suggestion';
  why: string;
}
export const DEMO_AUTOMATIONS: DemoAutomation[] = [
  { id: 'a1', at: '05:30', until: '07:00', title: 'Bathroom warm-up to 22 °', device: 'Bathroom thermostat', kind: 'heating', source: 'HomematicIP profile', why: 'Weekday heating profile' },
  { id: 'a2', at: '10:00', until: '16:00', title: 'Ventilation to level 4', device: 'Ventilation unit', kind: 'ventilation', source: 'Chit suggestion', why: 'Solar is covering it' },
  { id: 'a3', at: '13:00', until: '15:00', title: 'Start dishwasher', device: 'Dishwasher', kind: 'appliance', source: 'Chit suggestion', why: 'Cheapest two hours left today' },
  { id: 'a4', at: '17:30', title: 'Living room to 21 °', device: 'Living room thermostat', kind: 'heating', source: 'HomematicIP profile', why: 'Evening profile' },
  { id: 'a5', at: '22:00', until: '23:30', title: 'Coast: heating setback to 18 °', device: 'All rooms', kind: 'heating', source: 'HomematicIP profile', why: 'Night setback' },
  { id: 'a6', at: '02:00', until: '05:00', title: 'Heat pump pre-heats the buffer', device: 'Heat pump', kind: 'heating', source: 'Chit suggestion', why: 'Tomorrow’s cheapest night hours' },
];

/** How a Homematic IP model reaches the Grid page. This is the "what do I get" table of the integration panel. */
export const HMIP_MAPPING: { model: string; what: string; shows: string; count: number }[] = [
  { model: 'HmIP-PSM-2 / HmIP-FSM16', what: 'Switching plug or flush actuator with power metering', shows: 'Watts now, kWh today, cost per device', count: 6 },
  { model: 'HmIP-ESI-LED', what: 'Smart-meter reader (IEC, Sensor/LED)', shows: 'Whole-house import, export, the real daily total', count: 1 },
  { model: 'HmIP-eTRV-2, HmIP-WTH-2', what: 'Radiator and wall thermostats', shows: 'Room temperature, target, heating profile, battery', count: 5 },
  { model: 'HmIP-FCI1', what: 'Contact interface on a water or gas meter', shows: 'Litres today, month, year; leak at night', count: 1 },
  { model: 'HmIP-STHD, HmIP-SWDO', what: 'Humidity and window sensors', shows: 'Ventilation hints, open-window heat loss', count: 3 },
];

export const FALLBACK_PRICE_EUR_PER_KWH = 0.31;   // demo only: used for per-device cost when no Tibber average is known
