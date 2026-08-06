# Polytrack Controller Patch
This is a Python script to patch controller support into the downloadable version of Polytrack.

This mod has only been tested with specifically PolyTrack-v0.6.2-linux-x64 and works perfectly on that build specifically

## Usage

Download the script and place it in the root folder of your game files and run the python script from the terminal:
```
python3 controller_patch.py
```

Once it is done running, you may run the newly patched game from that same directory.

From here, you can drive with a gamepad of your choice with these controls:
- RT - Accelerate
- LT - Brake
- Left stick - Steer
- B - Reset from start

## Features

- Adds controller support
- Maps horizontal analogic stick input linearly to the car's steering 
- 10% deadzone (hardcoded (fuck you))
- Changes the steering according to the car's speed, keeping linearity (disabled whilst sliding to allow for countersteering)
- Disables "Invalid replay detected!" dialog box

## Disclaimers

- This mod is fully vibe coded lmaoo but it works well from my experience so like use it if you want I guess
- Using controller to play using this mod will invalidate your times, use at your own risk on your account
- You cannot rebind any of the keybinds in the settings to controller inputs currently as is
