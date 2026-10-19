from time import perf_counter
from contextlib import nullcontext

import pygame

from local.peg import getScoreMultiplier
from local.misc import createStaticCircles
from local.performance import (
    DISPLAY_METRICS,
    PERFORMANCE_COLUMNS,
    PerformanceMetrics,
)
from local.resources import (
    backgroundImg,
    ballCountFont,
    ballImg,
    debugFont,
    infoFont,
    menuFont,
)
from local.userConfig import configs


class GameRenderer:
    PERFORMANCE_PANEL_REFRESH_SECONDS = 0.25
    PERFORMANCE_PANEL_SCALE = 0.75

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._background_size: tuple[int, int] | None = None
        self._scaled_background: pygame.Surface | None = None
        self._performance_panel_source: pygame.Surface | None = None
        self._performance_panel: pygame.Surface | None = None
        self._performance_panel_screen_size: tuple[int, int] | None = None
        self._performance_panel_updated_at = float("-inf")
        self._performance_panel_position: tuple[int, int] | None = None
        self._developer_panel_position: tuple[int, int] | None = None
        self._developer_panel_rect: pygame.Rect | None = None
        self._active_debug_panel_drag: str | None = None
        self._debug_panel_drag_offset: tuple[int, int] | None = None

    def _get_scaled_background(self) -> pygame.Surface:
        background_size = (configs["WIDTH"], configs["HEIGHT"])
        if self._background_size != background_size:
            self._scaled_background = pygame.transform.scale(
                backgroundImg, background_size
            )
            self._background_size = background_size
        return self._scaled_background

    def prepare_spawn_frame(self, completed_spawn_frame: pygame.Surface) -> None:
        completed_spawn_frame.blit(self._get_scaled_background(), (0, 0))

    def draw_world(
        self,
        game,
        static_image: pygame.Surface,
        animation_frame: pygame.Surface,
        trajectory: list,
        is_gravity_power_up_active: bool,
        new_game_animation_active: bool,
        peg_removal_animation_active: bool,
        completed_spawn_frame: pygame.Surface | None = None,
        performance: PerformanceMetrics | None = None,
        large_level_spawn_progress: float | None = None,
    ) -> bool:
        screen = self.screen
        if new_game_animation_active:
            with (
                performance.measure("static_peg_layer")
                if performance is not None
                else nullcontext()
            ):
                if completed_spawn_frame is not None:
                    screen.blit(completed_spawn_frame, (0, 0))
                else:
                    screen.blit(self._get_scaled_background(), (0, 0))
            with (
                performance.measure("animation_layer")
                if performance is not None
                else nullcontext()
            ):
                if large_level_spawn_progress is None:
                    screen.blit(animation_frame, (0, 0))
                else:
                    reveal_height = round(
                        configs["HEIGHT"]
                        * min(1.0, max(0.0, large_level_spawn_progress))
                    )
                    if reveal_height:
                        screen.blit(
                            static_image,
                            (0, 0),
                            pygame.Rect(
                                0,
                                0,
                                configs["WIDTH"],
                                reveal_height,
                            ),
                        )
        else:
            with (
                performance.measure("static_peg_layer")
                if performance is not None
                else nullcontext()
            ):
                screen.blit(static_image, (0, 0))
                from local.misc import drawMovingPegs
                drawMovingPegs(
                    screen,
                    getattr(game.quadtree, "moving_pegs", ()),
                    game.interpolationAlpha,
                )
            if peg_removal_animation_active:
                with (
                    performance.measure("animation_layer")
                    if performance is not None
                    else nullcontext()
                ):
                    screen.blit(animation_frame, (0, 0))

        alpha = game.interpolationAlpha
        bucket_x = game.bucket.prevPos.x + (
            game.bucket.pos.x - game.bucket.prevPos.x
        ) * alpha
        bucket_y = game.bucket.prevPos.y + (
            game.bucket.pos.y - game.bucket.prevPos.y
        ) * alpha
        with (
            performance.measure("bucket_render")
            if performance is not None
            else nullcontext()
        ):
            bucket_back, bucket_front = game.bucket.getImage(
                game.powerUpType, game.powerUpActive
            )
            screen.blit(bucket_back, (bucket_x, bucket_y))
        if (
            not game.gameOver
            and not new_game_animation_active
            and not peg_removal_animation_active
        ):
            with (
                performance.measure("ball_render")
                if performance is not None
                else nullcontext()
            ):
                for ball in game.balls:
                    ball_x = ball.prevPos.x + (ball.pos.x - ball.prevPos.x) * alpha
                    ball_y = ball.prevPos.y + (ball.pos.y - ball.prevPos.y) * alpha
                    screen.blit(
                        ballImg,
                        (
                            ball_x - ballImg.get_width() / 2,
                            ball_y - ballImg.get_height() / 2,
                        ),
                    )
        with (
            performance.measure("bucket_render")
            if performance is not None
            else nullcontext()
        ):
            screen.blit(bucket_front, (bucket_x, bucket_y))

        done = not any(ball.isAlive for ball in game.balls)
        if (
            done
            and not game.gameOver
            and not game.gamePaused
            and not new_game_animation_active
            and not peg_removal_animation_active
        ):
            with (
                performance.measure("trajectory_render")
                if performance is not None
                else nullcontext()
            ):
                for ball in trajectory:
                    if not configs["USE_OLD_TRAJECTORY"]:
                        pygame.draw.line(
                            screen,
                            (10, 70, 163),
                            (ball.prevPos.x, ball.prevPos.y),
                            (ball.pos.x, ball.pos.y),
                            6,
                        )
                    else:
                        self._draw_circle(ball.pos.x, ball.pos.y, 4, (10, 70, 163))

        with (
            performance.measure("zoom_render")
            if performance is not None
            else nullcontext()
        ):
            self._draw_zoomed_world(game)
        with (
            performance.measure("scoreboard_render")
            if performance is not None
            else nullcontext()
        ):
            self._draw_scoreboard(game, is_gravity_power_up_active)
        return done

    def draw_game_over(self, game) -> None:
        if not game.gameOver:
            return
        text = menuFont.render("Game Over", False, (255, 255, 255))
        self.screen.blit(
            text,
            (configs["WIDTH"] / 2 - text.get_width() / 2, configs["HEIGHT"] / 4),
        )
        if game.ballsRemaining >= 0 and game.orangeCount < 1:
            score = self._format_score(game.score)
            score_text = menuFont.render(score, False, (20, 60, 255))
            self.screen.blit(
                score_text,
                (
                    configs["WIDTH"] / 2 - score_text.get_width() / 2,
                    configs["HEIGHT"] / 3 + 50,
                ),
            )
        else:
            try_again = menuFont.render("Try Again", False, (255, 60, 20))
            self.screen.blit(
                try_again,
                (
                    configs["WIDTH"] / 2 - try_again.get_width() / 2,
                    configs["HEIGHT"] / 2.2,
                ),
            )

    def draw_debug(
        self,
        game,
        clock,
        mouse_position: tuple[int, int],
        done: bool,
        joystick,
        nearby_pegs: list,
        query_rect,
        quadtree,
        total_time: float,
        draw_time: float,
    ) -> None:
        screen = self.screen
        mouse_x, mouse_y = mouse_position
        if configs["DEBUG_MODE"] or game.physicsTimeDebug or game.cheats:
            self._draw_developer_panel(
                game,
                clock,
                total_time,
                draw_time,
                quadtree,
                joystick,
            )
        if configs["DEBUG_MODE"]:
            if not done and game.powerUpType == "zenball" and game.bestTrajectory:
                if game.debugStaticImage is None:
                    game.debugStaticImage = createStaticCircles(
                        game.bestTrajectory,
                        game.bestTrajectoryBucketPoints,
                    )
                screen.blit(game.debugStaticImage, (0, 0))
            else:
                game.debugStaticImage = None
                game.bestTrajectory = []
                game.bestTrajectoryBucketPoints = None

            if not game.ball.isAlive and len(game.balls) < 2:
                self._draw_line(
                    game.ball.pos.x, game.ball.pos.y, mouse_x, mouse_y
                )
            for fake_peg in game.bucket.fakePegs.copy():
                self._draw_circle(
                    fake_peg.pos.x, fake_peg.pos.y, fake_peg.radius, (255, 0, 0)
                )

            if game.autoRemovePegs and game.debugAutoRemovePegsTimer:
                for peg in game.pegs:
                    time_remaining = (
                        peg.ballStuckTimer.timeRemaining
                        if peg.ballStuckTimer.timeRemaining > 0
                        else game.autoRemovePegsTimerValue
                    )
                    color = (
                        (255, 20, 10)
                        if peg.ballStuckTimer.timeRemaining > 0
                        else (255, 255, 255)
                    )
                    timer_text = debugFont.render(
                        str(round(time_remaining, 3)), False, color
                    )
                    screen.blit(timer_text, (peg.pos.x, peg.pos.y))

            if game.quadtreeDebug:
                screen.blit(game.quadtreeStaticScreen, (0, 0))
                if game.useQuadtree:
                    for peg in nearby_pegs:
                        self._draw_circle(
                            peg.pos.x, peg.pos.y, peg.radius, (255, 0, 0)
                        )
                pygame.draw.rect(
                    screen,
                    (0, 255, 0),
                    (
                        query_rect.x - game.queryRectSize,
                        query_rect.y - game.queryRectSize,
                        game.queryRectSize * 2,
                        game.queryRectSize * 2,
                    ),
                    2,
                )
            if game.debugBallPrevPos:
                for ball, path in game.debugBallFramePaths.items():
                    if len(path) > 1:
                        points = [
                            (round(x), round(y))
                            for x, y in path
                        ]
                        pygame.draw.lines(
                            screen, (255, 80, 40), False, points, 2
                        )
                        self._draw_circle(
                            path[0][0], path[0][1], 4, (255, 255, 0)
                        )
                        self._draw_circle(
                            path[-1][0], path[-1][1], 4, (0, 255, 0)
                        )

                for ball in game.balls:
                    if not ball.isAlive:
                        continue
                    self._draw_circle(ball.pos.x, ball.pos.y, 5, (0, 255, 0))
                    pygame.draw.line(
                        screen,
                        (255, 0, 255),
                        (ball.prevPos.x, ball.prevPos.y),
                        (
                            ball.prevPos.x + ball.prevVel.x * 10,
                            ball.prevPos.y + ball.prevVel.y * 10,
                        ),
                        2,
                    )
                    pygame.draw.line(
                        screen,
                        (0, 255, 255),
                        (ball.pos.x, ball.pos.y),
                        (
                            ball.pos.x + ball.vel.x * 10,
                            ball.pos.y + ball.vel.y * 10,
                        ),
                        2,
                    )

    def _draw_developer_panel(
        self,
        game,
        clock,
        total_time: float,
        draw_time: float,
        quadtree,
        joystick,
    ) -> None:
        panel_width = min(320, configs["WIDTH"] - 24)
        row_height = 19
        frame_ms = clock.get_rawtime()
        frame_color = (255, 92, 92) if frame_ms >= 16.7 else (100, 230, 150)
        physics_percent = (
            game.physicsTime / (clock.get_time() / 1000)
            if clock.get_time() > 0
            else 0.0
        )
        rows = (
            (
                "PERFORMANCE",
                (
                    (f"FPS  {clock.get_fps():.1f}", (235, 240, 250)),
                    (f"Frame  {frame_ms:.1f} ms", frame_color),
                    (f"Physics  {game.physicsTime * 1000:.2f} ms  ({physics_percent * 100:.0f}%)", (220, 230, 242)),
                    (f"Draw  {draw_time * 1000:.2f} ms", (220, 230, 242)),
                    (f"Total  {total_time * 1000:.2f} ms", (220, 230, 242)),
                    (f"Steps  {game.physicsStepsThisFrame}/{game.maxPhysicsStepsPerFrame}  |  dt {game.dt:.2f}", (220, 230, 242)),
                    (f"Dropped sim  {game.physicsDroppedTimeThisFrame:.2f}", (220, 230, 242)),
                ),
            ),
            (
                "GAME STATE",
                (
                    (f"Pegs  {len(game.pegs)}  |  orange {game.orangeCount}", (220, 230, 242)),
                    (f"Balls  {len(game.balls)}  |  velocity {game.ball.vel.getMag():.2f}", (220, 230, 242)),
                    (f"Quadtree  {'ON' if game.useQuadtree else 'OFF'}  |  capacity {quadtree.capacity}", (220, 230, 242)),
                    (f"Speed hack  {'ON' if game.speedHack else 'OFF'}", (220, 230, 242)),
                ),
            ),
        )
        game_state_values = list(rows[1][1])
        if game.controllerInput and joystick is not None:
            game_state_values.append(
                (f"Controller  {joystick.get_name()}", (220, 230, 242))
            )
        rows = (rows[0], ("GAME STATE", tuple(game_state_values)))
        content_rows = sum(1 + len(values) for _, values in rows)
        panel_height = 31 + row_height * content_rows + 8
        panel = pygame.Surface(
            (panel_width, panel_height),
            pygame.SRCALPHA,
        )
        panel.fill((9, 15, 28, 222))
        pygame.draw.rect(
            panel,
            (75, 105, 145),
            panel.get_rect(),
            1,
            border_radius=8,
        )
        title = debugFont.render(
            "DEVELOPER  |  LIVE",
            False,
            (130, 205, 255),
        )
        panel.blit(title, (10, 8))
        y = 31
        for section, values in rows:
            section_text = debugFont.render(section, False, (170, 185, 210))
            panel.blit(section_text, (10, y))
            y += row_height
            for text, color in values:
                rendered = debugFont.render(text, False, color)
                panel.blit(rendered, (12, y))
                y += row_height

        if game.cheats:
            cheats = debugFont.render(
                "CHEATS ENABLED",
                False,
                (255, 92, 92),
            )
            panel.blit(cheats, (panel_width - cheats.get_width() - 10, 8))

        panel_rect = panel.get_rect()
        if self._developer_panel_position is None:
            self._developer_panel_position = (
                configs["WIDTH"] - panel_width - 12,
                100,
            )
        self._developer_panel_position = self._clamp_panel_position(
            self._developer_panel_position,
            panel_rect.size,
        )
        self._developer_panel_rect = panel_rect.copy()
        self._developer_panel_rect.topleft = self._developer_panel_position
        self.screen.blit(panel, self._developer_panel_position)

    def draw_performance_metrics(
        self, performance: PerformanceMetrics
    ) -> None:
        now = perf_counter()
        panel_width = min(configs["WIDTH"] - 20, 980)
        if (
            self._performance_panel is None
            or self._performance_panel_screen_size
            != (configs["WIDTH"], configs["HEIGHT"])
            or now - self._performance_panel_updated_at
            >= self.PERFORMANCE_PANEL_REFRESH_SECONDS
        ):
            self._update_performance_panel(performance, panel_width)
            self._performance_panel_updated_at = now

        panel_rect = self._performance_panel.get_rect()
        if self._performance_panel_position is None:
            self._performance_panel_position = (
                10,
                configs["HEIGHT"] - panel_rect.height - 10,
            )
        self._performance_panel_position = self._clamp_panel_position(
            self._performance_panel_position,
            panel_rect.size,
        )
        self.screen.blit(
            self._performance_panel,
            self._performance_panel_position,
        )

    def handle_debug_panel_event(
        self,
        event: pygame.event.Event,
        performance_enabled: bool = True,
        developer_enabled: bool = True,
    ) -> bool:
        panels: dict[str, tuple[pygame.Rect, tuple[int, int], bool]] = {}
        if (
            self._performance_panel is not None
            and self._performance_panel_position is not None
        ):
            panels["performance"] = (
                self._performance_panel.get_rect(
                    topleft=self._performance_panel_position
                ),
                self._performance_panel.get_size(),
                performance_enabled,
            )
        if (
            self._developer_panel_rect is not None
            and self._developer_panel_position is not None
        ):
            panels["developer"] = (
                self._developer_panel_rect,
                self._developer_panel_rect.size,
                developer_enabled,
            )

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name in ("performance", "developer"):
                panel = panels.get(name)
                if panel is not None and panel[2] and panel[0].collidepoint(event.pos):
                    self._active_debug_panel_drag = name
                    self._debug_panel_drag_offset = (
                        event.pos[0] - panel[0].x,
                        event.pos[1] - panel[0].y,
                    )
                    return True

        if (
            self._active_debug_panel_drag is None
            or self._debug_panel_drag_offset is None
        ):
            return False

        active_panel = panels.get(self._active_debug_panel_drag)
        if active_panel is None:
            return event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP)

        if event.type == pygame.MOUSEMOTION:
            position = self._clamp_panel_position(
                (
                    event.pos[0] - self._debug_panel_drag_offset[0],
                    event.pos[1] - self._debug_panel_drag_offset[1],
                ),
                active_panel[1],
            )
            if self._active_debug_panel_drag == "performance":
                self._performance_panel_position = position
            else:
                self._developer_panel_position = position
                self._developer_panel_rect.topleft = position
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._active_debug_panel_drag = None
            self._debug_panel_drag_offset = None
            return True

        return False

    def handle_performance_event(
        self,
        event: pygame.event.Event,
        enabled: bool = True,
    ) -> bool:
        return self.handle_debug_panel_event(
            event,
            performance_enabled=enabled,
            developer_enabled=False,
        )

    @staticmethod
    def _clamp_panel_position(
        position: tuple[int, int],
        panel_size: tuple[int, int],
    ) -> tuple[int, int]:
        max_x = max(0, configs["WIDTH"] - panel_size[0])
        max_y = max(0, configs["HEIGHT"] - panel_size[1])
        return (
            min(max(0, position[0]), max_x),
            min(max(0, position[1]), max_y),
        )

    def _update_performance_panel(
        self,
        performance: PerformanceMetrics,
        panel_width: int,
    ) -> None:
        margin = 10
        column_width = (panel_width - margin * 3) // 2
        row_height = 19
        max_rows = max(len(metrics) for _, metrics in PERFORMANCE_COLUMNS)
        panel_height = 68 + max_rows * row_height + margin
        scale = min(
            self.PERFORMANCE_PANEL_SCALE,
            (configs["HEIGHT"] * 0.45) / panel_height,
        )
        display_size = (
            round(panel_width * scale),
            round(panel_height * scale),
        )
        panel_size = (panel_width, panel_height)
        if (
            self._performance_panel_source is None
            or self._performance_panel_source.get_size() != panel_size
        ):
            self._performance_panel_source = pygame.Surface(
                panel_size, pygame.SRCALPHA
            )
        panel = self._performance_panel_source
        panel.fill((9, 15, 28, 232))
        pygame.draw.rect(panel, (100, 125, 160), panel.get_rect(), 1)

        title = debugFont.render(
            "PERFORMANCE  |  latest / p95 / max ms  |  setup rows show last call",
            False,
            (240, 245, 255),
        )
        panel.blit(title, (margin, 6))

        labels = dict(DISPLAY_METRICS)
        header_color = (155, 175, 205)
        for column_index, (section, metric_names) in enumerate(PERFORMANCE_COLUMNS):
            column_x = margin + column_index * (column_width + margin)
            section_text = debugFont.render(section, False, (120, 205, 255))
            panel.blit(section_text, (column_x, 29))
            values_header = debugFont.render(
                "NOW   P95   MAX ms",
                False,
                header_color,
            )
            panel.blit(
                values_header,
                (
                    column_x + column_width - values_header.get_width(),
                    29,
                ),
            )

            for row, metric_name in enumerate(metric_names):
                latest, p95, maximum = performance.summary(metric_name)
                severity = performance.severity(metric_name, p95)
                color = {
                    "normal": (220, 230, 242),
                    "yellow": (255, 215, 80),
                    "red": (255, 92, 92),
                }[severity]
                y = 49 + row * row_height
                label = debugFont.render(labels[metric_name], False, color)
                values = debugFont.render(
                    f"{latest:5.1f} {p95:5.1f} {maximum:5.1f}",
                    False,
                    color,
                )
                panel.blit(label, (column_x, y))
                panel.blit(
                    values,
                    (
                        column_x + column_width - values.get_width(),
                        y,
                    ),
                )

        legend = debugFont.render(
            "Yellow: elevated   Red: high (based on P95)",
            False,
            (255, 215, 80),
        )
        panel.blit(legend, (margin, panel_height - 18))
        self._performance_panel = pygame.transform.smoothscale(
            panel,
            display_size,
        )
        self._performance_panel_screen_size = (
            configs["WIDTH"],
            configs["HEIGHT"],
        )

    def _draw_zoomed_world(self, game) -> None:
        if game.zoomInOnBall:
            game.zoom = min(game.zoom + 0.005, 1.8)
            self._blit_zoomed_world(game)
        elif game.zoom > 1.0:
            zoom_step = (
                0.0025
                if game.alreadyPlayedOdeToJoy
                or game.timeScale == game.closeCallTimeScale
                else 0.005
            )
            game.zoom -= zoom_step
            self._blit_zoomed_world(game)
        else:
            game.zoom = 1.0

    def _blit_zoomed_world(self, game) -> None:
        zoomed_screen = pygame.transform.smoothscale(
            self.screen,
            (
                int(configs["WIDTH"] * game.zoom),
                int(configs["HEIGHT"] * game.zoom),
            ),
        )
        target = None
        if game.orangeCount < 2:
            for peg in game.pegs:
                if peg.color == "orange" and (
                    not game.zoomInOnBall or not peg.isHit
                ):
                    target = peg.pos
                    break
        if target is None:
            target = game.ball.pos

        position = (
            zoomed_screen.get_width() / game.zoom / 2 - target.x * game.zoom,
            zoomed_screen.get_height() / game.zoom / 2 - target.y * game.zoom,
        )
        x = min(0, max(configs["WIDTH"] - zoomed_screen.get_width(), position[0]))
        y = min(0, max(configs["HEIGHT"] - zoomed_screen.get_height(), position[1]))
        self.screen.blit(zoomed_screen, (x, y))

    def _draw_scoreboard(self, game, is_gravity_power_up_active: bool) -> None:
        if game.gameOver:
            return
        panel_width = min(configs["WIDTH"] - 32, 820)
        panel_height = 76
        panel_x = (configs["WIDTH"] - panel_width) // 2
        panel = pygame.Surface(
            (panel_width, panel_height),
            pygame.SRCALPHA,
        )
        panel.fill((9, 15, 28, 218))
        pygame.draw.rect(
            panel,
            (67, 91, 130),
            panel.get_rect(),
            1,
            border_radius=10,
        )

        blocks = (
            (panel_width * 0.04, "SCORE", self._format_score(game.score), (255, 255, 255)),
            (panel_width * 0.30, "BALLS LEFT", str(game.ballsRemaining), (210, 225, 245)),
            (panel_width * 0.48, "ORANGE LEFT", str(game.orangeCount), (255, 175, 65)),
            (
                panel_width * 0.67,
                "MULTIPLIER",
                "x" + str(getScoreMultiplier(game.orangeCount, game.pegsHit)),
                (255, 220, 110),
            ),
        )
        for x, label, value, color in blocks:
            label_text = debugFont.render(label, False, (155, 175, 205))
            value_font = ballCountFont if label == "SCORE" else infoFont
            value_text = value_font.render(value, False, color)
            panel.blit(label_text, (round(x), 9))
            panel.blit(value_text, (round(x), 31))

        power_up_color = (50, 255, 20) if game.powerUpActive else (50, 170, 20)
        power_up_count = (
            str(round(game.noGravityPowerUpTimer.timeRemaining, 1))
            if is_gravity_power_up_active
            else str(game.powerUpCount)
        )
        power_up = infoFont.render(
            game.powerUpType.upper() + "  " + power_up_count,
            False,
            power_up_color,
        )
        power_x = panel_width - power_up.get_width() - 18
        power_label = debugFont.render("POWER-UP", False, (155, 175, 205))
        panel.blit(
            power_label,
            (power_x, 9),
        )
        panel.blit(power_up, (power_x, 34))
        self.screen.blit(panel, (panel_x, 12))

    def draw_long_shot(self, game, long_shot_pos) -> None:
        timer = game.longShotTextTimer
        timer.update()
        if timer.isTriggered:
            game.longShotBonus = False
            timer.cancelTimer()
        if game.longShotBonus and not timer.isActive:
            timer.setTimer(1.25)
        if game.longShotBonus and not timer.isTriggered:
            points = infoFont.render("25,000", False, (255, 110, 0))
            self.screen.blit(points, (long_shot_pos.x - 28, long_shot_pos.y + 11))
            label = infoFont.render("Long Shot!", False, (255, 110, 0))
            self.screen.blit(label, (long_shot_pos.x - 35, long_shot_pos.y - 20))

    @staticmethod
    def _format_score(score: int) -> str:
        return f"{score:,}"

    def _draw_circle(self, x, y, radius=5, color=(255, 255, 255)) -> None:
        pygame.draw.circle(self.screen, color, [x, y], radius)

    def _draw_line(self, x1, y1, x2, y2) -> None:
        pygame.draw.line(self.screen, (255, 0, 0), [x1, y1], [x2, y2])
