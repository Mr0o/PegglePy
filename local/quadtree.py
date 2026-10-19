import pygame
import random
from collections.abc import Callable
from local.peg import Peg

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
    LEAF_CAPACITY = 8
    MAX_DEPTH = 10

    def __init__(self, boundary, numPegs, depth=0):
        # boundary: Rectangle
        self.boundary: Rectangle = boundary
        self.capacity = self.LEAF_CAPACITY
        self.depth = depth
            
        self.pegs: list[Peg] = []
        self.moving_pegs: list[Peg] = []
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

        child_depth = self.depth + 1
        self.northeast = QuadtreePegs(ne, self.capacity, child_depth)
        self.northwest = QuadtreePegs(nw, self.capacity, child_depth)
        self.southeast = QuadtreePegs(se, self.capacity, child_depth)
        self.southwest = QuadtreePegs(sw, self.capacity, child_depth)
        self.divided = True

    def insert(self, peg: Peg):
        if not self.boundary.contains(peg):
            return False

        if (
            len(self.pegs) < self.capacity
            or self.depth >= self.MAX_DEPTH
            or max(self.boundary.w, self.boundary.h) <= 1
        ):
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

    def insert_many(
        self,
        pegs: list[Peg],
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> int:
        if self.pegs or getattr(self, "moving_pegs", ()) or self.divided:
            raise ValueError("insert_many requires an empty quadtree")
        self.moving_pegs = [peg for peg in pegs if peg.movement is not None]
        pegs = [peg for peg in pegs if peg.movement is None]
        if progress_callback is None:
            accepted = [peg for peg in pegs if self.boundary.contains(peg)]
            self._insert_many(accepted)
            return len(accepted) + len(self.moving_pegs)

        total_pegs = len(pegs)
        report_interval = max(1, total_pegs // 100)
        accepted = []
        if progress_callback is not None:
            progress_callback(0.0, "Preparing collision index")
        for index, peg in enumerate(pegs, start=1):
            if self.boundary.contains(peg):
                accepted.append(peg)
            if (
                progress_callback is not None
                and (index % report_interval == 0 or index == total_pegs)
            ):
                progress_callback(
                    0.1 * index / total_pegs,
                    "Preparing collision index",
                )
        last_build_percent = -1

        def report_build_progress(progress: float, status: str) -> None:
            nonlocal last_build_percent
            progress_percent = round(progress * 100)
            if progress_percent == last_build_percent:
                return
            last_build_percent = progress_percent
            progress_callback(progress, status)

        report_build_progress(0.1, "Distributing collision index")
        processed = [0]
        self._insert_many(
            accepted,
            report_build_progress,
            processed,
            len(accepted),
        )
        progress_callback(1.0, "Preparing collision index")
        return len(accepted) + len(self.moving_pegs)

    def _insert_many(
        self,
        pegs: list[Peg],
        progress_callback: Callable[[float, str], None] | None = None,
        processed: list[int] | None = None,
        total_pegs: int = 0,
    ) -> None:
        if progress_callback is not None and processed is None:
            processed = [0]
        if (
            len(pegs) <= self.capacity
            or self.depth >= self.MAX_DEPTH
            or max(self.boundary.w, self.boundary.h) <= 1
        ):
            self.pegs.extend(pegs)
            if (
                progress_callback is not None
                and processed is not None
                and total_pegs
            ):
                processed[0] += len(pegs)
                progress_callback(
                    0.1 + 0.9 * processed[0] / total_pegs,
                    "Preparing collision index",
                )
            return

        self.pegs.extend(pegs[: self.capacity])
        if (
            progress_callback is not None
            and processed is not None
            and total_pegs
        ):
            processed[0] += self.capacity
            progress_callback(
                0.1 + 0.9 * processed[0] / total_pegs,
                "Preparing collision index",
            )
        self.subdivide()
        quadrants = (
            [],
            [],
            [],
            [],
        )
        center_x = self.boundary.x
        center_y = self.boundary.y
        for peg in pegs[self.capacity :]:
            east = peg.pos.x >= center_x
            south = peg.pos.y >= center_y
            quadrant_index = (2 if south else 0) + (0 if east else 1)
            quadrants[quadrant_index].append(peg)

        for child, quadrant_pegs in zip(
            (
                self.northeast,
                self.northwest,
                self.southeast,
                self.southwest,
            ),
            quadrants,
        ):
            child._insert_many(
                quadrant_pegs,
                progress_callback,
                processed,
                total_pegs,
            )

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
            
    def query(self, range: Rectangle) -> list[Peg]:
        found = []
        self.queryInto(range, found)
        return found

    def queryInto(
        self,
        range: Rectangle,
        found: list[Peg],
        include_moving_pegs: bool = True,
    ) -> None:
        if not self.boundary.intersects(range):
            return
        for peg in self.pegs:
            if range.contains(peg):
                found.append(peg)
        if include_moving_pegs and self.depth == 0:
            self.queryMovingInto(range, self.moving_pegs, found)
        if self.divided:
            self.northeast.queryInto(range, found, include_moving_pegs)
            self.northwest.queryInto(range, found, include_moving_pegs)
            self.southeast.queryInto(range, found, include_moving_pegs)
            self.southwest.queryInto(range, found, include_moving_pegs)

    @staticmethod
    def queryMovingInto(
        range: Rectangle,
        pegs: list[Peg],
        found: list[Peg],
    ) -> None:
        left = range.x - range.w
        right = range.x + range.w
        top = range.y - range.h
        bottom = range.y + range.h
        for peg in pegs:
            radius = peg.radius
            if (
                min(peg.previousPos.x, peg.pos.x) - radius <= right
                and max(peg.previousPos.x, peg.pos.x) + radius >= left
                and min(peg.previousPos.y, peg.pos.y) - radius <= bottom
                and max(peg.previousPos.y, peg.pos.y) + radius >= top
            ):
                found.append(peg)

    def remove(self, peg: Peg) -> bool:
        for index, stored_peg in enumerate(getattr(self, "moving_pegs", ())):
            if stored_peg is peg:
                del self.moving_pegs[index]
                return True
        for index, stored_peg in enumerate(self.pegs):
            if stored_peg is peg:
                del self.pegs[index]
                return True
        if self.divided:
            return (
                self.northeast.remove(peg)
                or self.northwest.remove(peg)
                or self.southeast.remove(peg)
                or self.southwest.remove(peg)
            )
        return False

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