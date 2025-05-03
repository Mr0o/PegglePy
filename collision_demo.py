import sys
import pygame
from local.ball import Ball
from local.vectors import Vector
from local.collision import isBallTouchingLine, resolveCollisionLine, isBallTouchingPeg, resolveCollision
from math import sqrt

pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Collision Test: Lines and Circle-Circle")
clock = pygame.time.Clock()

# Create two balls for collision testing
ball1 = Ball(400, 50, 1)  # falling ball
ball1.radius = 20
ball1.vel = Vector(0, 0)
ball1.pos = Vector(400,50)
ball1.color = (255, 255, 255)  # white

ball2 = Ball(400, 300, 1)  # stationary ball acting as an obstacle (treated as a peg)
ball2.radius = 20
ball2.vel = Vector(0, 0)
ball2.pos = Vector(400,300)
ball2.color = (0, 255, 0)  # green

# Gravity constant and time-step conversion
gravity = 0.5  # acceleration (pixels/frame^2)
# Here we use dt in seconds; we'll scale gravity by dt*60 to approximate the original value.

# For line collisions: store lines. Each line is a tuple: ((x1, y1), (x2, y2))
lines = []

# For adding new lines with the mouse
line_start = None  # When user clicks, store first endpoint

while True:
    # dt in seconds
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Left mouse clicks to add lines
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()  # (x, y)
            if line_start is None:
                line_start = pos
            else:
                line_end = pos
                lines.append((line_start, line_end))
                line_start = None
        # Right mouse click: reset ball1's position
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mx, my = pygame.mouse.get_pos()
            ball1.pos = Vector(mx, my)
            ball1.vel = Vector(0, 0)
    
    # --- Update physics ---
    # Before moving the ball, store its previous position for continuous collision checks.
    ball1.prevPos = ball1.pos.copy()

    # Use dt (in seconds) for physics integration.
    ball1.vel.y += gravity * (dt * 60)
    ball1.pos.x += ball1.vel.x * (dt * 60)
    ball1.pos.y += ball1.vel.y * (dt * 60)

    # Wrap ball1 to top if it falls off the bottom of the screen.
    if ball1.pos.y - ball1.radius > screen_height:
        ball1.pos.y = -ball1.radius

    # --- Collision detection and response ---
    # Check for collisions with each line using dt (not ms)
    for ln in lines:
        (lx1, ly1), (lx2, ly2) = ln
        if isBallTouchingLine(ball1, lx1, ly1, lx2, ly2, dt):
            ball1 = resolveCollisionLine(ball1, ((lx1, ly1), (lx2, ly2)), dt)

    # Check for circle vs. circle collision (ball1 vs ball2)
    if isBallTouchingPeg(ball2, ball1, dt):
        # Assume ball2 is static; resolve the collision for ball1.
        ball1 = resolveCollision(ball1, [ball2], dt)
    
    # --- Drawing ---
    screen.fill((0, 0, 0))
    
    # Draw existing lines in red
    for ln in lines:
        pygame.draw.line(screen, (255, 0, 0), ln[0], ln[1], 3)
    
    # If in the middle of adding a line, draw a preview line
    if line_start is not None:
        pygame.draw.line(screen, (255, 100, 0), line_start, pygame.mouse.get_pos(), 2)
    
    # Draw ball1 and ball2 as circles
    pygame.draw.circle(screen, ball1.color, (int(ball1.pos.x), int(ball1.pos.y)), ball1.radius)
    pygame.draw.circle(screen, ball2.color, (int(ball2.pos.x), int(ball2.pos.y)), ball2.radius)
    
    pygame.display.flip()