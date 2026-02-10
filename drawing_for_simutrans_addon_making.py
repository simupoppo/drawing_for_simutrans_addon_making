import tkinter as tk
from tkinter import filedialog, colorchooser
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import change_image_paksize
import png_merge_for_simutrans


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
        self.after_id = None

        # ---- view ----
        self.zoom_levels = [25, 50, 100, 200, 400, 600, 800, 1000]
        self.zoom = 1.0
        self.cursor_x = None  # 初期化を追加
        self.cursor_y = None  # 初期化を追加
        self.view_x = 0
        self.view_y = 0
        self.pan_start = None
        self.inactive_dim_factor = 0.4

        # ---- tool ----
        self.tool = "pen"
        self.floating_image = None  # 貼り付け中の画像 (ndarray)
        self.floating_x = 0         # 貼り付け中のX座標 (キャンバス基準)
        self.floating_y = 0         # 貼り付け中のY座標 (キャンバス基準)
        self.is_dragging_floating = False
        self.draw_color = np.array([0, 0, 0, 255], dtype=np.uint8)

        self.layer_panels = []
        # ---- selection ----
        self.selection_rect = None  # [x1, y1, x2, y2] (キャンバス上のピクセル座標)
        self.clipboard = None       # コピーされた画像データ (ndarray)
        self.selection_id = None    # キャンバス上の枠オブジェクトID
        
        # ---- Simutrans Settings ----
        self.build_paksize = 128
        self.play_paksize = 128
        self.show_grid = True
        self.base_offset_y = 0  # 菱形の上下オフセット
        self.show_base_tile = True

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

        # create_ui メソッド内、各ボタン作成部分を以下のように書き換え
        self.tool_btns = {}

        btn_pen = tk.Button(bar, text="Pen", command=lambda: self.set_tool("pen"))
        btn_pen.pack(side=tk.LEFT)
        self.tool_btns["pen"] = btn_pen

        btn_eraser = tk.Button(bar, text="Eraser", command=lambda: self.set_tool("eraser"))
        btn_eraser.pack(side=tk.LEFT)
        self.tool_btns["eraser"] = btn_eraser

        btn_pipette = tk.Button(bar, text="Pipette", command=lambda: self.set_tool("pipette"))
        btn_pipette.pack(side=tk.LEFT)
        self.tool_btns["pipette"] = btn_pipette

        btn_move = tk.Button(bar, text="Move", command=lambda: self.set_tool("move"))
        btn_move.pack(side=tk.LEFT)
        self.tool_btns["move"] = btn_move

        # ツールバーに追加
        btn_select = tk.Button(bar, text="Select", command=lambda: self.set_tool("select"))
        btn_select.pack(side=tk.LEFT)
        self.tool_btns["select"] = btn_select

        # Editタブに追加
        tk.Button(tab_edit, text="Copy", command=self.copy_selection).pack(side=tk.LEFT)
        tk.Button(tab_edit, text="Paste", command=self.paste_image).pack(side=tk.LEFT)
        self.btn_confirm = tk.Button(tab_edit, text="Confirm Paste", bg="#ffcc00", 
                                     command=self.finalize_paste)
        self.btn_confirm.pack(side=tk.LEFT, padx=5)

        tk.Button(tab_layer, text="New Layer", command=self.add_layer).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Duplicate Layer", command=self.duplicate_layer).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Delete Layer", command=self.delete_layer).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="▲ Up", command=self.move_layer_up).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="▼ Down", command=self.move_layer_down).pack(side=tk.LEFT)
        # レイヤー操作タブなどに追加
        tk.Button(tab_layer, text="Export Layer", command=lambda:self.save_layer(-1)).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Export All Layer", command=self.save_all_layers).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Import to Layer", command=self.import_to_layer).pack(side=tk.LEFT)
        # --- Offset GUI ---
        off_ui_frame = tk.LabelFrame(tab_layer, text="Layer Offset")
        off_ui_frame.pack(side=tk.LEFT, padx=5, pady=2)

        tk.Label(off_ui_frame, text="X:").grid(row=0, column=0)
        self.off_x_entry = tk.Entry(off_ui_frame, width=5)
        self.off_x_entry.grid(row=0, column=1)

        tk.Label(off_ui_frame, text="Y:").grid(row=0, column=2)
        self.off_y_entry = tk.Entry(off_ui_frame, width=5)
        self.off_y_entry.grid(row=0, column=3)

        tk.Button(off_ui_frame, text="Apply", command=self.apply_offset_entry).grid(row=0, column=4, padx=5)
        
        # オフセット操作用（長押し対応版）
        off_frame = tk.Frame(tab_layer)
        off_frame.pack(side=tk.LEFT, padx=10)

        directions = [
            ("←", -1, 0, 1, 0),
            ("↑", 0, -1, 0, 1),
            ("↓", 0, 1, 2, 1),
            ("→", 1, 0, 1, 2)
        ]

        for text, dx, dy, r, c in directions:
            btn = tk.Button(off_frame, text=text)
            btn.grid(row=r, column=c)
            # マウス左ボタン押し下げでループ開始
            btn.bind("<ButtonPress-1>", lambda e, x=dx, y=dy: self.start_offset_loop(x, y))
            # マウスを離す、またはボタン外に出た時にループ停止
            btn.bind("<ButtonRelease-1>", self.stop_offset_loop)
            btn.bind("<Leave>", self.stop_offset_loop)
        # --- Simutrans Config GUI ---
        sim_frame = tk.LabelFrame(tab_process, text="Simutrans Guides")
        sim_frame.pack(side=tk.LEFT, padx=5)
        self.guide_var = tk.BooleanVar(value=True)
        tk.Checkbutton(sim_frame, text="Show", variable=self.guide_var, 
                       command=self.update_sim_settings).grid(row=0, column=0)

        tk.Label(sim_frame, text="Build:").grid(row=0, column=1)
        self.build_entry = tk.Entry(sim_frame, width=4)
        self.build_entry.insert(0, "128")
        self.build_entry.grid(row=0, column=2)

        tk.Label(sim_frame, text="Play:").grid(row=0, column=3)
        self.play_entry = tk.Entry(sim_frame, width=4)
        self.play_entry.insert(0, "128")
        self.play_entry.grid(row=0, column=4)

        tk.Label(sim_frame, text="Y-Off:").grid(row=0, column=5)
        self.base_off_entry = tk.Entry(sim_frame, width=4)
        self.base_off_entry.insert(0, "0")
        self.base_off_entry.grid(row=0, column=6)

        tk.Button(sim_frame, text="Apply", command=self.update_sim_settings).grid(row=0, column=7, padx=5)
        # color
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
        res_frame = tk.LabelFrame(tab_process, text="add margin (build_paksize)")
        res_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(res_frame, text="New Size:").grid(row=0, column=0)
        self.new_build_entry = tk.Entry(res_frame, width=6)
        self.new_build_entry.insert(0, str(self.build_paksize))
        self.new_build_entry.grid(row=0, column=1)

        tk.Button(res_frame, text="Apply Resize", 
                  command=self.execute_canvas_resize,
                  bg="#ffd0d0").grid(row=0, column=2, padx=5)
        res_frame = tk.LabelFrame(tab_process, text="Image Resize")
        res_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(res_frame, text="New Size:").grid(row=0, column=0)
        self.new_build_entry2 = tk.Entry(res_frame, width=6)
        self.new_build_entry2.insert(0, str(self.build_paksize))
        self.new_build_entry2.grid(row=0, column=1)

        tk.Button(res_frame, text="Apply Resize", 
                  command=self.execute_rescale,
                  bg="#ffd0d0").grid(row=0, column=2, padx=5)

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
        self.root.bind("<Control-c>", lambda e: self.copy_selection())
        self.root.bind("<Control-v>", lambda e: self.paste_image())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Escape>", self.clear_selection)
        self.root.bind("<Return>", lambda e: self.finalize_paste())

    def clear_selection(self, event=None):
        self.selection_rect = None
        self.redraw()
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

    def delete_layer(self):
        if len(self.layers) <= 1:
            return # 最後の1枚は消さない
        
        self.layers.pop(self.active_layer)
        self.active_layer = max(0, self.active_layer - 1)
        self.refresh_layer_panel()
        self.redraw()

    def compose_layers(self, for_display=True):
        if not self.layers:
            return np.zeros((self.height, self.width, 4), dtype=np.uint8)

        # キャンバスサイズの出力バッファ
        out = np.zeros((self.height, self.width, 4), dtype=np.float32)

        for i, layer in enumerate(self.layers):
            if not layer["visible"]: continue
            
            # 各レイヤーの現在の位置とサイズを取得
            src = layer["img"].astype(np.float32)
            lh, lw = src.shape[:2]
            ox, oy = layer.get("off_x", 0), layer.get("off_y", 0)

            # キャンバスとレイヤーが重なる範囲を計算（非破壊の鍵）
            x1, y1 = max(0, ox), max(0, oy)
            x2, y2 = min(self.width, ox + lw), min(self.height, oy + lh)

            if x2 > x1 and y2 > y1:
                # 転送元（レイヤー画像）のどの部分を使うか
                sx1, sy1 = x1 - ox, y1 - oy
                sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)
                
                crop = src[sy1:sy2, sx1:sx2]
                
                if for_display and i != self.active_layer:
                    crop[..., :3] *= self.inactive_dim_factor

                alpha = crop[..., 3:4] / 255.0
                out[y1:y2, x1:x2, :3] = out[y1:y2, x1:x2, :3] * (1 - alpha) + crop[..., :3] * alpha
                out[y1:y2, x1:x2, 3:4] = np.maximum(out[y1:y2, x1:x2, 3:4], crop[..., 3:4])

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
    def import_to_layer(self):
        if not self.layers:
            return
            
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if not path:
            return

        # 1. 読み込み画像をそのままNumPy配列にする
        import_img = Image.open(path).convert("RGBA")
        import_np = np.array(import_img, dtype=np.uint8)

        # 2. 新しいレイヤーとして追加（切り抜かず、オフセット0で配置）
        self.layers.append({
            "img": import_np,   # 画像データそのもの
            "visible": True,
            "off_x": 0,         # 表示開始位置X
            "off_y": 0          # 表示開始位置Y
        })
        
        self.active_layer = len(self.layers) - 1
        self.refresh_layer_panel()
        self.redraw()
    def offset_layer(self, dx, dy):
        """オフセット値を更新してレイヤーを移動させる（非破壊）"""
        if not self.layers:
            return
            
        layer = self.layers[self.active_layer]
        layer["off_x"] = layer.get("off_x", 0) + dx
        layer["off_y"] = layer.get("off_y", 0) + dy
        
        self.redraw()
    def save_layer(self,which):
        if not self.layers:
            return
        if(which<0):
            # call active layer
            which = self.active_layer
        
        layer_img = self.layers[which]["img"]
        path = filedialog.asksaveasfilename(
            title="選択中のレイヤーを保存",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile=f"layer_{which + 1}.png"
        )
        if path:
            Image.fromarray(layer_img, "RGBA").save(path)
    def save_all_layers(self):
        if not self.layers:
            return
        for i in range(len(self.layers)):
            self.save_layer(i)
    # ================= Tools =================
    def set_tool(self, tool_name):
        self.tool = tool_name
        
        # すべてのボタンの外見をデフォルトに戻す
        for name, btn in self.tool_btns.items():
            btn.config(relief=tk.RAISED, bg="SystemButtonFace") # 標準の背景色

        # 選択されたツールだけ強調
        if tool_name in self.tool_btns:
            # relief=tk.SUNKEN で押し込まれた見た目にする
            # bg="lightblue" などで色を変えるとより分かりやすい
            self.tool_btns[tool_name].config(relief=tk.SUNKEN, bg="#ADD8E6")
        if tool_name!="select":
            self.clear_selection()
        
        self.redraw()

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
    def update_sim_settings(self):
        try:
            self.show_grid = self.guide_var.get()
            self.build_paksize = int(self.build_entry.get())
            p_size = int(self.play_entry.get())
            
            # play_paksize が build_paksize より大きい場合は制限
            if p_size > self.build_paksize:
                p_size = self.build_paksize
                self.play_entry.delete(0, tk.END)
                self.play_entry.insert(0, str(p_size))
            
            self.play_paksize = p_size
            self.base_offset_y = int(self.base_off_entry.get())
            
            self.redraw()
        except ValueError:
            pass
    def execute_canvas_resize(self):
        try:
            new_pak = int(self.new_build_entry.get())
            old_pak = self.build_paksize
            
            if new_pak <= old_pak:
                return

            # 1. すべてのレイヤーの画像を変換
            for layer in self.layers:
                # 外部のプログラムを呼び出す
                layer["img"] = change_image_paksize.change_paksize_program(layer["img"], old_pak, new_pak, 3)
            
            # 2. キャンバス自体のサイズ設定を更新
            # ※全レイヤーが同じサイズになる前提の場合
            self.width = int(self.width*new_pak/old_pak)
            self.height = int(self.width*new_pak/old_pak)
            self.build_paksize = new_pak
            self.build_entry.delete(0, tk.END)
            self.build_entry.insert(0, str(new_pak))
            
            # 3. UIの整合性をとる
            self.update_sim_settings() # play_paksizeのバリデーション等
            self.refresh_layer_panel()
            self.redraw()
            
            print(f"Canvas resized to pak{new_pak}")
            
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Error", "Valid paksize required")
    def execute_rescale(self):
        try:
            new_pak = int(self.new_build_entry2.get())
            old_pak = self.build_paksize
            
            if new_pak == old_pak:
                return

            # 1. すべてのレイヤーの画像を変換
            for layer in self.layers:
                # 外部のプログラムを呼び出す
                layer["img"] = png_merge_for_simutrans.resize_program(layer["img"], old_pak, new_pak, 0,2)
            
            # 2. キャンバス自体のサイズ設定を更新
            # ※全レイヤーが同じサイズになる前提の場合
            self.width = int(self.width*new_pak/old_pak)
            self.height = int(self.width*new_pak/old_pak)
            self.play_paksize = int(self.play_paksize*new_pak/old_pak)
            self.play_entry.delete(0, tk.END)
            self.play_entry.insert(0, str(self.play_paksize))
            self.build_paksize = new_pak
            self.build_entry.delete(0, tk.END)
            self.build_entry.insert(0, str(new_pak))
            self.base_offset_y = int(self.base_offset_y*new_pak/old_pak)
            self.base_off_entry.delete(0, tk.END)
            self.base_off_entry.insert(0, str(self.base_offset_y))
            
            # 3. UIの整合性をとる
            self.update_sim_settings() # play_paksizeのバリデーション等
            self.refresh_layer_panel()
            self.redraw()
            
            print(f"Canvas resized to pak{new_pak}")
            
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Error", "Valid paksize required")
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
        if self.tool == "move_paste" and self.floating_image is not None:
            # ドラッグ開始位置の記録
            self.drag_start_pos = (ix, iy)
            self.floating_start_pos = (self.floating_x, self.floating_y)
            return
        if self.tool == "select":
            self.selection_rect = [ix, iy, ix, iy]
            return
        if self.tool == "move":
            # ドラッグ開始時のマウス位置と現在のオフセットを記録
            layer = self.layers[self.active_layer]
            self.drag_start_pos = (ix, iy)
            self.drag_start_offset = (layer.get("off_x", 0), layer.get("off_y", 0))
        elif self.tool == "pipette":
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
        if self.tool == "pipette":
            return
        ix, iy = self.canvas_to_image(e.x, e.y)
        if self.tool == "move_paste" and self.floating_image is not None:
            dx = ix - self.drag_start_pos[0]
            dy = iy - self.drag_start_pos[1]
            self.floating_x = self.floating_start_pos[0] + dx
            self.floating_y = self.floating_start_pos[1] + dy
            self.redraw()
            return
        if self.tool == "select":
            if self.selection_rect:
                self.selection_rect[2] = ix
                self.selection_rect[3] = iy
                self.redraw()
            return
        if self.tool == "move":
            dx = ix - self.drag_start_pos[0]
            dy = iy - self.drag_start_pos[1]
            layer = self.layers[self.active_layer]
            layer["off_x"] = self.drag_start_offset[0] + dx
            layer["off_y"] = self.drag_start_offset[1] + dy
            self.redraw()
        else:
            self.paint(ix, iy, self.tool == "eraser")

    def end_stroke(self, _):
        if self.tool == "select" and self.selection_rect:
            x1, y1, x2, y2 = self.selection_rect
            if x1 == x2 or y1 == y2:
                self.selection_rect = None
                self.redraw()
        if self.current_stroke:
            self.undo_stack.append(self.current_stroke)
            self.redo_stack.clear()
        self.current_stroke = []

    def paint(self, x, y, eraser):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        layer_dict = self.layers[self.active_layer]
        layer_img = layer_dict["img"]
        
        # キャンバス座標をレイヤー内の相対座標に変換
        ox = layer_dict.get("off_x", 0)
        oy = layer_dict.get("off_y", 0)
        lx, ly = x - ox, y - oy

        # レイヤーの画像範囲外なら描画しない（あるいは自動拡張させることも可能）
        lh, lw = layer_img.shape[:2]
        if not (0 <= lx < lw and 0 <= ly < lh):
            return

        before = layer_img[ly, lx].copy()
        color = np.array([0,0,0,0], dtype=np.uint8) if eraser else self.draw_color

        if np.array_equal(before, color):
            return

        layer_img[ly, lx] = color
        # Undo用データ（座標はキャンバス基準で保存しておくと戻しやすい）
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
    def copy_selection(self):
        """選択範囲をOSのクリップボードに画像としてコピー"""
        from PIL import Image
        import io
        try:
            import win32clipboard
            import win32con
        except ImportError:
            win32clipboard = None
        except ImportError:
            win32clipboard = None

        if not self.selection_rect or not self.layers:
            return

        x1, y1, x2, y2 = self.selection_rect
        sx, ex = sorted([x1, x2])
        sy, ey = sorted([y1, y2])

        layer_dict = self.layers[self.active_layer]
        img = layer_dict["img"]
        ox, oy = layer_dict.get("off_x", 0), layer_dict.get("off_y", 0)

        # レイヤー相対座標
        lx1, ly1 = max(0, sx - ox), max(0, sy - oy)
        lx2, ly2 = min(img.shape[1], ex - ox), min(img.shape[0], ey - oy)

        if lx2 > lx1 and ly2 > ly1:
            clip_np = img[ly1:ly2, lx1:lx2].copy()
            self.clipboard = clip_np  # 内部バッファに保持
            
            # OSクリップボード (Windows) への書き出し
            if win32clipboard:
                clip_img = Image.fromarray(clip_np, "RGBA")
                
                # 1. PNG形式のバイナリを作成（透過保持用）
                png_output = io.BytesIO()
                clip_img.save(png_output, format="PNG")
                png_data = png_output.getvalue()
                png_output.close()

                # 2. DIB形式（透過なし互換用）
                dib_output = io.BytesIO()
                clip_img.convert("RGB").save(dib_output, "BMP")
                dib_data = dib_output.getvalue()[14:]
                dib_output.close()

                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    
                    # PNG形式を登録してセット（最近のアプリ用）
                    fmt_png = win32clipboard.RegisterClipboardFormat("PNG")
                    win32clipboard.SetClipboardData(fmt_png, png_data)
                    
                    # 標準的なDIBもセット（古いアプリ用）
                    win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
                    
                    win32clipboard.CloseClipboard()
                    print("Copied to system clipboard (with alpha).")
                except Exception as e:
                    print(f"Clipboard error: {e}")

    def paste_image(self):
        """OSクリップボード等から画像を取得し、フローティング状態で開始"""
        from PIL import Image, ImageGrab
        
        try:
            pasted_img = ImageGrab.grabclipboard()
        except:
            pasted_img = None

        if isinstance(pasted_img, Image.Image):
            clip_np = np.array(pasted_img.convert("RGBA"), dtype=np.uint8)
        elif self.clipboard is not None:
            clip_np = self.clipboard.copy()
        else:
            return

        self.floating_image = clip_np
        
        # 貼り付け初期位置（選択範囲があればそこ、なければ左上）
        if self.selection_rect:
            self.floating_x = min(self.selection_rect[0], self.selection_rect[2])
            self.floating_y = min(self.selection_rect[1], self.selection_rect[3])
        else:
            self.floating_x, self.floating_y = 0, 0
        
        self.set_tool("move_paste") # 専用ツールに切り替え
        self.redraw()
    def finalize_paste(self):
        """フローティング画像を現在のアクティブレイヤーに書き込む"""
        if self.floating_image is None:
            return

        layer_dict = self.layers[self.active_layer]
        target_img = layer_dict["img"]
        th, tw = target_img.shape[:2]
        ch, cw = self.floating_image.shape[:2]
        
        # レイヤーのオフセットを考慮した貼り付け相対位置
        ox, oy = layer_dict.get("off_x", 0), layer_dict.get("off_y", 0)
        lx, ly = self.floating_x - ox, self.floating_y - oy

        # 書き込み範囲計算
        x1, y1 = max(0, lx), max(0, ly)
        x2, y2 = min(tw, lx + cw), min(th, ly + ch)

        if x2 > x1 and y2 > y1:
            # Undo用に変更範囲を保存 (既存のピクセル単位形式に合わせる)
            patch_undo = []
            sx1, sy1 = x1 - lx, y1 - ly
            for dy in range(y2 - y1):
                for dx in range(x2 - x1):
                    patch_undo.append((self.active_layer, x1 + dx + ox, y1 + dy + oy, 
                                       target_img[y1 + dy, x1 + dx].copy()))
            self.undo_stack.append(patch_undo)
            
            # 書き込み (アルファブレンドする場合はここで計算)
            sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)
            target_img[y1:y2, x1:x2] = self.floating_image[sy1:sy2, sx1:sx2]

        self.floating_image = None # フローティング解除
        self.set_tool("pen")       # ペンに戻す
        self.redraw()

    # ================= Undo / Redo =================
    def undo(self):
        if not self.undo_stack: return
        stroke = self.undo_stack.pop()

        # もし stroke が辞書形式（レイヤー全体のバックアップ）なら
        if isinstance(stroke, dict) and "full_img" in stroke:
            l_idx = stroke["layer_idx"]
            current_back = self.layers[l_idx]["img"].copy()
            self.layers[l_idx]["img"] = stroke["full_img"]
            self.redo_stack.append({"layer_idx": l_idx, "full_img": current_back})
            return

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
    def start_offset_loop(self, dx, dy):
        """長押しの開始"""
        self.offset_layer(dx, dy)
        # 100ミリ秒（0.1秒）ごとに実行。最初の反応を少し遅らせる場合は調整
        self.after_id = self.root.after(100, lambda: self.start_offset_loop(dx, dy))

    def stop_offset_loop(self, _=None):
        """長押しの停止"""
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
    def apply_offset_entry(self):
        """入力ボックスの数値をレイヤーのオフセットに反映する"""
        if not self.layers:
            return
        try:
            new_x = int(self.off_x_entry.get())
            new_y = int(self.off_y_entry.get())
            
            layer = self.layers[self.active_layer]
            layer["off_x"] = new_x
            layer["off_y"] = new_y
            self.redraw()
        except ValueError:
            # 数字以外が入った場合は無視、または警告
            pass

    def update_offset_ui(self):
        """現在のレイヤーのオフセット値を入力ボックスに表示する"""
        if not self.layers:
            return
        layer = self.layers[self.active_layer]
        ox = layer.get("off_x", 0)
        oy = layer.get("off_y", 0)

        # 一旦全削除してから挿入
        self.off_x_entry.delete(0, tk.END)
        self.off_x_entry.insert(0, str(ox))
        self.off_y_entry.delete(0, tk.END)
        self.off_y_entry.insert(0, str(oy))

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
        self.redraw()
    def start_pan(self, e):
        self.canvas.scan_mark(e.x, e.y)

    def pan(self, e):
        self.canvas.scan_dragto(e.x, e.y, gain=1)
        self.redraw()
    def draw_simutrans_guides(self):
        # ズームに応じたサイズ
        b_size = self.build_paksize * self.zoom
        p_size = self.play_paksize * self.zoom
        
        zw, zh = int(self.width * self.zoom), int(self.height * self.zoom)

        # 1. build_paksize ごとの区切り線
        for x in range(0, zw + 1, int(b_size)):
            self.canvas.create_line(x, 0, x, zh, fill="cyan", dash=(4, 4), tags="guide")
        for y in range(0, zh + 1, int(b_size)):
            self.canvas.create_line(0, y, zw, y, fill="cyan", dash=(4, 4), tags="guide")

        # 2. play_paksize に準拠したベースタイル（菱形）の描画
        # 各ビルド用正方形の中心から下側に配置
        if self.show_base_tile:
            for bx in range(0, int(self.width / self.build_paksize)):
                for by in range(0, int(self.height / self.build_paksize)):
                    # ビルド用正方形の中心（画像座標）
                    cx = (bx * self.build_paksize + self.build_paksize / 2) * self.zoom
                    # 中心点から下側にplay_paksize分確保するための基準点
                    cy = (by * self.build_paksize + self.build_paksize / 2) * self.zoom + self.base_offset_y * self.zoom
                    
                    # 菱形の頂点計算 (play_paksizeの半分を半径とする)
                    r_w = p_size / 2 
                    r_h = p_size / 4
                    
                    # 下側に基準を置くため、中心(cx, cy)から菱形を描画
                    # Simutransのタイル接地形状（菱形）
                    points = [
                        cx, cy,       # 上
                        cx + r_w, cy + r_h,       # 右
                        cx, cy + 2*r_h,       # 下
                        cx - r_w, cy + r_h       # 左
                    ]
                    self.canvas.create_polygon(points, fill="", outline="yellow", width=1, tags="guide")

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
        
        self.canvas.delete("selection_ui")
        if self.tool == "select" and self.selection_rect:
            x1, y1, x2, y2 = self.selection_rect
            # ズームを考慮した座標
            zx1, zy1 = x1 * self.zoom, y1 * self.zoom
            zx2, zy2 = x2 * self.zoom, y2 * self.zoom
            
            # 白黒の点線にすることで、どんな背景でも見やすくする
            self.canvas.create_rectangle(zx1, zy1, zx2, zy2, 
                                         outline="white", dash=(4, 4), tags="selection_ui")
            self.canvas.create_rectangle(zx1, zy1, zx2, zy2, 
                                         outline="black", dash=(4, 4), dashoffset=4, tags="selection_ui")

        # ---- Simutrans 補助線の描画 ----
        self.canvas.delete("fixed_guide") # 古いガイドだけを消去
        if self.show_grid:
            self.draw_simutrans_guides()

        if self.floating_image is not None:
            f_img = Image.fromarray(self.floating_image, "RGBA")
            # ズーム倍率に合わせてリサイズ
            zw, zh = int(f_img.width * self.zoom), int(f_img.height * self.zoom)
            if zw > 0 and zh > 0:
                f_img = f_img.resize((zw, zh), Image.NEAREST)
                self.floating_tk = ImageTk.PhotoImage(f_img)
                self.canvas.create_image(self.floating_x * self.zoom, 
                                         self.floating_y * self.zoom, 
                                         anchor="nw", image=self.floating_tk, tags="floating")

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
        ox, oy = 0, 0
        if self.layers:
            layer = self.layers[self.active_layer]
            ox, oy = layer.get("off_x", 0), layer.get("off_y", 0)

        self.info.config(
            text=f"Tool:{self.tool}  Layer:{self.active_layer+1}/{len(self.layers)}  "
                 f"RGBA({r},{g},{b},{a})  Zoom:{int(self.zoom*100)}%  "
                 f"Offset:({ox},{oy}){pos}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    ImageEditor(root)
    root.mainloop()
