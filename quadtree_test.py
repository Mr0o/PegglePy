# test for the quadtree module

import pygame
import random
from local.quadtree import QuadtreePegs, Rectangle
from local.peg import Peg
from local.vectors import Vector

def test_quadtree():
    # Set up the screen
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Quadtree Test")
    clock = pygame.time.Clock()

    # Set up the quadtree
    boundary = Rectangle(400, 300, 400, 300)
    quadtree = QuadtreePegs(boundary, quadtreeCapacity)

    # Create some pegs
    pegs = []
    for i in range(20):
        x = random.randint(0, 800)
        y = random.randint(0, 600)
        peg = Peg(x, y)
        pegs.append(peg)

    # Insert pegs into the quadtree
    for peg in pegs:
        quadtree.insert(peg)

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw the pegs
        screen.fill((0, 0, 0))
        query_range = Rectangle(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 50, 50)
        found = quadtree.query(query_range)
        for peg in found:
            if peg.isHit:
                pygame.draw.circle(screen, (255, 255, 255), (int(peg.pos.x), int(peg.pos.y)), peg.radius, 1)
            else:
                pygame.draw.circle(screen, (255, 0, 0), (int(peg.pos.x), int(peg.pos.y)), peg.radius, 1)
                
        # Draw the query range
        pygame.draw.rect(screen, (0, 255, 0), (query_range.x - query_range.w / 2, query_range.y - query_range.h / 2, query_range.w, query_range.h), 1)
        
        #draw the quadtree
        quadtree.show(screen)

        # Update the display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    
test_quadtree()