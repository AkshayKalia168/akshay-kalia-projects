from dotenv import load_dotenv
load_dotenv()

import os
import tkinter as tk
from PIL import Image, ImageTk

from dashboard import DashboardFrame
from view_log import ViewLogFrame
from addscrap import AddScrapFrame

try:
    from view_predictions import ViewPredictionsFrame
except ImportError:
    from view_predictions import PredictionsDashboardFrame as ViewPredictionsFrame

# Optional Generate Report
GENERATE_REPORT_AVAILABLE = True
try:
    from generate_report import GenerateReportFrame
except Exception:
    GenerateReportFrame = None
    GENERATE_REPORT_AVAILABLE = False


BASE_DIR = os.path.dirname(__file__)
IMAGE_DIR = os.path.join(BASE_DIR, "images")

SIDEBAR_BG = "#0F172A"
SIDEBAR_HOVER = "#1E293B"
SIDEBAR_ACTIVE = "#14532D"   # subtle green tint for active icon
ACTIVE_STRIP = "#16A34A"     # green strip color


def load_icon(filename, size):
    path = os.path.join(IMAGE_DIR, filename)
    img = Image.open(path).convert("RGBA")
    img = img.resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None

    def showtip(self):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() // 2
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self.text, justify="left",
            background="#333333", foreground="white",
            relief="solid", borderwidth=1, font=("Segoe UI", 10),
            padx=6, pady=4
        ).pack()

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class ScrapSenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ScrapSense — Recruiter Edition")
        self.configure(bg="#F8FAFC")

        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
                self.geometry(f"{int(sw*0.9)}x{int(sh*0.9)}+40+40")

        self.frames = {}
        self._sidebar_buttons = {}   # name -> (label, strip_frame)
        self._current_page = None

        self._build_sidebar()
        self._build_container()
        self.show_frame("Dashboard")

    # ---------- Sidebar ----------
    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=80)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # small logo (no title)
        try:
            logo = load_icon("scraplogo.png", (40, 40))
            lbl = tk.Label(self.sidebar, image=logo, bg=SIDEBAR_BG)
            lbl.image = logo
            lbl.pack(pady=16)
        except Exception:
            tk.Label(self.sidebar, text="SS", fg="white", bg=SIDEBAR_BG, font=("Segoe UI", 14, "bold")).pack(pady=16)

        buttons = [
            ("Dashboard",        "dashboard.png"),
            ("Add Scrap",        "add-button.png"),
            ("View Scrap Logs",  "doc.png"),
            ("View Predictions", "prediction.png"),
        ]
        if GENERATE_REPORT_AVAILABLE and GenerateReportFrame is not None:
            buttons.append(("Generate Report", "report-card.png"))

        def hover_on(widget):
            if widget is not self._active_widget:
                widget.config(bg=SIDEBAR_HOVER)

        def hover_off(widget):
            if widget is not self._active_widget:
                widget.config(bg=SIDEBAR_BG)

        self._active_widget = None
        for name, icon_file in buttons:
            try:
                icon = load_icon(icon_file, (30, 30))
            except Exception:
                icon = None

            # left green strip (hidden until active)
            strip = tk.Frame(self.sidebar, bg=ACTIVE_STRIP, width=4, height=46)
            strip.place_forget()

            btn = tk.Label(self.sidebar, image=icon, bg=SIDEBAR_BG, cursor="hand2", width=80, height=46)
            if icon:
                btn.image = icon
            btn.pack(pady=6)
            btn.bind("<Button-1>", lambda e, n=name, b=btn, s=strip: self._on_sidebar_click(n, b, s))

            tip = Tooltip(btn, name)
            btn.bind("<Enter>", lambda e, b=btn: (hover_on(b), tip.showtip()))
            btn.bind("<Leave>", lambda e, b=btn: (hover_off(b), tip.hidetip()))

            self._sidebar_buttons[name] = (btn, strip)

    def _on_sidebar_click(self, name, btn, strip):
        self.show_frame(name)
        # deactivate previous
        if self._active_widget and self._active_widget is not btn:
            self._active_widget.config(bg=SIDEBAR_BG)
        # hide all strips
        for b, s in self._sidebar_buttons.values():
            s.place_forget()
        # activate this one
        btn.config(bg=SIDEBAR_ACTIVE)
        # place the strip at the left edge of this button
        sx = btn.winfo_x()
        sy = btn.winfo_y()
        btn.update_idletasks()
        strip.configure(height=btn.winfo_height())
        strip.place(x=sx, y=sy)
        self._active_widget = btn
        self._current_page = name

    # ---------- Container / Frames ----------
    def _build_container(self):
        container = tk.Frame(self, bg="#F8FAFC")
        container.pack(side="left", expand=True, fill="both")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames["Dashboard"]        = DashboardFrame(container, self)
        self.frames["Add Scrap"]        = AddScrapFrame(container, self)
        self.frames["View Scrap Logs"]  = ViewLogFrame(container, self)
        self.frames["View Predictions"] = ViewPredictionsFrame(container, self)

        if GENERATE_REPORT_AVAILABLE and GenerateReportFrame is not None:
            self.frames["Generate Report"] = GenerateReportFrame(container, self)
        else:
            placeholder = tk.Frame(container, bg="#F8FAFC")
            tk.Label(placeholder, text="Generate Report is not available.", bg="#F8FAFC",
                     fg="#64748B", font=("Segoe UI", 14)).pack(expand=True)
            self.frames["Generate Report"] = placeholder

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, name):
        frame = self.frames.get(name)
        if frame:
            frame.tkraise()


if __name__ == "__main__":
    app = ScrapSenseApp()
    app.mainloop()
