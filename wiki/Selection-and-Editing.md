# Selection and Editing

## Selection tools

### Select (rectangle)
Drag on the canvas to select a rectangle. The selection is shown with a black-and-white dashed border.

- **Ctrl + A** selects the whole active layer.
- **Esc** removes the selection.

### ParaSelect (shaped selection)
Selects an area with the same shapes as the Rect tool. Choose the shape on the toolbar:

- **Box**: a rectangle
- **H-Para**: a wall-shaped parallelogram
- **D-Para**: an isometric diamond or parallelogram

This is useful for cutting out exactly one wall face or one ground tile.

> Switching to any tool other than Select or ParaSelect removes the current selection.

## Edit tab

| Button | Shortcut | Action |
|---|---|---|
| **Undo** | Ctrl + Z | Undoes the last change. |
| **Redo** | Ctrl + Y | Redoes the last undone change. |
| **Copy** | Ctrl + C | Copies the selected part of the active layer. |
| **Cut** | Ctrl + X | Copies the selection, then makes that area transparent. |
| **Paste** | Ctrl + V | Pastes an image as a floating image you can move (see below). |
| **Clear Outside** | — | Makes everything on the active layer **outside** the selection transparent. |
| **Confirm Paste** | Enter | Places the floating image onto the active layer. This button appears only while you are pasting. |

### Copy details

- **Rectangle selection**: the area is copied to the program's own clipboard and, if `pywin32` is available, to the **Windows clipboard** as a PNG with alpha. You can paste it into other image editors.
- **ParaSelect selection**: the shape's bounding box is copied, with everything outside the shape made transparent. This copy goes to the program's **own clipboard only**.

### Pasting

1. Press **Paste** or **Ctrl + V**.
   - If the **Windows clipboard contains an image**, that image is pasted.
   - Otherwise, the last image copied inside this program is pasted.
2. The image appears as a **floating image** with a dashed border, at the top-left corner of the current rectangle selection, or at (0, 0) if there is none.
3. **Drag** it to where you want it.
4. Press **Enter** or **Confirm Paste** to place it. Selecting another tool also places it.

The pasted image is **alpha-blended** onto the active layer, so its transparent pixels keep what is underneath.

## Undo / Redo

Undo and redo cover painting, lines, shapes, fill, paste, cut, Clear Outside, Turn gray, Delete Background, Color Replace, all layer operations (New, Duplicate, Delete, Import, Up / Down, Merge), and layer offset changes (Move tool, offset arrows, Layer Offset → Apply).

**add margin** and **Image Resize** (Process tab) are **not** undoable, so save before using them.

Opening a file or creating a new canvas clears the undo history.

Next: [Layers](Layers)
