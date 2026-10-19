import time
from math import sqrt, atan, cos, pi

from local.vectors import Vector, subVectors
from local.ball import Ball
from local.peg import Peg, getScoreMultiplier
from local.bucket import Bucket
from local.config import (
    LAUNCH_FORCE,
    trajectoryDepth,
    queryRectSize,
    longShotDistance,
)
from local.config import configs, gravity
from local.collision import (
    isBallTouchingPeg,
    resolveCollision,
    resolveCollisionAndGetPeg,
    updateSweptCollisionBounds,
)
from local.quadtree import QuadtreePegs, Rectangle

ZENBALL_SEARCH_TIME_LIMIT = 4.0

def _clone_moving_pegs(pegs: list[Peg]) -> list[Peg]:
    return [
        peg.clone_for_prediction()
        for peg in pegs
        if peg.movement is not None
    ]


class TrajectoryCalculation:
    def __init__(
        self,
        aim: Vector,
        startPos: Vector,
        pegs: list[Peg],
        bucketPegs: list[Peg],
        quadtree: QuadtreePegs,
        dt: float,
        collisionGuideBall: bool = False,
        depth: int = trajectoryDepth,
        debugTrajectory: bool = False,
        zeroGravity: bool = False,
        wrapAtBottom: bool = False,
        bucket: Bucket | None = None,
        useQuadtree: bool = True,
    ):
        self.points: list[Ball] = []
        self.result: list[Ball] | None = None
        bucket_pegs = []
        for peg in bucketPegs:
            fake_peg = Peg(peg.pos.x, peg.pos.y)
            fake_peg.radius = peg.radius
            bucket_pegs.append(fake_peg)
        self._movingPegSnapshots = _clone_moving_pegs(pegs)
        self._steps = self._calculate(
            aim,
            startPos,
            pegs,
            bucket_pegs,
            quadtree,
            dt,
            collisionGuideBall,
            depth,
            debugTrajectory,
            zeroGravity,
            wrapAtBottom,
            bucket,
            useQuadtree,
        )

    def advance(self, time_budget: float = 0.002) -> bool:
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < time_budget:
            try:
                next(self._steps)
            except StopIteration as completed:
                self.result = completed.value
                return True
        return self.result is not None

    def _calculate(
        self,
        aim: Vector,
        startPos: Vector,
        pegs: list[Peg],
        bucketPegs: list[Peg],
        quadtree: QuadtreePegs,
        dt: float,
        collisionGuideBall: bool,
        depth: int,
        debugTrajectory: bool,
        zeroGravity: bool,
        wrapAtBottom: bool,
        bucket: Bucket | None,
        useQuadtree: bool,
    ):
        hit = False
        fake_ball = Ball(startPos.x, startPos.y)
        launch_force = subVectors(aim, startPos)
        launch_force.setMag(LAUNCH_FORCE)
        fake_ball.applyForce(launch_force)
        candidate_pegs: list[Peg] = []
        candidate_bounds = Rectangle(0, 0, 0, 0)

        bucket_t = bucket.t if bucket is not None else 0.0
        bucket_direction = bucket.t_direction if bucket is not None else 1
        if bucket is not None:
            bucket_left = bucket.back_img_width - 300
            bucket_right = configs["WIDTH"] - bucket.back_img_width
            bucket_t_speed = bucket.t_speed * dt
            bucket_y = bucket.pos.y
            bucket_offsets = tuple(bucket.fakePegOffsets) + (
                (150, 453),
            ) * max(0, len(bucketPegs) - len(bucket.fakePegOffsets))
        else:
            bucket_left = bucket_right = bucket_t_speed = bucket_y = 0.0
            bucket_offsets = ()

        for step in range(depth):
            for moving_peg in self._movingPegSnapshots:
                moving_peg.update_movement(dt)
            updateSweptCollisionBounds(
                fake_ball,
                queryRectSize,
                candidate_bounds,
            )
            candidate_pegs.clear()
            if useQuadtree:
                quadtree.queryInto(
                    candidate_bounds,
                    candidate_pegs,
                    include_moving_pegs=False,
                )
            else:
                candidate_pegs.extend(
                    peg for peg in pegs if peg.movement is None
                )
            quadtree.queryMovingInto(
                candidate_bounds,
                self._movingPegSnapshots,
                candidate_pegs,
            )

            if bucket is not None and step > 0:
                eased_t = 0.5 - 0.5 * cos(pi * bucket_t)
                bucket_x = bucket_left + (bucket_right - bucket_left) * eased_t
                for peg, (offset_x, offset_y) in zip(
                    bucketPegs,
                    bucket_offsets,
                ):
                    peg.pos.x = bucket_x + offset_x
                    peg.pos.y = bucket_y + offset_y
            collided_peg = resolveCollisionAndGetPeg(
                fake_ball,
                candidate_pegs,
            )
            if zeroGravity:
                if fake_ball.vel.getMag() < 1.5:
                    fake_ball.vel.setMag(1.5)
                if fake_ball.vel.getMag() < 0.2:
                    fake_ball.vel.add(Vector(0, 1))

            bucket_collision = None
            for bucket_peg in bucketPegs:
                if isBallTouchingPeg(fake_ball, bucket_peg, dt):
                    resolveCollision(fake_ball, [bucket_peg], dt)
                    bucket_collision = bucket_peg
                    break
            if collided_peg is None:
                collided_peg = bucket_collision

            if collided_peg is not None:
                if self.points:
                    self.points[-1].pos = fake_ball.pos.copy()
                else:
                    self.points.append(self._snapshot_ball(fake_ball))
                if collisionGuideBall and hit:
                    return self.points
                if not collisionGuideBall and not debugTrajectory:
                    return self.points

                if collisionGuideBall:
                    hit = True

            fake_ball.update(dt, zeroGravity)
            if wrapAtBottom and fake_ball.pos.y + fake_ball.radius > configs["HEIGHT"]:
                fake_ball.pos.y = fake_ball.radius
                fake_ball.prevPos = fake_ball.pos.copy()
                fake_ball.prevAcc = fake_ball.acc.copy()
                fake_ball.prevVel = fake_ball.vel.copy()

            if bucket is not None:
                bucket_t, bucket_direction = Bucket._advance_motion_phase(
                    bucket_t,
                    bucket_direction,
                    bucket_t_speed,
                )

            if fake_ball.prevPos.y > configs["HEIGHT"] + fake_ball.radius:
                return self.points

            self.points.append(self._snapshot_ball(fake_ball))
            yield None

        return self.points

    @staticmethod
    def _snapshot_ball(ball: Ball) -> Ball:
        snapshot = Ball(ball.pos.x, ball.pos.y)
        snapshot.pos = ball.pos.copy()
        snapshot.prevPos = ball.prevPos.copy()
        snapshot.vel = ball.vel.copy()
        snapshot.prevVel = ball.prevVel.copy()
        snapshot.acc = ball.acc.copy()
        snapshot.prevAcc = ball.prevAcc.copy()
        return snapshot


def calcTrajectory(
    aim: Vector,
    startPos: Vector,
    pegs: list[Peg],
    bucketPegs: list[Peg],
    quadtree: QuadtreePegs,
    dt: float,
    collisionGuideBall: bool = False,
    depth: int = trajectoryDepth,
    debugTrajectory: bool = False,
    zeroGravity: bool = False,
    wrapAtBottom: bool = False,
    bucket: Bucket | None = None,
    useQuadtree: bool = True,
) -> list[Ball]:
    calculation = TrajectoryCalculation(
        aim,
        startPos,
        pegs,
        bucketPegs,
        quadtree,
        dt,
        collisionGuideBall,
        depth,
        debugTrajectory,
        zeroGravity,
        wrapAtBottom,
        bucket,
        useQuadtree,
    )
    while not calculation.advance(float("inf")):
        pass
    if calculation.result is None:
        raise RuntimeError("Completed trajectory calculation has no result")
    return calculation.result


def findBestTrajectory(
    aim: Vector,
    startPos: Vector,
    pegs: list[Peg],
    quadtree: QuadtreePegs,
    dt: float,
    maxRangeDegrees: int = 21,
    depth: int = 2500,
    setTimeLimit: float = ZENBALL_SEARCH_TIME_LIMIT,
    bucket: Bucket | None = None,
):
    search = BestTrajectorySearch(
        aim,
        startPos,
        pegs,
        quadtree,
        dt,
        maxRangeDegrees,
        depth,
        setTimeLimit,
        bucket,
    )
    while not search.advance(float("inf")):
        pass
    if search.result is None:
        raise RuntimeError("Completed trajectory search has no result")
    return search.result


class BestTrajectorySearch:
    def __init__(
        self,
        aim: Vector,
        startPos: Vector,
        pegs: list[Peg],
        quadtree: QuadtreePegs,
        dt: float,
        maxRangeDegrees: int = 21,
        depth: int = 2500,
        setTimeLimit: float = ZENBALL_SEARCH_TIME_LIMIT,
        bucket: Bucket | None = None,
    ):
        self.result: tuple[Vector, int, list[Ball]] | None = None
        self.reached_bucket = False
        self.elapsed = 0.0
        self.evaluated_angles = 0
        self._movingPegSnapshots = _clone_moving_pegs(pegs)
        self._steps = self._search_steps(
            aim,
            startPos,
            pegs,
            quadtree,
            dt,
            maxRangeDegrees,
            depth,
            setTimeLimit,
            bucket,
        )

    def advance(self, time_budget: float = 0.003) -> bool:
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < time_budget:
            try:
                next(self._steps)
            except StopIteration as completed:
                self.result = completed.value
                return True
        return False

    def _search_steps(
        self,
        aim: Vector,
        startPos: Vector,
        pegs: list[Peg],
        quadtree: QuadtreePegs,
        dt: float,
        maxRangeDegrees: int,
        depth: int,
        time_limit: float,
        bucket,
    ):
        original_aim = aim.copy()
        start_time = time.perf_counter()
        time_limit = min(
            max(float(time_limit), 0.0), ZENBALL_SEARCH_TIME_LIMIT
        )
        deadline = start_time + time_limit if time_limit else None
        initial_oranges = sum(
            peg.color == "orange" and not peg.isHit for peg in pegs
        )
        initial_direction = subVectors(original_aim, startPos)
        best_aim = initial_direction.copy()
        best_aim.setMag(LAUNCH_FORCE)
        best_score = -1
        best_reached_bucket = False
        best_angle_delta = float("inf")
        best_path: list[tuple[float, float]] = []

        if bucket is None:
            bucket_t = 0.0
            bucket_direction = 1
            bucket_left = bucket_right = bucket_y = 0.0
            bucket_t_speed = 0.0
            bucket_width = bucket_height = 0.0
            bucket_offsets = ()
            fake_bucket_pegs: list[Peg] = []
        else:
            bucket_t = bucket.t
            bucket_direction = bucket.t_direction
            bucket_left = bucket.back_img_width - 300
            bucket_right = configs["WIDTH"] - bucket.back_img_width
            bucket_y = bucket.pos.y
            bucket_t_speed = bucket.t_speed * dt
            bucket_width = bucket.bucketBackImg.get_width()
            bucket_height = bucket.bucketBackImg.get_height()
            bucket_offsets = tuple(bucket.fakePegOffsets[:2])
            fake_bucket_pegs = [
                Peg(0, 0),
                Peg(0, 0),
            ]
            for peg, source in zip(fake_bucket_pegs, bucket.fakePegs[:2]):
                peg.radius = source.radius

        candidates = []
        candidate_bounds = Rectangle(0, 0, 0, 0)
        best_coarse: list[tuple[int, bool, float]] = []

        def bucket_x_at(t_value: float) -> float:
            eased = 0.5 - 0.5 * cos(pi * t_value)
            return bucket_left + (bucket_right - bucket_left) * eased

        def remember_candidate(
            angle_value: float,
            score_value: int,
            caught_bucket: bool,
            path: list[tuple[float, float]],
        ) -> None:
            nonlocal best_aim, best_score, best_reached_bucket
            nonlocal best_angle_delta, best_path
            angle_delta = abs(angle_value - aim_angle)
            rank = (score_value, int(caught_bucket), -angle_delta)
            best_rank = (
                best_score,
                int(best_reached_bucket),
                -best_angle_delta,
            )
            if rank > best_rank:
                best_score = score_value
                best_reached_bucket = caught_bucket
                best_aim = Vector(1, 0)
                best_aim.setAngleDeg(angle_value)
                best_aim.setMag(LAUNCH_FORCE)
                best_angle_delta = angle_delta
                best_path = path

        def simulate_angle(angle_value: float):
            moving_pegs = [
                peg.clone_for_prediction()
                for peg in self._movingPegSnapshots
            ]
            ball = Ball(startPos.x, startPos.y)
            launch_force = Vector(1, 0)
            launch_force.setAngleDeg(angle_value)
            launch_force.setMag(LAUNCH_FORCE)
            ball.applyForce(launch_force)
            path: list[tuple[float, float]] = []
            hit_pegs: set[int] = set()
            score = 0
            orange_count = initial_oranges
            pegs_hit = 0
            last_hit_position: tuple[float, float] | None = None
            long_shot_awarded = False
            caught_bucket = False
            current_bucket_t = bucket_t
            current_bucket_direction = bucket_direction

            for _ in range(max(0, depth)):
                for moving_peg in moving_pegs:
                    moving_peg.update_movement(dt)
                if deadline is not None and time.perf_counter() >= deadline:
                    remember_candidate(
                        angle_value, score, caught_bucket, path
                    )
                    return score, caught_bucket, path, True

                updateSweptCollisionBounds(
                    ball, queryRectSize, candidate_bounds
                )
                candidates.clear()
                quadtree.queryInto(
                    candidate_bounds,
                    candidates,
                    include_moving_pegs=False,
                )
                quadtree.queryMovingInto(
                    candidate_bounds,
                    moving_pegs,
                    candidates,
                )
                collided_peg = resolveCollisionAndGetPeg(ball, candidates)
                if collided_peg is not None:
                    peg_id = id(collided_peg)
                    if (
                        last_hit_position is not None
                        and not long_shot_awarded
                        and collided_peg.color == "orange"
                        and not collided_peg.isHit
                    ):
                        delta_x = collided_peg.pos.x - last_hit_position[0]
                        delta_y = collided_peg.pos.y - last_hit_position[1]
                        if (
                            delta_x * delta_x + delta_y * delta_y
                            > longShotDistance * longShotDistance
                        ):
                            score += 25_000
                            long_shot_awarded = True
                    last_hit_position = (
                        collided_peg.pos.x,
                        collided_peg.pos.y,
                    )
                    if not collided_peg.isHit and peg_id not in hit_pegs:
                        hit_pegs.add(peg_id)
                        pegs_hit += 1
                        if collided_peg.color == "orange":
                            orange_count -= 1
                        score += collided_peg.points * getScoreMultiplier(
                            orange_count, pegs_hit
                        )

                if fake_bucket_pegs:
                    current_x = bucket_x_at(current_bucket_t)
                    for fake_peg, offset in zip(
                        fake_bucket_pegs, bucket_offsets
                    ):
                        fake_peg.pos.x = current_x + offset[0]
                        fake_peg.pos.y = bucket_y + offset[1]
                    resolveCollisionAndGetPeg(ball, fake_bucket_pegs)

                ball.update(dt)
                path.append((ball.pos.x, ball.pos.y))
                if bucket is not None:
                    current_bucket_t += (
                        current_bucket_direction * bucket_t_speed
                    )
                    if current_bucket_t >= 1.0:
                        current_bucket_t = 1.0
                        current_bucket_direction = -1
                    elif current_bucket_t <= 0.0:
                        current_bucket_t = 0.0
                        current_bucket_direction = 1
                    current_x = bucket_x_at(current_bucket_t)
                    caught_bucket = (
                        ball.pos.y
                        > configs["HEIGHT"] - bucket_height + 12
                        and ball.pos.x > current_x - bucket_width + 330
                        and ball.pos.x < current_x + bucket_width - 30
                    )
                    if caught_bucket:
                        break

                if ball.pos.y > configs["HEIGHT"] + ball.radius:
                    break

                yield None

            remember_candidate(angle_value, score, caught_bucket, path)
            return score, caught_bucket, path, False

        def candidate_angles(
            centers: list[float], spacing: float, radius: float
        ) -> list[float]:
            values: set[float] = set()
            for center in centers:
                for offset_index in range(
                    -int(radius / spacing), int(radius / spacing) + 1
                ):
                    values.add(round(center + offset_index * spacing, 6))
            return sorted(values)

        aim_angle = initial_direction.getAngleDeg()
        search_width = max(0.0, float(maxRangeDegrees))
        coarse_count = 1 if search_width == 0 else max(3, int(search_width) + 1)
        coarse_spacing = (
            search_width / (coarse_count - 1) if coarse_count > 1 else 0.0
        )
        coarse_angles = (
            [aim_angle]
            if coarse_count == 1
            else [
                aim_angle - search_width / 2 + index * coarse_spacing
                for index in range(coarse_count)
            ]
        )

        for angle_value in coarse_angles:
            completed = False
            simulation = simulate_angle(angle_value)
            while not completed:
                try:
                    next(simulation)
                    yield None
                except StopIteration as outcome:
                    if outcome.value is not None:
                        score_value, bucket_value, _, timed_out = outcome.value
                        self.evaluated_angles += 1
                        if not timed_out:
                            best_coarse.append(
                                (score_value, bucket_value, angle_value)
                            )
                    completed = True
            if deadline is not None and time.perf_counter() >= deadline:
                break

        if coarse_spacing > 0 and (
            deadline is None or time.perf_counter() < deadline
        ):
            best_coarse.sort(
                key=lambda item: (
                    item[0],
                    int(item[1]),
                    -abs(item[2] - aim_angle),
                ),
                reverse=True,
            )
            refine_centers = [item[2] for item in best_coarse[:3]]
            bucket_candidates = [
                item for item in best_coarse if item[1]
            ]
            if bucket_candidates:
                best_bucket_angle = max(
                    bucket_candidates,
                    key=lambda item: (
                        item[0],
                        -abs(item[2] - aim_angle),
                    ),
                )[2]
                if best_bucket_angle not in refine_centers:
                    refine_centers.append(best_bucket_angle)
            for angle_value in candidate_angles(
                refine_centers, 0.2, coarse_spacing
            ):
                if deadline is not None and time.perf_counter() >= deadline:
                    break
                completed = False
                simulation = simulate_angle(angle_value)
                while not completed:
                    try:
                        next(simulation)
                        yield None
                    except StopIteration as outcome:
                        if outcome.value is not None:
                            self.evaluated_angles += 1
                        completed = True

        if best_score < 0:
            best_score = 0
        self.elapsed = time.perf_counter() - start_time
        self.reached_bucket = best_reached_bucket
        best_trajectory = [
            Ball(x, y) for x, y in best_path
        ]
        return best_aim, best_score, best_trajectory


def getLaunchAngles(start: Vector,
                     target: Vector,
                     speed: float = LAUNCH_FORCE) -> list[float]:
    """
    Compute the two possible launch angles (in radians) required
    to hit `target` from `start` at given scalar launch `speed`.
    Returns [low_angle, high_angle], or [] if unreachable.
    """
    dx = target.x - start.x
    # screen y grows DOWN, so invert for physics y-up
    dy = start.y - target.y

    v2 = speed*speed
    g  = gravity.y

    # guard vertical shot
    if abs(dx) < 1e-6:
        # max height = v^2/(2g)
        if dy > v2/(2*g):
            # unreachable
            return []
        return [3/2*pi]   # 270 degrees, straight down

    # discriminant of v^4 - g*(g x^2 + 2 y v^2)
    disc = v2*v2 - g*(g*dx*dx + 2*dy*v2)
    if disc < 0:
        return []

    sqrt_d = sqrt(disc)
    # θ = atan( (v^2 ± sqrt(disc)) / (g·x) )
    low  = atan((v2 - sqrt_d)/(g*dx))
    high = atan((v2 + sqrt_d)/(g*dx))

    # if target is left of start, shift both angles by pi
    if dx < 0:
        low  += pi
        high += pi
    return [low, high]