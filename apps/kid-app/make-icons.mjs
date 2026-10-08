// Dependency-free PNG icons (iOS needs PNG for apple-touch-icon). Run: node apps/kid-app/make-icons.mjs
import { deflateSync } from 'node:zlib';
import { writeFileSync } from 'node:fs';
const crcT = new Uint32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
const crc = b => { let c = ~0; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return ~c >>> 0; };
const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };
const star = (cx, cy, R, r) => Array.from({ length: 10 }, (_, i) => { const a = -Math.PI / 2 + i * Math.PI / 5, d = i % 2 ? r : R; return [cx + d * Math.cos(a), cy + d * Math.sin(a)]; });
const inside = (p, x, y) => { let o = false; for (let i = 0, j = p.length - 1; i < p.length; j = i++) if ((p[i][1] > y) !== (p[j][1] > y) && x < (p[j][0] - p[i][0]) * (y - p[i][1]) / (p[j][1] - p[i][1]) + p[i][0]) o = !o; return o; };
function png(S) {
  const poly = star(S / 2, S * 0.53, S * 0.34, S * 0.15), raw = Buffer.alloc((S * 4 + 1) * S), SS = 3;
  for (let y = 0; y < S; y++) { raw[y * (S * 4 + 1)] = 0;
    for (let x = 0; x < S; x++) { let hit = 0; for (let a = 0; a < SS; a++) for (let b = 0; b < SS; b++) hit += inside(poly, x + (a + .5) / SS, y + (b + .5) / SS);
      const t = (x + y) / (2 * S), f = hit / (SS * SS), o = y * (S * 4 + 1) + 1 + x * 4;
      const bg = [0 + 0 * t, 163 - 76 * t, 143 - 68 * t], fg = [255, 211, 77];
      for (let k = 0; k < 3; k++) raw[o + k] = Math.round(bg[k] * (1 - f) + fg[k] * f); raw[o + 3] = 255; } }
  const ih = Buffer.alloc(13); ih.writeUInt32BE(S, 0); ih.writeUInt32BE(S, 4); ih[8] = 8; ih[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}
const dir = new URL('.', import.meta.url);
writeFileSync(new URL('icon-180.png', dir), png(180)); writeFileSync(new URL('icon-512.png', dir), png(512));
