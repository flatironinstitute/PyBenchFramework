#!/usr/bin/env python3
"""
fio_plotting.py

Generate SVG plots from fio JSON result directories.

INPUT SHAPE
-----------
You pass job_dir_list as a "list of rows", where each row is a list of job output directories.
Example (N=1 per row):
    job_dir_list = [
        ["../results/write/cephtest-rep3-kernel/5870457"],
        ["../results/randread/cephtest-rep3-kernel/5870457"],
    ]

Example (N=3 per row; side-by-side subplots in ONE SVG):
    job_dir_list = [
        ["../results/write/cephtest-rep3-kernel/5675920",
         "../results/write/cephtest-rep3-kernel/5820837",
         "../results/write/cephtest-rep3-kernel/5870457"],
    ]

WHAT GETS WRITTEN
-----------------
For each row in job_dir_list, we write ONE SVG that contains a grid:

    rows = 1 + (# latency measures detected/present)
    cols = N  (N = number of job dirs in that row)

Top row (per column/job_dir):
    - Bandwidth (GiB/s) vs nodes (left axis)
    - IOPS vs nodes (right axis; scaled to match bandwidth using block size "bs")

Latency rows (per column/job_dir):
    - Mean slat (ms) vs nodes
    - Mean clat (ms) vs nodes
    - Mean lat  (ms) vs nodes
    - Mean sync (ms) vs nodes   (WRITE JOBS ONLY; from jobs[0]['sync'] if present and not all zeros)

AGGREGATION LOGIC
-----------------
Each job output directory contains multiple fio JSON files (one per runner).
We group runners by (node_count, job_count) and then:
    - Sum bandwidth + IOPS across runners in the group
    - Compute each latency as a WEIGHTED MEAN by N:
          mean_total = sum(mean_i * N_i) / sum(N_i)

IMPORTANT: You should NOT sum latencies.

NOTES / EXTENSIONS
------------------
- Hockey-stick effects are often clearer in tail latency (p95/p99).
  fio's clat typically includes percentiles. If you want p95/p99 plots,
  we can add those as additional rows.
- latency_yscale="log" can help make inflection points visually obvious.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt


# -----------------------------------------------------------------------------
# 1) Find/represent fio json files in a job output directory
# -----------------------------------------------------------------------------

def return_FIO_job_results_objects(job_dir, block_size):
    """
    Given a job output directory, find all fio JSON result files matching the naming
    pattern and return a list of FIO_runner_ob objects that point to those files.

    Returns an empty list if no files match or the directory doesn't exist.
    """

    # Your naming convention regex:
    #   worker7410_11_24_16p_16f_4M.json
    file_pattern = r"[a-z]+[0-9]+_[0-9]+_[0-9]+_[0-9]+p_[0-9]+f_{}\.json".format(block_size)

    try:
        files = [f for f in os.listdir(job_dir) if re.search(file_pattern, f)]
    except FileNotFoundError:
        print(f"[ERROR] job_dir not found: {job_dir}")
        return []

    if not files:
        print(f"[WARN] No fio json files matched pattern in: {job_dir}")
        return []

    class FIO_runner_ob:
        """
        One object per fio JSON file in the directory.

        Parsed from filename:
          - hostname
          - local_rank
          - node_count
          - job_count (parsed from '<job_count>p' segment)
        """
        def __init__(self, hostname, local_rank, node_count, job_count, fio_json_file):
            self.hostname = hostname
            self.local_rank = int(local_rank)
            self.node_count = int(node_count)
            self.job_count = int(job_count)
            self.fio_dict = None
            self.fio_json_file = fio_json_file

        def load_FIO_json(self):
            """Load JSON into self.fio_dict with basic error handling."""
            try:
                with open(self.fio_json_file, "r") as f:
                    self.fio_dict = json.load(f)
            except FileNotFoundError:
                print(f"[ERROR] JSON file not found: {self.fio_json_file}")
                self.fio_dict = None
            except json.JSONDecodeError:
                print(f"[ERROR] Could not decode JSON: {self.fio_json_file}")
                self.fio_dict = None

    runner_list = []

    # Deterministic ordering
    for filename in sorted(files):
        parts = filename.split("_")

        hostname = parts[0]
        local_rank = parts[1]
        node_count = parts[2]
        job_count = parts[3].split("p")[0]  # "16p" -> "16"

        file_path = os.path.join(job_dir, filename)
        runner_list.append(FIO_runner_ob(hostname, local_rank, node_count, job_count, file_path))

    return runner_list


# -----------------------------------------------------------------------------
# 2) Helpers for fio conventions / extracting metrics
# -----------------------------------------------------------------------------

def _fio_io_key(jobname):
    """
    fio stores results under keys 'read' and 'write' even if jobname is 'randread'/'randwrite'.

    Maps:
      - randread  -> read
      - randwrite -> write
      - read/write stay as-is
    """
    j = (jobname or "").lower()
    if "read" in j:
        return "read"
    if "write" in j:
        return "write"
    return j


def _parse_size_to_bytes(size_str):
    """
    Parse fio-like size strings into bytes (binary units):
      '4M'   -> 4 * 1024^2
      '512k' -> 512 * 1024
      '1G'   -> 1 * 1024^3
      '4096' -> 4096

    Raises ValueError if it can't parse.
    """
    if size_str is None:
        return None

    s = str(size_str).strip()
    m = re.match(r"^(\d+(?:\.\d+)?)([kKmMgGtT]?)$", s)
    if not m:
        raise ValueError(f"Unrecognized size string: {size_str}")

    val = float(m.group(1))
    suf = m.group(2).lower()

    mult = 1
    if suf == "k":
        mult = 1024
    elif suf == "m":
        mult = 1024 ** 2
    elif suf == "g":
        mult = 1024 ** 3
    elif suf == "t":
        mult = 1024 ** 4

    return int(val * mult)


# We want to plot all latency measures commonly available in fio results PLUS write "sync" latency.
# Standard fio latencies are per-IO read/write stats: slat, clat, lat.
# Additionally, for WRITE jobs fio may report a top-level jobs[0]['sync'] dict with its own lat_*.
LATENCY_MEASURES = ("slat", "clat", "lat", "sync")

# fio may report latencies in ns/us/ms depending on version/options.
# We'll detect whichever unit exists and convert everything to ms.
_UNIT_TO_MS = {
    "ns": 1e-6,
    "us": 1e-3,
    "ms": 1.0,
}


def _extract_latency_means_ms(io_stats, measures=("slat", "clat", "lat")):
    """
    Extract mean latency in milliseconds for each requested measure in `measures`.

    io_stats is typically jobs[0]['read'] or jobs[0]['write'] dict.

    For each measure (slat/clat/lat), fio usually provides one of:
      - slat_ns / slat_us / slat_ms
      - clat_ns / clat_us / clat_ms
      - lat_ns  / lat_us  / lat_ms

    Each of these dicts typically includes:
      {'min','max','mean','stddev','N', ...}

    Returns:
      dict: measure -> (mean_ms, N)

    If a measure is missing, it won't appear in the output dict.
    """
    out = {}

    for measure in measures:
        found = False
        for unit, factor in _UNIT_TO_MS.items():
            key = f"{measure}_{unit}"
            if key in io_stats and isinstance(io_stats[key], dict):
                mean = io_stats[key].get("mean", None)
                N = io_stats[key].get("N", 0)

                # Defensive conversion
                try:
                    mean = float(mean) if mean is not None else None
                except (TypeError, ValueError):
                    mean = None

                try:
                    N = int(N)
                except (TypeError, ValueError):
                    N = 0

                if mean is not None and N > 0:
                    out[measure] = (mean * factor, N)  # convert to ms

                found = True
                break

        if not found:
            continue

    return out


def _sync_latency_is_all_zeros(lat_dict):
    """
    Determine whether a fio sync latency dict appears to be "all zeros".

    We consider it "all zeros" if all of min/max/mean/stddev are zero or missing.
    This is a practical heuristic to skip plotting meaningless sync latency rows.
    """
    if not isinstance(lat_dict, dict):
        return True

    def _f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0

    min_v = _f(lat_dict.get("min", 0))
    max_v = _f(lat_dict.get("max", 0))
    mean_v = _f(lat_dict.get("mean", 0))
    std_v = _f(lat_dict.get("stddev", 0))

    return (min_v == 0.0 and max_v == 0.0 and mean_v == 0.0 and std_v == 0.0)


def _extract_sync_latency_mean_ms(job0):
    """
    Extract write "sync" latency mean (ms) and N from jobs[0]['sync'] if it exists and is valid.

    In fio JSON, sync dict often looks like:
      "sync": {
        "total_ios": 209,
        "lat_ns": {"min":..., "max":..., "mean":..., "stddev":..., "N":..., ...}
      }

    Returns:
      (mean_ms, N) if present and not all zeros, else None.
    """
    sync = job0.get("sync", None)
    if not isinstance(sync, dict):
        return None

    # sync latency is stored as 'lat_ns' / 'lat_us' / 'lat_ms' (NOT 'sync_ns' etc)
    for unit, factor in _UNIT_TO_MS.items():
        key = f"lat_{unit}"
        if key in sync and isinstance(sync[key], dict):
            lat_dict = sync[key]

            # Skip if it looks like it's all zeros
            if _sync_latency_is_all_zeros(lat_dict):
                return None

            mean = lat_dict.get("mean", None)
            N = lat_dict.get("N", None)

            # Some fio versions also provide total_ios; use as fallback if N missing.
            if N is None:
                N = sync.get("total_ios", 0)

            try:
                mean = float(mean) if mean is not None else None
            except (TypeError, ValueError):
                mean = None

            try:
                N = int(N)
            except (TypeError, ValueError):
                N = 0

            # Require something sensible
            if mean is None or N <= 0:
                return None

            return (mean * factor, N)  # convert to ms

    return None


def _extract_bw_iops_bs_and_date_and_latencies(fio_dict, measures=LATENCY_MEASURES):
    """
    Extract bandwidth, IOPS, block size, date, and requested latency measures from a fio JSON dict.

    Returns:
      bw_bytes (int)                   bytes/sec
      iops (float)
      bs_bytes (int or None)           parsed from global options 'bs'
      jobname (str)
      date_str (str or None)           mm/dd/YYYY if parseable
      latencies_ms (dict)              measure -> (mean_ms, N)

    Special handling:
      - For WRITE jobs, if jobs[0]['sync'] exists and has non-zero latency stats,
        we add measure "sync" to latencies_ms.
    """
    job0 = fio_dict["jobs"][0]
    jobname = job0.get("jobname", "")
    io_key = _fio_io_key(jobname)

    io_stats = job0.get(io_key, {})

    # Prefer bw_bytes (bytes/sec). If missing, fall back to bw (KiB/sec).
    bw_bytes = io_stats.get("bw_bytes", None)
    if bw_bytes is None:
        bw_kib = io_stats.get("bw", 0)  # KiB/sec
        bw_bytes = int(bw_kib) * 1024
    else:
        bw_bytes = int(bw_bytes)

    iops = float(io_stats.get("iops", 0.0))

    # Block size for mapping bandwidth <-> IOPS on matched axes.
    bs_str = fio_dict.get("global options", {}).get("bs", None)
    bs_bytes = _parse_size_to_bytes(bs_str) if bs_str else None

    # Latencies from standard fio per-IO stats (slat/clat/lat)
    std_measures = [m for m in measures if m in ("slat", "clat", "lat")]
    latencies_ms = _extract_latency_means_ms(io_stats, measures=std_measures)

    # If this is a write job, optionally add sync latency
    if io_key == "write" and "sync" in measures:
        sync_tuple = _extract_sync_latency_mean_ms(job0)
        if sync_tuple is not None:
            latencies_ms["sync"] = sync_tuple

    # fio's "time" often looks like: "Fri Jan 23 16:57:40 2026"
    date_str = None
    t = fio_dict.get("time", None)
    if t:
        try:
            dt = datetime.strptime(t, "%a %b %d %H:%M:%S %Y")
            date_str = dt.strftime("%m/%d/%Y")
        except ValueError:
            date_str = None

    return bw_bytes, iops, bs_bytes, jobname, date_str, latencies_ms


# -----------------------------------------------------------------------------
# 3) Aggregation: sum BW/IOPS, weighted-mean latency per measure across runners
# -----------------------------------------------------------------------------

def _aggregate_job_dir(job_dir, block_size, measures=LATENCY_MEASURES):
    """
    Load all runner JSONs in one job_dir and aggregate by (job_count, node_count).

    Output structure:
      agg[job_count][node_count] = {
          "bw_gib_s": float,                 summed across runners
          "iops": float,                     summed across runners
          "lat_mean_ms": {measure: float},   weighted mean (ms) by N for EACH measure
      }

    Weighted mean latency:
      mean_total = sum(mean_i * N_i) / sum(N_i)
    """
    runners = return_FIO_job_results_objects(job_dir, block_size)
    if not runners:
        return None

    # Accumulator per (job_count, node_count)
    acc = defaultdict(lambda: defaultdict(lambda: {
        "bw_bytes": 0,
        "iops": 0.0,
        "lat_wsum_ms": defaultdict(float),  # measure -> sum(mean_ms * N)
        "lat_N": defaultdict(int),          # measure -> sum(N)
    }))

    bs_bytes = None
    jobname = None
    date_str = None

    n_loaded = 0

    for r in runners:
        r.load_FIO_json()
        if not r.fio_dict:
            continue

        n_loaded += 1

        bw_bytes, iops, this_bs, this_jobname, this_date, latencies_ms = \
            _extract_bw_iops_bs_and_date_and_latencies(r.fio_dict, measures=measures)

        # Metadata: fill once (assumes consistent within job_dir)
        if bs_bytes is None and this_bs is not None:
            bs_bytes = this_bs
        if jobname is None and this_jobname:
            jobname = this_jobname
        if date_str is None and this_date:
            date_str = this_date

        cell = acc[r.job_count][r.node_count]
        cell["bw_bytes"] += int(bw_bytes)
        cell["iops"] += float(iops)

        # Add latency contributions for ALL measures found in this file
        for measure, (mean_ms, N) in latencies_ms.items():
            if mean_ms is None or N <= 0:
                continue
            cell["lat_wsum_ms"][measure] += float(mean_ms) * int(N)
            cell["lat_N"][measure] += int(N)

    if n_loaded == 0:
        print(f"[WARN] No JSON files successfully loaded in {job_dir}")
        return None

    # Convert to plot-friendly structure
    agg_out = defaultdict(dict)

    # Track which measures were actually observed in this job_dir
    measures_seen = set()

    for job_ct, node_map in acc.items():
        for node_ct, vals in node_map.items():
            bw_gib_s = vals["bw_bytes"] / (1024 ** 3)

            lat_mean_ms = {}
            for measure in measures:
                Ntot = vals["lat_N"].get(measure, 0)
                if Ntot > 0:
                    lat_mean_ms[measure] = vals["lat_wsum_ms"][measure] / Ntot
                    measures_seen.add(measure)

            agg_out[job_ct][node_ct] = {
                "bw_gib_s": bw_gib_s,
                "iops": vals["iops"],
                "lat_mean_ms": lat_mean_ms,  # dict per measure
            }

    return {
        "job_dir": job_dir,
        "agg": agg_out,
        "bs_bytes": bs_bytes,
        "jobname": jobname,
        "date_str": date_str,
        "measures_seen": sorted(measures_seen),
    }


# -----------------------------------------------------------------------------
# 4) Plotting
# -----------------------------------------------------------------------------

def _slugify(s):
    """Make a safe-ish filename slug."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")


def updated_FIO_plotting(
    job_dir_list,
    block_size,
    output_dir="fio_svgs",
    latency_measures=LATENCY_MEASURES,
    latency_yscale="linear",
):
    """
    For each element in job_dir_list (a list of job output directories),
    write ONE SVG that contains a grid:

      - TOP ROW (per job_dir): bandwidth (GiB/s) vs nodes + twin y-axis IOPS
      - One row per latency measure present across these job_dirs:
          mean latency (ms) vs nodes
        This includes "sync" only if it is detected (write jobs w/ non-zero sync stats).

    latency_measures:
      Default: ("slat","clat","lat","sync")  -> all standard + optional write-sync.

    latency_yscale:
      - "linear" (default)
      - "log" can make hockey-stick inflection easier to see
    """
    os.makedirs(output_dir, exist_ok=True)

    for job_dirs in job_dir_list:
        # 1) Aggregate each job_dir in this row
        run_infos = []
        for jd in job_dirs:
            info = _aggregate_job_dir(jd, block_size, measures=latency_measures)
            if info is not None:
                run_infos.append(info)

        if not run_infos:
            print(f"[WARN] No usable runs found for row: {job_dirs}")
            continue

        ncols = len(run_infos)

        # Determine which latency measures are actually present across these runs (union)
        measures_present = set()
        for info in run_infos:
            measures_present.update(info.get("measures_seen", []))

        # Keep requested order but only plot those actually present
        measures_to_plot = [m for m in latency_measures if m in measures_present]

        # If none found, we still plot bandwidth only (rows=1)
        n_latency_rows = len(measures_to_plot)
        nrows = 1 + n_latency_rows

        # 2) Create subplot grid
        fig_height = 3.0 * nrows + 2.0
        fig_width = 6.5 * ncols

        fig, axes = plt.subplots(
            nrows, ncols,
            figsize=(fig_width, fig_height),
            sharex="col",
            sharey="row",
        )

        # Normalize axes indexing so axes[row][col] always works
        if nrows == 1 and ncols == 1:
            axes = [[axes]]
        elif nrows == 1:
            axes = [list(axes)]
        elif ncols == 1:
            axes = [[axes[r]] for r in range(nrows)]

        # 3) Compute global y-limits (bandwidth + per-latency-measure) for linear mode
        global_max_bw = 0.0
        global_max_lat = {m: 0.0 for m in measures_to_plot}

        for info in run_infos:
            for job_ct, node_map in info["agg"].items():
                for _, vals in node_map.items():
                    global_max_bw = max(global_max_bw, vals["bw_gib_s"])
                    for m in measures_to_plot:
                        lm = vals["lat_mean_ms"].get(m, None)
                        if lm is not None:
                            global_max_lat[m] = max(global_max_lat[m], lm)

        bw_ymax = global_max_bw * 1.10 if global_max_bw > 0 else 1.0
        lat_ymax = {
            m: (global_max_lat[m] * 1.10 if global_max_lat[m] > 0 else 1.0)
            for m in measures_to_plot
        }

        # 4) Plot each job_dir as a column
        for col, info in enumerate(run_infos):
            agg = info["agg"]
            bs_bytes = info["bs_bytes"]

            # -------------------------
            # ROW 0: Bandwidth + IOPS
            # -------------------------
            ax_bw = axes[0][col]

            # One line per job_count
            for job_ct in sorted(agg.keys()):
                node_counts = sorted(agg[job_ct].keys())
                bw_series = [agg[job_ct][nc]["bw_gib_s"] for nc in node_counts]

                ax_bw.plot(
                    node_counts,
                    bw_series,
                    marker="o",
                    linewidth=2,
                    label=f"{job_ct}_jobs",
                )

            ax_bw.set_ylabel("GiB/s")
            ax_bw.set_ylim(0, bw_ymax)
            ax_bw.grid(True, alpha=0.3)

            # Right axis: IOPS (scaled to match bandwidth)
            ax_iops = ax_bw.twinx()
            ax_iops.set_ylabel("IOPS")

            if bs_bytes:
                # Exact mapping:
                #   bytes/sec = GiB/s * 1024^3
                #   iops      = (bytes/sec) / bs_bytes
                iops_per_gib = (1024 ** 3) / bs_bytes
                y0, y1 = ax_bw.get_ylim()
                ax_iops.set_ylim(y0 * iops_per_gib, y1 * iops_per_gib)
            else:
                # Fallback scaling if bs missing: use observed max ratio (less ideal)
                max_iops = 0.0
                max_bw = 0.0
                for job_ct2, node_map in agg.items():
                    for _, vals in node_map.items():
                        max_bw = max(max_bw, vals["bw_gib_s"])
                        max_iops = max(max_iops, vals["iops"])
                scale = (max_iops / max_bw) if max_bw > 0 else 1.0
                y0, y1 = ax_bw.get_ylim()
                ax_iops.set_ylim(y0 * scale, y1 * scale)

            # Title for the column (top axis only)
            p = Path(info["job_dir"])
            run_id = p.name
            cfg = p.parent.name
            op = p.parent.parent.name
            d = info["date_str"] or ""
            ax_bw.set_title(f"{cfg}\n{op}  {run_id}\n{d}".strip())

            # Legend once (applies to all rows since labels are the same job_count lines)
            if col == 0:
                ax_bw.legend(title="Type of run")

            # -------------------------
            # ROWS 1..: Latency measures
            # -------------------------
            for r_i, measure in enumerate(measures_to_plot, start=1):
                ax_lat = axes[r_i][col]

                for job_ct in sorted(agg.keys()):
                    node_counts = sorted(agg[job_ct].keys())

                    x = []
                    y = []
                    for nc in node_counts:
                        lm = agg[job_ct][nc]["lat_mean_ms"].get(measure, None)
                        if lm is None:
                            continue

                        # For log scale, skip non-positive values
                        if latency_yscale == "log" and lm <= 0:
                            continue

                        x.append(nc)
                        y.append(lm)

                    if not x:
                        continue

                    ax_lat.plot(
                        x,
                        y,
                        marker="o",
                        linewidth=2,
                        label=f"{job_ct}_jobs",
                    )

                ax_lat.set_ylabel(f"Mean {measure} (ms)")
                ax_lat.grid(True, alpha=0.3)

                if latency_yscale == "log":
                    ax_lat.set_yscale("log")
                else:
                    ax_lat.set_ylim(0, lat_ymax[measure])

                # Put x-label only on the bottom row for cleanliness
                if r_i == nrows - 1:
                    ax_lat.set_xlabel("nodes")

        # 5) Save SVG for this row
        ops = [Path(info["job_dir"]).parent.parent.name for info in run_infos]
        cfgs = [Path(info["job_dir"]).parent.name for info in run_infos]
        common_op = ops[0] if all(o == ops[0] for o in ops) else "mixed_ops"
        common_cfg = cfgs[0] if all(c == cfgs[0] for c in cfgs) else "mixed_cfg"

        run_ids = [Path(info["job_dir"]).name for info in run_infos]
        lat_tag = "-".join(measures_to_plot) if measures_to_plot else "no-lat"
        base_name = f"{common_op}_{common_cfg}__" + "_".join(run_ids) + f"__lat_{lat_tag}_{latency_yscale}"

        fig.suptitle(f"{common_cfg} - {common_op} (latency={lat_tag}, y={latency_yscale})", fontsize=14)
        fig.tight_layout(rect=[0, 0.02, 1, 0.95])

        svg_path = os.path.join(output_dir, _slugify(base_name) + ".svg")
        fig.savefig(svg_path, format="svg")
        plt.close(fig)

        print(f"[OK] wrote {svg_path}")


# -----------------------------------------------------------------------------
# Example usage (commented)
# -----------------------------------------------------------------------------
#
# job_dir_list = [
#     ["../results/write/cephtest-rep3-kernel/5870457"],
#     ["../results/randread/cephtest-rep3-kernel/5870457"],
#     ["../results/write/cephtest-rep3-kernel/5675920",
#      "../results/write/cephtest-rep3-kernel/5820837",
#      "../results/write/cephtest-rep3-kernel/5870457"],
# ]
#
# # Linear latency:
# updated_FIO_plotting(job_dir_list, output_dir="fio_svgs", latency_yscale="linear")
#
# # Log latency (often better for spotting "hockey stick" effects):
# updated_FIO_plotting(job_dir_list, output_dir="fio_svgs", latency_yscale="log")
#

