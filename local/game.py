from collections.abc import Callable
from heapq import heappush, heapreplace
from time import perf_counter

from local.config import (
    LAUNCH_FORCE,
    autoRemovePegs,
    autoRemovePegsTimerValue,
    baseTimeScale,
    cheats,
    closeCallTimeScale,
    debugAutoRemovePegsTimer,
    longShotDistance,
    noGravityTimeLength,
    odeToJoyTimeScale,
    queryRectSize,
    speedHack,
    trajectoryDepth,
)
from local.userConfig import configs
from local.bucket import Bucket
from local.ball import Ball
from local.peg import Peg, getScoreMultiplier
from local.vectors import Vector, subVectors
from local.triggerEvents import TimedEvent
from local.quadtree import QuadtreePegs, Rectangle
import pygame

PEG_REMOVAL_PROXIMITY_MULTIPLIER = 1.5
PEG_PATH_REMOVAL_DISTANCE_MULTIPLIER = 4.0
PEG_PATH_REMOVAL_WIDTH_MULTIPLIER = 1.0
MAX_ADDITIONAL_PATH_PEG_REMOVALS = 8


class Game:
    def __init__(self):
        self.powerUpType = "spooky"
        self.powerUpActive = False
        self.powerUpCount = 0
        self.pitch = 1.0
        self.pitchRaiseCount = 0
        self.ballsRemaining = 10
        self.orangeCount = 0
        self.originPegs: list[Peg] = []
        self.LAUNCH_FORCE = LAUNCH_FORCE
        self.autoRemovePegs = autoRemovePegs
        self.autoRemovePegsTimerValue = autoRemovePegsTimerValue
        self.baseTimeScale = baseTimeScale
        self.cheats = cheats
        self.closeCallTimeScale = closeCallTimeScale
        self.debugAutoRemovePegsTimer = debugAutoRemovePegsTimer
        self.longShotDistance = longShotDistance
        self.noGravityTimeLength = noGravityTimeLength
        self.odeToJoyTimeScale = odeToJoyTimeScale
        self.queryRectSize = queryRectSize
        self.speedHack = speedHack
        self.trajectoryDepth = trajectoryDepth
        self.shouldClear = False
        self.previousAim = Vector(0, 1)
        self.balls: list[Ball]
        self.balls = []
        #self.balls.append(Ball(configs["WIDTH"]/2, configs["HEIGHT"]/25))
        self.balls.append(Ball(configs["WIDTH"]/2, configs["HEIGHT"]/25))
        self.ball = self.balls[0]

        # some extra global variable initialization stuff

        self.bucket = Bucket()
        self.pointsEarned = []
        self.score = 0
        self.drawTrajectory = False

        self.done = False
        self.pegsHit = 0

        self.fineTuneAmount = 0

        self.trajectory = []
        self.launchAim = Vector(0, 0)

        self.debugCollision = False
        self.gamePaused = False
        self.gameOver = False
        self.alreadyPlayedOdeToJoy = False
        self.closeBall = None
        self.longShotBonus = False
        self.longShotPos = Vector(0, 0)
        self.debugTrajectory = False
        self.firstSpookyHit = False
        self.bestTrajectory = []
        self.bestTrajectoryBucketPoints = None
        self.controllerInput = False
        #inputAim = Vector(configs["WIDTH"]/2, (configs["HEIGHT"]/25)+50)
        self.inputAim = Vector(configs["WIDTH"]/2, (configs["HEIGHT"]/25)+50)
        self.gamePadFineTuneAmount = 0
        self.debugBallPrevPos = False
        self.debugBallFramePaths: dict[Ball, list[tuple[float, float]]] = {}

        self.longShotTextTimer = TimedEvent()

        self.debugStaticImage: pygame.Surface = None
        self.gameRunning = True

        self.zoomInOnBall = False
        self.zoom = 1.0
        self.noGravityPowerUpTimer = TimedEvent()
        self.noGravityPowerUpTimer.setTimer(0.1)
        self.physicsTimeDebug = False
        self.totalTime = 0
        self.physicsTime = 0
        self.drawTime = 0
        self.updateTime = 0
        self.quadtreeBuildTime = 0.0
        self.pegStateResetTime = 0.0
        self.quadtreeDebug = False
        self.useQuadtree = True
        # transparent surface for the quadtree
        self.quadtreeStaticScreen = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA)
        self.dt = 1
        self.fixedPhysicsStep = 1.0
        self.maxPhysicsStepsPerFrame = 8
        self.physicsAccumulator = 0.0
        self.interpolationAlpha = 0.0
        self.frameDt = 0.0
        self.physicsStepsThisFrame = 0
        self.physicsDroppedTime = 0.0
        self.physicsDroppedTimeThisFrame = 0.0
        self.pegs: list[Peg] = []
        self.pegsWithActiveStuckTimers: set[Peg] = set()
        self.timeScale = baseTimeScale
        self.staticImage: pygame.Surface | None = None
        self.boundary: Rectangle | None = None
        self.quadtree: QuadtreePegs | None = None

    def setFrameTime(self, elapsed: float) -> None:
        self.frameDt = min(max(elapsed, 0.0), 50.0) * self.timeScale

    def accumulateFrameTime(self) -> None:
        self.physicsAccumulator += self.frameDt
        self.interpolationAlpha = min(
            self.physicsAccumulator / self.fixedPhysicsStep, 1.0
        )

    def consumePhysicsStep(self) -> None:
        self.physicsAccumulator = max(
            0.0, self.physicsAccumulator - self.fixedPhysicsStep
        )
        self.physicsStepsThisFrame += 1
        self.interpolationAlpha = min(
            self.physicsAccumulator / self.fixedPhysicsStep, 1.0
        )

    def beginPhysicsFrame(self) -> None:
        self.physicsStepsThisFrame = 0
        self.physicsDroppedTimeThisFrame = 0.0
        self.debugBallFramePaths = {
            ball: [(ball.pos.x, ball.pos.y)]
            for ball in self.balls
            if ball.isAlive
        }

    def finishPhysicsFrame(self) -> None:
        pending_steps = int(
            (self.physicsAccumulator + 1e-9) / self.fixedPhysicsStep
        )
        self.physicsDroppedTimeThisFrame = pending_steps * self.fixedPhysicsStep
        self.physicsDroppedTime += self.physicsDroppedTimeThisFrame
        self.physicsAccumulator = max(
            0.0,
            self.physicsAccumulator - self.physicsDroppedTimeThisFrame,
        )
        self.interpolationAlpha = min(
            self.physicsAccumulator / self.fixedPhysicsStep, 1.0
        )

    def updateBucketDuringZenballSearch(self) -> None:
        self.bucket.update(
            self.frameDt,
            self.powerUpType,
            self.powerUpActive,
        )
        self.interpolationAlpha = 1.0

    def recordBallPhysicsPosition(self, ball: Ball) -> None:
        path = self.debugBallFramePaths.setdefault(
            ball, [(ball.pos.x, ball.pos.y)]
        )
        position = (ball.pos.x, ball.pos.y)
        if position != path[-1]:
            path.append(position)

    def validateActiveStuckTimers(self) -> None:
        for peg in tuple(self.pegsWithActiveStuckTimers):
            peg.validate_ball_stuck_timer()
            if not peg.ballStuckTimer.isActive:
                self.pegsWithActiveStuckTimers.discard(peg)

    def remove_peg_cluster(
        self,
        peg: Peg,
        quadtree: QuadtreePegs,
        direction: Vector | None = None,
    ) -> list[Peg]:
        if peg not in self.pegs:
            return []

        proximity = peg.radius * PEG_REMOVAL_PROXIMITY_MULTIPLIER
        proximity_squared = proximity * proximity
        removed_set = {peg}
        travel_direction = None
        path_candidates: list[tuple[float, int, Peg]] = []
        if direction is not None and direction.getMag() > 0:
            travel_direction = direction.copy()
            travel_direction.normalize()
        max_distance = peg.radius * PEG_PATH_REMOVAL_DISTANCE_MULTIPLIER
        corridor_width_squared = (
            peg.radius * PEG_PATH_REMOVAL_WIDTH_MULTIPLIER
        ) ** 2

        for index, candidate in enumerate(self.pegs):
            if candidate is peg:
                continue
            dx = candidate.pos.x - peg.pos.x
            dy = candidate.pos.y - peg.pos.y
            distance_squared = dx * dx + dy * dy
            if distance_squared <= proximity_squared:
                removed_set.add(candidate)
                continue
            if travel_direction is not None:
                along_path = (
                    dx * travel_direction.x + dy * travel_direction.y
                )
                if 0 < along_path <= max_distance:
                    perpendicular_squared = max(
                        0.0,
                        distance_squared - along_path * along_path,
                    )
                    if perpendicular_squared <= corridor_width_squared:
                        heap_item = (-along_path, index, candidate)
                        if len(path_candidates) < MAX_ADDITIONAL_PATH_PEG_REMOVALS:
                            heappush(path_candidates, heap_item)
                        elif along_path < -path_candidates[0][0]:
                            heapreplace(path_candidates, heap_item)

        removed_set.update(
            candidate
            for _, _, candidate in path_candidates
        )

        removed = [candidate for candidate in self.pegs if candidate in removed_set]
        self.pegs[:] = [
            candidate
            for candidate in self.pegs
            if candidate not in removed_set
        ]
        for candidate in removed:
            quadtree.remove(candidate)
            self.pegsWithActiveStuckTimers.discard(candidate)
            candidate.cancel_ball_stuck_timer()
            if (
                candidate is not peg
                and not candidate.isHit
            ):
                if candidate.color == "orange":
                    self.orangeCount -= 1
                self.score += candidate.points * getScoreMultiplier(
                    self.orangeCount,
                    self.pegsHit,
                )
                candidate.isHit = True
                candidate.update_color()
        return removed

    def resetRound(
        self,
        origin_pegs: list[Peg],
        create_peg_colors: Callable[[list[Peg]], list[Peg]],
        create_static_image: Callable[..., pygame.Surface],
        play_new_song: Callable[[], None],
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> tuple[pygame.Surface, QuadtreePegs]:
        if self.balls:
            self.ball = self.balls[0]
            self.ball.originX = configs["WIDTH"] / 2
            self.ball.originY = configs["HEIGHT"] / 25
            self.balls[:] = [self.ball]
        else:
            self.ball = Ball(configs["WIDTH"] / 2, configs["HEIGHT"] / 25)
            self.balls.append(self.ball)
        self.ball.reset()

        self.pitch = 1.0
        self.pitchRaiseCount = 0
        self.powerUpActive = False
        self.powerUpCount = 0
        self.originPegs = origin_pegs.copy()
        self.pegsWithActiveStuckTimers.clear()
        self.pegs.clear()
        self.pegs = self.originPegs.copy()
        peg_state_reset_start = perf_counter()
        total_pegs = len(self.pegs)
        report_interval = max(1, total_pegs // 100)
        if progress_callback is not None:
            progress_callback(0.0, "Preparing peg data")
        for index, peg in enumerate(self.pegs, start=1):
            peg.reset()
            if (
                progress_callback is not None
                and (index % report_interval == 0 or index == total_pegs)
            ):
                progress_callback(
                    0.15 * index / total_pegs,
                    "Preparing peg data",
                )
        self.pegs = create_peg_colors(self.pegs)
        orange_count = 0
        for index, peg in enumerate(self.pegs, start=1):
            orange_count += peg.color == "orange"
            if (
                progress_callback is not None
                and (index % report_interval == 0 or index == total_pegs)
            ):
                progress_callback(
                    0.15 + 0.1 * index / total_pegs,
                    "Counting orange pegs",
                )
        self.orangeCount = orange_count
        self.pegStateResetTime = perf_counter() - peg_state_reset_start
        self.score = 0
        self.ballsRemaining = 10
        self.pegsHit = 0
        self.bucket.reset()
        self.gameOver = False
        self.shouldClear = False
        self.alreadyPlayedOdeToJoy = False
        self.timeScale = self.baseTimeScale
        self.longShotBonus = False
        self.physicsAccumulator = 0.0
        self.interpolationAlpha = 0.0
        self.frameDt = 0.0

        play_new_song()
        if progress_callback is None:
            static_image = create_static_image(self.pegs)
        else:
            progress_callback(0.25, "Rendering level...")
            static_image = create_static_image(
                self.pegs,
                progress_callback=lambda progress, status: progress_callback(
                    0.25 + 0.55 * progress,
                    status,
                ),
            )
        self.staticImage = static_image
        boundary = Rectangle(
            configs["WIDTH"] / 2,
            configs["HEIGHT"] / 2,
            configs["WIDTH"] / 2,
            configs["HEIGHT"] / 2,
        )
        self.boundary = boundary
        quadtree = QuadtreePegs(boundary, len(self.pegs))
        self.quadtree = quadtree
        quadtree_build_start = perf_counter()
        if progress_callback is None:
            quadtree.insert_many(self.pegs)
        else:
            quadtree.insert_many(
                self.pegs,
                progress_callback=lambda progress, status: progress_callback(
                    0.8 + 0.2 * progress,
                    status,
                ),
            )
        self.quadtreeBuildTime = perf_counter() - quadtree_build_start
        return static_image, quadtree

    def launchBall(self, aim: Vector) -> None:
        launch_force = subVectors(aim, self.ball.pos)
        launch_force.setMag(self.LAUNCH_FORCE)
        self.ball.applyForce(launch_force)
        self.ball.isLaunch = False
        self.shouldClear = True

    
    def changePowerUp(self) -> None:
        if self.powerUpType == "spooky":
            self.powerUpType = "multiball"
        elif self.powerUpType == "multiball":
            self.powerUpType = "zenball"
        elif self.powerUpType == "zenball":
            self.powerUpType = "guideball"
        elif self.powerUpType == "guideball":
            self.powerUpType = "spooky-multiball"
        elif self.powerUpType == "spooky-multiball":
            self.powerUpType = "no-gravity"
        elif self.powerUpType == "no-gravity":
            self.powerUpType = "spooky"
            