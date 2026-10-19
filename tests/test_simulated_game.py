import contextlib
import gc
import io
import os
import pickle
import runpy
import tempfile
import time
import unittest
import weakref
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()

import local.animate as animate_module
import editor as editor_module
import local.game as game_module
import local.menu_controller as menu_controller_module
import local.misc as misc_module
import local.rendering as renderer_module
from local.trajectory import BestTrajectorySearch, TrajectoryCalculation
import loadLevelMenu as level_menu_module
from editor import levelEditor
from loadLevelMenu import getLevelsList, loadLevelMenu
from local.menu_controller import MenuController
from local.bucket import Bucket
from local.config import bucketVelocity, configs
from local.ball import Ball
from local.misc import (
    createStaticCircles,
    createStaticImage,
    updateStaticImagePegs,
)
from local.performance import PerformanceMetrics
from local.collision import (
    getSweptCollisionBounds,
    isBallTouchingPeg,
    resolveCollision,
    resolveCollisionAndGetPeg,
    updateSweptCollisionBounds,
)
from local.events import Event, clearEventList, postEvent, subscribe
from local.peg import Peg
from local.loadLevel import loadData
from local.quadtree import QuadtreePegs, Rectangle
from local.rendering import GameRenderer
from local.vectors import Vector
from menu import getPauseScreen, mainMenu


_real_sleep = time.sleep


class FastClock:
    def tick(self, _rate=0):
        _real_sleep(0.006)

    def get_time(self):
        return 16

    def get_rawtime(self):
        return 16

    def get_fps(self):
        return 60


class SimulatedGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_configs = configs.copy()
        configs["WIDTH"] = 960
        configs["HEIGHT"] = 720
        configs["FULLSCREEN"] = False
        configs["VSYNC"] = False
        configs["REFRESH_RATE"] = 0
        configs["SOUND_ENABLED"] = False
        configs["MUSIC_ENABLED"] = False
        cls.screen = pygame.display.set_mode((configs["WIDTH"], configs["HEIGHT"]))

    @classmethod
    def tearDownClass(cls):
        configs.clear()
        configs.update(cls.original_configs)
        pygame.quit()

    def setUp(self):
        configs["WIDTH"] = 960
        configs["HEIGHT"] = 720
        configs["FULLSCREEN"] = False
        configs["VSYNC"] = False
        configs["REFRESH_RATE"] = 0
        configs["SOUND_ENABLED"] = False
        configs["MUSIC_ENABLED"] = False
        configs["DEBUG_MODE"] = False
        configs["ANIMATIONS_ENABLED"] = False

    def test_peg_stuck_timer_resets_after_ball_leaves_and_retouches(self):
        ball = Ball(137, 100)
        ball.isAlive = True
        peg = Peg(100, 100)

        with patch("local.triggerEvents.time.time", return_value=10.0):
            self.assertFalse(peg.update_ball_stuck_timer(ball, 0.4))
        self.assertTrue(peg.ballStuckTimer.isActive)
        self.assertAlmostEqual(peg.ballStuckTimer.timeRemaining, 0.4)

        ball.pos.x = 200
        peg.validate_ball_stuck_timer()
        self.assertFalse(peg.ballStuckTimer.isActive)
        self.assertEqual(peg.ballStuckTimer.timeRemaining, 0.0)

        ball.pos.x = 137
        with patch("local.triggerEvents.time.time", return_value=11.0):
            self.assertFalse(peg.update_ball_stuck_timer(ball, 0.4))
        self.assertTrue(peg.ballStuckTimer.isActive)
        self.assertAlmostEqual(peg.ballStuckTimer.timeRemaining, 0.4)

        with patch("local.triggerEvents.time.time", return_value=11.5):
            self.assertTrue(peg.update_ball_stuck_timer(ball, 0.4))

    def test_peg_stuck_timer_tracks_multiple_balls_without_restarting(self):
        first_ball = Ball(137, 100)
        second_ball = Ball(137, 100)
        third_ball = Ball(137, 100)
        for ball in (first_ball, second_ball, third_ball):
            ball.isAlive = True
        peg = Peg(100, 100)

        with patch("local.triggerEvents.time.time", return_value=10.0):
            self.assertFalse(peg.update_ball_stuck_timer(first_ball, 0.4))
        initial_trigger_time = peg.ballStuckTimer.triggerTime

        with patch("local.triggerEvents.time.time", return_value=10.2):
            self.assertFalse(peg.update_ball_stuck_timer(second_ball, 0.4))
        self.assertEqual(peg.ballStuckTimer.triggerTime, initial_trigger_time)
        self.assertEqual(peg.ballStuckBalls, {first_ball, second_ball})

        first_ball.vel = Vector(2, 0)
        with patch("local.triggerEvents.time.time", return_value=10.3):
            self.assertFalse(peg.update_ball_stuck_timer(first_ball, 0.4))
        self.assertTrue(peg.ballStuckTimer.isActive)
        self.assertEqual(peg.ballStuckBalls, {second_ball})

        with patch("local.triggerEvents.time.time", return_value=10.5):
            self.assertTrue(peg.update_ball_stuck_timer(second_ball, 0.4))
            self.assertTrue(peg.update_ball_stuck_timer(third_ball, 0.4))
        self.assertEqual(peg.ballStuckTimer.triggerTime, initial_trigger_time)

    def click_main_menu(self, selection):
        centers = {
            "start": (480, 347),
            "editor": (480, 497),
            "quit": (480, 647),
            "settings": (825, 645),
        }
        with (
            patch.object(
                pygame.event,
                "get",
                return_value=[pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)],
            ),
            patch.object(pygame.mouse, "get_pos", return_value=centers[selection]),
            patch.object(pygame.mouse, "get_rel", return_value=(0, 0)),
            patch.object(pygame.joystick, "get_count", return_value=0),
        ):
            self.assertEqual(mainMenu(self.screen), selection)

    def test_main_menu_buttons_are_clickable(self):
        for selection in ("start", "editor", "quit", "settings"):
            with self.subTest(selection=selection):
                self.click_main_menu(selection)

    def test_menu_controller_routes_startup_through_settings_and_editor(self):
        game = game_module.Game()
        editor_peg = Peg(200, 200)
        editor_peg.set_color("orange")

        with (
            patch.object(
                menu_controller_module,
                "mainMenu",
                side_effect=("settings", "editor"),
            ),
            patch.object(
                menu_controller_module, "settingsMenu", return_value="mainMenu"
            ),
            patch.object(
                menu_controller_module,
                "levelEditor",
                return_value=("play", [editor_peg]),
            ),
            patch.object(
                menu_controller_module,
                "createPegColors",
                side_effect=lambda pegs: pegs,
            ),
            patch("local.menu_controller.time.sleep"),
        ):
            selection, editor_selection = MenuController().start(
                self.screen, FastClock(), game
            )

        self.assertEqual(selection, "start")
        self.assertEqual(editor_selection, "play")
        self.assertEqual(game.pegs, [editor_peg])
        self.assertEqual(game.originPegs, [editor_peg])
        self.assertEqual(game.orangeCount, 1)

    def test_menu_controller_draws_pause_menu_and_returns_selection(self):
        pause_surface = pygame.Surface(self.screen.get_size())
        menus = MenuController()

        with patch.object(
            menu_controller_module,
            "getPauseScreen",
            return_value=(pause_surface, "restart"),
        ):
            selection = menus.pause_selection(self.screen, 10, 20, True)

        self.assertEqual(selection, "restart")

    def test_menu_controller_loads_level_selected_after_returning_to_menu(self):
        game = game_module.Game()
        selected_pegs = [Peg(200, 200)]
        origin_pegs = selected_pegs.copy()

        with patch.object(
            menu_controller_module,
            "loadLevelMenu",
            return_value=(selected_pegs, origin_pegs, 1, "Selected Level"),
        ) as load_level:
            level_name = MenuController().load_selected_level(
                self.screen, game
            )

        load_level.assert_called_once_with(self.screen)
        self.assertEqual(level_name, "Selected Level")
        self.assertIs(game.pegs, selected_pegs)
        self.assertIs(game.originPegs, origin_pegs)
        self.assertEqual(game.orangeCount, 1)

    def test_event_subscriber_errors_are_not_silently_swallowed(self):
        def failing_subscriber():
            raise TypeError("subscriber failure")

        subscribe("TEST_SUBSCRIBER_FAILURE", failing_subscriber)
        try:
            with self.assertRaisesRegex(TypeError, "subscriber failure"):
                postEvent("TEST_SUBSCRIBER_FAILURE")
        finally:
            clearEventList()

    def test_event_subscriber_can_receive_the_event_object(self):
        received_events = []
        subscribe("TEST_EVENT_ARGUMENT", received_events.append)
        try:
            postEvent("TEST_EVENT_ARGUMENT")
            self.assertEqual(len(received_events), 1)
            self.assertIsInstance(received_events[0], Event)
            self.assertEqual(received_events[0].getEventType(), "TEST_EVENT_ARGUMENT")
        finally:
            clearEventList()

    def test_pause_menu_buttons_report_the_selected_action(self):
        points = {
            "resume": (370, 300),
            "restart": (500, 305),
            "load": (480, 520),
            "quit": (480, 640),
            "mainMenu": (40, 650),
            "editor": (40, 590),
            "settings": (825, 645),
        }
        for expected, (x, y) in points.items():
            with self.subTest(selection=expected):
                _, selection = getPauseScreen(x, y, True)
                self.assertEqual(selection, expected)

    def test_level_select_loads_the_first_level(self):
        levels = getLevelsList()
        self.assertTrue(levels, "the repository should include at least one level")
        self.assertEqual(os.path.basename(levels[0]), "Level 1.lvl")

        with (
            patch.object(
                pygame.event,
                "get",
                return_value=[pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)],
            ),
            patch.object(pygame.mouse, "get_pos", return_value=(480, 240)),
        ):
            pegs, origin_pegs, orange_count, level_name = loadLevelMenu(self.screen)

        self.assertEqual(level_name, "Level 1")
        self.assertTrue(pegs)
        self.assertTrue(origin_pegs)
        self.assertGreaterEqual(orange_count, 0)

    def test_level_loading_reports_incremental_progress(self):
        progress_updates = []
        with tempfile.NamedTemporaryFile() as level_file:
            pickle.dump([(100, 100), (200, 300)], level_file)
            level_file.flush()
            pegs, _ = loadData(
                level_file.name,
                progress_callback=lambda progress, status: progress_updates.append(
                    (progress, status)
                ),
            )

        progress_values = [progress for progress, _ in progress_updates]
        self.assertEqual(progress_values, sorted(progress_values))
        self.assertEqual(progress_values[-1], 1.0)
        self.assertIn("Creating pegs", [status for _, status in progress_updates])
        self.assertIn(
            "Centering level", [status for _, status in progress_updates]
        )
        self.assertAlmostEqual(
            (pegs[0].pos.x + pegs[1].pos.x) / 2,
            configs["WIDTH"] / 2,
        )
        self.assertAlmostEqual(
            (pegs[0].pos.y + pegs[1].pos.y) / 2,
            configs["HEIGHT"] / 2,
        )

    def test_level_select_renders_progress_updates_during_loading(self):
        level_path = getLevelsList()[0]
        peg = Peg(100, 100)

        def load_selected_level(_path, progress_callback=None):
            for progress, status in (
                (0.1, "Reading level data"),
                (0.45, "Creating pegs"),
                (0.9, "Centering level"),
                (1.0, "Level data ready"),
            ):
                progress_callback(progress, status)
            return [peg], [peg], 1, "Level 1"

        with (
            patch.object(
                level_menu_module,
                "loadData",
                return_value=([peg], level_path),
            ),
            patch.object(
                level_menu_module, "loadLevel", side_effect=load_selected_level
            ),
            patch.object(
                pygame.event,
                "get",
                return_value=[
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
                ],
            ),
            patch.object(pygame.mouse, "get_pos", return_value=(480, 240)),
            patch.object(pygame.mouse, "get_rel", return_value=(0, 0)),
            patch.object(
                level_menu_module,
                "drawLoadingScreen",
                wraps=level_menu_module.drawLoadingScreen,
            ) as draw_loading_screen,
            patch.object(
                level_menu_module.time,
                "perf_counter",
                side_effect=(0.0, 1.01, 1.02, 1.03, 1.04, 1.05),
            ),
        ):
            loadLevelMenu(self.screen)

        self.assertEqual(draw_loading_screen.call_count, 1)
        rendered_progress = [
            call.args[2] for call in draw_loading_screen.call_args_list
        ]
        self.assertEqual(
            rendered_progress,
            sorted(rendered_progress),
        )
        self.assertLessEqual(
            rendered_progress[-1],
            level_menu_module.LEVEL_DATA_PROGRESS_END,
        )
        self.assertGreater(rendered_progress[0], 0.0)

    def test_loading_screen_is_not_shown_for_a_fast_load(self):
        loading_progress = level_menu_module.LoadingScreenProgress(
            self.screen, "Level 1"
        )
        with (
            patch.object(level_menu_module, "drawLoadingScreen") as draw_loading_screen,
            patch.object(
                level_menu_module.time,
                "perf_counter",
                side_effect=(0.0, 0.5, 0.99),
            ),
        ):
            loading_progress.begin()
            loading_progress(0.2, "Loading")
            loading_progress(1.0, "Complete")

        draw_loading_screen.assert_not_called()

    def test_large_level_can_show_loading_screen_before_delay(self):
        loading_progress = level_menu_module.LoadingScreenProgress(
            self.screen, "750,000 pegs stress test"
        )
        with (
            patch.object(
                level_menu_module,
                "drawLoadingScreen",
            ) as draw_loading_screen,
            patch.object(
                level_menu_module.time,
                "perf_counter",
                return_value=0.01,
            ),
        ):
            loading_progress.begin()
            loading_progress.show_immediately(0.55, "Rendering level...")

        draw_loading_screen.assert_called_once_with(
            self.screen,
            "750,000 pegs stress test",
            0.55,
            "Rendering level...",
        )

    def test_loading_screen_quit_event_exits_during_delayed_loading(self):
        loading_progress = level_menu_module.LoadingScreenProgress(
            self.screen, "Large level"
        )
        with (
            patch.object(pygame.event, "peek", return_value=True) as has_quit,
            patch.object(pygame, "quit") as quit_pygame,
            patch.object(
                level_menu_module,
                "drawLoadingScreen",
            ) as draw_loading_screen,
            patch.object(
                level_menu_module.time,
                "perf_counter",
                return_value=0.1,
            ),
        ):
            loading_progress.begin()
            with self.assertRaises(SystemExit):
                loading_progress(0.5, "Rendering level...")

        has_quit.assert_called_once_with(pygame.QUIT)
        quit_pygame.assert_called_once_with()
        draw_loading_screen.assert_not_called()

    def test_loading_screen_progress_throttles_redraws_but_draws_completion(self):
        loading_progress = level_menu_module.LoadingScreenProgress(
            self.screen, "Level 1"
        )
        with (
            patch.object(
                level_menu_module,
                "drawLoadingScreen",
            ) as draw_loading_screen,
            patch.object(
                level_menu_module.time,
                "perf_counter",
                side_effect=(0.0, 0.2, 0.99, 1.01, 1.02, 1.03),
            ),
        ):
            loading_progress.begin()
            for progress in (0.0, 0.1, 0.2, 0.3, 1.0):
                loading_progress(progress, "Rendering level...")

        self.assertEqual(
            [call.args[2] for call in draw_loading_screen.call_args_list],
            [0.2, 1.0],
        )

    def test_loading_screen_stacks_text_and_progress_bar_without_overlap(self):
        class SolidFont:
            def render(self, text, _antialias, _color):
                if text.startswith("Loading"):
                    size, color = (220, 36), (255, 0, 0)
                elif text.endswith("%"):
                    size, color = (48, 18), (255, 255, 0)
                else:
                    size, color = (180, 20), (0, 255, 0)
                surface = pygame.Surface(size)
                surface.fill(color)
                return surface

        screen = pygame.Surface((960, 720))
        background = pygame.Surface(screen.get_size())
        background.fill((0, 0, 0))

        with (
            patch.object(level_menu_module, "altBackgroundImg", background),
            patch.object(level_menu_module, "menuButtonFont", SolidFont()),
            patch.object(level_menu_module, "infoFont", SolidFont()),
            patch.object(pygame.display, "flip"),
            patch.object(pygame.event, "pump"),
        ):
            level_menu_module.drawLoadingScreen(
                screen, "Level 1", 0.5, "Creating pegs"
            )

        def color_bounds(color):
            points = [
                (x, y)
                for y in range(screen.get_height())
                for x in range(screen.get_width())
                if screen.get_at((x, y))[:3] == color
            ]
            self.assertTrue(points, f"Expected rendered pixels for {color}")
            xs, ys = zip(*points)
            return pygame.Rect(
                min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            )

        title_rect = color_bounds((255, 0, 0))
        status_rect = color_bounds((0, 255, 0))
        percent_rect = color_bounds((255, 255, 0))
        progress_fill_rect = color_bounds((0, 180, 255))
        self.assertFalse(title_rect.colliderect(status_rect))
        self.assertFalse(status_rect.colliderect(progress_fill_rect))
        self.assertFalse(progress_fill_rect.colliderect(percent_rect))

    def test_game_reset_restores_round_state_and_keeps_primary_ball_valid(self):
        game = game_module.Game()
        primary_ball = Ball(10, 20)
        primary_ball.isAlive = True
        primary_ball.isLaunch = True
        primary_ball.vel = Vector(4, -3)
        primary_ball.lastPegHit = Peg(50, 50)
        extra_ball = Ball(30, 40)
        extra_ball.isAlive = True
        game.balls = [primary_ball, extra_ball]
        game.ball = primary_ball

        orange_peg = Peg(200, 200)
        orange_peg.set_color("orange")
        orange_peg.isHit = True
        blue_peg = Peg(300, 200)
        game.pegs = [orange_peg, blue_peg]
        origin_pegs = game.pegs.copy()
        game.bucket.pos.x = 100
        game.bucket.vel.x = 0
        game.score = 500
        game.ballsRemaining = 2
        game.pegsHit = 8
        game.gameOver = True
        game.shouldClear = True
        game.alreadyPlayedOdeToJoy = True
        game.longShotBonus = True

        def restore_colors(reset_pegs):
            reset_pegs[0].set_color("orange")
            reset_pegs[1].set_color("blue")
            return reset_pegs

        song_changes = []
        static_image, quadtree = game.resetRound(
            origin_pegs,
            restore_colors,
            lambda _pegs: self.screen,
            lambda: song_changes.append(True),
        )

        self.assertEqual(game.balls, [primary_ball])
        self.assertIs(game.ball, primary_ball)
        self.assertFalse(game.ball.isAlive)
        self.assertFalse(game.ball.isLaunch)
        self.assertEqual(game.ball.pos.x, configs["WIDTH"] / 2)
        self.assertEqual(game.ball.pos.y, configs["HEIGHT"] / 25)
        self.assertEqual(game.ball.vel.getMag(), 0)
        self.assertIsNone(game.ball.lastPegHit)
        self.assertEqual(game.ballsRemaining, 10)
        self.assertFalse(game.powerUpActive)
        self.assertEqual(game.powerUpCount, 0)
        self.assertEqual(game.pitch, 1.0)
        self.assertEqual(game.pitchRaiseCount, 0)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.pegsHit, 0)
        self.assertEqual(game.orangeCount, 1)
        self.assertFalse(game.gameOver)
        self.assertFalse(game.shouldClear)
        self.assertFalse(game.alreadyPlayedOdeToJoy)
        self.assertEqual(game.timeScale, 1.0)
        self.assertFalse(game.longShotBonus)
        self.assertIs(static_image, self.screen)
        self.assertEqual(len(game.pegs), 2)
        self.assertTrue(all(not peg.isHit for peg in game.pegs))
        self.assertEqual([peg.color for peg in game.pegs], ["orange", "blue"])
        self.assertEqual(game.bucket.pos.x, configs["WIDTH"] / 2)
        self.assertEqual(game.bucket.vel.x, -bucketVelocity / 2)
        self.assertEqual(game.bucket.vel.y, 0)
        self.assertEqual(len(quadtree.pegs), len(game.pegs))
        self.assertIs(game.quadtree, quadtree)
        self.assertEqual(song_changes, [True])

    def test_game_round_reset_reports_loading_progress(self):
        game = game_module.Game()
        origin_pegs = [Peg(400, 300), Peg(500, 300)]
        progress_updates = []

        game.resetRound(
            origin_pegs,
            lambda pegs: pegs,
            lambda pegs, progress_callback: createStaticImage(
                pegs,
                progress_callback=progress_callback,
            ),
            lambda: None,
            progress_callback=lambda progress, status: progress_updates.append(
                (progress, status)
            ),
        )

        progress_values = [progress for progress, _ in progress_updates]
        self.assertEqual(progress_values, sorted(progress_values))
        self.assertEqual(progress_values[-1], 1.0)
        statuses = [status for _, status in progress_updates]
        self.assertIn("Preparing peg data", statuses)
        self.assertIn("Rendering pegs", statuses)
        self.assertIn("Preparing collision index", statuses)

    def test_game_launch_applies_force_and_marks_ball_for_cleanup(self):
        game = game_module.Game()
        game.ball.isAlive = True
        game.ball.isLaunch = True
        aim = game.ball.pos.copy()
        aim.x += 1

        game.launchBall(aim)

        self.assertAlmostEqual(game.ball.vel.getMag(), game.LAUNCH_FORCE)
        self.assertFalse(game.ball.isLaunch)
        self.assertTrue(game.shouldClear)

    def test_fixed_physics_steps_are_independent_of_frame_partitioning(self):
        results = []
        for frame_times in ([0.25] * 48, [2.0] * 6):
            game = game_module.Game()
            ball = Ball(100, 100)
            ball.vel = Vector(3, -2)
            steps = 0

            for elapsed in frame_times:
                game.setFrameTime(elapsed)
                game.accumulateFrameTime()
                while game.physicsAccumulator + 1e-9 >= game.fixedPhysicsStep:
                    ball.update(game.fixedPhysicsStep)
                    game.consumePhysicsStep()
                    steps += 1

            results.append((steps, game.physicsAccumulator, game.interpolationAlpha, ball.pos))

        self.assertEqual(results[0][0], 12)
        self.assertEqual(results[0][0], results[1][0])
        self.assertAlmostEqual(results[0][1], results[1][1])
        self.assertAlmostEqual(results[0][2], results[1][2])
        self.assertAlmostEqual(results[0][3].x, results[1][3].x)
        self.assertAlmostEqual(results[0][3].y, results[1][3].y)

    def test_physics_catch_up_is_bounded_and_discards_whole_step_backlog(self):
        game = game_module.Game()
        game.setFrameTime(10.5)
        game.beginPhysicsFrame()
        game.accumulateFrameTime()

        while (
            game.physicsAccumulator + 1e-9 >= game.fixedPhysicsStep
            and game.physicsStepsThisFrame < game.maxPhysicsStepsPerFrame
        ):
            game.consumePhysicsStep()

        game.finishPhysicsFrame()

        self.assertEqual(
            game.physicsStepsThisFrame, game.maxPhysicsStepsPerFrame
        )
        self.assertAlmostEqual(game.physicsDroppedTimeThisFrame, 2.0)
        self.assertAlmostEqual(game.physicsDroppedTime, 2.0)
        self.assertAlmostEqual(game.physicsAccumulator, 0.5)
        self.assertAlmostEqual(game.interpolationAlpha, 0.5)

    def test_bucket_keeps_moving_during_zenball_search_without_physics_steps(self):
        game = game_module.Game()
        game.bucket.t = 0.25
        game.bucket.t_direction = 1
        game.bucket.pos.x = 250
        game.bucket.prevPos.x = 250
        game.frameDt = 10
        game.physicsAccumulator = 0.5
        starting_t = game.bucket.t
        starting_x = game.bucket.pos.x

        game.updateBucketDuringZenballSearch()

        self.assertGreater(game.bucket.t, starting_t)
        self.assertNotEqual(game.bucket.pos.x, starting_x)
        self.assertEqual(game.bucket.prevPos.x, starting_x)
        self.assertEqual(game.physicsAccumulator, 0.5)
        self.assertEqual(game.interpolationAlpha, 1.0)

    def test_swept_circle_collision_detects_high_speed_crossing(self):
        ball = Ball(0, 100)
        ball.prevPos = Vector(-100, 100)
        ball.pos = Vector(100, 100)
        ball.vel = Vector(200, 0)
        peg = Peg(0, 100)

        self.assertTrue(isBallTouchingPeg(ball, peg, 1))

        resolveCollision(ball, [peg], 1)

        self.assertLess(ball.pos.x, peg.pos.x)
        self.assertLess(ball.vel.x, 0)

    def test_swept_collision_resolves_the_earliest_peg_independent_of_order(self):
        near_peg = Peg(100, 100)
        far_peg = Peg(150, 100)
        resolved_pegs = []

        for candidates in ([far_peg, near_peg], [near_peg, far_peg]):
            ball = Ball(0, 100)
            ball.prevPos = Vector(0, 100)
            ball.pos = Vector(200, 100)
            ball.vel = Vector(200, 0)
            resolved_pegs.append(resolveCollisionAndGetPeg(ball, candidates))

        self.assertEqual(resolved_pegs, [near_peg, near_peg])

    def test_swept_quadtree_query_includes_pegs_along_the_ball_path(self):
        ball = Ball(0, 100)
        ball.prevPos = Vector(-100, 100)
        ball.pos = Vector(100, 100)
        peg = Peg(0, 100)
        quadtree = QuadtreePegs(Rectangle(0, 100, 200, 200), 1)
        quadtree.insert(peg)

        candidates = quadtree.query(getSweptCollisionBounds(ball, 5))

        self.assertIn(peg, candidates)

    def test_quadtree_query_into_reuses_storage_and_finds_same_candidates(self):
        pegs = [
            Peg(12 + (index % 40) * 24, 14 + (index // 40) * 28)
            for index in range(1000)
        ]
        quadtree = QuadtreePegs(Rectangle(480, 360, 480, 360), len(pegs))
        for peg in pegs:
            quadtree.insert(peg)
        query = Rectangle(480, 360, 50, 50)
        expected = quadtree.query(query)
        reusable_results = [pegs[0]]
        quadtree.queryInto(query, reusable_results)

        self.assertIs(reusable_results[0], pegs[0])
        self.assertEqual(reusable_results[1:], expected)
        self.assertLess(len(expected), len(pegs) // 10)

    def test_quadtree_bulk_build_matches_incremental_insertion(self):
        pegs = [
            Peg((index * 37) % 1000 - 20, (index * 53) % 760 - 20)
            for index in range(500)
        ]
        pegs.extend((Peg(480, 360), Peg(0, 0), Peg(960, 720)))
        boundary = Rectangle(480, 360, 480, 360)
        incremental = QuadtreePegs(boundary, len(pegs))
        bulk = QuadtreePegs(boundary, len(pegs))

        for peg in pegs:
            incremental.insert(peg)
        inserted_count = bulk.insert_many(pegs)

        self.assertEqual(inserted_count, len(incremental.query(boundary)))
        for query in (
            Rectangle(480, 360, 480, 360),
            Rectangle(240, 180, 240, 180),
            Rectangle(480, 360, 40, 40),
            Rectangle(960, 720, 30, 30),
        ):
            self.assertEqual(bulk.query(query), incremental.query(query))
        removable_peg = next(
            peg for peg in pegs if boundary.contains(peg)
        )
        self.assertTrue(bulk.remove(removable_peg))
        self.assertTrue(incremental.remove(removable_peg))
        self.assertEqual(
            bulk.query(boundary),
            incremental.query(boundary),
        )

    def test_quadtree_bulk_build_reports_progress(self):
        pegs = [Peg(index % 100, index % 80) for index in range(100)]
        quadtree = QuadtreePegs(Rectangle(50, 40, 50, 40), len(pegs))
        progress_updates = []

        quadtree.insert_many(
            pegs,
            progress_callback=lambda progress, status: progress_updates.append(
                (progress, status)
            ),
        )

        progress_values = [progress for progress, _ in progress_updates]
        self.assertEqual(progress_values, sorted(progress_values))
        self.assertEqual(progress_values[-1], 1.0)
        self.assertTrue(
            all(
                status
                in (
                    "Preparing collision index",
                    "Distributing collision index",
                )
                for _, status in progress_updates
            )
        )

    def test_quadtree_removal_keeps_other_pegs_queryable(self):
        pegs = [Peg(100 + index * 20, 100) for index in range(12)]
        quadtree = QuadtreePegs(Rectangle(240, 200, 240, 200), len(pegs))
        for peg in pegs:
            quadtree.insert(peg)

        self.assertTrue(quadtree.remove(pegs[5]))
        found = quadtree.query(Rectangle(200, 100, 200, 10))

        self.assertNotIn(pegs[5], found)
        self.assertTrue(all(peg in found for peg in pegs[:5] + pegs[6:]))
        self.assertFalse(quadtree.remove(Peg(100, 100)))

    def test_quadtree_handles_many_pegs_at_the_same_position(self):
        pegs = [Peg(100, 100) for _ in range(40)]
        quadtree = QuadtreePegs(Rectangle(200, 200, 200, 200), len(pegs))

        for peg in pegs:
            self.assertTrue(quadtree.insert(peg))

        self.assertEqual(
            len(quadtree.query(Rectangle(100, 100, 1, 1))),
            len(pegs),
        )

    def test_fixed_step_collisions_match_at_low_and_high_render_rates(self):
        peg = Peg(200, 100)
        quadtree = QuadtreePegs(Rectangle(480, 360, 480, 360), 1)
        quadtree.insert(peg)
        results = []

        for frame_times in ([40.0], [1.0] * 40):
            game = game_module.Game()
            ball = Ball(100, 100)
            ball.vel = Vector(10, 0)
            bounds = Rectangle(0, 0, 0, 0)
            candidates = []
            hit_count = 0

            for elapsed in frame_times:
                game.setFrameTime(elapsed)
                game.accumulateFrameTime()
                while (
                    game.physicsAccumulator + 1e-9
                    >= game.fixedPhysicsStep
                ):
                    updateSweptCollisionBounds(
                        ball, game.queryRectSize, bounds
                    )
                    candidates.clear()
                    quadtree.queryInto(bounds, candidates)
                    if resolveCollisionAndGetPeg(ball, candidates) is peg:
                        hit_count += 1
                    ball.update(game.fixedPhysicsStep)
                    game.consumePhysicsStep()

            results.append((hit_count, ball.pos.x, ball.pos.y, ball.vel.x, ball.vel.y))

        self.assertEqual(results[0][0], 1)
        self.assertEqual(results[0][0], results[1][0])
        for coarse, fine in zip(results[0][1:], results[1][1:]):
            self.assertAlmostEqual(coarse, fine)

    def test_game_records_intermediate_ball_positions_for_frame_path(self):
        game = game_module.Game()
        ball = game.ball
        ball.isAlive = True
        game.beginPhysicsFrame()

        ball.pos = Vector(110, 90)
        game.recordBallPhysicsPosition(ball)
        ball.pos = Vector(120, 100)
        game.recordBallPhysicsPosition(ball)

        self.assertEqual(
            game.debugBallFramePaths[ball],
            [(ball.originX, ball.originY), (110, 90), (120, 100)],
        )

    def test_swept_circle_collision_handles_stationary_overlap(self):
        ball = Ball(0, 100)
        peg = Peg(0, 100)

        self.assertTrue(isBallTouchingPeg(ball, peg, 1))

        resolveCollision(ball, [peg], 1)

        separation = ball.pos.copy()
        separation.sub(peg.pos)
        self.assertGreater(separation.getMag(), 0)

    def test_close_call_uses_scaled_peg_radius_without_changing_peg(self):
        ball = Ball(100, 100)
        ball.pos = Vector(150, 100)
        ball.prevPos = ball.pos.copy()
        peg = Peg(100, 100, "orange")
        original_radius = peg.radius

        self.assertFalse(isBallTouchingPeg(ball, peg, 1))
        self.assertTrue(
            isBallTouchingPeg(ball, peg, 1, peg_radius_multiplier=5)
        )
        self.assertEqual(peg.radius, original_radius)

    def test_static_image_caches_scaled_background_and_skips_disk_load(self):
        background = pygame.Surface((17, 13))
        original_scale = pygame.transform.scale
        with (
            patch.object(
                misc_module.pygame.image,
                "load",
                side_effect=AssertionError("static image should not load assets"),
            ),
            patch.object(
                misc_module.pygame.transform,
                "scale",
                wraps=original_scale,
            ) as scale,
        ):
            first = misc_module.createStaticImage([], background)
            second = misc_module.createStaticImage([], background)

        self.assertIsNot(first, second)
        scale.assert_called_once_with(background, (configs["WIDTH"], configs["HEIGHT"]))

    def test_static_image_reports_rendering_progress(self):
        progress_updates = []
        pegs = [Peg(100 + index * 10, 100) for index in range(10)]

        createStaticImage(
            pegs,
            progress_callback=lambda progress, status: progress_updates.append(
                (progress, status)
            ),
        )

        progress_values = [progress for progress, _ in progress_updates]
        self.assertEqual(progress_values, sorted(progress_values))
        self.assertEqual(progress_values[-1], 1.0)
        self.assertIn("Rendering pegs", [status for _, status in progress_updates])
        self.assertIn("Preparing peg data", [status for _, status in progress_updates])

    def test_incremental_static_image_matches_full_redraw_after_hit_and_removal(self):
        pegs = []
        for index in range(18):
            peg = Peg(300 + (index % 3) * 12, 260 + (index % 4) * 10)
            peg.set_color(("blue", "orange", "green")[index % 3])
            pegs.append(peg)

        optimized_image = createStaticImage(pegs)
        changed_peg = pegs[4]
        changed_peg.isHit = True
        changed_peg.pos.x += 80
        changed_peg.pos.y += 40
        removed_pegs = [pegs[1], pegs[9], pegs[14]]
        active_pegs = [peg for peg in pegs if peg not in removed_pegs]

        updateStaticImagePegs(
            optimized_image,
            active_pegs,
            [changed_peg],
            removed_pegs,
        )
        full_redraw = createStaticImage(active_pegs)

        self.assertEqual(
            pygame.image.tobytes(optimized_image, "RGBA"),
            pygame.image.tobytes(full_redraw, "RGBA"),
        )

    def test_fractional_peg_removal_clears_every_rendered_pixel(self):
        pegs = [Peg(300.5, 260.5), Peg(360.25, 300.75)]
        optimized_image = createStaticImage(pegs)
        removed_peg = pegs[0]
        remaining_pegs = pegs[1:]

        updateStaticImagePegs(
            optimized_image,
            remaining_pegs,
            [],
            [removed_peg],
        )
        full_redraw = createStaticImage(remaining_pegs)

        self.assertEqual(
            pygame.image.tobytes(optimized_image, "RGBA"),
            pygame.image.tobytes(full_redraw, "RGBA"),
        )

    def test_game_validates_only_registered_stuck_timers(self):
        game = game_module.Game()
        active_peg = Peg(100, 100)
        outside_contact_peg = Peg(200, 100)
        active_ball = Ball(100, 100)
        outside_contact_ball = Ball(200, 100)
        active_ball.isAlive = True
        outside_contact_ball.isAlive = True
        active_peg.ballStuckBalls.add(active_ball)
        outside_contact_peg.ballStuckBalls.add(outside_contact_ball)

        with patch("local.triggerEvents.time.time", return_value=10.0):
            active_peg.ballStuckTimer.setTimer(10.0)
            outside_contact_peg.ballStuckTimer.setTimer(10.0)
        outside_contact_ball.pos.x = 300
        game.pegsWithActiveStuckTimers.update(
            (active_peg, outside_contact_peg)
        )

        with patch("local.triggerEvents.time.time", return_value=11.0):
            game.validateActiveStuckTimers()

        self.assertTrue(active_peg.ballStuckTimer.isActive)
        self.assertFalse(outside_contact_peg.ballStuckTimer.isActive)
        self.assertEqual(game.pegsWithActiveStuckTimers, {active_peg})

    def test_removing_peg_cluster_removes_neighbors_at_proximity_boundary(self):
        game = game_module.Game()
        source_peg = Peg(200, 200)
        source_peg.set_color("orange")
        proximity = (
            source_peg.radius
            * game_module.PEG_REMOVAL_PROXIMITY_MULTIPLIER
        )
        boundary_peg = Peg(200 + proximity, 200)
        boundary_peg.set_color("orange")
        outside_peg = Peg(200 + proximity + 0.1, 200)
        outside_peg.set_color("orange")
        source_peg.isHit = True
        source_peg.cancel_ball_stuck_timer()
        game.pegs = [source_peg, boundary_peg, outside_peg]
        game.orangeCount = 2
        boundary = Rectangle(200, 200, 100, 100)
        quadtree = QuadtreePegs(boundary, len(game.pegs))
        quadtree.insert_many(game.pegs)

        ball = Ball(boundary_peg.pos.x, 200)
        ball.isAlive = True
        with patch("local.triggerEvents.time.time", return_value=10.0):
            boundary_peg.ballStuckTimer.setTimer(10.0)
        boundary_peg.ballStuckBalls.add(ball)
        game.pegsWithActiveStuckTimers.add(boundary_peg)

        removed = game.remove_peg_cluster(source_peg, quadtree)

        self.assertEqual(removed, [source_peg, boundary_peg])
        self.assertEqual(game.pegs, [outside_peg])
        self.assertEqual(game.orangeCount, 1)
        self.assertEqual(game.score, 1000)
        self.assertTrue(boundary_peg.isHit)
        self.assertEqual(
            quadtree.query(
                Rectangle(boundary_peg.pos.x, 200, 0.01, 0.01)
            ),
            [],
        )
        self.assertEqual(
            quadtree.query(
                Rectangle(outside_peg.pos.x, 200, 0.01, 0.01)
            ),
            [outside_peg],
        )
        self.assertFalse(boundary_peg.ballStuckTimer.isActive)
        self.assertEqual(boundary_peg.ballStuckBalls, set())
        self.assertEqual(game.pegsWithActiveStuckTimers, set())

    def test_peg_cluster_removal_awards_points_along_bounded_ball_path(self):
        game = game_module.Game()
        source_peg = Peg(200, 200)
        source_peg.isHit = True
        path_peg = Peg(260, 200)
        path_peg.set_color("orange")
        outside_corridor_peg = Peg(260, 230)
        outside_corridor_peg.set_color("orange")
        beyond_path_peg = Peg(310.1, 200)
        beyond_path_peg.set_color("orange")
        game.pegs = [
            source_peg,
            path_peg,
            outside_corridor_peg,
            beyond_path_peg,
        ]
        game.orangeCount = 3
        boundary = Rectangle(250, 215, 150, 100)
        quadtree = QuadtreePegs(boundary, len(game.pegs))
        quadtree.insert_many(game.pegs)

        removed = game.remove_peg_cluster(
            source_peg,
            quadtree,
            Vector(1, 0),
        )

        self.assertEqual(removed, [source_peg, path_peg])
        self.assertEqual(
            game.pegs,
            [outside_corridor_peg, beyond_path_peg],
        )
        self.assertEqual(game.orangeCount, 2)
        self.assertEqual(game.score, 1000)
        self.assertTrue(path_peg.isHit)

    def test_peg_path_removal_is_capped_to_a_small_group(self):
        game = game_module.Game()
        source_peg = Peg(200, 200)
        source_peg.isHit = True
        path_pegs = [Peg(240 + index * 5, 200) for index in range(10)]
        game.pegs = [source_peg, *path_pegs]
        boundary = Rectangle(480, 360, 480, 360)
        quadtree = QuadtreePegs(boundary, len(game.pegs))
        quadtree.insert_many(game.pegs)

        removed = game.remove_peg_cluster(
            source_peg,
            quadtree,
            Vector(1, 0),
        )

        self.assertEqual(
            removed,
            [source_peg, *path_pegs[:game_module.MAX_ADDITIONAL_PATH_PEG_REMOVALS]],
        )
        self.assertEqual(
            game.pegs,
            path_pegs[game_module.MAX_ADDITIONAL_PATH_PEG_REMOVALS:],
        )

    def test_large_static_image_updates_rebuild_instead_of_removing_pegs_individually(self):
        pegs = [
            Peg(20 + (index % 20) * 35, 20 + (index // 20) * 30)
            for index in range(400)
        ]
        image = createStaticImage(pegs)
        remaining_pegs = pegs[300:]

        updated_image = updateStaticImagePegs(
            image,
            remaining_pegs,
            [],
            pegs[:300],
        )

        self.assertIsNot(updated_image, image)
        self.assertEqual(
            pygame.image.tobytes(updated_image, "RGBA"),
            pygame.image.tobytes(createStaticImage(remaining_pegs), "RGBA"),
        )

    def test_incremental_static_image_handles_dense_removal_batches(self):
        pegs = [Peg(400, 300) for _ in range(1000)]
        image = createStaticImage(pegs)
        remaining_pegs = pegs[250:]

        updateStaticImagePegs(image, remaining_pegs, [], pegs[:250])

        self.assertEqual(
            pygame.image.tobytes(image, "RGBA"),
            pygame.image.tobytes(createStaticImage(remaining_pegs), "RGBA"),
        )

    def test_static_image_tracking_does_not_keep_surfaces_alive(self):
        image = createStaticImage([])
        image_ref = weakref.ref(image)

        del image
        gc.collect()

        self.assertIsNone(image_ref())

    def test_massive_level_spawn_animations_are_skipped(self):
        self.assertTrue(animate_module.shouldAnimatePegs(animate_module.MAX_ANIMATED_PEGS))
        self.assertFalse(
            animate_module.shouldAnimatePegs(animate_module.MAX_ANIMATED_PEGS + 1)
        )

    def test_large_level_preview_limits_peg_object_creation(self):
        positions = [(index, index + 1) for index in range(6001)]
        with tempfile.NamedTemporaryFile() as level_file:
            with open(level_file.name, "wb") as file:
                pickle.dump(positions, file)

            preview_pegs, _ = loadData(
                level_file.name,
                centerPegs=False,
                peg_limit=level_menu_module.MAX_LEVEL_PREVIEW_PEGS,
            )

        self.assertEqual(
            len(preview_pegs),
            level_menu_module.MAX_LEVEL_PREVIEW_PEGS,
        )
        self.assertEqual(preview_pegs[0].pos.x, positions[0][0])
        self.assertEqual(preview_pegs[-1].pos.x, positions[-1][0])

    def test_load_data_rejects_nonpositive_peg_limit(self):
        with self.assertRaises(ValueError):
            loadData("unused", centerPegs=False, peg_limit=0)

    def test_animation_reuses_converted_and_scaled_images(self):
        animation = animate_module.AnimationFade(Vector(20, 20))
        source = pygame.Surface((9, 9), pygame.SRCALPHA)
        animation.set_image(source)
        converted = animation.original
        animation.set_image(source)
        second_animation = animate_module.AnimationFade(Vector(30, 30))
        second_animation.set_image(source)
        animation.elapsed = 0.5
        second_animation.elapsed = 0.501
        first_target = pygame.Surface((40, 40), pygame.SRCALPHA)
        second_target = pygame.Surface((40, 40), pygame.SRCALPHA)
        original_scale = pygame.transform.scale

        with patch.object(
            animate_module.pygame.transform,
            "scale",
            wraps=original_scale,
        ) as scale:
            animation.draw(first_target)
            animation.draw(second_target)

        self.assertIs(animation.original, converted)
        self.assertIs(second_animation.original, converted)
        scale.assert_called_once()

    def test_peg_animation_frame_reuses_and_clears_target_surface(self):
        peg = Peg(30, 30)
        peg.animation.startFadeIn()
        target = pygame.Surface(
            (configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA
        )
        target.fill((255, 0, 0, 255))

        frame = animate_module.getPegAnimationFrame([peg], 0, target)

        self.assertIs(frame, target)
        self.assertEqual(frame.get_at((0, 0)), (0, 0, 0, 0))

    def test_delayed_peg_fade_out_uses_underlying_peg_layer(self):
        animation = animate_module.AnimationFade(Vector(20, 20))
        source = pygame.Surface((10, 10), pygame.SRCALPHA)
        source.fill((255, 255, 255))
        animation.set_image(source)
        animation.startFadeOut(delay=1.0)
        target = pygame.Surface((50, 50), pygame.SRCALPHA)

        with patch.object(
            animate_module.pygame.transform,
            "scale",
            wraps=pygame.transform.scale,
        ) as scale:
            animation.draw(target)

        scale.assert_not_called()
        self.assertEqual(target.get_at((15, 15)), (0, 0, 0, 0))

    def test_completed_spawn_animation_keeps_peg_visible(self):
        animation = animate_module.AnimationFade(Vector(20, 20))
        source = pygame.Surface((10, 10), pygame.SRCALPHA)
        source.fill((255, 255, 255))
        animation.set_image(source)
        animation.fadeIn = True
        animation.done = True
        target = pygame.Surface((50, 50), pygame.SRCALPHA)

        animation.draw(target)

        self.assertEqual(target.get_at((20, 20)), (255, 255, 255, 255))

    def test_completed_spawn_peg_is_cached_once_in_completed_layer(self):
        peg = Peg(30, 30)
        peg.animation.duration = 0.1
        active_frame = pygame.Surface(
            (configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA
        )
        completed_frame = pygame.Surface(
            (configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA
        )

        animate_module.getPegAnimationFrame(
            [peg], 0.1, active_frame, completed_frame
        )
        self.assertTrue(peg.animation.completion_drawn)
        self.assertGreater(completed_frame.get_at((30, 30)).a, 0)
        self.assertEqual(active_frame.get_at((30, 30)).a, 0)

        completed_frame_snapshot = pygame.image.tobytes(
            completed_frame, "RGBA"
        )
        animate_module.getPegAnimationFrame(
            [peg], 0.1, active_frame, completed_frame
        )
        self.assertEqual(
            pygame.image.tobytes(completed_frame, "RGBA"),
            completed_frame_snapshot,
        )
        self.assertEqual(active_frame.get_at((30, 30)).a, 0)

    def test_spawn_renderer_scales_background_only_when_size_changes(self):
        renderer = GameRenderer(self.screen)
        game = game_module.Game()
        static_image = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        animation_frame = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        with (
            patch.object(renderer, "_draw_zoomed_world"),
            patch.object(renderer, "_draw_scoreboard"),
            patch.object(
                pygame.transform,
                "scale",
                wraps=pygame.transform.scale,
            ) as scale,
        ):
            for _ in range(2):
                renderer.draw_world(
                    game,
                    static_image,
                    animation_frame,
                    [],
                    False,
                    True,
                    False,
                )

        scale.assert_called_once()

    def test_spawn_renderer_uses_background_composited_into_completed_layer(self):
        renderer = GameRenderer(self.screen)
        game = game_module.Game()
        completed_frame = pygame.Surface(
            self.screen.get_size(), pygame.SRCALPHA
        )
        animation_frame = pygame.Surface(
            self.screen.get_size(), pygame.SRCALPHA
        )
        renderer.prepare_spawn_frame(completed_frame)
        background_pixel = completed_frame.get_at((0, 0))

        with (
            patch.object(renderer, "_draw_zoomed_world"),
            patch.object(renderer, "_draw_scoreboard"),
        ):
            renderer.draw_world(
                game,
                pygame.Surface(self.screen.get_size()),
                animation_frame,
                [],
                False,
                True,
                False,
                completed_frame,
            )

        self.assertEqual(self.screen.get_at((0, 0)), background_pixel)

    def test_performance_metrics_keep_a_bounded_rolling_summary(self):
        metrics = PerformanceMetrics()
        metrics.WINDOW_SIZE = 3
        for sample in (1.0, 2.0, 3.0, 4.0):
            metrics.record_ms("physics_step", sample)

        self.assertEqual(metrics.summary("physics_step"), (4.0, 4.0, 4.0))
        self.assertEqual(metrics.summary("unknown"), (0.0, 0.0, 0.0))
        self.assertEqual(metrics.severity("physics_step", 1.9), "normal")
        self.assertEqual(metrics.severity("physics_step", 2.0), "yellow")
        self.assertEqual(metrics.severity("physics_step", 5.0), "red")
        self.assertEqual(metrics.severity("display_present", 100.0), "normal")

    def test_per_frame_metrics_reset_and_accumulate_each_frame(self):
        metrics = PerformanceMetrics()
        metrics.begin_frame()
        metrics.record_ms("physics_step", 1.5)
        metrics.record_ms("physics_step", 2.0)
        metrics.end_frame()
        self.assertEqual(metrics.summary("physics_step"), (3.5, 3.5, 3.5))

        metrics.begin_frame()
        metrics.end_frame()
        self.assertEqual(metrics.summary("physics_step"), (0.0, 3.5, 3.5))

    def test_renderer_records_layer_and_ball_timings(self):
        renderer = GameRenderer(self.screen)
        game = game_module.Game()
        metrics = PerformanceMetrics()
        static_image = pygame.Surface(self.screen.get_size())
        animation_frame = pygame.Surface(
            self.screen.get_size(), pygame.SRCALPHA
        )

        with (
            patch.object(renderer, "_draw_zoomed_world"),
            patch.object(renderer, "_draw_scoreboard"),
        ):
            renderer.draw_world(
                game,
                static_image,
                animation_frame,
                [],
                False,
                False,
                False,
                performance=metrics,
            )

        self.assertGreater(metrics.summary("static_peg_layer")[0], 0)
        self.assertGreater(metrics.summary("bucket_render")[0], 0)
        self.assertGreater(metrics.summary("ball_render")[0], 0)

    def test_performance_overlay_draws_without_general_debug_mode(self):
        renderer = GameRenderer(self.screen)
        metrics = PerformanceMetrics()
        metrics.record_ms("physics_frame", 4.2)
        metrics.record_ms("frame_cpu", 12.5)
        metrics.record_ms("static_image_build", 80.0)
        self.screen.fill((200, 0, 0))
        initial_image = pygame.image.tobytes(self.screen, "RGBA")
        rendered_colors = []
        original_font = renderer_module.debugFont

        class RecordingFont:
            def render(self, text, antialias, color):
                rendered_colors.append(color)
                return original_font.render(text, antialias, color)

        with patch.object(renderer_module, "debugFont", RecordingFont()):
            renderer.draw_performance_metrics(metrics)

        self.assertNotEqual(
            pygame.image.tobytes(self.screen, "RGBA"),
            initial_image,
        )
        panel = renderer._performance_panel
        self.assertIsNotNone(panel)
        assert panel is not None
        panel_top = configs["HEIGHT"] - panel.get_height() - 10
        self.assertGreater(panel_top, configs["HEIGHT"] // 2)
        self.assertEqual(tuple(self.screen.get_at((5, 5))[:3]), (200, 0, 0))
        self.assertNotEqual(
            tuple(self.screen.get_at((15, panel_top + 15))[:3]),
            (200, 0, 0),
        )
        self.assertIn((255, 215, 80), rendered_colors)
        self.assertIn((255, 92, 92), rendered_colors)

    def test_game_hud_groups_score_objective_and_power_up_in_a_panel(self):
        game = game_module.Game()
        game.score = 12345
        game.ballsRemaining = 4
        game.orangeCount = 7
        game.powerUpCount = 2
        renderer = GameRenderer(self.screen)
        self.screen.fill((200, 0, 0))
        initial_pixel = tuple(self.screen.get_at((80, 20))[:3])
        rendered_text = []
        original_debug_font = renderer_module.debugFont
        original_info_font = renderer_module.infoFont
        original_ball_font = renderer_module.ballCountFont

        class RecordingFont:
            def __init__(self, font):
                self.font = font

            def render(self, text, antialias, color):
                rendered_text.append(text)
                return self.font.render(text, antialias, color)

        with (
            patch.object(
                renderer_module,
                "debugFont",
                RecordingFont(original_debug_font),
            ),
            patch.object(
                renderer_module,
                "infoFont",
                RecordingFont(original_info_font),
            ),
            patch.object(
                renderer_module,
                "ballCountFont",
                RecordingFont(original_ball_font),
            ),
        ):
            renderer._draw_scoreboard(game, False)

        for label in ("SCORE", "BALLS LEFT", "ORANGE LEFT", "MULTIPLIER", "POWER-UP"):
            self.assertIn(label, rendered_text)
        self.assertIn("12,345", rendered_text)
        self.assertIn("4", rendered_text)
        self.assertIn("7", rendered_text)
        self.assertNotEqual(
            tuple(self.screen.get_at((80, 20))[:3]),
            initial_pixel,
        )

    def test_developer_panel_groups_frame_rate_and_debug_state(self):
        game = game_module.Game()
        game.pegs = [Peg(100, 100), Peg(200, 200)]
        game.orangeCount = 1
        game.physicsStepsThisFrame = 2
        game.quadtree = QuadtreePegs(Rectangle(480, 360, 480, 360), 2)
        renderer = GameRenderer(self.screen)
        rendered_text = []
        original_font = renderer_module.debugFont

        class RecordingFont:
            def render(self, text, antialias, color):
                rendered_text.append(text)
                return original_font.render(text, antialias, color)

        with (
            patch.dict(configs, {"DEBUG_MODE": True}),
            patch.object(renderer_module, "debugFont", RecordingFont()),
        ):
            renderer.draw_debug(
                game,
                FastClock(),
                (480, 360),
                True,
                None,
                [],
                Rectangle(0, 0, 0, 0),
                game.quadtree,
                0.02,
                0.01,
            )

        self.assertIn("DEVELOPER  |  LIVE", rendered_text)
        self.assertIn("PERFORMANCE", rendered_text)
        self.assertIn("GAME STATE", rendered_text)
        self.assertTrue(any(text.startswith("FPS") for text in rendered_text))
        self.assertTrue(any(text.startswith("Frame") for text in rendered_text))
        self.assertTrue(any(text.startswith("Pegs") for text in rendered_text))
        self.assertFalse(any(text.endswith(" fps") for text in rendered_text))

    def test_performance_overlay_reuses_cached_panel_between_refreshes(self):
        renderer = GameRenderer(self.screen)
        metrics = PerformanceMetrics()

        with patch.object(metrics, "summary", wraps=metrics.summary) as summary:
            renderer.draw_performance_metrics(metrics)
            calls_after_update = summary.call_count
            renderer.draw_performance_metrics(metrics)

        self.assertGreater(calls_after_update, 0)
        self.assertEqual(summary.call_count, calls_after_update)
        panel = renderer._performance_panel
        assert panel is not None
        self.assertEqual(
            panel.get_width(),
            round(
                min(configs["WIDTH"] - 20, 980)
                * renderer.PERFORMANCE_PANEL_SCALE
            ),
        )

    def test_best_trajectory_search_can_be_advanced_incrementally(self):
        aim = Vector(480, 200)
        start = Vector(480, 30)
        peg = Peg(400, 300)
        pegs = [peg]
        quadtree = QuadtreePegs(Rectangle(480, 360, 480, 360), 1)
        quadtree.insert(peg)
        search = BestTrajectorySearch(
            aim, start, pegs, quadtree, 1, maxRangeDegrees=1, depth=500, setTimeLimit=0
        )

        completed = search.advance(0.00001)
        advance_calls = 1
        while not completed and advance_calls < 1000:
            completed = search.advance(0.00001)
            advance_calls += 1

        self.assertTrue(completed, "the trajectory search should eventually finish")
        self.assertGreater(advance_calls, 1)
        self.assertIsNotNone(search.result)
        self.assertEqual(aim.x, 480)
        self.assertEqual(aim.y, 200)
        self.assertFalse(peg.isHit)

    def test_zenball_search_scores_real_orange_hits_without_mutating_pegs(self):
        orange_peg = Peg(480, 100)
        orange_peg.set_color("orange")
        quadtree = QuadtreePegs(Rectangle(480, 360, 480, 360), 1)
        quadtree.insert(orange_peg)
        start = Vector(480, 50)
        aim = Vector(480, 51)
        search = BestTrajectorySearch(
            aim,
            start,
            [orange_peg],
            quadtree,
            1,
            maxRangeDegrees=0,
            depth=100,
            setTimeLimit=1,
        )

        while not search.advance(0.01):
            pass

        self.assertIsNotNone(search.result)
        self.assertGreaterEqual(search.result[1], 1000)
        self.assertFalse(search.reached_bucket)
        self.assertFalse(orange_peg.isHit)

    def test_zenball_search_includes_the_long_shot_score_bonus(self):
        first_peg = Peg(100, 100)
        orange_peg = Peg(500, 100)
        orange_peg.set_color("orange")
        search = BestTrajectorySearch(
            Vector(480, 51),
            Vector(480, 50),
            [first_peg, orange_peg],
            QuadtreePegs(Rectangle(480, 360, 480, 360), 0),
            1,
            maxRangeDegrees=0,
            depth=3,
            setTimeLimit=1,
        )

        with (
            patch("local.trajectory.longShotDistance", 10),
            patch(
                "local.trajectory.resolveCollisionAndGetPeg",
                side_effect=[first_peg, orange_peg, None],
            ),
        ):
            while not search.advance(0.01):
                pass

        self.assertIsNotNone(search.result)
        self.assertGreaterEqual(search.result[1], 25_000)

    def test_zenball_search_can_choose_a_bucket_path_without_peg_score(self):
        bucket = Bucket()
        start = Vector(150, 50)
        aim = Vector(150, 51)
        search = BestTrajectorySearch(
            aim,
            start,
            [],
            QuadtreePegs(Rectangle(480, 360, 480, 360), 0),
            1,
            maxRangeDegrees=0,
            depth=300,
            setTimeLimit=1,
            bucket=bucket,
        )

        while not search.advance(0.01):
            pass

        self.assertIsNotNone(search.result)
        self.assertEqual(search.result[1], 0)
        self.assertTrue(search.reached_bucket)

    def test_zenball_bucket_markers_match_bucket_after_trajectory_steps(self):
        bucket = Bucket()
        bucket.t = 0.37
        bucket.t_direction = -1
        start = Vector(480, 50)
        search = BestTrajectorySearch(
            Vector(480, 51),
            start,
            [],
            QuadtreePegs(Rectangle(480, 360, 480, 360), 0),
            1,
            maxRangeDegrees=0,
            depth=40,
            setTimeLimit=1,
            bucket=bucket,
        )

        while not search.advance(0.01):
            pass

        self.assertIsNotNone(search.result)
        trajectory = search.result[2]
        self.assertGreater(len(trajectory), 0)

        # The bucket can move while Zenball is calculating, then move again
        # during the rendered frame in which the search finishes.
        for _ in range(5):
            bucket.update(2.5)
        for _ in range(3):
            bucket.update(1.0)
        predicted_markers = bucket.predictMarkerPositions(
            len(trajectory), 1.0
        )
        marker_image = createStaticCircles(
            trajectory,
            predicted_markers,
        )
        for predicted_point in predicted_markers:
            marker_color = marker_image.get_at(
                (round(predicted_point[0]), round(predicted_point[1]))
            )
            self.assertEqual(tuple(marker_color[:3]), (255, 40, 40))

        for _ in trajectory:
            bucket.update(1)

        for predicted_point, offset in zip(
            predicted_markers, bucket.fakePegOffsets
        ):
            self.assertAlmostEqual(
                predicted_point[0], bucket.pos.x + offset[0]
            )
            self.assertAlmostEqual(
                predicted_point[1],
                bucket.pos.y + bucket.bucketBackImg.get_height() / 2,
            )

    def test_bucket_position_prediction_matches_updates_across_turnarounds(self):
        for start_t, start_direction in ((0.999, 1), (0.001, -1)):
            with self.subTest(t=start_t, direction=start_direction):
                bucket = Bucket()
                bucket.t = start_t
                bucket.t_direction = start_direction
                predicted = bucket.predictFakePegPositions(20, 1.0)

                for _ in range(20):
                    bucket.update(1.0)

                for predicted_point, fake_peg in zip(
                    predicted, bucket.fakePegs
                ):
                    self.assertAlmostEqual(
                        predicted_point[0], fake_peg.pos.x
                    )
                    self.assertAlmostEqual(
                        predicted_point[1], fake_peg.pos.y
                    )

    def test_zenball_search_honors_its_time_limit_and_returns_best_so_far(self):
        search = BestTrajectorySearch(
            Vector(480, 51),
            Vector(480, 50),
            [],
            QuadtreePegs(Rectangle(480, 360, 480, 360), 0),
            1,
            maxRangeDegrees=0,
            depth=100_000,
            setTimeLimit=0.03,
        )

        self.assertTrue(search.advance(1.0))
        self.assertLess(search.elapsed, 0.25)
        self.assertIsNotNone(search.result)
        self.assertGreater(len(search.result[2]), 0)

    def test_aim_trajectory_calculation_can_be_advanced_incrementally(self):
        calculation = TrajectoryCalculation(
            Vector(500, 200),
            Vector(480, 50),
            [],
            [],
            QuadtreePegs(Rectangle(480, 360, 480, 360), 0),
            1,
            depth=20,
        )
        completed = False
        for _ in range(100):
            if calculation.advance(0.0001):
                completed = True
                break

        self.assertTrue(completed)
        self.assertIsNotNone(calculation.result)
        self.assertIs(calculation.result, calculation.points)
        self.assertGreater(len(calculation.points), 0)

    def test_aim_trajectory_resolves_peg_crossed_between_samples(self):
        start = Vector(400, 200)
        peg = Peg(450, 200)
        quadtree = QuadtreePegs(Rectangle(480, 360, 480, 360), 1)
        quadtree.insert(peg)
        calculation = TrajectoryCalculation(
            Vector(600, 200),
            start,
            [peg],
            [],
            quadtree,
            20,
            depth=3,
            debugTrajectory=True,
        )

        self.assertTrue(calculation.advance(float("inf")))
        path_x = [point.pos.x for point in calculation.points]

        self.assertLess(max(path_x), peg.pos.x - 5)
        self.assertTrue(
            any(peg.pos.x - 40 < x < peg.pos.x - 20 for x in path_x)
        )
        self.assertLess(path_x[-1], start.x)

    def test_aim_trajectory_does_not_mutate_live_bucket_pegs(self):
        bucket = Bucket()
        bucket.update(1.0)
        original_positions = [
            (peg.pos.x, peg.pos.y) for peg in bucket.fakePegs
        ]
        original_phase = bucket.t
        calculation = TrajectoryCalculation(
            Vector(480, 200),
            Vector(480, 50),
            [],
            bucket.fakePegs.copy(),
            QuadtreePegs(Rectangle(480, 360, 480, 360), 0),
            1.0,
            depth=10,
            bucket=bucket,
        )

        self.assertTrue(calculation.advance(float("inf")))
        self.assertEqual(
            [(peg.pos.x, peg.pos.y) for peg in bucket.fakePegs],
            original_positions,
        )
        self.assertEqual(bucket.t, original_phase)

    def test_game_renderer_draws_gameplay_and_debug_overlays(self):
        game = game_module.Game()
        renderer = GameRenderer(self.screen)
        game.gameOver = True
        game.debugBallPrevPos = True
        game.ball.isAlive = True
        game.debugBallFramePaths = {
            game.ball: [(100, 100), (110, 90), (120, 100)]
        }
        game.quadtree = QuadtreePegs(Rectangle(480, 360, 480, 360), 0)

        with patch.dict(configs, {"DEBUG_MODE": True}):
            done = renderer.draw_world(
                game,
                self.screen,
                self.screen,
                [],
                False,
                False,
                False,
            )
            renderer.draw_game_over(game)
            renderer.draw_long_shot(game, Vector(0, 0))
            with patch.object(
                pygame.draw, "lines", wraps=pygame.draw.lines
            ) as draw_lines:
                renderer.draw_debug(
                    game,
                    FastClock(),
                    (480, 360),
                    done,
                    None,
                    [],
                    Rectangle(0, 0, 0, 0),
                    game.quadtree,
                    0,
                    0,
                )
                draw_lines.assert_any_call(
                    self.screen,
                    (255, 80, 40),
                    False,
                    [(100, 100), (110, 90), (120, 100)],
                    2,
                )

        self.assertFalse(done)

    def test_large_level_spawn_reveal_displays_static_layer_progressively(self):
        game = game_module.Game()
        renderer = GameRenderer(self.screen)
        static_image = pygame.Surface(
            (configs["WIDTH"], configs["HEIGHT"])
        )
        static_image.fill((200, 0, 0))
        completed_frame = pygame.Surface(
            (configs["WIDTH"], configs["HEIGHT"]),
            pygame.SRCALPHA,
        )
        completed_frame.fill((0, 0, 0, 255))
        animation_frame = pygame.Surface(
            (configs["WIDTH"], configs["HEIGHT"]),
            pygame.SRCALPHA,
        )
        animation_frame.fill((0, 200, 0, 255))

        renderer.draw_world(
            game,
            static_image,
            animation_frame,
            [],
            False,
            True,
            False,
            completed_frame,
            large_level_spawn_progress=0.5,
        )

        self.assertEqual(tuple(self.screen.get_at((20, 100))[:3]), (200, 0, 0))
        self.assertEqual(tuple(self.screen.get_at((20, 500))[:3]), (0, 0, 0))

    def test_level_editor_accepts_mouse_input_and_exits_from_pause_menu(self):
        frame_positions = iter(
            ((100, 250), (100, 250), (100, 250), (480, 640))
        )
        frame_events = iter(
            (
                [],
                [],
                [pygame.event.Event(pygame.KEYUP, key=pygame.K_ESCAPE)],
                [],
            )
        )
        button_states = iter(
            ((1, 0, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0))
        )

        with (
            patch.object(pygame.event, "get", side_effect=lambda: next(frame_events)),
            patch.object(pygame.mouse, "get_pos", side_effect=lambda: next(frame_positions)),
            patch.object(pygame.mouse, "get_pressed", side_effect=lambda: next(button_states)),
            patch.object(
                editor_module,
                "updateStaticImage",
                wraps=editor_module.updateStaticImage,
            ) as update_image,
            patch.object(
                editor_module,
                "createStaticImage",
                wraps=editor_module.createStaticImage,
            ) as create_image,
            patch.object(pygame.time, "Clock", FastClock),
        ):
            selection, pegs = levelEditor(
                self.screen, FastClock(), standalone=True
            )

        self.assertEqual(selection, "quit")
        self.assertEqual(pegs, [])
        self.assertGreaterEqual(update_image.call_count, 1)
        self.assertGreaterEqual(create_image.call_count, 2)

    def test_level_editor_saves_and_loads_with_keyboard_shortcuts(self):
        original_pegs = [Peg(80 + index * 24, 250) for index in range(30)]
        frame_positions = iter(((100, 250), (100, 250), (100, 250), (480, 640)))
        frame_events = iter(
            (
                [pygame.event.Event(pygame.KEYUP, key=pygame.K_s)],
                [pygame.event.Event(pygame.KEYUP, key=pygame.K_l)],
                [pygame.event.Event(pygame.KEYUP, key=pygame.K_ESCAPE)],
                [],
            )
        )
        button_states = iter(((0, 0, 0), (0, 0, 0), (0, 0, 0), (1, 0, 0)))

        with (
            patch.object(pygame.event, "get", side_effect=lambda: next(frame_events)),
            patch.object(
                pygame.mouse, "get_pos", side_effect=lambda: next(frame_positions)
            ),
            patch.object(
                pygame.mouse, "get_pressed", side_effect=lambda: next(button_states)
            ),
            patch.object(pygame.time, "Clock", FastClock),
            patch.object(editor_module, "saveData") as save_level,
            patch.object(
                editor_module,
                "loadLevelMenu",
                return_value=(original_pegs, original_pegs.copy(), 1, "Level 1"),
            ) as load_level,
        ):
            selection, _ = levelEditor(
                self.screen, FastClock(), standalone=True, pegs=original_pegs
            )

        self.assertEqual(selection, "quit")
        save_level.assert_called_once()
        load_level.assert_called_once_with(self.screen, configs["DEBUG_MODE"])

    def test_run_reaches_game_loop_launches_scores_and_survives_physics(self):
        original_load_level_menu = menu_controller_module.loadLevelMenu
        event_calls = 0
        game_frame = 0
        nested_main_menu = False
        game_over_seen = False
        game_over_restart_clicked = False
        score_seen = False
        tracked_games = []
        mouse_position = (480, 600)
        mouse_buttons = (0, 0, 0)
        event_trace = []
        selected_levels = []

        def scripted_events():
            nonlocal event_calls, game_frame, nested_main_menu
            nonlocal game_over_seen, game_over_restart_clicked, score_seen
            nonlocal mouse_position, mouse_buttons
            call_index = event_calls
            event_calls += 1

            if nested_main_menu:
                nested_main_menu = False
                mouse_position = (
                    configs["WIDTH"] // 2,
                    int(configs["HEIGHT"] / 2 - 12.5),
                )
                return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)]
            if call_index == 0:
                mouse_position = (
                    configs["WIDTH"] // 2,
                    int(configs["HEIGHT"] / 2 - 12.5),
                )
                event_trace.append(("main-menu", mouse_position))
                return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)]

            frame = game_frame
            game_frame += 1
            event_trace.append(("game", frame))
            mouse_buttons = (0, 0, 0)
            mouse_position = (480, configs["HEIGHT"] - 1)

            if tracked_games:
                current_game = tracked_games[-1]
                if current_game.score > 0 and not game_over_seen:
                    score_seen = True
                    current_game.gameOver = True
                    game_over_seen = True
                    return []
                if current_game.gameOver:
                    game_over_seen = True
                    if not game_over_restart_clicked:
                        game_over_restart_clicked = True
                        return [
                            pygame.event.Event(
                                pygame.MOUSEBUTTONDOWN, button=1
                            )
                        ]

            key_events = {
                0: pygame.K_3,
                1: pygame.K_4,
                2: pygame.K_5,
                3: pygame.K_6,
                4: pygame.K_8,
                5: pygame.K_9,
                6: pygame.K_x,
                7: pygame.K_p,
                8: pygame.K_2,
                9: pygame.K_2,
                10: pygame.K_4,
                11: pygame.K_7,
                12: pygame.K_7,
                13: pygame.K_0,
                14: pygame.K_0,
                15: pygame.K_t,
                16: pygame.K_t,
                17: pygame.K_m,
                18: pygame.K_m,
                19: pygame.K_n,
                20: pygame.K_n,
                21: pygame.K_v,
                22: pygame.K_v,
                23: pygame.K_f,
                24: pygame.K_f,
                25: pygame.K_1,
                26: pygame.K_1,
            }
            if frame in key_events:
                return [pygame.event.Event(pygame.KEYUP, key=key_events[frame])]
            if frame == 27:
                return [pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE)]
            if frame == 30:
                return [pygame.event.Event(pygame.KEYUP, key=pygame.K_l)]
            if frame == 35:
                nested_main_menu = True
                return [pygame.event.Event(pygame.KEYUP, key=pygame.K_z)]
            if frame == 40:
                return [pygame.event.Event(pygame.MOUSEWHEEL, y=1)]
            if frame == 110:
                return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)]
            if frame == 160:
                return [pygame.event.Event(pygame.KEYUP, key=pygame.K_2)]
            if frame == 161:
                mouse_position = (800, 300)
                mouse_buttons = (0, 0, 1)
                return []
            if frame == 162:
                return [pygame.event.Event(pygame.KEYUP, key=pygame.K_2)]
            if frame == 150:
                return [pygame.event.Event(pygame.KEYUP, key=pygame.K_ESCAPE)]
            if frame == 151:
                mouse_position = (
                    int(configs["WIDTH"] / 2 - 115),
                    int(configs["HEIGHT"] / 2 - 65),
                )
                mouse_buttons = (1, 0, 0)
                return []
            if frame == 200:
                return [pygame.event.Event(pygame.QUIT)]
            return []

        def add_test_peg(screen):
            levels = getLevelsList()
            pegs, original_pegs, orange_count, level_name = level_menu_module.loadLevel(
                levels[0]
            )
            level_name = f"Level {len(selected_levels) + 1}"
            selected_levels.append(level_name)
            target = Peg(configs["WIDTH"] / 2, configs["HEIGHT"] / 25 + 200)
            target.set_color("orange")
            pegs.append(target)
            original_pegs.append(target)
            return pegs, original_pegs, orange_count + 1, level_name

        class TrackingGame(game_module.Game):
            def __init__(self):
                super().__init__()
                tracked_games.append(self)

        # Keep the actual main menu and game loop; the level-menu test above
        # exercises its click path, while this run uses a deterministic test peg.
        menu_controller_module.loadLevelMenu = add_test_peg
        try:
            with (
                patch.object(pygame.event, "get", side_effect=scripted_events),
                patch.object(
                    pygame.mouse,
                    "get_pos",
                    side_effect=lambda: mouse_position,
                ),
                patch.object(
                    pygame.mouse,
                    "get_pressed",
                    side_effect=lambda: mouse_buttons,
                ),
                patch.object(pygame.mouse, "get_rel", return_value=(0, 0)),
                patch.object(pygame.joystick, "get_count", return_value=0),
                patch.object(pygame.display, "get_current_refresh_rate", return_value=60),
                patch.object(pygame.time, "Clock", FastClock),
                patch.object(game_module, "Game", TrackingGame),
                patch.object(time, "sleep", side_effect=lambda _seconds: None),
                patch("local.audio.playSoundPitch"),
                patch("local.userConfig.saveSettings"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                namespace = runpy.run_path("run.py", run_name="__main__")
        finally:
            menu_controller_module.loadLevelMenu = original_load_level_menu

        game = namespace["gameVars"]
        self.assertEqual(
            namespace["levelFileName"],
            "Level 3",
            msg=f"selected levels: {selected_levels}; event trace: {event_trace[:110]}",
        )
        self.assertEqual(selected_levels, ["Level 1", "Level 2", "Level 3"])
        self.assertTrue(
            score_seen,
            (
                "the test shot should score before game over; "
                f"game_over={game_over_seen}, clicked={game_over_restart_clicked}, "
                f"ball={game.ball.pos.x, game.ball.pos.y}, "
                f"velocity={game.ball.vel.x, game.ball.vel.y}, "
                f"alive={game.ball.isAlive}, frames={game_frame}"
            ),
        )
        self.assertTrue(game_over_seen, "the test shot should reach game over")
        self.assertTrue(game_over_restart_clicked)
        self.assertFalse(game.gameOver, "clicking after game over should reset the game")
        self.assertEqual(game.score, 0)
        self.assertEqual(game.ballsRemaining, 10)
        self.assertIn(game.ball, game.balls)
        self.assertFalse(game.gamePaused)
        self.assertLess(game.fineTuneAmount, 0)
        self.assertEqual(game.powerUpType, "multiball")
        self.assertFalse(game.quadtreeDebug)
        self.assertFalse(game.useQuadtree)
        self.assertTrue(game.physicsTimeDebug)
        self.assertTrue(game.speedHack)
        self.assertTrue(game.debugAutoRemovePegsTimer)
        self.assertTrue(game.zoomInOnBall)
        self.assertTrue(game.debugBallPrevPos)
        self.assertFalse(namespace["debugTrajectory"])
        self.assertFalse(game.cheats)
        self.assertFalse(configs["DEBUG_MODE"])
        self.assertFalse(configs["SOUND_ENABLED"])
        self.assertFalse(configs["MUSIC_ENABLED"])
        self.assertFalse(configs["VSYNC"])
        self.assertFalse(configs["FULLSCREEN"])
        self.assertEqual(game.timeScale, game.baseTimeScale)


if __name__ == "__main__":
    unittest.main()
