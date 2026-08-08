#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import vm from "node:vm";

const [mainBundlePath, workerBundlePath, outputPrefix = "/tmp/controller-patch"] =
  process.argv.slice(2);

if (!mainBundlePath || !workerBundlePath) {
  console.error(
    "usage: node tools/validate.mjs <pml-main.bundle.js> <pml-simulation_worker.bundle.js> [output-prefix]",
  );
  process.exit(2);
}

const modPath = new URL("../1.0.1/main.mod.js", import.meta.url);
let modSource = readFileSync(modPath, "utf8");
modSource = modSource.replace(
  /import\s*\{[\s\S]*?\}\s*from\s*"[^"]+";\s*/,
  `class PolyMod {}
const MixinType = { INSERT: 3, REPLACEBETWEEN: 5, REMOVEBETWEEN: 6 };
`,
);
modSource = modSource.replace(
  "export let polyMod = new ControllerPatch();",
  "globalThis.polyMod = new ControllerPatch();",
);

const context = vm.createContext({ console });
vm.runInContext(modSource, context, { filename: "main.mod.js" });

const mainMixins = [];
const workerMixins = [];
assert.equal(context.polyMod.touchingPhysics, true, "mod must be marked non-vanilla-compatible");
assert.throws(
  () => context.polyMod.preInit({ registerGlobalMixin() {} }),
  /simulation-worker mixins/,
  "unsupported PML builds must fail before partial registration",
);
context.polyMod.preInit({
  registerGlobalMixin(mixin) {
    mainMixins.push(mixin);
  },
  registerSimWorkerMixin(mixin) {
    workerMixins.push(mixin);
  },
});

function occurrenceCount(source, token) {
  if (!token) return 0;
  const value = typeof token === "string" ? token : token.token;
  return source.split(value).length - 1;
}

function tokenIndex(source, token) {
  if (typeof token === "string") return source.indexOf(token);
  let from = 0;
  for (let occurrence = 1; occurrence <= token.occ; occurrence++) {
    const index = source.indexOf(token.token, from);
    if (index < 0) return -1;
    if (occurrence === token.occ) return index;
    from = index + token.token.length;
  }
  return -1;
}

function tokenLength(token) {
  return typeof token === "string" ? token.length : token.token.length;
}

function applyMixin(source, mixin, label) {
  if (mixin.type === 3) {
    const count = occurrenceCount(source, mixin.token);
    if (typeof mixin.token === "string") assert.equal(count, 1, `${label}: insert token count`);
    else assert.ok(count >= mixin.token.occ, `${label}: insert occurrence missing`);
    const index = tokenIndex(source, mixin.token);
    assert.notEqual(index, -1, `${label}: insert token missing`);
    return (
      source.slice(0, index + tokenLength(mixin.token)) +
      mixin.func +
      source.slice(index + tokenLength(mixin.token))
    );
  }

  assert.equal(mixin.type, 5, `${label}: unsupported mixin type`);
  const startCount = occurrenceCount(source, mixin.tokenStart);
  const endCount = occurrenceCount(source, mixin.tokenEnd);
  const expected = mixin.expectedOccurrences ?? 1;
  if (mixin.tokenStart === mixin.tokenEnd) {
    assert.equal(startCount, expected, `${label}: replacement token count`);
  } else {
    assert.equal(startCount, 1, `${label}: range start count`);
    assert.equal(endCount, 1, `${label}: range end count`);
  }
  const start = tokenIndex(source, mixin.tokenStart);
  const end = tokenIndex(source, mixin.tokenEnd);
  assert.notEqual(start, -1, `${label}: range start missing`);
  assert.notEqual(end, -1, `${label}: range end missing`);
  assert.ok(end >= start, `${label}: range ends before it starts`);
  const selected = source.substring(start, end + tokenLength(mixin.tokenEnd));
  return source.split(selected).join(mixin.func);
}

const fullMain = readFileSync(mainBundlePath, "utf8");
const marker = "let globalFunc = ";
const functionStart = fullMain.indexOf(marker) + marker.length;
const functionEnd = fullMain.indexOf(";\n    ActivePolyModLoader.preInitMods();", functionStart);
assert.ok(functionStart >= marker.length && functionEnd > functionStart, "PML globalFunc not found");

let globalFunction = fullMain.slice(functionStart, functionEnd);
for (const [index, mixin] of mainMixins.entries())
  globalFunction = applyMixin(globalFunction, mixin, `main mixin ${index + 1}`);

let worker = readFileSync(workerBundlePath, "utf8");
for (const [index, mixin] of workerMixins.entries())
  worker = applyMixin(worker, mixin, `worker mixin ${index + 1}`);

const transformedMain =
  fullMain.slice(0, functionStart) + globalFunction + fullMain.slice(functionEnd);
writeFileSync(`${outputPrefix}-main.bundle.js`, transformedMain);
writeFileSync(`${outputPrefix}-simulation_worker.bundle.js`, worker);

assert.ok(globalFunction.includes("window.__polytrackController=new ControllerManager()"));
assert.ok(globalFunction.includes("get analogSteering()"));
assert.ok(globalFunction.includes("const analogSteering = null == d"));
assert.ok(globalFunction.includes('(0, R.gn)(this, Da, "f").update();'));
assert.ok(globalFunction.includes("polytrackControllerAction === t"));
assert.ok(globalFunction.includes("return Promise.resolve({ uploadId: null"));
assert.ok(!globalFunction.includes('get("Invalid replay detected!")'));
assert.ok(!globalFunction.includes("polytrack-controller-focus-frame"));
assert.ok(!globalFunction.includes("polytrack-controller-menu-legend"));
assert.ok(worker.includes("controllerAnalogStep"));
assert.ok(worker.includes("rearLeftGrip < 0.4 && rearRightGrip < 0.4"));
assert.ok(worker.includes("Math.max(rearLeftGrip, rearRightGrip) > 0.9"));
assert.ok(worker.includes("e.analogSteering ? controllerAnalogStep(t, e) : n(t, e)"));
assert.ok(worker.includes("i.push(n(t, e))"), "non-realtime replay path must stay digital");
assert.equal((worker.match(/controllerAnalogStep\(t, e\)/g) ?? []).length, 1);
assert.ok(worker.includes('.TestDeterminism: {'), "PML determinism mixin anchor must remain");
assert.ok(worker.includes('"lib/polytrack_physics.js"'), "PML physics URL mixin anchor must remain");

console.log(
  `validated ${mainMixins.length} main mixins and ${workerMixins.length} worker mixins`,
);
