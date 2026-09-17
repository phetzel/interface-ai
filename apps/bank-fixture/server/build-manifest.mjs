// Build-time only. This manifest is outside dist and is never an HTTP route.
import { readFileSync, readdirSync, lstatSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
const hash = (file) => createHash('sha256').update(readFileSync(file)).digest('hex');
const walk = (directory) =>
  readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    const info = lstatSync(path);
    if (info.isSymbolicLink()) throw Error('Build inputs must not be symlinks');
    return info.isDirectory() ? walk(path) : [path];
  });
const spec = JSON.parse(readFileSync('package.json', 'utf8')).interfaceAiBuild;
const files = [...spec.files, ...spec.trees.flatMap(walk)].sort();
const sources = Object.fromEntries(files.map((path) => [path, hash(path)]));
const runtime = Object.fromEntries(
  [...walk('dist'), 'server/index.mjs', 'server/scenarios.mjs'].map((path) => [
    '/app/' + path,
    hash(path),
  ]),
);
writeFileSync(
  'build-manifest.json',
  JSON.stringify({ format: 'build-v1', sources, runtime }, null, 2) + '\n',
);
