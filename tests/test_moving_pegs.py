from __future__ import annotations

import json
from math import hypot
import os
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame

pygame.init()

import editor as editor_module
from editor import levelEditor
from local.config import configs
from local.editor_tools import generate_shape_points, resample_polyline
from local.misc import createStaticImage, drawMovingPegs
from convert_legacy_levels import convert_file
from local.level_format import (
    FORMAT_NAME,
    FORMAT_VERSION,
    LEGACY_DEFAULT_MOVING_PEG_SPEED,
    LEGACY_FORMAT_VERSION,
    read_level_records,
)
from local.loadLevel import loadData, saveData
from local.moving_peg import DEFAULT_MOVING_PEG_SPEED, MovingPegPath
from local.performance import PerformanceMetrics
from local.peg import Peg
from local.ball import Ball
from local.collision import resolveCollisionAndGetPeg
from local.quadtree import QuadtreePegs, Rectangle
from local.rendering import GameRenderer
from local.game import Game
from local.trajectory import TrajectoryCalculation
from local.vectors import Vector


class MovingPegPathTests(unittest.TestCase):
    def test_easing_changes_progression_and_ping_pong_returns_to_start(self):
        points = [(0, 0), (0, 10), (10, 10), (10, 0)]
        linear = MovingPegPath(points, speed=10)
        ease_in = MovingPegPath(points, speed=10, easing="ease-in")
        linear_position = linear.advance(linear.length / linear.speed / 4)
        ease_position = ease_in.advance(ease_in.length / ease_in.speed / 4)

        self.assertNotAlmostEqual(linear_position.x, ease_position.x)
        self.assertNotAlmostEqual(linear_position.y, ease_position.y)
        self.assertEqual(ease_in.easing, "ease-in")
        ease_in.advance(ease_in.length / ease_in.speed * 1.75)
        self.assertAlmostEqual(ease_in.distance, 0, places=5)
        self.assertEqual(ease_in.direction, 1.0)

    def test_loop_traversal_wraps_and_catmull_curve_is_closed(self):
        route = [(0, 0), (20, 30), (50, 0), (80, 30)]
        path = MovingPegPath(
            route,
            speed=10,
            curve_type="catmull-rom",
            traversal="loop",
        )
        start = path.current_position()
        end = path.advance(path.length / path.speed)

        self.assertAlmostEqual(end.x, start.x, places=5)
        self.assertAlmostEqual(end.y, start.y, places=5)
        curve = path.sample_curve()
        self.assertEqual(curve[0], curve[-1])
        self.assertEqual(path.direction, 1.0)

    def test_invalid_movement_options_are_rejected(self):
        points = [(0, 0), (0, 10), (10, 10), (10, 0)]
        with self.assertRaises(ValueError):
            MovingPegPath(points, easing="bounce")
        with self.assertRaises(ValueError):
            MovingPegPath(points, traversal="teleport")

    def test_variable_route_points_define_smooth_catmull_rom_paths(self):
        route = [(0, 0), (20, 30), (50, 0), (80, 30), (100, 0)]
        path = MovingPegPath(route, curve_type="catmull-rom")

        self.assertEqual(path.curve_type, "catmull-rom")
        self.assertEqual(path.points, tuple(route))
        curve = path.sample_curve(segments=8)
        self.assertEqual(curve[8], route[1])
        self.assertEqual(curve[16], route[2])
        self.assertEqual(path.copy().curve_type, "catmull-rom")

        path.set_points([(0, 0), (30, 20), (100, 0)])
        self.assertEqual(len(path.points), 3)

    def test_moving_peg_is_not_baked_into_the_static_level_image(self):
        peg = Peg(100, 100)
        peg.set_movement(
            MovingPegPath([(100, 100), (110, 120), (130, 120), (140, 100)])
        )

        empty_image = createStaticImage([])
        moving_image = createStaticImage([peg])
        self.assertEqual(
            pygame.image.tobytes(empty_image, "RGBA"),
            pygame.image.tobytes(moving_image, "RGBA"),
        )
        drawMovingPegs(empty_image, [peg])
        self.assertNotEqual(
            pygame.image.tobytes(empty_image, "RGBA"),
            pygame.image.tobytes(moving_image, "RGBA"),
        )

    def test_cubic_bezier_starts_ends_and_moves_at_authored_speed(self):
        path = MovingPegPath(
            [(0, 0), (0, 10), (10, 10), (10, 0)],
            speed=10,
        )
        self.assertEqual(path.current_position().x, 0)
        self.assertEqual(path.current_position().y, 0)

        position = path.advance(0.5)
        self.assertAlmostEqual(hypot(position.x, position.y), 5, delta=0.1)
        end_position = path.advance((path.length - path.distance) / path.speed)
        self.assertAlmostEqual(end_position.x, 10, delta=0.1)
        self.assertAlmostEqual(end_position.y, 0, delta=0.1)
        start_position = path.advance(path.length / path.speed)
        self.assertAlmostEqual(start_position.x, 0, delta=0.1)

    def test_default_speed_is_in_bucket_speed_range(self):
        path = MovingPegPath([(0, 0), (30, 0), (70, 0), (100, 0)])
        self.assertEqual(path.speed, DEFAULT_MOVING_PEG_SPEED)
        self.assertLessEqual(path.speed, 2.5)

    def test_path_rejects_invalid_control_points_and_speed(self):
        with self.assertRaises(ValueError):
            MovingPegPath([(0, 0), (1, 1), (2, 2)])
        with self.assertRaises(ValueError):
            MovingPegPath([(0, 0), (1, 1), (2, 2), (3, 3)], speed=0)

    def test_peg_reset_restores_path_start_and_tracks_previous_position(self):
        peg = Peg(0, 0)
        peg.set_movement(MovingPegPath([(0, 0), (0, 10), (10, 10), (10, 0)], 30))
        peg.update_movement(0.1)
        self.assertNotEqual(peg.pos.x, peg.previousPos.x)
        peg.reset()
        self.assertEqual((peg.pos.x, peg.pos.y), (0, 0))
        self.assertEqual((peg.previousPos.x, peg.previousPos.y), (0, 0))

    def test_quadtree_queries_swept_bounds_for_moving_pegs(self):
        peg = Peg(0, 50)
        peg.set_movement(
            MovingPegPath([(0, 50), (30, 50), (70, 50), (100, 50)], 50)
        )
        tree = QuadtreePegs(Rectangle(100, 100, 100, 100), 1)
        self.assertEqual(tree.insert_many([peg]), 1)
        peg.update_movement(0.5)

        candidates = []
        tree.queryInto(Rectangle(25, 50, 5, 5), candidates)
        self.assertIn(peg, candidates)
        self.assertTrue(tree.remove(peg))
        candidates.clear()
        tree.queryInto(Rectangle(25, 50, 5, 5), candidates)
        self.assertNotIn(peg, candidates)

    def test_moving_peg_swept_collision_uses_relative_motion(self):
        peg = Peg(0, 50)
        peg.set_movement(
            MovingPegPath([(0, 50), (30, 50), (70, 50), (100, 50)], 100)
        )
        peg.update_movement(0.5)
        ball = Ball(50, 50)
        ball.prevPos = ball.pos.copy()

        self.assertIs(resolveCollisionAndGetPeg(ball, [peg]), peg)
        self.assertGreater(ball.vel.x, 0)

    def test_trajectory_advances_a_snapshot_without_moving_live_pegs(self):
        peg = Peg(10, 50)
        peg.set_movement(
            MovingPegPath([(10, 50), (30, 50), (70, 50), (90, 50)], 20)
        )
        tree = QuadtreePegs(Rectangle(100, 100, 100, 100), 1)
        tree.insert_many([peg])
        calculation = TrajectoryCalculation(
            Vector(1, 0),
            Vector(50, 10),
            [peg],
            [],
            tree,
            0.1,
            depth=1,
            zeroGravity=True,
        )
        live_position = peg.pos.copy()

        calculation.advance(time_budget=1)

        self.assertEqual((peg.pos.x, peg.pos.y), (live_position.x, live_position.y))
        self.assertNotEqual(
            (
                calculation._movingPegSnapshots[0].pos.x,
                calculation._movingPegSnapshots[0].pos.y,
            ),
            (live_position.x, live_position.y),
        )


class EditorShapeToolTests(unittest.TestCase):
    def test_preset_shapes_generate_evenly_spaced_peg_positions(self):
        line = generate_shape_points("Line", (0, 0, 100, 0), 25)
        rectangle = generate_shape_points("Rectangle", (0, 0, 100, 50), 25)
        circle = generate_shape_points("Circle", (0, 0, 100, 100), 25)
        triangle = generate_shape_points("Triangle", (0, 0, 100, 100), 25)

        self.assertEqual(len(line), 5)
        self.assertGreaterEqual(len(rectangle), 10)
        self.assertGreaterEqual(len(circle), 12)
        self.assertGreaterEqual(len(triangle), 10)
        self.assertAlmostEqual(line[0][0], 0)
        self.assertAlmostEqual(line[-1][0], 100)

    def test_freehand_path_is_resampled_by_distance(self):
        points = resample_polyline([(0, 0), (10, 0), (10, 10)], 5)
        self.assertEqual(points, [(0, 0), (5.0, 0.0), (10.0, 0.0), (10.0, 5.0), (10, 10)])

    def test_invalid_shape_and_spacing_are_rejected(self):
        with self.assertRaises(ValueError):
            generate_shape_points("Star", (0, 0, 100, 100), 20)
        with self.assertRaises(ValueError):
            generate_shape_points("Line", (0, 0, 100, 100), 0)


class LevelFormatTests(unittest.TestCase):
    def test_variable_route_path_is_saved_and_loaded(self):
        route = [(100, 120), (120, 150), (150, 130), (180, 160), (200, 120)]
        peg = Peg(*route[0])
        peg.set_movement(MovingPegPath(route, speed=3, curve_type="catmull-rom"))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.lvl"
            saveData([peg], str(path))
            records, _ = read_level_records(path)
            loaded, _ = loadData(str(path), centerPegs=False)

        self.assertEqual(records[0]["motion"]["type"], "catmull-rom")
        self.assertEqual(len(loaded[0].movement.points), 5)
        self.assertEqual(loaded[0].movement.curve_type, "catmull-rom")

    def test_easing_and_loop_options_are_saved_and_loaded(self):
        peg = Peg(100, 120)
        peg.set_movement(
            MovingPegPath(
                [(100, 120), (120, 150), (150, 130), (180, 160), (200, 120)],
                speed=3,
                curve_type="catmull-rom",
                easing="ease-in-out",
                traversal="loop",
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "loop.lvl"
            saveData([peg], str(path))
            records, _ = read_level_records(path)
            loaded, _ = loadData(str(path), centerPegs=False)

        self.assertEqual(records[0]["motion"]["easing"], "ease-in-out")
        self.assertEqual(records[0]["motion"]["traversal"], "loop")
        self.assertEqual(loaded[0].movement.easing, "ease-in-out")
        self.assertEqual(loaded[0].movement.traversal, "loop")

    def test_save_and_load_versioned_level_with_moving_path(self):
        peg = Peg(100, 120)
        peg.set_movement(
            MovingPegPath(
                [(100, 120), (110, 130), (130, 130), (140, 120)],
                speed=55,
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "moving.lvl"
            self.assertIsNone(saveData([peg], str(path)))
            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual((document["format"], document["version"]), (FORMAT_NAME, FORMAT_VERSION))

            loaded, _ = loadData(str(path), centerPegs=False)

        self.assertEqual(len(loaded), 1)
        self.assertIsNotNone(loaded[0].movement)
        self.assertEqual(loaded[0].movement.speed, 55)
        self.assertEqual(loaded[0].movement.points, tuple(peg.movement.points))

    def test_legacy_pickle_loads_and_converts_without_overwriting_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.lvl"
            destination = Path(directory) / "converted" / source.name
            source.write_bytes(pickle.dumps([(10, 20), (30, 40)]))
            legacy_bytes = source.read_bytes()

            self.assertTrue(convert_file(source, destination))
            records, is_legacy = read_level_records(destination)
            self.assertEqual(source.read_bytes(), legacy_bytes)

        self.assertFalse(is_legacy)
        self.assertEqual(records, [{"x": 10.0, "y": 20.0}, {"x": 30.0, "y": 40.0}])

    def test_invalid_legacy_file_uses_default_level_with_warning(self):
        with tempfile.NamedTemporaryFile() as level_file:
            level_file.write(b"")
            level_file.flush()
            with patch("builtins.print") as print_warning:
                pegs, _ = loadData(level_file.name, centerPegs=False)

        self.assertTrue(pegs)
        print_warning.assert_called_once()

    def test_converter_refuses_to_overwrite_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.lvl"
            destination = Path(directory) / "converted.lvl"
            source.write_bytes(pickle.dumps([(10, 20)]))
            destination.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                convert_file(source, destination)
            self.assertEqual(destination.read_text(encoding="utf-8"), "keep")

    def test_converter_refuses_to_replace_legacy_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.lvl"
            source.write_bytes(pickle.dumps([(10, 20)]))
            with self.assertRaises(ValueError):
                convert_file(source, source, overwrite=True)

    def test_new_format_rejects_invalid_path_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.lvl"
            path.write_text(
                json.dumps(
                    {
                        "format": FORMAT_NAME,
                        "version": FORMAT_VERSION,
                        "pegs": [
                            {
                                "x": 10,
                                "y": 20,
                                "motion": {
                                    "type": "cubic-bezier",
                                    "points": [[0, 0]],
                                    "speed": 20,
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                read_level_records(path)

    def test_previous_default_moving_speed_is_migrated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "previous-format.lvl"
            path.write_text(
                json.dumps(
                    {
                        "format": FORMAT_NAME,
                        "version": LEGACY_FORMAT_VERSION,
                        "pegs": [
                            {
                                "x": 10,
                                "y": 20,
                                "motion": {
                                    "type": "cubic-bezier",
                                    "points": [[10, 20], [20, 30], [30, 30], [40, 20]],
                                    "speed": LEGACY_DEFAULT_MOVING_PEG_SPEED,
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            records, is_legacy = read_level_records(path)

        self.assertFalse(is_legacy)
        self.assertEqual(records[0]["motion"]["speed"], DEFAULT_MOVING_PEG_SPEED)


class MovingPegEditorTests(unittest.TestCase):
    def setUp(self):
        configs["WIDTH"] = 960
        configs["HEIGHT"] = 720
        configs["REFRESH_RATE"] = 60
        self.surface = pygame.display.set_mode((configs["WIDTH"], configs["HEIGHT"]))

    def _run_editor(self, pegs, events, mouse_buttons=(False, False, False)):
        with (
            patch.object(pygame.event, "get", side_effect=events),
            patch.object(pygame.mouse, "get_pressed", return_value=mouse_buttons),
            patch.object(pygame.mouse, "get_pos", return_value=(500, 400)),
            patch.object(pygame.mouse, "set_visible"),
            patch.object(pygame.display, "set_caption"),
            patch.object(pygame, "quit"),
            patch.object(editor_module.sys, "exit", side_effect=SystemExit),
        ):
            with self.assertRaises(SystemExit):
                levelEditor(self.surface, pygame.time.Clock(), pegs=pegs)

    def test_toolbar_shape_dropdown_generates_circle_pegs_from_drag(self):
        pegs = []
        events = [
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(360, 80))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(360, 127))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 220))],
            [pygame.event.Event(pygame.MOUSEMOTION, pos=(300, 320), rel=(100, 100), buttons=(1, 0, 0))],
            [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(300, 320))],
            [pygame.event.Event(pygame.QUIT)],
        ]

        self._run_editor(pegs, events)

        self.assertGreaterEqual(len(pegs), 5)
        for peg in pegs:
            radius = ((peg.pos.x - 250) ** 2 + (peg.pos.y - 270) ** 2) ** 0.5
            self.assertAlmostEqual(radius, 50, delta=2)

    def test_select_tool_drag_moves_a_peg(self):
        peg = Peg(200, 220)
        pegs = [peg]
        events = [
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(40, 80))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 220))],
            [pygame.event.Event(pygame.MOUSEMOTION, pos=(250, 260), rel=(50, 40), buttons=(1, 0, 0))],
            [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(250, 260))],
            [pygame.event.Event(pygame.QUIT)],
        ]

        self._run_editor(pegs, events, mouse_buttons=(True, False, False))

        self.assertEqual((peg.pos.x, peg.pos.y), (250, 260))

    def test_freehand_shape_tool_generates_pegs_along_dragged_stroke(self):
        pegs = []
        events = [
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(360, 80))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(360, 202))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 220))],
            [pygame.event.Event(pygame.MOUSEMOTION, pos=(200, 220), rel=(100, 0), buttons=(1, 0, 0))],
            [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(200, 220))],
            [pygame.event.Event(pygame.QUIT)],
        ]

        self._run_editor(pegs, events)

        self.assertEqual(len(pegs), 2)
        self.assertTrue(all(peg.pos.y == 220 for peg in pegs))
        self.assertAlmostEqual(pegs[0].pos.x, 100)
        self.assertGreater(pegs[-1].pos.x, pegs[0].pos.x)

    def test_editor_builds_moving_peg_from_four_control_point_clicks(self):
        created_pegs = []

        def create_peg(x, y):
            peg = Peg(x, y)
            if x != 0 or y != 0:
                created_pegs.append(peg)
            return peg

        events = [
            [pygame.event.Event(pygame.KEYUP, key=pygame.K_m)],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 200))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(230, 240))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(270, 240))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(300, 200))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(600, 80))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(230, 240))],
            [pygame.event.Event(pygame.MOUSEMOTION, pos=(240, 260), rel=(10, 20), buttons=(1, 0, 0))],
            [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(240, 260))],
            [pygame.event.Event(pygame.KEYUP, key=pygame.K_PLUS)],
            [pygame.event.Event(pygame.QUIT)],
        ]

        with (
            patch.object(pygame.event, "get", side_effect=events),
            patch.object(pygame.mouse, "get_pressed", return_value=(True, False, False)),
            patch.object(pygame.mouse, "get_pos", return_value=(500, 400)),
            patch.object(pygame.mouse, "set_visible"),
            patch.object(pygame.display, "set_caption"),
            patch.object(pygame, "quit"),
            patch.object(editor_module.sys, "exit", side_effect=SystemExit),
            patch.object(editor_module, "Peg", side_effect=create_peg),
        ):
            with self.assertRaises(SystemExit):
                levelEditor(self.surface, pygame.time.Clock(), pegs=[])

        self.assertEqual(len(created_pegs), 1)
        self.assertIsNotNone(created_pegs[0].movement)
        self.assertEqual(
            created_pegs[0].movement.points,
            ((200.0, 200.0), (240.0, 260.0), (270.0, 240.0), (300.0, 200.0)),
        )
        self.assertEqual(created_pegs[0].movement.speed, DEFAULT_MOVING_PEG_SPEED + 0.5)

    def test_moving_menu_increases_route_point_count_for_created_peg(self):
        pegs = []
        events = [
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 80))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(300, 116))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 200))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(450, 240))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 260))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(550, 240))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(600, 200))],
            [pygame.event.Event(pygame.QUIT)],
        ]

        self._run_editor(pegs, events)

        self.assertEqual(len(pegs), 1)
        self.assertEqual(len(pegs[0].movement.points), 5)
        self.assertEqual(pegs[0].movement.curve_type, "catmull-rom")

    def test_moving_menu_applies_easing_and_loop_to_new_paths(self):
        pegs = []
        events = [
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 80))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(220, 206))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(220, 236))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(220, 236))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(220, 236))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 200))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(450, 220))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 200))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(550, 220))],
            [pygame.event.Event(pygame.QUIT)],
        ]

        self._run_editor(pegs, events)

        self.assertEqual(len(pegs), 1)
        self.assertEqual(pegs[0].movement.traversal, "loop")
        self.assertEqual(pegs[0].movement.easing, "ease-in-out")

    def test_live_preview_can_target_selected_peg_or_all_moving_pegs(self):
        selected = Peg(200, 220)
        selected.set_movement(
            MovingPegPath(
                [(200, 220), (220, 240), (260, 240), (280, 220)]
            )
        )
        other = Peg(500, 220)
        other.set_movement(
            MovingPegPath(
                [(500, 220), (520, 240), (560, 240), (580, 220)]
            )
        )
        updated_pegs = []
        update_movement = Peg.update_movement

        def track_update(peg, delta_seconds):
            updated_pegs.append(peg)
            return update_movement(peg, delta_seconds)

        events = [
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(40, 80))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 220))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 80))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 146))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 176))],
            [pygame.event.Event(pygame.QUIT)],
        ]
        clock = Mock()
        clock.get_time.return_value = 16
        clock.get_rawtime.return_value = 0
        clock.get_fps.return_value = 60

        with (
            patch.object(pygame.event, "get", side_effect=events),
            patch.object(pygame.mouse, "get_pressed", return_value=(False, False, False)),
            patch.object(pygame.mouse, "get_pos", return_value=(700, 400)),
            patch.object(pygame.mouse, "set_visible"),
            patch.object(pygame.display, "set_caption"),
            patch.object(pygame, "quit"),
            patch.object(editor_module.sys, "exit", side_effect=SystemExit),
            patch.object(Peg, "update_movement", autospec=True, side_effect=track_update),
        ):
            with self.assertRaises(SystemExit):
                levelEditor(self.surface, clock, pegs=[selected, other])

        self.assertIn(selected, updated_pegs)
        self.assertEqual(updated_pegs.count(other), 1)

    def test_moving_pegs_render_with_a_distinct_tint(self):
        static_peg = Peg(100, 100)
        moving_peg = Peg(100, 100)
        moving_peg.set_movement(
            MovingPegPath([(100, 100), (110, 120), (130, 120), (140, 100)])
        )
        background = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]))
        background.fill((0, 0, 0))
        static_image = createStaticImage(
            [static_peg],
            bgImg=background,
            track_changes=False,
        )
        moving_image = background.copy()
        drawMovingPegs(moving_image, [moving_peg])

        self.assertNotEqual(
            static_image.get_at((100, 100)),
            moving_image.get_at((100, 100)),
        )

    def test_performance_panel_can_be_dragged_and_released(self):
        renderer = GameRenderer(self.surface)
        metrics = PerformanceMetrics()
        renderer.draw_performance_metrics(metrics)
        original_position = renderer._performance_panel_position
        original_rect = renderer._performance_panel.get_rect(
            topleft=original_position
        )
        grab_position = (original_rect.x + 20, original_rect.y + 20)

        self.assertTrue(
            renderer.handle_performance_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    button=1,
                    pos=grab_position,
                )
            )
        )
        self.assertTrue(
            renderer.handle_performance_event(
                pygame.event.Event(
                    pygame.MOUSEMOTION,
                    pos=(grab_position[0] + 80, grab_position[1] - 60),
                    rel=(80, -60),
                    buttons=(1, 0, 0),
                )
            )
        )
        self.assertTrue(
            renderer.handle_performance_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONUP,
                    button=1,
                    pos=(grab_position[0] + 80, grab_position[1] - 60),
                )
            )
        )

        self.assertEqual(
            renderer._performance_panel_position,
            (original_position[0] + 80, original_position[1] - 60),
        )
        self.assertFalse(
            renderer.handle_performance_event(
                pygame.event.Event(
                    pygame.MOUSEMOTION,
                    pos=(grab_position[0] + 100, grab_position[1] + 80),
                    rel=(20, 20),
                    buttons=(0, 0, 0),
                )
            )
        )

    def test_developer_debug_panel_can_be_dragged_and_released(self):
        renderer = GameRenderer(self.surface)
        game = Game()
        renderer._draw_developer_panel(
            game,
            pygame.time.Clock(),
            total_time=0.016,
            draw_time=0.008,
            quadtree=Mock(capacity=8),
            joystick=None,
        )
        original_position = renderer._developer_panel_position
        original_rect = renderer._developer_panel_rect.copy()
        grab_position = (original_rect.x + 30, original_rect.y + 25)
        new_position = (grab_position[0] - 70, grab_position[1] + 40)

        self.assertTrue(
            renderer.handle_debug_panel_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    button=1,
                    pos=grab_position,
                ),
                developer_enabled=True,
            )
        )
        self.assertTrue(
            renderer.handle_debug_panel_event(
                pygame.event.Event(
                    pygame.MOUSEMOTION,
                    pos=new_position,
                    rel=(-70, 40),
                    buttons=(1, 0, 0),
                ),
                developer_enabled=True,
            )
        )
        self.assertTrue(
            renderer.handle_debug_panel_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONUP,
                    button=1,
                    pos=new_position,
                ),
                developer_enabled=True,
            )
        )
        self.assertEqual(
            renderer._developer_panel_position,
            (original_position[0] - 70, original_position[1] + 40),
        )


if __name__ == "__main__":
    unittest.main()
