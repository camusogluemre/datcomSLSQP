# DATCOM Optimization Tool

A desktop GUI for aerodynamic shape optimization of aircraft lifting surfaces
using **Digital DATCOM** as the aerodynamic solver and **SLSQP**
(`scipy.optimize.fmin_slsqp`) as the optimizer.

You load a standard DATCOM `for005.dat` input file, pick which wing / tail
planform parameters to optimize and their bounds, define a cost function from
the aerodynamic coefficients, and the tool drives DATCOM iteratively to find an
improved geometry. Results can be inspected as before/after tables, three-view
drawings, and full angle-of-attack sweeps.

> The original `for005.dat` is **never modified** — every DATCOM run is executed
> on a temporary copy.

---

## Features

- **Automatic parsing** of `for005.dat` (`$WGPLNF`, `$HTPLNF`, `$VTPLNF`,
  `$SYNTHS`, `$FLTCON`, `$OPTINS`). Single-panel and two-panel (cranked)
  surfaces are detected automatically.
- **30 geometry parameters** across wing, horizontal tail and vertical tail
  (sweep, span, break-panel span, dihedral, twist, root/break/tip chords).
  Enable/disable any subset and set per-parameter search bounds.
- **Custom cost function** built from `CL`, `CD`, `CM`, `rCL`, `wing_area`
  (with `abs(...)`), plus one-click presets (max lift, max L/D, min drag,
  min moment, trade-offs).
- **Multi-start SLSQP** — 6 passes from spread starting points to reduce the
  chance of stopping at a poor local optimum; the global best is kept.
- **Hard level-flight lift constraint**: candidates with `CL < rCL`
  (the lift coefficient required for level flight at the given weight and flight
  condition) are penalized.
- **Automatic XCG (MAC tracking)** — the pitching-moment reference `XCG` is
  recomputed each iteration to the quarter-chord of the wing mean aerodynamic
  chord, so `CM` stays referenced to a consistent point as the geometry changes.
  See [How XCG is handled](#how-xcg-is-handled).
- **Unit aware** — supports both `DIM FT` and `DIM M` input files; all derived
  quantities (e.g. `rCL`) are computed in SI internally.
- **Aircraft View** — side-by-side and overlay three-view drawings of the
  baseline vs optimized geometry.
- **Aero Sweep** — full angle-of-attack sweep of baseline vs optimized
  (`CL`, `CD`, `CM`, `L/D`, `dCM/dα`).
- **Exports** — optimized `for005.dat`, a before/after parameter `.csv`, and a
  full optimization log.

---

## Requirements

- **Windows** (Digital DATCOM is shipped here as `digital_DATCOM.EXE`).
- **Python 3.8+** with:
  - `numpy`
  - `scipy`
  - `matplotlib`
  - `tkinter` (ships with the standard CPython installer on Windows)

Install the Python dependencies:

```bash
pip install numpy scipy matplotlib
```

---

## Quick start

```bash
python datcom_optimizer.py
```

1. **Input File** tab → *Browse...* a `for005.dat`, then *Load & Parse*.
   (`digital_DATCOM.exe` in the repo root is used by default; override it with
   *Browse EXE...* if needed.)
2. **Parameters** tab → tick the parameters to optimize and adjust their
   low/high bounds (defaults to ±5 % of the current value).
3. **Cost Function** tab → type an expression or pick a preset.
4. **Run** tab → *START OPTIMIZATION* and watch the live log / metrics.
5. **Results**, **Aircraft View**, **Aero Sweep** tabs → inspect the outcome.

Ready-to-load sample inputs are included — see [Sample data](#sample-data).

For a full walkthrough see **[USER_MANUAL.md](USER_MANUAL.md)**.

---

## How XCG is handled

DATCOM computes the pitching-moment coefficient `CM` about the moment reference
station `XCG` (in the `$SYNTHS` namelist). Because the optimizer changes the
wing planform, a fixed `XCG` would mean `CM` is measured about an
increasingly inconsistent point from one iteration to the next.

To keep `CM` meaningful, **`XCG` is recomputed on every DATCOM evaluation** and
placed at a fixed fraction of the current wing **mean aerodynamic chord (MAC)**:

```
XCG = x_LE_MAC + MAC_CG_FRACTION * MAC
```

- `MAC` and its leading-edge station `x_LE_MAC` are the chord-weighted values of
  the current planform (wing apex `XW`, sweep referenced at `CHSTAT`, two-panel
  split at `bp = SSPN − SSPNOP`) — the same geometry convention used by the
  Aircraft View.
- `MAC_CG_FRACTION` defaults to **0.25** (quarter-chord of the MAC) and is a
  single constant near the top of `datcom_optimizer.py`.
- If the input file has no `$SYNTHS XW`, `XCG` is left untouched.

---

## Repository structure

| Path | Purpose |
|------|---------|
| `datcom_optimizer.py` | Main GUI application, DATCOM I/O, and the SLSQP driver. |
| `aircraft_view.py` | Three-view geometry drawing (top/side/front) from a `.dat`. |
| `digital_DATCOM.EXE` | Digital DATCOM solver executable (Windows). |
| `myfuncs.py` | Legacy/auxiliary helpers. |
| `original_Data_C500/` | Sample input — Cessna Citation II (Model 550). |
| `Orginal_Data_B737/` | Sample input — Boeing 737. |
| `Original_Data_F16/` | Sample input — F-16. |
| `drawDATCOM/` | Reference DATCOM drawing utility and test cases. |
| `old_codes/` | Archived earlier versions. |

---

## Sample data

| Aircraft | Folder | Input file |
|----------|--------|-----------|
| Cessna Citation II (Model 550) | `original_Data_C500/` | `for005.dat` |
| Boeing 737 | `Orginal_Data_B737/` | `for005.dat` |
| F-16 | `Original_Data_F16/` | `for005.dat` |

---

## Outputs

Each run writes, to a timestamped output folder:

- the **optimized** `for005.dat` (with the improved geometry and recomputed `XCG`),
- a **before/after** parameter table (`.csv`),
- the full **optimization log** (`optimization_log.txt`).

---

## Notes & limitations

- DATCOM is run by writing `for005.dat` into the executable's working directory,
  launching the EXE, and reading `datcom.out`; the original working `for005.dat`
  is backed up and restored around each run.
- Some geometries make DATCOM report zero coefficients. When detected, the tool
  offers an `SREF`-based scaling workaround so coefficients are evaluated against
  the current theoretical wing area. This scaling is **not** valid when `CBARR`
  is explicitly set in the input, and is blocked in that case.
- The angle-of-attack schedule (`ALSCHD`) is treated as fixed during
  optimization.
