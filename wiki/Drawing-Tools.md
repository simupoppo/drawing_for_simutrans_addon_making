# Drawing Tools

Click a tool button on the toolbar to select it. The selected tool is shown pressed in and light blue.
All tools draw on the **active layer** only (see [Layers](Layers)).

## Color and alpha

| Control | Description |
|---|---|
| **Color** | Opens a color picker and sets the drawing color (RGB). |
| **Alpha** slider | Sets the drawing color's opacity, from 0 to 255 in steps of 8. 255 is fully opaque. |
| Color preview | The small square next to the slider shows the current color. |
| **Special Colors** tab | Click a swatch to use a Simutrans special color. See [Special Colors](Special-Colors). |
| **Pipette** tool | Picks a color from the canvas. See below. |

Drawing tools **replace** the pixel's RGBA value with the drawing color. They do not blend with what is already there. If alpha is less than 255, the pixel becomes semi-transparent.

## Tools

### Pen
Click or drag to draw 1-pixel dots.

### Fill
Click a pixel to flood-fill the connected area of exactly the same RGBA color (up, down, left and right neighbors only) with the drawing color.

### Line
Drag from the start point to the end point. A dashed preview and the offset `(dx, dy)` are shown while you drag.

- Hold **Shift** while dragging to **snap** the line to one of the slopes Simutrans uses:
  horizontal, 3:8, 1:2, 5:8, 1:1 (45°), 3:2, and vertical.
  The 1:2 slope (two pixels across, one pixel down) is the standard isometric edge in Simutrans.

### Eraser
Click or drag to make pixels fully transparent.

### Pipette
Click a pixel to copy its color, **including alpha**, into the drawing color. The Alpha slider is updated too.
The tool then switches back to **Pen**.
The color is taken from the **active layer**, not from the combined image.

### Move
Drag to move the **whole active layer**. This changes the layer's offset, which is shown in the status bar.
For exact values, use the **Layer Offset** controls in the [Layers](Layers) tab.

### Rect / FillRect
Drag to draw a shape outline (**Rect**) or a filled shape (**FillRect**).
When one of these tools is selected, three shape buttons appear on the toolbar:

| Shape | Description | Typical use |
|---|---|---|
| **Box** | A normal rectangle. | Flat parts, icons |
| **H-Para** | A parallelogram with two vertical sides and two sides sloped at 1:2. | Building **walls** seen at an angle |
| **D-Para** | A diamond or parallelogram whose four sides all run at 2:1 isometric angles. The drag start is one corner, and the shape snaps to the nearest exact 2:1 shape. | **Ground tiles**, roofs, platforms |

While you drag, a dashed preview shows exactly the pixels that will be drawn, and the corner coordinates are shown as text.
FillRect fills exactly the area inside the outline that Rect would draw, so a filled shape and its outline always line up.

### Prism (3D box)
Draws an isometric box in one drag.

1. Drag the **footprint** (the box's base on the ground) the same way as with **D-Para**.
2. The box goes straight up by **Height** pixels.

Prism options on the toolbar:

| Option | Description |
|---|---|
| **Height** | The box height in pixels (default 16). If it is 0, only the top face is drawn. |
| **Left** | Color of the left wall. Click the swatch to change it (default 170,170,170). |
| **Right** | Color of the right wall. Click the swatch to change it (default 110,110,110). |
| Top | The top face uses the normal drawing **Color**. |

The walls are drawn first and the top face last, so the top covers the edges where they meet.
The preview shows the three faces as dashed outlines in their colors, with `h=<height>`.

> Tip: Use darker colors for the walls than for the top face, to get Simutrans-style lighting (light from the upper left).

## Zoom and view

| Action | How |
|---|---|
| Zoom | **Zoom[%]** slider (25, 50, 100, 200, 400, 600, 800, 1000%) or **Ctrl + mouse wheel**. Ctrl + wheel zooms toward the mouse position. |
| Scroll vertically | Mouse wheel, or the scrollbar |
| Scroll horizontally | **Shift + mouse wheel**, or the scrollbar |
| Pan | Drag with the **right mouse button** |
| Pixel grid | Shown automatically at 600% zoom and above |

Next: [Selection and Editing](Selection-and-Editing)
