# Color Replace

The **Color Replace** tab recolors every pixel of the **active layer** that is close to a chosen color, and keeps the shading.
Typical uses: changing the color of a whole vehicle body, or turning a painted area into **player colors**.

## Controls

| Control | Description |
|---|---|
| **Original (R,G,B)** | The color to look for, as `R,G,B` (default `255,0,0`). |
| **Update (R,G,B)** | The new color (default `0,0,255`). Used only in **Update Color** mode. |
| Color swatch | Click the small square next to a field to choose the color with a color picker. |
| **Use Current** | Copies the current drawing color into that field. Tip: use **Pipette** on the canvas first. |
| **Range (int or R,G,B)** | How far a pixel's color may be from *Original* and still match. Each of R, G and B is checked separately: `\|pixel − Original\| ≤ Range`. One number such as `16` uses the same range for all three. `R,G,B` such as `10,30,30` sets a range per channel. Default `16`. |
| **New Alpha** | The alpha value (0–255) given to replaced pixels (default 255). |
| **Ignore Special Color** | When checked (default), pixels that are already Simutrans special colors are left unchanged. |
| **Preview** | When checked (default), the pixels that would change are **darkened** on the canvas while this tab is open. |
| **Replace To** | **Update Color**, **Player 1** or **Player 2** (see below). |
| **Base Shade (= Original)** | In Player modes, choose which of the 8 player-color shades the *Original* color becomes. The selected shade has a red frame. Default: shade 6. |
| **Apply Replace** | Runs the replacement. The status bar shows how many pixels changed. |

Fully transparent pixels are never changed. Apply Replace can be undone with **Ctrl + Z**.

## Replace To: Update Color

Every matching pixel is **shifted** by the same amount as *Original* → *Update*:

```
new pixel = Update + (pixel − Original)
```

So a pixel slightly darker than *Original* becomes slightly darker than *Update*, and the shading is kept.
If a result would land exactly on a Simutrans special color, it is moved by one step so it doesn't turn into a special color by accident.

## Replace To: Player 1 / Player 2

Every matching pixel becomes one of the **8 player-color shades** (see [Special Colors](Special-Colors)):

1. The *Original* color itself becomes the **Base Shade** you selected.
2. Other matching pixels keep their brightness relative to *Original*. A pixel 20% darker than *Original* gets the shade closest to 20% darker than the Base Shade.

The result uses only real player-color values, so it changes color correctly in the game.

## Example: make a red car body use player color 1

1. Make the layer with the car active.
2. Open **Color Replace**, select **Pipette**, and click the body's main red. Then press **Use Current** next to *Original*.
3. Set **Range** so that the preview darkens the whole body, but not other parts such as tail lights. Try `24`, or `40,24,24` if the reds vary mostly in R.
4. Select **Replace To → Player 1**, and click a **Base Shade** (a mid-to-light shade usually looks right for the main body color).
5. Press **Apply Replace**. If you don't like the result, press **Ctrl + Z** and try another shade or range.

Next: [Keyboard and Mouse](Keyboard-and-Mouse)
