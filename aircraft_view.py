"""
aircraft_view.py
----------------
Python translation of drawDATCOMaircraft.m (Stepen, 2011).
Reads a DATCOM for005.dat file and draws:
  - Top view   (plan view)
  - Side view  (profile)
  - Front view (front elevation)
  - Wing / H-tail / V-tail airfoil cross-sections

Can be called standalone or embedded as a matplotlib Figure inside a
Tkinter frame via get_figure(dat_path).

Dependencies: numpy, matplotlib
"""

import re
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")           # non-interactive backend for embedding
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ── Thin airfoil profile used when no NACA string is present ─────────
_AFL_F_X = np.array([0, 0.01231, 0.04894, 0.10899,
                      0.19098, 0.29289])
_AFL_R_X = np.array([0.29289, 0.41221, 0.54601,
                      0.69098, 0.84357, 1.0])
_AFL_F_Y = np.array([0, 0.01880, 0.03522, 0.04828,
                      0.05682, 0.06001]) / 0.12
_AFL_R_Y = np.array([0.06001, 0.05755, 0.04982,
                      0.03751, 0.02128, 0.0]) / 0.12
AFL_X = np.concatenate([_AFL_F_X, _AFL_R_X])
AFL_Y = np.concatenate([_AFL_F_Y, _AFL_R_Y])     # upper half only (symmetric)

AT = 0.05   # airfoil thickness ratio for simplified profile


# ══════════════════════════════════════════════════════════════════════
# NACA airfoil generators  (translated from Stepen's MATLAB functions)
# ══════════════════════════════════════════════════════════════════════

def _x_cosine(n):
    """n points, cosine-spaced 0..1"""
    return 1 - np.cos(np.linspace(0, np.pi/2, n))


def naca4(afid: str, n=20):
    """NACA 4-series airfoil. Returns xu,yu,xl,yl."""
    m  = int(afid[0]) / 100
    p  = int(afid[1]) / 10
    t  = int(afid[2:4]) / 100
    xc = _x_cosine(n)
    yc = np.zeros(n);  gc = np.zeros(n)
    if m != 0 and p != 0:
        for i, x in enumerate(xc):
            if x <= p:
                yc[i] = (m/p**2)*(2*p*x - x**2)
                gc[i] = (m/p**2)*(2*p - 2*x)
            else:
                yc[i] = (m/(1-p)**2)*(1 - 2*p + 2*p*x - x**2)
                gc[i] = (m/(1-p)**2)*(2*p - 2*x)
    sc = np.degrees(np.arctan(gc))
    yt = 5*t*(0.2969*np.sqrt(xc) - 0.1260*xc -
              0.3516*xc**2 + 0.2843*xc**3 - 0.1015*xc**4)
    xu = xc - yt*np.sin(np.radians(sc))
    yu = yc + yt*np.cos(np.radians(sc))
    xl = xc + yt*np.sin(np.radians(sc))
    yl = yc - yt*np.cos(np.radians(sc))
    return xu, yu, xl, yl


def naca5(afid: str, n=20):
    """NACA 5-series airfoil."""
    mtable = [0.0580,0.1260,0.2025,0.2900,0.3910]
    ktable = [361.40,51.640,15.957,6.6430,3.2300]
    id2    = int(afid[1:3])
    idx    = [10,20,30,40,50].index(id2)
    m = mtable[idx]; k = ktable[idx]
    p = int(afid[1:3]) * 0.005
    t = int(afid[3:5]) / 100
    xc = _x_cosine(n)
    yc = np.zeros(n); gc = np.zeros(n)
    for i, x in enumerate(xc):
        if x <= m:
            yc[i] = (k/6)*(x**3 - 3*m*x**2 + m**2*(3-m)*x)
            gc[i] = (k/6)*(3*x**2 - 6*m*x + (3*m**2 - m**3))
        else:
            yc[i] = (k/6)*m**3*(1-x)
            gc[i] = -(k/6)*m**3
    fac = int(afid[0])/2
    yc *= fac; gc *= fac
    sc = np.degrees(np.arctan(gc))
    yt = 5*t*(0.2969*np.sqrt(xc) - 0.1260*xc -
              0.3516*xc**2 + 0.2843*xc**3 - 0.1015*xc**4)
    xu = xc - yt*np.sin(np.radians(sc))
    yu = yc + yt*np.cos(np.radians(sc))
    xl = xc + yt*np.sin(np.radians(sc))
    yl = yc - yt*np.cos(np.radians(sc))
    return xu, yu, xl, yl


def naca16(afid: str, n=20):
    """NACA 16-series airfoil."""
    cl = int(afid[2]) / 10
    t  = int(afid[3:5]) / 100
    xc_tab = np.array([0,1.25,2.5,5,7.5,10,15,20,30,40,50,
                        60,70,80,90,95,100])/100
    yc_tab = np.array([0,0.646,0.903,1.255,1.516,1.729,
                       2.067,2.332,2.709,2.927,3,2.917,
                       2.635,2.099,1.259,0.707,0.060])/600
    xc = _x_cosine(n)
    yc = np.zeros(n); gc = np.zeros(n)
    for i in range(1, n-1):
        x = xc[i]
        if x > 0 and x < 1:
            yc[i] = -(cl/(4*math.pi))*((1-x)*math.log(1-x) + x*math.log(x))
            gc[i] =  (cl/(4*math.pi))*(math.log(1-x) - math.log(x))
    yt = np.interp(xc, xc_tab, yc_tab) * (100*t)
    sc = np.degrees(np.arctan(gc))
    xu = xc - yt*np.sin(np.radians(sc))
    yu = yc + yt*np.cos(np.radians(sc))
    xl = xc + yt*np.sin(np.radians(sc))
    yl = yc - yt*np.cos(np.radians(sc))
    return xu, yu, xl, yl


def generate_naca(naca_type, naca_id):
    """Dispatch to correct NACA generator. Returns AFLX, AFLYU, AFLYL."""
    try:
        if naca_type == 1:      xu,yu,xl,yl = naca16(naca_id, 20)
        elif naca_type == 4:    xu,yu,xl,yl = naca4(naca_id, 20)
        elif naca_type == 5:    xu,yu,xl,yl = naca5(naca_id, 20)
        else:                   return None, None, None
        xu[0]=0; xu[-1]=1; xl[0]=0; xl[-1]=1
        AFLX  = np.linspace(0, 1, 21)
        AFLYU = np.interp(AFLX, xu, yu)
        AFLYL = np.interp(AFLX, xl, yl)
        return AFLX, AFLYU, AFLYL
    except Exception:
        return None, None, None


# ══════════════════════════════════════════════════════════════════════
# DATCOM file parser
# ══════════════════════════════════════════════════════════════════════

def _read_dat(filepath):
    """Read dat file, strip blank lines and comment lines (starting with *)."""
    lines = []
    with open(filepath, 'r') as f:
        for line in f:
            s = line.rstrip('\n')
            if s.strip() and not s.strip().startswith('*'):
                lines.append(s)
    return lines


def _extract_namecard(lines, name):
    """Extract all lines belonging to a $NAME ... $ namecard block."""
    result = []
    inside = False
    for line in lines:
        if not inside:
            if name in line:
                result.append(line)
                inside = (line.count('$') == 1)
        else:
            result.append(line)
            if '$' in line:
                inside = False
    return result


def _get_scalar(lines, key):
    """Extract first float following 'key=' in lines."""
    for line in lines:
        if key in line:
            idx = line.index(key) + len(key)
            m = re.search(r'[=\s]*([-\d.]+)', line[idx:])
            if m:
                try: return float(m.group(1))
                except: pass
    return None


def _get_array(lines, key, count):
    """Extract 'count' floats following 'key=' possibly spanning multiple lines."""
    result = []
    capturing = False
    start_line = None
    for i, line in enumerate(lines):
        if key in line and '=' in line:
            idx = line.index(key)
            after = line[idx + len(key):]
            after = re.sub(r'[=,$]', ' ', after)
            nums = re.findall(r'[-\d.]+', after)
            result.extend([float(x) for x in nums])
            capturing = True
            start_line = i
            continue
        if capturing:
            clean = re.sub(r'[$,]', ' ', line)
            nums = re.findall(r'[-\d.]+', clean)
            result.extend([float(x) for x in nums])
        if len(result) >= count:
            break
    return result[:count] if result else []


def parse_dat_for_view(filepath):
    """
    Parse a DATCOM for005.dat and return a geometry dict with all
    parameters needed for the three-view drawing.
    """
    lines = _read_dat(filepath)
    geo = {}

    # ── SYNTHS ────────────────────────────────────────────────────────
    synth = _extract_namecard(lines, 'SYNTHS')
    for key in ['XCG','ZCG','XW','ZW','XH','ZH','XV','ZV','XVF','ZVF']:
        v = _get_scalar(synth, key+'=')
        if v is not None:
            geo[key] = v

    # ── BODY ──────────────────────────────────────────────────────────
    body = _extract_namecard(lines, 'BODY')
    if body:
        nx = _get_scalar(body, 'NX=')
        if nx:
            nx = int(nx)
            geo['BX'] = _get_array(body, 'X(1)', nx)
            geo['BR'] = _get_array(body, 'R(1)', nx)
            geo['BZU']= _get_array(body, 'ZU(1)',nx)
            geo['BZL']= _get_array(body, 'ZL(1)',nx)
            S  = _get_array(body, 'S(1)', nx)
            P  = _get_array(body, 'P(1)', nx)
            if not geo['BR'] and P:
                geo['BR'] = [p/(2*math.pi) for p in P]
            if not geo['BR'] and S:
                geo['BR'] = [math.sqrt(s/math.pi) for s in S]

    # ── helper: parse planform block ──────────────────────────────────
    def parse_planform(block, prefix):
        d = {}
        for key, gkey in [('CHRDTP=', 'CHRDTP'),('CHRDBP=','CHRDBP'),
                           ('CHRDR=','CHRDR'),('SSPNOP=','SSPNOP'),
                           ('SSPNE=','SSPNE'),('SSPN=','SSPN'),
                           ('SAVSI=','SAVSI'),('SAVSO=','SAVSO'),
                           ('TWISTA=','TWISTA'),('DHDADI=','DHDADI'),
                           ('DHDADO=','DHDADO'),('TYPE=','TYPE'),
                           ('CHSTAT=','CHSTAT')]:
            v = _get_scalar(block, key)
            if v is not None:
                d[prefix+gkey] = v
        return d

    # ── WGPLNF ────────────────────────────────────────────────────────
    wing = _extract_namecard(lines, 'WGPLNF')
    if wing:
        geo.update(parse_planform(wing, 'W'))

    # ── HTPLNF ────────────────────────────────────────────────────────
    htp = _extract_namecard(lines, 'HTPLNF')
    if htp:
        geo.update(parse_planform(htp, 'H'))

    # ── VTPLNF ────────────────────────────────────────────────────────
    vtp = _extract_namecard(lines, 'VTPLNF')
    if vtp:
        geo.update(parse_planform(vtp, 'V'))

    # ── NACA airfoil strings ──────────────────────────────────────────
    for prefix, tag in [('W','NACA-W-'),('H','NACA-H-'),('V','NACA-V-')]:
        for line in lines:
            if tag in line:
                rest = line[line.index(tag)+len(tag):]
                try:
                    ntype = int(rest[0])
                    if ntype == 1:   nlen = 5
                    elif ntype == 6: nlen = 6 if len(rest)>5 and rest[4]=='-' else 5
                    else:            nlen = ntype
                    naca_id = rest[2:2+nlen].strip('-').strip()
                    geo[prefix+'NACA_TYPE'] = ntype
                    geo[prefix+'NACA_ID']   = naca_id
                except: pass
                break

    return geo


# ══════════════════════════════════════════════════════════════════════
# Planform geometry calculations  (direct translation of MATLAB)
# ══════════════════════════════════════════════════════════════════════

def _wing_planform(geo, prefix, XL, ZL):
    """
    Compute planform polygon points for top, side and front views.
    prefix = 'W','H','V'
    XL, ZL = leading edge attachment point from SYNTHS
    Returns dict with keys: x_top, y_top, z_top, x_side, z_side,
                             y_front, z_front  (all numpy arrays)
    """
    p = prefix
    TYPE   = geo.get(p+'TYPE',   1)
    CHRDR  = geo.get(p+'CHRDR',  1.0)
    CHRDTP = geo.get(p+'CHRDTP', 0.5)
    CHRDBP = geo.get(p+'CHRDBP', CHRDTP)
    SSPN   = geo.get(p+'SSPN',   1.0)
    SSPNOP = geo.get(p+'SSPNOP', SSPN)
    SAVSI  = geo.get(p+'SAVSI',  0.0)
    SAVSO  = geo.get(p+'SAVSO',  0.0)
    DHDADI = geo.get(p+'DHDADI', 0.0)
    DHDADO = geo.get(p+'DHDADO', 0.0)
    CHSTAT = geo.get(p+'CHSTAT', 0.0)
    at     = AT   # simplified airfoil thickness ratio

    tsi = math.tan(math.radians(SAVSI))
    tso = math.tan(math.radians(SAVSO))
    tdi = math.tan(math.radians(DHDADI))
    tdo = math.tan(math.radians(DHDADO))

    if TYPE == 1:
        # Straight tapered
        xLE_tip = XL + CHSTAT*CHRDR + SSPN*tsi - CHSTAT*CHRDTP
        xTE_tip = xLE_tip + CHRDTP
        x = np.array([XL, xLE_tip, xTE_tip, XL+CHRDR])
        y = np.array([0,  SSPN,    SSPN,    0])
        z = np.array([ZL, ZL+SSPN*tdi, ZL+SSPN*tdi, ZL])
        # front view z at each spanwise station
        zf = np.array([ZL+at*CHRDR,
                        ZL+SSPN*tdi+at*CHRDTP,
                        ZL+SSPN*tdi-at*CHRDTP,
                        ZL-at*CHRDR])
    else:
        # Double cranked (TYPE 2 or 3)
        bp = SSPN - SSPNOP   # inner panel span
        x = np.array([
            XL,
            XL + CHSTAT*CHRDR + bp*tsi - CHSTAT*CHRDBP,
            XL + CHSTAT*CHRDR + bp*tsi + SSPNOP*tso - CHSTAT*CHRDTP,
            XL + CHSTAT*CHRDR + bp*tsi + SSPNOP*tso + (1-CHSTAT)*CHRDTP,
            XL + CHSTAT*CHRDR + bp*tsi + (1-CHSTAT)*CHRDBP,
            XL + CHRDR,
        ])
        y = np.array([0, bp, SSPN, SSPN, bp, 0])
        z = np.array([
            ZL,
            ZL + bp*tdi,
            ZL + bp*tdi + SSPNOP*tdo,
            ZL + bp*tdi + SSPNOP*tdo,
            ZL + bp*tdi,
            ZL,
        ])
        zf = np.array([
            ZL + at*CHRDR,
            ZL + bp*tdi + at*CHRDBP,
            ZL + bp*tdi + SSPNOP*tdo + at*CHRDTP,
            ZL + bp*tdi + SSPNOP*tdo - at*CHRDTP,
            ZL + bp*tdi - at*CHRDBP,
            ZL - at*CHRDR,
        ])

    return dict(x=x, y=y, z=z, zf=zf,
                SSPN=SSPN, CHRDR=CHRDR, CHRDTP=CHRDTP)


def _vtail_planform(geo, XV, ZV):
    """Vertical tail: span goes in Z direction."""
    TYPE   = geo.get('VTYPE',   1)
    CHRDR  = geo.get('VCHRDR',  1.0)
    CHRDTP = geo.get('VCHRDTP', 0.5)
    CHRDBP = geo.get('VCHRDBP', CHRDTP)
    SSPN   = geo.get('VSSPN',   1.0)
    SSPNOP = geo.get('VSSPNOP', SSPN)
    SAVSI  = geo.get('VSAVSI',  0.0)
    SAVSO  = geo.get('VSAVSO',  0.0)
    CHSTAT = geo.get('VCHSTAT', 0.0)
    at     = AT

    tsi = math.tan(math.radians(SAVSI))
    tso = math.tan(math.radians(SAVSO))

    if TYPE == 1:
        xv = np.array([XV,
                        XV + CHSTAT*CHRDR + SSPN*tsi - CHSTAT*CHRDTP,
                        XV + CHSTAT*CHRDR + SSPN*tsi + (1-CHSTAT)*CHRDTP,
                        XV + CHRDR])
        yv_side = np.array([at*CHRDR, at*CHRDTP, -at*CHRDTP, -at*CHRDR])
        zv = ZV + np.array([0, SSPN, SSPN, 0])
    else:
        bp = SSPN - SSPNOP
        xv = np.array([XV,
                        XV + CHSTAT*CHRDR + bp*tsi - CHSTAT*CHRDBP,
                        XV + CHSTAT*CHRDR + bp*tsi + SSPNOP*tso - CHSTAT*CHRDTP,
                        XV + CHSTAT*CHRDR + bp*tsi + SSPNOP*tso + (1-CHSTAT)*CHRDTP,
                        XV + CHSTAT*CHRDR + bp*tsi + (1-CHSTAT)*CHRDBP,
                        XV + CHRDR])
        yv_side = np.array([at*CHRDR, at*CHRDBP, at*CHRDTP,
                             -at*CHRDTP, -at*CHRDBP, -at*CHRDR])
        zv = ZV + np.array([0, bp, SSPN, SSPN, bp, 0])

    # top-view: vertical tail appears as a line (no span in y)
    return dict(x=xv, y_side=yv_side, z=zv, SSPN=SSPN)


# ══════════════════════════════════════════════════════════════════════
# Main figure builder
# ══════════════════════════════════════════════════════════════════════

DARK_BG  = '#0d1117'
DARK_AX  = '#1c2128'
COL_BODY = '#8baac8'
COL_WING = '#4fc3f7'
COL_HTP  = '#81c784'
COL_VTP  = '#ffb74d'
COL_EDGE = '#cdd9e5'
COL_AFL  = '#f48fb1'
ACCENT   = '#2ea043'
ACCENT2  = '#388bfd'


def get_figure(dat_path, title="Aircraft Three-View", figsize=(13, 9)):
    """
    Parse dat_path and return a matplotlib Figure with the three-view
    drawing plus airfoil cross-sections.  Suitable for embedding in Tk.
    """
    geo = parse_dat_for_view(dat_path)

    fig = plt.figure(figsize=figsize, facecolor=DARK_BG)
    fig.suptitle(title, color=COL_EDGE, fontsize=11,
                 fontfamily='monospace', y=0.98)

    def _ax(rect, xlabel='', ylabel='', title=''):
        ax = fig.add_axes(rect, facecolor=DARK_AX)
        ax.tick_params(colors=COL_EDGE, labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor('#30363d')
        ax.set_xlabel(xlabel, color=COL_EDGE, fontsize=7)
        ax.set_ylabel(ylabel, color=COL_EDGE, fontsize=7)
        ax.set_title(title,   color=COL_EDGE, fontsize=8,
                     fontfamily='monospace')
        ax.grid(True, color='#30363d', linewidth=0.4)
        return ax

    ax_top   = _ax([0.05, 0.42, 0.55, 0.52], 'x (m)', 'y (m)',   'Top View')
    ax_side  = _ax([0.05, 0.05, 0.55, 0.33], 'x (m)', 'z (m)',   'Side View')
    ax_front = _ax([0.63, 0.05, 0.34, 0.33], 'y (m)', 'z (m)',   'Front View')
    ax_wafl  = _ax([0.63, 0.75, 0.34, 0.18], 'x/c',   'y/c',     'Wing Airfoil')
    ax_hafl  = _ax([0.63, 0.55, 0.34, 0.16], 'x/c',   'y/c',     'H-Tail Airfoil')
    ax_vafl  = _ax([0.63, 0.42, 0.34, 0.10], 'x/c',   'y/c',     'V-Tail Airfoil')

    def fill_top(ax, x, y, color, alpha=0.55):
        # mirror about y=0 for both wings
        ax.fill(np.concatenate([x, x[::-1]]),
                np.concatenate([y, -y[::-1]]),
                color=color, alpha=alpha, linewidth=0)
        ax.plot(np.concatenate([x, x[::-1]]),
                np.concatenate([y, -y[::-1]]),
                color=COL_EDGE, linewidth=0.6)

    def fill_side(ax, x, z, color, alpha=0.6):
        ax.fill(x, z, color=color, alpha=alpha, linewidth=0)
        ax.plot(np.concatenate([x, [x[0]]]),
                np.concatenate([z, [z[0]]]),
                color=COL_EDGE, linewidth=0.6)

    def fill_front(ax, y, z, color, alpha=0.55):
        ax.fill(np.concatenate([y, -y[::-1]]),
                np.concatenate([z, z[::-1]]),
                color=color, alpha=alpha, linewidth=0)
        ax.plot(np.concatenate([y, -y[::-1], [y[0]]]),
                np.concatenate([z, z[::-1],  [z[0]]]),
                color=COL_EDGE, linewidth=0.6)

    # ── Fuselage ──────────────────────────────────────────────────────
    if 'BX' in geo and geo['BX']:
        BX = np.array(geo['BX']); BR = np.array(geo['BR'])
        # top view: fuselage outline
        ax_top.fill(np.concatenate([BX, BX[::-1]]),
                    np.concatenate([BR, -BR[::-1]]),
                    color=COL_BODY, alpha=0.45, linewidth=0)
        ax_top.plot(BX,  BR,  color=COL_EDGE, linewidth=0.7)
        ax_top.plot(BX, -BR,  color=COL_EDGE, linewidth=0.7)

        BZU = np.array(geo.get('BZU', BR)) if geo.get('BZU') else BR
        BZL = np.array(geo.get('BZL',-BR)) if geo.get('BZL') else -BR
        ax_side.fill(np.concatenate([BX, BX[::-1]]),
                     np.concatenate([BZU, BZL[::-1]]),
                     color=COL_BODY, alpha=0.45, linewidth=0)
        ax_side.plot(BX, BZU, color=COL_EDGE, linewidth=0.7)
        ax_side.plot(BX, BZL, color=COL_EDGE, linewidth=0.7)

        # front view: oval
        theta = np.linspace(0, 2*math.pi, 60)
        rmax  = float(np.max(BR))
        zc    = float(np.mean(BZU)) if geo.get('BZU') else 0
        ax_front.fill(rmax*np.cos(theta), zc + rmax*np.sin(theta),
                      color=COL_BODY, alpha=0.45, linewidth=0)
        ax_front.plot(rmax*np.cos(theta), zc + rmax*np.sin(theta),
                      color=COL_EDGE, linewidth=0.7)

    # ── Wing ──────────────────────────────────────────────────────────
    if all(k in geo for k in ['WCHRDR','WSSPN','WCHRDTP','XW','ZW']):
        XW = geo['XW']; ZW = geo['ZW']
        wp = _wing_planform(geo, 'W', XW, ZW)
        fill_top(ax_top, wp['x'], wp['y'], COL_WING)
        fill_side(ax_side,
                  np.concatenate([wp['x'], wp['x'][::-1]]),
                  np.concatenate([wp['z']+AT*np.array([wp['CHRDR'] if i==0 else wp['CHRDTP']
                                                        for i in range(len(wp['z']))]),
                                   wp['z']-AT*np.array([wp['CHRDR'] if i==0 else wp['CHRDTP']
                                                         for i in range(len(wp['z']))])[::-1]]),
                  COL_WING, 0.3)
        fill_front(ax_front, wp['y'], wp['zf'], COL_WING)

        # Wing airfoil
        ntype = geo.get('WNACA_TYPE'); nid = geo.get('WNACA_ID')
        if ntype and nid:
            ax, ayu, ayl = generate_naca(ntype, nid)
            if ax is not None:
                ax_wafl.fill(np.concatenate([ax, ax[::-1]]),
                             np.concatenate([ayu, ayl[::-1]]),
                             color=COL_WING, alpha=0.5)
                ax_wafl.plot(ax, ayu, color=COL_AFL, lw=1)
                ax_wafl.plot(ax, ayl, color=COL_AFL, lw=1)
        ax_wafl.set_aspect('equal', adjustable='datalim')

    # ── Horizontal tail ───────────────────────────────────────────────
    if all(k in geo for k in ['HCHRDR','HSSPN','HCHRDTP','XH','ZH']):
        XH = geo['XH']; ZH = geo['ZH']
        hp = _wing_planform(geo, 'H', XH, ZH)
        fill_top(ax_top, hp['x'], hp['y'], COL_HTP)
        fill_front(ax_front, hp['y'], hp['zf'], COL_HTP)

        ntype = geo.get('HNACA_TYPE'); nid = geo.get('HNACA_ID')
        if ntype and nid:
            ax, ayu, ayl = generate_naca(ntype, nid)
            if ax is not None:
                ax_hafl.fill(np.concatenate([ax, ax[::-1]]),
                             np.concatenate([ayu, ayl[::-1]]),
                             color=COL_HTP, alpha=0.5)
                ax_hafl.plot(ax, ayu, color=COL_AFL, lw=1)
                ax_hafl.plot(ax, ayl, color=COL_AFL, lw=1)
        ax_hafl.set_aspect('equal', adjustable='datalim')

    # ── Vertical tail ─────────────────────────────────────────────────
    if all(k in geo for k in ['VCHRDR','VSSPN','VCHRDTP','XV','ZV']):
        XV = geo['XV']; ZV = geo['ZV']
        vp = _vtail_planform(geo, XV, ZV)
        # top view: just a thin line (no span in y)
        ax_top.fill(np.concatenate([vp['x'], vp['x'][::-1]]),
                    np.concatenate([vp['y_side'], -vp['y_side'][::-1]]),
                    color=COL_VTP, alpha=0.55, linewidth=0)
        ax_top.plot(vp['x'], vp['y_side'], color=COL_EDGE, lw=0.6)
        ax_top.plot(vp['x'],-vp['y_side'],color=COL_EDGE, lw=0.6)
        # side view
        fill_side(ax_side, vp['x'], vp['z'], COL_VTP)
        # front view: vertical fin
        ax_front.fill([0, 0], [ZV, ZV+vp['SSPN']],
                      color=COL_VTP, alpha=0.0)
        ax_front.fill(np.concatenate([vp['y_side'], -vp['y_side'][::-1]]),
                      np.concatenate([vp['z'], vp['z'][::-1]]),
                      color=COL_VTP, alpha=0.55, linewidth=0)
        ax_front.plot(np.concatenate([vp['y_side'], -vp['y_side'][::-1], [vp['y_side'][0]]]),
                      np.concatenate([vp['z'],       vp['z'][::-1],      [vp['z'][0]]]),
                      color=COL_EDGE, lw=0.6)

        ntype = geo.get('VNACA_TYPE'); nid = geo.get('VNACA_ID')
        if ntype and nid:
            ax, ayu, ayl = generate_naca(ntype, nid)
            if ax is not None:
                ax_vafl.fill(np.concatenate([ax, ax[::-1]]),
                             np.concatenate([ayu, ayl[::-1]]),
                             color=COL_VTP, alpha=0.5)
                ax_vafl.plot(ax, ayu, color=COL_AFL, lw=1)
                ax_vafl.plot(ax, ayl, color=COL_AFL, lw=1)
        ax_vafl.set_aspect('equal', adjustable='datalim')

    # CG marker intentionally hidden.
    # XCG/ZCG may be user-entered fixed reference values rather than
    # optimized or re-computed mass properties, so plotting them can be misleading.

    # Axis equal + invert y for top view (nose left)
    for ax in [ax_top, ax_side, ax_front, ax_wafl, ax_hafl, ax_vafl]:
        ax.set_aspect('equal', adjustable='datalim')
    ax_top.invert_xaxis()

    # Legend
    handles = [
        mpatches.Patch(color=COL_BODY, label='Fuselage'),
        mpatches.Patch(color=COL_WING, label='Wing'),
        mpatches.Patch(color=COL_HTP,  label='H-Tail'),
        mpatches.Patch(color=COL_VTP,  label='V-Tail'),
    ]
    ax_top.legend(handles=handles, fontsize=7, facecolor='#21262d',
                  edgecolor='#30363d', labelcolor=COL_EDGE,
                  loc='lower right')

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    return fig


def get_figure_sidebyside(dat_before, dat_after,
                           label_left="Before",
                           label_right="After (Optimized)",
                           figsize=(18, 8)):
    """
    Produce a single matplotlib Figure with two three-view drawings
    side-by-side: left = dat_before, right = dat_after.
    """
    geo_b = parse_dat_for_view(dat_before)
    geo_a = parse_dat_for_view(dat_after)

    fig = plt.figure(figsize=figsize, facecolor=DARK_BG)

    # Column titles
    fig.text(0.25, 0.97, label_left,  ha='center', va='top',
             color=ACCENT2,  fontsize=10, fontfamily='monospace',
             fontweight='bold')
    fig.text(0.75, 0.97, label_right, ha='center', va='top',
             color=ACCENT,   fontsize=10, fontfamily='monospace',
             fontweight='bold')

    def _ax(left, bottom, width, height, xlabel='', ylabel='', title=''):
        ax = fig.add_axes([left, bottom, width, height], facecolor=DARK_AX)
        ax.tick_params(colors=COL_EDGE, labelsize=6)
        for sp in ax.spines.values(): sp.set_edgecolor('#30363d')
        ax.set_xlabel(xlabel, color=COL_EDGE, fontsize=6)
        ax.set_ylabel(ylabel, color=COL_EDGE, fontsize=6)
        ax.set_title(title,   color=COL_EDGE, fontsize=7, fontfamily='monospace')
        ax.grid(True, color='#30363d', linewidth=0.3)
        return ax

    # Layout: each column gets top/side/front + 3 airfoil strips
    # left column: x 0.02..0.48,  right column: x 0.52..0.98
    def make_column_axes(ox):
        """ox = left offset of column (0.02 or 0.52)"""
        w = 0.44
        ax_top   = _ax(ox,       0.38, w*0.62, 0.55, 'x','y',  'Top View')
        ax_side  = _ax(ox,       0.04, w*0.62, 0.30, 'x','z',  'Side View')
        ax_front = _ax(ox+w*0.65,0.04, w*0.33, 0.30, 'y','z',  'Front View')
        ax_wafl  = _ax(ox+w*0.65,0.74, w*0.33, 0.17, 'x/c','', 'Wing Afl')
        ax_hafl  = _ax(ox+w*0.65,0.56, w*0.33, 0.14, 'x/c','', 'H-Tail Afl')
        ax_vafl  = _ax(ox+w*0.65,0.45, w*0.33, 0.08, 'x/c','', 'V-Tail Afl')
        return ax_top, ax_side, ax_front, ax_wafl, ax_hafl, ax_vafl

    axes_b = make_column_axes(0.02)
    axes_a = make_column_axes(0.52)

    for geo, (ax_top, ax_side, ax_front, ax_wafl, ax_hafl, ax_vafl) in \
            [(geo_b, axes_b), (geo_a, axes_a)]:
        _draw_geometry(geo, ax_top, ax_side, ax_front,
                       ax_wafl, ax_hafl, ax_vafl)

    # Vertical divider
    fig.add_artist(plt.Line2D([0.5, 0.5], [0.01, 0.96],
                               transform=fig.transFigure,
                               color='#30363d', lw=1))
    return fig


def _draw_geometry(geo, ax_top, ax_side, ax_front,
                   ax_wafl, ax_hafl, ax_vafl):
    """Draw one aircraft's geometry onto the provided axes."""

    def fill_top(ax, x, y, color, alpha=0.55):
        ax.fill(np.concatenate([x, x[::-1]]),
                np.concatenate([y, -y[::-1]]),
                color=color, alpha=alpha, linewidth=0)
        ax.plot(np.concatenate([x, x[::-1], [x[0]]]),
                np.concatenate([y, -y[::-1], [y[0]]]),
                color=COL_EDGE, linewidth=0.5)

    def fill_side(ax, x, z, color, alpha=0.5):
        ax.fill(x, z, color=color, alpha=alpha, linewidth=0)
        ax.plot(np.concatenate([x,[x[0]]]),
                np.concatenate([z,[z[0]]]),
                color=COL_EDGE, linewidth=0.5)

    def fill_front(ax, y, z, color, alpha=0.55):
        ax.fill(np.concatenate([y, -y[::-1]]),
                np.concatenate([z,  z[::-1]]),
                color=color, alpha=alpha, linewidth=0)
        ax.plot(np.concatenate([y, -y[::-1], [y[0]]]),
                np.concatenate([z,  z[::-1], [z[0]]]),
                color=COL_EDGE, linewidth=0.5)

    def draw_airfoil(ax, ntype, nid, color):
        if not ntype or not nid: return
        axf, ayu, ayl = generate_naca(ntype, nid)
        if axf is None: return
        ax.fill(np.concatenate([axf, axf[::-1]]),
                np.concatenate([ayu, ayl[::-1]]),
                color=color, alpha=0.5)
        ax.plot(axf, ayu, color=COL_AFL, lw=0.9)
        ax.plot(axf, ayl, color=COL_AFL, lw=0.9)
        ax.set_aspect('equal', adjustable='datalim')

    # ── Fuselage ──────────────────────────────────────────────────────
    if 'BX' in geo and geo['BX']:
        BX = np.array(geo['BX']); BR = np.array(geo['BR'])
        ax_top.fill(np.concatenate([BX, BX[::-1]]),
                    np.concatenate([BR, -BR[::-1]]),
                    color=COL_BODY, alpha=0.4, linewidth=0)
        ax_top.plot(BX,  BR, color=COL_EDGE, lw=0.6)
        ax_top.plot(BX, -BR, color=COL_EDGE, lw=0.6)

        BZU = np.array(geo['BZU']) if geo.get('BZU') else BR
        BZL = np.array(geo['BZL']) if geo.get('BZL') else -BR
        ax_side.fill(np.concatenate([BX, BX[::-1]]),
                     np.concatenate([BZU, BZL[::-1]]),
                     color=COL_BODY, alpha=0.4, linewidth=0)
        ax_side.plot(BX, BZU, color=COL_EDGE, lw=0.6)
        ax_side.plot(BX, BZL, color=COL_EDGE, lw=0.6)

        rmax = float(np.max(BR))
        zc   = float(np.mean(BZU)) if geo.get('BZU') else 0
        theta = np.linspace(0, 2*math.pi, 60)
        ax_front.fill(rmax*np.cos(theta), zc+rmax*np.sin(theta),
                      color=COL_BODY, alpha=0.4, linewidth=0)
        ax_front.plot(rmax*np.cos(theta), zc+rmax*np.sin(theta),
                      color=COL_EDGE, lw=0.6)

    # ── Wing ──────────────────────────────────────────────────────────
    if all(k in geo for k in ['WCHRDR','WSSPN','WCHRDTP','XW','ZW']):
        wp = _wing_planform(geo, 'W', geo['XW'], geo['ZW'])
        fill_top(ax_top, wp['x'], wp['y'], COL_WING)
        fill_front(ax_front, wp['y'], wp['zf'], COL_WING)
        draw_airfoil(ax_wafl, geo.get('WNACA_TYPE'), geo.get('WNACA_ID'), COL_WING)

    # ── H-Tail ────────────────────────────────────────────────────────
    if all(k in geo for k in ['HCHRDR','HSSPN','HCHRDTP','XH','ZH']):
        hp = _wing_planform(geo, 'H', geo['XH'], geo['ZH'])
        fill_top(ax_top, hp['x'], hp['y'], COL_HTP)
        fill_front(ax_front, hp['y'], hp['zf'], COL_HTP)
        draw_airfoil(ax_hafl, geo.get('HNACA_TYPE'), geo.get('HNACA_ID'), COL_HTP)

    # ── V-Tail ────────────────────────────────────────────────────────
    if all(k in geo for k in ['VCHRDR','VSSPN','VCHRDTP','XV','ZV']):
        vp = _vtail_planform(geo, geo['XV'], geo['ZV'])
        ax_top.fill(np.concatenate([vp['x'], vp['x'][::-1]]),
                    np.concatenate([vp['y_side'], -vp['y_side'][::-1]]),
                    color=COL_VTP, alpha=0.5, linewidth=0)
        ax_top.plot(vp['x'],  vp['y_side'], color=COL_EDGE, lw=0.5)
        ax_top.plot(vp['x'], -vp['y_side'], color=COL_EDGE, lw=0.5)
        fill_side(ax_side, vp['x'], vp['z'], COL_VTP)
        ax_front.fill(
            np.concatenate([vp['y_side'], -vp['y_side'][::-1]]),
            np.concatenate([vp['z'],       vp['z'][::-1]]),
            color=COL_VTP, alpha=0.5, linewidth=0)
        ax_front.plot(
            np.concatenate([vp['y_side'], -vp['y_side'][::-1], [vp['y_side'][0]]]),
            np.concatenate([vp['z'],       vp['z'][::-1],      [vp['z'][0]]]),
            color=COL_EDGE, lw=0.5)
        draw_airfoil(ax_vafl, geo.get('VNACA_TYPE'), geo.get('VNACA_ID'), COL_VTP)

    # CG intentionally hidden.
    # XCG/ZCG may be user-entered fixed reference values rather than
    # optimized or re-computed mass properties, so plotting them can be misleading.

    for ax in [ax_top, ax_side, ax_front, ax_wafl, ax_hafl, ax_vafl]:
        ax.set_aspect('equal', adjustable='datalim')
    ax_top.invert_xaxis()


# ── Standalone test ───────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'for005.dat'
    matplotlib.use('TkAgg')
    fig = get_figure_sidebyside(path, path,
                                 label_left='Before',
                                 label_right='After (same file test)')
    plt.show()
