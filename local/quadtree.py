import pygame
import random
from local.peg import Peg
from local.vectors import Vector

# ------------------------------
# Quadtree support classes
# ------------------------------

class Rectangle:
    def __init__(self, x, y, w, h):
        # Center coordinates and half dimensions
        self.x = x
        self.y = y
        self.w = w  # half-width
        self.h = h  # half-height

    def contains(self, peg: Peg):
        # point is expected to have a pos attribute of type Vector
        return (peg.pos.x >= self.x - self.w and
                peg.pos.x < self.x + self.w and
                peg.pos.y >= self.y - self.h and
                peg.pos.y < self.y + self.h)

    def intersects(self, range):
        # range: another Rectangle
        return not (range.x - range.w > self.x + self.w or
                    range.x + range.w < self.x - self.w or
                    range.y - range.h > self.y + self.h or
                    range.y + range.h < self.y - self.h)

class QuadtreePegs:
    def __init__(self, boundary, capacity):
        # boundary: Rectangle
        self.boundary: Rectangle = boundary
        self.capacity = capacity  # maximum number of pegs before subdivision
        self.pegs: list[Peg] = []
        self.divided = False

    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w / 2
        h = self.boundary.h / 2

        ne = Rectangle(x + w, y - h, w, h)
        nw = Rectangle(x - w, y - h, w, h)
        se = Rectangle(x + w, y + h, w, h)
        sw = Rectangle(x - w, y + h, w, h)

        self.northeast = QuadtreePegs(ne, self.capacity)
        self.northwest = QuadtreePegs(nw, self.capacity)
        self.southeast = QuadtreePegs(se, self.capacity)
        self.southwest = QuadtreePegs(sw, self.capacity)
        self.divided = True

    def insert(self, peg: Peg):
        if not self.boundary.contains(peg):
            return False

        if len(self.pegs) < self.capacity:
            self.pegs.append(peg)
            return True
        else:
            if not self.divided:
                self.subdivide()

            if self.northeast.insert(peg): return True
            if self.northwest.insert(peg): return True
            if self.southeast.insert(peg): return True
            if self.southwest.insert(peg): return True

        return False

    def show(self, surface):
        # Draw the boundary rectangle (convert half dimensions to full width, height)
        rect = pygame.Rect(self.boundary.x - self.boundary.w, 
                           self.boundary.y - self.boundary.h, 
                           self.boundary.w * 2, 
                           self.boundary.h * 2)
        pygame.draw.rect(surface, (255, 255, 255), rect, 1)  # white outline

        if self.divided:
            self.northeast.show(surface)
            self.northwest.show(surface)
            self.southeast.show(surface)
            self.southwest.show(surface)
            
    def query(self, range: Rectangle):
        found = []
        if not self.boundary.intersects(range):
            return found
        else:
            for peg in self.pegs:
                if range.contains(peg):
                    found.append(peg)
            if self.divided:
                found.extend(self.northeast.query(range))
                found.extend(self.northwest.query(range))
                found.extend(self.southeast.query(range))
                found.extend(self.southwest.query(range))
        return found

# ------------------------------
# Simulation: Ball class
# ------------------------------

# Simulation constants
WIDTH, HEIGHT = 800, 600
NUM_BALLS = 1000
QT_CAPACITY = 4
FPS = 60


# ------------------------------
# Main simulation loop
# ------------------------------

def main():
    from ball import Ball
    from peg import Peg
    
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Quadtree Visualization")
    clock = pygame.time.Clock()

    # Create 1000 balls
    balls = [Ball(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
             for _ in range(NUM_BALLS)]

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update ball positions
        for ball in balls:
            ball.update()

        # Build the quadtree each frame over the entire screen
        boundary = Rectangle(WIDTH/2, HEIGHT/2, WIDTH/2, HEIGHT/2)
        qt = QuadtreePegs(boundary, QT_CAPACITY)
        for ball in balls:
            qt.insert(ball)

        # Draw everything
        screen.fill((0, 0, 0))  # Black background

        # Draw the quadtree partitions
        qt.show(screen)

        # Draw all balls
        for ball in balls:
            ball.draw(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()