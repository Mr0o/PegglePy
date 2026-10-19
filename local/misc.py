import pygame
from math import sqrt
from collections.abc import Callable
from functools import lru_cache
from weakref import WeakKeyDictionary

### local imports ###
from local.config import baseTimeScale
from local.userConfig import configs
from local.resources import backgroundImg, bluePegImg, orangePegImg, greenPegImg
from local.resources import hitBluePegImg, hitOrangePegImg, hitGreenPegImg
from local.peg import Peg
from local.ball import Ball
from local.audio import newSong
from local.quadtree import QuadtreePegs, Rectangle


_PEG_IMAGES = {
    "orange": (orangePegImg, hitOrangePegImg),
    "green": (greenPegImg, hitGreenPegImg),
    "blue": (bluePegImg, hitBluePegImg),
}
_MOVING_PEG_IMAGES: dict[int, pygame.Surface] = {}


@lru_cache(maxsize=4)
def _scaled_background(bg_img: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    return pygame.transform.scale(bg_img, size)


def _peg_image(peg: Peg) -> pygame.Surface:
    normal, hit = _PEG_IMAGES.get(peg.color, _PEG_IMAGES["blue"])
    image = hit if peg.isHit else normal
    if peg.movement is None:
        return image
    moving_image = _MOVING_PEG_IMAGES.get(id(image))
    if moving_image is None:
        moving_image = image.copy()
        tint = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        tint.fill((0, 28, 42, 0))
        moving_image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        _MOVING_PEG_IMAGES[id(image)] = moving_image
    return moving_image


def _peg_image_rect(peg: Peg) -> pygame.Rect:
    image = _peg_image(peg)
    return pygame.Rect(
        peg.pos.x - peg.posAdjust,
        peg.pos.y - peg.posAdjust,
        image.get_width(),
        image.get_height(),
    )


class _StaticImageState:
    CELL_SIZE = 64

    def __init__(
        self,
        surface: pygame.Surface,
        background: pygame.Surface,
        pegs: list[Peg],
        progress_callback: Callable[[float, str], None] | None = None,
    ):
        self.surface_rect = surface.get_rect()
        self.background = background
        self.active: dict[int, Peg] = {}
        self.cells: dict[tuple[int, int], list[Peg]] = {}
        self.peg_cells: dict[int, tuple[tuple[int, int], ...]] = {}
        self.peg_rects: dict[int, pygame.Rect] = {}
        self.order: dict[int, int] = {}
        self.next_order = 0
        if progress_callback is None:
            for peg in pegs:
                self._index(peg)
        else:
            total_pegs = len(pegs)
            report_interval = max(1, total_pegs // 100)
            for index, peg in enumerate(pegs, start=1):
                self._index(peg)
                if index % report_interval == 0 or index == total_pegs:
                    progress_callback(
                        0.7 + 0.3 * index / total_pegs,
                        "Preparing peg data",
                    )
            if not total_pegs:
                progress_callback(1.0, "Rendering level...")

    def _image_rect(self, peg: Peg) -> pygame.Rect:
        return _peg_image_rect(peg)

    def _cells_for_rect(self, rect: pygame.Rect) -> tuple[tuple[int, int], ...]:
        visible = rect.clip(self.surface_rect)
        if visible.width <= 0 or visible.height <= 0:
            return ()
        left = visible.left // self.CELL_SIZE
        right = (visible.right - 1) // self.CELL_SIZE
        top = visible.top // self.CELL_SIZE
        bottom = (visible.bottom - 1) // self.CELL_SIZE
        return tuple(
            (cell_x, cell_y)
            for cell_y in range(top, bottom + 1)
            for cell_x in range(left, right + 1)
        )

    def _index(self, peg: Peg) -> None:
        peg_id = id(peg)
        if peg_id not in self.order:
            self.order[peg_id] = self.next_order
            self.next_order += 1
        self.active[peg_id] = peg
        image_rect = self._image_rect(peg)
        self.peg_rects[peg_id] = image_rect
        cells = self._cells_for_rect(image_rect)
        self.peg_cells[peg_id] = cells
        for cell in cells:
            self.cells.setdefault(cell, []).append(peg)

    def update(
        self,
        surface: pygame.Surface,
        changed_pegs: list[Peg],
        removed_pegs: list[Peg] = (),
    ) -> None:
        dirty_rects: list[pygame.Rect] = []

        removed_by_id: dict[int, Peg] = {}
        for peg in removed_pegs:
            peg_id = id(peg)
            if peg_id in self.active:
                removed_by_id[peg_id] = peg

        changed_ids: set[int] = set()
        changed_to_index: list[Peg] = []
        cells_to_filter: set[tuple[int, int]] = set()
        for peg_id in removed_by_id:
            dirty_rects.append(self.peg_rects.pop(peg_id))
            cells = self.peg_cells.pop(peg_id, ())
            cells_to_filter.update(cells)
            self.active.pop(peg_id, None)
            self.order.pop(peg_id, None)

        removed_ids = set(removed_by_id)
        for peg in changed_pegs:
            peg_id = id(peg)
            if peg_id in removed_ids or peg_id in changed_ids:
                continue
            changed_ids.add(peg_id)
            old_rect = self.peg_rects.pop(peg_id, None)
            if old_rect is not None:
                dirty_rects.append(old_rect)
            old_cells = self.peg_cells.pop(peg_id, ())
            cells_to_filter.update(old_cells)
            changed_to_index.append(peg)

        for cell in cells_to_filter:
            pegs_in_cell = self.cells[cell]
            remaining = [
                peg
                for peg in pegs_in_cell
                if id(peg) not in changed_ids
                and id(peg) not in removed_ids
            ]
            if remaining:
                self.cells[cell] = remaining
            else:
                del self.cells[cell]

        for peg in changed_to_index:
            self._index(peg)
            dirty_rects.append(self.peg_rects[id(peg)])

        for region in self._merge_dirty_rects(dirty_rects):
            surface.blit(self.background, region, region)
            candidate_ids: set[int] = set()
            for cell in self._cells_for_rect(region):
                candidate_ids.update(
                    id(peg) for peg in self.cells.get(cell, ())
                )
            candidates = sorted(
                (self.active[peg_id] for peg_id in candidate_ids),
                key=lambda item: self.order[id(item)],
            )
            for peg in candidates:
                image = _peg_image(peg)
                image_rect = self.peg_rects[id(peg)]
                clipped = image_rect.clip(region)
                if clipped.width and clipped.height:
                    source_rect = pygame.Rect(
                        clipped.x - image_rect.x,
                        clipped.y - image_rect.y,
                        clipped.width,
                        clipped.height,
                    )
                    surface.blit(
                        image,
                        clipped.topleft,
                        source_rect,
                    )

    def _merge_dirty_rects(
        self, dirty_rects: list[pygame.Rect]
    ) -> list[pygame.Rect]:
        merged: list[pygame.Rect] = []
        for dirty_rect in dirty_rects:
            region = dirty_rect.clip(self.surface_rect)
            if region.width <= 0 or region.height <= 0:
                continue
            index = 0
            while index < len(merged):
                if region.colliderect(merged[index]):
                    region.union_ip(merged.pop(index))
                    index = 0
                else:
                    index += 1
            merged.append(region)
        return merged


_static_image_states: WeakKeyDictionary[
    pygame.Surface, _StaticImageState
] = WeakKeyDictionary()


# create a static image of the background and pegs, this avoids redrawing the background and pegs every frame
# -- dramatic performance improvement especially in levels with lots of pegs
def _stationary_pegs(pegs: list[Peg]) -> list[Peg]:
    return [peg for peg in pegs if getattr(peg, "movement", None) is None]


def drawMovingPegs(
    surface: pygame.Surface,
    pegs: list[Peg],
    interpolation_alpha: float = 1.0,
) -> None:
    alpha = min(max(interpolation_alpha, 0.0), 1.0)
    blit = surface.blit
    for peg in pegs:
        if peg.movement is None or not peg.isVisible:
            continue
        x = peg.previousPos.x + (peg.pos.x - peg.previousPos.x) * alpha
        y = peg.previousPos.y + (peg.pos.y - peg.previousPos.y) * alpha
        blit(
            _peg_image(peg),
            (round(x - peg.posAdjust), round(y - peg.posAdjust)),
        )


def createStaticImage(
    pegs: list[Peg],
    bgImg=backgroundImg,
    *,
    track_changes: bool = True,
    progress_callback: Callable[[float, str], None] | None = None,
):
    staticImg = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]))
    static_pegs = _stationary_pegs(pegs)

    # draw background
    size = (configs["WIDTH"], configs["HEIGHT"])
    scaled_background = _scaled_background(bgImg, size)
    staticImg.blit(scaled_background, (0, 0))

    # draw pegs
    blit = staticImg.blit
    if progress_callback is None:
        for peg in static_pegs:
            blit(
                _peg_image(peg),
                _peg_image_rect(peg).topleft,
            )
    else:
        total_pegs = len(static_pegs)
        report_interval = max(1, total_pegs // 100)
        progress_callback(0.0, "Rendering pegs")
        for index, peg in enumerate(static_pegs, start=1):
            blit(
                _peg_image(peg),
                _peg_image_rect(peg).topleft,
            )
            if index % report_interval == 0 or index == total_pegs:
                progress_callback(
                    0.7 * index / total_pegs,
                    "Rendering pegs",
                )

    if track_changes:
        if progress_callback is not None:
            progress_callback(0.7, "Preparing peg data")
        _static_image_states[staticImg] = _StaticImageState(
            staticImg,
            scaled_background,
            static_pegs,
            progress_callback=progress_callback,
        )
    elif progress_callback is not None:
        progress_callback(1.0, "Rendering level...")

    # anti-aliasing
    # staticImg = pygame.transform.smoothscale(staticImg, (configs["WIDTH"], configs["HEIGHT"]))

    return staticImg


# blit a single peg to the static image rather than redrawing the entire image (this may not look correct if the peg is overlapping another peg)
def updateStaticImage(staticImg: pygame.Surface, peg: Peg):
    state = _static_image_states.get(staticImg)
    if state is None:
        image_rect = _peg_image_rect(peg)
        staticImg.blit(
            _peg_image(peg),
            image_rect.topleft,
        )
    else:
        state.update(staticImg, [peg])

    return staticImg


def updateStaticImagePegs(
    staticImg: pygame.Surface,
    pegs: list[Peg],
    changed_pegs: list[Peg],
    removed_pegs: list[Peg] = (),
) -> pygame.Surface:
    state = _static_image_states.get(staticImg)
    if state is None:
        return createStaticImage(pegs)
    static_pegs = _stationary_pegs(pegs)
    static_changed_pegs = _stationary_pegs(changed_pegs)
    static_removed_pegs = _stationary_pegs(list(removed_pegs))
    update_count = len(static_changed_pegs) + len(static_removed_pegs)
    rebuild_threshold = (
        152 if len(state.active) > 5000 else max(256, len(state.active) // 8)
    )
    if update_count > rebuild_threshold:
        return createStaticImage(static_pegs)
    state.update(staticImg, static_changed_pegs, static_removed_pegs)
    return staticImg


# create a static image of cicles used when debugging (zenball trajectory, to be specific)
def createStaticCircles(
    trajectory: list[Ball],
    marker_points: tuple[
        tuple[float, float], tuple[float, float]
    ] | None = None,
) -> pygame.Surface:
    staticCircles = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]))

    # surface is transparent
    staticCircles.set_colorkey((0, 0, 0))

    for fb in trajectory:
        pygame.draw.circle(staticCircles, (0, 220, 10), [fb.pos.x, fb.pos.y], 1)

    if marker_points is not None:
        for point in marker_points:
            pygame.draw.circle(staticCircles, (255, 40, 40), point, 8)

    return staticCircles


# Reset the mutable game state while preserving the legacy return contract.
def resetGame(balls, createPegColors, bucket, pegs, originPegs, quadtree):
    if balls:
        ball = balls[0]
        ball.originX = configs["WIDTH"] / 2
        ball.originY = configs["HEIGHT"] / 25
        balls[:] = [ball]
    else:
        ball = Ball(configs["WIDTH"] / 2, configs["HEIGHT"] / 25)
        balls.append(ball)
    ball.reset()
    pitch = 1.0
    pitchRaiseCount = 0
    powerUpActive = False
    powerUpCount = 0
    pegs.clear()
    pegs = originPegs.copy()
    for peg in pegs:
        peg.reset()
    pegs = createPegColors(pegs)
    orangeCount = sum(peg.color == "orange" for peg in pegs)
    score = 0
    ballsRemaining = 10
    pegsHit = 0
    bucket.reset()
    gameOver = False
    alreadyPlayedOdeToJoy = False
    timeScale = baseTimeScale
    longShotBonus = False
    newSong()
    staticImage = createStaticImage(pegs)
    boundary = Rectangle(
        configs["WIDTH"] / 2,
        configs["HEIGHT"] / 2,
        configs["WIDTH"] / 2,
        configs["HEIGHT"] / 2,
    )
    quadtree = QuadtreePegs(boundary, len(pegs))
    quadtree.insert_many(pegs)
    return (
        ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount,
        ball, score, pegsHit, pegs, orangeCount, gameOver,
        alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree,
    )


def distBetweenTwoPoints(x1, y1, x2, y2):
    return sqrt(((x1-x2)**2) + ((y1-y2)**2))
