import {
  PolyMod,
  MixinType,
} from "https://cdn.polymodloader.com/pml/PolyModLoader/0.6.2/PolyTypes.js";

function controllerRuntime() {
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
const MENU_ROOT_CLASSES=new Set(["menu-ui","settings-menu-ui","pause-screen-ui","message-box-ui","news-popup-ui","invite-ui","leaderboard-ui","multiplayer-ui","server-message-ui","session-end-ui","track-export-ui","track-info-ui","track-selection-ui","library-div"]);
const FOCUS_CLASS="polytrack-controller-focused";
const MENU_DEBOUNCE_MS=180;

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
constructor(){this.config=load();this.draft=null;this.activeIndex=null;this.pad=null;this.actionDown=new Array(ACTION_NAMES.length).fill(false);this.steering=0;this.capture=null;this.captureArmed=false;this.captureOverlay=null;this.settingsRoot=null;this.menuRoot=null;this.menuState={up:false,down:false,left:false,right:false,a:false,b:false};this.repeatAt={up:0,down:0,left:0,right:0};this.focused=null;this.preferredX=null;this.blockedButtons=new Set;this.blockedAxes=new Set;this.menuDebounceUntil=0;this.startDown=false;this.wasUi=false;this.decorateQueued=false;this.installStyle();this.installObservers();window.addEventListener("blur",()=>this.clear(),true);document.addEventListener("visibilitychange",()=>{if(document.hidden)this.clear()},true);window.addEventListener("keydown",event=>{if(this.capture&&"Escape"===event.code){event.preventDefault();event.stopImmediatePropagation();this.finishCapture(null,false)}},true);window.addEventListener("pointermove",event=>{if(this.capture)return;const root=this.findMenuRoot();const target=event.target instanceof Element?event.target.closest("button,input,textarea,select,a[href],[role=button]"):null;if(root&&target&&root.contains(target)&&visible(target)&&!target.disabled)this.setFocus(target)},true);requestAnimationFrame(time=>this.loop(time))}
installStyle(){const style=document.createElement("style");style.textContent=`.polytrack-controller-binding{min-width:92px}.setting.key-binding>.button-wrapper{flex-wrap:wrap}.polytrack-controller-separator{opacity:.65;padding:0 .25rem}.polytrack-controller-capture{position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.76)}.polytrack-controller-capture-panel{max-width:560px;padding:28px;border-radius:12px;background:#20242b;color:#fff;text-align:center;box-shadow:0 12px 48px #000}.polytrack-controller-capture-panel p{white-space:pre-line}.polytrack-controller-capture-panel .button-wrapper{display:flex;gap:12px;justify-content:center}.polytrack-analog-row{margin-top:.4rem}.polytrack-controller-focused{outline:2px solid var(--text-color)!important;outline-offset:2px!important}.polytrack-controller-focused.button,.polytrack-controller-focused[role="button"],.polytrack-controller-focused[href]{background-color:var(--button-hover-color)!important;text-decoration:underline!important}.polytrack-controller-focused.button::after{width:100%}.polytrack-controller-focused[type="range"]{accent-color:var(--text-color)}`;(document.head||document.documentElement).appendChild(style)}
installObservers(){const start=()=>{const observer=new MutationObserver(()=>this.queueDecorate());observer.observe(document.documentElement,{childList:true,subtree:true});this.queueDecorate()};document.documentElement?start():window.addEventListener("DOMContentLoaded",start,{once:true})}
queueDecorate(){if(this.decorateQueued)return;this.decorateQueued=true;queueMicrotask(()=>{this.decorateQueued=false;this.decorateSettings()})}
getPads(){if("function"!==typeof navigator.getGamepads)return[];try{return Array.from(navigator.getGamepads()||[]).filter(pad=>pad&&pad.connected&&("standard"===pad.mapping||""===pad.mapping))}catch{return[]}}
selectPad(){const pads=this.getPads();if(null!==this.activeIndex){const current=pads.find(pad=>pad.index===this.activeIndex);if(current)return current;this.activeIndex=null;this.releaseActions();this.steering=0;this.blockedButtons.clear();this.blockedAxes.clear()}
const active=pads.find(hasActivity);if(active){this.activeIndex=active.index;this.blockedButtons.clear();this.blockedAxes.clear();return active}return null}
emit(action,type){const event=new KeyboardEvent(type,{bubbles:true,cancelable:true});Object.defineProperty(event,"polytrackControllerAction",{value:action});window.dispatchEvent(event)}
releaseActions(){for(let action=0;action<this.actionDown.length;action++)if(this.actionDown[action]){this.actionDown[action]=false;this.emit(action,"keyup")}}
clear(){this.releaseActions();this.steering=0;if(this.pad)this.blockHeldInputs(this.pad,true);this.pad=null;this.startDown=false;this.menuDebounceUntil=0;this.resetMenuState()}
resetMenuState(){for(const key of Object.keys(this.menuState))this.menuState[key]=false;for(const key of Object.keys(this.repeatAt))this.repeatAt[key]=0}
blockHeldInputs(pad,all=false){if(!pad)return;const menuButtons=all?Array.from({length:pad.buttons?.length||0},(_,index)=>index):[0,1,12,13,14,15],menuAxes=all?Array.from({length:pad.axes?.length||0},(_,index)=>index):[0,1];for(const index of menuButtons)if(buttonValue(pad,index)>.35)this.blockedButtons.add(index);for(const index of menuAxes)if(Math.abs(Number(pad.axes?.[index])||0)>.35)this.blockedAxes.add(index)}
refreshBlocked(pad){for(const index of Array.from(this.blockedButtons))if(buttonValue(pad,index)<=.35)this.blockedButtons.delete(index);for(const index of Array.from(this.blockedAxes))if(Math.abs(Number(pad.axes?.[index])||0)<=.2)this.blockedAxes.delete(index)}
markMenuTransition(pad,time){this.blockHeldInputs(pad,false);this.menuDebounceUntil=Math.max(this.menuDebounceUntil,(Number.isFinite(time)?time:0)+MENU_DEBOUNCE_MS)}
menuButtonDown(pad,index,time){return time>=this.menuDebounceUntil&&!this.blockedButtons.has(index)&&buttonValue(pad,index)>.5}
menuAxisValue(pad,index,time){return time>=this.menuDebounceUntil&&!this.blockedAxes.has(index)?Number(pad.axes?.[index])||0:0}
bindingDown(pad,binding,wasDown){if(!binding)return false;if("button"===binding.kind){if(9===binding.index||this.blockedButtons.has(binding.index))return false;return buttonValue(pad,binding.index)>(wasDown?.35:.5)}if(this.blockedAxes.has(binding.index))return false;const value=(Number(pad.axes?.[binding.index])||0)*binding.direction;return value>(wasDown?.45:.65)}
updateActions(pad){for(let action=0;action<ACTION_NAMES.length;action++){const slots=this.config.actions[ACTION_NAMES[action]]||[null,null],wasDown=this.actionDown[action],down=slots.some(binding=>this.bindingDown(pad,binding,wasDown));if(down!==wasDown){this.actionDown[action]=down;this.emit(action,down?"keydown":"keyup")}}}
updateSteering(pad){const binding=this.config.steering;if(!binding||this.blockedAxes.has(binding.index)){this.steering=0;return}let value=Number(pad.axes?.[binding.index])||0;if(binding.invert)value=-value;const deadzone=.1;this.steering=Math.abs(value)<=deadzone?0:Math.sign(value)*(Math.abs(value)-deadzone)/(1-deadzone);this.steering=Math.max(-1,Math.min(1,this.steering))}
getSteering(){return this.steering}
pressEscape(){window.dispatchEvent(new KeyboardEvent("keydown",{code:"Escape",bubbles:true,cancelable:true}));window.dispatchEvent(new KeyboardEvent("keyup",{code:"Escape",bubbles:true,cancelable:true}))}
updateStart(pad){const down=buttonValue(pad,9)>.5;if(down&&!this.startDown)this.pressEscape();this.startDown=down}
loop(time){this.pad=this.selectPad();this.updateStart(this.pad);const root=this.findMenuRoot(),ui=!!root&&this.candidates(root).length>0;if(ui!==this.wasUi){this.releaseActions();this.steering=0;if(!ui)this.blockHeldInputs(this.pad,false);this.resetMenuState();this.wasUi=ui}const menuChanged=root!==this.menuRoot||!!(ui&&this.focused&&!this.isFocusValid(root));if(menuChanged){if(this.pad)this.markMenuTransition(this.pad,time);this.setFocus(null);this.preferredX=null;this.menuRoot=root;this.resetMenuState()}if(ui)this.ensureFocus(root);
if(this.pad)this.refreshBlocked(this.pad);if(this.capture)this.updateCapture(this.pad);else if(ui)this.updateMenu(this.pad,root,time);else if(this.pad){this.updateActions(this.pad);this.updateSteering(this.pad)}else{this.releaseActions();this.steering=0}
requestAnimationFrame(next=>this.loop(next))}
findMenuRoot(){const dialogs=Array.from(document.querySelectorAll("dialog[open]")).filter(visible);if(dialogs.length)return dialogs[dialogs.length-1];const priority=[".settings-menu-ui",".library-div",".track-info-ui",".track-export-ui",".session-end-ui",".invite-ui",".news-popup-ui",".server-message-ui",".multiplayer-ui",".track-selection-ui",".leaderboard-ui",".menu-ui"];let emptyFallback=null;for(const selector of priority){const roots=Array.from(document.querySelectorAll(selector)).filter(visible);if(!roots.length)continue;const withControls=roots.filter(element=>this.candidates(element).length);if(withControls.length)return withControls[withControls.length-1];emptyFallback=roots[roots.length-1]}const roots=[];for(const element of document.querySelectorAll("[class]")){if(!visible(element))continue;const tokens=Array.from(element.classList);if(tokens.some(token=>MENU_ROOT_CLASSES.has(token)||token.endsWith("-menu-ui"))){if(this.candidates(element).length)roots.push(element);else emptyFallback=element}}return roots.length?roots[0]:emptyFallback}
candidates(root){return Array.from(root.querySelectorAll("button:not([disabled]),input:not([disabled]):not([type=hidden]),textarea:not([disabled]),select:not([disabled]),a[href],[role=button]" )).filter(visible)}
setFocus(element,preserveColumn=false){const previous=this.focused;if(previous&&previous!==element)previous.classList?.remove?.(FOCUS_CLASS);this.focused=element||null;if(this.focused){this.focused.classList?.add?.(FOCUS_CLASS);if(!preserveColumn){const rect=this.focused.getBoundingClientRect();this.preferredX=rect.left+rect.width/2}try{this.focused.focus({preventScroll:true})}catch{this.focused.focus()}this.focused.scrollIntoView({block:"nearest",inline:"nearest"})}}
isFocusValid(root){return!!(this.focused&&root&&root.contains(this.focused)&&this.candidates(root).includes(this.focused))}
ensureFocus(root){const candidates=this.candidates(root);if(this.isFocusValid(root)){this.focused.classList?.add?.(FOCUS_CLASS);return this.focused}const onScreen=candidates.filter(element=>{const rect=element.getBoundingClientRect();return rect.bottom>0&&rect.right>0&&rect.top<innerHeight&&rect.left<innerWidth}),pool=onScreen.length?onScreen:candidates,first=pool.sort((a,b)=>{const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();return ar.top-br.top||ar.left-br.left})[0]||null;this.setFocus(first);return first}
buildRows(root){const items=this.candidates(root).map(element=>{const rect=element.getBoundingClientRect();return{element,rect,cx:rect.left+rect.width/2,cy:rect.top+rect.height/2}}).sort((a,b)=>a.cy-b.cy||a.cx-b.cx),rows=[];for(const item of items){let row=rows.find(candidate=>Math.abs(candidate.cy-item.cy)<=Math.max(10,Math.min(candidate.height,item.rect.height)*.45));if(!row){row={cy:item.cy,height:item.rect.height,items:[]};rows.push(row)}row.items.push(item);row.cy=row.items.reduce((sum,value)=>sum+value.cy,0)/row.items.length;row.height=Math.max(row.height,item.rect.height)}for(const row of rows)row.items.sort((a,b)=>a.cx-b.cx);return rows.sort((a,b)=>a.cy-b.cy)}
moveFocus(root,direction){const current=this.ensureFocus(root);if(!current)return;if("range"===current.type&&(direction==="left"||direction==="right")){const step=Number(current.step)||1,min=Number(current.min)||0,max=Number(current.max)||100,value=Math.max(min,Math.min(max,(Number(current.value)||0)+(direction==="left"?-step:step)));current.value=String(value);current.dispatchEvent(new Event("input",{bubbles:true}));current.dispatchEvent(new Event("change",{bubbles:true}));return}if(root.matches(".track-info-ui")){const panel=current.closest(".side-panel");if(direction==="right"&&!panel){const target=root.querySelector(".side-panel > button.watch:not([disabled]),.side-panel > button.play:not([disabled])");if(target){this.setFocus(target);return}}if(direction==="left"&&panel){const rect=current.getBoundingClientRect(),cy=rect.top+rect.height/2,left=this.candidates(root).filter(element=>!element.closest(".side-panel")).map(element=>{const target=element.getBoundingClientRect();return{element,cy:target.top+target.height/2}}).reduce((best,item)=>!best||Math.abs(item.cy-cy)<Math.abs(best.cy-cy)?item:best,null);if(left){this.setFocus(left.element);return}}if(panel&&(direction==="up"||direction==="down")){const rect=current.getBoundingClientRect(),cx=rect.left+rect.width/2,cy=rect.top+rect.height/2,sign=direction==="up"?-1:1,next=this.candidates(root).filter(element=>element!==current&&element.closest(".side-panel")).map(element=>{const target=element.getBoundingClientRect(),dx=target.left+target.width/2-cx,dy=target.top+target.height/2-cy;return{element,dx,dy}}).filter(item=>item.dy*sign>2).reduce((best,item)=>{const score=Math.abs(item.dy)+.25*Math.abs(item.dx);return!best||score<best.score?{element:item.element,score}:best},null);if(next){this.setFocus(next.element,true);return}}}const rows=this.buildRows(root),rowIndex=rows.findIndex(row=>row.items.some(item=>item.element===current));if(rowIndex<0)return;const row=rows[rowIndex],column=row.items.findIndex(item=>item.element===current);if(direction==="left"||direction==="right"){const next=column+(direction==="left"?-1:1);if(next>=0&&next<row.items.length)this.setFocus(row.items[next].element);return}const nextRowIndex=rowIndex+(direction==="up"?-1:1);if(nextRowIndex<0||nextRowIndex>=rows.length)return;const targetX=this.preferredX??row.items[column].cx,next=rows[nextRowIndex].items.reduce((best,item)=>!best||Math.abs(item.cx-targetX)<Math.abs(best.cx-targetX)?item:best,null);if(next)this.setFocus(next.element,true)}
repeatDirection(name,down,root,time){const was=this.menuState[name];if(down&&!was){this.moveFocus(root,name);this.repeatAt[name]=time+350}else if(down&&was&&time>=this.repeatAt[name]){this.moveFocus(root,name);this.repeatAt[name]=time+100}else if(!down)this.repeatAt[name]=0;this.menuState[name]=down}
pressBack(root){let target=root.querySelector("button.cancel:not([disabled])");if(!target&&root.matches("dialog.message-box-ui"))target=this.candidates(root)[0]||null;if(target&&visible(target))target.click();else this.pressEscape()}
updateMenu(pad,root,time){this.releaseActions();this.steering=0;if(!pad){this.resetMenuState();return}const hadFocus=this.isFocusValid(root);this.ensureFocus(root);const x=this.menuAxisValue(pad,0,time),y=this.menuAxisValue(pad,1,time);this.repeatDirection("up",this.menuButtonDown(pad,12,time)||y<-.55,root,time);this.repeatDirection("down",this.menuButtonDown(pad,13,time)||y>.55,root,time);this.repeatDirection("left",this.menuButtonDown(pad,14,time)||x<-.55,root,time);this.repeatDirection("right",this.menuButtonDown(pad,15,time)||x>.55,root,time);const a=this.menuButtonDown(pad,0,time),b=this.menuButtonDown(pad,1,time);if(a&&!this.menuState.a&&hadFocus&&this.isFocusValid(root)){const target=this.focused;if(target){if(target.matches("input[type=range]"))this.setFocus(target);else target.click()}}if(b&&!this.menuState.b)this.pressBack(root);this.menuState.a=a;this.menuState.b=b}
beginCapture(options){if(this.capture)return;this.capture=options;this.captureArmed=false;this.releaseActions();this.steering=0;const overlay=document.createElement("div");overlay.className="polytrack-controller-capture";const panel=document.createElement("div");panel.className="polytrack-controller-capture-panel";const title=document.createElement("h2");title.textContent=options.steering?"Bind analog steering":"Bind controller input";const message=document.createElement("p");message.textContent=options.steering?"Release all controls, then move the desired steering axis to the right.\nPress Escape to cancel.":"Release all controls, then press a button, trigger, D-pad direction, or move a stick.\nPress Escape to cancel.";const wrapper=document.createElement("div");wrapper.className="button-wrapper";const cancel=document.createElement("button");cancel.className="button cancel";cancel.textContent="Cancel";cancel.addEventListener("click",()=>this.finishCapture(null,false));const clear=document.createElement("button");clear.className="button";clear.textContent="Clear";clear.addEventListener("click",()=>this.finishCapture(null,true));wrapper.append(cancel,clear);panel.append(title,message,wrapper);overlay.appendChild(panel);document.body.appendChild(overlay);this.captureOverlay=overlay}
updateCapture(pad){if(!pad)return;if(!this.captureArmed){if(allNeutral(pad))this.captureArmed=true;return}if(this.capture.steering){for(let index=0;index<(pad.axes?.length||0);index++){const value=Number(pad.axes[index])||0;if(Math.abs(value)>.65){this.finishCapture({kind:"axis",index,invert:value<0,deadzone:.1},true);return}}return}
for(let index=0;index<(pad.buttons?.length||0);index++)if(buttonValue(pad,index)>.5){this.finishCapture({kind:"button",index},true);return}for(let index=0;index<(pad.axes?.length||0);index++){const value=Number(pad.axes[index])||0;if(Math.abs(value)>.65){this.finishCapture({kind:"axis",index,direction:value<0?-1:1},true);return}}}
finishCapture(value,apply){const capture=this.capture;this.capture=null;this.captureArmed=false;if(this.captureOverlay){this.captureOverlay.remove();this.captureOverlay=null}if(apply&&capture)capture.complete(value);this.resetMenuState();this.queueDecorate()}
decorateSettings(){const root=document.querySelector(".settings-menu-ui");if(!root){if(this.settingsRoot&&!this.settingsRoot.isConnected){this.settingsRoot=null;this.draft=null}return}if(root!==this.settingsRoot){this.settingsRoot=root;this.draft=clone(this.config);const apply=root.querySelector("button.apply"),cancel=root.querySelector("button.cancel"),reset=root.querySelector("button.reset");if(apply)apply.addEventListener("click",()=>{if(this.draft){this.config=validate(this.draft);save(this.config)}this.draft=null});if(cancel)cancel.addEventListener("click",()=>{this.draft=null});if(reset)reset.addEventListener("click",()=>{this.draft=defaults();this.queueDecorate()})}
if(!this.draft)this.draft=clone(this.config);const rows=Array.from(root.querySelectorAll(".setting.key-binding:not(.polytrack-analog-row)"));for(let rowIndex=0;rowIndex<Math.min(rows.length,SETTINGS_ACTION_ORDER.length);rowIndex++){const row=rows[rowIndex];if(row.dataset.controllerEnhanced)continue;row.dataset.controllerEnhanced="true";const action=SETTINGS_ACTION_ORDER[rowIndex],wrapper=row.querySelector(".button-wrapper");if(!wrapper)continue;const separator=document.createElement("span");separator.className="polytrack-controller-separator";separator.textContent="Controller";wrapper.appendChild(separator);for(let slot=0;slot<2;slot++){const button=document.createElement("button");button.className="button polytrack-controller-binding";const refresh=()=>{button.textContent=`GP: ${labelDescriptor(this.draft?.actions?.[ACTION_NAMES[action]]?.[slot])}`};refresh();button.addEventListener("click",()=>this.beginCapture({steering:false,complete:value=>{if(!this.draft)this.draft=clone(this.config);this.draft.actions[ACTION_NAMES[action]][slot]=value;refresh()}}));wrapper.appendChild(button)}}
if(!root.querySelector(".polytrack-analog-row")&&rows.length>=4){const row=document.createElement("div");row.className="setting key-binding polytrack-analog-row";const text=document.createElement("p");text.textContent="Analog steering";const wrapper=document.createElement("div");wrapper.className="button-wrapper";const bind=document.createElement("button");bind.className="button polytrack-controller-binding";const clear=document.createElement("button");clear.className="button";clear.textContent="Clear";const refresh=()=>{bind.textContent=`GP: ${labelSteering(this.draft?.steering)}`};refresh();bind.addEventListener("click",()=>this.beginCapture({steering:true,complete:value=>{if(!this.draft)this.draft=clone(this.config);this.draft.steering=value;refresh()}}));clear.addEventListener("click",()=>{if(!this.draft)this.draft=clone(this.config);this.draft.steering=null;refresh()});wrapper.append(bind,clear);row.append(text,wrapper);rows[3].insertAdjacentElement("afterend",row)}}}

window.__polytrackController=new ControllerManager();
}

const VEHICLE_INPUT = `const Wt = class {
            constructor(e) {
              this._up = !1;
              this._right = !1;
              this._down = !1;
              this._left = !1;
              this._reset = !1;
              this._steering = 0;
              this._callbacks = [];
              this._keyDown = (t) => {
                e.checkKeyBinding(t, ge.A.VehicleAccelerate)
                  ? ((this.up = !0), t.preventDefault())
                  : e.checkKeyBinding(t, ge.A.VehicleTurnRight)
                    ? ((this.right = !0), t.preventDefault())
                    : e.checkKeyBinding(t, ge.A.VehicleBrake)
                      ? ((this.down = !0), t.preventDefault())
                      : e.checkKeyBinding(t, ge.A.VehicleTurnLeft) &&
                        ((this.left = !0), t.preventDefault());
              };
              this._keyUp = (t) => {
                e.checkKeyBinding(t, ge.A.VehicleAccelerate)
                  ? (this.up = !1)
                  : e.checkKeyBinding(t, ge.A.VehicleTurnRight)
                    ? (this.right = !1)
                    : e.checkKeyBinding(t, ge.A.VehicleBrake)
                      ? (this.down = !1)
                      : e.checkKeyBinding(t, ge.A.VehicleTurnLeft) &&
                        (this.left = !1);
              };
              window.addEventListener("keydown", this._keyDown);
              window.addEventListener("keyup", this._keyUp);
            }
            _notify() {
              for (const e of this._callbacks) e(this);
            }
            update() {
              this.steering = window.__polytrackController?.getSteering() ?? 0;
            }
            get up() { return this._up; }
            set up(e) { e = !!e; this._up != e && ((this._up = e), this._notify()); }
            get right() { return this._right; }
            set right(e) { e = !!e; this._right != e && ((this._right = e), this._notify()); }
            get down() { return this._down; }
            set down(e) { e = !!e; this._down != e && ((this._down = e), this._notify()); }
            get left() { return this._left; }
            set left(e) { e = !!e; this._left != e && ((this._left = e), this._notify()); }
            get reset() { return this._reset; }
            set reset(e) { e = !!e; this._reset != e && ((this._reset = e), this._notify()); }
            get steering() { return this._steering; }
            set steering(e) {
              e = Number.isFinite(e) ? Math.max(-1, Math.min(1, e)) : 0;
              this._steering != e && ((this._steering = e), this._notify());
            }
            get analogSteering() {
              return Math.abs(this.steering) > 1e-4 && !this.right && !this.left;
            }
            addChangeCallback(e) { this._callbacks.push(e); }
            removeChangeCallback(e) {
              const t = this._callbacks.indexOf(e);
              t >= 0 && this._callbacks.splice(t, 1);
            }
            dispose() {
              window.removeEventListener("keydown", this._keyDown);
              window.removeEventListener("keyup", this._keyUp);
              this._steering = 0;
            }
            getControls() {
              return {
                up: this.up,
                right: this.right,
                down: this.down,
                left: this.left,
                reset: this.reset,
                steering: this.steering,
                analogSteering: this.analogSteering,
              };
            }
          };
          var Vt;`;

const CONTROL_CAR = `controlCar(e, t, n, i, a, s, c, d) {
                const steering = Number.isFinite(c)
                  ? Math.max(-1, Math.min(1, c))
                  : window.__polytrackController?.getSteering() ?? 0;
                const analogSteering = null == d
                  ? Math.abs(steering) > 1e-4 && !n && !a
                  : !!d;
                const l = {
                  messageType: o.ControlCar,
                  carId: e,
                  up: t,
                  right: n,
                  down: i,
                  left: a,
                  reset: s,
                  steering,
                  analogSteering,
                };
                (0, r.gn)(this, h, "f").postMessage(l);
              }
              pauseCar(e, t) {`;

const DISABLED_CONTROL_CALL = `(0, l.gn)(this, X, "f")?.controlCar(
                          (0, l.gn)(this, ee, "f"),
                          !1,
                          !1,
                          !1,
                          !1,
                          !1,
                        )`;

const DISABLED_CONTROL_REPLACEMENT = `(0, l.gn)(this, X, "f")?.controlCar(
                          (0, l.gn)(this, ee, "f"),
                          !1,
                          !1,
                          !1,
                          !1,
                          !1,
                          0,
                          !1,
                        )`;

const WORKER_UPDATE = `function n(e, r) {
            t.ccall(
              "updateCarModel",
              "void",
              [
                "number",
                "boolean",
                "boolean",
                "boolean",
                "boolean",
                "boolean",
                "number",
              ],
              [e.id, r.up, r.right, r.down, r.left, r.reset, i],
            );
            return new Uint8Array(t.HEAPU8.buffer, i, 227).slice().buffer;
          }
          function controllerAnalogStep(e, r) {
            let right = r.right;
            let left = r.left;
            const speed = Math.abs(Number.isFinite(e.nativeSpeed) ? e.nativeSpeed : 0);
            const speedLimit = Math.min(0.410258, 155 / Math.pow(Math.max(1, speed), 1.55));
            const driftBlend = Number.isFinite(e.driftSteering) ? e.driftSteering : 0;
            const steeringLimit = speedLimit + (0.410258 - speedLimit) * driftBlend;
            const target = Number.isFinite(r.steering)
              ? -Math.max(-1, Math.min(1, r.steering)) * steeringLimit
              : 0;
            const tolerance = Math.max(2e-5, 0.002 * steeringLimit);
            if (!right && !left) {
              const current = Number.isFinite(e.nativeSteering) ? e.nativeSteering : 0;
              target - current < -tolerance
                ? (right = !0)
                : target - current > tolerance && (left = !0);
            }
            t.ccall(
              "updateCarModel",
              "void",
              [
                "number",
                "boolean",
                "boolean",
                "boolean",
                "boolean",
                "boolean",
                "number",
              ],
              [e.id, r.up, right, r.down, left, r.reset, i],
            );
            const view = new DataView(t.HEAPU8.buffer);
            e.nativeSpeed = view.getFloat32(i + 4 + 3, !0);
            let offset = i + 4 + 3 + 4;
            const flags = t.HEAPU8[offset++];
            2 & flags && (offset += 3);
            offset += 2 + 12 + 16;
            const checkpointCount = t.HEAPU8[offset++];
            offset += 4 * checkpointCount;
            for (let wheel = 0; wheel < 4; wheel++)
              8 << wheel & flags && (offset += 24);
            const rearLeftGrip = 32 & flags ? view.getFloat32(offset + 56, !0) : 1;
            const rearRightGrip = 64 & flags ? view.getFloat32(offset + 60, !0) : 1;
            e.isDrifting
              ? Math.max(rearLeftGrip, rearRightGrip) > 0.9 && (e.isDrifting = !1)
              : rearLeftGrip < 0.4 && rearRightGrip < 0.4 && (e.isDrifting = !0);
            const previousBlend = Number.isFinite(e.driftSteering) ? e.driftSteering : 0;
            e.driftSteering = Math.max(
              0,
              Math.min(1, previousBlend + (e.isDrifting ? 0.0125 : -0.004)),
            );
            e.nativeSteering = view.getFloat32(offset + 64, !0);
            return new Uint8Array(t.HEAPU8.buffer, i, 227).slice().buffer;
          }
          (($o.length = 0), (onmessage = r));`;

function replaceExact(pml, method, token, replacement, expectedOccurrences = 1) {
  pml[method]({
    type: MixinType.REPLACEBETWEEN,
    tokenStart: token,
    tokenEnd: token,
    func: replacement,
    expectedOccurrences,
  });
}

function replaceRange(pml, method, tokenStart, tokenEnd, replacement) {
  pml[method]({
    type: MixinType.REPLACEBETWEEN,
    tokenStart,
    tokenEnd,
    func: replacement,
  });
}

class ControllerPatch extends PolyMod {
  touchingPhysics = true;

  preInit = (pml) => {
    if (
      typeof pml?.registerGlobalMixin !== "function" ||
      typeof pml?.registerSimWorkerMixin !== "function"
    ) {
      throw new Error(
        "Controller Patch requires a stable PolyModLoader 0.6.x build with simulation-worker mixins.",
      );
    }

    pml.registerGlobalMixin({
      type: MixinType.INSERT,
      token: { token: "() => {", occ: 1 },
      func: `\n;(${controllerRuntime.toString()})();\n`,
    });

    replaceRange(
      pml,
      "registerGlobalMixin",
      "var Ut, Nt, zt, Dt, Bt, Gt, Ft, Ot;",
      "var Vt;",
      VEHICLE_INPUT,
    );
    replaceRange(
      pml,
      "registerGlobalMixin",
      "controlCar(e, t, n, i, a, s) {",
      "pauseCar(e, t) {",
      CONTROL_CAR,
    );
    replaceExact(
      pml,
      "registerGlobalMixin",
      DISABLED_CONTROL_CALL,
      DISABLED_CONTROL_REPLACEMENT,
    );
    replaceExact(
      pml,
      "registerGlobalMixin",
      `update(e) {
              const t = (0, R.gn)(this, jr, "m", ys).call(this);`,
      `update(e) {
              (0, R.gn)(this, Da, "f").update();
              const t = (0, R.gn)(this, jr, "m", ys).call(this);`,
    );
    pml.registerGlobalMixin({
      type: MixinType.INSERT,
      token: "checkKeyBinding(e, t) {",
      func: `\n              if (e.polytrackControllerAction === t) return !0;`,
    });
    pml.registerGlobalMixin({
      type: MixinType.INSERT,
      token: "submitLeaderboard(e, t, n, i, r, a, s, o) {",
      func: `\n              return Promise.resolve({ uploadId: null, positionChange: null });`,
    });
    replaceRange(
      pml,
      "registerGlobalMixin",
      `((0, R.gn)(this, Za, "f") &&`,
      `(0, R.GG)(this, Za, !1, "f"))))`,
      `((0, R.gn)(this, Za, "f") &&
                        (0, R.GG)(this, Za, !1, "f")))`,
    );

    replaceExact(
      pml,
      "registerSimWorkerMixin",
      `n = {
                        up: !1,
                        right: !1,
                        down: !1,
                        left: !1,
                        reset: !1,
                        buffer: [],
                      }`,
      `n = {
                        up: !1,
                        right: !1,
                        down: !1,
                        left: !1,
                        reset: !1,
                        steering: 0,
                        analogSteering: !1,
                        buffer: [],
                      }`,
    );
    replaceExact(
      pml,
      "registerSimWorkerMixin",
      `targetSimulationFrames: null,
                      isPaused: !1,`,
      `targetSimulationFrames: null,
                      isPaused: !1,
                      nativeSteering: 0,
                      nativeSpeed: 0,
                      driftSteering: 0,
                      isDrifting: !1,`,
    );
    replaceExact(
      pml,
      "registerSimWorkerMixin",
      "reset: t.reset,",
      `reset: t.reset,
                          steering: t.steering ?? 0,
                          analogSteering: !!t.analogSteering,`,
      3,
    );
    replaceExact(
      pml,
      "registerSimWorkerMixin",
      "t.userControls.reset = e.reset",
      `t.userControls.reset = e.reset),
                        (t.userControls.steering = e.steering ?? 0),
                        (t.userControls.analogSteering = !!e.analogSteering`,
    );
    replaceExact(
      pml,
      "registerSimWorkerMixin",
      "reset: t.userControls.reset,",
      `reset: t.userControls.reset,
                        steering: t.userControls.steering,
                        analogSteering: t.userControls.analogSteering,`,
    );
    replaceRange(
      pml,
      "registerSimWorkerMixin",
      "function n(e, r) {",
      "(($o.length = 0), (onmessage = r));",
      WORKER_UPDATE,
    );
    replaceExact(
      pml,
      "registerSimWorkerMixin",
      "for (const { car: t, controls: e } of i) r.push(n(t, e));",
      `for (const { car: t, controls: e } of i)
              r.push(e.analogSteering ? controllerAnalogStep(t, e) : n(t, e));`,
    );
  };
}

export let polyMod = new ControllerPatch();
