// Dependency-free PNG icons (iOS needs PNG for apple-touch-icon) drawn from the Chit mark. Run: node apps/kid-app/make-icons.mjs
// Writes the kid app icons here and the hub's apple-touch icon into apps/web/public.
import { deflateSync } from 'node:zlib';
import { mkdirSync, writeFileSync } from 'node:fs';
const crcT = new Uint32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
const crc = b => { let c = ~0; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return ~c >>> 0; };
const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };

// The mark in a 100 x 100 box: five stars traced into a lowercase c, the first one lit.
const PATH = [[70.6, 25.5], [34, 22.3], [18, 50], [34, 77.7], [70.6, 74.5]];
const NODES = PATH.slice(1), LIT = PATH[0];
const segDist = (x, y, [ax, ay], [bx, by]) => { const dx = bx - ax, dy = by - ay, t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy))); return Math.hypot(x - ax - t * dx, y - ay - t * dy); };
const lerp = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const over = (bg, fg, f) => bg.map((v, i) => v * (1 - f) + fg[i] * f);

// `theme`: bg gradient corners, ink for lines and nodes, lit for the bright star.
function png(S, theme) {
  const k = S * 0.0082, ox = S / 2 - 50 * k, oy = S / 2 - 46 * k;   // centred, with room for a maskable crop
  const raw = Buffer.alloc((S * 4 + 1) * S), SS = 3;
  for (let y = 0; y < S; y++) { raw[y * (S * 4 + 1)] = 0;
    for (let x = 0; x < S; x++) {
      let px = lerp(theme.bg[0], theme.bg[1], (x + y) / (2 * S));
      let line = 0, nodes = 0, halo = 0, lit = 0;
      for (let a = 0; a < SS; a++) for (let b = 0; b < SS; b++) {
        const u = (x + (a + .5) / SS - ox) / k, v = (y + (b + .5) / SS - oy) / k;
        let d = Infinity; for (let i = 0; i < PATH.length - 1; i++) d = Math.min(d, segDist(u, v, PATH[i], PATH[i + 1]));
        if (d <= 1.75) line++;
        if (NODES.some(n => Math.hypot(u - n[0], v - n[1]) <= 6)) nodes++;
        const dl = Math.hypot(u - LIT[0], v - LIT[1]);
        if (Math.abs(dl - 17) <= 1.5) halo++;
        if (dl <= 10) lit++;
      }
      const n = SS * SS;
      px = over(px, theme.ink, Math.max(line, nodes) / n);
      px = over(px, theme.lit, 0.55 * halo / n);
      px = over(px, theme.lit, lit / n);
      const o = y * (S * 4 + 1) + 1 + x * 4;
      for (let c = 0; c < 3; c++) raw[o + c] = Math.round(px[c]); raw[o + 3] = 255;
    } }
  const ih = Buffer.alloc(13); ih.writeUInt32BE(S, 0); ih.writeUInt32BE(S, 4); ih[8] = 8; ih[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

const kids = { bg: [[0, 163, 143], [0, 87, 75]], ink: [255, 255, 255], lit: [255, 211, 77] };   // teal gradient, white stars, warm yellow
const hub = { bg: [[14, 21, 40], [5, 7, 13]], ink: [232, 238, 255], lit: [255, 200, 87] };      // the hub's void, its text colour, its amber
const kidDir = new URL('.', import.meta.url), hubDir = new URL('../web/public/', import.meta.url);
mkdirSync(hubDir, { recursive: true });
writeFileSync(new URL('icon-180.png', kidDir), png(180, kids)); writeFileSync(new URL('icon-512.png', kidDir), png(512, kids));
writeFileSync(new URL('icon-180.png', hubDir), png(180, hub)); writeFileSync(new URL('icon-512.png', hubDir), png(512, hub));
