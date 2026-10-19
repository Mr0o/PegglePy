from __future__ import annotations

from math import ceil, hypot, pi, cos, sin


SHAPE_TOOLS = ("Line", "Circle", "Rectangle", "Triangle", "Freehand")


def _sample_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    spacing: float,
    include_start: bool = True,
) -> list[tuple[float, float]]:
    distance = hypot(end[0] - start[0], end[1] - start[1])
    segments = max(1, ceil(distance / spacing))
    first_step = 0 if include_start else 1
    return [
        (
            start[0] + (end[0] - start[0]) * step / segments,
            start[1] + (end[1] - start[1]) * step / segments,
        )
        for step in range(first_step, segments + 1)
    ]


def generate_shape_points(
    shape: str,
    bounds: tuple[float, float, float, float],
    spacing: float,
) -> list[tuple[float, float]]:
    if spacing <= 0:
        raise ValueError("Peg spacing must be greater than zero")
    x1, y1, x2, y2 = bounds
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    width, height = right - left, bottom - top

    if shape == "Line":
        return _sample_segment((left, top), (right, bottom), spacing)

    if shape == "Circle":
        radius_x = radius_y = min(width, height) / 2
        circumference_estimate = pi * (
            3 * (radius_x + radius_y)
            - ((3 * radius_x + radius_y) * (radius_x + 3 * radius_y)) ** 0.5
        )
        count = max(3, ceil(circumference_estimate / (spacing * 1.1)))
        center_x, center_y = (left + right) / 2, (top + bottom) / 2
        return [
            (
                center_x + radius_x * cos(2 * pi * index / count),
                center_y + radius_y * sin(2 * pi * index / count),
            )
            for index in range(count)
        ]

    if shape == "Rectangle":
        corners = [
            (left, top),
            (right, top),
            (right, bottom),
            (left, bottom),
            (left, top),
        ]
    elif shape == "Triangle":
        corners = [
            ((left + right) / 2, top),
            (right, bottom),
            (left, bottom),
            ((left + right) / 2, top),
        ]
    else:
        raise ValueError(f"Unsupported peg shape: {shape}")

    points: list[tuple[float, float]] = []
    for start, end in zip(corners, corners[1:]):
        points.extend(_sample_segment(start, end, spacing, include_start=not points))
    if len(points) > 1 and points[-1] == points[0]:
        points.pop()
    return points


def resample_polyline(
    points: list[tuple[float, float]],
    spacing: float,
) -> list[tuple[float, float]]:
    if spacing <= 0:
        raise ValueError("Peg spacing must be greater than zero")
    if len(points) < 2:
        return points.copy()

    result = [points[0]]
    distance_to_next = spacing
    for start, end in zip(points, points[1:]):
        segment_length = hypot(end[0] - start[0], end[1] - start[1])
        if segment_length == 0:
            continue
        travelled = distance_to_next
        while travelled <= segment_length:
            fraction = travelled / segment_length
            result.append(
                (
                    start[0] + (end[0] - start[0]) * fraction,
                    start[1] + (end[1] - start[1]) * fraction,
                )
            )
            travelled += spacing
        distance_to_next = travelled - segment_length
    if hypot(points[-1][0] - result[-1][0], points[-1][1] - result[-1][1]) >= spacing * 0.5:
        result.append(points[-1])
    return result
