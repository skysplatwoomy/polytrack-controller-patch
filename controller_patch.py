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
    old_input = (
        'var Ut,Nt,zt,Dt,Bt,Gt,Ft,Ot;Ut=new WeakMap,Nt=new WeakMap,zt=new WeakMap,Dt=new WeakMap,Bt=new WeakMap,Gt=new WeakMap,Ft=new WeakMap,Ot=new WeakMap;const Wt=class{constructor(e){Ut.set(this,!1),Nt.set(this,!1),zt.set(this,!1),Dt.set(this,!1),Bt.set(this,!1),Gt.set(this,void 0),Ft.set(this,void 0),Ot.set(this,[]),window.addEventListener("keydown",(0,R.GG)(this,Gt,(t=>{e.checkKeyBinding(t,ge.A.VehicleAccelerate)?(this.up=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleTurnRight)?(this.right=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleBrake)?(this.down=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleTurnLeft)&&(this.left=!0,t.preventDefault())}),"f")),window.addEventListener("keyup",(0,R.GG)(this,Ft,(t=>{e.checkKeyBinding(t,ge.A.VehicleAccelerate)?this.up=!1:e.checkKeyBinding(t,ge.A.VehicleTurnRight)?this.right=!1:e.checkKeyBinding(t,ge.A.VehicleBrake)?this.down=!1:e.checkKeyBinding(t,ge.A.VehicleTurnLeft)&&(this.left=!1)}),"f"))}get up(){return(0,R.gn)(this,Ut,"f")}set up(e){if((0,R.gn)(this,Ut,"f")!=e){(0,R.GG)(this,Ut,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}get right(){return(0,R.gn)(this,Nt,"f")}set right(e){if((0,R.gn)(this,Nt,"f")!=e){(0,R.GG)(this,Nt,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}get down(){return(0,R.gn)(this,zt,"f")}set down(e){if((0,R.gn)(this,zt,"f")!=e){(0,R.GG)(this,zt,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}get left(){return(0,R.gn)(this,Dt,"f")}set left(e){if((0,R.gn)(this,Dt,"f")!=e){(0,R.GG)(this,Dt,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}get reset(){return(0,R.gn)(this,Bt,"f")}set reset(e){if((0,R.gn)(this,Bt,"f")!=e){(0,R.GG)(this,Bt,e,"f");for(const e of(0,R.gn)(this,Ot,"f"))e(this)}}addChangeCallback(e){(0,R.gn)(this,Ot,"f").push(e)}removeChangeCallback(e){const t=(0,R.gn)(this,Ot,"f").indexOf(e);t>=0&&(0,R.gn)(this,Ot,"f").splice(t,1)}dispose(){window.removeEventListener("keydown",(0,R.gn)(this,Gt,"f")),window.removeEventListener("keyup",(0,R.gn)(this,Ft,"f"))}getControls(){return{up:this.up,right:this.right,down:this.down,left:this.left,reset:this.reset}}};var Vt;'
    )
    new_input = (
        'const Wt=class{constructor(e,t=null){this._keyboardUp=!1,this._keyboardRight=!1,this._keyboardDown=!1,this._keyboardLeft=!1,this._reset=!1,this._gamepadUp=!1,this._gamepadDown=!1,this._steering=0,this._gamepad=null,this._lastGamepadB=!1,this._callbacks=[],this._resetCallback=t,this._keyDown=(t=>{e.checkKeyBinding(t,ge.A.VehicleAccelerate)?(this.up=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleTurnRight)?(this.right=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleBrake)?(this.down=!0,t.preventDefault()):e.checkKeyBinding(t,ge.A.VehicleTurnLeft)&&(this.left=!0,t.preventDefault())}),this._keyUp=(t=>{e.checkKeyBinding(t,ge.A.VehicleAccelerate)?this.up=!1:e.checkKeyBinding(t,ge.A.VehicleTurnRight)?this.right=!1:e.checkKeyBinding(t,ge.A.VehicleBrake)?this.down=!1:e.checkKeyBinding(t,ge.A.VehicleTurnLeft)&&(this.left=!1)}),this._clearGamepad=(()=>{const e=null!=this._gamepad||this._gamepadUp||this._gamepadDown||0!=this._steering||this._lastGamepadB;this._gamepad=null,this._lastGamepadB=!1,this._setGamepad(!1,!1),this.steering=0,e&&this._notify()}),window.addEventListener("keydown",this._keyDown),window.addEventListener("keyup",this._keyUp),window.addEventListener("blur",this._clearGamepad),document.addEventListener("visibilitychange",this._clearGamepad)}_notify(){for(const e of this._callbacks)e(this)}_setGamepad(e,t){this._gamepadUp=e,this._gamepadDown=t}_findGamepad(){const e="function"==typeof navigator.getGamepads?navigator.getGamepads():[],t=this._gamepad;if(null!=t){const n=e[t.index];if(null!=n&&n.connected)return n;this._gamepad=null}for(const t of e)if(null!=t&&t.connected&&("standard"==t.mapping||""==t.mapping))return this._gamepad=t,t;return null}_buttonValue(e,t){const n=t?.[e];return null==n?0:Math.max(n.value??0,n.pressed?1:0)}update(){const e=this._findGamepad();if(null==e)return this._clearGamepad(),void 0;const t=e.axes?.[0]??0,n=Math.abs(t)<.1?0:Math.max(-1,Math.min(1,(t-Math.sign(t)*.1)/.9)),i=this._buttonValue(7,e.buttons)>.1,r=this._buttonValue(6,e.buttons)>.1,a=this._buttonValue(1,e.buttons)>=.5;this._setGamepad(i,r),this.steering=n,a&&!this._lastGamepadB&&this._resetCallback?.(),this._lastGamepadB=a,this._notify()}get up(){return this._keyboardUp||this._gamepadUp}set up(e){e=!!e,this._keyboardUp!=e&&(this._keyboardUp=e,this._notify())}get right(){return this._keyboardRight}set right(e){e=!!e,this._keyboardRight!=e&&(this._keyboardRight=e,this._notify())}get down(){return this._keyboardDown||this._gamepadDown}set down(e){e=!!e,this._keyboardDown!=e&&(this._keyboardDown=e,this._notify())}get left(){return this._keyboardLeft}set left(e){e=!!e,this._keyboardLeft!=e&&(this._keyboardLeft=e,this._notify())}get reset(){return this._reset}set reset(e){e=!!e,this._reset!=e&&(this._reset=e,this._notify())}get steering(){return this._steering}set steering(e){e=Number.isFinite(e)?Math.max(-1,Math.min(1,e)):0,this._steering!=e&&(this._steering=e,this._notify())}addChangeCallback(e){this._callbacks.push(e)}removeChangeCallback(e){const t=this._callbacks.indexOf(e);t>=0&&this._callbacks.splice(t,1)}dispose(){window.removeEventListener("keydown",this._keyDown),window.removeEventListener("keyup",this._keyUp),window.removeEventListener("blur",this._clearGamepad),document.removeEventListener("visibilitychange",this._clearGamepad),this._gamepad=null,this._lastGamepadB=!1,this._gamepadUp=!1,this._gamepadDown=!1,this._steering=0}getControls(){return{up:this.up,right:this.right,down:this.down,left:this.left,reset:this.reset,steering:this.steering}}};var Vt;'
    )
    source = replace_once(source, old_input, new_input, "vehicle input manager")
    source = replace_once(
        source,
        'this._gamepadDown=!1,this._steering=0,this._gamepad=null',
        'this._gamepadDown=!1,this._steering=0,this._gamepadActive=!1,this._gamepad=null',
        "gamepad source state",
    )
    source = replace_once(
        source,
        'const e=null!=this._gamepad||this._gamepadUp||this._gamepadDown||0!=this._steering||this._lastGamepadB;this._gamepad=null,this._lastGamepadB=!1,',
        'const e=null!=this._gamepad||this._gamepadActive||this._gamepadUp||this._gamepadDown||0!=this._steering||this._lastGamepadB;this._gamepad=null,this._gamepadActive=!1,this._lastGamepadB=!1,',
        "gamepad clear source state",
    )
    source = replace_once(
        source,
        'const e=this._findGamepad();if(null==e)return this._clearGamepad(),void 0;const t=e.axes?.[0]??0,',
        'const e=this._findGamepad();if(null==e)return this._clearGamepad(),void 0;this._gamepadActive=!0;const t=e.axes?.[0]??0,',
        "gamepad active state",
    )
    source = replace_once(
        source,
        'this._gamepad=null,this._lastGamepadB=!1,this._gamepadUp=!1,this._gamepadDown=!1,this._steering=0}',
        'this._gamepad=null,this._gamepadActive=!1,this._lastGamepadB=!1,this._gamepadUp=!1,this._gamepadDown=!1,this._steering=0}',
        "gamepad dispose source state",
    )
    source = replace_once(
        source,
        'getControls(){return{up:this.up,right:this.right,down:this.down,left:this.left,reset:this.reset,steering:this.steering}}',
        'getControls(){return{up:this.up,right:this.right,down:this.down,left:this.left,reset:this.reset,steering:this.steering,analogSteering:this._gamepadActive}}',
        "gamepad source controls",
    )
    source = replace_once(
        source,
        '(0,R.gn)(this,Za,"f")&&((0,R.gn)(this,ra,"f").show((0,R.gn)(this,Yr,"f").get("Invalid replay detected!"),(0,R.gn)(this,Yr,"f").get("Ok"),(()=>{(0,R.gn)(this,ra,"f").hide()})),(0,R.GG)(this,Za,!1,"f"))',
        '(0,R.gn)(this,Za,"f")&&(0,R.GG)(this,Za,!1,"f")',
        "disable invalid replay dialog",
    )
    source = replace_once(
        source,
        'controlCar(e,t,n,i,a,s){const l={messageType:o.ControlCar,carId:e,up:t,right:n,down:i,left:a,reset:s};',
        'controlCar(e,t,n,i,a,s,c,d){const l={messageType:o.ControlCar,carId:e,up:t,right:n,down:i,left:a,reset:s,steering:c??0,analogSteering:!!d||Number.isFinite(c)&&Math.abs(c)>1e-4};',
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
        '(0,R.GG)(this,Da,new Wt(u),"f")',
        '(0,R.GG)(this,Da,new Wt(u,(()=>{!I.ip()&&(0,R.gn)(this,jr,"m",ys).call(this)&&(0,R.gn)(this,Fa,"f").hasStarted()&&(0,R.gn)(this,jr,"m",fs).call(this)})),"f")',
        "gamepad reset callback",
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
        'r.push(e.analogSteering||Number.isFinite(e.steering)&&Math.abs(e.steering)>1e-4?controllerAnalogStep(t,e):n(t,e))',
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
