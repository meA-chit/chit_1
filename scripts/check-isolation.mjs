// Fails when a module reaches into another module (ADR-0006: no cross-module imports).
// Allowed: @chit/core (web), chit_server/chit_store public APIs (python), and a module's own files.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const modulesDir = join(root, 'modules');
const bad = [];

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    if (name === 'node_modules' || name === '__pycache__') continue;
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* walk(path);
    else if (/\.(ts|tsx|js|jsx|mjs|py)$/.test(name)) yield path;
  }
}

for (const moduleId of readdirSync(modulesDir)) {
  const moduleDir = join(modulesDir, moduleId);
  if (!statSync(moduleDir).isDirectory()) continue;
  for (const file of walk(moduleDir)) {
    const text = readFileSync(file, 'utf8');
    const rel = relative(root, file).split(sep).join('/');
    // relative imports that climb out of this module
    for (const match of text.matchAll(/(?:from|import)\s*\(?\s*['"]((?:\.\.\/)+[^'"]*)['"]/g)) {
      const resolved = join(file, '..', match[1]);
      if (!resolved.startsWith(moduleDir + sep) && resolved !== moduleDir) bad.push(`${rel}: relative import leaves module -> ${match[1]}`);
    }
    // direct references to another module's folder
    for (const match of text.matchAll(/modules[/.]([a-z-]+)[/.]/g)) {
      if (match[1] !== moduleId) bad.push(`${rel}: references module "${match[1]}"`);
    }
    // python: one module's server code loading another module's files
    if (file.endsWith('.py') && /load_file_module\([^)]*\.\.\//.test(text)) {
      bad.push(`${rel}: load_file_module must only load files of the same submodule`);
    }
  }
}

if (bad.length) {
  console.error('Module isolation violations:\n  ' + bad.join('\n  '));
  process.exit(1);
}
console.log('module isolation: ok');
