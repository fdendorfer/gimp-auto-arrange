# gimp-auto-arrange

GIMP 3.0 plug-ins for arranging a stack of layers side by side and cleaning
up their background — built for lining up stained tree-ring microsection
scans, but generally useful for any batch of similarly-named, sequentially
numbered images.

## Workflow

1. Open your numbered images as layers into a single image
   (`File > Open as Layers`).
2. Run `Image > Arrange Layers Side by Side` (see below).
3. Run `Image > Remove White/Grey Background` (see below).
4. Manually nudge layers closer together now that their backgrounds are
   transparent — this last bit stays manual since it needs a precise eye.

## Plug-ins

### Arrange Layers Side by Side

If you regularly open a batch of numbered images as layers, this saves you
from dragging each one into place and resizing the canvas by hand.

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

### Remove White/Grey Background

For stained microsection scans (e.g. red/blue cells on white/grey paper):
makes the white/grey background of every layer transparent so the images can
then be packed closer together than their rectangular bounds would allow.

- Detects background by **color saturation**, not brightness: any pixel
  close to grayscale (white, light grey, or dark grey/shadow) is treated as
  background, while colored (e.g. red/blue stained) pixels stay opaque
  regardless of how light or dark they are.
- Light-colored areas **enclosed inside a cell** (e.g. a pale interior
  surrounded by a stained wall) are left alone rather than being punched
  through — only background that's contiguously connected to the edge of
  the image gets removed. This assumes the four corners of the image are
  genuine background.
- Four constants at the top of the script control the behavior — tune them
  by eye if needed:
  - `TRANSPARENCY_THRESHOLD` / `OPACITY_THRESHOLD` (default `0.02` /
    `0.02`): saturation at or below `TRANSPARENCY_THRESHOLD` is fully
    transparent, at or above `OPACITY_THRESHOLD` is fully opaque, values in
    between form a ramp. Equal values (the default) give a hard edge; give
    `OPACITY_THRESHOLD` a slightly higher value for a soft/feathered edge
    instead. Real saturation values in a scan tend to be much lower than
    you'd guess — check a layer's actual range before tuning (see the
    comment above these constants in the script for how).
  - `SAMPLE_THRESHOLD` (default `0.05`): how similar a pixel must be to a
    corner pixel to flood-fill together as background, when deciding what
    counts as an enclosed island.
  - `GROW_PIXELS` (default `1`): expands the detected background region by
    this many pixels before excluding everything else, so the true outer
    edge doesn't get treated as an enclosed island too.
- If the image is in **Grayscale mode**, saturation is always zero, so
  layers are left untouched rather than being made fully transparent.
- A layer that **already has a layer mask** is skipped with a warning,
  rather than risking that mask.
- Runs as a single undo step.

## Install

For each plug-in, copy its folder into your GIMP plug-ins directory:

- **Linux/macOS**: `~/.config/GIMP/<version>/plug-ins/`
- **Windows**: `%APPDATA%\GIMP\<version>\plug-ins\`

`<version>` is GIMP's own per-release config folder (e.g. `3.0`, `3.2`, ...)
— **not** always `3.0`. GIMP creates this folder the first time you launch
it, so **launch GIMP at least once** before installing, then check
`~/.config/GIMP/` (or `%APPDATA%\GIMP\`) to see which version folder is
actually there. Using the wrong one is the most common reason a plug-in
doesn't show up: GIMP only scans its own version's folder, even though the
plug-in code itself (`gi.require_version("Gimp", "3.0")`) targets the
GIMP-3 API generation as a whole and works unchanged across 3.0, 3.2, etc.

So you end up with e.g.
`~/.config/GIMP/3.2/plug-ins/side-by-side-arrange/side-by-side-arrange.py`.

The commands below auto-detect the right version folder (falling back to
`3.0` if GIMP has never been run) so you don't have to figure it out
by hand. On Linux/macOS:

```sh
gimp_ver=$(ls -1 ~/.config/GIMP 2>/dev/null | grep -E '^[0-9]+\.[0-9]+$' | sort -V | tail -n1); gimp_ver=${gimp_ver:-3.0}; mkdir -p ~/.config/GIMP/$gimp_ver/plug-ins/side-by-side-arrange && curl -fsSL -o ~/.config/GIMP/$gimp_ver/plug-ins/side-by-side-arrange/side-by-side-arrange.py https://raw.githubusercontent.com/fdendorfer/gimp-auto-arrange/main/plug-ins/side-by-side-arrange/side-by-side-arrange.py && chmod +x ~/.config/GIMP/$gimp_ver/plug-ins/side-by-side-arrange/side-by-side-arrange.py
```

```sh
gimp_ver=$(ls -1 ~/.config/GIMP 2>/dev/null | grep -E '^[0-9]+\.[0-9]+$' | sort -V | tail -n1); gimp_ver=${gimp_ver:-3.0}; mkdir -p ~/.config/GIMP/$gimp_ver/plug-ins/remove-white-grey-background && curl -fsSL -o ~/.config/GIMP/$gimp_ver/plug-ins/remove-white-grey-background/remove-white-grey-background.py https://raw.githubusercontent.com/fdendorfer/gimp-auto-arrange/main/plug-ins/remove-white-grey-background/remove-white-grey-background.py && chmod +x ~/.config/GIMP/$gimp_ver/plug-ins/remove-white-grey-background/remove-white-grey-background.py
```

On Windows, from PowerShell:

```powershell
$gimpVer = (Get-ChildItem "$env:APPDATA\GIMP" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^\d+\.\d+$' } | Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1 -ExpandProperty Name); if (-not $gimpVer) { $gimpVer = "3.0" }; New-Item -ItemType Directory -Force -Path "$env:APPDATA\GIMP\$gimpVer\plug-ins\side-by-side-arrange" | Out-Null; Invoke-WebRequest -Uri "https://raw.githubusercontent.com/fdendorfer/gimp-auto-arrange/main/plug-ins/side-by-side-arrange/side-by-side-arrange.py" -OutFile "$env:APPDATA\GIMP\$gimpVer\plug-ins\side-by-side-arrange\side-by-side-arrange.py"
```

```powershell
$gimpVer = (Get-ChildItem "$env:APPDATA\GIMP" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^\d+\.\d+$' } | Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1 -ExpandProperty Name); if (-not $gimpVer) { $gimpVer = "3.0" }; New-Item -ItemType Directory -Force -Path "$env:APPDATA\GIMP\$gimpVer\plug-ins\remove-white-grey-background" | Out-Null; Invoke-WebRequest -Uri "https://raw.githubusercontent.com/fdendorfer/gimp-auto-arrange/main/plug-ins/remove-white-grey-background/remove-white-grey-background.py" -OutFile "$env:APPDATA\GIMP\$gimpVer\plug-ins\remove-white-grey-background\remove-white-grey-background.py"
```

Otherwise, copy each script's folder in by hand into the correct version
folder. On Linux/macOS make sure it's executable:

```sh
chmod +x side-by-side-arrange.py remove-white-grey-background.py
```

Then restart GIMP (Python plug-ins are only picked up on startup, unlike
Script-Fu's "Refresh Scripts").

## Requirements

GIMP 3.0 with Python support enabled.
