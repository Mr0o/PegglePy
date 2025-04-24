from math import sqrt
from local.vectors import Vector
from local.ball import Ball
from local.peg import Peg
from local.config import collisionSampleSize

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
def isBallTouchingPeg(ball: Ball, peg: Peg, dt: float) -> bool:
    samples = collisionSampleSize   # number of points to sample along the path
    # Check the endpoints first
    startPoint = ball.prevPos.copy()
    d_start = startPoint.copy()
    d_start.sub(peg.pos)
    if d_start.getMag() <= (ball.radius + peg.radius - EPSILON):
        return True

    endPoint = ball.pos.copy()
    d_end = endPoint.copy()
    d_end.sub(peg.pos)
    if d_end.getMag() <= (ball.radius + peg.radius - EPSILON):
        return True

    # Uniformly sample along the swept path
    for i in range(1, samples):
        t = i / samples  # t is the fraction of dt along the path
        samplePoint = ball.prevPos.copy()
        delta = ball.pos.copy()
        delta.sub(ball.prevPos)
        delta.mult(t)
        samplePoint.add(delta)
        d = samplePoint.copy()
        d.sub(peg.pos)
        if d.getMag() <= (ball.radius + peg.radius - EPSILON):
            return True
    return False

###############################################################################
# Updated circle vs. circle collision resolution using dt.
# We determine the time-of-impact along ball.prevPos->ball.pos then reposition
# the ball so that its center is exactly (ball.radius+peg.radius) away from peg.pos.
# also handles multiple collisions with the ball
###############################################################################
def resolveCollision(ball: Ball, pegs: list[Peg], dt: float) -> Ball:
    # This tolerance is in fractional dt (0 to 1)
    tol = 1e-3  
    best_fraction = 1.0  # best time-of-impact as a fraction of dt
    best_peg = None
    best_normal = None

    # Check each peg for a collision along the path from prevPos to pos (scaled by dt)
    for peg in pegs:
        low, high = 0.0, 1.0
        impact_fraction = None
        # Binary search along the swept path to determine the time-of-impact fraction
        while high - low > tol:
            mid = (low + high) / 2.0
            samplePoint = ball.prevPos.copy()
            delta = ball.pos.copy()
            delta.sub(ball.prevPos)
            delta.mult(mid)  # 'mid' represents fraction of dt
            samplePoint.add(delta)
            d = samplePoint.copy()
            d.sub(peg.pos)
            # If the ball is colliding with the peg at this sample point,
            # consider it a hit (using EPSILON to ignore very slight penetrations)
            if d.getMag() <= (ball.radius + peg.radius - EPSILON):
                impact_fraction = mid
                high = mid
            else:
                low = mid

        # Keep the peg with the earliest (smallest fraction) collision
        if impact_fraction is not None and impact_fraction < best_fraction:
            best_fraction = impact_fraction
            best_peg = peg

            # Get the collision point along the path using the computed fraction of dt
            collisionPos = ball.prevPos.copy()
            delta = ball.pos.copy()
            delta.sub(ball.prevPos)
            delta.mult(impact_fraction)
            collisionPos.add(delta)

            # Compute the collision normal from peg center to collision point.
            normal = collisionPos.copy()
            normal.sub(peg.pos)
            if normal.getMag() != 0:
                normal.normalize()
            else:
                normal = Vector(0, -1)  # fallback normal if the vectors coincide
            best_normal = normal

    # If no collision was detected along the swept path, return the ball unmodified.
    if best_peg is None or best_normal is None:
        return ball

    # With dt in use, best_fraction represents when (within dt) the collision happens.
    # Recompute collision point if needed (here it’s used to snap the ball correctly):
    collisionPos = ball.prevPos.copy()
    delta = ball.pos.copy()
    delta.sub(ball.prevPos)
    delta.mult(best_fraction)
    collisionPos.add(delta)

    # Calculate the final position so that the centers are exactly (ball.radius + peg.radius) apart.
    final_normal = best_normal.copy()  # work on a fresh copy
    final_normal.mult(ball.radius + best_peg.radius)
    finalPos = best_peg.pos.copy()
    finalPos.add(final_normal)
    ball.pos = finalPos

    # Reflect the ball's velocity, but only if it is moving toward the peg.
    # (v_dot_n is computed using the collision normal from our binary search.)
    v_dot_n = ball.vel.x * best_normal.x + ball.vel.y * best_normal.y
    # Use a modified bounciness depending on the ball's current speed.
    bounce = BOUNCINESS
    if ball.vel.getMag() < 2:
        bounce = BOUNCINESS * 0.30
    if ball.vel.getMag() < 1:
        bounce = BOUNCINESS * 0.10
    if v_dot_n < 0:
        correction = best_normal.copy()
        correction.mult((1 + RESTITUITON * bounce) * v_dot_n)
        ball.vel.sub(correction)

    return ball

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