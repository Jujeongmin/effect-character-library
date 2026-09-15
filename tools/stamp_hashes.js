#!/usr/bin/env node
// Writes a short content hash next to every file a manifest points at.
// Loaders append it as ?v=<hash>, so a sheet re-uploaded under the same path
// never pairs with a stale cached copy (GitHub Pages serves max-age=600).
// Re-run after changing any image or Spine export:  node tools/stamp_hashes.js
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const root = path.resolve(__dirname, '..');
const read = (rel) => fs.readFileSync(path.join(root, rel));

function hash(buffers) {
  const h = crypto.createHash('sha1');
  buffers.forEach((b) => h.update(b));
  return h.digest('hex').slice(0, 10);
}

function stampClip(clip) {
  if (clip && clip.file) clip.hash = hash([read(clip.file)]);
}

function stampSpine(spec) {
  const dir = path.posix.dirname(spec.atlas);
  const pages = read(spec.atlas).toString('utf8').split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => /\.(png|webp|jpe?g)$/i.test(l));
  spec.hash = hash([read(spec.skeleton), read(spec.atlas)]
    .concat(pages.map((p) => read(path.posix.join(dir, p)))));
  (spec.variants || []).forEach(stampSpine);
}

function rewrite(rel, fn) {
  const file = path.join(root, rel);
  const raw = fs.readFileSync(file, 'utf8');
  const manifest = JSON.parse(raw);
  fn(manifest);
  const eol = raw.includes('\r\n') ? '\r\n' : '\n';
  const trailing = /\n$/.test(raw) ? eol : '';
  fs.writeFileSync(file, JSON.stringify(manifest, null, 2).replace(/\n/g, eol) + trailing);
  console.log('stamped', rel, manifest.assets.length, 'assets');
}

rewrite('effects.json', (m) => m.assets.forEach(stampClip));
for (const rel of ['characters.json', 'icons.json']) {
  rewrite(rel, (m) => m.assets.forEach((a) => {
    if (a.animations) Object.values(a.animations).forEach(stampClip);
    else stampClip(a);
    if (a.spine) stampSpine(a.spine);
  }));
}
