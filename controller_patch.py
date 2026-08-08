#!/usr/bin/env python3
"""Patch the packaged PolyTrack ASAR with standard gamepad driving support.

The distribution contains compiled webpack bundles rather than the original
TypeScript sources.  This script performs guarded, exact replacements and
rebuilds the ASAR header (including per-file integrity records).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path


BLOCK_SIZE = 4 * 1024 * 1024


CONTROLLER_RUNTIME = r'''(()=>{
"use strict";
if(window.__polytrackController)return;

const STORAGE_KEY="polytrack_controller_bindings_v1";
const ACTION_NAMES=[
"VehicleAccelerate","VehicleTurnRight","VehicleBrake","VehicleTurnLeft",
"VehicleCheckpointReset","VehicleStartReset","VehicleCockpitCamera","ToggleUI","Pause",
"EditorRotatePart","EditorHeightModifier","EditorDelete","EditorMoveForwards","EditorMoveRight",
"EditorMoveBackwards","EditorMoveLeft","EditorRotateViewUp","EditorRotateViewDown",
"EditorRotateViewLeft","EditorRotateViewRight","EditorMoveDown","EditorMoveUp","EditorTest",
"EditorPick","ToggleFpsCounter","ToggleSpectatorCamera","SpectatorMoveForwards",
"SpectatorMoveRight","SpectatorMoveBackwards","SpectatorMoveLeft","SpectatorSpeedModifier",
"PreviewStepForward","PreviewStepBack"
];
const SETTINGS_ACTION_ORDER=[0,2,3,1,4,5,6,9,10,11,12,14,15,13,16,17,18,19,20,21,22,23,26,28,29,27,30,31,32,7,8,24,25];
const BUTTON_NAMES=["A","B","X","Y","LB","RB","LT","RT","Back","Start","Left Stick","Right Stick","D-pad Up","D-pad Down","D-pad Left","D-pad Right","Home"];
const AXIS_NAMES=["Left Stick X","Left Stick Y","Right Stick X","Right Stick Y"];
const MENU_ROOT_CLASSES=new Set(["menu-ui","settings-menu-ui","pause-screen-ui","message-box-ui","news-popup-ui","invite-ui","leaderboard-ui","multiplayer-ui","server-message-ui","session-end-ui","track-export-ui","track-info-ui","track-selection-ui"]);

function blankActions(){const actions={};for(const name of ACTION_NAMES)actions[name]=[null,null];return actions}
function defaults(){const actions=blankActions();actions.VehicleAccelerate[0]={kind:"button",index:7};actions.VehicleBrake[0]={kind:"button",index:6};actions.VehicleCheckpointReset[0]={kind:"button",index:2};actions.VehicleStartReset[0]={kind:"button",index:1};actions.VehicleCockpitCamera[0]={kind:"button",index:3};actions.ToggleUI[0]={kind:"button",index:8};return{version:1,actions,steering:{kind:"axis",index:0,invert:false,deadzone:.1}}}
function validDescriptor(value){if(null===value)return null;if(!value||"object"!==typeof value)return null;if("button"===value.kind&&Number.isInteger(value.index)&&value.index>=0&&value.index<64&&9!==value.index)return{kind:"button",index:value.index};if("axis"===value.kind&&Number.isInteger(value.index)&&value.index>=0&&value.index<16&&(1===value.direction||-1===value.direction))return{kind:"axis",index:value.index,direction:value.direction};return null}
function validate(value){if(!value||1!==value.version||!value.actions||"object"!==typeof value.actions)return defaults();const result=defaults();for(const name of ACTION_NAMES){const slots=value.actions[name];if(Array.isArray(slots)&&2===slots.length)result.actions[name]=[validDescriptor(slots[0]),validDescriptor(slots[1])]}
const steering=value.steering;if(null===steering)result.steering=null;else if(steering&&"axis"===steering.kind&&Number.isInteger(steering.index)&&steering.index>=0&&steering.index<16)result.steering={kind:"axis",index:steering.index,invert:!!steering.invert,deadzone:.1};return result}
function clone(value){return JSON.parse(JSON.stringify(value))}
function load(){try{const value=localStorage.getItem(STORAGE_KEY);return null===value?defaults():validate(JSON.parse(value))}catch(error){console.warn("Failed to load controller bindings",error);return defaults()}}
function save(value){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(validate(value)))}catch(error){console.warn("Failed to save controller bindings",error)}}
function visible(element){if(!element||!element.isConnected)return false;const style=getComputedStyle(element);if("none"===style.display||"hidden"===style.visibility||"0"===style.opacity)return false;const rect=element.getBoundingClientRect();return rect.width>0&&rect.height>0}
function buttonValue(pad,index){const button=pad?.buttons?.[index];return button?Math.max(Number(button.value)||0,button.pressed?1:0):0}
function allNeutral(pad){if(!pad)return true;for(const button of pad.buttons||[])if(Math.max(Number(button.value)||0,button.pressed?1:0)>.35)return false;for(const axis of pad.axes||[])if(Math.abs(Number(axis)||0)>.45)return false;return true}
function hasActivity(pad){if(!pad)return false;for(const button of pad.buttons||[])if(Math.max(Number(button.value)||0,button.pressed?1:0)>.2)return true;for(const axis of pad.axes||[])if(Math.abs(Number(axis)||0)>.2)return true;return false}
function labelDescriptor(value){if(!value)return "—";if("button"===value.kind)return BUTTON_NAMES[value.index]||`Button ${value.index}`;const base=AXIS_NAMES[value.index]||`Axis ${value.index}`;if(0===value.index||2===value.index)return `${base} ${value.direction<0?"Left":"Right"}`;if(1===value.index||3===value.index)return `${base} ${value.direction<0?"Up":"Down"}`;return `${base} ${value.direction<0?"−":"+"}`}
function labelSteering(value){if(!value)return "—";return`${AXIS_NAMES[value.index]||`Axis ${value.index}`}${value.invert?" (inverted)":""}`}

class ControllerManager{
constructor(){this.config=load();this.draft=null;this.activeIndex=null;this.pad=null;this.actionDown=new Array(ACTION_NAMES.length).fill(false);this.steering=0;this.capture=null;this.captureArmed=false;this.captureOverlay=null;this.settingsRoot=null;this.menuRoot=null;this.menuState={up:false,down:false,left:false,right:false,a:false,b:false};this.repeatAt={up:0,down:0,left:0,right:0};this.focused=null;this.preferredX=null;this.blockedButtons=new Set;this.blockedAxes=new Set;this.startDown=false;this.wasUi=false;this.decorateQueued=false;this.installStyle();this.installObservers();window.addEventListener("blur",()=>this.clear(),true);document.addEventListener("visibilitychange",()=>{if(document.hidden)this.clear()},true);window.addEventListener("keydown",event=>{if(this.capture&&"Escape"===event.code){event.preventDefault();event.stopImmediatePropagation();this.finishCapture(null,false)}},true);window.addEventListener("pointermove",event=>{if(this.capture)return;const root=this.findMenuRoot();const target=event.target instanceof Element?event.target.closest("button,input,textarea,select,a[href],[role=button]"):null;if(root&&target&&root.contains(target)&&visible(target)&&!target.disabled)this.setFocus(target)},true);requestAnimationFrame(time=>this.loop(time))}
installStyle(){const style=document.createElement("style");style.textContent=`.polytrack-controller-binding{min-width:92px}.setting.key-binding>.button-wrapper{flex-wrap:wrap}.polytrack-controller-separator{opacity:.65;padding:0 .25rem}.polytrack-controller-capture{position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.76)}.polytrack-controller-capture-panel{max-width:560px;padding:28px;border-radius:12px;background:#20242b;color:#fff;text-align:center;box-shadow:0 12px 48px #000}.polytrack-controller-capture-panel p{white-space:pre-line}.polytrack-controller-capture-panel .button-wrapper{display:flex;gap:12px;justify-content:center}.polytrack-analog-row{margin-top:.4rem}`;(document.head||document.documentElement).appendChild(style)}
installObservers(){const start=()=>{const observer=new MutationObserver(()=>this.queueDecorate());observer.observe(document.documentElement,{childList:true,subtree:true});this.queueDecorate()};document.documentElement?start():window.addEventListener("DOMContentLoaded",start,{once:true})}
queueDecorate(){if(this.decorateQueued)return;this.decorateQueued=true;queueMicrotask(()=>{this.decorateQueued=false;this.decorateSettings()})}
getPads(){if("function"!==typeof navigator.getGamepads)return[];try{return Array.from(navigator.getGamepads()||[]).filter(pad=>pad&&pad.connected&&("standard"===pad.mapping||""===pad.mapping))}catch{return[]}}
selectPad(){const pads=this.getPads();if(null!==this.activeIndex){const current=pads.find(pad=>pad.index===this.activeIndex);if(current)return current;this.activeIndex=null;this.releaseActions();this.steering=0;this.blockedButtons.clear();this.blockedAxes.clear()}
const active=pads.find(hasActivity);if(active){this.activeIndex=active.index;this.blockedButtons.clear();this.blockedAxes.clear();return active}return null}
emit(action,type){const event=new KeyboardEvent(type,{bubbles:true,cancelable:true});Object.defineProperty(event,"polytrackControllerAction",{value:action});window.dispatchEvent(event)}
releaseActions(){for(let action=0;action<this.actionDown.length;action++)if(this.actionDown[action]){this.actionDown[action]=false;this.emit(action,"keyup")}}
clear(){this.releaseActions();this.steering=0;if(this.pad)this.blockHeldInputs(this.pad,true);this.pad=null;this.startDown=false;this.resetMenuState()}
resetMenuState(){for(const key of Object.keys(this.menuState))this.menuState[key]=false;for(const key of Object.keys(this.repeatAt))this.repeatAt[key]=0}
blockHeldInputs(pad,all=false){if(!pad)return;const menuButtons=all?Array.from({length:pad.buttons?.length||0},(_,index)=>index):[0,1,12,13,14,15],menuAxes=all?Array.from({length:pad.axes?.length||0},(_,index)=>index):[0,1];for(const index of menuButtons)if(buttonValue(pad,index)>.35)this.blockedButtons.add(index);for(const index of menuAxes)if(Math.abs(Number(pad.axes?.[index])||0)>.35)this.blockedAxes.add(index)}
refreshBlocked(pad){for(const index of Array.from(this.blockedButtons))if(buttonValue(pad,index)<=.35)this.blockedButtons.delete(index);for(const index of Array.from(this.blockedAxes))if(Math.abs(Number(pad.axes?.[index])||0)<=.2)this.blockedAxes.delete(index)}
bindingDown(pad,binding,wasDown){if(!binding)return false;if("button"===binding.kind){if(9===binding.index||this.blockedButtons.has(binding.index))return false;return buttonValue(pad,binding.index)>(wasDown?.35:.5)}if(this.blockedAxes.has(binding.index))return false;const value=(Number(pad.axes?.[binding.index])||0)*binding.direction;return value>(wasDown?.45:.65)}
updateActions(pad){for(let action=0;action<ACTION_NAMES.length;action++){const slots=this.config.actions[ACTION_NAMES[action]]||[null,null],wasDown=this.actionDown[action],down=slots.some(binding=>this.bindingDown(pad,binding,wasDown));if(down!==wasDown){this.actionDown[action]=down;this.emit(action,down?"keydown":"keyup")}}}
updateSteering(pad){const binding=this.config.steering;if(!binding||this.blockedAxes.has(binding.index)){this.steering=0;return}let value=Number(pad.axes?.[binding.index])||0;if(binding.invert)value=-value;const deadzone=.1;this.steering=Math.abs(value)<=deadzone?0:Math.sign(value)*(Math.abs(value)-deadzone)/(1-deadzone);this.steering=Math.max(-1,Math.min(1,this.steering))}
getSteering(){return this.steering}
pressEscape(){window.dispatchEvent(new KeyboardEvent("keydown",{code:"Escape",bubbles:true,cancelable:true}));window.dispatchEvent(new KeyboardEvent("keyup",{code:"Escape",bubbles:true,cancelable:true}))}
updateStart(pad){const down=buttonValue(pad,9)>.5;if(down&&!this.startDown)this.pressEscape();this.startDown=down}
loop(time){this.pad=this.selectPad();this.updateStart(this.pad);const root=this.findMenuRoot(),ui=!!root;if(ui!==this.wasUi){this.releaseActions();this.steering=0;if(!ui)this.blockHeldInputs(this.pad,false);this.resetMenuState();this.wasUi=ui}if(root!==this.menuRoot){this.focused=null;this.preferredX=null;this.menuRoot=root;this.resetMenuState()}
if(this.pad)this.refreshBlocked(this.pad);if(this.capture)this.updateCapture(this.pad);else if(ui)this.updateMenu(this.pad,root,time);else if(this.pad){this.updateActions(this.pad);this.updateSteering(this.pad)}else{this.releaseActions();this.steering=0}
requestAnimationFrame(next=>this.loop(next))}
findMenuRoot(){const dialog=Array.from(document.querySelectorAll("dialog.message-box-ui[open]")).find(visible);if(dialog)return dialog;const priority=[".settings-menu-ui",".track-info-ui",".track-export-ui",".session-end-ui",".invite-ui",".news-popup-ui",".server-message-ui",".multiplayer-ui",".track-selection-ui",".leaderboard-ui",".menu-ui"];for(const selector of priority){const roots=Array.from(document.querySelectorAll(selector)).filter(element=>visible(element)&&this.candidates(element).length);if(roots.length)return roots[roots.length-1]}const roots=[];for(const element of document.querySelectorAll("[class]")){if(!visible(element))continue;const tokens=Array.from(element.classList);if(tokens.some(token=>MENU_ROOT_CLASSES.has(token)||token.endsWith("-menu-ui"))&&this.candidates(element).length)roots.push(element)}return roots.length?roots[0]:null}
candidates(root){return Array.from(root.querySelectorAll("button:not([disabled]),input:not([disabled]):not([type=hidden]),textarea:not([disabled]),select:not([disabled]),a[href],[role=button]" )).filter(visible)}
setFocus(element,preserveColumn=false){this.focused=element||null;if(this.focused){if(!preserveColumn){const rect=this.focused.getBoundingClientRect();this.preferredX=rect.left+rect.width/2}try{this.focused.focus({preventScroll:true})}catch{this.focused.focus()}this.focused.scrollIntoView({block:"nearest",inline:"nearest"})}}
isFocusValid(root){return!!(this.focused&&root&&root.contains(this.focused)&&this.candidates(root).includes(this.focused))}
ensureFocus(root){const candidates=this.candidates(root);if(this.isFocusValid(root))return this.focused;const onScreen=candidates.filter(element=>{const rect=element.getBoundingClientRect();return rect.bottom>0&&rect.right>0&&rect.top<innerHeight&&rect.left<innerWidth}),pool=onScreen.length?onScreen:candidates,first=pool.sort((a,b)=>{const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();return ar.top-br.top||ar.left-br.left})[0]||null;this.setFocus(first);return first}
buildRows(root){const items=this.candidates(root).map(element=>{const rect=element.getBoundingClientRect();return{element,rect,cx:rect.left+rect.width/2,cy:rect.top+rect.height/2}}).sort((a,b)=>a.cy-b.cy||a.cx-b.cx),rows=[];for(const item of items){let row=rows.find(candidate=>Math.abs(candidate.cy-item.cy)<=Math.max(10,Math.min(candidate.height,item.rect.height)*.45));if(!row){row={cy:item.cy,height:item.rect.height,items:[]};rows.push(row)}row.items.push(item);row.cy=row.items.reduce((sum,value)=>sum+value.cy,0)/row.items.length;row.height=Math.max(row.height,item.rect.height)}for(const row of rows)row.items.sort((a,b)=>a.cx-b.cx);return rows.sort((a,b)=>a.cy-b.cy)}
moveFocus(root,direction){const current=this.ensureFocus(root);if(!current)return;if("range"===current.type&&(direction==="left"||direction==="right")){const step=Number(current.step)||1,min=Number(current.min)||0,max=Number(current.max)||100,value=Math.max(min,Math.min(max,(Number(current.value)||0)+(direction==="left"?-step:step)));current.value=String(value);current.dispatchEvent(new Event("input",{bubbles:true}));current.dispatchEvent(new Event("change",{bubbles:true}));return}if(root.matches(".track-info-ui")){const panel=current.closest(".side-panel");if(direction==="right"&&!panel){const target=root.querySelector(".side-panel > button.watch:not([disabled]),.side-panel > button.play:not([disabled])");if(target){this.setFocus(target);return}}if(direction==="left"&&panel){const rect=current.getBoundingClientRect(),cy=rect.top+rect.height/2,left=this.candidates(root).filter(element=>!element.closest(".side-panel")).map(element=>{const target=element.getBoundingClientRect();return{element,cy:target.top+target.height/2}}).reduce((best,item)=>!best||Math.abs(item.cy-cy)<Math.abs(best.cy-cy)?item:best,null);if(left){this.setFocus(left.element);return}}if(panel&&(direction==="up"||direction==="down")){const rect=current.getBoundingClientRect(),cx=rect.left+rect.width/2,cy=rect.top+rect.height/2,sign=direction==="up"?-1:1,next=this.candidates(root).filter(element=>element!==current&&element.closest(".side-panel")).map(element=>{const target=element.getBoundingClientRect(),dx=target.left+target.width/2-cx,dy=target.top+target.height/2-cy;return{element,dx,dy}}).filter(item=>item.dy*sign>2).reduce((best,item)=>{const score=Math.abs(item.dy)+.25*Math.abs(item.dx);return!best||score<best.score?{element:item.element,score}:best},null);if(next){this.setFocus(next.element,true);return}}}const rows=this.buildRows(root),rowIndex=rows.findIndex(row=>row.items.some(item=>item.element===current));if(rowIndex<0)return;const row=rows[rowIndex],column=row.items.findIndex(item=>item.element===current);if(direction==="left"||direction==="right"){const next=column+(direction==="left"?-1:1);if(next>=0&&next<row.items.length)this.setFocus(row.items[next].element);return}const nextRowIndex=rowIndex+(direction==="up"?-1:1);if(nextRowIndex<0||nextRowIndex>=rows.length)return;const targetX=this.preferredX??row.items[column].cx,next=rows[nextRowIndex].items.reduce((best,item)=>!best||Math.abs(item.cx-targetX)<Math.abs(best.cx-targetX)?item:best,null);if(next)this.setFocus(next.element,true)}
repeatDirection(name,down,root,time){const was=this.menuState[name];if(down&&!was){this.moveFocus(root,name);this.repeatAt[name]=time+350}else if(down&&was&&time>=this.repeatAt[name]){this.moveFocus(root,name);this.repeatAt[name]=time+100}else if(!down)this.repeatAt[name]=0;this.menuState[name]=down}
pressBack(root){let target=root.querySelector("button.cancel:not([disabled])");if(!target&&root.matches("dialog.message-box-ui"))target=this.candidates(root)[0]||null;if(target&&visible(target))target.click();else this.pressEscape()}
updateMenu(pad,root,time){this.releaseActions();this.steering=0;if(!pad){this.resetMenuState();return}const hadFocus=this.isFocusValid(root);this.ensureFocus(root);const x=Number(pad.axes?.[0])||0,y=Number(pad.axes?.[1])||0;this.repeatDirection("up",buttonValue(pad,12)>.5||y<-.55,root,time);this.repeatDirection("down",buttonValue(pad,13)>.5||y>.55,root,time);this.repeatDirection("left",buttonValue(pad,14)>.5||x<-.55,root,time);this.repeatDirection("right",buttonValue(pad,15)>.5||x>.55,root,time);const a=buttonValue(pad,0)>.5,b=buttonValue(pad,1)>.5;if(a&&!this.menuState.a&&hadFocus&&this.isFocusValid(root)){const target=this.focused;if(target){if(target.matches("input[type=range]"))this.setFocus(target);else target.click()}}if(b&&!this.menuState.b)this.pressBack(root);this.menuState.a=a;this.menuState.b=b}
beginCapture(options){if(this.capture)return;this.capture=options;this.captureArmed=false;this.releaseActions();this.steering=0;const overlay=document.createElement("div");overlay.className="polytrack-controller-capture";const panel=document.createElement("div");panel.className="polytrack-controller-capture-panel";const title=document.createElement("h2");title.textContent=options.steering?"Bind analog steering":"Bind controller input";const message=document.createElement("p");message.textContent=options.steering?"Release all controls, then move the desired steering axis to the right.\nPress Escape to cancel.":"Release all controls, then press a button, trigger, D-pad direction, or move a stick.\nPress Escape to cancel.";const wrapper=document.createElement("div");wrapper.className="button-wrapper";const cancel=document.createElement("button");cancel.className="button cancel";cancel.textContent="Cancel";cancel.addEventListener("click",()=>this.finishCapture(null,false));const clear=document.createElement("button");clear.className="button";clear.textContent="Clear";clear.addEventListener("click",()=>this.finishCapture(null,true));wrapper.append(cancel,clear);panel.append(title,message,wrapper);overlay.appendChild(panel);document.body.appendChild(overlay);this.captureOverlay=overlay}
updateCapture(pad){if(!pad)return;if(!this.captureArmed){if(allNeutral(pad))this.captureArmed=true;return}if(this.capture.steering){for(let index=0;index<(pad.axes?.length||0);index++){const value=Number(pad.axes[index])||0;if(Math.abs(value)>.65){this.finishCapture({kind:"axis",index,invert:value<0,deadzone:.1},true);return}}return}
for(let index=0;index<(pad.buttons?.length||0);index++)if(buttonValue(pad,index)>.5){this.finishCapture({kind:"button",index},true);return}for(let index=0;index<(pad.axes?.length||0);index++){const value=Number(pad.axes[index])||0;if(Math.abs(value)>.65){this.finishCapture({kind:"axis",index,direction:value<0?-1:1},true);return}}}
finishCapture(value,apply){const capture=this.capture;this.capture=null;this.captureArmed=false;if(this.captureOverlay){this.captureOverlay.remove();this.captureOverlay=null}if(apply&&capture)capture.complete(value);this.resetMenuState();this.queueDecorate()}
decorateSettings(){const root=document.querySelector(".settings-menu-ui");if(!root){if(this.settingsRoot&&!this.settingsRoot.isConnected){this.settingsRoot=null;this.draft=null}return}if(root!==this.settingsRoot){this.settingsRoot=root;this.draft=clone(this.config);const apply=root.querySelector("button.apply"),cancel=root.querySelector("button.cancel"),reset=root.querySelector("button.reset");if(apply)apply.addEventListener("click",()=>{if(this.draft){this.config=validate(this.draft);save(this.config)}this.draft=null});if(cancel)cancel.addEventListener("click",()=>{this.draft=null});if(reset)reset.addEventListener("click",()=>{this.draft=defaults();this.queueDecorate()})}
if(!this.draft)this.draft=clone(this.config);const rows=Array.from(root.querySelectorAll(".setting.key-binding:not(.polytrack-analog-row)"));for(let rowIndex=0;rowIndex<Math.min(rows.length,SETTINGS_ACTION_ORDER.length);rowIndex++){const row=rows[rowIndex];if(row.dataset.controllerEnhanced)continue;row.dataset.controllerEnhanced="true";const action=SETTINGS_ACTION_ORDER[rowIndex],wrapper=row.querySelector(".button-wrapper");if(!wrapper)continue;const separator=document.createElement("span");separator.className="polytrack-controller-separator";separator.textContent="Controller";wrapper.appendChild(separator);for(let slot=0;slot<2;slot++){const button=document.createElement("button");button.className="button polytrack-controller-binding";const refresh=()=>{button.textContent=`GP: ${labelDescriptor(this.draft?.actions?.[ACTION_NAMES[action]]?.[slot])}`};refresh();button.addEventListener("click",()=>this.beginCapture({steering:false,complete:value=>{if(!this.draft)this.draft=clone(this.config);this.draft.actions[ACTION_NAMES[action]][slot]=value;refresh()}}));wrapper.appendChild(button)}}
if(!root.querySelector(".polytrack-analog-row")&&rows.length>=4){const row=document.createElement("div");row.className="setting key-binding polytrack-analog-row";const text=document.createElement("p");text.textContent="Analog steering";const wrapper=document.createElement("div");wrapper.className="button-wrapper";const bind=document.createElement("button");bind.className="button polytrack-controller-binding";const clear=document.createElement("button");clear.className="button";clear.textContent="Clear";const refresh=()=>{bind.textContent=`GP: ${labelSteering(this.draft?.steering)}`};refresh();bind.addEventListener("click",()=>this.beginCapture({steering:true,complete:value=>{if(!this.draft)this.draft=clone(this.config);this.draft.steering=value;refresh()}}));clear.addEventListener("click",()=>{if(!this.draft)this.draft=clone(this.config);this.draft.steering=null;refresh()});wrapper.append(bind,clear);row.append(text,wrapper);rows[3].insertAdjacentElement("afterend",row)}}}

window.__polytrackController=new ControllerManager();
})();'''


def read_asar(path: Path) -> tuple[dict, dict[str, bytes]]:
    raw = path.read_bytes()
    words = struct.unpack_from("<4I", raw, 0)
    json_size = words[3]
    header = json.loads(raw[16 : 16 + json_size].decode("utf-8"))
    data_base = 8 + words[1]
    files: dict[str, bytes] = {}

    def visit(node: dict, prefix: str = "") -> None:
        for name, entry in node.get("files", {}).items():
            file_path = f"{prefix}/{name}" if prefix else name
            if "files" in entry:
                visit(entry, file_path)
            else:
                offset = int(entry["offset"])
                size = int(entry["size"])
                files[file_path] = raw[data_base + offset : data_base + offset + size]

    visit(header)
    return header, files


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new)


def patch_main(source: str) -> str:
    source = replace_once(
        source,
        '(()=>{"use strict";',
        '(()=>{"use strict";' + CONTROLLER_RUNTIME,
        "controller runtime",
    )
    old_input = (
        'var Ut,Nt,zt,Dt,Bt,Gt,Ft,Ot;Ut=new WeakMap,Nt=new WeakMap,zt=new WeakMap,Dt=new WeakMap,Bt=new WeakMap,Gt=new WeakMap,Ft=new WeakMap,Ot=new WeakMap;const Wt=class{constructor(e){Ut.set(this,!1),Nt.set(this,!1),zt.set(this,!1),Dt.set(this,!1),Bt.set(this,!1),Gt.set(this,void 0),Ft.set(this,void 0),Ot.set(this,[]),window.addEventListener("keydown",(0,R.GG)(this,Gt,(t=>{e.checkKeyBinding(t,ge.A.VehicleAccelerate)?(this.up=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleTurnRight)?(this.right=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleBrake)?(this.down=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleTurnLeft)&&(this.left=!0,t.preventDefault())}),"f")),window.addEventListener("keyup",(0,R.GG)(this,Ft,(t=>{e.checkKeyBinding(t,ge.A.VehicleAccelerate)?this.up=!1:e.checkKeyBinding(t,ge.A.VehicleTurnRight)?this.right=!1:e.checkKeyBinding(t,ge.A.VehicleBrake)?this.down=!1:e.checkKeyBinding(t,ge.A.VehicleTurnLeft)&&(this.left=!1)}),"f"))}get up(){return(0,R.gn)(this,Ut,"f")}set up(e){if((0,R.gn)(this,Ut,"f")!=e){(0,R.GG)(this,Ut,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}get right(){return(0,R.gn)(this,Nt,"f")}set right(e){if((0,R.gn)(this,Nt,"f")!=e){(0,R.GG)(this,Nt,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}get down(){return(0,R.gn)(this,zt,"f")}set down(e){if((0,R.gn)(this,zt,"f")!=e){(0,R.GG)(this,zt,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}get left(){return(0,R.gn)(this,Dt,"f")}set left(e){if((0,R.gn)(this,Dt,"f")!=e){(0,R.GG)(this,Dt,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}get reset(){return(0,R.gn)(this,Bt,"f")}set reset(e){if((0,R.gn)(this,Bt,"f")!=e){(0,R.GG)(this,Bt,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}addChangeCallback(e){(0,R.gn)(this,Ot,"f").push(e)}removeChangeCallback(e){const t=(0,R.gn)(this,Ot,"f").indexOf(e);t>=0&&(0,R.gn)(this,Ot,"f").splice(t,1)}dispose(){window.removeEventListener("keydown",(0,R.gn)(this,Gt,"f")),window.removeEventListener("keyup",(0,R.gn)(this,Ft,"f"))}getControls(){return{up:this.up,right:this.right,down:this.down,left:this.left,reset:this.reset}}};var Vt;'
    )
    new_input = (
        'const Wt=class{constructor(e){this._up=!1,this._right=!1,this._down=!1,this._left=!1,this._reset=!1,this._steering=0,this._callbacks=[],this._keyDown=(t=>{e.checkKeyBinding(t,ge.A.VehicleAccelerate)?(this.up=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleTurnRight)?(this.right=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleBrake)?(this.down=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleTurnLeft)&&(this.left=!0,t.preventDefault())}),this._keyUp=(t=>{e.checkKeyBinding(t,ge.A.VehicleAccelerate)?this.up=!1:e.checkKeyBinding(t,ge.A.VehicleTurnRight)?this.right=!1:e.checkKeyBinding(t,ge.A.VehicleBrake)?this.down=!1:e.checkKeyBinding(t,ge.A.VehicleTurnLeft)&&(this.left=!1)}),window.addEventListener("keydown",this._keyDown),window.addEventListener("keyup",this._keyUp)}_notify(){for(const e of this._callbacks)e(this)}update(){this.steering=window.__polytrackController?.getSteering()??0}get up(){return this._up}set up(e){e=!!e,this._up!=e&&(this._up=e,this._notify())}get right(){return this._right}set right(e){e=!!e,this._right!=e&&(this._right=e,this._notify())}get down(){return this._down}set down(e){e=!!e,this._down!=e&&(this._down=e,this._notify())}get left(){return this._left}set left(e){e=!!e,this._left!=e&&(this._left=e,this._notify())}get reset(){return this._reset}set reset(e){e=!!e,this._reset!=e&&(this._reset=e,this._notify())}get steering(){return this._steering}set steering(e){e=Number.isFinite(e)?Math.max(-1,Math.min(1,e)):0,this._steering!=e&&(this._steering=e,this._notify())}get analogSteering(){return Math.abs(this.steering)>1e-4&&!this.right&&!this.left}addChangeCallback(e){this._callbacks.push(e)}removeChangeCallback(e){const t=this._callbacks.indexOf(e);t>=0&&this._callbacks.splice(t,1)}dispose(){window.removeEventListener("keydown",this._keyDown),window.removeEventListener("keyup",this._keyUp),this._steering=0}getControls(){return{up:this.up,right:this.right,down:this.down,left:this.left,reset:this.reset,steering:this.steering,analogSteering:this.analogSteering}}};var Vt;'
    )
    source = replace_once(source, old_input, new_input, "vehicle input manager")
    source = replace_once(
        source,
        'checkKeyBinding(e,t){const n=(0,R.gn)(this,hf,"f").get(t)??[];',
        'checkKeyBinding(e,t){if(e.polytrackControllerAction===t)return!0;const n=(0,R.gn)(this,hf,"f").get(t)??[];',
        "controller action dispatch",
    )
    source = replace_once(
        source,
        '(0,R.gn)(this,Za,"f")&&((0,R.gn)(this,ra,"f").show((0,R.gn)(this,Yr,"f").get("Invalid replay detected!"),(0,R.gn)(this,Yr,"f").get("Ok"),(()=>{(0,R.gn)(this,ra,"f").hide()})),(0,R.GG)(this,Za,!1,"f"))',
        '(0,R.gn)(this,Za,"f")&&(0,R.GG)(this,Za,!1,"f")',
        "disable invalid replay dialog",
    )
    source = replace_once(
        source,
        'submitLeaderboard(e,t,n,i,r,a,s,o){return new Promise(',
        'submitLeaderboard(e,t,n,i,r,a,s,o){if(!0)return Promise.resolve({uploadId:null,positionChange:null});return new Promise(',
        "disable leaderboard time uploads",
    )
    source = replace_once(
        source,
        'controlCar(e,t,n,i,a,s){const l={messageType:o.ControlCar,carId:e,up:t,right:n,down:i,left:a,reset:s};',
        'controlCar(e,t,n,i,a,s,c,d){const l={messageType:o.ControlCar,carId:e,up:t,right:n,down:i,left:a,reset:s,steering:c??0,analogSteering:!!d};',
        "controlCar message shape",
    )

    source = replace_once(
        source,
        '(0,l.gn)(this,X,"f")?.controlCar(e,(0,l.gn)(this,ne,"f").up,(0,l.gn)(this,ne,"f").right,(0,l.gn)(this,ne,"f").down,(0,l.gn)(this,ne,"f").left,(0,l.gn)(this,ne,"f").reset)',
        '(0,l.gn)(this,X,"f")?.controlCar(e,(0,l.gn)(this,ne,"f").up,(0,l.gn)(this,ne,"f").right,(0,l.gn)(this,ne,"f").down,(0,l.gn)(this,ne,"f").left,(0,l.gn)(this,ne,"f").reset,(0,l.gn)(this,ne,"f").steering,(0,l.gn)(this,ne,"f").analogSteering)',
        "initial car control",
    )
    source = replace_once(
        source,
        '(0,l.gn)(this,X,"f")?.controlCar(e,t.up,t.right,t.down,t.left,t.reset)',
        '(0,l.gn)(this,X,"f")?.controlCar(e,t.up,t.right,t.down,t.left,t.reset,t.steering,t.analogSteering)',
        "car control callback",
    )
    source = replace_once(
        source,
        '(0,l.gn)(this,X,"f")?.controlCar((0,l.gn)(this,ee,"f"),!1,!1,!1,!1,!1)',
        '(0,l.gn)(this,X,"f")?.controlCar((0,l.gn)(this,ee,"f"),!1,!1,!1,!1,!1,0,!1)',
        "disabled car control",
    )

    source = replace_once(
        source,
        '(0,l.gn)(this,X,"f")?.controlCar((0,l.gn)(this,ee,"f"),(0,l.gn)(this,ne,"f").up,(0,l.gn)(this,ne,"f").right,(0,l.gn)(this,ne,"f").down,(0,l.gn)(this,ne,"f").left,(0,l.gn)(this,ne,"f").reset)),(0,l.GG)(this,$,e,"f"))',
        '(0,l.gn)(this,X,"f")?.controlCar((0,l.gn)(this,ee,"f"),(0,l.gn)(this,ne,"f").up,(0,l.gn)(this,ne,"f").right,(0,l.gn)(this,ne,"f").down,(0,l.gn)(this,ne,"f").left,(0,l.gn)(this,ne,"f").reset,(0,l.gn)(this,ne,"f").steering,(0,l.gn)(this,ne,"f").analogSteering)),(0,l.GG)(this,$,e,"f"))',
        "reenabled car control",
    )

    source = replace_once(
        source,
        'update(e){const t=(0,R.gn)(this,jr,"m",ys).call(this);',
        'update(e){(0,R.gn)(this,Da,"f").update();const t=(0,R.gn)(this,jr,"m",ys).call(this);',
        "gamepad polling",
    )
    return source


def patch_worker(source: str) -> str:
    source = replace_once(
        source,
        'r=new jo,n={up:!1,right:!1,down:!1,left:!1,reset:!1,buffer:[]}',
        'r=new jo,n={up:!1,right:!1,down:!1,left:!1,reset:!1,steering:0,analogSteering:!1,buffer:[]}',
        "live control state",
    )
    source = replace_once(
        source,
        'e.push({id:l,controls:r,userControls:n,hasStarted:!1,frames:0,targetSimulationFrames:null,isPaused:!1})',
        'e.push({id:l,controls:r,userControls:n,hasStarted:!1,frames:0,targetSimulationFrames:null,isPaused:!1,nativeSteering:0,nativeSpeed:0,driftSteering:0,isDrifting:!1})',
        "car simulation state",
    )
    queued = 's.userControls.buffer.push({frame:r,up:t.up,right:t.right,down:t.down,left:t.left,reset:t.reset})'
    queued_count = source.count(queued)
    if queued_count != 2:
        raise RuntimeError(f"queued controller state: expected two matches, found {queued_count}")
    source = source.replace(
        queued,
        's.userControls.buffer.push({frame:r,up:t.up,right:t.right,down:t.down,left:t.left,reset:t.reset,steering:t.steering??0,analogSteering:!!t.analogSteering})',
    )
    source = replace_once(
        source,
        's.userControls.buffer[s.userControls.buffer.length-1]={frame:r,up:t.up,right:t.right,down:t.down,left:t.left,reset:t.reset}',
        's.userControls.buffer[s.userControls.buffer.length-1]={frame:r,up:t.up,right:t.right,down:t.down,left:t.left,reset:t.reset,steering:t.steering??0,analogSteering:!!t.analogSteering}',
        "replaced controller state",
    )
    source = replace_once(
        source,
        'null!=e&&(t.userControls.up=e.up,t.userControls.right=e.right,t.userControls.down=e.down,t.userControls.left=e.left,t.userControls.reset=e.reset)',
        'null!=e&&(t.userControls.up=e.up,t.userControls.right=e.right,t.userControls.down=e.down,t.userControls.left=e.left,t.userControls.reset=e.reset,t.userControls.steering=e.steering??0,t.userControls.analogSteering=!!e.analogSteering)',
        "applied controller state",
    )
    source = replace_once(
        source,
        'i.push({car:t,controls:{up:t.userControls.up,right:t.userControls.right,down:t.userControls.down,left:t.userControls.left,reset:t.userControls.reset}})',
        'i.push({car:t,controls:{up:t.userControls.up,right:t.userControls.right,down:t.userControls.down,left:t.userControls.left,reset:t.userControls.reset,steering:t.userControls.steering,analogSteering:t.userControls.analogSteering}})',
        "realtime controls",
    )
    old_update = 'function n(e,r){t.ccall("updateCarModel","void",["number","boolean","boolean","boolean","boolean","boolean","number"],[e.id,r.up,r.right,r.down,r.left,r.reset,i]);return new Uint8Array(t.HEAPU8.buffer,i,227).slice().buffer}'
    new_update = (
        # Keep the original digital bridge intact for keyboard input, replay
        # playback, and replay verification. Only live gamepad controls opt
        # into the analog bridge below.
        # The native physics ABI still exposes steering as two digital buttons.
        # It continuously moves the wheel toward zero when neither is held, so
        # feed back the serialized wheel angle and close a small position loop.
        # Native testing shows that the maximum wheel angle is 0.410258 radians
        # below 46 km/h, then falls as 155 / speedKmh**1.55.  Scale the analog
        # target by that same envelope so 20% stick remains 20% of the steering
        # range available at the current speed instead of saturating it.
        # When both rear wheels fall below 0.4 grip, smoothly blend back toward
        # the fixed low-speed target range.  Exit as soon as either rear wheel
        # rises above 0.9.  The native physics still owns the hard
        # wheel-angle cap, but partial stick now reaches more of that cap while
        # drifting, providing the countersteering authority the player expects.
        # The native output starts with a four-byte car id; omitting it reads a
        # speed byte as the flags byte and makes every stick position saturate.
        'function n(e,r){t.ccall("updateCarModel","void",["number","boolean","boolean","boolean","boolean","boolean","number"],[e.id,r.up,r.right,r.down,r.left,r.reset,i]);return new Uint8Array(t.HEAPU8.buffer,i,227).slice().buffer}function controllerAnalogStep(e,r){let s=r.right,o=r.left;const a=Math.abs(Number.isFinite(e.nativeSpeed)?e.nativeSpeed:0),l=Math.min(.410258,155/Math.pow(Math.max(1,a),1.55)),c=Number.isFinite(e.driftSteering)?e.driftSteering:0,h=l+(.410258-l)*c,d=Number.isFinite(r.steering)?-Math.max(-1,Math.min(1,r.steering))*h:0,u=Math.max(2e-5,.002*h);if(!s&&!o){const t=Number.isFinite(e.nativeSteering)?e.nativeSteering:0;d-t<-u?s=!0:d-t>u&&(o=!0)}t.ccall("updateCarModel","void",["number","boolean","boolean","boolean","boolean","boolean","number"],[e.id,r.up,s,r.down,o,r.reset,i]);const f=new DataView(t.HEAPU8.buffer);e.nativeSpeed=f.getFloat32(i+4+3,!0);let p=i+4+3+4,g=t.HEAPU8[p++];2&g&&(p+=3),p+=2+12+16;const m=t.HEAPU8[p++];p+=4*m;for(let e=0;e<4;e++)8<<e&g&&(p+=24);const A=32&g?f.getFloat32(p+56,!0):1,v=64&g?f.getFloat32(p+60,!0):1;e.isDrifting?Math.max(A,v)>.9&&(e.isDrifting=!1):A<.4&&v<.4&&(e.isDrifting=!0);const b=Number.isFinite(e.driftSteering)?e.driftSteering:0;e.driftSteering=Math.max(0,Math.min(1,b+(e.isDrifting?0.0125:-.004))),e.nativeSteering=f.getFloat32(p+64,!0);return new Uint8Array(t.HEAPU8.buffer,i,227).slice().buffer}'
    )
    source = replace_once(source, old_update, new_update, "native steering bridge")
    source = replace_once(
        source,
        'r.push(n(t,e))',
        'r.push(e.analogSteering?controllerAnalogStep(t,e):n(t,e))',
        "live analog steering selection",
    )
    return source


def update_integrity(entry: dict, data: bytes, offset: int) -> None:
    blocks = [
        hashlib.sha256(data[i : i + BLOCK_SIZE]).hexdigest()
        for i in range(0, len(data), BLOCK_SIZE)
    ]
    entry.clear()
    entry.update(
        {
            "size": len(data),
            "offset": str(offset),
            "integrity": {
                "algorithm": "SHA256",
                "hash": hashlib.sha256(data).hexdigest(),
                "blockSize": BLOCK_SIZE,
                "blocks": blocks,
            },
        }
    )


def rebuild_asar(template: dict, files: dict[str, bytes]) -> bytes:
    header = copy.deepcopy(template)
    offset = 0

    def visit(node: dict, prefix: str = "") -> None:
        nonlocal offset
        for name, entry in node.get("files", {}).items():
            file_path = f"{prefix}/{name}" if prefix else name
            if "files" in entry:
                visit(entry, file_path)
            else:
                data = files[file_path]
                update_integrity(entry, data, offset)
                offset += len(data)

    visit(header)
    header_json = json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    words = (4, len(header_json) + 9, len(header_json) + 5, len(header_json))
    payload = b"".join(files[path] for path in files)
    return struct.pack("<4I", *words) + header_json + b"\x00" + payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    header, files = read_asar(args.input)
    files["main.bundle.js"] = patch_main(files["main.bundle.js"].decode()).encode()
    files["simulation_worker.bundle.js"] = patch_worker(
        files["simulation_worker.bundle.js"].decode()
    ).encode()
    args.output.write_bytes(rebuild_asar(header, files))
    print(f"wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
