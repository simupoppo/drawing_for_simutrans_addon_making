# Special Colors

Simutrans treats some exact RGB values as **special colors**. They are drawn differently in the game. For example, some glow at night, and the player colors are replaced with each company's colors.
A special color only works if the RGB value is **exactly** right, so this tab gives you all of them as one-click swatches.

## Special Colors tab

| Control | Action |
|---|---|
| Color swatches | Click a swatch to set it as the drawing color. Alpha is not changed. |
| **Highlight Special Colors** | When checked, every pixel that is **not** a special color is shown in dark gray. Special colors keep their real color, so you can find them, and spot near-miss colors, at a glance. This affects the display only. |

## Color list

The palette contains these 30 colors, in order:

**Lights and windows** (14 colors)

| # | RGB | # | RGB |
|---|---|---|---|
| 1 | 107,107,107 | 8 | 255,33,29 |
| 2 | 155,155,155 | 9 | 1,221,1 |
| 3 | 179,179,179 | 10 | 227,227,255 |
| 4 | 201,201,201 | 11 | 193,177,209 |
| 5 | 223,223,223 | 12 | 77,77,77 |
| 6 | 127,155,241 | 13 | 255,1,127 |
| 7 | 255,255,83 | 14 | 1,1,255 |

**Player color 1** (8 shades, dark to light)

| Shade | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| RGB | 36,75,103 | 57,94,124 | 76,113,145 | 96,132,167 | 116,151,189 | 136,171,211 | 156,190,233 | 176,210,255 |

**Player color 2** (8 shades, dark to light)

| Shade | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| RGB | 123,88,3 | 142,111,4 | 161,134,5 | 180,157,7 | 198,180,8 | 217,203,10 | 236,226,11 | 255,249,13 |

For what each light or window color does in the game, see the Simutrans add-on documentation.

## Where special colors matter in this program

- **Merge Layer Down** never mixes special colors. They are copied unchanged (see [Layers](Layers)).
- **Color Replace** can skip pixels that are already special colors, and makes sure its results never turn into a special color by accident (see [Color Replace](Color-Replace)).
- **Turn gray** converts *all* non-transparent pixels, including special colors (see [Process Tab](Process-Tab)).

> Tip: Avoid ordinary colors that are *almost* a special color. Some image tools change colors slightly when they save. Check your result with **Highlight Special Colors**.

Next: [Process Tab](Process-Tab)
