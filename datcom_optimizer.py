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

REF_SREF_FORCED = 10.0
CM_SREF_SCALE = 1000.0

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


SURFACE_CONFIG = {
    "Wing": {
        "label": "Wing",
        "base": 1,
        "required_single": [1, 3, 5, 7, 8, 10],
        "required_two":    [2, 4, 6, 9],
    },
    "Vertical Tail": {
        "label": "V-Tail",
        "base": 11,
        "required_single": [11, 13, 15, 17, 18, 20],
        "required_two":    [12, 14, 16, 19],
    },
    "Horizontal Tail": {
        "label": "H-Tail",
        "base": 21,
        "required_single": [21, 23, 25, 27, 28, 30],
        "required_two":    [22, 24, 26, 29],
    },
}

PARAM_INFO = {idx: {"label": label, "unit": unit, "scale": scale, "section": section}
              for idx, label, unit, scale, section in PARAM_DEFS}

SURFACE_PARAM_KEYWORDS = {
    1: "SAVSI",  2: "SAVSO",  3: "SSPN",   4: "SSPNOP", 5: "DHDADI",
    6: "DHDADO", 7: "TWISTA", 8: "CHRDR",  9: "CHRDBP", 10: "CHRDTP",
    11: "SAVSI", 12: "SAVSO", 13: "SSPN", 14: "SSPNOP", 15: "DHDADI",
    16: "DHDADO",17: "TWISTA",18: "CHRDR",19: "CHRDBP",20: "CHRDTP",
    21: "SAVSI", 22: "SAVSO", 23: "SSPN", 24: "SSPNOP", 25: "DHDADI",
    26: "DHDADO",27: "TWISTA",28: "CHRDR",29: "CHRDBP",30: "CHRDTP",
}


LENGTH_PARAM_INDICES = {3,4,8,9,10,13,14,18,19,20,23,24,28,29,30}

def _detect_dim_system(text):
    m = re.search(r'\bDIM\s+(M|FT)\b', text, re.IGNORECASE)
    return m.group(1).upper() if m else 'FT'

def _display_unit_for_param(idx, dim_system):
    if idx in LENGTH_PARAM_INDICES:
        return 'm' if dim_system == 'M' else 'ft'
    return PARAM_INFO[idx]['unit']

def _length_scale_for_dim(dim_system):
    return 100.0

def _area_to_si(area_value, dim_system):
    return area_value if dim_system == 'M' else area_value * 0.09290304

def _velocity_to_si(velocity_value, dim_system):
    return velocity_value if dim_system == 'M' else velocity_value * 0.3048

def _pressure_to_si(pressure_value, dim_system):
    return pressure_value if dim_system == 'M' else pressure_value * 47.88025898

def _temperature_to_si(temp_value, dim_system):
    return temp_value if dim_system == 'M' else temp_value * (5.0 / 9.0)

def _weight_to_si(weight_value, dim_system):
    return weight_value if dim_system == 'M' else weight_value * 4.4482216152605

def _extract_surface_blocks(text):
    pattern = re.compile(r'\$(WGPLNF|VTPLNF|HTPLNF)\b(.*?)\$', re.IGNORECASE | re.DOTALL)
    blocks = {'WGPLNF': [], 'VTPLNF': [], 'HTPLNF': []}
    for name, body in pattern.findall(text):
        assigns = {}
        for key, val in re.findall(r'([A-Z][A-Z0-9()]*?)\s*=\s*([^,$]+)', body, re.IGNORECASE):
            k = key.upper().strip()
            try:
                assigns[k] = float(val.strip())
            except ValueError:
                continue
        blocks[name.upper()].append(assigns)
    return blocks


# ── Custom Checkbox widget ────────────────────────────────────────────
class CheckBox(tk.Canvas):
    """Fully custom-drawn checkbox. Works on any dark/light theme."""
    SZ = 17

    def __init__(self, parent, variable, bg=BG_CARD, enabled=True, **kw):
        super().__init__(parent, width=self.SZ, height=self.SZ,
                         bg=bg, highlightthickness=0,
                         cursor="hand2" if enabled else "arrow", **kw)
        self._var = variable
        self._enabled = enabled
        self._draw()
        self._var.trace_add("write", lambda *_: self._draw())
        self.bind("<Button-1>", self._on_click)

    def _on_click(self, _event=None):
        if self._enabled:
            self._var.set(not self._var.get())

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        self.configure(cursor="hand2" if self._enabled else "arrow")
        self._draw()

    def _draw(self):
        self.delete("all")
        n = self.SZ
        outline = "#5a7a9a" if self._enabled else BORDER
        fill = "#1e2d3d" if self._enabled else BG_INPUT
        tick = "#38d8f0" if self._enabled else TEXT_DIM
        self.create_rectangle(1, 1, n-2, n-2, outline=outline, fill=fill, width=1)
        if self._var.get():
            p = 3
            self.create_line(p, n//2, n//2-1, n-p-1, fill=tick, width=2, capstyle="round")
            self.create_line(n//2-1, n-p-1, n-p, p, fill=tick, width=2, capstyle="round")


# ── DATCOM file parser ────────────────────────────────────────────────
def parse_for005(filepath):
    try:
        with open(filepath, 'r') as f:
            text = f.read()

        dim_system = _detect_dim_system(text)
        blocks = _extract_surface_blocks(text)

        def find_scalar(kw):
            m = re.search(rf'\b{re.escape(kw)}\s*=\s*([^,\n\r$]+)', text, re.IGNORECASE)


            if not m:
                return None
            try:
                return float(m.group(1).strip())
            except Exception:
                return None

        alschd = find_scalar('ALSCHD(1)')
        if alschd is None:
            alschd = find_scalar('ALSCHD')
        if alschd is None:
            alschd = 5.0
        zv = find_scalar('ZV')
        if zv is None:
            zv = 0.017 if dim_system == 'M' else 0.0558
        wt = find_scalar('WT')
        if wt is None:
            wt = 26500.0
        zh_raw = find_scalar('ZH')
        if zh_raw is None:
            zh_raw = 0.366 if dim_system == 'M' else 1.2008

        surface_types = {}
        missing_errors = []
        block_map = {
            'Wing': blocks['WGPLNF'][0] if blocks['WGPLNF'] else {},
            'Vertical Tail': blocks['VTPLNF'][0] if blocks['VTPLNF'] else {},
            'Horizontal Tail': blocks['HTPLNF'][0] if blocks['HTPLNF'] else {},
        }

        essential_single = {'SAVSI', 'SSPN', 'TWISTA', 'CHRDR', 'CHRDTP'}
        essential_two = {'SAVSO', 'SSPNOP', 'CHRDBP'}

        for section_name, cfg in SURFACE_CONFIG.items():
            surf = block_map.get(section_name, {})
            if not surf:
                missing_errors.append(f"{cfg['label']}: missing ${'WGPLNF' if section_name=='Wing' else 'VTPLNF' if section_name=='Vertical Tail' else 'HTPLNF'}$ block")
                surface_types[section_name] = 'single'
                continue

            has_two = (
                ('SAVSO' in surf and abs(surf.get('SAVSO', 0.0)) > 1e-9) or
                ('CHRDBP' in surf and abs(surf.get('CHRDBP', 0.0)) > 1e-9) or
                ('DHDADO' in surf and abs(surf.get('DHDADO', 0.0)) > 1e-9) or
                ('SSPNOP' in surf and abs(surf.get('SSPNOP', 0.0)) > 1e-9)
            )
            surface_types[section_name] = 'two' if has_two else 'single'

            for kw in essential_single:
                if kw not in surf:
                    missing_errors.append(f"{cfg['label']}: missing required input {kw}")

            if has_two:
                for kw in essential_two:
                    if kw not in surf:
                        missing_errors.append(f"{cfg['label']}: detected two-panel geometry but missing required input {kw}")

        if missing_errors:
            return [], 0.017, 26500.0, False, "\n".join(missing_errors), {}, dim_system

        length_scale = _length_scale_for_dim(dim_system)
        angle_scale = 1000.0

        def gp(surface_dict, key, default=0.0, scale=length_scale):
            return surface_dict.get(key, default) / scale

        wing = block_map['Wing']
        vtail = block_map['Vertical Tail']
        htail = block_map['Horizontal Tail']

        inp = [None] * 32
        inp[0]  = alschd / 10.0
        inp[1]  = gp(wing, 'SAVSI', 40.0, angle_scale); inp[2]  = gp(wing, 'SAVSO', 40.0, angle_scale)
        inp[3]  = gp(wing, 'SSPN', 4.572);              inp[4]  = gp(wing, 'SSPNOP', 3.2258)
        inp[5]  = gp(wing, 'DHDADI', 0.0, 100.0);      inp[6]  = gp(wing, 'DHDADO', 0.0, 100.0)
        inp[7]  = gp(wing, 'TWISTA', -3.28, 100.0);    inp[8]  = gp(wing, 'CHRDR', 4.965)
        inp[9]  = gp(wing, 'CHRDBP', 1.29);            inp[10] = gp(wing, 'CHRDTP', 1.29)
        inp[11] = gp(vtail, 'SAVSI', 47.5, angle_scale); inp[12] = gp(vtail, 'SAVSO', 47.5, angle_scale)
        inp[13] = gp(vtail, 'SSPN', 3.1968);           inp[14] = gp(vtail, 'SSPNOP', 2.568)
        inp[15] = gp(vtail, 'DHDADI', 0.0, 100.0);     inp[16] = gp(vtail, 'DHDADO', 0.0, 100.0)
        inp[17] = gp(vtail, 'TWISTA', 0.0, 100.0);     inp[18] = gp(vtail, 'CHRDR', 3.088)
        inp[19] = gp(vtail, 'CHRDBP', 1.2);            inp[20] = gp(vtail, 'CHRDTP', 1.206)
        inp[21] = gp(htail, 'SAVSI', 40.0, angle_scale); inp[22] = gp(htail, 'SAVSO', 40.0, angle_scale)
        inp[23] = gp(htail, 'SSPN', 2.808);            inp[24] = gp(htail, 'SSPNOP', 1.7686)
        inp[25] = gp(htail, 'DHDADI', -1.0, 100.0);    inp[26] = gp(htail, 'DHDADO', -1.0, 100.0)
        inp[27] = gp(htail, 'TWISTA', 0.0, 100.0);     inp[28] = gp(htail, 'CHRDR', 3.328)
        inp[29] = gp(htail, 'CHRDBP', 0.9497);         inp[30] = gp(htail, 'CHRDTP', 0.9497)
        inp[31] = zh_raw / length_scale

        return inp, zv, wt, True, '', surface_types, dim_system
    except Exception as e:
        import traceback
        return [], 0.017, 26500.0, False, traceback.format_exc(), {}, 'FT'


# ── Write inp vector to a dat file ───────────────────────────────────
def write_inp_to_dat(inp, dat_path, fixed_zv, zv_orig, force_sref_manipulation=False):
    with open(dat_path, 'r') as f:
        text = f.read()

    dim_system = _detect_dim_system(text)
    length_scale = _length_scale_for_dim(dim_system)

    def fmt(v):
        return f"{v:.5f}"

    replacements = {
        'SAVSI': [inp[1]*1000, inp[11]*1000, inp[21]*1000],
        'SAVSO': [inp[2]*1000, inp[12]*1000, inp[22]*1000],
        'SSPN': [inp[3]*length_scale,  inp[13]*length_scale,  inp[23]*length_scale],
        'SSPNOP':[inp[4]*length_scale,  inp[14]*length_scale,  inp[24]*length_scale],
        'DHDADI':[inp[5]*100,  inp[15]*100,  inp[25]*100],
        'DHDADO':[inp[6]*100,  inp[16]*100,  inp[26]*100],
        'TWISTA':[inp[7]*100,  inp[17]*100,  inp[27]*100],
        'CHRDR': [inp[8]*length_scale,  inp[18]*length_scale,  inp[28]*length_scale],
        'CHRDBP':[inp[9]*length_scale,  inp[19]*length_scale,  inp[29]*length_scale],
        'CHRDTP':[inp[10]*length_scale, inp[20]*length_scale,  inp[30]*length_scale],
    }

    block_surface_index = {'WGPLNF': 0, 'VTPLNF': 1, 'HTPLNF': 2}

    def _replace_block(match):
        block_name = match.group(1).upper()
        body = match.group(2)
        surf_idx = block_surface_index.get(block_name)
        if surf_idx is None:
            return match.group(0)
        for key, vals in replacements.items():
            val = vals[surf_idx]
            body = re.sub(rf'(\b{key}\s*=\s*)([^,$]+)', rf'\g<1>{fmt(val)}', body, flags=re.IGNORECASE)
        return f'${block_name}{body}$'

    text = re.sub(r'\$(WGPLNF|VTPLNF|HTPLNF)\b(.*?)\$', _replace_block, text, flags=re.IGNORECASE | re.DOTALL)

    if force_sref_manipulation:
        text = re.sub(r'(\bSREF\s*=\s*)([^,\n\r$]+)', rf'\g<1>{fmt(REF_SREF_FORCED)}', text, flags=re.IGNORECASE)

    if not fixed_zv:
        zh_val = inp[31] * length_scale
        text = re.sub(r'(\bZH\s*=\s*)([^,\n\r$]+)', rf'\g<1>{fmt(zh_val)}', text, flags=re.IGNORECASE)



    with open(dat_path, 'w') as f:
        f.write(text)


# ── Read datcom.out ───────────────────────────────────────────────────
def _token_reads_as_zero(token):
    if token is None:
        return False
    tok = str(token).strip().upper().replace("D", "E")
    return bool(re.fullmatch(r"[-+]?0(?:\.0+)?(?:E[-+]?\d+)?", tok))


def read_datcom_out(out_path, apply_sref_manipulation=False, dim_system='FT'):
    with open(out_path, 'r') as f:
        lines = f.readlines()
    words = [l.split() for l in lines]

    theoretical_wing_area = None
    reference_area = None
    raw_cl = raw_cd = raw_cm = 1.0
    raw_cl_token = raw_cd_token = raw_cm_token = None
    level_flight_cl = None
    velocity = pressure = temperature = 288.15

    for i, line in enumerate(lines):
        row = words[i]
        # Primary reference dimensions table
        if reference_area is None and re.search(r'FLIGHT CONDITIONS', line, re.IGNORECASE):
            for k in range(i + 1, min(i + 8, len(words))):
                if words[k] and words[k][0] == '0' and len(words[k]) >= 7:
                    try:
                        velocity = float(words[k][3])
                        pressure = float(words[k][4])
                        temperature = float(words[k][5])
                        reference_area = float(words[k][7])
                        break
                    except Exception:
                        pass

        if level_flight_cl is None:
            m_lvl = re.search(r'LEVEL\s+FLIGHT\s+LIFT\s+COEFFICIENT\s*=\s*([\-+0-9.DEde]+)', line, re.IGNORECASE)
            if m_lvl:
                try:
                    level_flight_cl = float(m_lvl.group(1).replace('D', 'E').replace('d', 'e'))
                except Exception:
                    pass

        # Theoretical wing area: only take the WING block, not HT/VT
        if theoretical_wing_area is None and re.search(r'^0\s+WING\s*$', line.strip(), re.IGNORECASE):
            for k in range(i + 1, min(i + 6, len(lines))):
                if re.search(r'TOTAL\s+THEORITICAL', lines[k], re.IGNORECASE):
                    try:
                        vals = re.findall(r'[\-+]?\d+(?:\.\d+)?(?:[ED][\-+]?\d+)?', lines[k + 1], re.IGNORECASE)
                        if vals:
                            theoretical_wing_area = float(vals[0].replace('D', 'E').replace('d', 'e'))
                            break
                    except Exception:
                        pass

        for j, w in enumerate(row):
            if w == "CL":
                try:
                    raw_cl_token = words[i+2][j-1]
                    raw_cl = float(raw_cl_token)
                except Exception:
                    pass
            if w == "CD":
                try:
                    raw_cd_token = words[i+2][j-1]
                    raw_cd = float(raw_cd_token)
                except Exception:
                    pass
            if w == "CM":
                try:
                    raw_cm_token = words[i+2][j-1]
                    raw_cm = float(raw_cm_token)
                except Exception:
                    pass

    if reference_area is None:
        reference_area = REF_SREF_FORCED if apply_sref_manipulation else 1.0
    if theoretical_wing_area is None:
        theoretical_wing_area = reference_area

    if apply_sref_manipulation:
        area_den = max(theoretical_wing_area, 1e-12)
        scale_ref = REF_SREF_FORCED / area_den
        scale_cm = CM_SREF_SCALE / area_den
        CL = raw_cl * scale_ref
        CD = raw_cd * scale_ref
        CM = raw_cm * scale_cm
    else:
        CL, CD, CM = raw_cl, raw_cd, raw_cm

    # rCL is recomputed later from theoretical wing area using
    # current flight condition and weight with unit-consistent SI values.
    rCL = None

    pressure_si    = _pressure_to_si(pressure, dim_system)
    temperature_si = _temperature_to_si(temperature, dim_system)
    density = pressure_si / (287.058 * temperature_si)
    zero_fields = []
    if _token_reads_as_zero(raw_cl_token):
        zero_fields.append("CL")
    if _token_reads_as_zero(raw_cd_token):
        zero_fields.append("CD")
    if _token_reads_as_zero(raw_cm_token):
        zero_fields.append("CM")

    return {
        "CL": CL,
        "CD": CD,
        "CM": CM,
        "rCL": rCL,
        "theoretical_wing_area": theoretical_wing_area,
        "reference_area": reference_area,
        "velocity": velocity,
        "density": density,
        "level_flight_cl": level_flight_cl,
        "raw_CL": raw_cl,
        "raw_CD": raw_cd,
        "raw_CM": raw_cm,
        "raw_CL_token": raw_cl_token,
        "raw_CD_token": raw_cd_token,
        "raw_CM_token": raw_cm_token,
        "zero_detected": bool(zero_fields),
        "zero_fields": zero_fields,
        "sref_manipulation_applied": bool(apply_sref_manipulation),
    }


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
    import re

    results = []
    velocity = pressure = temperature = None

    with open(out_path, 'r', errors='replace') as f:
        lines = f.readlines()

    def _try_parse_vel_block(start_idx):
        """
        VELOCITY başlığından sonraki birkaç satır içinde
        sayısal veri satırını bulmaya çalışır.
        Beklenen veri satırı mantığı:
            [0] MACH VELOCITY PRESSURE TEMPERATURE ...
        veya
            MACH VELOCITY PRESSURE TEMPERATURE ...
        """
        for j in range(start_idx + 1, min(start_idx + 8, len(lines))):
            raw = lines[j].strip()
            if not raw:
                continue

            tok = raw.split()
            if not tok:
                continue

            # İlk token '0' section marker olabilir
            s = 1 if tok[0] == '0' else 0

            # En az MACH + VELOCITY + PRESSURE + TEMPERATURE olmalı
            if len(tok) < s + 4:
                continue

            try:
                mach = float(tok[s + 0])   # kullanılmasa da satır doğrulaması için
                vel  = float(tok[s + 1])
                pres = float(tok[s + 2])
                temp = float(tok[s + 3])
                return vel, pres, temp
            except (ValueError, IndexError):
                continue

        return None, None, None

    in_table = False

    for i, line in enumerate(lines):
        sline = line.strip()

        # VELOCITY / PRESSURE / TEMPERATURE ilk uygun yerden alınsın
        if velocity is None and re.search(r'\bVELOCITY\b', line, re.IGNORECASE):
            vel, pres, temp = _try_parse_vel_block(i)
            if vel is not None:
                velocity, pressure, temperature = vel, pres, temp

        # Doğru aero coeff tablosunu yakala:
        # ALPHA, CD, CL, CM içermeli
        # ama EPSLON/QINF/CLQ/CMQ gibi başka tablolar olmamalı
        if (re.search(r'\bALPHA\b', sline) and
                re.search(r'\bCD\b', sline) and
                re.search(r'\bCL\b', sline) and
                re.search(r'\bCM\b', sline) and
                not re.search(r'\bEPSLON\b|\bQINF\b|\bCLQ\b|\bCMQ\b', sline)):
            in_table = True
            continue

        if not in_table:
            continue

        # Tablo içi
        if not sline or sline == '0':
            continue

        tokens = sline.split()
        try:
            alpha = float(tokens[0])
            CD    = float(tokens[1])
            CL    = float(tokens[2])
            CM    = float(tokens[3])
            results.append({
                'alpha': alpha,
                'CL': CL,
                'CD': CD,
                'CM': CM
            })
        except (ValueError, IndexError):
            # numerik olmayan satır geldiyse tablo bitmiş kabul et
            in_table = False

    if velocity is None or pressure is None or temperature is None:
        raise ValueError(
            'VELOCITY / PRESSURE / TEMPERATURE could not be parsed from datcom.out during sweep.'
        )

    if alpha_list is not None:
        expected = [float(a) for a in alpha_list]
        parsed = [row['alpha'] for row in results]

        if len(parsed) != len(expected):
            raise ValueError(
                f"Sweep parse mismatch: expected {len(expected)} alpha rows, parsed {len(parsed)}."
            )

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
        self.dim_system       = 'FT'
        self._running         = False
        self._iter_count      = 0
        self._best_score      = float('inf')
        self._initial_inp     = []
        self._final_inp       = []   # set after optimization
        self._sref_manipulation_enabled = False
        self._sref_manipulation_decided = False
        self._cbarr_explicit = False

        # Aero Sweep tab state
        self._sweep_running   = False
        self._sweep_data_base = None   # list of (alpha, CD, CL, CM) for baseline
        self._sweep_data_opt  = None   # list of (alpha, CD, CL, CM) for optimized

        self.param_enabled = {idx: tk.BooleanVar(value=True) for idx,*_ in PARAM_DEFS}
        self.param_lo      = {idx: tk.StringVar() for idx,*_ in PARAM_DEFS}
        self.param_hi      = {idx: tk.StringVar() for idx,*_ in PARAM_DEFS}
        self.param_cur     = {idx: tk.StringVar(value="-") for idx,*_ in PARAM_DEFS}
        self.param_available = {idx: True for idx,*_ in PARAM_DEFS}
        self.surface_panel_type = {name: "two" for name in SURFACE_CONFIG}
        self._param_widgets = {}

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
        self._param_widgets = {}
        for w in f.winfo_children():
            w.destroy()

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

                panel_var = self.surface_panel_type.get(section, "two")
                panel_text = f"Detected geometry: {panel_var.title()} Panel"
                tk.Label(sr, text=panel_text, bg=BG_DARK, fg=TEXT_DIM,
                         font=self.FSMALL).pack(side="right", padx=8)

            bg = BG_CARD if idx%2==0 else BG_PANEL
            row = tk.Frame(f, bg=bg); row.pack(fill="x", pady=1)

            cb = CheckBox(row, self.param_enabled[idx], bg=bg, enabled=self.param_available.get(idx, True))
            cb.pack(side="left", padx=(10, 4), pady=4)

            lbl = tk.Label(row, text=label, bg=bg,
                           fg=TEXT_PRI if self.param_available.get(idx, True) else TEXT_DIM,
                           font=self.FBODY, width=34, anchor="w")
            lbl.pack(side="left", padx=4)

            cur_lbl = tk.Label(row, textvariable=self.param_cur[idx], bg=bg,
                               fg=ACCENT3 if self.param_available.get(idx, True) else TEXT_DIM,
                               font=self.FBODY, width=16, anchor="w")
            cur_lbl.pack(side="left", padx=4)

            lo_entry = tk.Entry(row, textvariable=self.param_lo[idx], bg=BG_INPUT, fg=TEXT_PRI,
                                insertbackground=TEXT_PRI, relief="flat",
                                font=self.FBODY, width=13)
            lo_entry.pack(side="left", padx=4, ipady=4)

            hi_entry = tk.Entry(row, textvariable=self.param_hi[idx], bg=BG_INPUT, fg=TEXT_PRI,
                                insertbackground=TEXT_PRI, relief="flat",
                                font=self.FBODY, width=13)
            hi_entry.pack(side="left", padx=4, ipady=4)

            unit_lbl = tk.Label(row, text=_display_unit_for_param(idx, self.dim_system), bg=bg,
                                fg=TEXT_DIM if self.param_available.get(idx, True) else BORDER,
                                font=self.FSMALL, width=6)
            unit_lbl.pack(side="left")

            self._param_widgets[idx] = {
                "row": row,
                "checkbox": cb,
                "label": lbl,
                "current": cur_lbl,
                "lo": lo_entry,
                "hi": hi_entry,
                "unit": unit_lbl,
                "bg": bg,
            }

            self._apply_param_widget_state(idx)

    def _apply_param_widget_state(self, idx):
        if idx not in self._param_widgets:
            return
        widgets = self._param_widgets[idx]
        available = self.param_available.get(idx, True)
        widgets["checkbox"].set_enabled(available)
        if not available:
            self.param_enabled[idx].set(False)
        state = "normal" if available else "disabled"
        widgets["lo"].config(state=state,
                             disabledbackground=BG_INPUT,
                             disabledforeground=TEXT_DIM)
        widgets["hi"].config(state=state,
                             disabledbackground=BG_INPUT,
                             disabledforeground=TEXT_DIM)
        widgets["label"].config(fg=TEXT_PRI if available else TEXT_DIM)
        widgets["current"].config(fg=ACCENT3 if available else TEXT_DIM)
        widgets["unit"].config(fg=TEXT_DIM if available else BORDER)

    def _sync_param_availability(self):
        for idx in self.param_available:
            self.param_available[idx] = True

        for section_name, cfg in SURFACE_CONFIG.items():
            if self.surface_panel_type.get(section_name, "two") == "single":
                for idx in cfg["required_two"]:
                    self.param_available[idx] = False

        if self._param_widgets:
            for idx in self._param_widgets:
                self._apply_param_widget_state(idx)

    def _set_initial_percent_bounds(self, pct=0.05):
        if not self.inp_vals:
            return
        for (idx, _label, _unit, scale, _section) in PARAM_DEFS:
            if idx >= len(self.inp_vals):
                continue
            if not self.param_available.get(idx, True):
                self.param_lo[idx].set("")
                self.param_hi[idx].set("")
                continue

            val = self.inp_vals[idx]
            if abs(val) < 1e-12:
                if idx in DEFAULT_BOUNDS:
                    lo, hi = DEFAULT_BOUNDS[idx]
                else:
                    lo, hi = -pct, pct
            else:
                delta = abs(val) * pct
                lo = min(val - delta, val + delta)
                hi = max(val - delta, val + delta)

            self.param_lo[idx].set(f"{lo * scale:.4f}")
            self.param_hi[idx].set(f"{hi * scale:.4f}")

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
        for idx, bv in self.param_enabled.items():
            if self.param_available.get(idx, True):
                bv.set(v)
            else:
                bv.set(False)

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
        inp, zv, wt, ok, err, surface_types, dim_system = parse_for005(path)
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
        self.surface_panel_type.update(surface_types)
        self.dim_system   = dim_system
        self._cbarr_explicit = self._input_has_explicit_cbarr(path)
        self._sync_param_availability()
        self._build_param_rows()

        with open(path) as f:
            self.preview.delete("1.0","end")
            self.preview.insert("end", f.read())

        self.alschd_label.config(text=f"ALSCHD = {inp[0]*10:.2f}  deg")

        for (idx,label,unit,scale,_) in PARAM_DEFS:
            disp_unit = _display_unit_for_param(idx, self.dim_system)
            self.param_cur[idx].set(f"{inp[idx]*scale:.4f} {disp_unit}")
        self._set_initial_percent_bounds(0.05)

        cbarr_note = "\n\nWARNING: Explicit CBARR detected in input.\nCM area-only scaling is not valid in this case, so optimization/sweep with scaling is blocked." if self._cbarr_explicit else ""
        messagebox.showinfo("Loaded",
            f"File parsed successfully.\n32 parameters read.\n"
            f"DIM = {self.dim_system}\n"
            f"WT = {wt:.1f} {'N' if self.dim_system == 'M' else 'lbf'}\n\n"
            f"Original file will NOT be modified during optimization.\n"
            f"A temporary working copy is used for each DATCOM evaluation."
            f"{cbarr_note}")

    # ── Logging ───────────────────────────────────────────────────────
    def _log(self, msg, tag="info"):
        self.log.insert("end", msg+"\n", tag)
        self.log.see("end")

    def _clear_log(self):
        self.log.delete("1.0","end")
    def _extract_current_sref_from_file(self, dat_path):
        try:
            with open(dat_path, "r") as f:
                txt = f.read()
            m = re.search(r'\bSREF\s*=\s*([^,\n\r$]+)', txt, re.IGNORECASE)
            if m:
                return float(m.group(1).strip())
        except Exception:
            pass
        return REF_SREF_FORCED

    def _input_has_explicit_cbarr(self, dat_path):
        try:
            with open(dat_path, "r") as f:
                txt = f.read()
            return bool(re.search(r'\bCBARR\s*=', txt, re.IGNORECASE))
        except Exception:
            return False

    def _ask_sref_manipulation(self, zero_fields):
        fields_txt = ", ".join(zero_fields) if zero_fields else "CL/CD/CM"
        result = {"apply": False}
        done = threading.Event()

        def _prompt():
            try:
                msg = (
                    f"DATCOM çıktısında şu katsayı(lar) 0.000 okundu: {fields_txt}.\n\n"
                    "Bu bir çözünürlük / yuvarlama problemi olabilir.\n"
                    "SREF manipülasyonu uygulansın mı?\n\n"
                    "Evet -> SREF=10 zorlanır ve eski /10 /1000 ölçek mantığı uygulanır.\n"
                    "Hayır -> kullanıcı SREF'i aynen korunur."
                )
                result["apply"] = messagebox.askyesno("SREF Manipulation", msg)
            finally:
                done.set()

        self.after(0, _prompt)
        done.wait()
        return bool(result["apply"])


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
        if self._cbarr_explicit:
            messagebox.showerror(
                "CBARR Detected",
                "CM area-only scaling is not valid when CBARR is explicitly defined in the DATCOM input.\n\n"
                "Please remove CBARR from the input or disable/replace the current CM scaling approach."
            )
            return
        if self._running: return
        self._running    = True
        self._iter_count = 0
        self._best_score = float('inf')
        self._sref_manipulation_enabled = False
        self._sref_manipulation_decided = False
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
        self._cleanup_datcom_outputs()
        self.after(0, self.prog.stop)
        self.after(0, lambda: self.status_lbl.config(text=msg))
        self.after(0, lambda: self.run_btn.config(state="normal"))

    def _cleanup_datcom_outputs(self):
        work_dir = os.path.dirname(self.datcom_exe.get().strip()) if self.datcom_exe.get().strip() else os.getcwd()
        for name in ("datcom.out", "for0013.dat", "for0014.dat"):
            try:
                fp = os.path.join(work_dir, name)
                if os.path.exists(fp):
                    os.remove(fp)
            except Exception:
                pass

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
        both(f"  WT           : {wt:.1f} N")
        both(f"  ALSCHD       : {inp[0]*10:.2f} deg  (fixed, not optimized)")
        both(f"  Cost expr    : {cost_expr}")
        both("-"*70)

        native_sref = self._extract_current_sref_from_file(dat_path)
        _wa_si = _area_to_si(max(native_sref, 1e-12), self.dim_system)
        _wt_si = _weight_to_si(wt, self.dim_system)
        _rCL = 2*_wt_si/(_wa_si*1.225*102.0**2) if _wa_si else 1e6
        both(f"  rCL estimate : {_rCL:.4f}  (rough estimate using input SREF)")
        if _rCL > 1.0:
            both("  NOTE: hard lift constraint active -> if CL < rCL, score = 1e6", "warn")
        both("-"*70)

        # Collect active params
        active_idx, active_lo, active_hi = [], [], []
        for (idx,label,unit,scale,_) in PARAM_DEFS:
            if self.param_available.get(idx, True) and self.param_enabled[idx].get():
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
        sc_b, cl_b, cd_b, cm_b, rcl_b, s_theoretical_b = self._evaluate(
            list(inp), zv, wt, dat_path, tmp_dat, exe_dir, cost_expr, fixed_zv)
        both(f"\n  Initial eval:  score={sc_b:.5f}  CL={cl_b:.4f}  CD={cd_b:.4f}  CM={cm_b:.4f}  rCL={rcl_b:.4f}  S_theoretical={s_theoretical_b:.4f}", "info")
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
                score, CL, CD, CM, rCL, s_theoretical = self._evaluate(
                    full, zv, wt, dat_path, tmp_dat, exe_dir, cost_expr, fixed_zv)
                it = self._iter_count
                self.after(0, lambda n=it: (
                    self.iter_lbl.config(text=f"Iter: {n}"),
                    self._sv['iter'].set(str(n))))
                if score < pass_best[0]:
                    pass_best[0] = score
                    both(f"  Pass {pi+1} | Iter {pass_call[0]:4d} | "
                         f"score={score:12.5f} | "
                         f"CL={CL:.4f}  CD={CD:.4f}  CM={CM:.5f}  rCL={rCL:.4f}  S_theoretical={s_theoretical:.4f}",
                         "score")
                if score < best_score:
                    best_x     = list(x)
                    best_score = score
                    best_vals  = dict(CL=CL,CD=CD,CM=CM,rCL=rCL)
                    self.after(0, lambda s=score: self._sv['score'].set(f"{s:.5f}"))
                    self.after(0, lambda bv=dict(best_vals): [
                        self._sv['cl' ].set(f"{bv['CL']:.4f}"),
                        self._sv['cd' ].set(f"{bv['CD']:.4f}"),
                        self._sv['cm' ].set(f"{bv['CM']:.4f}"),
                        self._sv['rcl'].set(f"{bv['rCL']:.4f}"),
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
        sc_a, cl_a, cd_a, cm_a, rcl_a, s_theoretical_a = self._evaluate(
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
        exe_path = self.datcom_exe.get().strip()
        exe = exe_path if exe_path else os.path.join(exe_dir, "digital_DATCOM.exe")
        if not os.path.exists(exe):
            raise FileNotFoundError(f"digital_DATCOM.exe not found: {exe}")

        out_path = os.path.join(exe_dir, "datcom.out")
        work_dat = os.path.join(exe_dir, "for005.dat")
        bak_dat = os.path.join(exe_dir, "for005._gui_backup.dat")
        had_original = os.path.exists(work_dat)
        native_sref = self._extract_current_sref_from_file(orig_dat)

        def _run_datcom_once(force_sref_manipulation):
            shutil.copy2(orig_dat, tmp_dat)
            write_inp_to_dat(inp, tmp_dat, fixed_zv, zv, force_sref_manipulation=force_sref_manipulation)

            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except Exception:
                pass

            try:
                if had_original:
                    shutil.copy2(work_dat, bak_dat)
                shutil.copy2(tmp_dat, work_dat)

                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                subprocess.Popen(exe, startupinfo=si, cwd=exe_dir)

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

                return read_datcom_out(out_path, apply_sref_manipulation=force_sref_manipulation, dim_system=self.dim_system)
            finally:
                try:
                    if had_original and os.path.exists(bak_dat):
                        shutil.copy2(bak_dat, work_dat)
                        os.remove(bak_dat)
                    elif (not had_original) and os.path.exists(work_dat):
                        os.remove(work_dat)
                except Exception:
                    pass

        result = _run_datcom_once(self._sref_manipulation_enabled)
        if (not self._sref_manipulation_enabled) and result.get("zero_detected", False) and (not self._sref_manipulation_decided):
            self._sref_manipulation_decided = True
            self._sref_manipulation_enabled = self._ask_sref_manipulation(result.get("zero_fields", []))
            if self._sref_manipulation_enabled:
                result = _run_datcom_once(True)

        CL = result["CL"]
        CD = result["CD"]
        CM = result["CM"]
        theoretical_wing_area = result["theoretical_wing_area"]
        reference_area = result.get("reference_area", native_sref)
        velocity = result["velocity"]
        density = result["density"]

        if self._cbarr_explicit:
            raise ValueError(
                "CM area-only scaling is not valid when CBARR is explicitly defined in the DATCOM input."
            )

        # Apply geometric-consistency scaling so that DATCOM coefficients,
        # originally normalized by the fixed input SREF, are evaluated with
        # respect to the current theoretical wing area of the iterated geometry.
        if theoretical_wing_area and reference_area:
            area_ratio = reference_area / max(theoretical_wing_area, 1e-12)
            CL *= area_ratio
            CD *= area_ratio
            CM *= area_ratio

        # rCL is always recomputed from the current theoretical wing area.
        # Units are normalized to SI so both DIM M and DIM FT cases stay correct:
        #   rCL = 2*W / (rho * V^2 * S_theoretical)
        wing_area_si = _area_to_si(theoretical_wing_area, self.dim_system)
        velocity_si = _velocity_to_si(velocity, self.dim_system)
        wt_si = _weight_to_si(wt, self.dim_system)
        den = wing_area_si * density * (velocity_si ** 2)
        rCL = 2*wt_si/den if den > 1e-12 else 1e6
        used_sref = REF_SREF_FORCED if result.get("sref_manipulation_applied", False) else reference_area
        self._last_eval_meta = {
            "forced_sref": REF_SREF_FORCED,
            "used_sref": used_sref,
            "reference_area": reference_area,
            "theoretical_wing_area": theoretical_wing_area,
            "wing_area": theoretical_wing_area,
            "velocity": velocity,
            "density": density,
            "level_flight_cl": result.get("level_flight_cl"),
            "area_ratio": (reference_area / max(theoretical_wing_area, 1e-12)) if theoretical_wing_area else 1.0,
            "rCL": rCL,
            "sref_manipulation_applied": result.get("sref_manipulation_applied", False),
            "zero_detected": result.get("zero_detected", False),
            "zero_fields": result.get("zero_fields", []),
        }

        try:
            base = float(eval(cost_expr, {"__builtins__":{}}, {
                "CL":CL,"CD":CD,"CM":CM,"rCL":rCL,
                "wing_area":theoretical_wing_area,"theoretical_wing_area":theoretical_wing_area,
                "sref":used_sref,"forced_sref":REF_SREF_FORCED,
                "velocity":velocity,
                "density":density,"weight":wt,"abs":abs,"math":math}))
        except:
            base = 1e6

        if CL < rCL:
            score = 1e6
        else:
            score = base
        return score, CL, CD, CM, rCL, theoretical_wing_area



    # ── Tab 6: Aircraft View ──────────────────────────────────────────
    def _tab_view(self, p):
        self._view_frame    = p
        self._canvas_widget = None   # side-by-side canvas
        self._ov_canvas     = None   # overlay canvas
        self._last_fig      = None
        self._ov_fig        = None

        # ── Control bar ──────────────────────────────────────────────
        ctrl = tk.Frame(p, bg=BG_CARD); ctrl.pack(fill="x", padx=20, pady=8)
        self._btn(ctrl, "Draw  Before  &  After",
                  self._draw_both, ACCENT, big=True).pack(side="left")
        self._btn(ctrl, "Save PNG...",
                  self._save_view_png, BG_PANEL).pack(side="left", padx=8)
        self._view_status = tk.Label(
            ctrl,
            text="Load a dat file (and optionally run optimization), then click Draw.",
            bg=BG_CARD, fg=TEXT_SEC, font=self.FSMALL)
        self._view_status.pack(side="left", padx=12)

        # ── Inner notebook: 2 sub-tabs ────────────────────────────────
        s = ttk.Style()
        s.configure("ViewSub.TNotebook", background=BG_DARK, borderwidth=0)
        s.configure("ViewSub.TNotebook.Tab",
                    background=BG_INPUT, foreground=TEXT_SEC,
                    padding=[10, 5], font=("Consolas", 8, "bold"))
        s.map("ViewSub.TNotebook.Tab",
              background=[("selected", BG_PANEL)],
              foreground=[("selected", TEXT_PRI)])

        vnb = ttk.Notebook(p, style="ViewSub.TNotebook")
        vnb.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        tab_sb = tk.Frame(vnb, bg=BG_DARK)   # sub-tab 1: side-by-side
        tab_ov = tk.Frame(vnb, bg=BG_DARK)   # sub-tab 2: overlay
        vnb.add(tab_sb, text="  Side-by-Side  ")
        vnb.add(tab_ov, text="  Overlay  ")

        # Side-by-side area
        self._view_area = tk.Frame(tab_sb, bg=BG_DARK)
        self._view_area.pack(fill="both", expand=True)
        tk.Label(self._view_area,
                 text="No drawing yet.\nClick 'Draw Before & After' above.",
                 bg=BG_DARK, fg=TEXT_DIM,
                 font=("Consolas", 10)).pack(expand=True)

        # Overlay area
        self._ov_area = tk.Frame(tab_ov, bg=BG_DARK)
        self._ov_area.pack(fill="both", expand=True)
        tk.Label(self._ov_area,
                 text="No overlay yet.\nClick 'Draw Before & After' above.",
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
            from aircraft_view import get_figure_sidebyside, get_figure_overlay

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

            # ── Side-by-side ──────────────────────────────────────────
            fig_sb = get_figure_sidebyside(
                tmp_before, tmp_after,
                label_left="Before (Original)",
                label_right=after_label,
                figsize=(18, 8),
                dim_system=self.dim_system)
            self._last_fig = fig_sb
            self._embed_figure(fig_sb)

            # ── Overlay ───────────────────────────────────────────────
            fig_ov = get_figure_overlay(
                tmp_before, tmp_after,
                label_before="Before (Original)",
                label_after=after_label,
                figsize=(13, 9),
                dim_system=self.dim_system)
            self._ov_fig = fig_ov
            self._embed_overlay_figure(fig_ov)

            self._view_status.config(
                text=f"Before vs After  |  "
                     f"{'Optimized result shown.' if self._final_inp else 'Run optimization to see changes.'}")
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
        self._bind_scroll_zoom(canvas, fig)

    def _embed_overlay_figure(self, fig):
        for w in self._ov_area.winfo_children(): w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self._ov_area)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=BG_DARK)
        widget.pack(fill="both", expand=True)
        self._ov_canvas = canvas
        self._bind_scroll_zoom(canvas, fig)

    @staticmethod
    def _bind_scroll_zoom(mpl_canvas, fig):
        """
        Bind:
          • Mouse-wheel  → zoom only the axis under the cursor
          • Middle-button drag (Button-2) → pan the axis under the cursor
        """
        state = {"pan_ax": None, "pan_x": None, "pan_y": None,
                 "pan_xlim": None, "pan_ylim": None}

        def _get_ax_under(event):
            widget = mpl_canvas.get_tk_widget()
            w_px = widget.winfo_width()
            h_px = widget.winfo_height()
            if w_px <= 0 or h_px <= 0:
                return None
            fig_x = event.x / w_px
            fig_y = 1.0 - event.y / h_px
            for ax in fig.get_axes():
                pos = ax.get_position()
                if (pos.x0 <= fig_x <= pos.x1 and
                        pos.y0 <= fig_y <= pos.y1):
                    return ax
            return None

        # ── Scroll zoom ───────────────────────────────────────────────
        def _on_scroll(event):
            ax = _get_ax_under(event)
            if ax is None:
                return
            factor = 0.85 if event.delta > 0 else 1.0 / 0.85
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            xc = (xlim[0] + xlim[1]) / 2
            yc = (ylim[0] + ylim[1]) / 2
            ax.set_xlim(xc - (xlim[1]-xlim[0])*factor/2,
                        xc + (xlim[1]-xlim[0])*factor/2)
            ax.set_ylim(yc - (ylim[1]-ylim[0])*factor/2,
                        yc + (ylim[1]-ylim[0])*factor/2)
            mpl_canvas.draw_idle()

        # ── Pan: press middle button ──────────────────────────────────
        def _on_press(event):
            ax = _get_ax_under(event)
            if ax is None:
                return
            state["pan_ax"]   = ax
            state["pan_x"]    = event.x
            state["pan_y"]    = event.y
            state["pan_xlim"] = ax.get_xlim()
            state["pan_ylim"] = ax.get_ylim()

        # ── Pan: drag with left button held ──────────────────────────
        def _on_drag(event):
            ax = state["pan_ax"]
            if ax is None:
                return
            widget = mpl_canvas.get_tk_widget()
            w_px = widget.winfo_width()
            h_px = widget.winfo_height()
            if w_px <= 0 or h_px <= 0:
                return

            # ax occupies a fraction of the figure — use that fraction
            # to convert pixel delta → data delta accurately
            pos = ax.get_position()
            ax_w_px = pos.width  * w_px   # ax width in pixels
            ax_h_px = pos.height * h_px   # ax height in pixels
            if ax_w_px <= 0 or ax_h_px <= 0:
                return

            xl = state["pan_xlim"]
            yl = state["pan_ylim"]
            dx_data = (xl[1] - xl[0]) / ax_w_px * (event.x - state["pan_x"])
            # screen y grows downward, data y grows upward → sign flip
            dy_data = (yl[1] - yl[0]) / ax_h_px * (event.y - state["pan_y"])
            ax.set_xlim(xl[0] - dx_data, xl[1] - dx_data)
            ax.set_ylim(yl[0] + dy_data, yl[1] + dy_data)
            mpl_canvas.draw_idle()

        # ── Pan: release middle button ────────────────────────────────
        def _on_release(event):
            state["pan_ax"] = None

        widget = mpl_canvas.get_tk_widget()
        widget.bind("<MouseWheel>",  _on_scroll)
        widget.bind("<ButtonPress-1>",   _on_press)
        widget.bind("<B1-Motion>",       _on_drag)
        widget.bind("<ButtonRelease-1>", _on_release)

    def _save_view_png(self):
        # Save whichever figure exists (prefer side-by-side)
        fig = self._last_fig or self._ov_fig
        if fig is None:
            messagebox.showinfo("Nothing to save", "Draw the aircraft first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save aircraft view as PNG",
            defaultextension=".png",
            filetypes=[("PNG image","*.png"),("All files","*.*")])
        if path:
            fig.savefig(path, dpi=150, bbox_inches='tight',
                        facecolor=fig.get_facecolor())
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
        if self._cbarr_explicit:
            messagebox.showerror(
                "CBARR Detected",
                "CM area-only scaling is not valid when CBARR is explicitly defined in the DATCOM input.\n\n"
                "Please remove CBARR from the input or disable/replace the current CM scaling approach."
            )
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

                    # Apply the same geometric-consistency scaling used during
                    # optimization so that sweep curves are directly comparable.
                    out_meta = read_datcom_out(out_path, apply_sref_manipulation=False, dim_system=self.dim_system)
                    sweep_ref_area = out_meta.get("reference_area", self._extract_current_sref_from_file(dat_path))
                    sweep_theoretical_area = out_meta.get("theoretical_wing_area", sweep_ref_area)
                    if sweep_theoretical_area and sweep_ref_area:
                        sweep_ratio = sweep_ref_area / max(sweep_theoretical_area, 1e-12)
                        for row in data:
                            row["CL"] *= sweep_ratio
                            row["CD"] *= sweep_ratio
                            row["CM"] *= sweep_ratio

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
        self._bind_scroll_zoom(canvas, fig)

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
