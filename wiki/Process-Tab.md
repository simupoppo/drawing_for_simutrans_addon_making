# Process Tab

## Simutrans Guides

Draws guide lines over the canvas to help you place graphics on the Simutrans tile grid. Guides are only displayed. They are never saved.

| Field | Meaning |
|---|---|
| **Show** | Shows or hides the guides. |
| **Build** | Build paksize: the size of one image cell in the PNG (default 128). |
| **Play** | Play paksize: the in-game tile size (default 128). It can't be larger than Build. A larger value is changed to the Build value. |
| **Y-Off** | Moves the ground-tile outline up or down, in pixels (default 0). |
| **Apply** | Applies the values above. |

What is drawn:

- **Cyan dashed lines**: a grid every *Build* pixels, so each cell matches one image in your `.dat` file.
- **Yellow diamond**: the ground-tile outline in each cell. It is *Play* wide and *Play / 2* high, centered horizontally, with its top at the cell's vertical center plus *Y-Off*.

Example: if you draw pak128 graphics on a larger 192-pixel cell (to leave room for tall objects), set **Build = 192** and **Play = 128**.

## Turn gray

Changes every pixel of the active layer to **128,128,128** (opaque), except:

- fully transparent pixels (0,0,0,0)
- the Simutrans background color (231,255,255)

It gives you a flat "neutral" silhouette of an object, which is a good starting point for a **Lightmap** shading layer (see [Layers](Layers)). It can be undone.

## Delete Background

Changes every pixel of the active layer that is exactly the Simutrans background color **(231, 255, 255)** to **transparent**.
Use this after opening older add-on images that use the cyan background instead of alpha. It can be undone.

## add margin (build_paksize)

Makes each cell bigger without scaling the drawing. The empty space is filled with transparency.

1. Make sure **Build** in *Simutrans Guides* is the **current** cell size.
2. Enter a **larger** size in **New Size**.
3. Press **Apply Resize**.

Each *Build*-sized cell becomes a *New Size* cell, with the original image **centered** in it. A 32×32 icon in the top-left corner of a cell, surrounded by transparency, stays in the top-left corner.
The **Build** value is updated to the new size, and every layer is processed.

- It only enlarges. A New Size smaller than or equal to the current Build does nothing.
- It can't be undone. Save first.

## Image Resize

**Scales** the whole image (every layer) from the current Build paksize to **New Size**, for example to turn pak128 graphics into pak64.

1. Make sure **Build** in *Simutrans Guides* is the **current** cell size.
2. Enter the target size in **New Size**.
3. Press **Apply Resize**.

**Build**, **Play** and **Y-Off** are scaled by the same ratio.
When shrinking, groups of pixels are merged into one in a way meant to keep the result sharp.

- It can't be undone. Save first.
- Check special colors afterwards with **Highlight Special Colors**, and touch them up if needed.

Next: [Color Replace](Color-Replace)
