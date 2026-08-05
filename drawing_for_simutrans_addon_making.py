import sys
import ctypes
import tkinter as tk
from tkinter import filedialog, colorchooser
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import change_image_paksize
import png_merge_for_simutrans


class _DirtyTrackingList(list):
    """A list that flags its owner as having unsaved changes whenever a new
    undo record is pushed. Every mutating tool (paint, rect, fill, layer
    add/move, paste, resize, ...) already pushes exactly one undo record per
    action, so hooking append() here is a single, reliable place to detect
    "the document changed" without threading a dirty flag through every
    mutation site individually."""
    def __init__(self, owner):
        super().__init__()
        self._owner = owner

    def append(self, item):
        self._owner.dirty = True
        super().append(item)


class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("drawing for simutrans addon making")

        # ---- image / layer ----
        self.layers = []   # [{img: ndarray, visible: bool}]
        self.active_layer = 0
        self.width = 0
        self.height = 0
        self.bg_pattern = self.create_base_tile()
        self.canvas_bg_ids = []

        # ---- save state ----
        self.file_path = None
        self.dirty = False

        # ---- undo / redo ----
        self.undo_stack = _DirtyTrackingList(self)
        self.redo_stack = []
        self.current_stroke = []
        self.after_id = None

        # ---- view ----
        self.zoom_levels = [25, 50, 100, 200, 400, 600, 800, 1000]
        self.zoom = 1.0
        self.cursor_x = None
        self.cursor_y = None
        self.view_x = 0
        self.view_y = 0
        self.pan_start = None
        self.inactive_dim_factor = 0.4
        self.line_start = None

        # ---- tool ----
        self.tool = "pen"
        self.floating_image = None
        self.floating_x = 0
        self.floating_y = 0
        self.is_dragging_floating = False
        self.draw_color = np.array([0, 0, 0, 255], dtype=np.uint8)

        self.layer_panels = []
        # ---- selection ----
        self.selection_rect = None       # [x1, y1, x2, y2]
        self.selection_para_pts = None   # [(x,y)x4] parallelogram selection
        self.clipboard = None            # copied data
        self.selection_id = None         #
        
        # ---- Simutrans Settings ----
        self.build_paksize = 128
        self.play_paksize = 128
        self.show_grid = True
        self.base_offset_y = 0  # offset of the basement tile
        self.show_base_tile = True
        self.ALLOWED_SLOPES = [0, 3/8, 1/2, 5/8, 1, 3/2, float('inf')] # slope angle
        self.special_color_list = [
            [107,107,107],[155,155,155],[179,179,179],[201,201,201],[223,223,223],
            [127,155,241],[255,255,83],[255,33,29],[1,221,1],[227,227,255],
            [193,177,209],[77,77,77],[255,1,127],[1,1,255],[36,75,103],
            [57,94,124],[76,113,145],[96,132,167],[116,151,189],[136,171,211],
            [156,190,233],[176,210,255],[123,88,3],[142,111,4],[161,134,5],
            [180,157,7],[198,180,8],[217,203,10],[236,226,11],[255,249,13]
        ]
        self.special_color_mode = False

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
        tab_color = tk.Frame(notebook)
        tab_layer = tk.Frame(notebook)
        tab_process = tk.Frame(notebook)

        notebook.add(tab_file, text="File")
        notebook.add(tab_edit, text="Edit")
        notebook.add(tab_color, text="Special Colors")
        # notebook.add(tab_draw, text="Draw")
        notebook.add(tab_layer, text="Layer")
        notebook.add(tab_process, text="Process")

        tk.Button(tab_file, text="New", command=self.new_canvas).pack(side=tk.LEFT)
        tk.Button(tab_file, text="Open", command=self.open_image).pack(side=tk.LEFT)
        tk.Button(tab_file, text="Save", command=self.save_image).pack(side=tk.LEFT)
        tk.Button(tab_file, text="Save As...", command=self.save_image_as).pack(side=tk.LEFT)
        tk.Button(tab_edit, text="Undo", command=self.undo).pack(side=tk.LEFT)
        tk.Button(tab_edit, text="Redo", command=self.redo).pack(side=tk.LEFT)

        # special colors
        self.create_palette_ui(tab_color)
        self.view_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tab_color, text="Highlight Special Colors", variable=self.special_color_mode, 
                       command=self.toggle_special_color_mode).pack(side=tk.LEFT)
        # create_ui
        self.tool_btns = {}

        btn_pen = tk.Button(bar, text="Pen", command=lambda: self.set_tool("pen"))
        btn_pen.pack(side=tk.LEFT)
        self.tool_btns["pen"] = btn_pen

        btn_fill = tk.Button(bar, text="Fill", command=lambda: self.set_tool("fill"))
        btn_fill.pack(side=tk.LEFT)
        self.tool_btns["fill"] = btn_fill
        btn_line = tk.Button(bar, text="Line", command=lambda: self.set_tool("line"))
        btn_line.pack(side=tk.LEFT)
        self.tool_btns["line"] = btn_line

        btn_eraser = tk.Button(bar, text="Eraser", command=lambda: self.set_tool("eraser"))
        btn_eraser.pack(side=tk.LEFT)
        self.tool_btns["eraser"] = btn_eraser

        btn_pipette = tk.Button(bar, text="Pipette", command=lambda: self.set_tool("pipette"))
        btn_pipette.pack(side=tk.LEFT)
        self.tool_btns["pipette"] = btn_pipette

        btn_move = tk.Button(bar, text="Move", command=lambda: self.set_tool("move"))
        btn_move.pack(side=tk.LEFT)
        self.tool_btns["move"] = btn_move

        # toolbar
        btn_select = tk.Button(bar, text="Select", command=lambda: self.set_tool("select"))
        btn_select.pack(side=tk.LEFT)
        self.tool_btns["select"] = btn_select

        btn_para_select = tk.Button(bar, text="ParaSelect", command=lambda: self.set_tool("para_select"))
        btn_para_select.pack(side=tk.LEFT)
        self.tool_btns["para_select"] = btn_para_select

        # rectangle
        btn_rect = tk.Button(bar, text="Rect", command=lambda: self.set_tool("rect"))
        btn_rect.pack(side=tk.LEFT)
        self.tool_btns["rect"] = btn_rect

        btn_fill_rect = tk.Button(bar, text="FillRect", command=lambda: self.set_tool("fill_rect"))
        btn_fill_rect.pack(side=tk.LEFT)
        self.tool_btns["fill_rect"] = btn_fill_rect

        self.rect_mode = tk.StringVar(value="box") # box, h_para, d_para
        rect_options = [("Box", "box"), ("H-Para", "h_para"), ("D-Para", "d_para")]
        self.create_rect_icons()
        self.rect_option_frame = tk.Frame(bar)
        for text, mode in rect_options:
            rb = tk.Radiobutton(
                self.rect_option_frame, 
                image=self.rect_icons[mode],
                text=text,
                compound=tk.LEFT,
                variable=self.rect_mode, 
                value=mode,
                indicatoron=0,
                padx=5, pady=2
            )
            rb.pack(side=tk.LEFT, padx=2)

        # Edit
        tk.Button(tab_edit, text="Copy", command=self.copy_selection).pack(side=tk.LEFT)
        tk.Button(tab_edit, text="Cut", command=self.cut_selection).pack(side=tk.LEFT)
        tk.Button(tab_edit, text="Paste", command=self.paste_image).pack(side=tk.LEFT)
        tk.Button(tab_edit, text="Clear Outside", command=self.clear_outside_selection).pack(side=tk.LEFT)
        self.btn_confirm = tk.Button(tab_edit, text="Confirm Paste", bg="#ffcc00", 
                                     command=self.finalize_paste)
        self.btn_confirm.pack(side=tk.LEFT, padx=5)
        #layer
        tk.Button(tab_layer, text="New Layer", command=self.add_layer).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Duplicate Layer", command=self.duplicate_layer).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Delete Layer", command=self.delete_layer).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="▲ Up", command=self.move_layer_up).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="▼ Down", command=self.move_layer_down).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Export Layer", command=lambda:self.save_layer(-1)).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Export All Layer", command=self.save_all_layers).pack(side=tk.LEFT)
        tk.Button(tab_layer, text="Import to Layer", command=self.import_to_layer).pack(side=tk.LEFT)
        merge_frame = tk.LabelFrame(tab_layer, text="Merge Layer Down")
        merge_frame.pack(side=tk.LEFT, padx=5)

        modes = [("Add", "add"), ("Mult", "multiply"), ("Replace", "replace"), ("Bright", "brightness"), ("Lightmap", "lightmap")]
        for text, m in modes:
            tk.Button(merge_frame, text=text, command=lambda mode=m: self.merge_layer(mode)).pack(side=tk.LEFT, padx=2)
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
        
        # offset for layer

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
            btn.bind("<ButtonPress-1>", lambda e, x=dx, y=dy: self.start_offset_loop(x, y))
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
        self.hbar = tk.Scrollbar(body, orient=tk.HORIZONTAL,command=self.on_scrollbar_x)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar = tk.Scrollbar(body, orient=tk.VERTICAL,command=self.on_scrollbar_y)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ---- layer panel ----
        self.layer_frame = tk.Frame(body, width=120, relief="sunken", bd=1)
        self.layer_frame.pack(side=tk.LEFT, fill=tk.Y)

        # ---- canvas ----
        self.canvas = tk.Canvas(body, bd=0, highlightthickness=0,
                                xscrollcommand=self.hbar.set,
                                yscrollcommand=self.vbar.set)
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

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
        self.root.bind("<Control-x>", lambda e: self.cut_selection())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<Escape>", self.clear_selection)
        self.root.bind("<Return>", lambda e: self.finalize_paste())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # self.canvas.bind("<Button-4>", self.on_linux_scroll_up)
        # self.canvas.bind("<Button-5>", self.on_linux_scroll_down)

    def clear_selection(self, event=None):
        self.selection_rect = None
        self.selection_para_pts = None
        self.redraw()
    def create_base_tile(self):
        size = 8
        c1, c2 = (220, 220, 220, 255), (190, 190, 190, 255)
        data = np.zeros((size * 2, size * 2, 4), dtype=np.uint8)
        data[:size, :size] = c1
        data[size:, size:] = c1
        data[:size, size:] = c2
        data[size:, :size] = c2
        return ImageTk.PhotoImage(Image.fromarray(data, "RGBA"))
    def on_scrollbar_x(self, *args):
        self.canvas.xview(*args)
        self.redraw()

    def on_scrollbar_y(self, *args):
        self.canvas.yview(*args)
        self.redraw()
    
    def check_simutrans_special_colors(self, rgb_array):
        mask = np.zeros(rgb_array.shape[:2], dtype=bool)
        
        for color in self.special_color_list:
            match = np.all(rgb_array == color, axis=-1)
            mask |= match
        return mask
    def create_rect_icons(self):
        self.rect_icons = {}
        modes = ["box", "h_para", "d_para"]
        
        for m in modes:
            img = Image.new("RGBA", (24, 24), (0,0,0,0))
            draw = Image.new("RGBA", (24, 24), (0,0,0,0))
            if m == "box":
                points = [(4,4), (19,4), (19,19), (4,19)]
            elif m == "h_para":
                points = [(4,8), (19,4), (19,15), (4,19)]
            elif m == "d_para":
                points = [(11,4), (20,11), (11,18), (2,11)]
            
            from PIL import ImageDraw
            d = ImageDraw.Draw(img)
            d.polygon(points, outline="black", fill="#ddd")
            self.rect_icons[m] = ImageTk.PhotoImage(img)
    # ================= Image I/O =================
    def open_image(self):
        if not self.confirm_unsaved_changes():
            return

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

        self.file_path = path
        self.dirty = False

        self.refresh_layer_panel()
        self.redraw()

    def new_canvas(self):
        if not self.confirm_unsaved_changes():
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("New Canvas")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text="Width:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        w_entry = tk.Entry(dialog, width=8)
        w_entry.insert(0, str(self.build_paksize))
        w_entry.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(dialog, text="Height:").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        h_entry = tk.Entry(dialog, width=8)
        h_entry.insert(0, str(self.build_paksize))
        h_entry.grid(row=1, column=1, padx=6, pady=6)

        error_label = tk.Label(dialog, text="", fg="red")
        error_label.grid(row=2, column=0, columnspan=2)

        def create():
            from tkinter import messagebox
            try:
                w = int(w_entry.get())
                h = int(h_entry.get())
            except ValueError:
                error_label.config(text="Width/Height must be integers")
                return
            if w <= 0 or h <= 0:
                error_label.config(text="Width/Height must be positive")
                return

            self.width, self.height = w, h
            self.layers = [{
                "img": np.zeros((h, w, 4), dtype=np.uint8),
                "visible": True
            }]
            self.active_layer = 0

            self.undo_stack.clear()
            self.redo_stack.clear()

            self.view_x = self.view_y = 0
            self.zoom = 1.0
            self.zoom_scale.set(2)

            self.file_path = None
            self.dirty = False

            self.refresh_layer_panel()
            self.redraw()
            dialog.destroy()

        tk.Button(dialog, text="Create", command=create, bg="#d0ffd0").grid(
            row=3, column=0, columnspan=2, pady=8)
        w_entry.focus_set()

    def save_image(self):
        if not self.layers:
            return False
        if not self.file_path:
            return self.save_image_as()

        out = self.compose_layers(for_display=False)
        Image.fromarray(out, "RGBA").save(self.file_path)
        self.dirty = False
        return True

    def save_image_as(self):
        if not self.layers:
            return False

        out = self.compose_layers(for_display=False)
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if not path:
            return False

        Image.fromarray(out, "RGBA").save(path)
        self.file_path = path
        self.dirty = False
        return True

    def confirm_unsaved_changes(self):
        """If there are unsaved changes, ask the user whether to save,
        save as, or discard them. Returns True if it's OK to proceed
        (changes were saved or the user chose to discard them), False if
        the user cancelled (the caller should abort whatever it was about
        to do: opening another file, starting a new canvas, or closing)."""
        if not self.dirty:
            return True

        result = {"choice": "cancel"}
        dialog = tk.Toplevel(self.root)
        dialog.title("Unsaved Changes")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text="You have unsaved changes.\nWhat would you like to do?",
                 justify="left", padx=16, pady=12).pack()
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=(0, 12), padx=12)

        def choose(c):
            result["choice"] = c
            dialog.destroy()

        tk.Button(btn_frame, text="Save", width=10,
                  command=lambda: choose("save")).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Save As...", width=10,
                  command=lambda: choose("save_as")).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Don't Save", width=10,
                  command=lambda: choose("discard")).pack(side=tk.LEFT, padx=4)

        dialog.protocol("WM_DELETE_WINDOW", lambda: choose("cancel"))
        dialog.wait_window()

        if result["choice"] == "save":
            return self.save_image()
        if result["choice"] == "save_as":
            return self.save_image_as()
        if result["choice"] == "discard":
            return True
        return False

    def on_close(self):
        if self.confirm_unsaved_changes():
            self.root.destroy()

    # ================= Layers =================
    def merge_layer(self, mode="add"):
        if self.active_layer <= 0:
            return
        import copy
        self.undo_stack.append(("whole_layers", copy.deepcopy(self.layers), self.active_layer))
        self.redo_stack.clear()

        upper_idx = self.active_layer
        lower_idx = self.active_layer - 1

        upper = self.layers[upper_idx]
        lower = self.layers[lower_idx]

        ux, uy = upper.get("off_x", 0), upper.get("off_y", 0)
        lx, ly = lower.get("off_x", 0), lower.get("off_y", 0)
        u_img = upper["img"].astype(np.float32)
        l_img = lower["img"].astype(np.float32)
        uh, uw = u_img.shape[:2]
        lh, lw = l_img.shape[:2]

        # reset canvas pos
        new_x = min(ux, lx)
        new_y = min(uy, ly)
        new_w = max(ux + uw, lx + lw) - new_x
        new_h = max(uy + uh, ly + lh) - new_y

        merged_img = np.zeros((new_h, new_w, 4), dtype=np.float32)

        merged_img[ly-new_y : ly-new_y+lh, lx-new_x : lx-new_x+lw] = l_img

        # calc merging pos
        tx1, ty1 = ux - new_x, uy - new_y
        tx2, ty2 = tx1 + uw, ty1 + uh

        # special color?
        upper_special = self.check_simutrans_special_colors(u_img[..., :3])

        target_area = merged_img[ty1:ty2, tx1:tx2]
        lower_special = self.check_simutrans_special_colors(target_area[..., :3])
        is_not_transparent = u_img[..., 3] > 0
        is_not_sim_bg = ~(np.all(u_img[..., :3] == [231, 255, 255], axis=-1))
        if(  mode=="lightmap"  ):
            calc_mask = (~upper_special) & is_not_sim_bg
        else:
            calc_mask = is_not_transparent & is_not_sim_bg & (~upper_special) & (~lower_special)

        if mode == "add":
            target_area[calc_mask, :3] += u_img[calc_mask, :3]
            target_area[calc_mask, 3] = np.minimum(target_area[calc_mask, 3] + u_img[calc_mask, 3], 255.0)
        elif mode == "multiply":
            target_area[calc_mask, :3] = (target_area[calc_mask, :3] / 255.0 * u_img[calc_mask, :3] / 255.0) * 255.0
            target_area[calc_mask, 3] = np.minimum(target_area[calc_mask, 3] * u_img[calc_mask, 3] / 255.0, 255.0)
            
        elif mode == "replace":
            target_area[calc_mask] = u_img[calc_mask]
        
        elif mode == "lightmap":
            target_area[calc_mask, :3] = (target_area[calc_mask, :3] * u_img[calc_mask, :3] /128.0 )
            target_area[calc_mask, 3] = np.minimum(target_area[calc_mask, 3] * u_img[calc_mask, 3] / 255.0, 255.0)
            
        elif mode == "brightness":
            target_area[calc_mask, :3] = np.maximum(target_area[calc_mask, :3], 
                                                    u_img[calc_mask, :3])
            target_area[calc_mask, 3] = np.maximum(target_area[calc_mask, 3], u_img[calc_mask, 3])
        if mode != "replace":
            special_overwrite = is_not_transparent & is_not_sim_bg & (upper_special | lower_special)
            target_area[special_overwrite] = u_img[special_overwrite]


        final_img = np.clip(merged_img, 0, 255).astype(np.uint8)

        self.save_full_undo(lower_idx)
        self.layers[lower_idx] = {
            "img": final_img,
            "visible": True,
            "off_x": new_x,
            "off_y": new_y
        }
        self.layers.pop(upper_idx)
        self.active_layer = lower_idx
        
        self.refresh_layer_panel()
        self.redraw()
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
            # only 1 layer, not delete it
            return
        
        self.layers.pop(self.active_layer)
        self.active_layer = max(0, self.active_layer - 1)
        self.refresh_layer_panel()
        self.redraw()

    def compose_layers(self, for_display=True):
        if not self.layers:
            return np.zeros((self.height, self.width, 4), dtype=np.uint8)

        out = np.zeros((self.height, self.width, 4), dtype=np.float32)

        for i, layer in enumerate(self.layers):
            if not layer["visible"]: continue
            
            src = layer["img"].astype(np.float32)
            lh, lw = src.shape[:2]
            ox, oy = layer.get("off_x", 0), layer.get("off_y", 0)

            x1, y1 = max(0, ox), max(0, oy)
            x2, y2 = min(self.width, ox + lw), min(self.height, oy + lh)

            if x2 > x1 and y2 > y1:
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

        import_img = Image.open(path).convert("RGBA")
        import_np = np.array(import_img, dtype=np.uint8)

        self.layers.append({
            "img": import_np,
            "visible": True,
            "off_x": 0,
            "off_y": 0
        })
        
        self.active_layer = len(self.layers) - 1
        self.refresh_layer_panel()
        self.redraw()
    def offset_layer(self, dx, dy):
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
            title="save No.{which} layer",
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
    def get_emphasized_image(self, img_array):
        temp_img = img_array.astype(np.float32)
        
        special_mask = self.check_simutrans_special_colors(temp_img[..., :3])
        
        is_bg = np.all(temp_img[..., :3] == [231, 255, 255], axis=-1)
        target_mask = (~special_mask) & (~is_bg) & (temp_img[..., 3] > 0)
        
        gray = temp_img[target_mask, 0] * 0.299 + \
               temp_img[target_mask, 1] * 0.587 + \
               temp_img[target_mask, 2] * 0.114
        
        temp_img[target_mask, 0] = gray * 0.3
        temp_img[target_mask, 1] = gray * 0.3
        temp_img[target_mask, 2] = gray * 0.3
        
        return np.clip(temp_img, 0, 255).astype(np.uint8)
    # ================= Tools =================
    def set_tool(self, tool_name):
        if self.tool == "move_paste" and tool_name != "move_paste":
            self.finalize_paste()
        if tool_name in ("rect", "fill_rect", "para_select"):
            self.rect_option_frame.pack(side=tk.LEFT, padx=10)
        else:
            self.rect_option_frame.pack_forget()

        self.tool = tool_name

        for name, btn in self.tool_btns.items():
            btn.config(relief=tk.RAISED, bg="SystemButtonFace")
        if tool_name in self.tool_btns:
            self.tool_btns[tool_name].config(relief=tk.SUNKEN, bg="#ADD8E6")

        if self.tool == "move_paste":
            self.btn_confirm.pack(side=tk.LEFT, padx=5)
        else:
            self.btn_confirm.pack_forget()

        if tool_name not in ("select", "para_select"):
            self.clear_selection()
        elif tool_name == "select":
            self.selection_para_pts = None
            self.redraw()
        elif tool_name == "para_select":
            self.selection_rect = None
            self.redraw()

        self.redraw()

    def choose_color(self):
        c = colorchooser.askcolor()
        if c[0]:
            self.draw_color[:3] = np.array(c[0], dtype=np.uint8)
            self.update_color_preview()
    def create_palette_ui(self, parent_frame):
        palette_frame = tk.LabelFrame(parent_frame, text="Simutrans Special Colors")
        palette_frame.pack(fill=tk.X, padx=5, pady=5)

        for i, rgb in enumerate(self.special_color_list):
            hex_color = "#{:02x}{:02x}{:02x}".format(*rgb)
            
            btn = tk.Button(
                palette_frame, 
                bg=hex_color, 
                width=2, 
                height=1,
                command=lambda c=rgb: self.set_brush_color(c)
            )
            btn.grid(row=i // 16, column=i % 16, padx=1, pady=1)

    def set_brush_color(self, rgb):
        self.draw_color[:3]=rgb
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

            for layer in self.layers:
                layer["img"] = change_image_paksize.change_paksize_program(layer["img"], old_pak, new_pak, 3)
            
            self.width = int(self.width*new_pak/old_pak)
            self.height = int(self.width*new_pak/old_pak)
            self.build_paksize = new_pak
            self.build_entry.delete(0, tk.END)
            self.build_entry.insert(0, str(new_pak))
            
            self.update_sim_settings()
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

            for layer in self.layers:
                layer["img"] = png_merge_for_simutrans.resize_program(layer["img"], old_pak, new_pak, 0,2)
            
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
            
            self.update_sim_settings()
            self.refresh_layer_panel()
            self.redraw()
            
            print(f"Canvas resized to pak{new_pak}")
            
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Error", "Valid paksize required")
    def get_rect_points(self, x1, y1, x2, y2, mode):
        if mode == "box":
            return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        
        elif mode == "h_para":
            dx = x2 - x1
            dy = y2 - y1
            dy_slope = abs(dx) // 2
            if dx*dy>0:
                x_min = min(x1,x2)
                x_max = max(x1,x2)
                y_min = min(y1,y2)
                y_max = max(y1,y2)
                if abs(dy_slope) < abs(dy):
                    return[(x_min,y_min), (x_max, y_min + dy_slope), (x_max, y_max), (x_min, y_max - dy_slope)]
                return[(x_min, y_min), (x_min + abs(dy)*2, y_max), (x_max, y_max), (x_max - abs(dy)*2, y_min)]
            else:
                x_min = max(x1,x2)
                x_max = min(x1,x2)
                y_min = min(y1,y2)
                y_max = max(y1,y2)
                if abs(dy_slope) < abs(dy):
                    return[(x_min,y_min), (x_max, y_min + dy_slope), (x_max, y_max), (x_min, y_max - dy_slope)]
                return[(x_min, y_min), (x_min - abs(dy)*2, y_max), (x_max, y_max), (x_max + abs(dy)*2, y_min)]

        elif mode == "d_para":
            if abs(y2-y1)*2>=abs(x2-x1):
                y_min = min(y1,y2)
                y_max = max(y1,y2)
                x_min = x1 if y_min==y1 else x2
                x_max = x1 if y_max==y1 else x2
                dy = y_max-y_min
                dy_slope = int(np.sign(x_max-x_min) * abs(x_max-x_min)//2)
                p_a = (x_min, y_min)
                p_b = (x_max, y_max)
                # first offset corner: single clean division, exact 2:1 edge
                p_c1 = (x_min+abs(dy)+dy_slope, y_min + (abs(dy)+dy_slope)//2)
                # opposite corner: derived from the parallelogram identity
                # (diagonals bisect each other) instead of its own separately
                # rounded formula, so this edge is exactly parallel to p_a-p_c1
                # rather than off by a pixel when (abs(dy)+dy_slope) and
                # (abs(dy)-dy_slope) have different parity.
                p_c2 = (p_a[0]+p_b[0]-p_c1[0], p_a[1]+p_b[1]-p_c1[1])
                return[p_a, p_c1, p_b, p_c2]
            else:
                x_min = min(x1,x2)
                x_max = max(x1,x2)
                y_min = y1 if x_min==x1 else y2
                y_max = y1 if x_max==x1 else y2
                dy = y_max-y_min
                dy_slope = int(np.sign(x_max-x_min) * abs(x_max-x_min)//2)
                p_a = (x_min, y_min)
                p_b = (x_max, y_max)
                p_c0 = (x_min-(dy)+abs(dy_slope), y_min+((dy)-abs(dy_slope))//2)
                p_c2 = (p_a[0]+p_b[0]-p_c0[0], p_a[1]+p_b[1]-p_c0[1])
                return[p_c0, p_b, p_c2, p_a]
        
        return []

    def get_fill_rect_edges(self, x1s, y1s, x2s, y2s, mode):
        """Return the 4 border segments [(x1,y1,x2,y2), ...] that the "rect"
        outline tool actually draws (via finalize_line) for this drag/mode.
        Shared by the outline tool and the fill tool so a filled shape's
        border always matches the unfilled outline pixel-for-pixel."""
        pts = self.get_rect_points(x1s, y1s, x2s, y2s, mode)
        edges = []
        for i in range(len(pts)):
            x1, y1 = pts[i][0], pts[i][1]
            x2, y2 = pts[(i + 1) % 4][0], pts[(i + 1) % 4][1]
            x_ref3 = pts[(i + 2) % 4][0]
            x_ref4 = pts[(i + 3) % 4][0]
            if y1 == y2:
                x1, x2 = min(x1, x2) - 1, max(x1, x2)
            elif x1 == x2:
                y1, y2 = min(y1, y2) - 1, max(y1, y2)
            else:
                if y1 < y2 and x1 < x2:
                    y2 += 1
                    x2 += 1
                elif y1 > y2 and x1 > x2:
                    y1 += 1
                    x1 += 1
                elif y1 < y2 and x1 > x2:
                    y2 += 1
                    x2 -= 1
                elif y1 > y2 and x1 < x2:
                    y1 += 1
                    x1 -= 1
                if mode == "h_para" and i == 2:
                    if max(x1, x2, x_ref3, x_ref4) == x1 and x2 != x_ref3:
                        x1 -= 1
                        x2 -= 1
                    elif x2 != x_ref3:
                        x1 += 1
                        x2 += 1
            if mode == "d_para":
                if i == 1:
                    y2 -= 1
                elif i > 1:
                    x1 -= 1
                    x2 -= 1
                    if i == 2:
                        y1 -= 1
            edges.append((x1, y1, x2, y2))
        return edges
    # ================= Polygon Helpers =================
    def _rasterize_edge_points(self, x1, y1, x2, y2):
        """Return the list of pixel coordinates for the segment (x1,y1)-(x2,y2)
        using the exact same stepping rule as finalize_line, so filled shapes
        share their border with the outline rect/line tools."""
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return [(x1, y1)]

        signx = int(np.sign(dx))
        signy = int(np.sign(dy))
        startx = min(x1, x2)
        starty = min(y1, y2)

        pts = []
        if abs(dx) < abs(dy):
            for i in range(abs(dy)):
                temp_x = startx + (i * abs(dx) // abs(dy))
                temp_y = starty + i if (signx * signy > 0) else max(y1, y2) - i
                pts.append((temp_x, temp_y))
        else:
            for i in range(abs(dx)):
                temp_x = startx + i if (signx * signy > 0) else max(x1, x2) - i
                temp_y = starty + (i * abs(dy) // abs(dx))
                pts.append((temp_x, temp_y))
        return pts

    def _make_polygon_mask(self, pts, shape):
        """Return a boolean numpy mask (h, w) where True = inside polygon.
        pts: list of (x, y) in layer-local coordinates.

        Rasterizes the polygon border with the same per-edge stepping as
        finalize_line, then fills each row between its leftmost and
        rightmost border pixel (scanline fill), so the fill matches the
        border drawn by the rect/line tools exactly."""
        h, w = shape
        mask = np.zeros((h, w), dtype=bool)

        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            for x, y in self._rasterize_edge_points(x1, y1, x2, y2):
                if 0 <= x < w and 0 <= y < h:
                    mask[y, x] = True

        for y in range(h):
            xs = np.nonzero(mask[y])[0]
            if xs.size:
                mask[y, xs.min():xs.max() + 1] = True

        return mask

    def fill_polygon_pixels(self, pts):
        """Fill the interior of a polygon (image coordinates) with draw_color."""
        layer_dict = self.layers[self.active_layer]
        layer_img = layer_dict["img"]
        ox = layer_dict.get("off_x", 0)
        oy = layer_dict.get("off_y", 0)
        adj_pts = [(x - ox, y - oy) for x, y in pts]
        mask = self._make_polygon_mask(adj_pts, layer_img.shape[:2])
        if mask.any():
            layer_img[mask] = self.draw_color

    def fill_rect_edges(self, edges):
        """Fill the area bounded by explicit border segments (image coords),
        e.g. from get_fill_rect_edges, with draw_color. Rasterizes each
        segment with the same rule finalize_line uses, so the filled area's
        border is identical to the unfilled outline's border."""
        layer_dict = self.layers[self.active_layer]
        layer_img = layer_dict["img"]
        ox = layer_dict.get("off_x", 0)
        oy = layer_dict.get("off_y", 0)
        h, w = layer_img.shape[:2]

        mask = np.zeros((h, w), dtype=bool)
        for x1, y1, x2, y2 in edges:
            for x, y in self._rasterize_edge_points(x1 - ox, y1 - oy, x2 - ox, y2 - oy):
                if 0 <= x < w and 0 <= y < h:
                    mask[y, x] = True

        for y in range(h):
            xs = np.nonzero(mask[y])[0]
            if xs.size:
                mask[y, xs.min():xs.max() + 1] = True

        if mask.any():
            layer_img[mask] = self.draw_color

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
            self.drag_start_pos = (ix, iy)
            self.floating_start_pos = (self.floating_x, self.floating_y)
            return
        if self.tool == "select":
            self.selection_rect = [ix, iy, ix, iy]
            return
        if self.tool == "line":
            self.line_start = (ix, iy)
            self.save_full_undo(self.active_layer) # save for undo
            self.drag_start_pos = (ix, iy)
            return
        if self.tool == "rect":
            self.line_start = (ix, iy) # start point
            self.save_full_undo(self.active_layer) # save for undo
            return
        if self.tool == "fill_rect":
            self.line_start = (ix, iy)
            self.save_full_undo(self.active_layer)
            return
        if self.tool == "para_select":
            self.line_start = (ix, iy)
            self.selection_para_pts = None
            return
        if self.tool == "move":
            layer = self.layers[self.active_layer]
            self.drag_start_pos = (ix, iy)
            self.drag_start_offset = (layer.get("off_x", 0), layer.get("off_y", 0))
        elif self.tool == "pipette":
            layers = self.layers[self.active_layer]
            ox, oy = layers.get("off_x", 0), layers.get("off_y", 0)
            layer = layers["img"]
            if 0 <= ix < self.width and 0 <= iy < self.height:
                self.draw_color = layer[iy-oy, ix-ox].copy()
                self.alpha.set(self.draw_color[3])
                self.update_color_preview()
            self.set_tool("pen")
        elif self.tool == "eraser":
            self.paint(ix, iy, True)
        elif self.tool == "fill":
            self.flood_fill(ix, iy)
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
        if self.tool == "line":
            x1, y1 = self.line_start
            if e.state & 0x0001:
                ix, iy = self.snap_coordinate(x1, y1, ix, iy)
            
            self.redraw()
            self.draw_preview_line(ix, iy)
            return
        if self.tool in ("rect", "fill_rect", "para_select"):
            self.redraw()
            if self.line_start:
                self.draw_preview_rect(ix, iy)
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

    def end_stroke(self, e):
        ix, iy = self.canvas_to_image(e.x, e.y)
        
        if self.tool == "line":
            x1, y1 = self.line_start
            if e.state & 0x0001:
                ix, iy = self.snap_coordinate(x1, y1, ix, iy)
            
            self.finalize_line(x1, y1, ix, iy)
            return
        if self.tool == "fill_rect" and self.line_start:
            edges = self.get_fill_rect_edges(self.line_start[0], self.line_start[1], ix, iy, self.rect_mode.get())
            self.fill_rect_edges(edges)
            self.line_start = None
            self.redraw()
            return
        if self.tool == "para_select" and self.line_start:
            pts = self.get_rect_points(self.line_start[0], self.line_start[1], ix, iy, self.rect_mode.get())
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if max(xs) != min(xs) and max(ys) != min(ys):
                self.selection_para_pts = pts
            else:
                self.selection_para_pts = None
            self.line_start = None
            self.redraw()
            return
        if self.tool == "rect" and self.line_start:
            edges = self.get_fill_rect_edges(self.line_start[0], self.line_start[1], ix, iy, self.rect_mode.get())
            for x1, y1, x2, y2 in edges:
                self.finalize_line(x1, y1, x2, y2)
            self.line_start = None
            self.redraw()
            return
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
        
        ox = layer_dict.get("off_x", 0)
        oy = layer_dict.get("off_y", 0)
        lx, ly = x - ox, y - oy

        lh, lw = layer_img.shape[:2]
        if not (0 <= lx < lw and 0 <= ly < lh):
            return

        before = layer_img[ly, lx].copy()
        color = np.array([0,0,0,0], dtype=np.uint8) if eraser else self.draw_color

        if np.array_equal(before, color):
            return

        layer_img[ly, lx] = color
        self.current_stroke.append((self.active_layer, x, y, before))
        self.redraw()
    def flood_fill(self, x, y):
        layer_dict = self.layers[self.active_layer]
        img = layer_dict["img"]
        h, w = img.shape[:2]

        target_color = img[y, x].copy()
        fill_color = np.array(self.draw_color, dtype=np.uint8)

        if np.array_equal(target_color, fill_color):
            return

        stack = [(x, y)]

        undo_data = []

        visited = np.zeros((h, w), dtype=bool)

        while stack:
            cx, cy = stack.pop()

            if not (0 <= cx < w and 0 <= cy < h):
                continue
            if visited[cy, cx]:
                continue
            
            if np.array_equal(img[cy, cx], target_color):
                undo_data.append((self.active_layer, cx, cy, img[cy, cx].copy()))
                
                img[cy, cx] = fill_color
                visited[cy, cx] = True
                
                stack.append((cx + 1, cy))
                stack.append((cx - 1, cy))
                stack.append((cx, cy + 1))
                stack.append((cx, cy - 1))

        if undo_data:
            self.undo_stack.append(undo_data)
            self.redraw()
    def snap_coordinate(self, x1, y1, x2, y2):
        import math
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return x2, y2

        current_angle = math.atan2(abs(dy), abs(dx))
        slopes = [0, 0.375, 0.5, 0.625, 1.0, 1.5, float('inf')]
        target_angles = [math.atan(s) if s != float('inf') else math.pi/2 for s in slopes]
        
        best_angle = min(target_angles, key=lambda a: abs(a - current_angle))
        
        dist = math.sqrt(dx**2 + dy**2)
        sign_x = 1 if dx >= 0 else -1
        sign_y = 1 if dy >= 0 else -1
        
        new_dx = dist * math.cos(best_angle) * sign_x
        new_dy = dist * math.sin(best_angle) * sign_y
        
        return int(round(x1 + new_dx)), int(round(y1 + new_dy))
    def draw_preview_line(self, cur_ix, cur_iy):
        x1 = self.line_start[0] * self.zoom
        y1 = self.line_start[1] * self.zoom
        x2 = cur_ix * self.zoom
        y2 = cur_iy * self.zoom
        r, g, b = self.draw_color[:3]
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        
        self.canvas.create_line(
            x1, y1, x2, y2, 
            fill=hex_color, 
            width=1, 
            dash=(4, 4),
            tags="preview"
        )
        
        info_text = f"({cur_ix-self.line_start[0]}, {cur_iy-self.line_start[1]})"
        self.canvas.create_text(
            x2 + 15, y2 + 15,
            text=info_text,
            fill=hex_color,
            anchor="nw",
            font=("Consolas", 10, "bold"),
            tags="preview"
        )
    def draw_preview_rect(self, ix, iy):
        pts = self.get_rect_points(self.line_start[0], self.line_start[1], ix, iy, self.rect_mode.get())
        edges = self.get_fill_rect_edges(self.line_start[0], self.line_start[1], ix, iy, self.rect_mode.get())
        r, g, b = self.draw_color[:3]
        hex_color = f"#{r:02x}{g:02x}{b:02x}"

        # edges' own (x1,y1)/(x2,y2) include a padding nudge that lets
        # finalize_line's pixel loop reach the true corner, but that nudged
        # coordinate is never itself a drawn pixel. Use the actual first/last
        # rasterized pixel (same rule finalize_line uses) instead.
        endpoints = []
        for x1, y1, x2, y2 in edges:
            raster = self._rasterize_edge_points(x1, y1, x2, y2)
            endpoints.append((raster[0], raster[-1]))

        # A drawn pixel (px,py) visually covers the square [px,px+1)x[py,py+1)
        # on screen. Anchoring every point at its pixel's near (top-left)
        # corner makes the north/west sides line up, but leaves the
        # south/east sides looking a full pixel short of the actually
        # rendered extent. So pixels on the shape's own right/bottom edge
        # need to be anchored at their far corner instead.
        all_pts = [p for pair in endpoints for p in pair]
        x_max = max(p[0] for p in all_pts)
        y_max = max(p[1] for p in all_pts)

        def outer_corner(p):
            px, py = p
            return (px + 1 if px == x_max else px, py + 1 if py == y_max else py)

        for f, l in endpoints:
            fx, fy = outer_corner(f)
            lx, ly = outer_corner(l)
            self.canvas.create_line(fx*self.zoom, fy*self.zoom,
                                    lx*self.zoom, ly*self.zoom, fill=hex_color, dash=(4,4))
        info_text = f"{pts[0]}{pts[1]}{pts[2]}{pts[3]}"
        x2 = ix * self.zoom
        y2 = iy * self.zoom
        self.canvas.create_text(
            x2 + 15, y2 + 15,
            text=info_text,
            fill=hex_color,
            anchor="nw",
            font=("Consolas", 10, "bold"),
            tags="preview"
        )
    def finalize_line(self, x1, y1, x2, y2):
        # please save current state BEFORE call this function!
        layer_dict = self.layers[self.active_layer]
        layer_img = layer_dict["img"]
        ox = layer_dict.get("off_x", 0)
        oy = layer_dict.get("off_y", 0)
        color = self.draw_color

        dx = x2-x1
        dy = y2-y1
        if dx*dx+dy*dy==0:
            # no line
            return
        signx = int(np.sign(dx))
        signy = int(np.sign(dy))
        startx = min(x1,x2)
        starty = min(y1,y2)

        print(f"draw line from {x1},{y1} to {x2},{y2}, ({dx},{dy})")

        lh, lw = layer_img.shape[:2]
        if abs(dx)<abs(dy):
            for i in range(abs(dy)):
                temp_x = startx+((i)*abs(dx)//abs(dy))-ox
                temp_y = (starty + i if (signx*signy>0) else max(y1,y2) - i)-oy
                if 0 <= temp_x < lw and 0 <= temp_y < lh:
                    layer_img[temp_y,temp_x]=color
        else:
            for i in range(abs(dx)):
                temp_x = (startx + i if (signx*signy>0) else max(x1,x2) - i)-ox
                temp_y = starty+((i)*abs(dy)//abs(dx))-oy
                if 0 <= temp_x < lw and 0 <= temp_y < lh:
                    layer_img[temp_y,temp_x]=color

        self.redraw()
    # ================= Using Changing Tools =================
    def select_all(self):
        if not self.layers:
            return
        self.set_tool("select")
        iy=len(self.layers[self.active_layer]["img"])
        ix=len(self.layers[self.active_layer]["img"][0])
        self.selection_rect=[0,0,ix,iy]

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
        from PIL import Image
        import io
        try:
            import win32clipboard
            import win32con
        except ImportError:
            win32clipboard = None
        except ImportError:
            win32clipboard = None

        if not self.layers:
            return

        if self.selection_para_pts:
            pts = self.selection_para_pts
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            bx1, bx2 = min(xs), max(xs) + 1
            by1, by2 = min(ys), max(ys) + 1
            layer_dict = self.layers[self.active_layer]
            img = layer_dict["img"]
            ox, oy = layer_dict.get("off_x", 0), layer_dict.get("off_y", 0)
            lx1, ly1 = max(0, bx1 - ox), max(0, by1 - oy)
            lx2, ly2 = min(img.shape[1], bx2 - ox), min(img.shape[0], by2 - oy)
            if lx2 > lx1 and ly2 > ly1:
                clip_np = img[ly1:ly2, lx1:lx2].copy()
                adj_pts = [(x - ox - lx1, y - oy - ly1) for x, y in pts]
                mask = self._make_polygon_mask(adj_pts, clip_np.shape[:2])
                clip_np[~mask] = [0, 0, 0, 0]
                self.clipboard = clip_np
            return

        if not self.selection_rect:
            return

        x1, y1, x2, y2 = self.selection_rect
        sx, ex = sorted([x1, x2])
        sy, ey = sorted([y1, y2])

        layer_dict = self.layers[self.active_layer]
        img = layer_dict["img"]
        ox, oy = layer_dict.get("off_x", 0), layer_dict.get("off_y", 0)

        lx1, ly1 = max(0, sx - ox), max(0, sy - oy)
        lx2, ly2 = min(img.shape[1], ex - ox), min(img.shape[0], ey - oy)

        if lx2 > lx1 and ly2 > ly1:
            clip_np = img[ly1:ly2, lx1:lx2].copy()
            self.clipboard = clip_np
            
            if win32clipboard:
                clip_img = Image.fromarray(clip_np, "RGBA")
                
                png_output = io.BytesIO()
                clip_img.save(png_output, format="PNG")
                png_data = png_output.getvalue()
                png_output.close()

                dib_output = io.BytesIO()
                clip_img.convert("RGB").save(dib_output, "BMP")
                dib_data = dib_output.getvalue()[14:]
                dib_output.close()

                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    
                    fmt_png = win32clipboard.RegisterClipboardFormat("PNG")
                    win32clipboard.SetClipboardData(fmt_png, png_data)
                    
                    win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
                    
                    win32clipboard.CloseClipboard()
                    print("Copied to system clipboard (with alpha).")
                except Exception as e:
                    print(f"Clipboard error: {e}")

    def paste_image(self):
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
        
        if self.selection_rect:
            self.floating_x = min(self.selection_rect[0], self.selection_rect[2])
            self.floating_y = min(self.selection_rect[1], self.selection_rect[3])
        else:
            self.floating_x, self.floating_y = 0, 0
        
        self.set_tool("move_paste")
        self.redraw()
    def finalize_paste(self):
        if self.floating_image is None:
            return

        layer_dict = self.layers[self.active_layer]
        target_img = layer_dict["img"]
        th, tw = target_img.shape[:2]
        ch, cw = self.floating_image.shape[:2]

        ox, oy = layer_dict.get("off_x", 0), layer_dict.get("off_y", 0)
        lx, ly = self.floating_x - ox, self.floating_y - oy


        x1, y1 = max(0, lx), max(0, ly)
        x2, y2 = min(tw, lx + cw), min(th, ly + ch)

        if x2 > x1 and y2 > y1:
            patch_undo = []
            sx1, sy1 = x1 - lx, y1 - ly
            for dy in range(y2 - y1):
                for dx in range(x2 - x1):
                    patch_undo.append((self.active_layer, x1 + dx + ox, y1 + dy + oy, 
                                       target_img[y1 + dy, x1 + dx].copy()))
            self.undo_stack.append(patch_undo)

            sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)
            patch = self.floating_image[sy1:sy2, sx1:sx2].astype(np.float32)
            src_alpha = patch[:, :, 3:4] / 255.0
            dst = target_img[y1:y2, x1:x2].astype(np.float32)
            blended = dst * (1 - src_alpha) + patch * src_alpha
            target_img[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)

        self.floating_image = None
        self.set_tool("pen")
        self.redraw()
    def cut_selection(self):
        if not self.layers:
            return

        if self.selection_para_pts:
            self.copy_selection()
            layer_dict = self.layers[self.active_layer]
            img = layer_dict["img"]
            ox, oy = layer_dict.get("off_x", 0), layer_dict.get("off_y", 0)
            adj_pts = [(x - ox, y - oy) for x, y in self.selection_para_pts]
            mask = self._make_polygon_mask(adj_pts, img.shape[:2])
            self.save_full_undo(self.active_layer)
            img[mask] = [0, 0, 0, 0]
            self.redraw()
            return

        if self.selection_rect is None:
            return

        self.copy_selection()
        layer_dict = self.layers[self.active_layer]
        img = layer_dict["img"]
        ox, oy = layer_dict.get("off_x", 0), layer_dict.get("off_y", 0)
        x1, y1, x2, y2 = self.selection_rect
        sx, ex = sorted([x1, x2])
        sy, ey = sorted([y1, y2])

        xmin, ymin = max(0, sx - ox), max(0, sy - oy)
        xmax, ymax = min(img.shape[1], ex - ox), min(img.shape[0], ey - oy)

        xmin, xmax = max(0, xmin), min(self.width, xmax + 1)
        ymin, ymax = max(0, ymin), min(self.height, ymax + 1)

        layer_img = self.layers[self.active_layer]["img"]
        
        self.save_full_undo(self.active_layer)

        layer_img[ymin:ymax, xmin:xmax] = [0, 0, 0, 0]

        self.redraw()

    def clear_outside_selection(self):
        if not self.layers:
            return

        if self.selection_para_pts:
            self.save_full_undo(self.active_layer)
            layer_dict = self.layers[self.active_layer]
            img = layer_dict["img"]
            ox, oy = layer_dict.get("off_x", 0), layer_dict.get("off_y", 0)
            adj_pts = [(x - ox, y - oy) for x, y in self.selection_para_pts]
            mask = self._make_polygon_mask(adj_pts, img.shape[:2])
            img[~mask] = [0, 0, 0, 0]
            self.redraw()
            return

        if self.selection_rect is None:
            return

        self.save_full_undo(self.active_layer)
        layer_img = self.layers[self.active_layer]["img"]

        x1, y1, x2, y2 = self.selection_rect
        xmin, xmax = sorted([x1, x2])
        ymin, ymax = sorted([y1, y2])

        new_img = np.zeros_like(layer_img)

        xmin, xmax = max(0, xmin), min(self.width, xmax + 1)
        ymin, ymax = max(0, ymin), min(self.height, ymax + 1)

        new_img[ymin:ymax, xmin:xmax] = layer_img[ymin:ymax, xmin:xmax]

        self.layers[self.active_layer]["img"] = new_img
        self.redraw()
        

    # ================= Undo / Redo =================
    def save_full_undo(self, layer_idx):
        img_copy = self.layers[layer_idx]["img"].copy()
        self.undo_stack.append({
            "type": "full", 
            "layer_idx": layer_idx, 
            "img": img_copy
        })
        self.redo_stack.clear()
    def undo(self):
        if not self.undo_stack:
            return
        self.dirty = True
        stroke = self.undo_stack.pop()

        if isinstance(stroke, dict) and stroke.get("type") == "full":
            l_idx = stroke["layer_idx"]
            current_img = self.layers[l_idx]["img"].copy()
            
            self.layers[l_idx]["img"] = stroke["img"]

            self.redo_stack.append({
                "type": "full", 
                "layer_idx": l_idx, 
                "img": current_img
            })
        elif isinstance(stroke, tuple) and stroke[0] == "whole_layers":
            import copy
            self.redo_stack.append(("whole_layers", copy.deepcopy(self.layers), self.active_layer))
            self.layers = stroke[1]
            self.active_layer = stroke[2]


        elif isinstance(stroke, tuple) and stroke[0] == "move_layer":
            _, src, dst = stroke
            self.layers[src], self.layers[dst] = self.layers[dst], self.layers[src]
            self.redo_stack.append(("move_layer", dst, src))
            self.active_layer = src


        elif isinstance(stroke, list):
            redo_list = []
            for l, x, y, before in stroke:
                redo_list.append((l, x, y, self.layers[l]["img"][y, x].copy()))
                self.layers[l]["img"][y, x] = before
            self.redo_stack.append(redo_list)

        self.refresh_layer_panel()
        self.redraw()

    def redo(self):
        if not self.redo_stack:
            return
        stroke = self.redo_stack.pop()

        # 1. 
        if isinstance(stroke, dict) and stroke.get("type") == "full":
            l_idx = stroke["layer_idx"]
            current_img = self.layers[l_idx]["img"].copy()
            self.layers[l_idx]["img"] = stroke["img"]
            self.undo_stack.append({
                "type": "full", 
                "layer_idx": l_idx, 
                "img": current_img
            })

        # 2. whole_layers
        elif isinstance(stroke, tuple) and stroke[0] == "whole_layers":
            import copy
            self.undo_stack.append(("whole_layers", copy.deepcopy(self.layers), self.active_layer))
            self.layers = stroke[1]
            self.active_layer = stroke[2]

        # 3. move_layer
        elif isinstance(stroke, tuple) and stroke[0] == "move_layer":
            _, src, dst = stroke
            self.layers[src], self.layers[dst] = self.layers[dst], self.layers[src]
            self.undo_stack.append(("move_layer", dst, src))
            self.active_layer = dst

        elif isinstance(stroke, list):
            undo_list = []
            for l, x, y, before in stroke:
                undo_list.append((l, x, y, self.layers[l]["img"][y, x].copy()))
                self.layers[l]["img"][y, x] = before
            self.undo_stack.append(undo_list)

        self.refresh_layer_panel()
        self.redraw()
    def start_offset_loop(self, dx, dy):
        self.offset_layer(dx, dy)
        self.after_id = self.root.after(100, lambda: self.start_offset_loop(dx, dy))

    def stop_offset_loop(self, _=None):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
    def apply_offset_entry(self):
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
            # no integer value, false
            pass

    def update_offset_ui(self):
        if not self.layers:
            return
        layer = self.layers[self.active_layer]
        ox = layer.get("off_x", 0)
        oy = layer.get("off_y", 0)

        self.off_x_entry.delete(0, tk.END)
        self.off_x_entry.insert(0, str(ox))
        self.off_y_entry.delete(0, tk.END)
        self.off_y_entry.insert(0, str(oy))

    # ================= View =================
    def set_zoom_index(self, v):
        x_left, x_right = self.canvas.xview()
        y_top, y_bottom = self.canvas.yview()
        
        center_x = (x_left + x_right) / 2
        center_y = (y_top + y_bottom) / 2

        # change zoom
        self.zoom = self.zoom_levels[int(v)] / 100.0
        self.zoom_label.config(text=f"{self.zoom_levels[int(v)]}%")
        
        # redraw
        self.redraw()

        # offset
        view_width = x_right - x_left
        view_height = y_bottom - y_top
        
        self.canvas.xview_moveto(center_x - view_width / 2)
        self.canvas.yview_moveto(center_y - view_height / 2)

    def zoom_wheel(self, e):
        # Ctrl + Wheel: zoom
        if e.state & 0x0004:  # Control key
            mx = self.canvas.canvasx(e.x)/self.zoom
            my = self.canvas.canvasy(e.y)/self.zoom

            ini_start_x,ini_end_x = self.canvas.xview()
            ini_start_x *= self.width
            ini_start_y,ini_end_y = self.canvas.yview()
            ini_start_y *= self.height

            i = self.zoom_scale.get()
            old_zoom = self.zoom
            if e.delta > 0 and i < len(self.zoom_levels) - 1:
                i += 1
            elif e.delta < 0 and i > 0:
                i -= 1
            
            if i == self.zoom_scale.get(): return
            
            self.zoom_scale.set(i) # call redraw here
            self.zoom = self.zoom_levels[i] / 100.0

            moveto_x = (mx-(mx-ini_start_x)/(self.zoom)*old_zoom)
            moveto_y = (my-(my-ini_start_y)/(self.zoom)*old_zoom)
            self.canvas.xview_moveto(moveto_x/self.width/old_zoom*self.zoom)
            self.canvas.yview_moveto(moveto_y/self.height/old_zoom*self.zoom)
            self.redraw()
            
        # Shift + Wheel: horizontal scroll
        elif e.state & 0x0001:  # Shift key
            delta = -1 if e.delta > 0 else 1
            self.on_scrollbar_x("scroll", delta, "units")
        else: #vertical scroll
            delta = -1 if e.delta > 0 else 1
            self.on_scrollbar_y("scroll", delta, "units")
    def start_pan(self, e):
        self.canvas.scan_mark(e.x, e.y)

    def pan(self, e):
        self.canvas.scan_dragto(e.x, e.y, gain=1)
        self.redraw()
    def draw_simutrans_guides(self):
        b_size = self.build_paksize * self.zoom
        p_size = self.play_paksize * self.zoom
        
        zw, zh = int(self.width * self.zoom), int(self.height * self.zoom)

        for x in range(0, zw + 1, int(b_size)):
            self.canvas.create_line(x, 0, x, zh, fill="cyan", dash=(4, 4), tags="guide")
        for y in range(0, zh + 1, int(b_size)):
            self.canvas.create_line(0, y, zw, y, fill="cyan", dash=(4, 4), tags="guide")

        if self.show_base_tile:
            for bx in range(0, int(self.width / self.build_paksize)):
                for by in range(0, int(self.height / self.build_paksize)):
                    cx = (bx * self.build_paksize + self.build_paksize / 2) * self.zoom
                    cy = (by * self.build_paksize + self.build_paksize / 2) * self.zoom + self.base_offset_y * self.zoom
                
                    r_w = p_size / 2 
                    r_h = p_size / 4
                    points = [
                        cx, cy,       # 上
                        cx + r_w, cy + r_h,       # 右
                        cx, cy + 2*r_h,       # 下
                        cx - r_w, cy + r_h       # 左
                    ]
                    self.canvas.create_polygon(points, fill="", outline="yellow", width=1, tags="guide")

    def draw_pixel_grid(self, ix1, iy1, ix2, iy2):
        """Draw a 1px-per-pixel grid over the visible area once zoomed in
        enough (>=600%) for individual pixels to be worth distinguishing."""
        if self.zoom < 6.0:
            return
        x0 = self.canvas.canvasx(0)
        y0 = self.canvas.canvasy(0)
        zw = (ix2 - ix1) * self.zoom
        zh = (iy2 - iy1) * self.zoom
        for x in range(ix1, ix2 + 1):
            cx = x0 + (x - ix1) * self.zoom
            self.canvas.create_line(cx, y0, cx, y0 + zh, fill="#808080", tags="pixel_grid")
        for y in range(iy1, iy2 + 1):
            cy = y0 + (y - iy1) * self.zoom
            self.canvas.create_line(x0, cy, x0 + zw, cy, fill="#808080", tags="pixel_grid")

    def toggle_special_color_mode(self):
        self.special_color_mode = not self.special_color_mode
        self.redraw()
    # ================= Rendering =================
    def redraw(self):
        if not self.layers or self.width == 0:
            return
        self.canvas.delete("preview")
        self.canvas.delete("selection")

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        full_w = self.width * self.zoom
        full_h = self.height * self.zoom

        region_w = max(cw, full_w)
        region_h = max(ch, full_h)
        self.canvas.config(scrollregion=(0, 0, region_w, region_h))

        # 1. get area
        x_start, x_end = self.canvas.xview()
        y_start, y_end = self.canvas.yview()

        # 2. get pixel pos
        ix1 = int(x_start * self.width)
        iy1 = int(y_start * self.height)
        ix2 = int(np.ceil(x_end * self.width))
        iy2 = int(np.ceil(y_end * self.height))

        ix1, iy1 = max(0, ix1), max(0, iy1)
        ix2, iy2 = min(self.width, ix2), min(self.height, iy2)

        if ix2 <= ix1 or iy2 <= iy1: return


        # 3. crop
        img_full = self.compose_layers()
        
        if self.special_color_mode:
            print("show special color's region")
            img_full = self.get_emphasized_image(img_full)
        img_crop = img_full[iy1:iy2, ix1:ix2]

        crop_h, crop_w = img_crop.shape[:2]
        disp_w = int(crop_w * self.zoom)
        disp_h = int(crop_h * self.zoom)

        # 4. bg
        bg_size = 8
        yy, xx = np.indices((disp_h, disp_w))
        
        # offset
        offset_x = int(ix1 * self.zoom) % (bg_size * 2)
        offset_y = int(iy1 * self.zoom) % (bg_size * 2)
        
        checker = ((xx + offset_x) // bg_size + (yy + offset_y) // bg_size) % 2
        
        # RGB data of BG
        bg_rgb = np.zeros((disp_h, disp_w, 3), dtype=np.uint8)
        bg_rgb[checker == 0] = [220, 220, 220]
        bg_rgb[checker == 1] = [190, 190, 190]
        
        # PIL->RGBA
        bg_pil = Image.fromarray(bg_rgb, "RGB").convert("RGBA")

        # 5. back->front
        fg_pil = Image.fromarray(img_crop, "RGBA").resize((disp_w, disp_h), Image.NEAREST)
        bg_pil.alpha_composite(fg_pil)

        # 6. draw in canvas
        self.tkimg = ImageTk.PhotoImage(bg_pil)
        self.canvas.delete("all")

        self.canvas.create_image(
            self.canvas.canvasx(0),
            self.canvas.canvasy(0),
            image=self.tkimg,
            anchor="nw"
        )

        self.draw_pixel_grid(ix1, iy1, ix2, iy2)

        self.canvas.delete("selection_ui")
        if self.tool == "select" and self.selection_rect:
            x1, y1, x2, y2 = self.selection_rect
            zx1, zy1 = x1 * self.zoom, y1 * self.zoom
            zx2, zy2 = x2 * self.zoom, y2 * self.zoom
            self.canvas.create_rectangle(zx1, zy1, zx2, zy2,
                                         outline="white", dash=(4, 4), tags="selection_ui")
            self.canvas.create_rectangle(zx1, zy1, zx2, zy2,
                                         outline="black", dash=(4, 4), dashoffset=4, tags="selection_ui")
        if self.tool == "para_select" and self.selection_para_pts:
            pts_z = [(p[0]*self.zoom, p[1]*self.zoom) for p in self.selection_para_pts]
            n = len(pts_z)
            for i in range(n):
                p1, p2 = pts_z[i], pts_z[(i+1) % n]
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                        fill="white", dash=(4, 4), tags="selection_ui")
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                        fill="black", dash=(4, 4), dashoffset=4, tags="selection_ui")

        # ---- Simutrans line ----
        self.canvas.delete("fixed_guide") # remove old guide
        if self.show_grid:
            self.draw_simutrans_guides()

        if self.floating_image is not None:
            f_img = Image.fromarray(self.floating_image, "RGBA")
            zw, zh = int(f_img.width * self.zoom), int(f_img.height * self.zoom)
            if zw > 0 and zh > 0:
                f_img = f_img.resize((zw, zh), Image.NEAREST)
                self.floating_tk = ImageTk.PhotoImage(f_img)
                self.canvas.create_image(self.floating_x * self.zoom, 
                                         self.floating_y * self.zoom, 
                                         anchor="nw", image=self.floating_tk, tags="floating")   
            floating_x, floating_y = int(self.floating_x*self.zoom), int(self.floating_y*self.zoom)         
            self.canvas.create_rectangle(
                floating_x, floating_y, floating_x+zw, floating_y+zh,
                outline="#222222",
                width=2,
                dash=(4, 4),
                tags="floating_ui"
            )

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
    if sys.platform == "win32":
        try:
            # Make the process DPI-aware so mouse event coordinates line up
            # 1:1 with the pixels Tk actually draws. Without this, Windows
            # display scaling (>100%) makes the OS scale mouse coordinates
            # while Tk still renders at "96 DPI" logical pixels, so the
            # cursor position reported by events drifts from the pixel the
            # user actually clicked on.
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    root = tk.Tk()
    ImageEditor(root)
    root.mainloop()
