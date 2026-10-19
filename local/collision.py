from math import sqrt
from local.vectors import Vector
from local.ball import Ball
from local.peg import Peg
from local.config import collisionSampleSize
from local.quadtree import Rectangle

EPSILON = 0.25  # Tolerance to ignore very slight penetrations
RESTITUITON = 0.90  # Coefficient of restitution
BOUNCINESS = 1.0  # Coefficient of bounciness

def point_to_segment_distance(P: Vector, A: Vector, B: Vector) -> float:
    AP = P.copy()
    AP.sub(A)       # modifies AP in-place
    AB = B.copy()
    AB.sub(A)       # modifies AB in-place
    ab2 = AB.x * AB.x + AB.y * AB.y
    if ab2 == 0:
        return AP.getMag()
    t = (AP.x * AB.x + AP.y * AB.y) / ab2
    if t < 0:
        t = 0
    elif t > 1:
        t = 1
    proj = A.copy()
    AB2 = B.copy()  # re-copy for a fresh vector
    AB2.sub(A)
    AB2.mult(t)
    proj.add(AB2)
    diff = P.copy()
    diff.sub(proj)
    return diff.getMag()

###############################################################################
# Continuous circle vs circle collision detection and resolution with dt.
###############################################################################
def isBallTouchingPeg(
    ball: Ball, peg: Peg, dt: float, peg_radius_multiplier: float = 1.0
) -> bool:
    return _circle_impact(ball, peg, peg_radius_multiplier) is not None


def getSweptCollisionBounds(ball: Ball, padding: float) -> Rectangle:
    return Rectangle(
        (ball.prevPos.x + ball.pos.x) / 2,
        (ball.prevPos.y + ball.pos.y) / 2,
        abs(ball.pos.x - ball.prevPos.x) / 2 + padding,
        abs(ball.pos.y - ball.prevPos.y) / 2 + padding,
    )


def updateSweptCollisionBounds(
    ball: Ball, padding: float, bounds: Rectangle
) -> None:
    bounds.x = (ball.prevPos.x + ball.pos.x) / 2
    bounds.y = (ball.prevPos.y + ball.pos.y) / 2
    bounds.w = abs(ball.pos.x - ball.prevPos.x) / 2 + padding
    bounds.h = abs(ball.pos.y - ball.prevPos.y) / 2 + padding

###############################################################################
# Updated circle vs. circle collision resolution using dt.
# We determine the time-of-impact along ball.prevPos->ball.pos then reposition
# the ball so that its center is exactly (ball.radius+peg.radius) away from peg.pos.
# also handles multiple collisions with the ball
###############################################################################
def resolveCollision(ball: Ball, pegs: list[Peg], dt: float) -> Ball:
    resolveCollisionAndGetPeg(ball, pegs)
    return ball


def resolveCollisionAndGetPeg(ball: Ball, pegs: list[Peg]) -> Peg | None:
    best_fraction = 1.0
    best_peg = None
    best_normal = None

    for peg in pegs:
        impact = _circle_impact(ball, peg)
        if impact is not None and impact[0] < best_fraction:
            best_fraction, best_normal = impact
            best_peg = peg

    # If no collision was detected along the swept path, return the ball unmodified.
    if best_peg is None or best_normal is None:
        return None

    ball.pos = best_peg.pos.copy()
    normal_offset = best_normal.copy()
    normal_offset.mult(ball.radius + best_peg.radius)
    ball.pos.add(normal_offset)

    # Reflect the ball's velocity, but only if it is moving toward the peg.
    # (v_dot_n is computed using the collision normal from our binary search.)
    relative_velocity = Vector(
        ball.vel.x - best_peg.vel.x,
        ball.vel.y - best_peg.vel.y,
    )
    v_dot_n = (
        relative_velocity.x * best_normal.x
        + relative_velocity.y * best_normal.y
    )
    # Use a modified bounciness depending on the ball's current speed.
    bounce = BOUNCINESS
    if relative_velocity.getMag() < 2:
        bounce = BOUNCINESS * 0.30
    if relative_velocity.getMag() < 1:
        bounce = BOUNCINESS * 0.10
    if v_dot_n < 0:
        correction = best_normal.copy()
        correction.mult((1 + RESTITUITON * bounce) * v_dot_n)
        ball.vel.sub(correction)

    return best_peg


def _circle_impact(
    ball: Ball, peg: Peg, peg_radius_multiplier: float = 1.0
) -> tuple[float, Vector] | None:
    peg_previous_position = (
        peg.previousPos
        if getattr(peg, "movement", None) is not None
        else peg.pos
    )
    start_x = ball.prevPos.x - peg_previous_position.x
    start_y = ball.prevPos.y - peg_previous_position.y
    delta_x = (ball.pos.x - ball.prevPos.x) - (peg.pos.x - peg_previous_position.x)
    delta_y = (ball.pos.y - ball.prevPos.y) - (peg.pos.y - peg_previous_position.y)
    radius = ball.radius + peg.radius * peg_radius_multiplier - EPSILON
    radius_squared = radius * radius

    start_distance_squared = start_x * start_x + start_y * start_y
    if start_distance_squared <= radius_squared:
        normal = Vector(start_x, start_y)
        if normal.getMag() == 0:
            normal = Vector(0, -1)
        else:
            normal.normalize()
        return 0.0, normal

    movement_squared = delta_x * delta_x + delta_y * delta_y
    if movement_squared == 0:
        return None

    start_dot_movement = start_x * delta_x + start_y * delta_y
    discriminant = (
        start_dot_movement * start_dot_movement
        - movement_squared * (start_distance_squared - radius_squared)
    )
    if discriminant < 0:
        return None

    impact_fraction = (
        -start_dot_movement - sqrt(discriminant)
    ) / movement_squared
    if not 0 <= impact_fraction <= 1:
        return None

    normal = Vector(
        start_x + delta_x * impact_fraction,
        start_y + delta_y * impact_fraction,
    )
    if normal.getMag() == 0:
        normal = Vector(0, -1)
    else:
        normal.normalize()
    return impact_fraction, normal

###############################################################################
# Continuous line collision detection and resolution with dt.
###############################################################################
def isBallTouchingLine(ball: Ball, linex1: float, liney1: float, linex2: float, liney2: float, dt: float) -> bool:
    samples = collisionSampleSize
    # limit samples to 000 to prevent major performance drop offs
    samples = min(samples, 100)
    L1 = Vector(linex1, liney1)
    L2 = Vector(linex2, liney2)
    for i in range(samples + 1):
        t = i / samples
        samplePoint = ball.prevPos.copy()
        delta = ball.pos.copy()
        delta.sub(ball.prevPos)
        delta.mult(t)
        samplePoint.add(delta)
        d = point_to_segment_distance(samplePoint, L1, L2)
        if d < (ball.radius - EPSILON):
            return True
    return False

###############################################################################
# Updated line collision resolution using dt.
# We binary search to find the time-of-impact along the swept path.
# Then we project the collision point onto the line and reposition the ball so that
# the distance from the line equals the ball's radius.
###############################################################################
def resolveCollisionLine(ball: Ball, line: tuple, dt: float) -> Ball:
    (L1, L2) = line
    L1_v = Vector(L1[0], L1[1])
    L2_v = Vector(L2[0], L2[1])

    # 1) Calculate line direction and an outward normal
    lineDir = L2_v.copy()
    lineDir.sub(L1_v)  # modifies lineDir
    normal = Vector(-lineDir.y, lineDir.x)
    if normal.getMag() == 0:
        normal = Vector(0, 1)
    else:
        mag = normal.getMag()
        normal.div(mag)  # modifies normal

    # Reorient normal so it points from line to the ball's previous position
    testVec = ball.prevPos.copy()
    testVec.sub(L1_v)
    dot_val = testVec.x * normal.x + testVec.y * normal.y
    if dot_val < 0:
        normal.mult(-1)

    # 2) Binary search for time-of-impact
    tol = 1e-3
    low, high = 0.0, 1.0
    while (high - low) > tol:
        mid = (low + high) / 2.0
        samplePoint = ball.prevPos.copy()
        tmpDelta = ball.pos.copy()
        tmpDelta.sub(ball.prevPos)
        tmpDelta.mult(mid)
        samplePoint.add(tmpDelta)
        d = point_to_segment_distance(samplePoint, L1_v, L2_v)
        if d < (ball.radius - EPSILON):
            high = mid
        else:
            low = mid
    impact_t = high

    # 3) Reposition ball at collision time
    collisionPos = ball.prevPos.copy()
    bigDelta = ball.pos.copy()
    bigDelta.sub(ball.prevPos)
    bigDelta.mult(impact_t)
    collisionPos.add(bigDelta)

    # 4) Determine where on the line to snap
    #    (project collisionPos onto L1->L2)
    projBase = collisionPos.copy()
    projBase.sub(L1_v)
    lineDir2 = L2_v.copy()
    lineDir2.sub(L1_v)
    lineLength2 = lineDir2.getMag() ** 2 or 0.0001

    dotVal2 = projBase.x * lineDir2.x + projBase.y * lineDir2.y
    t_proj = dotVal2 / lineLength2
    if t_proj < 0:
        t_proj = 0
    elif t_proj > 1:
        t_proj = 1
    linePoint = L1_v.copy()
    lineDirScaled = lineDir2.copy()
    lineDirScaled.mult(t_proj)
    linePoint.add(lineDirScaled)

    finalPos = linePoint.copy()
    normalScaled = normal.copy()
    normalScaled.mult(ball.radius)
    finalPos.add(normalScaled)

    ball.pos = finalPos

    # 5) # Reflect the ball's velocity if it's moving into the line:
    v_dot_n = ball.vel.x * normal.x + ball.vel.y * normal.y
    # use a different bounciness if the velocity is below 3
    bounce = BOUNCINESS
    if ball.vel.getMag() < 2:
        bounce = BOUNCINESS * 0.30
    if ball.vel.getMag() < 1:
        bounce = BOUNCINESS * 0.10
    if v_dot_n < 0:
        correction = normal.copy()
        correction.mult((1 + RESTITUITON * bounce) * v_dot_n)
        ball.vel.sub(correction)

    return ball