# drawing for simutrans addon making — User Manual

**drawing for simutrans addon making** is a small pixel-art editor for PNG images, made for drawing [Simutrans](https://www.simutrans.com/) add-on graphics.
Besides normal drawing tools, it has features built for Simutrans:

- Paksize guide lines and the ground-tile (diamond) outline drawn over the canvas
- Line snapping to Simutrans-friendly slopes, and parallelogram / diamond / 3D-box drawing tools
- A palette of the Simutrans **special colors** (lights, windows, player colors), plus a view that highlights them
- Layers with Simutrans-aware merge modes (Add, Multiply, Replace, Brightness, Lightmap)
- Color replacement, including conversion to **player colors**
- Changing the paksize: adding a margin, or rescaling the image
- English and Japanese (日本語) user interface

## Contents

1. [Getting Started](Getting-Started): installing, launching, screen layout, New / Open / Save, language
2. [Drawing Tools](Drawing-Tools): Pen, Fill, Line, Eraser, Pipette, Move, Rect, FillRect, Prism, colors and alpha
3. [Selection and Editing](Selection-and-Editing): Select, ParaSelect, Copy / Cut / Paste, Clear Outside, Undo / Redo
4. [Layers](Layers): the layer panel, layer operations, merge modes, layer offset
5. [Special Colors](Special-Colors): the Simutrans special color palette and the highlight view
6. [Process Tab](Process-Tab): Simutrans guides, Turn gray, Delete Background, add margin, Image Resize
7. [Color Replace](Color-Replace): replacing color ranges and converting to player colors
8. [Keyboard and Mouse](Keyboard-and-Mouse): all shortcuts in one table
9. [Tips and Notes](Tips-and-Notes): a sample workflow, and behavior worth knowing

## Quick start

1. Run `drawing_for_simutrans_addon_making.exe`.
2. Click **File → New**, enter the size (e.g. `128` × `128`) and press **Create**. You can also use **File → Open** to load an existing PNG.
3. Pick a color with **Color**, or from the **Special Colors** tab, and draw with **Pen**, **Line**, **Rect** and the other tools.
4. Zoom with **Ctrl + mouse wheel**, and pan by dragging with the **right mouse button**.
5. Save with **File → Save** or **Save As...**. The visible layers are combined into one PNG.

## Release history

| Date | Version | Changes |
|---|---|---|
| 2026-02-10 | v0 | First release |
| 2026-02-10 | v0.1 | Merged png_merge_for_simutrans and change_image_paksize; added guide lines |
| 2026-02-11 | v0.2 | Added fill and line; improved mouse-wheel handling |
| 2026-02-12 | v0.3 | Added layer merge, cut, select all, Simutrans special colors |
| 2026-02-12 | v0.3.1 | Fixed mouse wheel and canvas movement |
| 2026-02-18 | v0.4 | Improved layer-merge calculation for transparent pixels |
| 2026-02-20 | v0.5 | Added rectangle |
| 2026-03-02 | v0.6 | Added polygon fill and select |
| 2026-10-03 | v0.7 | Added color replace |
