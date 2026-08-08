const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(
  new URL("../1.0.0/main.mod.js", `file://${__filename}`),
  "utf8",
);
const start = source.indexOf("function controllerRuntime() {");
const end = source.indexOf("\n}\n\nconst VEHICLE_INPUT", start);
assert.ok(start >= 0 && end > start, "controller runtime source not found");
const runtime = `${source.slice(start, end + 2)}\ncontrollerRuntime();`;

const emitted = [];
const storage = new Map();
global.window = global;
global.localStorage = {
  getItem(key) { return storage.has(key) ? storage.get(key) : null; },
  setItem(key, value) { storage.set(key, value); },
};
global.navigator = { getGamepads() { return []; } };
global.KeyboardEvent = class KeyboardEvent {
  constructor(type, init = {}) { this.type = type; Object.assign(this, init); }
};
window.addEventListener = () => {};
window.dispatchEvent = event => { emitted.push(event); return true; };
global.requestAnimationFrame = () => 1;
global.queueMicrotask = () => {};
global.innerWidth = 1920;
global.innerHeight = 1080;
global.MutationObserver = class { observe() {} };
global.Element = class {};
const inertElement = () => ({
  className: "", textContent: "", style: {}, dataset: {},
  appendChild() {}, append() {}, addEventListener() {}, remove() {},
});
global.document = {
  hidden: false,
  head: inertElement(),
  documentElement: inertElement(),
  body: inertElement(),
  createElement: inertElement,
  addEventListener() {},
  querySelector() { return null; },
  querySelectorAll() { return []; },
};
global.getComputedStyle = () => ({ display: "block", visibility: "visible", opacity: "1" });

vm.runInThisContext(runtime);
const manager = window.__polytrackController;
const buttons = Array.from({ length: 17 }, () => ({ value: 0, pressed: false }));
const pad = { index: 0, connected: true, mapping: "standard", buttons, axes: [0, 0, 0, 0] };

assert.equal(Object.keys(manager.config.actions).length, 33);
assert.equal(manager.config.actions.VehicleAccelerate[0].index, 7);
assert.equal(manager.config.actions.VehicleStartReset[0].index, 1);
assert.ok(manager.config.actions.EditorDelete.every(value => !value));
assert.ok(manager.config.actions.Pause.every(value => !value));

buttons[7] = { value: 0.7, pressed: false };
manager.updateActions(pad);
assert.equal(manager.actionDown[0], true);
assert.equal(emitted.at(-1).polytrackControllerAction, 0);
buttons[7] = { value: 0.4, pressed: false };
manager.updateActions(pad);
assert.equal(manager.actionDown[0], true);
buttons[7] = { value: 0.2, pressed: false };
manager.updateActions(pad);
assert.equal(manager.actionDown[0], false);

manager.config.actions.VehicleAccelerate[1] = { kind: "button", index: 0 };
buttons[7] = { value: 1, pressed: true };
buttons[0] = { value: 1, pressed: true };
manager.updateActions(pad);
buttons[7] = { value: 0, pressed: false };
manager.updateActions(pad);
assert.equal(manager.actionDown[0], true, "one released slot must not release the action");
buttons[0] = { value: 0, pressed: false };
manager.updateActions(pad);
assert.equal(manager.actionDown[0], false);

pad.axes[0] = 0.28;
manager.updateSteering(pad);
assert.ok(Math.abs(manager.getSteering() - 0.2) < 1e-9);
pad.axes[0] = 0.55;
manager.updateSteering(pad);
assert.ok(Math.abs(manager.getSteering() - 0.5) < 1e-9);
pad.axes[0] = 1;
manager.updateSteering(pad);
assert.equal(manager.getSteering(), 1);
manager.config.steering.invert = true;
pad.axes[0] = 0.28;
manager.updateSteering(pad);
assert.ok(Math.abs(manager.getSteering() + 0.2) < 1e-9);
manager.config.steering.invert = false;

buttons[0] = { value: 1, pressed: true };
buttons[7] = { value: 1, pressed: true };
pad.axes[0] = 0.8;
manager.blockHeldInputs(pad, false);
assert.ok(manager.blockedButtons.has(0));
assert.ok(!manager.blockedButtons.has(7));
assert.ok(manager.blockedAxes.has(0));

const beforeStart = emitted.length;
buttons[9] = { value: 1, pressed: true };
manager.updateStart(pad);
assert.equal(emitted.length, beforeStart + 2);
assert.equal(emitted.at(-2).code, "Escape");
manager.updateStart(pad);
assert.equal(emitted.length, beforeStart + 2);
assert.equal(manager.bindingDown(pad, { kind: "button", index: 9 }, false), false);

const fake = (name, left, top) => ({
  name,
  type: "button",
  classList: {
    values: new Set(),
    add(...values) { values.forEach(value => this.values.add(value)); },
    remove(...values) { values.forEach(value => this.values.delete(value)); },
    contains(value) { return this.values.has(value); },
  },
  getBoundingClientRect() {
    return { left, top, width: 80, height: 40, right: left + 80, bottom: top + 40 };
  },
  focus() {},
  scrollIntoView() {},
  matches() { return false; },
  closest() { return null; },
});
const a = fake("a", 0, 0);
const b = fake("b", 120, 0);
const c = fake("c", 0, 80);
const d = fake("d", 120, 80);
const root = { contains() { return true; }, matches() { return false; } };
manager.candidates = () => [a, b, c, d];
manager.setFocus(a);
assert.equal(a.classList.contains("polytrack-controller-focused"), true);
manager.moveFocus(root, "right");
assert.equal(manager.focused, b);
assert.equal(a.classList.contains("polytrack-controller-focused"), false);
assert.equal(b.classList.contains("polytrack-controller-focused"), true);
manager.moveFocus(root, "down");
assert.equal(manager.focused, d);
manager.moveFocus(root, "left");
assert.equal(manager.focused, c);
manager.moveFocus(root, "up");
assert.equal(manager.focused, a);

let clicks = 0;
const first = fake("first", 0, 0);
first.click = () => { clicks += 1; };
const activationRoot = {
  contains() { return true; },
  matches() { return false; },
  querySelector() { return null; },
};
manager.candidates = () => [first];
manager.setFocus(null);
manager.resetMenuState();
buttons[0] = { value: 0, pressed: false };
manager.refreshBlocked(pad);
buttons[0] = { value: 1, pressed: true };
manager.updateMenu(pad, activationRoot, 0);
assert.equal(clicks, 0, "A must not activate a newly chosen fallback target");
buttons[0] = { value: 0, pressed: false };
manager.updateMenu(pad, activationRoot, 16);
buttons[0] = { value: 1, pressed: true };
manager.updateMenu(pad, activationRoot, 32);
assert.equal(clicks, 1);

manager.resetMenuState();
manager.markMenuTransition(pad, 100);
assert.equal(manager.menuButtonDown(pad, 0, 100), false, "transition debounce must suppress held A");
buttons[0] = { value: 0, pressed: false };
manager.refreshBlocked(pad);
assert.equal(manager.menuButtonDown(pad, 0, 200), false, "cooldown must survive a quick release");
assert.equal(manager.menuButtonDown(pad, 0, 300), false);
buttons[0] = { value: 1, pressed: true };
assert.equal(manager.menuButtonDown(pad, 0, 300), true, "A must re-arm after the cooldown");

const leftEntry = fake("leaderboard-entry", 50, 300);
const watch = fake("watch", 700, 700);
watch.closest = selector => selector === ".side-panel" ? {} : null;
const trackRoot = {
  contains() { return true; },
  matches(selector) { return selector === ".track-info-ui"; },
  querySelector() { return watch; },
};
manager.candidates = () => [leftEntry, watch];
manager.setFocus(leftEntry);
manager.moveFocus(trackRoot, "right");
assert.equal(manager.focused, watch);

console.log("controller runtime unit checks passed");
