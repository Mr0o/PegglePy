from __future__ import annotations

from math import cos, pi
from math import hypot
from math import isfinite

from local.vectors import Vector


DEFAULT_MOVING_PEG_SPEED = 2.0
MIN_MOVING_PEG_SPEED = 0.25


class MovingPegPath:
    """An eased Bezier or Catmull-Rom path with looping or ping-pong traversal."""

    SAMPLE_COUNT = 64
    EASING_TYPES = ("linear", "ease-in", "ease-out", "ease-in-out")
    TRAVERSAL_TYPES = ("ping-pong", "loop")

    def __init__(
        self,
        points: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        speed: float = DEFAULT_MOVING_PEG_SPEED,
        curve_type: str = "cubic-bezier",
        easing: str = "linear",
        traversal: str = "ping-pong",
    ):
        if curve_type == "cubic-bezier" and len(points) != 4:
            raise ValueError("A cubic-bezier path requires exactly four control points")
        if curve_type == "catmull-rom" and len(points) < 2:
            raise ValueError("A catmull-rom path requires at least two route points")
        if curve_type not in ("cubic-bezier", "catmull-rom"):
            raise ValueError(f"Unsupported moving peg curve type: {curve_type}")
        if easing not in self.EASING_TYPES:
            raise ValueError(f"Unsupported moving peg easing: {easing}")
        if traversal not in self.TRAVERSAL_TYPES:
            raise ValueError(f"Unsupported moving peg traversal: {traversal}")
        if speed <= 0:
            raise ValueError("Moving peg speed must be greater than zero")

        self.curve_type = curve_type
        self.easing = easing
        self.traversal = traversal
        self.points = tuple((float(x), float(y)) for x, y in points)
        if any(not isfinite(x) or not isfinite(y) for x, y in self.points):
            raise ValueError("Moving peg control points must be finite")
        if not isfinite(speed):
            raise ValueError("Moving peg speed must be finite")
        self.speed = float(speed)
        self.distance = 0.0
        self.direction = 1.0
        self._phase = 0.0
        self._rebuild_samples()
        if self.length == 0:
            raise ValueError("A moving peg path must have nonzero length")

    def _bezier(self, t: float) -> tuple[float, float]:
        inverse = 1.0 - t
        weights = (inverse**3, 3 * inverse**2 * t, 3 * inverse * t**2, t**3)
        return (
            sum(weight * point[0] for weight, point in zip(weights, self.points)),
            sum(weight * point[1] for weight, point in zip(weights, self.points)),
        )

    def _catmull_rom(self, t: float, closed: bool = False) -> tuple[float, float]:
        segment_count = len(self.points) if closed else len(self.points) - 1
        scaled_t = min(max(t, 0.0), 1.0) * segment_count
        segment_index = min(int(scaled_t), segment_count - 1)
        local_t = scaled_t - segment_index
        if closed:
            p0 = self.points[(segment_index - 1) % len(self.points)]
            p1 = self.points[segment_index % len(self.points)]
            p2 = self.points[(segment_index + 1) % len(self.points)]
            p3 = self.points[(segment_index + 2) % len(self.points)]
        else:
            p0 = self.points[max(segment_index - 1, 0)]
            p1 = self.points[segment_index]
            p2 = self.points[segment_index + 1]
            p3 = self.points[min(segment_index + 2, len(self.points) - 1)]
        t2 = local_t * local_t
        t3 = t2 * local_t
        return tuple(
            0.5
            * (
                2 * p1[axis]
                + (-p0[axis] + p2[axis]) * local_t
                + (2 * p0[axis] - 5 * p1[axis] + 4 * p2[axis] - p3[axis]) * t2
                + (-p0[axis] + 3 * p1[axis] - 3 * p2[axis] + p3[axis]) * t3
            )
            for axis in (0, 1)
        )

    def _curve_point(self, t: float) -> tuple[float, float]:
        if self.curve_type == "catmull-rom":
            return self._catmull_rom(t, closed=self.traversal == "loop")
        return self._bezier(t)

    def _ease(self, progress: float) -> float:
        if self.easing == "ease-in":
            return progress * progress
        if self.easing == "ease-out":
            return 1.0 - (1.0 - progress) ** 2
        if self.easing == "ease-in-out":
            return 0.5 - 0.5 * cos(pi * progress)
        return progress

    def _position_at_distance(self, distance: float) -> Vector:
        distance = min(max(distance, 0.0), self.length)
        for index in range(1, len(self._lengths)):
            if self._lengths[index] >= distance:
                start_distance = self._lengths[index - 1]
                segment_length = self._lengths[index] - start_distance
                fraction = 0.0 if segment_length == 0 else (distance - start_distance) / segment_length
                start = self._samples[index - 1]
                end = self._samples[index]
                return Vector(
                    start[0] + (end[0] - start[0]) * fraction,
                    start[1] + (end[1] - start[1]) * fraction,
                )
        return Vector(*self._samples[-1])

    def current_position(self) -> Vector:
        return self._position_at_distance(self.distance)

    def copy(self) -> MovingPegPath:
        copied_path = MovingPegPath(
            self.points,
            self.speed,
            self.curve_type,
            self.easing,
            self.traversal,
        )
        copied_path.distance = self.distance
        copied_path.direction = self.direction
        copied_path._phase = self._phase
        return copied_path

    def sample_curve(self, segments: int = 32) -> list[tuple[float, float]]:
        if segments < 1:
            raise ValueError("segments must be at least one")
        if self.curve_type == "catmull-rom":
            segment_count = (
                len(self.points)
                if self.traversal == "loop"
                else len(self.points) - 1
            )
            return [
                self._catmull_rom(
                    index / (segments * segment_count),
                    closed=self.traversal == "loop",
                )
                for index in range(segments * segment_count + 1)
            ]
        curve = [
            self._curve_point(index / segments)
            for index in range(segments + 1)
        ]
        if self.traversal == "loop":
            curve.extend(
                (
                    curve[-1][0] + (curve[0][0] - curve[-1][0]) * index / segments,
                    curve[-1][1] + (curve[0][1] - curve[-1][1]) * index / segments,
                )
                for index in range(1, segments + 1)
            )
        return curve

    def advance(self, delta_seconds: float) -> Vector:
        if delta_seconds < 0:
            raise ValueError("delta_seconds cannot be negative")

        period = self.length if self.traversal == "loop" else 2.0 * self.length
        self._phase = (self._phase + self.speed * delta_seconds) % period
        if self.traversal == "loop":
            progress = self._phase / self.length
            self.distance = self._ease(progress) * self.length
            self.direction = 1.0
        elif self._phase <= self.length:
            progress = self._phase / self.length
            self.distance = self._ease(progress) * self.length
            self.direction = 1.0
        else:
            progress = (self._phase - self.length) / self.length
            self.distance = (1.0 - self._ease(progress)) * self.length
            self.direction = -1.0

        return self.current_position()

    def translate(self, dx: float, dy: float) -> None:
        self.points = tuple((x + dx, y + dy) for x, y in self.points)
        self._rebuild_samples()

    def set_points(self, points: list[tuple[float, float]]) -> None:
        if self.curve_type == "cubic-bezier" and len(points) != 4:
            raise ValueError("A cubic-bezier path requires exactly four control points")
        if self.curve_type == "catmull-rom" and len(points) < 2:
            raise ValueError("A catmull-rom path requires at least two route points")
        if any(not isfinite(x) or not isfinite(y) for x, y in points):
            raise ValueError("Moving peg control points must be finite")
        previous_points = self.points
        self.points = tuple((float(x), float(y)) for x, y in points)
        self._rebuild_samples()
        if self.length == 0:
            self.points = previous_points
            self._rebuild_samples()
            raise ValueError("A moving peg path must have nonzero length")
        self.distance = 0.0
        self.direction = 1.0
        self._phase = 0.0

    def reset(self) -> None:
        self._phase = 0.0
        self.distance = 0.0
        self.direction = 1.0

    def set_motion_options(self, easing: str, traversal: str) -> None:
        if easing not in self.EASING_TYPES:
            raise ValueError(f"Unsupported moving peg easing: {easing}")
        if traversal not in self.TRAVERSAL_TYPES:
            raise ValueError(f"Unsupported moving peg traversal: {traversal}")
        self.easing = easing
        self.traversal = traversal
        self._rebuild_samples()
        self.reset()

    def _rebuild_samples(self) -> None:
        segment_count = 1
        if self.curve_type == "catmull-rom":
            segment_count = (
                len(self.points)
                if self.traversal == "loop"
                else len(self.points) - 1
            )
        samples_per_segment = max(8, self.SAMPLE_COUNT // segment_count)
        sample_count = samples_per_segment * segment_count
        self._samples = tuple(
            self._curve_point(index / sample_count)
            for index in range(sample_count + 1)
        )
        if self.traversal == "loop" and self.curve_type == "cubic-bezier":
            start = self._samples[-1]
            end = self._samples[0]
            closing = tuple(
                (
                    start[0] + (end[0] - start[0]) * index / samples_per_segment,
                    start[1] + (end[1] - start[1]) * index / samples_per_segment,
                )
                for index in range(1, samples_per_segment + 1)
            )
            self._samples += closing
        self._lengths = [0.0]
        for previous, current in zip(self._samples, self._samples[1:]):
            self._lengths.append(
                self._lengths[-1] + hypot(current[0] - previous[0], current[1] - previous[1])
            )
        self.length = self._lengths[-1]
