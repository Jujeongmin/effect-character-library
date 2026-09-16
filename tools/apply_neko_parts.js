#!/usr/bin/env node
// Applies the neko_boy_casual hair/ear/eye/eyebrow/mouth/tail template to
// another neko_boy-family character that shares the same rig (same head
// bone length/rotation, same 8 *_BoneFollower bones, same lack of a hair
// atlas). Copies the already-premultiplied part images, extends atlas.txt,
// and wires new slots + attachments into the character's own used skin.
const fs = require('fs');
const path = require('path');

const ROOT = 'C:/Users/anjsh/OneDrive/Desktop/effect-character-library';
const TEMPLATE = JSON.parse(fs.readFileSync(
  'C:/Users/anjsh/AppData/Local/Temp/claude/C--Users-anjsh-OneDrive-Desktop-effect-character-library/dffdf290-c498-4be6-a51b-24dfae2235a0/scratchpad/neko_template.json',
  'utf8'
));
const SRC_PARTS = path.join(ROOT, 'characters/humanoid/neko_boy_casual.spine/parts');

const PART_SIZES = {
  hair_01: [27, 46], hair_02: [50, 46], hair_03: [40, 91], hair_04: [66, 76],
  hair_05: [82, 63], hair_06: [94, 81], ear_back: [32, 50], ear_front: [28, 45],
  eye: [35, 18], eyebrow: [37, 7], mouth: [19, 5], tail: [94, 90],
};

// Exact relative draw order the user arranged by hand in
// tools/part_editor.html for neko_boy_casual (e.g. ear_back sits behind
// face/hair so it doesn't float on top of the fringe). Re-derive with:
//   node -e "const d=require('./characters/humanoid/neko_boy_casual.spine/skeleton.json'); ..."
// walking d.slots and recording, for each special part, the nearest
// preceding non-special ("native") slot name.
const ORDER_PLAN = [
  { after: 'leg_R', part: 'tail' },
  { after: 'body', part: 'hair_06' },
  { after: 'body', part: 'hair_05' },
  { after: 'body', part: 'ear_back' },
  { after: 'faceeffect', part: 'ear_front' },
  { after: 'faceeffect', part: 'hair_04' },
  { after: 'faceeffect', part: 'hair_01' },
  { after: 'faceeffect', part: 'hair_02' },
  { after: 'faceeffect', part: 'hair_03' },
  { after: 'faceeffect', part: 'eye' },
  { after: 'faceeffect', part: 'eyebrow' },
  { after: 'faceeffect', part: 'mouth' },
];
// Some costumes split the torso into body_01/body_02 instead of a plain
// "body" slot (e.g. paladin_armor) - fall back to whichever exists.
const ANCHOR_FALLBACKS = { body: ['body', 'body_01', 'body_02'] };

function applyTo(charId, skinName) {
  const dir = path.join(ROOT, 'characters/humanoid', charId + '.spine');
  const skeletonPath = path.join(dir, 'skeleton.json');
  const atlasPath = path.join(dir, 'atlas.txt');
  const partsDir = path.join(dir, 'parts');

  fs.mkdirSync(partsDir, { recursive: true });
  for (const name of Object.keys(PART_SIZES)) {
    fs.copyFileSync(path.join(SRC_PARTS, name + '.webp'), path.join(partsDir, name + '.webp'));
  }

  let atlas = fs.readFileSync(atlasPath, 'utf8').replace(/\s+$/, '');
  let add = '';
  for (const [name, [w, h]] of Object.entries(PART_SIZES)) {
    add += `\n\nparts/${name}.webp\nsize:${w},${h}\nfilter:Linear,Linear\npma:false\npart_${name}\nbounds:0,0,${w},${h}`;
  }
  fs.writeFileSync(atlasPath, atlas + add + '\n');

  const d = JSON.parse(fs.readFileSync(skeletonPath, 'utf8'));
  const skin = d.skins.find((s) => s.name === skinName);
  if (!skin) throw new Error(charId + ': skin ' + skinName + ' not found');
  if (!skin.attachments) skin.attachments = {};

  function resolveAnchor(anchor) {
    const candidates = ANCHOR_FALLBACKS[anchor] || [anchor];
    const found = candidates.find((c) => d.slots.some((s) => s.name === c));
    if (!found) throw new Error(charId + ': none of the anchor candidates found: ' + candidates.join(', '));
    return found;
  }

  // Insert each part right after its anchor, in ORDER_PLAN's sequence. A
  // cursor tracks the last part inserted after a given anchor so a second
  // part sharing that anchor lands after the first, not ahead of it -
  // otherwise repeated inserts at the same anchor index would come out
  // reversed relative to the plan.
  const cursor = {};
  for (const { after, part } of ORDER_PLAN) {
    const anchorNow = cursor[after] || resolveAnchor(after);
    const idx = d.slots.findIndex((s) => s.name === anchorNow);
    d.slots.splice(idx + 1, 0, { name: part, bone: TEMPLATE[part].bone, attachment: part });
    cursor[after] = part;
  }

  for (const [name, { att }] of Object.entries(TEMPLATE)) {
    skin.attachments[name] = { [name]: { name: 'part_' + name, x: att.x, y: att.y, rotation: att.rotation, width: att.width, height: att.height, scaleX: att.scaleX, scaleY: att.scaleY } };
  }

  fs.writeFileSync(skeletonPath, JSON.stringify(d));
  console.log(charId, 'done -', d.slots.length, 'slots');
}

module.exports = { applyTo };

if (require.main === module) {
  const [, , charId, skinName] = process.argv;
  if (!charId || !skinName) { console.error('usage: node apply_neko_parts.js <charId> <skinName>'); process.exit(1); }
  applyTo(charId, skinName);
}
