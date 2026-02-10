import tkinter as tk
from tkinter import filedialog, colorchooser
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np


class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("drawing for simutrans addon making")

        # ---- image / layer ----
        self.layers = []   # [{img: ndarray, visible: bool}]
        self.active_layer = 0
        self.width = 0
        self.height = 0
        self.bg_pattern = self.create_base_tile() # 背景タイルを生成
        self.canvas_bg_ids = [] # 背景タイルオブジェクトのIDリスト

        # ---- undo / redo ----
        self.undo_stack = []
        self.redo_stack = []
        self.current_stroke = []

        # ---- view ----
        self.zoom_levels = [25, 50, 100, 200, 400, 600, 800, 1000]
        self.zoom = 1.0
        self.view_x = 0
        self.view_y = 0
        self.pan_start = None
        self.inactive_dim_factor = 0.4

        # ---- tool ----
        self.tool = "pen"
        self.draw_color = np.array([0, 0, 0, 255], dtype=np.uint8)

        self.layer_panels = []

        self.create_ui()

    # ================= UI =================
    def create_ui(self):
        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)


        # ---- top bar ----
        bar = tk.Frame(main)
        bar.pack(fill=tk.X)

        bar = tk.Frame(main)
        bar.pack(fill=tk.X)

        notebook = ttk.Notebook(bar)
        notebook.pack(fill=tk.X)

        tab_file = tk.Frame(notebook)
        tab_edit = tk.Frame(notebook)
        # tab_draw = tk.Frame(notebook)
        tab_layer = tk.Frame(notebook)
        tab_process = tk.Frame(notebook)

        notebook.add(tab_file, text="File")
        notebook.add(tab_edit, text="Edit")
        # notebook.add(tab_draw, text="Draw")
        notebook.add(tab_layer, text="Layer")
        notebook.add(tab_process, text="Process")

        tk.Button(tab_file, text="Open", command=self.open_image).pack(side=tk.LEFT)
        tk.Button(tab_file, text="Save", command=self.save_image).pack(side=tk.LEFT)
        tk.Button(tab_edit, text="Undo", command=self.undo).pack(side=tk.LEFT)
        tk.Button(tab_edit, text="Redo", command=self.redo).pack(side=tk.LEFT)

        tk.Button(bar, text="Pen", command=lambda: self.set_tool("pen")).pack(side=tk.LEFT)
        tk.Button(bar, text="Eraser", command=lambda: self.set_tool("eraser")).pack(side=tk.LEFT)
        tk.Button(bar, text="Pipette", command=lambda: self.set_tool("pipette")).pack(side=tk.LEFT)

        tk.Button(tab_layer, text="New Layer", command=self.add_layer).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Duplicate Layer", command=self.duplicate_layer).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="▲ Up", command=self.move_layer_up).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="▼ Down", command=self.move_layer_down).pack(side=tk.LEFT)
        tk.Button(bar, text="Color", command=self.choose_color).pack(side=tk.LEFT)
        tk.Button(
            tab_process,
            text="Turn gray",
            command=self.normalize_active_layer
        ).pack(side=tk.LEFT)
        tk.Button(
            tab_process,
            text="Delete Background",
            command=self.delete_background_active_layer
        ).pack(side=tk.LEFT)

        self.alpha = tk.Scale(bar, from_=0, to=255, resolution=8,
                              orient=tk.HORIZONTAL, label="Alpha",
                              command=self.set_alpha, length=120)
        self.alpha.set(255)
        self.alpha.pack(side=tk.LEFT)

        self.color_preview = tk.Canvas(bar, width=24, height=24, bd=1, relief="sunken")
        self.color_preview.pack(side=tk.LEFT, padx=4)

        self.zoom_scale = tk.Scale(bar, from_=0, to=len(self.zoom_levels)-1,
                                   orient=tk.HORIZONTAL, label="Zoom[%]",
                                   command=self.set_zoom_index, length=150)
        self.zoom_scale.set(2)
        self.zoom_scale.pack(side=tk.RIGHT)
        self.zoom_label = tk.Label(bar, text="100%")
        self.zoom_label.pack(side=tk.RIGHT, padx=4)

        # ---- body ----
        body = tk.Frame(main)
        body.pack(fill=tk.BOTH, expand=True)

        # ---- scroll bar ----
        self.hbar = tk.Scrollbar(body, orient=tk.HORIZONTAL)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar = tk.Scrollbar(body, orient=tk.VERTICAL)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ---- layer panel ----
        self.layer_frame = tk.Frame(body, width=120, relief="sunken", bd=1)
        self.layer_frame.pack(side=tk.LEFT, fill=tk.Y)

        # ---- canvas ----
        self.canvas = tk.Canvas(body, bd=0, highlightthickness=0,
                                xscrollcommand=self.hbar.set,
                                yscrollcommand=self.vbar.set)
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.hbar.config(command=self.canvas.xview)
        self.vbar.config(command=self.canvas.yview)

        # ---- footer ----
        self.info = tk.Label(main, anchor="w")
        self.info.pack(fill=tk.X)

        # ---- bindings ----
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_stroke)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan)
        self.canvas.bind("<MouseWheel>", self.zoom_wheel)
        self.canvas.bind("<Motion>", self.update_cursor_info)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan)
    def create_base_tile(self):
        """16x16pxの固定市松模様タイルを生成"""
        size = 8 # 1マスのサイズ。16x16のタイル内に4マス入る
        c1, c2 = (220, 220, 220, 255), (190, 190, 190, 255)
        data = np.zeros((size * 2, size * 2, 4), dtype=np.uint8)
        data[:size, :size] = c1
        data[size:, size:] = c1
        data[:size, size:] = c2
        data[size:, :size] = c2
        return ImageTk.PhotoImage(Image.fromarray(data, "RGBA"))
    # ================= Image I/O =================
    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if not path:
            return

        img = Image.open(path).convert("RGBA")
        base = np.array(img, dtype=np.uint8)

        self.height, self.width = base.shape[:2]
        self.layers = [{
            "img": base,
            "visible": True
        }]
        self.active_layer = 0

        self.undo_stack.clear()
        self.redo_stack.clear()

        self.view_x = self.view_y = 0
        self.zoom = 1.0
        self.zoom_scale.set(2)

        self.refresh_layer_panel()
        self.redraw()

    def save_image(self):
        if not self.layers:
            return

        # 本来の色で合成
        out = self.compose_layers(for_display=False)
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            Image.fromarray(out, "RGBA").save(path)

    # ================= Layers =================
    def add_layer(self):
        if not self.layers:
            return
        self.layers.append({
            "img": np.zeros((self.height, self.width, 4), dtype=np.uint8),
            "visible": True
        })
        self.active_layer = len(self.layers) - 1
        self.refresh_layer_panel()
        self.redraw()

    def toggle_layer(self, i, var):
        self.layers[i]["visible"] = var.get()
        self.redraw()

    def set_active_layer(self, i):
        self.active_layer = i
        self.refresh_layer_panel()
        self.redraw()

    def refresh_layer_panel(self):
        for w in self.layer_frame.winfo_children():
            w.destroy()

        for i, layer in enumerate(reversed(self.layers)):
            idx = len(self.layers) - 1 - i

            f = tk.Frame(self.layer_frame)
            f.pack(fill=tk.X, pady=2)

            var = tk.BooleanVar(value=layer["visible"])
            chk = tk.Checkbutton(f, variable=var,
                                 command=lambda i=idx, v=var: self.toggle_layer(i, v))
            chk.pack(side=tk.LEFT)

            thumb = Image.fromarray(layer["img"], "RGBA").resize((32, 32), Image.NEAREST)
            tkimg = ImageTk.PhotoImage(thumb)

            lbl = tk.Label(f, image=tkimg)
            lbl.image = tkimg
            lbl.pack(side=tk.LEFT)

            lbl.bind("<Button-1>", lambda e, i=idx: self.set_active_layer(i))

            if idx == self.active_layer:
                f.config(bg="#a0c0ff")

    def compose_layers(self, for_display=True):
        """
        レイヤーを合成する。
        for_display=True のときは非アクティブレイヤーを暗くし、
        for_display=False のときは本来の色でマージする。
        """
        # レイヤーがない場合は空の画像を返す
        if not self.layers:
            return np.zeros((self.height, self.width, 4), dtype=np.uint8)

        out = np.zeros_like(self.layers[0]["img"], dtype=np.float32)

        for i, layer in enumerate(self.layers):
            if not layer["visible"]:
                continue

            src = layer["img"].astype(np.float32)

            # --- 表示用の場合のみ、非アクティブレイヤーを暗くする ---
            if for_display and i != self.active_layer:
                src[..., :3] *= self.inactive_dim_factor

            # アルファブレンド処理
            alpha = src[..., 3:4] / 255.0
            out[..., :3] = out[..., :3] * (1 - alpha) + src[..., :3] * alpha
            out[..., 3:4] = np.maximum(out[..., 3:4], src[..., 3:4])

        return np.clip(out, 0, 255).astype(np.uint8)
    def duplicate_layer(self):
        if not self.layers:
            return

        src = self.layers[self.active_layer]

        new_layer = {
            "img": src["img"].copy(),
            "visible": src["visible"]
        }

        insert_index = self.active_layer + 1
        self.layers.insert(insert_index, new_layer)

        # Undo
        self.undo_stack.append(("add_layer", insert_index))
        self.redo_stack.clear()

        self.active_layer = insert_index
        self.refresh_layer_panel()
        self.redraw()
    def move_layer_up(self):
        i = self.active_layer
        if i >= len(self.layers) - 1:
            return

        self.layers[i], self.layers[i + 1] = self.layers[i + 1], self.layers[i]

        self.undo_stack.append(("move_layer", i, i + 1))
        self.redo_stack.clear()

        self.active_layer = i + 1
        self.refresh_layer_panel()
        self.redraw()
    def move_layer_down(self):
        i = self.active_layer
        if i <= 0:
            return

        self.layers[i], self.layers[i - 1] = self.layers[i - 1], self.layers[i]

        self.undo_stack.append(("move_layer", i, i - 1))
        self.redo_stack.clear()

        self.active_layer = i - 1
        self.refresh_layer_panel()
        self.redraw()
    # ================= Tools =================
    def set_tool(self, t):
        self.tool = t

    def choose_color(self):
        c = colorchooser.askcolor()
        if c[0]:
            self.draw_color[:3] = np.array(c[0], dtype=np.uint8)
            self.update_color_preview()

    def set_alpha(self, v):
        self.draw_color[3] = min(int(v),255)
        self.update_color_preview()

    def update_color_preview(self):
        r, g, b, _ = self.draw_color
        self.color_preview.delete("all")
        self.color_preview.create_rectangle(
            0, 0, 24, 24, fill=f"#{r:02x}{g:02x}{b:02x}", outline=""
        )
    
    # ================= Drawing =================
    def canvas_to_image(self, x, y):
        cx = self.canvas.canvasx(x)
        cy = self.canvas.canvasy(y)
        return int((cx) / self.zoom), int((cy) / self.zoom)

    def on_click(self, e):
        if not self.layers:
            return
        self.current_stroke = []

        ix, iy = self.canvas_to_image(e.x, e.y)

        if self.tool == "pipette":
            layer = self.layers[self.active_layer]["img"]
            if 0 <= ix < self.width and 0 <= iy < self.height:
                self.draw_color = layer[iy, ix].copy()
                self.alpha.set(self.draw_color[3])
                self.update_color_preview()
            self.tool = "pen"
        elif self.tool == "eraser":
            self.paint(ix, iy, True)
        else:
            self.paint(ix, iy, False)

    def on_drag(self, e):
        if self.tool != "pen" and self.tool != "eraser":
            return
        ix, iy = self.canvas_to_image(e.x, e.y)
        self.paint(ix, iy, self.tool == "eraser")

    def end_stroke(self, _):
        if self.current_stroke:
            self.undo_stack.append(self.current_stroke)
            self.redo_stack.clear()
        self.current_stroke = []

    def paint(self, x, y, eraser):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        layer = self.layers[self.active_layer]["img"]
        before = layer[y, x].copy()

        if eraser:
            color = np.array([0,0,0,0], dtype=np.uint8)
        else:
            color = self.draw_color

        if np.array_equal(before, color):
            return

        layer[y, x] = color
        self.current_stroke.append((self.active_layer, x, y, before))
        self.redraw()


    # ================= Using Changing Tools =================
    def normalize_active_layer(self):
        if not self.layers:
            return

        layer = self.layers[self.active_layer]["img"]

        # replace condition
        c1 = np.array([0, 0, 0, 0], dtype=np.uint8)
        c2 = np.array([231, 255, 255, 255], dtype=np.uint8)
        replace = np.array([128, 128, 128, 255], dtype=np.uint8)

        # check
        is_c1 = np.all(layer == c1, axis=-1)
        is_c2 = np.all(layer == c2, axis=-1)

        # mask region
        mask = ~(is_c1 | is_c2)

        # for Undo
        ys, xs = np.where(mask)
        stroke = []
        for y, x in zip(ys, xs):
            stroke.append(
                (self.active_layer, x, y, layer[y, x].copy())
            )

        if not stroke:
            return

        self.undo_stack.append(stroke)
        self.redo_stack.clear()

        # replace
        layer[mask] = replace

        self.redraw()
    def delete_background_active_layer(self):
        if not self.layers:
            return

        layer = self.layers[self.active_layer]["img"]

        c2 = np.array([231, 255, 255, 255], dtype=np.uint8)
        replace = np.array([0, 0, 0, 0], dtype=np.uint8)

        is_c2 = np.all(layer == c2, axis=-1)

        mask = is_c2

        ys, xs = np.where(mask)
        stroke = []
        for y, x in zip(ys, xs):
            stroke.append(
                (self.active_layer, x, y, layer[y, x].copy())
            )

        if not stroke:
            return

        self.undo_stack.append(stroke)
        self.redo_stack.clear()

        layer[mask] = replace

        self.redraw()

    # ================= Undo / Redo =================
    def undo(self):
        if not self.undo_stack:
            return
        stroke = self.undo_stack.pop()

        if isinstance(stroke, tuple) and stroke[0] == "move_layer":
            _, src, dst = stroke
            self.layers[src], self.layers[dst] = self.layers[dst], self.layers[src]
            self.redo_stack.append(("move_layer", dst, src))
            self.active_layer = src
            self.refresh_layer_panel()
            self.redraw()
            return
        redo = []
        for l, x, y, before in stroke:
            redo.append((l, x, y, self.layers[l]["img"][y, x].copy()))
            self.layers[l]["img"][y, x] = before
        self.redo_stack.append(redo)
        self.redraw()

    def redo(self):
        if not self.redo_stack:
            return
        stroke = self.redo_stack.pop()

        if isinstance(stroke, tuple) and stroke[0] == "move_layer":
            _, src, dst = stroke
            self.layers[src], self.layers[dst] = self.layers[dst], self.layers[src]
            self.undo_stack.append(("move_layer", dst, src))
            self.active_layer = dst
            self.refresh_layer_panel()
            self.redraw()
            return
        undo = []
        for l, x, y, before in stroke:
            undo.append((l, x, y, self.layers[l]["img"][y, x].copy()))
            self.layers[l]["img"][y, x] = before
        self.undo_stack.append(undo)
        self.redraw()

    # ================= View =================
    def set_zoom_index(self, v):
        # 1. 現在の表示中心（比率 0.0 ~ 1.0）を記録
        # xview() は (現在の表示開始比率, 現在の表示終了比率) を返す
        x_left, x_right = self.canvas.xview()
        y_top, y_bottom = self.canvas.yview()
        
        center_x = (x_left + x_right) / 2
        center_y = (y_top + y_bottom) / 2

        # 2. ズーム倍率を更新
        self.zoom = self.zoom_levels[int(v)] / 100.0
        self.zoom_label.config(text=f"{self.zoom_levels[int(v)]}%")
        
        # 3. 再描画（ここで scrollregion が更新される）
        self.redraw()

        # 4. 記録しておいた中心位置へスクロールを戻す
        # movetoは「表示領域の左端」を指定するため、中心から表示幅の半分を引く
        view_width = x_right - x_left
        view_height = y_bottom - y_top
        
        self.canvas.xview_moveto(center_x - view_width / 2)
        self.canvas.yview_moveto(center_y - view_height / 2)

    def zoom_wheel(self, e):
        # ズーム前のマウス下のピクセル座標を記録
        mx = self.canvas.canvasx(e.x)
        my = self.canvas.canvasy(e.y)

        # ズーム倍率変更
        i = self.zoom_scale.get()
        old_zoom = self.zoom
        if e.delta > 0 and i < len(self.zoom_levels) - 1:
            i += 1
        elif e.delta < 0 and i > 0:
            i -= 1
        
        if i == self.zoom_scale.get(): return
        
        self.zoom_scale.set(i) # これで redraw() が呼ばれる
        self.zoom = self.zoom_levels[i] / 100.0

        # ズーム後の「マウスがあったピクセル」の新しいCanvas座標
        new_mx = mx * (self.zoom / old_zoom)
        new_my = my * (self.zoom / old_zoom)

        # 新しい座標がマウスの元の位置（e.x, e.y）に来るようにスクロール
        self.canvas.xview_moveto((new_mx - e.x) / (self.width * self.zoom))
        self.canvas.yview_moveto((new_my - e.y) / (self.height * self.zoom))
    def start_pan(self, e):
        self.canvas.scan_mark(e.x, e.y)

    def pan(self, e):
        self.canvas.scan_dragto(e.x, e.y, gain=1)
        self.redraw()

    # ================= Rendering =================
    def redraw(self):
        if not self.layers or self.width == 0:
            return

        # 1. 表示範囲の取得
        x_start, x_end = self.canvas.xview()
        y_start, y_end = self.canvas.yview()

        # 2. 画像上の座標に変換
        ix1 = int(x_start * self.width)
        iy1 = int(y_start * self.height)
        ix2 = int(np.ceil(x_end * self.width))
        iy2 = int(np.ceil(y_end * self.height))

        ix1, iy1 = max(0, ix1), max(0, iy1)
        ix2, iy2 = min(self.width, ix2), min(self.height, iy2)

        if ix2 <= ix1 or iy2 <= iy1: return

        # 3. 表示範囲を切り出し
        img_full = self.compose_layers()
        img_crop = img_full[iy1:iy2, ix1:ix2]

        crop_h, crop_w = img_crop.shape[:2]
        disp_w = int(crop_w * self.zoom)
        disp_h = int(crop_h * self.zoom)

        # 4. 背景の市松模様を生成 (エラー修正ポイント)
        bg_size = 8
        yy, xx = np.indices((disp_h, disp_w))
        
        # オフセット計算（スクロールしても模様がズレないように調整）
        offset_x = int(ix1 * self.zoom) % (bg_size * 2)
        offset_y = int(iy1 * self.zoom) % (bg_size * 2)
        
        checker = ((xx + offset_x) // bg_size + (yy + offset_y) // bg_size) % 2
        
        # 3チャンネル(RGB)の配列を確実に作成
        bg_rgb = np.zeros((disp_h, disp_w, 3), dtype=np.uint8)
        bg_rgb[checker == 0] = [220, 220, 220] # 明るいグレー
        bg_rgb[checker == 1] = [190, 190, 190] # 濃いグレー
        
        # PILに変換してからRGBAに
        bg_pil = Image.fromarray(bg_rgb, "RGB").convert("RGBA")

        # 5. 前景を合成
        fg_pil = Image.fromarray(img_crop, "RGBA").resize((disp_w, disp_h), Image.NEAREST)
        bg_pil.alpha_composite(fg_pil)

        # 6. Canvasに描画
        self.tkimg = ImageTk.PhotoImage(bg_pil)
        self.canvas.delete("all")
        
        self.canvas.create_image(
            self.canvas.canvasx(0), 
            self.canvas.canvasy(0), 
            image=self.tkimg, 
            anchor="nw"
        )

        # 全体サイズを維持
        zw, zh = int(self.width * self.zoom), int(self.height * self.zoom)
        self.canvas.config(scrollregion=(0, 0, zw, zh))
        
        self.update_footer()

    def update_cursor_info(self, e):
        ix, iy = self.canvas_to_image(e.x, e.y)
        self.cursor_x = ix if 0 <= ix < self.width else None
        self.cursor_y = iy if 0 <= iy < self.height else None
        self.update_footer()

    def update_footer(self):
        r, g, b, a = self.draw_color
        pos = ""
        if self.cursor_x is not None:
            pos = f"  Pos:({self.cursor_x},{self.cursor_y})"
        self.info.config(
            text=f"Tool:{self.tool}  Layer:{self.active_layer+1}/{len(self.layers)}  "
                 f"RGBA({r},{g},{b},{a})  Zoom:{int(self.zoom*100)}%{pos}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    ImageEditor(root)
    root.mainloop()
