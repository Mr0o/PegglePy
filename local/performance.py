from collections import deque
from contextlib import contextmanager
from math import ceil
from time import perf_counter_ns
from typing import Generator


DISPLAY_METRICS = (
    ("frame_cpu", "Frame CPU"),
    ("input_events", "Input/events"),
    ("aim_input", "Aim/input processing"),
    ("gameplay_update", "Gameplay update"),
    ("animation_schedule", "Animation scheduling"),
    ("animation_update", "Animation frame work"),
    ("animation_generation", "Animation generation"),
    ("aim_prediction", "Aim/trajectory"),
    ("zenball_search", "Zenball search"),
    ("physics_frame", "Physics total"),
    ("physics_step", "Physics / step"),
    ("peg_timer_scan", "Active stuck-timer scan"),
    ("collision_query", "Collision query/resolve"),
    ("ball_update", "Ball update"),
    ("static_image_update", "Static image update"),
    ("static_image_build", "Static image build (last)"),
    ("quadtree_build", "Quadtree build (last)"),
    ("peg_state_reset", "Peg reset/color (last)"),
    ("round_reset_total", "Round reset total (last)"),
    ("static_peg_layer", "Peg layer blit"),
    ("animation_layer", "Animation layer blit"),
    ("bucket_render", "Bucket render"),
    ("ball_render", "Ball render"),
    ("trajectory_render", "Trajectory render"),
    ("zoom_render", "Zoom render"),
    ("scoreboard_render", "Scoreboard render"),
    ("world_render", "World render total"),
    ("game_overlay_render", "Game overlay"),
    ("debug_render", "Debug overlay"),
    ("performance_overlay", "Metrics overlay"),
    ("display_present", "Display present"),
)

PERFORMANCE_COLUMNS = (
    (
        "FRAME AND SIMULATION",
        (
            "frame_cpu",
            "input_events",
            "aim_input",
            "gameplay_update",
            "animation_schedule",
            "animation_update",
            "animation_generation",
            "aim_prediction",
            "zenball_search",
            "physics_frame",
            "physics_step",
            "peg_timer_scan",
            "collision_query",
            "ball_update",
            "display_present",
        ),
    ),
    (
        "RENDERING AND LEVEL SETUP",
        (
            "static_image_update",
            "static_image_build",
            "quadtree_build",
            "peg_state_reset",
            "round_reset_total",
            "static_peg_layer",
            "animation_layer",
            "bucket_render",
            "ball_render",
            "trajectory_render",
            "zoom_render",
            "scoreboard_render",
            "world_render",
            "game_overlay_render",
            "debug_render",
            "performance_overlay",
        ),
    ),
)

PER_FRAME_METRICS = frozenset(
    (
        "frame_cpu",
        "input_events",
        "aim_input",
        "gameplay_update",
        "animation_schedule",
        "animation_update",
        "animation_generation",
        "aim_prediction",
        "zenball_search",
        "physics_frame",
        "physics_step",
        "peg_timer_scan",
        "collision_query",
        "ball_update",
        "static_image_update",
        "static_peg_layer",
        "animation_layer",
        "bucket_render",
        "ball_render",
        "trajectory_render",
        "zoom_render",
        "scoreboard_render",
        "world_render",
        "game_overlay_render",
        "debug_render",
        "performance_overlay",
        "display_present",
    )
)

METRIC_THRESHOLDS_MS = {
    "frame_cpu": (12.0, 16.7),
    "physics_frame": (6.0, 12.0),
    "physics_step": (2.0, 5.0),
    "peg_timer_scan": (2.0, 5.0),
    "collision_query": (2.0, 5.0),
    "ball_update": (1.0, 3.0),
    "animation_schedule": (5.0, 15.0),
    "animation_update": (2.0, 5.0),
    "animation_generation": (2.0, 5.0),
    "aim_prediction": (2.0, 5.0),
    "zenball_search": (7.0, 9.0),
    "static_image_update": (5.0, 15.0),
    "static_image_build": (20.0, 75.0),
    "quadtree_build": (15.0, 50.0),
    "peg_state_reset": (15.0, 50.0),
    "round_reset_total": (50.0, 150.0),
    "static_peg_layer": (2.0, 6.0),
    "animation_layer": (2.0, 6.0),
    "bucket_render": (1.0, 3.0),
    "ball_render": (1.0, 3.0),
    "trajectory_render": (2.0, 5.0),
    "zoom_render": (3.0, 8.0),
    "scoreboard_render": (1.0, 3.0),
    "world_render": (5.0, 12.0),
    "game_overlay_render": (1.0, 3.0),
    "debug_render": (2.0, 5.0),
}


class PerformanceMetrics:
    WINDOW_SIZE = 240

    def __init__(self) -> None:
        self._samples: dict[str, deque[float]] = {}
        self._frame_samples: dict[str, float] | None = None

    def begin_frame(self) -> None:
        self._frame_samples = {name: 0.0 for name in PER_FRAME_METRICS}

    def end_frame(self) -> None:
        if self._frame_samples is None:
            return
        for name, elapsed_ms in self._frame_samples.items():
            self._append_sample(name, elapsed_ms)
        self._frame_samples = None

    @contextmanager
    def measure(self, name: str) -> Generator[None, None, None]:
        start = perf_counter_ns()
        try:
            yield
        finally:
            self.record_ms(name, (perf_counter_ns() - start) / 1_000_000)

    def record_ms(self, name: str, elapsed_ms: float) -> None:
        elapsed_ms = max(0.0, elapsed_ms)
        if self._frame_samples is not None and name in self._frame_samples:
            self._frame_samples[name] += elapsed_ms
            return
        self._append_sample(name, elapsed_ms)

    def _append_sample(self, name: str, elapsed_ms: float) -> None:
        samples = self._samples.get(name)
        if samples is None:
            samples = deque(maxlen=self.WINDOW_SIZE)
            self._samples[name] = samples
        samples.append(elapsed_ms)

    def record_since(self, name: str, start_ns: int) -> None:
        self.record_ms(
            name,
            (perf_counter_ns() - start_ns) / 1_000_000,
        )

    def summary(self, name: str) -> tuple[float, float, float]:
        samples = self._samples.get(name)
        if not samples:
            return 0.0, 0.0, 0.0

        ordered = sorted(samples)
        p95_index = min(len(ordered) - 1, ceil(len(ordered) * 0.95) - 1)
        return samples[-1], ordered[p95_index], max(ordered)

    @staticmethod
    def severity(name: str, p95_ms: float) -> str:
        thresholds = METRIC_THRESHOLDS_MS.get(name)
        if thresholds is None:
            return "normal"
        warning_ms, critical_ms = thresholds
        if p95_ms >= critical_ms:
            return "red"
        if p95_ms >= warning_ms:
            return "yellow"
        return "normal"
