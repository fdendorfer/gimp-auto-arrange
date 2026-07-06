# gimp-auto-arrange

A GIMP 3.0 plug-in that arranges a stack of layers side by side in one pass.

If you regularly open a batch of similarly-named, sequentially-numbered
images as layers (e.g. `File > Open as Layers`), this saves you from
dragging each one into place and resizing the canvas by hand.

## What it does

- Reads the **last number** found in each layer's name (e.g. `scan_012` → `12`).
- Lines the layers up in a single horizontal row, **no gap**: the layer with
  the **highest** number ends up on the **left**, the **lowest** on the
  **right**.
- **Vertically centers** every layer on a common horizontal axis, so images
  of different heights still line up in the middle.
- **Resizes the canvas** to exactly fit the resulting strip.
- Layers with no number in their name are placed at the right end, and a
  message names them so you can double check the result.
- Runs as a single undo step.

## Install

1. Copy the `side-by-side-arrange` folder into your GIMP 3.0 plug-ins
   directory:
   - **Linux/macOS**: `~/.config/GIMP/3.0/plug-ins/side-by-side-arrange/`
   - **Windows**: `%APPDATA%\GIMP\3.0\plug-ins\side-by-side-arrange\`
2. Make sure the script is executable:
   ```sh
   chmod +x side-by-side-arrange.py
   ```
3. Restart GIMP (Python plug-ins are only picked up on startup, unlike
   Script-Fu's "Refresh Scripts").

## Use

1. Open your numbered images as layers into a single image
   (`File > Open as Layers`).
2. Run `Image > Arrange Layers Side by Side`.

## Requirements

GIMP 3.0 with Python support enabled.
