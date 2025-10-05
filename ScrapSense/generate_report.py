from dotenv import load_dotenv
load_dotenv()

import os, tempfile, shutil, webbrowser
from datetime import datetime, date, timedelta
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from tkcalendar import Calendar
import psycopg2
import pandas as pd
import plotly.express as px

# HTML templating (PDF is optional)
from jinja2 import Environment, FileSystemLoader, select_autoescape
try:
    import pdfkit
except Exception:
    pdfkit = None  # optional

# ---------- THEME ----------
APP_BG        = "#ECF4FA"
CARD_BG       = "#FFFFFF"
BORDER_COLOR  = "#E5E7EB"
TEXT_MAIN     = "#0E2A47"
TEXT_SECOND   = "#374151"
PRIMARY_BG    = "#16A34A"
PRIMARY_FG    = "#FFFFFF"
PRIMARY_BG_HI = "#12833B"
NEUTRAL_BG    = "#E5E7EB"
NEUTRAL_FG    = "#111827"
ROW_A         = "#FFFFFF"
ROW_B         = "#F9FAFB"
HEAD_BG       = "#F3F4F6"
HEAD_FG       = "#111827"
FONT_FAMILY   = "Segoe UI"

IMAGE_DIR          = os.path.join(os.path.dirname(__file__), "images")
ICON_REPORT_HEADER = "icon_report.png"
ICON_PREVIEW       = "icon_view.png"
ICON_EXPORT        = "icon_pdf.png"
ICON_KPI_TOTAL     = "kpi_weight.png"
ICON_KPI_ENTRIES   = "kpi_list.png"
ICON_KPI_AVGDAY    = "kpi_trend.png"
ICON_KPI_TOPREASON = "kpi_cause.png"
ICON_CALENDAR      = "schedule.png"

DEFAULT_PDF_NAME  = "ScrapSense_Report.pdf"
DEFAULT_HTML_NAME = "ScrapSense_Report.html"

# Support all your historical template names (most important: "reporthtml")
TEMPLATE_CANDIDATES = [
    "reporthtml",
    "reporthtml.html",
    "report.html",
    "report_template_legacy_pro.html",
    "report_template.html",
]

# ---------- DB ----------
def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if (v is not None and v != "") else default

def get_db_connection():
    host = _env("PGHOST", "127.0.0.1")
    port = int(_env("PGPORT", "5432"))
    db   = _env("PGDATABASE", "scrapsense")
    user = _env("PGUSER", "scrapsense")
    pwd  = _env("PGPASSWORD", "")

    return psycopg2.connect(
        dbname=db, user=user, password=pwd,
        host=host, port=port, connect_timeout=10,
        sslmode=os.getenv("PGSSLMODE", "prefer"),
    )

def table_has_column(conn, table_name: str, column_name: str, schema: str = "public") -> bool:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema=%s AND table_name=%s AND column_name=%s
            LIMIT 1
        """, (schema, table_name, column_name))
        return cur.fetchone() is not None

# ---------- DATA ----------
def load_scrap_data(start_date, end_date, shift=None, operator=None, reason=None):
    conn = get_db_connection()
    try:
        has_entry_type = table_has_column(conn, "scrap_logs", "entry_type")
        has_total_prod = table_has_column(conn, "scrap_logs", "total_produced")

        cols = [
            "id","machine_operator","machine_name",
            "date::date AS date","quantity::numeric AS quantity",
            "unit","shift","reason","comments"
        ]
        if has_total_prod:
            cols.append("total_produced::numeric AS total_produced")
        if has_entry_type:
            cols.append("entry_type")

        where = ["date::date BETWEEN %(start)s AND %(end)s"]
        params = {"start": start_date, "end": end_date}
        if shift and shift != "All":
            where.append("shift = %(shift)s"); params["shift"] = shift
        if operator:
            where.append("machine_operator ILIKE %(op)s"); params["op"] = f"%{operator.strip()}%"
        if reason:
            where.append("reason ILIKE %(re)s"); params["re"] = f"%{reason.strip()}%"

        sql = f"SELECT {', '.join(cols)} FROM public.scrap_logs WHERE {' AND '.join(where)} ORDER BY date ASC, id ASC"
        df = pd.read_sql_query(sql, conn, params=params)
        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
        if "total_produced" in df.columns:
            df["total_produced"] = pd.to_numeric(df["total_produced"], errors="coerce")
            df["scrap_percent"] = df.apply(
                lambda r: (float(r["quantity"]) / float(r["total_produced"]) * 100.0)
                if pd.notnull(r["total_produced"]) and float(r["total_produced"]) > 0 else None,
                axis=1
            )
        return df
    finally:
        conn.close()

def compute_kpis(df: pd.DataFrame):
    if df.empty:
        return {"total_scrap":0.0,"entries":0,"avg_per_day":0.0,"top_reason":"—",
                "scrap_rate":None,"total_produced":None,"finished_qty":None,
                "top_machine":None,"top_machine_qty":None}

    total = float(df["quantity"].sum())
    entries = int(len(df))
    per_day = df.groupby("date")["quantity"].sum()
    avg_day = float(per_day.mean()) if not per_day.empty else 0.0

    top_reason = df.groupby("reason")["quantity"].sum().sort_values(ascending=False)
    top_reason_label = top_reason.index[0] if len(top_reason) else "—"

    total_produced = None; scrap_rate = None
    if "total_produced" in df.columns:
        total_produced = pd.to_numeric(df["total_produced"], errors="coerce").dropna().sum()
        if total_produced > 0:
            scrap_rate = total / total_produced * 100.0

    finished_qty = (total_produced - total) if (total_produced is not None) else None

    by_machine = df.groupby("machine_name")["quantity"].sum().sort_values(ascending=False)
    top_machine = by_machine.index[0] if len(by_machine) else None
    top_machine_qty = float(by_machine.iloc[0]) if len(by_machine) else None

    return {
        "total_scrap": total,
        "entries": entries,
        "avg_per_day": avg_day,
        "top_reason": top_reason_label if top_reason_label else "—",
        "scrap_rate": scrap_rate,
        "total_produced": total_produced,
        "finished_qty": finished_qty,
        "top_machine": top_machine,
        "top_machine_qty": top_machine_qty
    }

# ---------- Helpers ----------
def _as_uri(p: Path) -> str:
    return p.resolve().as_uri()

def _save_fig(fig, path: Path, w=680, h=260, scale=2):
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    fig.write_image(str(path), width=w, height=h, scale=scale)  # needs kaleido

def _period_delta(start_date: date, end_date: date):
    days = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days-1)
    return prev_start, prev_end

def _fmt_delta(curr, prev, for_scrap_percent=False):
    if prev is None or prev == 0 or curr is None:
        return "—", "neutral"
    diff = curr - prev
    pct = (diff / prev) * 100.0
    if for_scrap_percent:
        cls = "down" if diff < 0 else ("up" if diff > 0 else "neutral")
    else:
        cls = "up" if diff > 0 else ("down" if diff < 0 else "neutral")
    arrow = "▲" if diff > 0 else ("▼" if diff < 0 else "→")
    return f"{arrow} {abs(pct):.1f}%", cls

def _choose_template_name():
    base = os.path.dirname(__file__)
    for name in TEMPLATE_CANDIDATES:
        if os.path.exists(os.path.join(base, name)):
            return name
    return TEMPLATE_CANDIDATES[0]

# Generate HTML, and optionally PDF. If PDF unavailable, can save HTML with assets.
def generate_report(df: pd.DataFrame, start_date: date, end_date: date,
                    save_path: str | None, filters: dict | None = None) -> tuple[str, str | None]:
    """Returns (html_path, pdf_path_or_none)."""
    tmpdir = Path(tempfile.mkdtemp())
    try:
        # previous period (for deltas)
        prev_start, prev_end = _period_delta(start_date, end_date)
        try:
            df_prev = load_scrap_data(prev_start, prev_end,
                                      filters.get("shift") if filters else None,
                                      filters.get("operator") if filters else None,
                                      filters.get("reason") if filters else None)
        except Exception:
            df_prev = df.iloc[0:0]

        k_cur = compute_kpis(df)
        k_prev = compute_kpis(df_prev) if df_prev is not None else {"scrap_rate": None}

        scrap_pct = (f"{k_cur['scrap_rate']:.2f}%" if k_cur["scrap_rate"] is not None else "—")
        delta_str, delta_class = _fmt_delta(k_cur["scrap_rate"], k_prev["scrap_rate"], for_scrap_percent=True)
        trend_class = "down" if delta_class == "down" else ("up" if delta_class == "up" else "")
        trend_arrow = "▼" if trend_class == "down" else ("▲" if trend_class == "up" else "")

        hero = {
            "scrap_pct": scrap_pct,
            "scrap_delta": delta_str if delta_str != "—" else "n/a",
            "trend_class": trend_class,
            "trend_arrow": trend_arrow,
            "finished_qty": f"{(k_cur['total_produced']-k_cur['total_scrap']):.2f}" if k_cur.get("total_produced") else "—",
            "scrap_qty": f"{k_cur['total_scrap']:.2f}"
        }

        minis = [
            {"label":"Work Center Scrap %",   "value": scrap_pct},
            {"label":"Work Center Scrap",     "value": f"{k_cur['total_scrap']:.2f}"},
            {"label":"Work Center Output",    "value": f"{(k_cur['total_produced'] or 0):.2f}" if k_cur.get("total_produced") else "—"},
            {"label":"Machine Center Scrap %","value": f"{(k_cur.get('top_machine_qty')/k_cur['total_produced']*100):.2f}%"
                                                      if (k_cur.get('top_machine_qty') and k_cur.get('total_produced')) else "—"},
            {"label":"Machine Center Scrap",  "value": f"{(k_cur.get('top_machine_qty') or 0):.2f}" if k_cur.get("top_machine_qty") else "—"},
            {"label":"Top Reason",            "value": k_cur['top_reason']},
        ]

        # Charts -> PNG files
        ts = df.groupby("date", as_index=False)["quantity"].sum() if not df.empty else pd.DataFrame({"date":[],"quantity":[]})
        line_fig = px.line(ts, x="date", y="quantity");      _save_fig(line_fig, tmpdir/"line.png")
        if not df.empty and "shift" in df.columns:
            total_q = max(df["quantity"].sum(), 1)
            s = df.groupby("shift")["quantity"].sum()
            sh = (s * 100.0 / total_q).reset_index(); sh.columns = ["shift","percent"]
            shift_fig = px.bar(sh.sort_values("percent"), x="percent", y="shift", orientation="h")
        else:
            shift_fig = px.bar(pd.DataFrame({"percent":[],"shift":[]}), x="percent", y="shift")
        _save_fig(shift_fig, tmpdir/"shift.png")

        if not df.empty and "reason" in df.columns:
            rs = df.groupby("reason", as_index=False)["quantity"].sum()
            reason_fig = px.bar(rs.sort_values("quantity", ascending=False).head(12), x="reason", y="quantity")
        else:
            reason_fig = px.bar(pd.DataFrame({"reason":[],"quantity":[]}), x="reason", y="quantity")
        _save_fig(reason_fig, tmpdir/"reason.png")

        if not df.empty and "machine_name" in df.columns:
            mc = df.groupby("machine_name", as_index=False)["quantity"].sum()
            machine_fig = px.bar(mc.sort_values("quantity", ascending=False).head(12), x="machine_name", y="quantity")
        else:
            machine_fig = px.bar(pd.DataFrame({"machine_name":[],"quantity":[]}), x="machine_name", y="quantity")
        _save_fig(machine_fig, tmpdir/"machine.png")

        charts = {"line": _as_uri(tmpdir/"line.png"),
                  "shift": _as_uri(tmpdir/"shift.png"),
                  "reason": _as_uri(tmpdir/"reason.png"),
                  "machine": _as_uri(tmpdir/"machine.png")}

        # top 3 with deltas
        def top3_with_delta(df_now, df_prev, by):
            if df_now.empty:
                return [{"name":"—","qty":"—","delta":"—","delta_class":""}]*3
            now = df_now.groupby(by)["quantity"].sum().sort_values(ascending=False).head(3)
            prev = df_prev.groupby(by)["quantity"].sum() if not df_prev.empty else pd.Series(dtype=float)
            out = []
            for name, qty in now.items():
                prev_q = float(prev.get(name, 0))
                if prev_q == 0:
                    out.append({"name":name,"qty":f"{float(qty):.2f}","delta":"new","delta_class":"up"})
                else:
                    sign = "up" if qty > prev_q else ("down" if qty < prev_q else "neutral")
                    pct = abs((qty - prev_q)/prev_q*100.0)
                    out.append({"name":name,"qty":f"{float(qty):.2f}",
                                "delta":f"{'▲' if sign=='up' else ('▼' if sign=='down' else '→')} {pct:.1f}%",
                                "delta_class":sign})
            while len(out) < 3:
                out.append({"name":"—","qty":"—","delta":"—","delta_class":""})
            return out

        top3_machines = top3_with_delta(df, df_prev, "machine_name")
        top3_ops      = top3_with_delta(df, df_prev, "machine_operator")

        insights = []
        if not df.empty:
            by_shift = df.groupby('shift')['quantity'].sum()
            by_machine = df.groupby('machine_name')['quantity'].sum()
            by_operator = df.groupby('machine_operator')['quantity'].sum()
            by_reason = df.groupby('reason')['quantity'].sum()
            if not by_shift.empty: insights.append(f"Highest Shift: <b>{by_shift.idxmax()}</b> ({by_shift.max():.0f})")
            if not by_machine.empty: insights.append(f"Top Machine: <b>{by_machine.idxmax()}</b> ({by_machine.max():.0f})")
            if not by_operator.empty: insights.append(f"Top Operator: <b>{by_operator.idxmax()}</b> ({by_operator.max():.0f})")
            if not by_reason.empty: insights.append(f"Leading Cause: <b>{by_reason.idxmax()}</b> ({by_reason.max():.0f})")
            if k_cur["scrap_rate"] is not None: insights.append(f"Scrap %: <b>{k_cur['scrap_rate']:.2f}%</b>")

        table_cols = [c for c in ["date","shift","machine_operator","machine_name","reason","quantity","unit","comments"] if c in df.columns]
        table_data = df[table_cols].astype(str).values.tolist() if not df.empty else []

        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)),
                          autoescape=select_autoescape(['html','xml']))
        template = env.get_template(_choose_template_name())

        html = template.render(
            start_date=start_date, end_date=end_date,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            hero=hero, minis=minis, insights=insights, charts=charts,
            top3_machines=top3_machines, top3_ops=top3_ops,
            table_cols=[c.title().replace("_"," ") for c in table_cols],
            table_data=table_data
        )

        # write temp HTML
        html_tmp = tmpdir / "report.html"
        html_tmp.write_text(html, encoding="utf-8")

        # Decide outcome
        pdf_path = None
        if save_path and str(save_path).lower().endswith(".pdf"):
            wkhtml = (os.getenv("WKHTMLTOPDF_PATH") or shutil.which("wkhtmltopdf"))
            if pdfkit and wkhtml:
                cfg = pdfkit.configuration(wkhtmltopdf=wkhtml)
                options = {
                    "enable-local-file-access": "",
                    "load-error-handling": "ignore",
                    "quiet": "",
                    "margin-bottom": "15mm",
                    "footer-left": "ScrapSense | Confidential",
                    "footer-right": "Page [page] of [toPage]",
                    "footer-font-size": "8"
                }
                pdfkit.from_file(str(html_tmp), save_path, configuration=cfg, options=options)
                pdf_path = save_path
            else:
                # fallback: change to HTML path beside requested PDF
                save_path = os.path.splitext(save_path)[0] + ".html"

        if save_path and str(save_path).lower().endswith(".html"):
            # copy html + chart images next to it, and rewrite srcs to filenames
            out = Path(save_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            # rewrite src to filenames
            html_local = html.replace(str(charts["line"]), "line.png") \
                             .replace(str(charts["shift"]), "shift.png") \
                             .replace(str(charts["reason"]), "reason.png") \
                             .replace(str(charts["machine"]), "machine.png")
            out.write_text(html_local, encoding="utf-8")
            for name in ["line.png","shift.png","reason.png","machine.png"]:
                shutil.copy2(tmpdir/name, out.parent/name)
            return str(out), pdf_path

        # no save path: open temp HTML in browser
        webbrowser.open_new_tab(html_tmp.as_uri())
        return str(html_tmp), pdf_path

    finally:
        # keep tmpdir if we returned temp HTML path; otherwise, safe to remove
        pass  # temp cleaned by OS; do not force-delete to keep temp HTML viewable


# ---------- TK UI ----------
def load_icon(filename, size):
    from PIL import Image, ImageTk
    try:
        path = os.path.join(IMAGE_DIR, filename)
        if not os.path.exists(path):
            return None
        img = Image.open(path).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


class GenerateReportFrame(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg=APP_BG)
        self.controller = controller
        self.current_df = pd.DataFrame()
        self._calendar_imgs = []
        self._init_style()
        self._build()

    def _init_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", background=APP_BG, foreground=TEXT_SECOND, font=(FONT_FAMILY, 12))
        style.configure("PageTitle.TLabel", background=APP_BG, foreground=TEXT_MAIN, font=(FONT_FAMILY, 24, "bold"))
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_SECOND, font=(FONT_FAMILY, 12, "bold"))
        style.configure("CardValue.TLabel", background=CARD_BG, foreground=TEXT_MAIN, font=(FONT_FAMILY, 16, "bold"))
        style.configure("Primary.TButton",
                        background=PRIMARY_BG, foreground=PRIMARY_FG,
                        font=(FONT_FAMILY, 12, "bold"), padding=8, relief="flat")
        style.map("Primary.TButton", background=[("active", PRIMARY_BG_HI), ("pressed", PRIMARY_BG_HI)])
        style.configure("Neutral.TButton",
                        background=NEUTRAL_BG, foreground=NEUTRAL_FG,
                        font=(FONT_FAMILY, 12, "bold"), padding=8, relief="flat")
        style.configure("Treeview",
                        background=ROW_A, fieldbackground=ROW_A,
                        foreground="#111", rowheight=28, font=(FONT_FAMILY, 11))
        style.configure("Treeview.Heading",
                        background=HEAD_BG, foreground=HEAD_FG, font=(FONT_FAMILY, 11, "bold"))
        style.map("Treeview", background=[("selected", "#DBEAFE")])

    def _calendar_button(self, parent, target_entry):
        img = load_icon(ICON_CALENDAR, (20, 20))
        btn = tk.Button(parent, image=img if img else None, text="" if img else "📅",
                        bg=CARD_BG, bd=0, cursor="hand2",
                        command=lambda: self._open_calendar_for(target_entry))
        if img:
            self._calendar_imgs.append(img)
        return btn

    def _open_calendar_for(self, target_entry):
        top = tk.Toplevel(self); top.title("Select Date")
        top.transient(self.winfo_toplevel()); top.grab_set()
        x = target_entry.winfo_rootx()
        y = target_entry.winfo_rooty() + target_entry.winfo_height() + 6
        top.geometry(f"+{x}+{y}")
        today = datetime.now()
        cal = Calendar(top, selectmode="day", year=today.year, month=today.month, day=today.day)
        cal.pack(padx=12, pady=12)
        def pick_date():
            raw = cal.get_date()
            dt = None
            for fmt in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(raw, fmt); break
                except ValueError: pass
            if dt is None: dt = today
            target_entry.delete(0, tk.END); target_entry.insert(0, dt.strftime("%Y-%m-%d")); top.destroy()
        ttk.Button(top, text="Select", command=pick_date).pack(pady=8)

    def _build(self):
        header_row = tk.Frame(self, bg=APP_BG); header_row.pack(fill="x", padx=24, pady=(20, 8))
        icon = load_icon(ICON_REPORT_HEADER, (28, 28))
        if icon:
            tk.Label(header_row, image=icon, bg=APP_BG).pack(side="left"); self._icon_header = icon
        ttk.Label(header_row, text="Generate Reports", style="PageTitle.TLabel").pack(side="left", padx=(10, 0))

        filt = tk.Frame(self, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER_COLOR)
        filt.pack(fill="x", padx=24, pady=(0, 12))
        row = tk.Frame(filt, bg=CARD_BG); row.pack(fill="x", padx=16, pady=12)

        ttk.Label(row, text="Start Date:", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.start_date = ttk.Entry(row, width=16); self.start_date.grid(row=0, column=1, sticky="w")
        self._calendar_button(row, self.start_date).grid(row=0, column=2, sticky="w", padx=(8, 16))

        ttk.Label(row, text="End Date:", style="Card.TLabel").grid(row=0, column=3, sticky="w", padx=(0, 6))
        self.end_date = ttk.Entry(row, width=16); self.end_date.grid(row=0, column=4, sticky="w")
        self._calendar_button(row, self.end_date).grid(row=0, column=5, sticky="w", padx=(8, 16))

        ttk.Label(row, text="Shift:", style="Card.TLabel").grid(row=0, column=6, sticky="w", padx=(0, 6))
        self.shift_var = tk.StringVar(value="All")
        self.shift_combo = ttk.Combobox(row, textvariable=self.shift_var, state="readonly",
                                        values=["All", "A", "B", "C"], width=16)
        self.shift_combo.grid(row=0, column=7, sticky="w", padx=(0, 16))

        ttk.Label(row, text="Operator:", style="Card.TLabel").grid(row=0, column=8, sticky="w", padx=(0, 6))
        self.operator_entry = ttk.Entry(row, width=20); self.operator_entry.grid(row=0, column=9, sticky="w", padx=(0, 16))

        ttk.Label(row, text="Reason:", style="Card.TLabel").grid(row=0, column=10, sticky="w", padx=(0, 6))
        self.reason_entry = ttk.Entry(row, width=22); self.reason_entry.grid(row=0, column=11, sticky="w")

        btns = tk.Frame(filt, bg=CARD_BG); btns.pack(fill="x", padx=16, pady=(8, 12))
        preview_icon = load_icon(ICON_PREVIEW, (18, 18))
        export_icon  = load_icon(ICON_EXPORT, (18, 18))

        self.preview_btn = ttk.Button(btns, text="  Preview Data", style="Neutral.TButton", command=self.on_preview)
        if preview_icon: self.preview_btn.config(image=preview_icon, compound="left"); self._icon_preview = preview_icon
        self.preview_btn.pack(side="left")

        self.export_btn = ttk.Button(btns, text="  Generate Report", style="Primary.TButton", command=self.on_export)
        if export_icon: self.export_btn.config(image=export_icon, compound="left"); self._icon_export = export_icon
        self.export_btn.pack(side="left", padx=(10, 0))

        # KPIs
        kpi_wrap = tk.Frame(self, bg=APP_BG); kpi_wrap.pack(fill="x", padx=24)
        self.kpi_vars = {
            "total": tk.StringVar(value="0.00"),
            "entries": tk.StringVar(value="0"),
            "avg": tk.StringVar(value="0.00"),
            "top": tk.StringVar(value="—"),
            "rate": tk.StringVar(value="—"),
        }
        self._build_kpi_card(kpi_wrap, "Total Scrap", self.kpi_vars["total"], ICON_KPI_TOTAL).pack(side="left", padx=(0, 12))
        self._build_kpi_card(kpi_wrap, "Entries", self.kpi_vars["entries"], ICON_KPI_ENTRIES).pack(side="left", padx=(0, 12))
        self._build_kpi_card(kpi_wrap, "Avg/Day", self.kpi_vars["avg"], ICON_KPI_AVGDAY).pack(side="left", padx=(0, 12))
        self._build_kpi_card(kpi_wrap, "Top Reason", self.kpi_vars["top"], ICON_KPI_TOPREASON).pack(side="left", padx=(0, 12))
        self._build_kpi_card(kpi_wrap, "Scrap Rate", self.kpi_vars["rate"]).pack(side="left", padx=(0, 12))

        # Table
        table_wrap = tk.Frame(self, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER_COLOR)
        table_wrap.pack(fill="both", expand=True, padx=24, pady=12)

        base_cols = ["date","shift","machine_operator","machine_name","reason","quantity","unit"]
        self.tree = ttk.Treeview(table_wrap, columns=base_cols, show="headings")
        headings = {
            "date":"Date","shift":"Shift","machine_operator":"Machine Operator",
            "machine_name":"Machine Name","reason":"Reason","quantity":"Quantity","unit":"Unit",
        }
        widths = {"date":110,"shift":90,"machine_operator":150,"machine_name":130,"reason":140,"quantity":90,"unit":70}
        for c in base_cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.tag_configure("odd", background=ROW_A)
        self.tree.tag_configure("even", background=ROW_B)

        # Defaults: last 7 days
        today = date.today()
        start_default = today - timedelta(days=6)
        self.start_date.insert(0, start_default.strftime("%Y-%m-%d"))
        self.end_date.insert(0, today.strftime("%Y-%m-%d"))

    def _build_kpi_card(self, parent, label, var, icon_name=None):
        card = ttk.Frame(parent, style="Card.TFrame")
        card["padding"] = (12, 10, 12, 10)
        card_inner = tk.Frame(card, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card_inner.pack(fill="both", expand=True)
        inner = tk.Frame(card_inner, bg=CARD_BG); inner.pack(fill="x", expand=True, padx=10, pady=8)
        ic = load_icon(icon_name, (20, 20)) if icon_name else None
        if ic:
            tk.Label(inner, image=ic, bg=CARD_BG).pack(side="left", padx=(0, 8)); setattr(self, f"_kpi_{label}_icon", ic)
        ttk.Label(inner, text=label, style="Card.TLabel").pack(side="left")
        ttk.Label(card_inner, textvariable=var, style="CardValue.TLabel").pack(anchor="w", padx=10, pady=(4, 4))
        return card

    def _parse_date_str(self, s: str) -> date:
        s = s.strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        raise ValueError("Invalid date")

    def _get_filters(self):
        try:
            start = self._parse_date_str(self.start_date.get())
            end = self._parse_date_str(self.end_date.get())
        except Exception:
            messagebox.showerror("Invalid Date", "Dates must be in YYYY-MM-DD or MM/DD/YYYY format.")
            return None
        if start > end:
            messagebox.showerror("Invalid Range", "Start date must be before or equal to end date.")
            return None
        shift = self.shift_var.get()
        operator = self.operator_entry.get().strip() or None
        reason = self.reason_entry.get().strip() or None
        return {"start": start, "end": end, "shift": shift, "operator": operator, "reason": reason}

    def on_preview(self):
        flt = self._get_filters()
        if not flt: return
        df = load_scrap_data(flt["start"], flt["end"], flt["shift"], flt["operator"], flt["reason"])
        self.current_df = df
        self._populate_table(df)
        k = compute_kpis(df)
        self.kpi_vars["total"].set(f"{k['total_scrap']:.2f}")
        self.kpi_vars["entries"].set(str(k["entries"]))
        self.kpi_vars["avg"].set(f"{k['avg_per_day']:.2f}")
        self.kpi_vars["top"].set(k["top_reason"])
        self.kpi_vars["rate"].set(f"{k['scrap_rate']:.2f}%" if k['scrap_rate'] is not None else "—")
        if df.empty:
            messagebox.showinfo("No Data", "No scrap logs found for the selected filters.")

    def _populate_table(self, df: pd.DataFrame):
        for r in self.tree.get_children(): self.tree.delete(r)
        if df.empty: return
        for i, row in df.iterrows():
            values = [str(row.get("date","")), str(row.get("shift","")), str(row.get("machine_operator","")),
                      str(row.get("machine_name","")), str(row.get("reason","")),
                      f"{float(row.get('quantity',0) or 0):.2f}", str(row.get("unit",""))]
            tag = "even" if (i % 2) else "odd"
            self.tree.insert("", "end", values=values, tags=(tag,))

    def on_export(self):
        if self.current_df is None or self.current_df.empty:
            messagebox.showwarning("No Data", "Preview data first (or no rows matched your filters).")
            return
        # Offer PDF or HTML filename; default to PDF if tool exists
        wkhtml = (os.getenv("WKHTMLTOPDF_PATH") or shutil.which("wkhtmltopdf"))
        default_name = DEFAULT_PDF_NAME if (pdfkit and wkhtml) else DEFAULT_HTML_NAME

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf" if (pdfkit and wkhtml) else ".html",
            filetypes=[("PDF files","*.pdf"), ("HTML files","*.html")],
            initialfile=default_name,
            title="Save Report"
        )
        if not path:
            return

        flt = self._get_filters()
        if not flt: return

        try:
            html_path, pdf_path = generate_report(
                df=self.current_df,
                start_date=flt["start"],
                end_date=flt["end"],
                save_path=path,
                filters={"shift": flt["shift"], "operator": flt["operator"], "reason": flt["reason"]}
            )
            if pdf_path:
                messagebox.showinfo("Success", f"PDF saved to:\n{pdf_path}")
            else:
                messagebox.showinfo("Saved", f"Report saved to:\n{html_path}\n\nOpening in your browser…")
                webbrowser.open_new_tab(Path(html_path).resolve().as_uri())
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not generate report.\n\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("ScrapSense - Generate Report")
    root.configure(bg=APP_BG)
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{int(sw*0.8)}x{int(sh*0.8)}+50+50")
    app = GenerateReportFrame(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
