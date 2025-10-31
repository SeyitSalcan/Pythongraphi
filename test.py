import tkinter as tk
from tkinter import ttk

class ExcelHeaderFilter(ttk.Frame):
    def __init__(self, parent, columns, rows, height=18):
        super().__init__(parent)
        self.columns = list(columns)
        self.full_data = list(rows)
        self.active_filters = {c: "" for c in self.columns}
        self.sort_col = None
        self.sort_desc = False

        # ---- Stil (doğru sınıf adları)
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        custom_style = "EHFT.Treeview"
        custom_heading = "EHFT.Treeview.Heading"
        fallback_style = "Treeview"  # eğer custom başarısız olursa

        # Custom tarzı konfigüre et (Treeview sınıfına uygun)
        try:
            style.configure(custom_style,
                            font=("Segoe UI", 9),
                            rowheight=24,
                            background="#FFFFFF",
                            fieldbackground="#FFFFFF",
                            borderwidth=0)
            style.configure(custom_heading,
                            font=("Segoe UI", 9, "bold"),
                            background="#EEF1F5",
                            relief="flat")
            style.map(custom_heading, background=[("active", "#D7DBE2")])
            use_style = custom_style
        except tk.TclError:
            # Bazı platformlarda özel layout yoksa defaults'a dön
            use_style = fallback_style

        # ---- Kapsayıcı
        holder = ttk.Frame(self)
        holder.pack(fill="both", expand=True)

        # ---- Tree + scroll
        self.tree = ttk.Treeview(
            holder,
            columns=self.columns,
            show="headings",
            height=height,
            style=use_style
        )
        self.vsb = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(holder, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=self.vsb.set, xscroll=self.hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)

        # Başlık/kolonlar
        for c in self.columns:
            # heading stilini custom'a taşıyamıyorsak default da iş görür
            try:
                self.tree.heading(c, text=c, anchor="center", style=custom_heading)
            except tk.TclError:
                self.tree.heading(c, text=c, anchor="center")
            self.tree.column(c, width=140, minwidth=70, stretch=True, anchor="center")

        # ---- Overlay panel (aynı konteyner içinde)
        self.panel = ttk.Frame(holder, relief="solid", borderwidth=1)
        self.panel_visible = False
        self.panel_col = None

        # Panel içeriği
        self._panel_title = ttk.Label(self.panel, text="", font=("Segoe UI", 9, "bold"))
        self._panel_entry = ttk.Entry(self.panel)
        self._btn_row = ttk.Frame(self.panel)
        self._btn_apply = ttk.Button(self.panel, text="Filtrele", command=self._apply_filter_click)
        self._btn_clear = ttk.Button(self.panel, text="Temizle", command=self._clear_filter_click)
        self._btn_asc = ttk.Button(self._btn_row, text="▲ Artan", command=lambda: self._apply_sort(False))
        self._btn_desc = ttk.Button(self._btn_row, text="▼ Azalan", command=lambda: self._apply_sort(True))

        self._panel_title.pack(anchor="w", padx=10, pady=(8, 2))
        self._panel_entry.pack(fill="x", padx=10)
        self._btn_row.pack(fill="x", padx=10, pady=(6, 2))
        self._btn_asc.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._btn_desc.pack(side="left", expand=True, fill="x", padx=(4, 0))
        self._btn_apply.pack(fill="x", padx=10, pady=(4, 2))
        self._btn_clear.pack(fill="x", padx=10, pady=(0, 8))

        # ---- Etkileşimler
        self.tree.bind("<Button-1>", self._on_header_click, add="+")
        self.bind_all("<Button-1>", self._global_click_close, add="+")
        self.bind_all("<Escape>", lambda e: self._hide_panel(), add="+")

        # Başlangıç veri yükle
        self._recompute_and_render()

    # ---------- Panel konum hesaplama (hizalı & scroll uyumlu)
    def _place_panel_below_column(self, col_index: int):
        total_w = sum(self.tree.column(c, "width") for c in self.columns)
        try:
            view0 = self.tree.xview()[0]  # 0..1
        except Exception:
            view0 = 0.0
        offset_px = int(total_w * view0)

        col_x = sum(self.tree.column(self.columns[i], "width") for i in range(col_index))

        tree_x = self.tree.winfo_rootx()
        tree_y = self.tree.winfo_rooty()

        holder = self.panel.master
        holder_x = holder.winfo_rootx()
        holder_y = holder.winfo_rooty()

        rel_x = (tree_x - holder_x) + col_x - offset_px
        rel_y = (tree_y - holder_y) + self._heading_height()

        w, h = 220, 160
        self.panel.place(x=max(0, rel_x), y=max(0, rel_y), width=w, height=h)

    def _heading_height(self):
        # Heading yüksekliğini makul bir değerle sabitle (temalara göre stabil)
        return 26

    # ---------- Click handling
    def _on_header_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "heading":
            return
        col_id = self.tree.identify_column(event.x)
        if not col_id:
            return
        col_idx = int(col_id.replace("#", "")) - 1
        if col_idx < 0 or col_idx >= len(self.columns):
            return

        self.panel_col = self.columns[col_idx]
        self._panel_title.config(text=self.panel_col)
        self._panel_entry.delete(0, tk.END)
        if self.active_filters.get(self.panel_col):
            self._panel_entry.insert(0, self.active_filters[self.panel_col])

        self._place_panel_below_column(col_idx)
        self.panel.lift()
        self.panel_visible = True
        self._panel_entry.focus_set()

    def _global_click_close(self, event):
        if not self.panel_visible:
            return
        w = event.widget
        while w is not None:
            if w is self.panel:
                return
            w = getattr(w, "master", None)
        self._hide_panel()

    def _hide_panel(self):
        if self.panel_visible:
            self.panel.place_forget()
            self.panel_visible = False
            self.panel_col = None

    # ---------- Panel butonları
    def _apply_filter_click(self):
        kw = (self._panel_entry.get() or "").strip().lower()
        self.active_filters[self.panel_col] = kw
        self._recompute_and_render()
        self._hide_panel()

    def _clear_filter_click(self):
        self.active_filters[self.panel_col] = ""
        self._recompute_and_render()
        self._hide_panel()

    def _apply_sort(self, desc: bool):
        self.sort_col = self.panel_col
        self.sort_desc = desc
        self._recompute_and_render()
        self._hide_panel()

    # ---------- Veri işleme & render
    def _recompute_and_render(self):
        data = self.full_data
        # Filtreler
        for c, kw in self.active_filters.items():
            if kw:
                idx = self.columns.index(c)
                data = [r for r in data if kw in str(r[idx]).lower()]
        # Sıralama
        if self.sort_col is not None:
            idx = self.columns.index(self.sort_col)
            def keyfunc(row):
                v = row[idx]
                try:
                    return float(str(v).replace(",", "."))
                except Exception:
                    return str(v).lower()
            data = sorted(data, key=keyfunc, reverse=self.sort_desc)

        # Başlık okları
        for c in self.columns:
            t = c
            if c == getattr(self, "sort_col", None):
                t += " ▼" if self.sort_desc else " ▲"
            self.tree.heading(c, text=t)

        # Tree doldur
        self.tree.delete(*self.tree.get_children())
        for r in data:
            self.tree.insert("", "end", values=r)


# ==== DEMO ====
if __name__ == "__main__":
    root = tk.Tk()
    root.title("SQL Panel • Excel Başlık Filtresi (Stabil Overlay)")
    root.geometry("980x480")
    root.configure(bg="#F3F4F7")

    ttk.Label(root, text="Excel Mantığında Sütun Paneli",
              font=("Segoe UI", 11, "bold"), background="#F3F4F7").pack(pady=(10, 6))

    cols = ["ID", "İl", "İlçe", "Kaynak", "Süre (dk)"]
    rows = [
        (1, "Antalya", "Kepez", "Dağıtım-OG", 45),
        (2, "Burdur", "Merkez", "Dağıtım-AG", 32),
        (3, "Isparta", "Yalvaç", "İletim", 120),
        (4, "Antalya", "Alanya", "Dağıtım-OG", 20),
        (5, "Isparta", "Senirkent", "Dağıtım-AG", 80),
        (6, "Antalya", "Manavgat", "Dağıtım-OG", 65),
        (7, "Burdur", "Gölhisar", "Dağıtım-AG", 55),
        (8, "Antalya", "Finike", "İletim", 90),
        (9, "Isparta", "Eğirdir", "Dağıtım-OG", 40),
        (10, "Antalya", "Kumluca", "Dağıtım-AG", 75),
    ]

    grid = ExcelHeaderFilter(root, cols, rows, height=16)
    grid.pack(fill="both", expand=True, padx=14, pady=10)

    root.mainloop()
