#!/usr/bin/env python3
"""
Validate equilibration and extract mechanical metrics for all completed cases.

Key correction
--------------
The original script used a fixed 101-point Savitzky-Golay window. Because the
1e9 s^-1 and 1e10 s^-1 simulations were written at different strain increments,
101 points represented very different physical strain widths.

This version defines smoothing in STRAIN SPACE instead:
    target smoothing width = 0.5% engineering strain = 0.005

The number of Savitzky-Golay points is determined independently for each case
from the median strain spacing, so all strain rates are smoothed over
approximately the same physical strain interval.
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
from common import find_cases

try:
    from scipy.signal import savgol_filter
except ImportError as exc:
    raise SystemExit(
        'SciPy is required for the strain-normalized mechanical analysis. '
        'Install the project dependencies with: pip install -r requirements.txt'
    ) from exc


# ---------------------------------------------------------------------------
# Analysis settings
# ---------------------------------------------------------------------------

# Full target smoothing width in engineering strain.
# 0.005 = 0.5% strain.
SMOOTH_WIDTH_STRAIN = 0.005

# Cubic Savitzky-Golay polynomial.
SAVGOL_POLYORDER = 3

# Mechanical-analysis windows.
ELASTIC_FIT_MIN = 0.02
ELASTIC_FIT_MAX = 0.10

YIELD_SEARCH_MIN = 0.10
YIELD_SEARCH_MAX = 0.20

POST_YIELD_DROP_WINDOW = 0.03

FLOW_MIN = 0.20
FLOW_MAX = 0.25


def _strain_based_window(strain, target_width=SMOOTH_WIDTH_STRAIN):
    """
    Convert a target strain width into an odd Savitzky-Golay window length.

    Parameters
    ----------
    strain : array-like
        Monotonically increasing engineering strain values.
    target_width : float
        Desired smoothing width in engineering strain.
        Example: 0.005 = 0.5% strain.

    Returns
    -------
    window_points : int or None
        Odd Savitzky-Golay window length.
    median_dstrain : float
        Median positive strain increment.
    """
    x = np.asarray(strain, dtype=float)

    if x.size < 5:
        return None, float("nan")

    dx = np.diff(x)
    dx = dx[np.isfinite(dx) & (dx > 0.0)]

    if dx.size == 0:
        return None, float("nan")

    median_dstrain = float(np.median(dx))

    # Convert the requested physical strain width into a point count.
    window_points = int(round(target_width / median_dstrain))

    # Savitzky-Golay requires an odd window and window > polyorder.
    minimum_window = SAVGOL_POLYORDER + 2
    if minimum_window % 2 == 0:
        minimum_window += 1

    window_points = max(window_points, minimum_window)

    if window_points % 2 == 0:
        window_points += 1

    # Window cannot exceed the available number of samples.
    max_window = x.size if x.size % 2 == 1 else x.size - 1
    window_points = min(window_points, max_window)

    if window_points <= SAVGOL_POLYORDER or window_points < 5:
        return None, median_dstrain

    return int(window_points), median_dstrain


def smooth_by_strain(strain, y, target_width=SMOOTH_WIDTH_STRAIN):
    """
    Smooth y using a common PHYSICAL STRAIN width across all simulations.

    Returns
    -------
    y_smooth : ndarray
    info : dict
        Diagnostic information describing the actual smoothing used.
    """
    x = np.asarray(strain, dtype=float)
    y = np.asarray(y, dtype=float)

    if x.shape != y.shape:
        raise ValueError("strain and y must have the same shape")

    window_points, median_dstrain = _strain_based_window(
        x, target_width=target_width
    )

    if window_points is None:
        return y.copy(), {
            "method": "none",
            "target_width_strain": float(target_width),
            "target_width_percent": float(100.0 * target_width),
            "median_strain_step": float(median_dstrain),
            "window_points": None,
            "effective_span_strain": None,
            "effective_span_percent": None,
            "polyorder": None,
        }

    y_smooth = savgol_filter(
        y,
        window_length=window_points,
        polyorder=SAVGOL_POLYORDER,
        mode="interp",
    )

    # Approximate strain span from first to last point in the centered window.
    effective_span = (window_points - 1) * median_dstrain

    info = {
        "method": "Savitzky-Golay",
        "target_width_strain": float(target_width),
        "target_width_percent": float(100.0 * target_width),
        "median_strain_step": float(median_dstrain),
        "window_points": int(window_points),
        "effective_span_strain": float(effective_span),
        "effective_span_percent": float(100.0 * effective_span),
        "polyorder": int(SAVGOL_POLYORDER),
    }

    return y_smooth, info


def analyze_case(meta):
    d = meta["dir"]
    out = d / "output"
    post = d / "post"
    post.mkdir(exist_ok=True)

    eq = pd.read_csv(out / "equilibration.csv")
    m = pd.read_csv(out / "mechanics.csv")

    # Sort and remove duplicated strain values before smoothing.
    m = (
        m.sort_values("strain")
        .drop_duplicates("strain", keep="first")
        .reset_index(drop=True)
    )

    required_mech = {"strain", "sigma_zz_GPa"}
    missing_mech = required_mech.difference(m.columns)
    if missing_mech:
        raise ValueError(
            f"{out/'mechanics.csv'} missing columns: {sorted(missing_mech)}"
        )

    required_eq = {
        "time_ps",
        "temp_K",
        "press_bar",
        "pxx_bar",
        "pyy_bar",
        "pzz_bar",
    }
    missing_eq = required_eq.difference(eq.columns)
    if missing_eq:
        raise ValueError(
            f"{out/'equilibration.csv'} missing columns: {sorted(missing_eq)}"
        )

    # -----------------------------------------------------------------------
    # Strain-based stress smoothing
    # -----------------------------------------------------------------------
    sigma_smooth, smooth_info = smooth_by_strain(
        m["strain"].to_numpy(),
        m["sigma_zz_GPa"].to_numpy(),
        target_width=SMOOTH_WIDTH_STRAIN,
    )
    m["sigma_zz_smooth_GPa"] = sigma_smooth

    # -----------------------------------------------------------------------
    # Equilibration statistics from final 20 ps
    # -----------------------------------------------------------------------
    tmax = float(eq["time_ps"].max())
    eq_tail = eq[eq["time_ps"] >= tmax - 20.0]

    if eq_tail.empty:
        raise ValueError(
            f"No equilibration data found in final 20 ps for {meta['label']}"
        )

    eq_stats = {
        "T_mean_K": float(eq_tail["temp_K"].mean()),
        "T_std_K": float(eq_tail["temp_K"].std(ddof=1)),
        "P_mean_bar": float(eq_tail["press_bar"].mean()),
        "P_std_bar": float(eq_tail["press_bar"].std(ddof=1)),
        "Pxx_mean_bar": float(eq_tail["pxx_bar"].mean()),
        "Pyy_mean_bar": float(eq_tail["pyy_bar"].mean()),
        "Pzz_mean_bar": float(eq_tail["pzz_bar"].mean()),
    }

    # -----------------------------------------------------------------------
    # Elastic modulus: linear fit over 2-10% compressive strain
    # -----------------------------------------------------------------------
    fit = m[
        (m["strain"] >= ELASTIC_FIT_MIN)
        & (m["strain"] <= ELASTIC_FIT_MAX)
    ]

    if len(fit) >= 5:
        slope, intercept = np.polyfit(
            fit["strain"].to_numpy(),
            fit["sigma_zz_smooth_GPa"].to_numpy(),
            1,
        )
    else:
        slope = intercept = float("nan")

    # -----------------------------------------------------------------------
    # Yield point: maximum smoothed axial stress within 10-20% strain
    # -----------------------------------------------------------------------
    yw = m[
        (m["strain"] >= YIELD_SEARCH_MIN)
        & (m["strain"] <= YIELD_SEARCH_MAX)
    ]

    if yw.empty:
        raise ValueError(
            f"No data inside yield-search window for {meta['label']}"
        )

    iy = yw["sigma_zz_smooth_GPa"].idxmax()
    ye = float(m.loc[iy, "strain"])
    ys = float(m.loc[iy, "sigma_zz_smooth_GPa"])

    # -----------------------------------------------------------------------
    # Stress drop over the next 3% strain after yield
    # -----------------------------------------------------------------------
    upper_drop_strain = min(ye + POST_YIELD_DROP_WINDOW, FLOW_MAX)
    after = m[
        (m["strain"] >= ye)
        & (m["strain"] <= upper_drop_strain)
    ]

    post_min = (
        float(after["sigma_zz_smooth_GPa"].min())
        if not after.empty
        else float("nan")
    )

    # -----------------------------------------------------------------------
    # Flow stress over 20-25% strain
    # Use raw stress values: averaging already suppresses high-frequency noise.
    # -----------------------------------------------------------------------
    flow = m[
        (m["strain"] >= FLOW_MIN)
        & (m["strain"] <= FLOW_MAX)
    ]

    flow_mean = (
        float(flow["sigma_zz_GPa"].mean())
        if not flow.empty
        else float("nan")
    )
    flow_std = (
        float(flow["sigma_zz_GPa"].std(ddof=1))
        if len(flow) >= 2
        else float("nan")
    )

    metrics = {
        "case": meta["label"],
        "atoms": meta["atoms"],
        "strain_rate_s-1": meta["strain_rate_s-1"],
        "smoothing": smooth_info,
        "equilibration": eq_stats,
        "elastic_modulus_GPa_fit_2to10pct": float(slope),
        "elastic_fit_intercept_GPa": float(intercept),
        "yield_strain": ye,
        "yield_strain_percent": float(100.0 * ye),
        "yield_stress_GPa": ys,
        "stress_drop_GPa_next_3pct": float(ys - post_min),
        "flow_stress_mean_GPa_20to25pct": flow_mean,
        "flow_stress_std_GPa_20to25pct": flow_std,
    }

    m.to_csv(post / "mechanics_processed.csv", index=False)
    (post / "metrics.json").write_text(json.dumps(metrics, indent=2))

    return metrics


if __name__ == "__main__":
    all_metrics = []

    for meta in find_cases():
        try:
            met = analyze_case(meta)
            all_metrics.append(met)

            sm = met["smoothing"]
            wtxt = (
                f"{sm['window_points']} points "
                f"(~{sm['effective_span_percent']:.3f}% strain)"
                if sm["window_points"] is not None
                else "no smoothing"
            )

            print(
                f"OK: {meta['label']} | "
                f"yield = {met['yield_stress_GPa']:.3f} GPa "
                f"at {met['yield_strain_percent']:.2f}% | "
                f"smoothing = {wtxt}"
            )

        except FileNotFoundError as e:
            print(f"SKIP {meta['label']}: missing {e.filename}")

        except Exception as e:
            print(f"ERROR {meta['label']}: {e}")
            raise

    if all_metrics:
        summary_path = Path(__file__).with_name("mechanical_summary.json")
        summary_path.write_text(json.dumps(all_metrics, indent=2))
        print(f"Wrote {summary_path}")
