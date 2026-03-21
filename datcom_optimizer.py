"""
DATCOM Wing Optimization GUI
- Parameters parsed from for005.dat automatically
- Original dat file is NEVER modified during iteration (temp copy used)
- Custom drawn checkboxes (visible on dark themes)
- Before/After parameter comparison in Results tab
- Aero Sweep tab: runs full alpha sweep on baseline & optimized, plots CL/CD/CM/L/D
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess, math, os, shutil, threading, datetime, tempfile, time, re
from time import sleep
try:
    import myfuncs
except ImportError:
    myfuncs = None

# matplotlib embedding (imported lazily inside the tab to avoid startup cost)
try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _MPL_OK = True
except ImportError:
    _MPL_OK = False

# ── Palette ─────────────────────────────────────────────────────────
BG_DARK  = "#0d1117"
BG_PANEL = "#161b22"
BG_CARD  = "#1c2128"
BG_INPUT = "#21262d"
ACCENT   = "#2ea043"
ACCENT2  = "#388bfd"
ACCENT3  = "#ffb86b"
TEXT_PRI = "#f5f7fa"
TEXT_SEC = "#c9d1d9"
TEXT_DIM = "#9aa4b2"
BORDER   = "#30363d"
RED      = "#f85149"
YELLOW   = "#d29922"

# ── Parameter definitions (idx 0 = ALSCHD excluded from opt) ────────
PARAM_DEFS = [
    ( 1,"Wing - SAVSI  (inner sweep)","deg", 1000,"Wing"),
    ( 2,"Wing - SAVSO  (outer sweep)","deg", 1000,"Wing"),
    ( 3,"Wing - SSPN   (span)",       "m",   100, "Wing"),
    ( 4,"Wing - SSPNOP (bp span)",    "m",   100, "Wing"),
    ( 5,"Wing - DHDADI (inner dihed.)","deg", 100,"Wing"),
    ( 6,"Wing - DHDADO (outer dihed.)","deg", 100,"Wing"),
    ( 7,"Wing - TWISTA (twist)",      "deg", 100, "Wing"),
    ( 8,"Wing - CHRDR  (root chord)", "m",   100, "Wing"),
    ( 9,"Wing - CHRDBP (bp chord)",   "m",   100, "Wing"),
    (10,"Wing - CHRDTP (tip chord)",  "m",   100, "Wing"),
    (11,"V-Tail - SAVSI  (inner sw.)","deg", 1000,"Vertical Tail"),
    (12,"V-Tail - SAVSO  (outer sw.)","deg", 1000,"Vertical Tail"),
    (13,"V-Tail - SSPN   (span)",     "m",   100, "Vertical Tail"),
    (14,"V-Tail - SSPNOP (bp span)",  "m",   100, "Vertical Tail"),
    (15,"V-Tail - DHDADI (inner)",    "deg", 100, "Vertical Tail"),
    (16,"V-Tail - DHDADO (outer)",    "deg", 100, "Vertical Tail"),
    (17,"V-Tail - TWISTA (twist)",    "deg", 100, "Vertical Tail"),
    (18,"V-Tail - CHRDR  (root)",     "m",   100, "Vertical Tail"),
    (19,"V-Tail - CHRDBP (bp)",       "m",   100, "Vertical Tail"),
    (20,"V-Tail - CHRDTP (tip)",      "m",   100, "Vertical Tail"),
    (21,"H-Tail - SAVSI  (inner sw.)","deg", 1000,"Horizontal Tail"),
    (22,"H-Tail - SAVSO  (outer sw.)","deg", 1000,"Horizontal Tail"),
    (23,"H-Tail - SSPN   (span)",     "m",   100, "Horizontal Tail"),
    (24,"H-Tail - SSPNOP (bp span)",  "m",   100, "Horizontal Tail"),
    (25,"H-Tail - DHDADI (inner)",    "deg", 100, "Horizontal Tail"),
    (26,"H-Tail - DHDADO (outer)",    "deg", 100, "Horizontal Tail"),
    (27,"H-Tail - TWISTA (twist)",    "deg", 100, "Horizontal Tail"),
    (28,"H-Tail - CHRDR  (root)",     "m",   100, "Horizontal Tail"),
    (29,"H-Tail - CHRDBP (bp)",       "m",   100, "Horizontal Tail"),
    (30,"H-Tail - CHRDTP (tip)",      "m",   100, "Horizontal Tail"),
]

DEFAULT_BOUNDS = {
     1:(0.03,0.05),   2:(0.03,0.05),   3:(0.040,0.055),  4:(0.032,0.033),
     5:(0.0, 0.06),   6:(0.0, 0.05),   7:(-0.04,0.03),   8:(0.046,0.051),
     9:(0.01,0.02),  10:(0.01,0.02),  11:(0.055,0.055), 12:(0.03,0.058),
    13:(0.03,0.04),  14:(0.017,0.018),15:(0.0,0.001),   16:(0.0,0.001),
    17:(-0.04,0.04), 18:(0.03,0.04),  19:(0.01,0.02),   20:(0.01,0.02),
    21:(0.03,0.05),  22:(0.03,0.05),  23:(0.025,0.032), 24:(0.0176,0.0178),
    25:(-0.04,0.0),  26:(-0.04,0.0),  27:(-0.02,0.02),  28:(0.03,0.04),
    29:(0.008,0.015),30:(0.008,0.015),
}


# ── Custom Checkbox widget ────────────────────────────────────────────
class CheckBox(tk.Canvas):
    """Fully custom-drawn checkbox. Works on any dark/light theme."""
    SZ = 17

    def __init__(self, parent, variable, bg=BG_CARD, **kw):
        super().__init__(parent, width=self.SZ, height=self.SZ,
                         bg=bg, highlightthickness=0, cursor="hand2", **kw)
        self._var = variable
        self._draw()
        self._var.trace_add("write", lambda *_: self._draw())
        self.bind("<Button-1>", lambda _: self._var.set(not self._var.get()))

    def _draw(self):
        self.delete("all")
        n = self.SZ
        # Box
        self.create_rectangle(1, 1, n-2, n-2,
                               outline="#5a7a9a", fill="#1e2d3d", width=1)
        if self._var.get():
            # Bold cyan tick
            p = 3
            self.create_line(p, n//2, n//2-1, n-p-1,
                              fill="#38d8f0", width=2, capstyle="round")
            self.create_line(n//2-1, n-p-1, n-p, p,
                              fill="#38d8f0", width=2, capstyle="round")


# ── DATCOM file parser ────────────────────────────────────────────────
def parse_for005(filepath):
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        words = [l.split() for l in lines]

        def find_scalar(kw):
            for row in words:
                for w in row:
                    if w[:len(kw)] == kw and '=' in w:
                        s = w[w.index('=')+1:].rstrip(',$')
                        try: return float(s)
                        except: pass
            return None

        lists = {k:[] for k in ['savsi','savso','sspn','sspnop','dhdadi',
                                  'dhdado','twista','chrdr','chrdbp','chrdtp']}
        kw_map = {'SAVSI':'savsi','SAVSO':'savso','SSPN=':'sspn','SSPNOP':'sspnop',
                  'DHDADI':'dhdadi','DHDADO':'dhdado','TWISTA':'twista',
                  'CHRDR':'chrdr','CHRDBP':'chrdbp','CHRDTP':'chrdtp'}
        for row in words:
            for w in row:
                for kw, var in kw_map.items():
                    if w[:len(kw)] == kw and '=' in w:
                        s = w[w.index('=')+1:].rstrip(',$')
                        try: lists[var].append(float(s))
                        except: pass

        def gl(lst, i, d=0.0): return (lst[i]/1000.0) if i < len(lst) else d
        def gm(lst, i, d=0.0): return (lst[i]/100.0)  if i < len(lst) else d

        alschd = find_scalar('ALSCHD(1)') or find_scalar('ALSCHD') or 5.0
        zv     = find_scalar('ZV') or 0.017
        wt     = find_scalar('WT') or 26500.0
        zh_raw = find_scalar('ZH') or 0.366
        s = lists

        inp = [None]*32
        inp[0]  = alschd/10.0
        inp[1]  = gl(s['savsi'], 0, 0.040);    inp[2]  = gl(s['savso'], 0, 0.040)
        inp[3]  = gm(s['sspn'],  0, 0.04572);  inp[4]  = gm(s['sspnop'],0, 0.032258)
        inp[5]  = gm(s['dhdadi'],0, 0.0);      inp[6]  = gm(s['dhdado'],0, 0.0)
        inp[7]  = gm(s['twista'],0,-0.0328);   inp[8]  = gm(s['chrdr'], 0, 0.04965)
        inp[9]  = gm(s['chrdbp'],0, 0.0129);   inp[10] = gm(s['chrdtp'],0, 0.0129)
        inp[11] = gl(s['savsi'], 1, 0.0475);   inp[12] = gl(s['savso'], 1, 0.0475)
        inp[13] = gm(s['sspn'],  1, 0.031968); inp[14] = gm(s['sspnop'],1, 0.02568)
        inp[15] = gm(s['dhdadi'],1, 0.0);      inp[16] = gm(s['dhdado'],1, 0.0)
        inp[17] = gm(s['twista'],1, 0.0);      inp[18] = gm(s['chrdr'], 1, 0.03088)
        inp[19] = gm(s['chrdbp'],1, 0.01200);  inp[20] = gm(s['chrdtp'],1, 0.01206)
        inp[21] = gl(s['savsi'], 2, 0.040);    inp[22] = gl(s['savso'], 2, 0.040)
        inp[23] = gm(s['sspn'],  2, 0.02808);  inp[24] = gm(s['sspnop'],2, 0.017686)
        inp[25] = gm(s['dhdadi'],2,-0.01);     inp[26] = gm(s['dhdado'],2,-0.01)
        inp[27] = gm(s['twista'],2, 0.0);      inp[28] = gm(s['chrdr'], 2, 0.03328)
        inp[29] = gm(s['chrdbp'],2, 0.009497); inp[30] = gm(s['chrdtp'],2, 0.009497)
        inp[31] = zh_raw/100.0

        return inp, zv, wt, True, ""
    except Exception as e:
        import traceback
        return [], 0.017, 26500.0, False, traceback.format_exc()


# ── Write inp vector to a dat file ───────────────────────────────────
def write_inp_to_dat(inp, dat_path, fixed_zv, zv_orig):
    with open(dat_path, 'r') as f:
        lines = f.readlines()
    words = [l.split() for l in lines]

    kw_map = {
        'SAVSI': [inp[1]*1000, inp[11]*1000, inp[21]*1000],
        'SAVSO': [inp[2]*1000, inp[12]*1000, inp[22]*1000],
        'SSPN=': [inp[3]*100,  inp[13]*100,  inp[23]*100],
        'SSPNOP':[inp[4]*100,  inp[14]*100,  inp[24]*100],
        'DHDADI':[inp[5]*100,  inp[15]*100,  inp[25]*100],
        'DHDADO':[inp[6]*100,  inp[16]*100,  inp[26]*100],
        'TWISTA':[inp[7]*100,  inp[17]*100,  inp[27]*100],
        'CHRDR': [inp[8]*100,  inp[18]*100,  inp[28]*100],
        'CHRDBP':[inp[9]*100,  inp[19]*100,  inp[29]*100],
        'CHRDTP':[inp[10]*100, inp[20]*100,  inp[30]*100],
    }
    counters = {k:0 for k in kw_map}

    for r, row in enumerate(words):
        for c, w in enumerate(row):
            for kw, vals in kw_map.items():
                if w[:len(kw)] == kw and '=' in w:
                    n = counters[kw]
                    if n < len(vals):
                        idx2 = w.index('=')+1
                        words[r][c] = w[:idx2] + f"{vals[n]:.5f},"
                        lines[r] = " " + ' '.join(words[r]) + '\n'
                        counters[kw] = n+1
            if not fixed_zv:
                if w[:2] == 'ZH' and '=' in w:
                    idx2 = w.index('=')+1
                    words[r][c] = w[:idx2] + f"{inp[31]*100:.5f},$"
                    lines[r] = " " + ' '.join(words[r]) + '\n'

    with open(dat_path, 'w') as f:
        f.writelines(lines)


# ── Read datcom.out ───────────────────────────────────────────────────
def read_datcom_out(out_path):
    with open(out_path, 'r') as f:
        lines = f.readlines()
    words = [l.split() for l in lines]
    wing_area = CL = CD = CM = 1.0
    velocity = pressure = temperature = 288.15
    for i, row in enumerate(words):
        for j, w in enumerate(row):
            if w[:11] == "THEORITICAL":
                try: wing_area = float(words[i+1][j])
                except: pass
            if w == "CL":
                try: CL = float(words[i+2][j-1])*10/wing_area
                except: pass
            if w == "CD":
                try: CD = float(words[i+2][j-1])*10/wing_area
                except: pass
            if w == "CM":
                try: CM = float(words[i+2][j-1])*1000/wing_area
                except: pass
            if w[:8] == "VELOCITY":
                try:
                    velocity    = float(words[i+3][j+1])
                    pressure    = float(words[i+3][j+2])
                    temperature = float(words[i+3][j+3])
                except: pass
    density = pressure/(287.058*temperature)
    return CL, CD, CM, wing_area, velocity, density



# ── Alpha-sweep DATCOM output parser ─────────────────────────────────
# Reads ALL alpha cases from a datcom.out produced with NALPHA=15.
# Returns a list of dicts: [{'alpha':..,'CL':..,'CD':..,'CM':..}, ...]
# The file has one block per alpha; we collect every CL/CD/CM row and
# pair it with the corresponding ALSCHD value found in the for005.dat.

def parse_sweep_out(out_path, alpha_list):
    """
    Parse a datcom.out produced with NALPHA>1.
    Finds the single table with header:
      "0 ALPHA  CD  CL  CM  CN  CA  XCP ..."
    and reads all data rows: col0=alpha, col1=CD, col2=CL, col3=CM.
    Other alpha-containing tables (EPSLON, CLQ/CMQ, etc.) are ignored.
    Returns (results, velocity, pressure, temperature) where
    results = [{'alpha':..,'CL':..,'CD':..,'CM':..}, ...]
    """
    results = []
    velocity = pressure = temperature = 288.15

    with open(out_path, 'r', errors='replace') as f:
        lines = f.readlines()

    in_table = False
    for i, line in enumerate(lines):
        sline = line.strip()

        # ── Detect the correct header: must have ALPHA, CD, CL, CM
        #    but NOT the other alpha-tables (EPSLON, QINF, CLQ, CMQ …)
        if (re.search(r'\bALPHA\b', sline) and
                re.search(r'\bCD\b', sline) and
                re.search(r'\bCL\b', sline) and
                re.search(r'\bCM\b', sline) and
                not re.search(r'\bEPSLON\b|\bQINF\b|\bCLQ\b|\bCMQ\b', sline)):
            in_table = True
            continue

        if not in_table:
            # Capture velocity / pressure / temperature (first occurrence)
            if re.search(r'\bVELOCITY\b', line, re.IGNORECASE) and velocity == 288.15:
                try:
                    tok = lines[i+3].split()
                    s = 1 if tok[0] == '0' else 0
                    velocity    = float(tok[s+2])
                    pressure    = float(tok[s+3])
                    temperature = float(tok[s+4])
                except (ValueError, IndexError):
                    pass
            continue

        # ── Inside the table ─────────────────────────────────────────
        if not sline or sline == '0':
            continue   # blank / section marker

        tokens = sline.split()
        try:
            alpha = float(tokens[0])
            CD    = float(tokens[1])
            CL    = float(tokens[2])
            CM    = float(tokens[3])
            results.append({'alpha': alpha, 'CL': CL, 'CD': CD, 'CM': CM})
        except (ValueError, IndexError):
            in_table = False  # non-numeric row ends the table

    density = pressure / (287.058 * temperature)
    return results, velocity, pressure, temperature


def patch_dat_for_sweep(src_dat, dst_dat, nalpha, alschd_list):
    """
    Copy src_dat -> dst_dat, then replace NALPHA and ALSCHD lines
    so that a full alpha sweep is performed.
    alschd_list : list of floats, e.g. [-10,-8,...,18]

    Produces:
        NALPHA=15.0,
        ALSCHD(1)=-10.0, -8.0, -6.0, -4.0, -2.0, 0.0, 2.0, 4.0,
        6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0,
    Handles ALSCHD inline, own line, old ALSCHD(9) format, and
    bare-numeric continuation lines — without touching other sections
    like $BODY X(1)/ZU(1) continuations.
    """
    shutil.copy2(src_dat, dst_dat)
    with open(dst_dat, "r") as f:
        content = f.read()

    # ── Replace NALPHA ────────────────────────────────────────────────
    content = re.sub(r"NALPHA\s*=\s*[\d.]+", f"NALPHA={float(nalpha):.1f}",
                     content, flags=re.IGNORECASE)

    # ── Remove ALSCHD lines + their bare-numeric continuations ────────
    # Work line-by-line so we never touch other sections' continuations
    # (e.g. $BODY X(1)=... continuation lines look identical but must survive).
    # Rule: strip the ALSCHD token from any line it appears on; then drop the
    # immediately following line(s) only if they are bare-numeric — those are
    # old continuation lines that belong to the removed ALSCHD block.
    lines = content.split("\n")
    out = []
    skip_next_if_bare = False
    for line in lines:
        if re.search(r"ALSCHD\s*(\(\s*\d+\s*\))?\s*=", line, re.IGNORECASE):
            # Strip the ALSCHD token (values) but keep rest of line (other keywords)
            cleaned = re.sub(
                r"ALSCHD\s*(\(\s*\d+\s*\))?\s*=\s*[0-9 ,.\-]+,?",
                "", line, flags=re.IGNORECASE).rstrip()
            out.append(cleaned if cleaned.strip().strip(",").strip() else "")
            skip_next_if_bare = True
            continue
        if skip_next_if_bare:
            stripped = line.strip().rstrip(",").strip()
            if re.match(r"^[\d .,\-]+$", stripped):
                skip_next_if_bare = True   # chain: keep dropping multi-line blocks
                continue
            skip_next_if_bare = False
        out.append(line)
    content = "\n".join(out)

    # ── Build new two-line ALSCHD block ───────────────────────────────
    MAX_FIRST = 8
    vals1 = alschd_list[:MAX_FIRST]
    vals2 = alschd_list[MAX_FIRST:]
    line1 = " ALSCHD(1)=" + ", ".join(f"{a:.1f}" for a in vals1) + ","
    if vals2:
        line2 = " " + ", ".join(f"{a:.1f}" for a in vals2) + ","
        alschd_block = line1 + "\n" + line2
    else:
        alschd_block = line1

    # ── Insert after NALPHA=N ─────────────────────────────────────────
    content = re.sub(
        r"(NALPHA\s*=\s*\d+\.?\d*),?",
        r"\1,\n" + alschd_block,
        content, flags=re.IGNORECASE)

    content = re.sub(r"\n{3,}", "\n\n", content)

    with open(dst_dat, "w") as f:
        f.write(content)


class DatcomApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DATCOM Wing Optimization Tool")
        self.configure(bg=BG_DARK)
        self.geometry("1340x920")
        self.minsize(1100, 740)

        self.dat_file         = tk.StringVar(value="")
        self.datcom_exe       = tk.StringVar(value="")
        self.cost_expr        = tk.StringVar(value="")
        self.inp_vals         = []
        self.zv_val           = 0.017
        self.wt_val           = 26500.0
        self._running         = False
        self._iter_count      = 0
        self._best_score      = float('inf')
        self._initial_inp     = []
        self._final_inp       = []   # set after optimization

        # Aero Sweep tab state
        self._sweep_running   = False
        self._sweep_data_base = None   # list of (alpha, CD, CL, CM) for baseline
        self._sweep_data_opt  = None   # list of (alpha, CD, CL, CM) for optimized

        self.param_enabled = {idx: tk.BooleanVar(value=True) for idx,*_ in PARAM_DEFS}
        self.param_lo      = {idx: tk.StringVar() for idx,*_ in PARAM_DEFS}
        self.param_hi      = {idx: tk.StringVar() for idx,*_ in PARAM_DEFS}
        self.param_cur     = {idx: tk.StringVar(value="-") for idx,*_ in PARAM_DEFS}

        self.FH1    = ("Consolas",12,"bold")
        self.FBODY  = ("Consolas",9)
        self.FSMALL = ("Consolas",8)

        self._build_ui()

    # ── UI skeleton ───────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_DARK, height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="DATCOM OPTIMIZATION TOOL", bg=BG_DARK,
                 fg=ACCENT, font=self.FH1).pack(side="left", padx=20, pady=10)
        tk.Label(hdr, text="Digital DATCOM  |  Wing / Tail Surface Geometry Optimizer",
                 bg=BG_DARK, fg=TEXT_SEC, font=self.FSMALL).pack(side="left")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        s = ttk.Style(); s.theme_use('default')
        s.configure("TNotebook",     background=BG_DARK, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG_PANEL, foreground=TEXT_SEC,
                    padding=[14,8],  font=("Consolas",9,"bold"))
        s.map("TNotebook.Tab",
              background=[("selected",BG_CARD)],
              foreground=[("selected",TEXT_PRI)])
        s.configure("opt.Horizontal.TProgressbar",
                    troughcolor=BG_PANEL, background=ACCENT)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        tabs = [tk.Frame(nb, bg=BG_CARD) for _ in range(7)]
        for t, lbl in zip(tabs, ["   Input File   ","   Parameters   ",
                                   "   Cost Function   ","   Run   ","   Results   ",
                                   "   Aircraft View   ","   Aero Sweep   "]):
            nb.add(t, text=lbl)

        self._tab_input(tabs[0])
        self._tab_params(tabs[1])
        self._tab_cost(tabs[2])
        self._tab_run(tabs[3])
        self._tab_results(tabs[4])
        self._tab_view(tabs[5])
        self._tab_sweep(tabs[6])

    # ── Tab 1: Input ──────────────────────────────────────────────────
    def _tab_input(self, p):
        self._sec(p,"Input File (for005.dat)").pack(fill="x", padx=20, pady=(18,4))
        row = tk.Frame(p, bg=BG_CARD); row.pack(fill="x", padx=20)
        tk.Entry(row, textvariable=self.dat_file, bg=BG_INPUT, fg=TEXT_PRI,
                 insertbackground=TEXT_PRI, relief="flat",
                 font=self.FBODY, width=60).pack(
                     side="left", fill="x", expand=True, ipady=6, padx=(0,8))
        self._btn(row,"Browse...",    self._browse, ACCENT2).pack(side="left")
        self._btn(row,"Load & Parse", self._load,   ACCENT ).pack(side="left", padx=(8,0))

        self._sec(p,"Digital DATCOM EXE").pack(fill="x", padx=20, pady=(12,4))
        row_exe = tk.Frame(p, bg=BG_CARD); row_exe.pack(fill="x", padx=20)
        tk.Entry(row_exe, textvariable=self.datcom_exe, bg=BG_INPUT, fg=TEXT_PRI,
                 insertbackground=TEXT_PRI, relief="flat",
                 font=self.FBODY, width=60).pack(
                     side="left", fill="x", expand=True, ipady=6, padx=(0,8))
        self._btn(row_exe,"Browse EXE...", self._browse_exe, ACCENT2).pack(side="left")

        ac = self._card(p); ac.pack(fill="x", padx=20, pady=(0,12))
        tk.Label(ac, text="ALSCHD  --  Angle of Attack  (read-only, fixed during optimization)",
                 bg=BG_PANEL, fg=TEXT_SEC, font=("Consolas",9,"bold")).pack(anchor="w")
        self.alschd_label = tk.Label(ac, text="ALSCHD = -  deg",
                                      bg=BG_PANEL, fg=ACCENT3, font=self.FBODY)
        self.alschd_label.pack(anchor="w", pady=(4,0))

        self._sec(p,"File Preview").pack(fill="x", padx=20, pady=(4,3))
        self.preview = scrolledtext.ScrolledText(
            p, height=14, bg=BG_INPUT, fg=TEXT_SEC, font=("Consolas",8),
            relief="flat", insertbackground=TEXT_PRI)
        self.preview.pack(fill="both", expand=True, padx=20, pady=(0,16))

    # ── Tab 2: Parameters ─────────────────────────────────────────────
    def _tab_params(self, p):
        bar = tk.Frame(p, bg=BG_CARD); bar.pack(fill="x", padx=20, pady=(10,4))
        tk.Label(bar, text="Select parameters to optimize and set their search bounds.",
                 bg=BG_CARD, fg=TEXT_SEC, font=self.FSMALL).pack(side="left")
        self._btn(bar,"Select All",   lambda: self._tog_all(True),  ACCENT2).pack(side="right", padx=4)
        self._btn(bar,"Deselect All", lambda: self._tog_all(False), RED   ).pack(side="right")

        outer = tk.Frame(p, bg=BG_CARD)
        outer.pack(fill="both", expand=True, padx=20, pady=(0,12))
        canvas = tk.Canvas(outer, bg=BG_CARD, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._pi = tk.Frame(canvas, bg=BG_CARD)
        self._pw = canvas.create_window((0,0), window=self._pi, anchor="nw")
        self._pi.bind("<Configure>",
                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(self._pw, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))
        self._build_param_rows()

    def _build_param_rows(self):
        f = self._pi
        for w in f.winfo_children(): w.destroy()

        hdr = tk.Frame(f, bg=BG_PANEL); hdr.pack(fill="x", pady=(0,1))
        for txt, wid in [(" ",3),("Parameter",34),("Current Value",16),
                          ("Lower Bound",13),("Upper Bound",13),("Unit",6)]:
            tk.Label(hdr, text=txt, bg=BG_PANEL, fg=TEXT_SEC,
                     font=self.FSMALL, width=wid, anchor="w").pack(
                         side="left", padx=3, pady=5)

        cur_sec = None
        for (idx, label, unit, scale, section) in PARAM_DEFS:
            if section != cur_sec:
                cur_sec = section
                sr = tk.Frame(f, bg=BG_DARK); sr.pack(fill="x", pady=(7,1))
                tk.Label(sr, text=f"  {section}",
                         bg=BG_DARK, fg=ACCENT, font=("Consolas",8,"bold")).pack(
                             side="left", padx=6, pady=2)

            bg = BG_CARD if idx%2==0 else BG_PANEL
            row = tk.Frame(f, bg=bg); row.pack(fill="x", pady=1)

            CheckBox(row, self.param_enabled[idx], bg=bg).pack(
                side="left", padx=(10, 4), pady=4)

            tk.Label(row, text=label, bg=bg, fg=TEXT_PRI,
                     font=self.FBODY, width=34, anchor="w").pack(side="left", padx=4)
            tk.Label(row, textvariable=self.param_cur[idx], bg=bg, fg=ACCENT3,
                     font=self.FBODY, width=16, anchor="w").pack(side="left", padx=4)
            for var in [self.param_lo[idx], self.param_hi[idx]]:
                tk.Entry(row, textvariable=var, bg=BG_INPUT, fg=TEXT_PRI,
                         insertbackground=TEXT_PRI, relief="flat",
                         font=self.FBODY, width=13).pack(side="left", padx=4, ipady=4)
            tk.Label(row, text=unit, bg=bg, fg=TEXT_DIM,
                     font=self.FSMALL, width=6).pack(side="left")

    # ── Tab 3: Cost Function ──────────────────────────────────────────
    def _tab_cost(self, p):
        self._sec(p,"Cost Function").pack(fill="x", padx=20, pady=(18,6))

        info = self._card(p); info.pack(fill="x", padx=20, pady=4)
        tk.Label(info, text="Enter a custom objective or choose a generic preset below.",
                 bg=BG_PANEL, fg=TEXT_PRI, font=("Consolas",10,"bold")).pack(anchor="w")
        tk.Label(info, text="The optimizer minimizes the expression. Use negative sign for maximize-type targets.",
                 bg=BG_PANEL, fg=TEXT_SEC, font=self.FSMALL).pack(anchor="w", pady=(4,0))

        self._sec(p,"Custom Expression").pack(fill="x", padx=20, pady=(16,4))
        ic = self._card(p); ic.pack(fill="x", padx=20, pady=4)
        tk.Label(ic, text="Available:  CL   CD   CM   rCL   wing_area   abs(...) ",
                 bg=BG_PANEL, fg=TEXT_PRI, font=self.FSMALL).pack(anchor="w")
        tk.Label(ic, text="Examples:  -CL   |   -(CL/CD)   |   CD + 0.1*abs(CM)",
                 bg=BG_PANEL, fg=TEXT_SEC, font=self.FSMALL).pack(anchor="w", pady=(2,0))

        self.cost_entry = tk.Entry(p, textvariable=self.cost_expr,
                                   bg=BG_INPUT, fg=TEXT_PRI,
                                   insertbackground=TEXT_PRI, relief="flat",
                                   font=("Consolas",11))
        self.cost_entry.pack(fill="x", padx=20, pady=6, ipady=9)

        self._sec(p,"Preset Templates").pack(fill="x", padx=20, pady=(14,4))
        tf = tk.Frame(p, bg=BG_CARD); tf.pack(fill="x", padx=20)
        for name, expr in [
            ("Maximize Lift",      "-CL"),
            ("Maximize L/D",       "-(CL/CD)"),
            ("Minimize Drag",      "CD"),
            ("Minimize Moment",    "abs(CM)"),
            ("Lift + Drag Tradeoff","-CL + 3*CD"),
            ("L/D + Trim Tradeoff", "-(CL/CD) + 0.1*abs(CM)"),
        ]:
            tk.Button(tf, text=name, command=lambda e=expr: self._set_tpl(e),
                      bg=BG_PANEL, fg=TEXT_PRI, relief="flat", font=self.FSMALL,
                      cursor="hand2", activebackground=BG_INPUT,
                      activeforeground=TEXT_PRI,
                      padx=12, pady=6).pack(side="left", padx=4, pady=4)

    def _set_tpl(self, expr):
        self.cost_expr.set(expr)

    # ── Tab 4: Run ────────────────────────────────────────────────────
    def _tab_run(self, p):
        ctrl = tk.Frame(p, bg=BG_CARD); ctrl.pack(fill="x", padx=20, pady=14)
        self.run_btn = self._btn(ctrl,">> START OPTIMIZATION",
                                  self._start, ACCENT, big=True)
        self.run_btn.pack(side="left")
        self._btn(ctrl,"[X] Stop",  self._stop,      RED   ).pack(side="left", padx=10)
        self._btn(ctrl,"Clear Log", self._clear_log, BG_PANEL).pack(side="right")

        pg = tk.Frame(p, bg=BG_CARD); pg.pack(fill="x", padx=20, pady=(0,6))
        self.status_lbl = tk.Label(pg, text="Ready", bg=BG_CARD,
                                    fg=TEXT_SEC, font=self.FSMALL)
        self.status_lbl.pack(side="left")
        self.prog = ttk.Progressbar(pg, mode="indeterminate", length=320,
                                    style="opt.Horizontal.TProgressbar")
        self.prog.pack(side="left", padx=12)
        self.iter_lbl = tk.Label(pg, text="Iter: -", bg=BG_CARD,
                                  fg=TEXT_SEC, font=self.FSMALL)
        self.iter_lbl.pack(side="left", padx=8)

        sc = tk.Frame(p, bg=BG_CARD); sc.pack(fill="x", padx=20, pady=(0,6))
        self._sv = {}
        for lbl, key in [("Best Score","score"),("Iterations","iter"),
                          ("CL","cl"),("CD","cd"),("CM","cm"),("rCL","rcl")]:
            c = self._stat_card(sc, lbl); c.pack(side="left", padx=5)
            self._sv[key] = c.var

        self._sec(p,"Optimization Log").pack(fill="x", padx=20, pady=(4,3))
        self.log = scrolledtext.ScrolledText(
            p, bg=BG_INPUT, fg=TEXT_SEC, font=("Consolas",8),
            relief="flat", insertbackground=TEXT_PRI)
        self.log.pack(fill="both", expand=True, padx=20, pady=(0,10))
        self.log.tag_config("ok",    foreground=ACCENT)
        self.log.tag_config("err",   foreground=RED)
        self.log.tag_config("warn",  foreground=YELLOW)
        self.log.tag_config("score", foreground=ACCENT2)
        self.log.tag_config("info",  foreground=TEXT_SEC)
        self.log.tag_config("head",  foreground=ACCENT3)

    # ── Tab 5: Results ────────────────────────────────────────────────
    def _tab_results(self, p):
        self._sec(p,"Optimization Results  --  Before / After").pack(
            fill="x", padx=20, pady=(18,6))

        sc = tk.Frame(p, bg=BG_CARD); sc.pack(fill="x", padx=20, pady=(0,10))
        self._rsv = {}
        for lbl, key in [("Score Before","sc_before"),("Score After","sc_after"),
                          ("CL Before","cl_before"),  ("CL After","cl_after"),
                          ("CD Before","cd_before"),  ("CD After","cd_after"),
                          ("CM Before","cm_before"),  ("CM After","cm_after")]:
            c = self._stat_card(sc, lbl); c.pack(side="left", padx=4)
            self._rsv[key] = c.var

        self._sec(p,"Parameter Changes").pack(fill="x", padx=20, pady=(4,3))

        th = tk.Frame(p, bg=BG_PANEL); th.pack(fill="x", padx=20)
        for txt, wid in [("Parameter",34),("Before",14),("After",14),
                          ("Change",14),("Unit",7),("Status",10)]:
            tk.Label(th, text=txt, bg=BG_PANEL, fg=TEXT_SEC,
                     font=("Consolas",8,"bold"), width=wid, anchor="w").pack(
                         side="left", padx=4, pady=5)

        outer2 = tk.Frame(p, bg=BG_CARD)
        outer2.pack(fill="both", expand=True, padx=20, pady=(0,16))
        self._rc = tk.Canvas(outer2, bg=BG_CARD, highlightthickness=0)
        sb2 = tk.Scrollbar(outer2, orient="vertical", command=self._rc.yview)
        self._rc.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self._rc.pack(side="left", fill="both", expand=True)
        self._ri = tk.Frame(self._rc, bg=BG_CARD)
        self._rw = self._rc.create_window((0,0), window=self._ri, anchor="nw")
        self._ri.bind("<Configure>",
                      lambda e: self._rc.configure(scrollregion=self._rc.bbox("all")))
        self._rc.bind("<Configure>",
                      lambda e: self._rc.itemconfig(self._rw, width=e.width))

        tk.Label(self._ri, text="Run optimization to see results here.",
                 bg=BG_CARD, fg=TEXT_DIM, font=self.FBODY).pack(pady=30)

    def _populate_results(self, initial, final, active_idx,
                          sc_b, sc_a, cl_b, cl_a, cd_b, cd_a, cm_b, cm_a):
        for key, val in [("sc_before",sc_b),("sc_after",sc_a),
                          ("cl_before",cl_b),("cl_after",cl_a),
                          ("cd_before",cd_b),("cd_after",cd_a),
                          ("cm_before",cm_b),("cm_after",cm_a)]:
            self._rsv[key].set(f"{val:.4f}" if val is not None else "-")

        f = self._ri
        for w in f.winfo_children(): w.destroy()

        changed   = [(idx,lbl,unit,sc,initial[idx]*sc,final[idx]*sc,
                       final[idx]*sc - initial[idx]*sc)
                      for (idx,lbl,unit,sc,_) in PARAM_DEFS if idx in active_idx]
        unchanged = [(idx,lbl,unit,sc,initial[idx]*sc,final[idx]*sc,
                       final[idx]*sc - initial[idx]*sc)
                      for (idx,lbl,unit,sc,_) in PARAM_DEFS if idx not in active_idx]

        def row_widget(items, title, optimized):
            if not items: return
            sh = tk.Frame(f, bg=BG_DARK); sh.pack(fill="x", pady=(6,1))
            tk.Label(sh, text=f"  {title}", bg=BG_DARK,
                     fg=ACCENT if optimized else TEXT_DIM,
                     font=("Consolas",8,"bold")).pack(side="left", padx=6, pady=2)
            for i,(idx,lbl,unit,sc,vb,va,d) in enumerate(items):
                bg = BG_CARD if i%2==0 else BG_PANEL
                r = tk.Frame(f, bg=bg); r.pack(fill="x", pady=1)
                tk.Label(r, text=lbl, bg=bg, fg=TEXT_PRI,
                         font=self.FBODY, width=34, anchor="w").pack(side="left",padx=4,pady=3)
                tk.Label(r, text=f"{vb:.5f}", bg=bg, fg=TEXT_SEC,
                         font=self.FBODY, width=14, anchor="w").pack(side="left",padx=4)
                af_col = ACCENT if abs(d)>1e-6 else TEXT_SEC
                af_fnt = ("Consolas",9,"bold") if abs(d)>1e-6 else self.FBODY
                tk.Label(r, text=f"{va:.5f}", bg=bg, fg=af_col,
                         font=af_fnt, width=14, anchor="w").pack(side="left",padx=4)
                sign = "+" if d>0 else ""
                ch_col = ACCENT if d>1e-6 else (ACCENT3 if d<-1e-6 else TEXT_DIM)
                tk.Label(r, text=f"{sign}{d:.5f}", bg=bg, fg=ch_col,
                         font=self.FBODY, width=14, anchor="w").pack(side="left",padx=4)
                tk.Label(r, text=unit, bg=bg, fg=TEXT_DIM,
                         font=self.FSMALL, width=7, anchor="w").pack(side="left",padx=4)
                st_col = ACCENT2 if optimized else TEXT_DIM
                tk.Label(r, text="optimized" if optimized else "fixed",
                         bg=bg, fg=st_col, font=self.FSMALL,
                         width=10, anchor="w").pack(side="left",padx=4)

        row_widget(changed,   "Optimized Parameters", True)
        row_widget(unchanged, "Fixed Parameters (not selected for optimization)", False)

    # ── Helpers ───────────────────────────────────────────────────────
    def _sec(self, parent, text):
        f = tk.Frame(parent, bg=parent['bg'])
        tk.Label(f, text=text.upper(), bg=parent['bg'],
                 fg=TEXT_DIM, font=self.FSMALL).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(side="left",fill="x",expand=True,padx=8)
        return f

    def _card(self, parent):
        return tk.Frame(parent, bg=BG_PANEL, padx=14, pady=10)

    def _btn(self, parent, text, cmd, color=BG_PANEL, big=False):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color, fg=TEXT_PRI, relief="flat",
                         font=("Consolas",10,"bold") if big else self.FSMALL,
                         cursor="hand2", activebackground=BG_INPUT,
                         activeforeground=TEXT_PRI,
                         padx=16 if big else 10, pady=9 if big else 5)

    def _stat_card(self, parent, label):
        f = tk.Frame(parent, bg=BG_PANEL, padx=12, pady=8, width=108)
        f.pack_propagate(False)
        tk.Label(f, text=label, bg=BG_PANEL, fg=TEXT_SEC, font=self.FSMALL).pack()
        f.var = tk.StringVar(value="-")
        tk.Label(f, textvariable=f.var, bg=BG_PANEL, fg=TEXT_PRI,
                 font=("Consolas",9,"bold")).pack()
        return f

    def _tog_all(self, v):
        for bv in self.param_enabled.values(): bv.set(v)

    # ── File ops ──────────────────────────────────────────────────────
    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select for005.dat",
            filetypes=[("DAT files","*.dat"),("All files","*.*")])
        if path:
            self.dat_file.set(path)
            self._load()

    def _browse_exe(self):
        path = filedialog.askopenfilename(
            title="Select digital_DATCOM.exe",
            filetypes=[("Executable","*.exe"),("All files","*.*")])
        if path:
            self.datcom_exe.set(path)

    def _load(self):
        path = self.dat_file.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error","Please enter a valid file path.")
            return
        inp, zv, wt, ok, err = parse_for005(path)
        if not ok:
            messagebox.showerror("Parse Error", f"Could not parse file:\n{err}")
            return

        # auto-detect Digital DATCOM EXE next to selected DAT if possible
        cur_exe = self.datcom_exe.get().strip()
        if (not cur_exe) or (not os.path.exists(cur_exe)):
            auto_exe = os.path.join(os.path.dirname(path), "digital_DATCOM.exe")
            if os.path.exists(auto_exe):
                self.datcom_exe.set(auto_exe)

        if myfuncs is not None:
            try:
                if hasattr(myfuncs, "set_datcom_exe_path"):
                    myfuncs.set_datcom_exe_path(self.datcom_exe.get().strip())
                if hasattr(myfuncs, "set_datcom_dat_path"):
                    myfuncs.set_datcom_dat_path(path)
            except Exception:
                pass
        self.inp_vals     = inp
        self._initial_inp = list(inp)
        self.zv_val       = zv
        self.wt_val       = wt

        with open(path) as f:
            self.preview.delete("1.0","end")
            self.preview.insert("end", f.read())

        self.alschd_label.config(text=f"ALSCHD = {inp[0]*10:.2f}  deg")

        for (idx,label,unit,scale,_) in PARAM_DEFS:
            self.param_cur[idx].set(f"{inp[idx]*scale:.4f} {unit}")
            lo, hi = DEFAULT_BOUNDS[idx]
            self.param_lo[idx].set(f"{lo*scale:.4f}")
            self.param_hi[idx].set(f"{hi*scale:.4f}")

        messagebox.showinfo("Loaded",
            f"File parsed successfully.\n32 parameters read.\n"
            f"ZV = {zv:.5f} m    WT = {wt:.1f} N\n\n"
            f"Original file will NOT be modified during optimization.\n"
            f"A temporary working copy is used for each DATCOM evaluation.")

    # ── Logging ───────────────────────────────────────────────────────
    def _log(self, msg, tag="info"):
        self.log.insert("end", msg+"\n", tag)
        self.log.see("end")

    def _clear_log(self):
        self.log.delete("1.0","end")

    # ── Opt control ───────────────────────────────────────────────────
    def _start(self):
        if not self.inp_vals:
            messagebox.showerror("Error","Please load a for005.dat file first.")
            return
        exe_path = self.datcom_exe.get().strip()
        if not exe_path or not os.path.exists(exe_path):
            messagebox.showerror("Error","Please select a valid digital_DATCOM.exe path first.")
            return
        if myfuncs is not None:
            try:
                if hasattr(myfuncs, "set_datcom_exe_path"):
                    myfuncs.set_datcom_exe_path(exe_path)
                if hasattr(myfuncs, "set_datcom_dat_path"):
                    myfuncs.set_datcom_dat_path(self.dat_file.get().strip())
            except Exception:
                pass
        if self._running: return
        self._running    = True
        self._iter_count = 0
        self._best_score = float('inf')
        self.run_btn.config(state="disabled")
        self.prog.start(14)
        self.status_lbl.config(text="Running...")
        for v in self._sv.values(): v.set("-")
        threading.Thread(target=self._opt_thread, daemon=True).start()

    def _stop(self):
        self._running = False
        self.prog.stop()
        self.status_lbl.config(text="Stopped")
        self.run_btn.config(state="normal")

    def _finish(self, msg="Done"):
        self._running = False
        self.after(0, self.prog.stop)
        self.after(0, lambda: self.status_lbl.config(text=msg))
        self.after(0, lambda: self.run_btn.config(state="normal"))

    def _opt_thread(self):
        try:
            self._run_optimization()
        except StopIteration:
            self.after(0, lambda: self._log("Stopped by user.","warn"))
            self._finish("Stopped")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.after(0, lambda: self._log(f"ERROR: {e}\n{tb}","err"))
            self._finish("Error")

    # ── Core optimization ─────────────────────────────────────────────
    def _run_optimization(self):
        from scipy.optimize import fmin_slsqp

        dat_path  = self.dat_file.get().strip()
        inp       = list(self.inp_vals)
        initial   = list(self._initial_inp)
        zv        = self.zv_val
        wt        = self.wt_val
        fixed_zv  = True
        cost_expr = self.cost_expr.get()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        exe_path  = self.datcom_exe.get().strip()
        exe_dir   = os.path.dirname(exe_path) if exe_path else os.path.dirname(dat_path)

        # Output folder
        out_folder = os.path.join(exe_dir, f"opt_result_{timestamp}")
        os.makedirs(out_folder, exist_ok=True)

        # Temp dat — original never touched during iterations
        tmp_dat = os.path.join(exe_dir, f"_opt_temp_{timestamp}.dat")
        shutil.copy2(dat_path, tmp_dat)

        log_lines = []
        def both(msg, tag="info"):
            self.after(0, lambda m=msg, t=tag: self._log(m, t))
            log_lines.append(msg)

        both("="*70, "head")
        both(f"  DATCOM Optimization  --  {timestamp}", "head")
        both("="*70, "head")
        both(f"  Input file   : {dat_path}")
        both(f"  DATCOM EXE   : {exe_path if exe_path else os.path.join(exe_dir, 'digital_DATCOM.exe')}")
        both(f"  Temp copy    : {tmp_dat}  (original read-only)")
        both(f"  Output dir   : {out_folder}")
        both(f"  ZV           : {zv:.5f} m")
        both("  ZH           : fixed (not optimized)")
        both(f"  WT           : {wt:.1f} N")
        both(f"  ALSCHD       : {inp[0]*10:.2f} deg  (fixed, not optimized)")
        both(f"  Cost expr    : {cost_expr}")
        both("-"*70)

        _wa  = max((inp[3]*100)*(inp[8]*100), 0.01)
        _rCL = 2*wt/(_wa*1.225*102.0**2)
        both(f"  rCL estimate : {_rCL:.4f}  (required lift coeff for level flight)")
        if _rCL > 1.0:
            both(f"  NOTE: soft penalty active while CL < rCL", "warn")
        both("-"*70)

        # Collect active params
        active_idx, active_lo, active_hi = [], [], []
        for (idx,label,unit,scale,_) in PARAM_DEFS:
            if self.param_enabled[idx].get():
                try:
                    lo = float(self.param_lo[idx].get())/scale
                    hi = float(self.param_hi[idx].get())/scale
                    active_idx.append(idx)
                    active_lo.append(lo)
                    active_hi.append(hi)
                except ValueError:
                    both(f"  WARNING: invalid bounds for {label}, skipped.","warn")

        if not active_idx:
            both("No parameters selected!","err"); self._finish("Error"); return

        both(f"\n  Active parameters ({len(active_idx)}):", "ok")
        for k, idx in enumerate(active_idx):
            _, lbl, unit, sc, _ = next(d for d in PARAM_DEFS if d[0]==idx)
            both(f"    [{idx:2d}] {lbl:40s}  lo={active_lo[k]*sc:.4f}  hi={active_hi[k]*sc:.4f}  {unit}")
        both("-"*70)

        bounds = list(zip(active_lo, active_hi))
        x0 = [inp[i] for i in active_idx]

        # Evaluate initial point
        sc_b, cl_b, cd_b, cm_b, rcl_b = self._evaluate(
            list(inp), zv, wt, dat_path, tmp_dat, exe_dir, cost_expr, fixed_zv)
        both(f"\n  Initial eval:  score={sc_b:.5f}  CL={cl_b:.4f}  CD={cd_b:.4f}  CM={cm_b:.4f}  rCL={rcl_b:.4f}", "info")
        both("-"*70)

        best_x     = list(x0)
        best_score = sc_b
        best_vals  = dict(CL=cl_b, CD=cd_b, CM=cm_b, rCL=rcl_b)

        for i_inp in range(6):
            if not self._running: raise StopIteration

            if i_inp == 0:
                xstart = list(x0)
            else:
                xstart = [x0[0]]
                for k in range(1, len(x0)):
                    step = (active_hi[k]-active_lo[k])/5.0
                    xstart.append(min(active_hi[k],
                                      max(active_lo[k],
                                          active_lo[k]+i_inp*step)))

            lbl_start = ["nominal","1/5","2/5","3/5","4/5","4.5/5"][i_inp]
            both(f"\n  -- Pass {i_inp+1}/6  (start: {lbl_start})", "head")
            pass_call = [0]
            pass_best = [float('inf')]

            def objective(x, pi=i_inp):
                nonlocal best_x, best_score, best_vals
                if not self._running: raise StopIteration
                pass_call[0] += 1
                self._iter_count += 1
                full = list(inp)
                for k2, i2 in enumerate(active_idx): full[i2] = x[k2]
                score, CL, CD, CM, rCL = self._evaluate(
                    full, zv, wt, dat_path, tmp_dat, exe_dir, cost_expr, fixed_zv)
                it = self._iter_count
                self.after(0, lambda n=it: (
                    self.iter_lbl.config(text=f"Iter: {n}"),
                    self._sv['iter'].set(str(n))))
                if score < pass_best[0]:
                    pass_best[0] = score
                    both(f"  Pass {pi+1} | Iter {pass_call[0]:4d} | "
                         f"score={score:12.5f} | "
                         f"CL={CL:.4f}  CD={CD:.4f}  CM={CM:.5f}  rCL={rCL:.4f}",
                         "score")
                if score < best_score:
                    best_x     = list(x)
                    best_score = score
                    best_vals  = dict(CL=CL,CD=CD,CM=CM,rCL=rCL)
                    self.after(0, lambda s=score: self._sv['score'].set(f"{s:.5f}"))
                    self.after(0, lambda: [
                        self._sv['cl' ].set(f"{best_vals['CL']:.4f}"),
                        self._sv['cd' ].set(f"{best_vals['CD']:.4f}"),
                        self._sv['cm' ].set(f"{best_vals['CM']:.4f}"),
                        self._sv['rcl'].set(f"{best_vals['rCL']:.4f}"),
                    ])
                return score

            try:
                res = fmin_slsqp(objective, xstart, bounds=bounds,
                                 epsilon=0.001, iprint=0, full_output=True)
                _, _of, _, _, _ = res
                both(f"  Pass {i_inp+1} done  ->  pass best = {pass_best[0]:.5f} | global best = {best_score:.5f}", "ok")
            except StopIteration:
                raise
            except Exception as e:
                both(f"  Pass {i_inp+1} error: {e}", "err")

        # Final inp
        final_inp = list(inp)
        for k, idx in enumerate(active_idx): final_inp[idx] = best_x[k]
        self._final_inp = final_inp   # save for Aircraft View tab

        # Evaluate final point
        sc_a, cl_a, cd_a, cm_a, rcl_a = self._evaluate(
            final_inp, zv, wt, dat_path, tmp_dat, exe_dir, cost_expr, fixed_zv)

        both("\n"+"="*70, "head")
        both(f"  OPTIMIZATION COMPLETE", "ok")
        both(f"  Score  : {sc_b:.5f}  ->  {sc_a:.5f}", "ok")
        both(f"  CL     : {cl_b:.4f}  ->  {cl_a:.4f}", "ok")
        both(f"  CD     : {cd_b:.4f}  ->  {cd_a:.4f}", "ok")
        both(f"  CM     : {cm_b:.4f}  ->  {cm_a:.4f}", "ok")
        both("="*70, "head")
        both("\n  Parameter changes:", "head")
        for idx in active_idx:
            _,lbl,unit,sc,_ = next(d for d in PARAM_DEFS if d[0]==idx)
            vb = initial[idx]*sc; va = final_inp[idx]*sc
            sg = "+" if va>vb else ""
            both(f"    [{idx:2d}] {lbl:40s}  {vb:.5f} -> {va:.5f}  ({sg}{va-vb:.5f}) {unit}")

        # Write outputs
        opt_dat = os.path.join(out_folder, "for005_optimized.dat")
        shutil.copy2(dat_path, opt_dat)
        write_inp_to_dat(final_inp, opt_dat, fixed_zv, zv)
        both(f"\n  Optimized dat  ->  {opt_dat}", "ok")

        csv_path = os.path.join(out_folder, "parameters_before_after.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("Index,Parameter,Unit,Before,After,Change,LoBound,HiBound,Optimized\n")
            for (idx,lbl,unit,sc,_) in PARAM_DEFS:
                vb = initial[idx]*sc; va = final_inp[idx]*sc
                opt_flag = "yes" if idx in active_idx else "no"
                lo = DEFAULT_BOUNDS.get(idx,(0,0))[0]*sc
                hi = DEFAULT_BOUNDS.get(idx,(0,0))[1]*sc
                f.write(f"{idx},{lbl},{unit},{vb:.6f},{va:.6f},{va-vb:.6f},{lo:.6f},{hi:.6f},{opt_flag}\n")
        both(f"  CSV (before/after) ->  {csv_path}", "ok")

        with open(os.path.join(out_folder,"optimization_log.txt"),
                  'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        both(f"  Log file  ->  {os.path.join(out_folder,'optimization_log.txt')}", "ok")
        both(f"\n  Output folder  :  {out_folder}\n", "head")

        # Cleanup temp
        try: os.remove(tmp_dat)
        except: pass

        # Populate Results tab
        self.after(0, lambda: self._populate_results(
            initial, final_inp, active_idx,
            sc_b, sc_a, cl_b, cl_a, cd_b, cd_a, cm_b, cm_a))

        self._finish("Optimization complete")

    # ── Single DATCOM evaluation — uses temp copy, never original ─────
    def _evaluate(self, inp, zv, wt, orig_dat, tmp_dat, exe_dir, cost_expr, fixed_zv):
        # Fresh copy from original every time
        shutil.copy2(orig_dat, tmp_dat)
        write_inp_to_dat(inp, tmp_dat, fixed_zv, zv)

        exe_path = self.datcom_exe.get().strip()
        exe = exe_path if exe_path else os.path.join(exe_dir, "digital_DATCOM.exe")
        if not os.path.exists(exe):
            raise FileNotFoundError(f"digital_DATCOM.exe not found: {exe}")

        out_path = os.path.join(exe_dir, "datcom.out")
        work_dat = os.path.join(exe_dir, "for005.dat")
        bak_dat = os.path.join(exe_dir, "for005._gui_backup.dat")
        had_original = os.path.exists(work_dat)

        # remove stale output
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
        except Exception:
            pass

        # place current input where DATCOM expects it
        try:
            if had_original:
                shutil.copy2(work_dat, bak_dat)
            shutil.copy2(tmp_dat, work_dat)

            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            subprocess.Popen(exe, startupinfo=si, cwd=exe_dir)

            # wait for output to appear and settle
            t0 = time.time()
            last_size = -1
            stable_hits = 0
            while time.time() - t0 < 20.0:
                if os.path.exists(out_path):
                    sz = os.path.getsize(out_path)
                    if sz > 0 and sz == last_size:
                        stable_hits += 1
                        if stable_hits >= 2:
                            break
                    else:
                        stable_hits = 0
                    last_size = sz
                time.sleep(0.25)

            if not os.path.exists(out_path):
                raise FileNotFoundError(f"datcom.out was not created in: {exe_dir}")

            CL,CD,CM,wing_area,velocity,density = read_datcom_out(out_path)
        finally:
            # restore original for005.dat if there was one
            try:
                if had_original and os.path.exists(bak_dat):
                    shutil.copy2(bak_dat, work_dat)
                    os.remove(bak_dat)
                elif (not had_original) and os.path.exists(work_dat):
                    os.remove(work_dat)
            except Exception:
                pass

        rCL = 2*wt/(wing_area*density*velocity**2) if (wing_area*density*velocity) else 1e6

        try:
            base = float(eval(cost_expr, {"__builtins__":{}}, {
                "CL":CL,"CD":CD,"CM":CM,"rCL":rCL,
                "wing_area":wing_area,"velocity":velocity,
                "density":density,"weight":wt,"abs":abs,"math":math}))
        except:
            base = 1e6

        score = base + 1000.0*(1.0+(rCL-CL)) if rCL > CL else base
        return score, CL, CD, CM, rCL


    # ── Tab 6: Aircraft View ──────────────────────────────────────────
    def _tab_view(self, p):
        self._view_frame = p
        self._canvas_widget = None
        self._last_fig      = None

        ctrl = tk.Frame(p, bg=BG_CARD); ctrl.pack(fill="x", padx=20, pady=10)
        self._btn(ctrl, "Draw  Before  &  After  (side-by-side)",
                  self._draw_both, ACCENT, big=True).pack(side="left")
        self._btn(ctrl, "Save PNG...",
                  self._save_view_png, BG_PANEL).pack(side="left", padx=10)

        self._view_status = tk.Label(
            ctrl,
            text="Load a dat file (and optionally run optimization), then click Draw.",
            bg=BG_CARD, fg=TEXT_SEC, font=self.FSMALL)
        self._view_status.pack(side="left", padx=12)

        self._view_area = tk.Frame(p, bg=BG_DARK)
        self._view_area.pack(fill="both", expand=True, padx=8, pady=(0,8))
        tk.Label(self._view_area,
                 text="No drawing yet.\nClick 'Draw Before & After' above.",
                 bg=BG_DARK, fg=TEXT_DIM,
                 font=("Consolas", 10)).pack(expand=True)

    def _make_draw_dat(self, inp_list, dat_path):
        """
        Write inp_list into a temp copy of dat_path and return the temp path.
        Caller is responsible for deleting it.
        """
        import tempfile as _tf
        tmp = _tf.NamedTemporaryFile(suffix='.dat', delete=False,
                                      dir=os.path.dirname(dat_path))
        tmp.close()
        shutil.copy2(dat_path, tmp.name)
        write_inp_to_dat(inp_list, tmp.name,
                          True, self.zv_val)
        return tmp.name

    def _draw_both(self):
        if not _MPL_OK:
            messagebox.showerror("Missing library",
                "matplotlib is required.\n  pip install matplotlib")
            return

        dat_path = self.dat_file.get().strip()
        if not dat_path or not os.path.exists(dat_path):
            messagebox.showerror("Error", "Please load a for005.dat file first.")
            return

        self._view_status.config(text="Rendering...")
        self.update_idletasks()

        tmp_before = tmp_after = None
        try:
            from aircraft_view import get_figure_sidebyside

            # Before: original inp_vals as loaded from file
            before_inp = list(self._initial_inp) if self._initial_inp else list(self.inp_vals)
            tmp_before = self._make_draw_dat(before_inp, dat_path)

            # After: final optimized inp if available, else same as before
            if self._final_inp:
                after_inp = list(self._final_inp)
                after_label = "After (Optimized)"
            else:
                after_inp = list(before_inp)
                after_label = "After (no optimization yet)"
            tmp_after = self._make_draw_dat(after_inp, dat_path)

            fig = get_figure_sidebyside(
                tmp_before, tmp_after,
                label_left="Before (Original)",
                label_right=after_label,
                figsize=(18, 8))

            self._last_fig = fig
            self._embed_figure(fig)
            self._view_status.config(
                text=f"Before vs After  |  "
                     f"{'Optimized result shown on right.' if self._final_inp else 'Run optimization to see changes.'}")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self._view_status.config(text=f"Error: {e}")
            messagebox.showerror("Draw Error",
                f"Could not generate drawing:\n{e}\n\n{tb[:600]}")
        finally:
            for tmp in [tmp_before, tmp_after]:
                if tmp:
                    try: os.remove(tmp)
                    except: pass

    def _embed_figure(self, fig):
        for w in self._view_area.winfo_children(): w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self._view_area)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=BG_DARK)
        widget.pack(fill="both", expand=True)
        self._canvas_widget = canvas

    def _save_view_png(self):
        if self._last_fig is None:
            messagebox.showinfo("Nothing to save", "Draw the aircraft first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save aircraft view as PNG",
            defaultextension=".png",
            filetypes=[("PNG image","*.png"),("All files","*.*")])
        if path:
            self._last_fig.savefig(path, dpi=150, bbox_inches='tight',
                                    facecolor=self._last_fig.get_facecolor())
            messagebox.showinfo("Saved", f"Saved to:\n{path}")


    # ── Tab 7: Aero Sweep ─────────────────────────────────────────────
    SWEEP_ALPHAS = [-10.0, -8.0, -6.0, -4.0, -2.0,
                     0.0,  2.0,  4.0,  6.0,  8.0,
                    10.0, 12.0, 14.0, 16.0, 18.0]

    def _tab_sweep(self, p):
        """Tab 7 – full alpha sweep and aerodynamic coefficient plots."""
        self._sweep_fig         = None
        self._sweep_canvas_obj  = None

        # ── Top control bar ──────────────────────────────────────────
        ctrl = tk.Frame(p, bg=BG_CARD); ctrl.pack(fill="x", padx=20, pady=14)

        self.sweep_btn = self._btn(
            ctrl, "▶  Run Alpha Sweep  (Baseline + Optimized)",
            self._start_sweep, ACCENT, big=True)
        self.sweep_btn.pack(side="left")

        self._btn(ctrl, "[X] Stop", self._stop_sweep, RED).pack(
            side="left", padx=10)

        self._btn(ctrl, "Save PNG...", self._save_sweep_png, BG_PANEL).pack(
            side="left", padx=4)

        # ── Status / progress bar ────────────────────────────────────
        pg = tk.Frame(p, bg=BG_CARD); pg.pack(fill="x", padx=20, pady=(0, 6))
        self.sweep_status = tk.Label(
            pg, text="Load a dat file (run optimization for Optimized curve), then click Run.",
            bg=BG_CARD, fg=TEXT_SEC, font=self.FSMALL)
        self.sweep_status.pack(side="left")
        self.sweep_prog = ttk.Progressbar(
            pg, mode="indeterminate", length=260,
            style="opt.Horizontal.TProgressbar")
        self.sweep_prog.pack(side="left", padx=12)

        # ── Alpha list editor ────────────────────────────────────────
        ae = tk.Frame(p, bg=BG_CARD); ae.pack(fill="x", padx=20, pady=(0, 4))
        tk.Label(ae, text="Alpha list (comma-separated):",
                 bg=BG_CARD, fg=TEXT_DIM, font=self.FSMALL).pack(side="left")
        self._sweep_alpha_var = tk.StringVar(
            value=", ".join(str(a) for a in self.SWEEP_ALPHAS))
        tk.Entry(ae, textvariable=self._sweep_alpha_var,
                 bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                 relief="flat", font=self.FSMALL, width=80).pack(
                     side="left", padx=8, ipady=4)

        # ── Mach label for legend (editable) ────────────────────────
        ml = tk.Frame(p, bg=BG_CARD); ml.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(ml, text="Legend Mach label:",
                 bg=BG_CARD, fg=TEXT_DIM, font=self.FSMALL).pack(side="left")
        self._sweep_mach_var = tk.StringVar(value="Mach = 0.3")
        tk.Entry(ml, textvariable=self._sweep_mach_var,
                 bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                 relief="flat", font=self.FSMALL, width=20).pack(
                     side="left", padx=8, ipady=4)

        # ── Plot canvas area ─────────────────────────────────────────
        self._sweep_area = tk.Frame(p, bg=BG_DARK)
        self._sweep_area.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        tk.Label(self._sweep_area,
                 text="No sweep data yet.\nClick 'Run Alpha Sweep' above.",
                 bg=BG_DARK, fg=TEXT_DIM,
                 font=("Consolas", 10)).pack(expand=True)

    # ── Sweep control ─────────────────────────────────────────────────
    def _start_sweep(self):
        if not _MPL_OK:
            messagebox.showerror("Missing library",
                "matplotlib is required for this tab.\n  pip install matplotlib")
            return
        if not self.inp_vals:
            messagebox.showerror("Error", "Please load a for005.dat file first.")
            return
        exe_path = self.datcom_exe.get().strip()
        if not exe_path or not os.path.exists(exe_path):
            messagebox.showerror("Error",
                "Please select a valid digital_DATCOM.exe path first.")
            return
        if self._sweep_running:
            return

        # Parse alpha list from the editable field
        try:
            alphas = [float(x.strip())
                      for x in self._sweep_alpha_var.get().split(',')
                      if x.strip()]
            if not alphas:
                raise ValueError("empty")
        except ValueError:
            messagebox.showerror("Error",
                "Invalid alpha list. Use comma-separated numbers.")
            return

        self._sweep_running = True
        self.sweep_btn.config(state="disabled")
        self.sweep_prog.start(14)
        self.sweep_status.config(text="Running baseline sweep...")
        threading.Thread(
            target=self._sweep_thread,
            args=(alphas,),
            daemon=True).start()

    def _stop_sweep(self):
        self._sweep_running = False
        self.sweep_prog.stop()
        self.sweep_status.config(text="Stopped")
        self.sweep_btn.config(state="normal")

    def _sweep_finish(self, msg="Done"):
        self._sweep_running = False
        self.after(0, self.sweep_prog.stop)
        self.after(0, lambda: self.sweep_status.config(text=msg))
        self.after(0, lambda: self.sweep_btn.config(state="normal"))

    # ── Sweep worker thread ────────────────────────────────────────────
    def _sweep_thread(self, alphas):
        try:
            self._run_sweep(alphas)
        except StopIteration:
            self.after(0, lambda: self.sweep_status.config(text="Stopped by user."))
            self._sweep_finish("Stopped")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.after(0, lambda: messagebox.showerror(
                "Sweep Error", f"{e}\n\n{tb[:800]}"))
            self._sweep_finish(f"Error: {e}")

    # ── Core sweep logic ───────────────────────────────────────────────
    def _run_sweep(self, alphas):
        dat_path = self.dat_file.get().strip()
        exe_path = self.datcom_exe.get().strip()
        exe_dir  = os.path.dirname(exe_path)
        nalpha   = len(alphas)
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        def check():
            if not self._sweep_running:
                raise StopIteration

        # ── Helper: write sweep dat, run DATCOM, parse output ─────────
        def run_one_sweep(inp_list, label):
            check()
            tmp_dat = os.path.join(exe_dir, f"_sweep_{label}_{ts}.dat")
            try:
                # 1. Write geometry into a copy of the original dat
                shutil.copy2(dat_path, tmp_dat)
                write_inp_to_dat(inp_list, tmp_dat, True, self.zv_val)
                # 2. Patch NALPHA + ALSCHD onto that copy
                patched = os.path.join(exe_dir, f"_sweep_{label}_patched_{ts}.dat")
                patch_dat_for_sweep(tmp_dat, patched, nalpha, alphas)

                # 3. Place as for005.dat next to the exe
                work_dat = os.path.join(exe_dir, "for005.dat")
                out_path = os.path.join(exe_dir, "datcom.out")
                bak_dat  = os.path.join(exe_dir, "for005._sweep_bak.dat")
                had_orig = os.path.exists(work_dat)

                try:
                    if os.path.exists(out_path):
                        os.remove(out_path)
                except Exception:
                    pass

                try:
                    if had_orig:
                        shutil.copy2(work_dat, bak_dat)
                    shutil.copy2(patched, work_dat)

                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = subprocess.SW_HIDE
                    subprocess.Popen(exe_path, startupinfo=si, cwd=exe_dir)

                    # Wait for output to settle
                    t0, last_sz, hits = time.time(), -1, 0
                    while time.time() - t0 < 60.0:
                        check()
                        if os.path.exists(out_path):
                            sz = os.path.getsize(out_path)
                            if sz > 0 and sz == last_sz:
                                hits += 1
                                if hits >= 3:
                                    break
                            else:
                                hits = 0
                            last_sz = sz
                        time.sleep(0.3)

                    if not os.path.exists(out_path):
                        raise FileNotFoundError(
                            f"datcom.out not created (sweep:{label})")

                    data, vel, pres, temp = parse_sweep_out(out_path, alphas)

                finally:
                    try:
                        if had_orig and os.path.exists(bak_dat):
                            shutil.copy2(bak_dat, work_dat)
                            os.remove(bak_dat)
                        elif (not had_orig) and os.path.exists(work_dat):
                            os.remove(work_dat)
                    except Exception:
                        pass

                return data
            finally:
                for f in [tmp_dat,
                          os.path.join(exe_dir, f"_sweep_{label}_patched_{ts}.dat")]:
                    try: os.remove(f)
                    except: pass

        # ── Baseline sweep ────────────────────────────────────────────
        self.after(0, lambda: self.sweep_status.config(
            text=f"Running BASELINE sweep  ({nalpha} alphas)..."))
        base_data = run_one_sweep(list(self._initial_inp) if self._initial_inp
                                  else list(self.inp_vals), "base")
        self._sweep_data_base = base_data
        self.after(0, lambda: self.sweep_status.config(
            text=f"Baseline done ({len(base_data)} pts). Running OPTIMIZED sweep..."))

        # ── Optimized sweep ───────────────────────────────────────────
        check()
        if self._final_inp:
            opt_data = run_one_sweep(list(self._final_inp), "opt")
        else:
            # No optimization run yet – show same data with a warning
            opt_data = list(base_data)
            self.after(0, lambda: self.sweep_status.config(
                text="Warning: no optimized result available – showing baseline for both curves."))
        self._sweep_data_opt = opt_data

        # ── Plot ──────────────────────────────────────────────────────
        check()
        mach_lbl = self._sweep_mach_var.get().strip() or "Mach = 0.3"
        self.after(0, lambda: self._draw_sweep_plots(
            base_data, opt_data, mach_lbl))
        self._sweep_finish(
            f"Sweep complete — {len(base_data)} baseline pts, "
            f"{len(opt_data)} optimized pts.")

    # ── Plotting ───────────────────────────────────────────────────────
    def _draw_sweep_plots(self, base_data, opt_data, mach_lbl):
        if not _MPL_OK:
            return
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        import numpy as np

        def _extract(data):
            a  = [d['alpha'] for d in data]
            CL = [d['CL']    for d in data]
            CD = [d['CD']    for d in data]
            CM = [d['CM']    for d in data]
            LD = [cl/cd if abs(cd) > 1e-9 else 0.0
                  for cl, cd in zip(CL, CD)]
            dCM = list(np.gradient(CM, a)) if len(a) > 1 else CM
            return a, CL, CD, CM, LD, dCM

        ab, CLb, CDb, CMb, LDb, dCMb = _extract(base_data)
        ao, CLo, CDo, CMo, LDo, dCMo = _extract(opt_data)

        # ── Figure layout ─────────────────────────────────────────────
        fig = plt.Figure(figsize=(16, 13), facecolor="#0d1117")
        fig.subplots_adjust(hspace=0.42, wspace=0.32,
                            left=0.07, right=0.97,
                            top=0.93, bottom=0.06)
        gs = gridspec.GridSpec(3, 2, figure=fig)

        axes = [
            fig.add_subplot(gs[0, 0]),  # CL vs alpha
            fig.add_subplot(gs[0, 1]),  # CD vs alpha
            fig.add_subplot(gs[1, 0]),  # CM vs alpha
            fig.add_subplot(gs[1, 1]),  # L/D vs alpha
            fig.add_subplot(gs[2, :]),  # dCM/dAlpha vs alpha (full width)
        ]

        plot_cfg = [
            ("CL vs α",          ab, CLb,  ao, CLo,  "C_L",           "b-o", "r-o"),
            ("CD vs α",          ab, CDb,  ao, CDo,  "C_D",           "b-s", "r-s"),
            ("CM vs α",          ab, CMb,  ao, CMo,  "C_M",           "b-^", "r-^"),
            ("L/D vs α",         ab, LDb,  ao, LDo,  "C_L / C_D",     "b-o", "r-o"),
            ("dCM/dα vs α",      ab, dCMb, ao, dCMo, "dC_M / dα",     "b--o","r--o"),
        ]

        STYLE = dict(linewidth=1.8, markersize=4)
        ZERO  = dict(color="#555566", linewidth=0.8, linestyle="--")

        for ax, (title, xa, ya, xo, yo, ylabel, sfmt_b, sfmt_o) in zip(axes, plot_cfg):
            ax.set_facecolor("#161b22")
            ax.tick_params(colors="#c9d1d9", labelsize=7)
            for sp in ax.spines.values():
                sp.set_edgecolor("#30363d")
            ax.grid(True, color="#30363d", linewidth=0.5)
            ax.axhline(0, **ZERO)
            ax.axvline(0, **ZERO)

            ax.plot(xa, ya, sfmt_b, label="Baseline", color="#388bfd", **STYLE)
            ax.plot(xo, yo, sfmt_o, label="Optimized", color="#f85149", **STYLE)

            ax.set_xlabel("α (deg)", color="#c9d1d9", fontsize=8)
            ax.set_ylabel(ylabel,    color="#c9d1d9", fontsize=8)
            ax.set_title(title,      color="#f5f7fa", fontsize=9, fontweight="bold",
                         pad=5)

            leg = ax.legend(fontsize=7, framealpha=0.3,
                            facecolor="#1c2128", edgecolor="#30363d",
                            labelcolor="#c9d1d9", loc="best")
            leg.set_title(mach_lbl,
                          prop={"size": 7, "weight": "normal"})
            leg.get_title().set_color("#9aa4b2")

        fig.suptitle("Aerodynamic Coefficient Sweep  —  Baseline vs Optimized",
                     color="#f5f7fa", fontsize=11, fontweight="bold", y=0.975)

        self._sweep_fig = fig
        self._embed_sweep_figure(fig)

    def _embed_sweep_figure(self, fig):
        for w in self._sweep_area.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self._sweep_area)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=BG_DARK)
        widget.pack(fill="both", expand=True)
        self._sweep_canvas_obj = canvas

    def _save_sweep_png(self):
        if self._sweep_fig is None:
            messagebox.showinfo("Nothing to save",
                "Run the alpha sweep first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save sweep plots as PNG",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")])
        if path:
            self._sweep_fig.savefig(
                path, dpi=150, bbox_inches="tight",
                facecolor=self._sweep_fig.get_facecolor())
            messagebox.showinfo("Saved", f"Saved to:\n{path}")



if __name__ == "__main__":
    app = DatcomApp()
    app.mainloop()
