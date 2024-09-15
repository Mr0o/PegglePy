from math import sqrt
from local.vectors import Vector
from local.ball import Ball
from local.peg import Peg

def isBallTouchingPeg(b1x, b1y, b1r, b2x, b2y, b2r) -> bool:
    return ((b1x-b2x)*(b1x-b2x) + (b1y-b2y)*(b1y-b2y)) < (b1r+b2r)*(b1r+b2r)

# circle vs circle collision
def resolveCollision(ball: Ball, peg: Peg) -> Ball:
    """
    Resolve elastic collisions between two spheres (ball and peg):

    - Both arguments are expected to be objects with mass, radius, position (pos), and velocity (vel).
    - Returns the ball object with updated position and velocity from the collision.
    """

    # Calculate the vector between the centers
    delta_pos = ball.pos.copy()
    delta_pos.sub(peg.pos)

    # Calculate the distance between centers
    distance = delta_pos.getMag()

    # Prevent division by zero
    if distance == 0:
        distance = 0.0001  # Small number to avoid division by zero

    # Calculate the overlap
    overlap = (ball.radius + peg.radius) - distance

    # Check if there is an overlap (collision)
    if overlap > 0:
        # Normalize the delta position to get the collision normal vector
        collision_normal = delta_pos.copy()
        collision_normal.div(distance)

        # Calculate inverse masses (handle infinite mass if mass is zero)
        inv_mass_ball = 1 / ball.mass if ball.mass != 0 else 0
        inv_mass_peg = 1 / peg.mass if peg.mass != 0 else 0
        inv_mass_total = inv_mass_ball + inv_mass_peg

        # Correct the positions to resolve overlap
        correction = collision_normal.copy()
        correction.mult(overlap / inv_mass_total)

        # Adjust positions based on inverse masses
        correctionVecBall = correction.copy()
        correctionVecBall.mult(inv_mass_ball)
        correctionVecPeg = correction.copy()
        correctionVecPeg.mult(inv_mass_peg)
        
        ball.pos.add(correctionVecBall)

        # Calculate relative velocity
        relative_velocity = ball.vel.copy()
        relative_velocity.sub(peg.vel)

        # Calculate velocity along the normal
        vel_along_normal = relative_velocity.dot(collision_normal)

        # Proceed only if the objects are moving towards each other
        if vel_along_normal < 0:
            # Coefficient of restitution (e = 1 for perfectly elastic collision)
            e = 1.0
            
            # lower the restitution if the ball velocity is low (to debounce the ball as it approaches rest)
            # and only if the ball is moving down
            if ball.vel.getMag() < 2.5 and ball.vel.y > 0:
                e = 0.0

            # Calculate impulse scalar
            impulse_scalar = -(1 + e) * vel_along_normal
            impulse_scalar /= inv_mass_total

            # Calculate impulse vector
            impulse = collision_normal.copy()
            impulse.mult(impulse_scalar)

            # Update velocities based on impulse and inverse masses
            impulseVecBall = impulse.copy()
            impulseVecBall.mult(inv_mass_ball)
            impulseVecPeg = impulse.copy()
            impulseVecPeg.mult(inv_mass_peg)
            
            ball.vel.add(impulseVecBall)

    return ball


# circle vs line collision
def isBallTouchingLine(ball: Ball, linex1: float, liney1: float, linex2: float, liney2: float) -> bool:
    """
    Determines if the ball is touching or intersecting the line segment defined by two points.

    Parameters:
        ball (Ball): The ball object with pos and radius.
        linex1, liney1 (float): Coordinates of the first endpoint of the line segment.
        linex2, liney2 (float): Coordinates of the second endpoint of the line segment.

    Returns:
        bool: True if the ball is touching the line, False otherwise.
    """
    # Create Vector instances for the line endpoints
    line_point1 = Vector(linex1, liney1)
    line_point2 = Vector(linex2, liney2)

    # Line segment vector
    line_vec = line_point2 - line_point1
    line_length_sq = line_vec.getMag() ** 2  # Squared length of the line segment

    # Early exit if the line is a point
    if line_length_sq == 0:
        # Check if the distance between the ball center and the line point is less than or equal to the radius
        distance_vec = ball.pos - line_point1
        distance = distance_vec.getMag()
        return distance <= ball.radius

    # Vector from line start to ball center
    ball_to_line_start = ball.pos - line_point1

    # Compute t: the parameterized position on the line segment closest to the ball
    t = line_vec.dot(ball_to_line_start) / line_length_sq

    # Clamp t to [0, 1] to restrict to the segment
    t_clamped = max(0, min(t, 1))

    # Closest point on the line segment to the ball center
    closest_point = line_point1 + line_vec * t_clamped

    # Distance from ball center to closest point
    distance_vec = ball.pos - closest_point
    distance = distance_vec.getMag()

    # Check if the distance is less than or equal to the radius
    return distance <= ball.radius
