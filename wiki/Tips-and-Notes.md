# Tips and Notes

## Sample workflow: a simple building

1. **File → New**, 128 × 128.
2. **Process → Simutrans Guides**: Build `128`, Play `128`, and **Apply**. The yellow diamond shows the ground tile.
3. Select **Prism**, set **Height** (e.g. `40`), choose the wall colors, set the main **Color** for the roof, and drag the footprint along the yellow diamond.
4. **Layer → New Layer**. Draw windows with **Special Colors** swatches using **Pen**, **Rect** or **FillRect** with **H-Para** so they follow the walls.
5. Add details such as doors and signs on more layers. Use **Line** with **Shift** for clean 2:1 edges.
6. Optional: on a layer of 128 gray (**Turn gray** on a duplicate), paint shading and merge it down with **Lightmap**.
7. Check **Special Colors → Highlight Special Colors** to confirm the lights and player colors are exact.
8. **File → Save As...** to write the PNG for makeobj.

## Behavior worth knowing

- **Save combines layers.** The saved PNG contains only the visible layers, merged into one. Use **Export All Layer** if you want to keep each layer as a separate PNG to work on later.
- **Paste uses the Windows clipboard first.** If you copied an image in another program, Ctrl+V pastes that image, even after you copied a **ParaSelect** area here, because ParaSelect copies only to the program's own clipboard. Copying a rectangle selection here replaces the Windows clipboard, so this only affects ParaSelect copies.
- **add margin** and **Image Resize** can't be undone. Save before using them.
- **Pipette** reads from the active layer, not the combined image. Switch to the layer that has the color first.
- The checkerboard and the darkening of inactive layers are display only and never saved.
- The language setting is saved in `.drawing_for_simutrans_addon_making.json` in your user folder. Delete this file to go back to automatic language detection.
- On high-DPI screens (Windows scaling above 100%), the program sets itself as DPI-aware, so the mouse position matches the pixel you click.

## Troubleshooting

| Problem | Solution |
|---|---|
| Drawing has no effect | Check that the **active layer** (blue in the layer panel) is the one you expect, and that it is visible. |
| A drawn color looks semi-transparent | The **Alpha** slider is below 255. The Pipette also copies the alpha of the pixel you click. |
| A merge mode left some pixels unchanged | Those pixels are special colors or the background color (231,255,255), which merging leaves unchanged on purpose. |
| Color Replace says "no pixels in range" | Increase **Range**, check the **Original** color, or turn off **Ignore Special Color** if the target is a special color. |
| Paste puts in an unexpected image | The Windows clipboard contains another image. See *Paste uses the Windows clipboard first* above. |
