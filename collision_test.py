from local.ball import Ball
from local.peg import Peg
from local.collision import isBallTouchingPeg, resolveCollision, isBallTouchingLine, resolveCollisionLine

# create a simple pygame screen to test the collision functions
# have a Ball that follows the cursor and a Peg that is stationary
# have a line that the ball can collide with

import pygame
from pygame.locals import *
from local.config import configs
from local.vectors import Vector

pygame.init()

WIDTH = configs["WIDTH"]
HEIGHT = configs["HEIGHT"]

# set up the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
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

# This ball will have physics applied to it
ball2 = Ball(0, 0)
ball2.radius = 25
ball2.pos = Vector(200, 100)
ball2.vel = Vector(0, 0)
ball2.acc = Vector(0, 0)
ball2.mass = 1

# set up the Peg
peg = Peg(WIDTH // 2, HEIGHT // 2)
peg.radius = 40
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

lines = [line, line2, line3, line4, line5, line6]

leftMouseHeld = False

while True:
    clock.tick(300)
    dt = clock.get_time() / 5
    
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
            
        # if right mouse button is held
        if event.type == MOUSEBUTTONDOWN and event.button == 3:
            leftMouseHeld = True
            # create x1, y1 of the line
            x1, y1 = pygame.mouse.get_pos()
        # if right mouse button is released
        if event.type == MOUSEBUTTONUP and event.button == 3:
            leftMouseHeld = False
            # create x2, y2 of the line
            x2, y2 = pygame.mouse.get_pos()
            # add the line to the list of lines
            lines.append([(x1, y1), (x2, y2)])

    # fill the screen with black
    screen.fill(BLACK)

    # get the mouse position
    mouse_pos = pygame.mouse.get_pos()
    ball.pos = Vector(mouse_pos[0] - ball.radius, mouse_pos[1] - ball.radius)
    # reset the ball velocity
    ball.vel = Vector(0, 0)
    ball.acc = Vector(0, 0)
    
    # if mouse is left clicked, put ball2 at the mouse position
    if pygame.mouse.get_pressed()[0]:
        ball2.pos = Vector(mouse_pos[0] - ball2.radius, mouse_pos[1] - ball2.radius)
        ball2.vel = Vector(0, 0)
        ball2.acc = Vector(0, 0)
        

    # draw the line
    for line in lines:
        pygame.draw.line(screen, WHITE, line[0], line[1])
    
    # draw the line being created
    if leftMouseHeld:
        pygame.draw.line(screen, WHITE, (x1, y1), mouse_pos)

    # check for collision between the ball and the peg
    ballIsTouchingPeg = False
    ball2IsTouchingPeg = False
    if isBallTouchingPeg(ball.pos.x, ball.pos.y, ball.radius, peg.pos.x, peg.pos.y, peg.radius):
        ball = resolveCollision(ball, peg)
        ballIsTouchingPeg = True
    if isBallTouchingPeg(ball2.pos.x, ball2.pos.y, ball2.radius, peg.pos.x, peg.pos.y, peg.radius):
        ball2 = resolveCollision(ball2, peg)
        ball2IsTouchingPeg = True

    # check for collision between the ball and the line
    ballIsTouchingLine = False
    ball2IsTouchingLine = False
    for line in lines:
        if isBallTouchingLine(ball, line[0][0], line[0][1], line[1][0], line[1][1]):
            ball = resolveCollisionLine(ball, line)
            ballIsTouchingLine = True
        if isBallTouchingLine(ball2, line[0][0], line[0][1], line[1][0], line[1][1]):
            ball2 = resolveCollisionLine(ball2, line)
            ball2IsTouchingPeg = True
    
    if ball2.pos.y < 0:
        ball2.vel.y *= -1
    if ball2.pos.y > HEIGHT - ball2.radius:
        ball2.vel.y *= -1
    # check for collision between the ball2 and the peg
    ballIsTouchingPeg = False
    if isBallTouchingPeg(ball2.pos.x, ball2.pos.y, ball2.radius, peg.pos.x, peg.pos.y, peg.radius):
        ball2 = resolveCollision(ball2, peg)
        ballIsTouchingPeg = True
    

    # update the ball
    ball.update(dt)
    
    # update ball2
    ball2.update(dt)

    # draw the ball
    if ballIsTouchingPeg:
        pygame.draw.circle(screen, RED, (int(ball.pos.x), int(ball.pos.y)), ball.radius)
    elif ballIsTouchingLine:
        pygame.draw.circle(screen, BLUE, (int(ball.pos.x), int(ball.pos.y)), ball.radius)
    else:
        pygame.draw.circle(screen, WHITE, (int(ball.pos.x), int(ball.pos.y)), ball.radius)
        
    # draw the ball2
    if ball2IsTouchingPeg:
        pygame.draw.circle(screen, RED, (int(ball2.pos.x), int(ball2.pos.y)), ball2.radius)
    elif ballIsTouchingLine:
        pygame.draw.circle(screen, BLUE, (int(ball2.pos.x), int(ball2.pos.y)), ball2.radius)
    else:
        pygame.draw.circle(screen, WHITE, (int(ball2.pos.x), int(ball2.pos.y)), ball2.radius)
        
    # print frametime
    debugFont = pygame.font.Font(None, 20)
    frameColor = (0, 255, 0)
    frameTime = debugFont.render(
        str(clock.get_rawtime()) + " ms", False, (frameColor))
    screen.blit(frameTime, (5, 10))
    framesPerSec = debugFont.render(
        str(round(clock.get_fps())) + " fps", False, (255, 255, 255))
    screen.blit(framesPerSec, (5, 25))

    # draw the peg
    pygame.draw.circle(screen, GREEN, (int(peg.pos.x), int(peg.pos.y)), peg.radius)

    pygame.display.update()