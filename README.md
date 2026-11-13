# Polytrack Controller Patch
This repo contains a mod to patch controller support (with proper implementation for fully analog steering) into the downloadable version of Polytrack.

## Supported game versions

| Game version | Mod version | Status |
|-|-|-|
| 0.6.3 | 1.0.1 | Validated against the official PML 0.6.3 game bundles |
| 0.6.2 | 1.0.0 | Tested with PolyTrack-v0.6.2-linux-x64 |

The PolyModLoader mod ships both versions side by side in this repo. PolyModLoader picks the correct one automatically based on the game version (via `controller-patch-PML/manifest.json`), so the same mod URL works for both game builds. The Python Script Patcher was not changed.

## Usage

There are two ways to download and use this mod:
- Load with PolyModLoader (Recommended)
- Python Script Patcher : Will directly patch your app.asar

### PolyModLoader Mod

Go to your mods in your Polytrack game that has PolyModLoader installed, and load the mod with this URL:
```
https://cdn.polymodloader.com/gh/skysplatwoomy/polytrack-controller-patch/main//controller-patch-PML/
```
On game 0.6.3 this loads mod version 1.0.1 (`controller-patch-PML/1.0.1/`); on game 0.6.2 it loads mod version 1.0.0 (`controller-patch-PML/1.0.0/`).

### Python Script Patcher 

Navigate to the root folder of your game files, and first rename your app.asar to have a copy:
```
mv resources/app.asar resources/original.asar
```
Download the script and place it in the root folder of your game files and run the python script from the terminal:
```
python3 controller_patch.py resources/original.asar resources/app.asar
```

Once it is done running, you may run the newly patched game from that same directory.

From here, you can bind all actions to a gamepad and play with a gamepad of your choice.

## Features

- Adds controller support
- Allows you to bind all bindable actions to controller inputs
- Allows you to navigate in-game menus with a controller
- Maps horizontal analogic stick input linearly to the car's steering 
- 10% deadzone (hardcoded (fuck you))
- Changes the steering according to the car's speed, keeping linearity (disabled whilst sliding to allow for countersteering)
- Disables "Invalid replay detected!" dialog box (Not even sure if this is even needed now but keeping it anyways)
- Disables uploading times to leaderboard (This mod is effectively a cheat)

## Development

The PML mod is verified against the official PolyModLoader game bundles. With a local checkout of the matching PolyModLoader branch (e.g. `0.6.3`), run:

```
node controller-patch-PML/tools/validate.mjs <pml-main.bundle.js> <pml-simulation_worker.bundle.js> [output-prefix] [mod-version]
node controller-patch-PML/tools/controller-runtime.test.cjs [mod-version]
```

Both default to mod version 1.0.1. Pass `1.0.0` to validate the 0.6.2 build instead (against the 0.6.2 PML bundles).

## Disclaimers

- This mod is fully vibe coded lmaoo but it works well from my experience so like use it if you want I guess
- Using controller to play using this mod will invalidate your times, use at your own risk on your account
- Using this mod is considered as cheating
