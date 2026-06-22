# DATCOM Wing Optimization Tool — User Manual

This manual walks through the application tab by tab. For an overview, features
and installation, see [README.md](README.md).

## Contents

1. [Launching the tool](#1-launching-the-tool)
2. [Tab 1 — Input File](#2-tab-1--input-file)
3. [Tab 2 — Parameters](#3-tab-2--parameters)
4. [Tab 3 — Cost Function](#4-tab-3--cost-function)
5. [Tab 4 — Run](#5-tab-4--run)
6. [Tab 5 — Results](#6-tab-5--results)
7. [Tab 6 — Aircraft View](#7-tab-6--aircraft-view)
8. [Tab 7 — Aero Sweep](#8-tab-7--aero-sweep)
9. [How XCG (moment reference) is computed](#9-how-xcg-moment-reference-is-computed)
10. [Outputs](#10-outputs)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Launching the tool

```bash
python datcom_optimizer.py
```

The main window (*DATCOM Wing Optimization Tool*) opens with seven tabs that are
meant to be used left to right: **Input File → Parameters → Cost Function → Run
→ Results → Aircraft View → Aero Sweep**.

The original input file is never written to — every DATCOM run uses a temporary
copy, and the executable's own working `for005.dat` is backed up and restored
around each run.

---

## 2. Tab 1 — Input File

Load and inspect the DATCOM input.

1. **Input File (for005.dat)** — click **Browse...**, select your `for005.dat`,
   then click **Load & Parse**. On success the tool reports that the file was
   parsed and shows the detected parameters.
2. **Digital DATCOM EXE** — defaults to `digital_DATCOM.exe` in the program
   folder. Use **Browse EXE...** only if you want a different solver build.
3. **ALSCHD — Angle of Attack** — shows the angle-of-attack schedule read from
   the file. It is **read-only and fixed** during optimization.
4. **File Preview** — a scrollable view of the raw `.dat` contents.

The parser reads the `$WGPLNF` / `$HTPLNF` / `$VTPLNF` planform blocks plus
`$SYNTHS`, `$FLTCON` and `$OPTINS`, and supports both `DIM FT` and `DIM M`
files. Single-panel and two-panel (cranked) surfaces are detected
automatically.

> If parsing fails, the error message names the missing or invalid namelist input
> (for example a required `CHRDR` or, for a cranked surface, `CHRDBP`).

---

## 3. Tab 2 — Parameters

Choose **what** to optimize and **within what range**.

Parameters are grouped by surface — **Wing**, **V-Tail**, **H-Tail** — and each
group shows its detected geometry (*Single Panel* or *Two Panel*). Each row has:

| Column | Meaning |
|--------|---------|
| Checkbox | Include this parameter in the optimization. |
| Name | The DATCOM keyword and a description. |
| Current | Value read from the file. |
| Low / High | Search bounds for this parameter. |
| Unit | `deg` or length (`m`/`ft`, matching the file's `DIM`). |

Optimizable parameters per surface: inner/outer sweep (`SAVSI`, `SAVSO`), span
and break-panel span (`SSPN`, `SSPNOP`), inner/outer dihedral (`DHDADI`,
`DHDADO`), twist (`TWISTA`), and root/break/tip chords (`CHRDR`, `CHRDBP`,
`CHRDTP`).

Notes:

- Bounds are initialized to **±5 %** of each current value — adjust them to set
  a sensible, physically realistic design space.
- Parameters not present in the file (e.g. break-panel inputs on a single-panel
  surface) are unavailable and cannot be selected.
- Keep bounds tight enough to stay realistic but wide enough to give the
  optimizer room to move.

---

## 4. Tab 3 — Cost Function

Define the scalar objective. **The optimizer minimizes the expression**, so use
a negative sign to maximize a quantity.

**Variables available** in the expression:

| Symbol | Meaning |
|--------|---------|
| `CL` | Lift coefficient |
| `CD` | Drag coefficient |
| `CM` | Pitching-moment coefficient (about the recomputed `XCG`) |
| `rCL` | Lift coefficient required for level flight at the given weight/condition |
| `wing_area` | Current theoretical wing area |
| `abs(...)` | Absolute value |

**Preset templates** (buttons):

| Preset | Expression |
|--------|-----------|
| Maximize Lift | `-CL` |
| Maximize L/D | `-(CL/CD)` |
| Minimize Drag | `CD` |
| Minimize Moment | `abs(CM)` |
| Lift + Drag Tradeoff | `-CL + 3*CD` |
| L/D + Trim Tradeoff | `-(CL/CD) + 0.1*abs(CM)` |

You can type any combination, e.g. `CD + 0.1*abs(CM)`.

---

## 5. Tab 4 — Run

Drive the optimization and watch progress live.

- **START OPTIMIZATION** — begins the run. **Stop** halts it; **Clear Log**
  empties the log panel.
- **Status / progress / Iter** — current state and DATCOM evaluation count.
- **Live metric cards** — Best Score, Iterations, `CL`, `CD`, `CM`, `rCL`.
- **Optimization Log** — colour-coded messages: the active parameter list, the
  initial evaluation, the per-pass best, and the final summary.

**What happens during a run:**

1. The current geometry is evaluated once to establish the baseline.
2. **Six SLSQP passes** run from different starting points across the bounds
   (multi-start). This reduces the risk of converging to a poor local optimum.
3. The **global best** design across all passes is kept and re-evaluated.

**Level-flight lift constraint:** any candidate whose `CL` is below the required
`rCL` is penalized with a very large score, so the optimizer is pushed toward
designs that can actually sustain level flight.

**Zero-coefficient handling:** for some geometries DATCOM reports zero
coefficients. When this is detected the tool offers an `SREF`-based scaling
workaround so coefficients are evaluated against the current theoretical wing
area. (This scaling is not valid — and is blocked — when `CBARR` is explicitly
defined in the input.)

---

## 6. Tab 5 — Results

A before/after summary, populated automatically when a run finishes.

- **Summary cards** — Score, `CL`, `CD`, `CM`, each shown *Before* and *After*.
- **Parameter Changes table** — for every parameter: *Before*, *After*,
  *Change*, *Unit*, and a *Status* flag indicating whether it was optimized.

The optimized geometry, a before/after `.csv`, and the full log are also written
to disk — see [Outputs](#10-outputs).

---

## 7. Tab 6 — Aircraft View

Visual comparison of the geometry.

- Click **Draw Before & After** to render three-view drawings (top, side,
  front) of the baseline and the optimized aircraft.
- Two sub-tabs:
  - **Side-by-Side** — baseline and optimized drawn next to each other.
  - **Overlay** — both superimposed for a direct shape comparison.
- **Save PNG...** exports the current figure.

You can draw the baseline right after loading a file; the optimized drawing
appears once an optimization has been run.

---

## 8. Tab 7 — Aero Sweep

Compare aerodynamic behaviour across angle of attack.

1. Optionally edit the **Alpha list** (comma-separated angles, in degrees).
2. Click **Run Alpha Sweep (Baseline + Optimized)**. **Stop** cancels;
   **Save PNG...** exports the plots.
3. The tool runs a full DATCOM sweep for both geometries and plots, baseline vs
   optimized: **CL vs α**, **CD vs α**, **CM vs α**, **L/D vs α**, and
   **dCM/dα vs α**.

The Optimized curve requires that an optimization has been run first; the
Baseline curve only needs a loaded file.

---

## 9. How XCG (moment reference) is computed

`CM` is computed by DATCOM about the moment-reference station `XCG` in
`$SYNTHS`. Because optimization changes the wing planform, the tool
**recomputes `XCG` on every DATCOM evaluation** and places it at a fixed
fraction of the current wing **mean aerodynamic chord (MAC)**:

```
XCG = x_LE_MAC + MAC_CG_FRACTION * MAC
```

- `MAC` and its leading-edge station `x_LE_MAC` are the chord-weighted values of
  the current planform — wing apex `XW`, sweep referenced at `CHSTAT`, and the
  two-panel split at `bp = SSPN − SSPNOP` — matching the Aircraft View geometry.
- `MAC_CG_FRACTION` defaults to **0.25** (the MAC quarter-chord). It is a single
  constant near the top of `datcom_optimizer.py` if you need a different
  convention (e.g. a different static-margin reference).
- If the input has no `$SYNTHS XW`, `XCG` is left at its file value.

Practical consequence: because the baseline is also evaluated at 25 % MAC, the
*CM Before* value is referenced to the same convention as *CM After*, so the
before/after moment comparison is consistent.

---

## 10. Outputs

Each completed run writes, into a timestamped output folder:

- the **optimized `for005.dat`** — improved geometry with the recomputed `XCG`,
- a **before/after parameter table** (`.csv`),
- the full **optimization log** (`optimization_log.txt`).

The output folder location is reported at the end of the log.

---

## 11. Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| *"digital_DATCOM.exe not found"* | Set the correct EXE path on the **Input File** tab. |
| Parse error on load | A required namelist input is missing/invalid; the message names it. |
| Coefficients read as zero | Accept the `SREF` scaling workaround when prompted (unless `CBARR` is explicit). |
| Optimization scores stuck at a huge value | Candidates fail the `CL ≥ rCL` level-flight constraint — widen bounds or revisit the cost function. |
| `CM`/scaling blocked | `CBARR` is explicitly defined in the input; remove it to allow area-based scaling. |
| No "Optimized" sweep/drawing | Run an optimization first; those curves/views need an optimized geometry. |
