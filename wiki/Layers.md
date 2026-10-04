# Layers

An image can have several layers. All drawing and processing works on the **active layer** only.

## Layer panel (left side)

```
[✓] [thumb]   <- top layer (drawn last)
[✓] [thumb]   <- active layer (blue background)
[ ] [thumb]   <- hidden layer
```

- Layers are listed **top to bottom**. The first row is the top layer.
- **Click a thumbnail** to make that layer active. The active layer has a **blue** background.
- The **checkbox** shows or hides a layer. Hidden layers are **not saved** in File → Save.
- Layers other than the active one are shown darker on the canvas (display only).

## Layer tab

| Button | Action |
|---|---|
| **New Layer** | Adds an empty, transparent layer the size of the canvas, at the top. |
| **Duplicate Layer** | Copies the active layer, including its offset, and puts the copy directly above it. |
| **Delete Layer** | Deletes the active layer. You can't delete the last remaining layer. |
| **▲ Up / ▼ Down** | Moves the active layer up or down by one. |
| **Export Layer** | Saves the active layer by itself as a PNG (default name `layer_<n>.png`). |
| **Export All Layer** | Saves every layer as its own PNG. A save dialog opens once for each layer. |
| **Import to Layer** | Opens a PNG and adds it as a new top layer at offset (0, 0). It may have a different size from the canvas. |

> Exported layers are saved at the layer's own size and position. The layer offset is not applied.

## Merge Layer Down

Combines the **active layer** (upper) with the layer **directly below** it (lower). The result replaces the lower layer.
This doesn't work when the active layer is the bottom layer. Merging can be undone with a single **Ctrl + Z**.

Rules for every mode:

- Upper-layer pixels with the Simutrans background color **(231, 255, 255)** are ignored.
- **Special colors are protected.** If the upper or lower pixel is a Simutrans special color, the result is not calculated. Instead, the upper pixel is copied as-is (in **Replace** mode, the lower pixel is kept). This keeps lights and player colors exact.
- If the two layers have different offsets or sizes, the merged layer is enlarged to cover both.

| Button | Mode | Result for each color channel |
|---|---|---|
| **Add** | Add | `lower + upper` (limited to 255). Good for adding light. |
| **Mult** | Multiply | `lower × upper / 255`. Good for shadows and darkening. |
| **Replace** | Replace | Non-transparent upper pixels overwrite the lower ones. |
| **Bright** | Brightness | `max(lower, upper)`: the lighter of the two. |
| **Lightmap** | Lightmap | `lower × upper / 128`. Gray **128** leaves the lower color unchanged, darker grays shade it, and lighter grays brighten it. |

### Using Lightmap

1. Put the finished, unshaded image on the lower layer.
2. On the layer above it, paint shading in grays. 128 means no change. Tip: **Process → Turn gray** quickly turns a copy of the shape into flat 128 gray.
3. Make the gray layer active and press **Lightmap**.

> In Lightmap mode, **transparent pixels in the upper layer make the result transparent**, so the lightmap layer also works as a mask. Cover the whole object with gray.

## Layer Offset

Each layer can be moved relative to the canvas. The current offset is shown in the status bar as `Offset:(x,y)`.

| Control | Action |
|---|---|
| **X / Y + Apply** | The fields show the active layer's current offset. Enter new values and press **Apply** to move the layer there. |
| **← ↑ ↓ →** | Moves the layer by 1 pixel. Hold the button down to keep moving. |
| **Move** tool | Drag the layer with the mouse (see [Drawing Tools](Drawing-Tools)). |

Offset changes can be undone. One press or hold of an arrow button counts as one undo step.

Next: [Special Colors](Special-Colors)
