from __future__ import annotations

import json
import pickle
from pathlib import Path
from math import isfinite
from typing import Any

from local.moving_peg import DEFAULT_MOVING_PEG_SPEED

FORMAT_NAME = "pegglepy-level"
FORMAT_VERSION = 3
LEGACY_FORMAT_VERSION = 2
LEGACY_DEFAULT_MOVING_PEG_SPEED = 80.0


def read_level_records(path: str | Path) -> tuple[list[dict[str, Any]], bool]:
    """Read either a versioned level file or a legacy pickled position list."""
    data = Path(path).read_bytes()
    if data.lstrip().startswith(b"{"):
        document = json.loads(data)
        if not isinstance(document, dict):
            raise ValueError("Level data must be a JSON object")
        if document.get("format") != FORMAT_NAME:
            raise ValueError("Unrecognized level file format")
        version = document.get("version")
        if version not in (LEGACY_FORMAT_VERSION, FORMAT_VERSION):
            raise ValueError(f"Unsupported level format version: {document.get('version')!r}")
        records = document.get("pegs")
        if not isinstance(records, list):
            raise ValueError("Level data must contain a peg list")
        validated_records = [_validate_record(record) for record in records]
        if version == LEGACY_FORMAT_VERSION:
            for record in validated_records:
                motion = record.get("motion")
                if motion is not None and motion["speed"] == LEGACY_DEFAULT_MOVING_PEG_SPEED:
                    motion["speed"] = DEFAULT_MOVING_PEG_SPEED
        return validated_records, False

    try:
        positions = pickle.loads(data)
    except (pickle.PickleError, EOFError, AttributeError, ImportError, IndexError) as error:
        raise ValueError("Unable to decode legacy pickle level data") from error
    if not isinstance(positions, (list, tuple)):
        raise ValueError("Legacy level data must be a list of peg positions")
    records = []
    for position in positions:
        if not isinstance(position, (list, tuple)) or len(position) != 2:
            raise ValueError("Each legacy peg position must contain x and y")
        try:
            records.append({"x": float(position[0]), "y": float(position[1])})
        except (TypeError, ValueError) as error:
            raise ValueError("Legacy peg coordinates must be numeric") from error
    return records, True


def _validate_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Each peg must be a JSON object")
    try:
        x = float(record["x"])
        y = float(record["y"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Each peg must have numeric x and y coordinates") from error
    if not isfinite(x) or not isfinite(y):
        raise ValueError("Peg coordinates must be finite")

    validated: dict[str, Any] = {"x": x, "y": y}
    motion = record.get("motion")
    if motion is not None:
        if not isinstance(motion, dict):
            raise ValueError("Peg motion must be a motion object")
        curve_type = motion.get("type")
        if curve_type not in ("cubic-bezier", "catmull-rom"):
            raise ValueError("Peg motion must use a supported curve type")
        points = motion.get("points")
        if not isinstance(points, list):
            raise ValueError("A moving peg path must have a list of points")
        if curve_type == "cubic-bezier" and len(points) != 4:
            raise ValueError("A cubic-bezier path must have four control points")
        if curve_type == "catmull-rom" and len(points) < 2:
            raise ValueError("A catmull-rom path must have at least two route points")
        if any(not isinstance(point, (list, tuple)) or len(point) != 2 for point in points):
            raise ValueError("Each motion control point must contain x and y")
        easing = motion.get("easing", "linear")
        traversal = motion.get("traversal", "ping-pong")
        if easing not in ("linear", "ease-in", "ease-out", "ease-in-out"):
            raise ValueError("Motion easing must be a supported easing type")
        if traversal not in ("ping-pong", "loop"):
            raise ValueError("Motion traversal must be ping-pong or loop")
        try:
            validated_points = [[float(point[0]), float(point[1])] for point in points]
            speed = float(motion["speed"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Motion points and speed must be numeric") from error
        if (
            any(not isfinite(value) for point in validated_points for value in point)
            or not isfinite(speed)
        ):
            raise ValueError("Motion points and speed must be finite")
        if speed <= 0:
            raise ValueError("Moving peg speed must be greater than zero")
        validated["motion"] = {
            "type": curve_type,
            "points": validated_points,
            "speed": speed,
            "easing": easing,
            "traversal": traversal,
        }
    return validated


def make_level_document(pegs: list[Any]) -> dict[str, Any]:
    records = []
    for peg in pegs:
        record: dict[str, Any] = {
            "x": float(peg.pos.x),
            "y": float(peg.pos.y),
        }
        movement = getattr(peg, "movement", None)
        if movement is not None:
            record["motion"] = {
                "type": movement.curve_type,
                "points": [[x, y] for x, y in movement.points],
                "speed": movement.speed,
                "easing": movement.easing,
                "traversal": movement.traversal,
            }
        records.append(record)
    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "pegs": records,
    }


def write_level_file(pegs: list[Any], path: str | Path) -> None:
    write_level_records(make_level_document(pegs)["pegs"], path)


def write_level_records(records: list[dict[str, Any]], path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(
            {
                "format": FORMAT_NAME,
                "version": FORMAT_VERSION,
                "pegs": [_validate_record(record) for record in records],
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
