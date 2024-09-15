from local.ball import Ball
from local.peg import Peg
from local.collision import isBallTouchingPeg, resolveCollision, isBallTouchingLine

# create a simple pygame window to test the collision functions
# have a Ball that follows the cursor and a Peg that is stationary
# have a line that the ball can collide with

import pygame
from pygame.locals import *
from local.config import configs
from local.vectors import Vector

pygame.init()

WIDTH = configs["RESOLUTION"][0]
HEIGHT = configs["RESOLUTION"][1]

# set up the window
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Collision Test")

# set up the colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# set up the clock
clock = pygame.time.Clock()

# set up the Ball
ball = Ball(0, 0)
ball.radius = 10
ball.pos = Vector(100, 100)
ball.vel = Vector(0, 0)
ball.acc = Vector(0, 0)
ball.mass = 1

# set up the Peg
peg = Peg(WIDTH // 2, HEIGHT // 2)
peg.radius = 20
peg.pos = Vector(200, 200)
peg.vel = Vector(0, 0)
peg.mass = 1

# create 6 different lines (2)
line = [(WIDTH // 2, HEIGHT // 2), (WIDTH // 2 + 100, HEIGHT // 2 + 100)]
line2 = [(WIDTH // 2 + 100, HEIGHT // 2 + 100), (WIDTH // 2 + 200, HEIGHT // 2 + 100)]
line3 = [(WIDTH // 2 + 200, HEIGHT // 2 + 100), (WIDTH // 2 + 200, HEIGHT // 2 + 200)]
line4 = [(WIDTH // 2 + 200, HEIGHT // 2 + 200), (WIDTH // 2 + 100, HEIGHT // 2 + 200)]
line5 = [(WIDTH // 2 + 100, HEIGHT // 2 + 200), (WIDTH // 2, HEIGHT // 2 + 200)]
line6 = [(WIDTH // 2, HEIGHT // 2 + 200), (WIDTH // 2, HEIGHT // 2 + 100)]


while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()

    # fill the screen with black
    window.fill(BLACK)

    # get the mouse position
    mouse_pos = pygame.mouse.get_pos()
    ball.pos = Vector(mouse_pos[0] - ball.radius, mouse_pos[1] - ball.radius)
    # reset the ball velocity
    ball.vel = Vector(0, 0)
    ball.acc = Vector(0, 0)

    # draw the line
    pygame.draw.line(window, WHITE, line[0], line[1], 2)
    pygame.draw.line(window, WHITE, line2[0], line2[1], 2)
    pygame.draw.line(window, WHITE, line3[0], line3[1], 2)
    pygame.draw.line(window, WHITE, line4[0], line4[1], 2)
    pygame.draw.line(window, WHITE, line5[0], line5[1], 2)
    pygame.draw.line(window, WHITE, line6[0], line6[1], 2)

    # check for collision between the ball and the peg
    ballIsTouchingPeg = False
    if isBallTouchingPeg(ball.pos.x, ball.pos.y, ball.radius, peg.pos.x, peg.pos.y, peg.radius):
        ball = resolveCollision(ball, peg)
        ballIsTouchingPeg = True

    # check for collision between the ball and the line
    ballIsTouchingLine = False
    if isBallTouchingLine(ball, line[0][0], line[0][1], line[1][0], line[1][1]):
        ballIsTouchingLine = True
        
    if isBallTouchingLine(ball, line2[0][0], line2[0][1], line2[1][0], line2[1][1]):
        ballIsTouchingLine = True
        
    if isBallTouchingLine(ball, line3[0][0], line3[0][1], line3[1][0], line3[1][1]):
        ballIsTouchingLine = True
        
    if isBallTouchingLine(ball, line4[0][0], line4[0][1], line4[1][0], line4[1][1]):
        ballIsTouchingLine = True
        
    if isBallTouchingLine(ball, line5[0][0], line5[0][1], line5[1][0], line5[1][1]):
        ballIsTouchingLine = True
        
    if isBallTouchingLine(ball, line6[0][0], line6[0][1], line6[1][0], line6[1][1]):    
        ballIsTouchingLine = True

    # update the ball
    ball.update()

    # draw the ball
    if ballIsTouchingPeg:
        pygame.draw.circle(window, RED, (int(ball.pos.x), int(ball.pos.y)), ball.radius)
    elif ballIsTouchingLine:
        pygame.draw.circle(window, BLUE, (int(ball.pos.x), int(ball.pos.y)), ball.radius)
    else:
        pygame.draw.circle(window, WHITE, (int(ball.pos.x), int(ball.pos.y)), ball.radius)

    # draw the peg
    pygame.draw.circle(window, GREEN, (int(peg.pos.x), int(peg.pos.y)), peg.radius)

    # update the display
    pygame.display.update()

    # tick the clock
    clock.tick(144)