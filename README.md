# Polytrack Controller Patch
This repo contains a mod to patch controller support (with proper implementation for fully analog steering) into the downloadable version of Polytrack.

This mod has only been tested with specifically PolyTrack-v0.6.2-linux-x64 and works perfectly on that build specifically

## Usage

There are two ways to download and use this mod:
- Load with PolyModLoader (Recommended)
- Python Script Patcher : Will directly patch your app.asar

### PolyModLoader Mod

Go to your mods in your Polytrack game that has PolyModLoader installed, and load the mod with this URL:
```
https://cdn.polymodloader.com/gh/skysplatwoomy/polytrack-controller-patch/main//controller-patch-PML/
```

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

## Disclaimers

- This mod is fully vibe coded lmaoo but it works well from my experience so like use it if you want I guess
- Using controller to play using this mod will invalidate your times, use at your own risk on your account
- Using this mod is considered as cheating
