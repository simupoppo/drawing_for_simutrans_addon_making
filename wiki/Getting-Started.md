# Getting Started

## Running the program

### Windows executable

Download `drawing_for_simutrans_addon_making.exe` and double-click it. You don't need to install anything.

### Running from source

You need Python 3 and these packages:

```
pip install pillow numpy
pip install pywin32   # optional: lets Copy put images on the Windows clipboard
```

Keep `change_image_paksize.py` and `png_merge_for_simutrans.py` in the same folder as the main script, then run:

```
python drawing_for_simutrans_addon_making.py
```

To build the exe yourself, install PyInstaller and run `make build`. The exe is written to `dist/`.

## Screen layout

```
+----------------------------------------------------------------------------+
| [File] [Edit] [Special Colors] [Layer] [Process] [Color Replace]  <- tabs  |
|  (buttons for the selected tab)                                            |
+----------------------------------------------------------------------------+
| Pen Fill Line Eraser Pipette Move Select ParaSelect Rect FillRect Prism    |
| (tool options)  Color  Alpha[----]  [■]                    100%  Zoom[---] |
+---------+------------------------------------------------------------------+
| Layer   |                                                                  |
| panel   |                         Canvas                                   |
|         |                                                                  |
+---------+------------------------------------------------------------------+
| Tool:pen  Layer:1/1  RGBA(0,0,0,255)  Zoom:100%  Offset:(0,0)  Pos:(12,34) |
+----------------------------------------------------------------------------+
```

| Area | Description |
|---|---|
| **Tabs** | Groups of commands: file, edit, special colors, layer, process and color replace. |
| **Toolbar** | Drawing tools, the **Color** button, the **Alpha** slider, a preview of the current color, and zoom. Some tools (Rect, FillRect, ParaSelect, Prism) show extra options next to the tool buttons. |
| **Layer panel** | One row per layer, with the top layer first. See [Layers](Layers). |
| **Canvas** | The image. Transparent areas show a gray checkerboard. At 600% zoom and above, a 1-pixel grid is shown. |
| **Status bar** | The current tool, active layer, current color (RGBA), zoom, the active layer's offset, and the pixel under the cursor. Some commands, such as Color Replace, also show messages here. |

> Layers other than the active one are shown **darker** on the canvas, so you can see which layer you are editing. This only affects the display. Saved images are not darkened.

## File tab

| Button | Action |
|---|---|
| **New** | Creates a new transparent canvas. A dialog asks for **Width** and **Height** (the default is the current Build paksize, 128). |
| **Open** | Opens a PNG file as a single layer. |
| **Save** | Saves to the current file. If the image has not been saved yet, this works like **Save As...**. |
| **Save As...** | Saves to a new PNG file. |
| **Language** | Switches the user interface between **English** and **日本語** (Japanese). See below. |

### What gets saved

**Save** and **Save As...** combine all **visible** layers into **one flat PNG** with alpha:

- Hidden layers are **not** included.
- Parts of a layer that are outside the canvas because of its offset are cut off.
- Layers are **not** stored in the file. To keep layers separately, use **Layer → Export Layer** or **Export All Layer** (see [Layers](Layers)).

### Language

On the first start, the program uses Japanese if Windows is set to Japanese, and English otherwise.
To change it, choose **English** or **日本語** in **File → Language**. All labels change immediately, and the choice is remembered for the next start.

This manual uses the English labels. The Japanese labels are defined in `translate_jp.py`.

### Unsaved changes

If you click **New** or **Open**, or close the window, while you have unsaved changes, a dialog asks what to do:

- **Save**: save and continue
- **Save As...**: save to a new file and continue
- **Don't Save**: discard the changes and continue
- Closing the dialog cancels the action.

Next: [Drawing Tools](Drawing-Tools)
