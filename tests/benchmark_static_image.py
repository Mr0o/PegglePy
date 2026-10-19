"""Compare full peg-layer redraws with incremental peg updates.

Run from the repository root:
    python tests/benchmark_static_image.py --pegs 1000 2500 5000
"""

import argparse
import math
import os
import random
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from local.misc import createStaticImage, updateStaticImagePegs
from local.peg import Peg
from local.userConfig import configs


def _percentile(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    index = min(math.ceil(percentile * len(ordered)) - 1, len(ordered) - 1)
    return ordered[index]


def _make_pegs(count: int, seed: int) -> list[Peg]:
    rng = random.Random(seed)
    colors = ("blue", "orange", "green")
    return [
        _make_peg(
            rng.randrange(0, configs["WIDTH"]),
            rng.randrange(0, configs["HEIGHT"]),
            colors[index % len(colors)],
        )
        for index in range(count)
    ]


def _make_peg(x: int, y: int, color: str) -> Peg:
    peg = Peg(x, y)
    peg.set_color(color)
    return peg


def _measure_case(peg_count: int, changes: int, iterations: int) -> None:
    baseline_pegs = _make_pegs(peg_count, 2026)
    incremental_pegs = _make_pegs(peg_count, 2026)
    baseline_image = createStaticImage(
        baseline_pegs, track_changes=False
    )
    incremental_image = createStaticImage(incremental_pegs)
    baseline_times = []
    incremental_times = []

    for iteration in range(iterations):
        count = min(changes, len(baseline_pegs), len(incremental_pegs))
        baseline_removed = baseline_pegs[:count]
        incremental_removed = incremental_pegs[:count]
        baseline_pegs = baseline_pegs[count:]
        incremental_pegs = incremental_pegs[count:]

        start = time.perf_counter()
        baseline_image = createStaticImage(
            baseline_pegs, track_changes=False
        )
        baseline_times.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        updateStaticImagePegs(
            incremental_image,
            incremental_pegs,
            [],
            incremental_removed,
        )
        incremental_times.append((time.perf_counter() - start) * 1000)

    if pygame.image.tobytes(baseline_image, "RGBA") != pygame.image.tobytes(
        incremental_image, "RGBA"
    ):
        raise AssertionError(
            f"incremental surface differs from full redraw ({peg_count} pegs)"
        )

    baseline_median = statistics.median(baseline_times)
    incremental_median = statistics.median(incremental_times)
    speedup = baseline_median / incremental_median if incremental_median else float("inf")
    print(
        f"{peg_count:>5} pegs | "
        f"full redraw p50/p95/max "
        f"{baseline_median:7.3f}/{_percentile(baseline_times, 0.95):7.3f}/"
        f"{max(baseline_times):7.3f} ms | "
        f"incremental {incremental_median:7.3f}/"
        f"{_percentile(incremental_times, 0.95):7.3f}/"
        f"{max(incremental_times):7.3f} ms | "
        f"median speedup {speedup:.2f}x"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pegs", type=int, nargs="+", default=[1000, 2500, 5000])
    parser.add_argument("--changes", type=int, default=24)
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()

    if args.changes < 1 or args.iterations < 1:
        parser.error("--changes and --iterations must be positive")

    configs["WIDTH"] = 960
    configs["HEIGHT"] = 720
    print("Static peg layer update timing (ms; p50/p95/max)")
    print(f"removing up to {args.changes} pegs in each of {args.iterations} batches")
    for peg_count in args.pegs:
        if peg_count < 1:
            parser.error("--pegs values must be positive")
        _measure_case(peg_count, args.changes, args.iterations)

    pygame.quit()


if __name__ == "__main__":
    main()
