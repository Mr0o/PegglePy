import math
import sys
import time  # used to exit the program immediately
from typing import Protocol

import pygame  # used for input, audio and graphics

from random import randint

##### local imports #####
from local.config import configs
from local.config import pegRad
from local.userConfig import configs
from local.loadLevel import loadData, saveData
from local.collision import isBallTouchingPeg
from local.peg import Peg
from local.ball import Ball
from local.misc import createStaticImage, updateStaticImage, drawMovingPegs
from local.moving_peg import (
    DEFAULT_MOVING_PEG_SPEED,
    MIN_MOVING_PEG_SPEED,
    MovingPegPath,
)
from local.editor_tools import SHAPE_TOOLS, generate_shape_points, resample_polyline
from local.triggerEvents import TimedEvent
from local.audio import playSoundPitch, loadRandMusic, playMusic, stopMusic, setMusicVolume, newSong
from local.resources import editorIconImg, backgroundImg, infoFont, warnFont, helpFont, transparentPegImg, invalidPegImg, newPegSound, invalidPegSound, debugFont
from local.vectors import Vector

from menu import getEditorPauseScreen
from loadLevelMenu import loadLevelMenu


class EditorClock(Protocol):
    def tick(self, framerate: float = 0, /) -> int: ...
    def get_time(self) -> int: ...
    def get_rawtime(self) -> int: ...
    def get_fps(self) -> float: ...


## the level editor function (called from run.py via the user menu selection) ##
def levelEditor(
    screen: pygame.Surface,
    clock: EditorClock,
    standalone: bool = False,
    pegs: list[Peg] | None = None,
) -> tuple[str, list[Peg]]:
    pegs = [] if pegs is None else pegs
    # warning timer for displaying warning messages
    warningTimer = TimedEvent()
    savedTimer = TimedEvent()

    tempPeg = Peg(0, 0)
    isRunning = True
    editorPaused = False

    # reset the pegs
    for peg in pegs:
        peg.reset()

    staticImg = createStaticImage(pegs)

    skipValidPegCheck = False
    validNewPegPos = True
    mouseOutofBounds = False

    widthBound = 35
    heightBound = 150
    lowerHeightBound = 75
    movingPegMode = False
    movingPegEditMode = False
    activeTool = "peg"
    movingPegSpeed = DEFAULT_MOVING_PEG_SPEED
    movingPegPointCount = 4
    movingPegEasing = "linear"
    movingPegTraversal = "ping-pong"
    movingPegPreviewEnabled = False
    movingPegPreviewScope = "selected"
    pathPoints: list[tuple[float, float]] = []
    selectedMovingPeg: Peg | None = None
    selectedControlPoint: int | None = None
    selectedPeg: Peg | None = None
    draggingPeg = False
    dragLastPosition: tuple[int, int] | None = None
    shapeMenuOpen = False
    movingMenuOpen = False
    selectedShape = "Line"
    shapeDragStart: tuple[int, int] | None = None
    shapeDragCurrent: tuple[int, int] | None = None
    freehandPoints: list[tuple[float, float]] = []
    shapeDragActive = False
    toolbarButtons = [
        ("Select", pygame.Rect(10, 70, 78, 30)),
        ("Peg", pygame.Rect(92, 70, 68, 30)),
        ("Moving v", pygame.Rect(164, 70, 88, 30)),
        ("Erase", pygame.Rect(256, 70, 70, 30)),
        ("Shapes v", pygame.Rect(330, 70, 104, 30)),
        ("Save", pygame.Rect(438, 70, 68, 30)),
        ("Load", pygame.Rect(510, 70, 68, 30)),
        ("Path", pygame.Rect(582, 70, 82, 30)),
    ]
    shapeMenuButtons = [
        (shape, pygame.Rect(330, 102 + index * 25, 120, 24))
        for index, shape in enumerate(SHAPE_TOOLS)
    ]
    movingMenuRect = pygame.Rect(160, 100, 164, 154)
    movingPointMinusButton = pygame.Rect(164, 104, 30, 24)
    movingPointPlusButton = pygame.Rect(286, 104, 30, 24)
    movingPreviewButton = pygame.Rect(164, 134, 152, 24)
    movingScopeButton = pygame.Rect(164, 164, 152, 24)
    movingTraversalButton = pygame.Rect(164, 194, 152, 24)
    movingEasingButton = pygame.Rect(164, 224, 152, 24)

    def add_static_pegs(points: list[tuple[float, float]]) -> int:
        nonlocal staticImg
        spacing_squared = (pegRad * 2) ** 2
        added = 0
        for x, y in points:
            if not (
                widthBound + pegRad <= x <= configs["WIDTH"] - widthBound - pegRad
                and heightBound + pegRad <= y <= configs["HEIGHT"] - lowerHeightBound - pegRad
            ):
                continue
            if any(
                (peg.pos.x - x) ** 2 + (peg.pos.y - y) ** 2 < spacing_squared
                for peg in pegs
            ):
                continue
            peg = Peg(round(x), round(y))
            pegs.append(peg)
            added += 1
        if added:
            staticImg = createStaticImage(pegs)
        return added

    pygame.display.set_caption("PegglePy  -  Level Editor")

    #unhide the mouse
    pygame.mouse.set_visible(True)

    if configs["MUSIC_ENABLED"]:
        # play random music
        loadRandMusic()
        playMusic()
        setMusicVolume(configs["MUSIC_VOLUME"])

    ##### main loop #####
    while isRunning:
        for event in pygame.event.get():  # check events and quit if the program is closed
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    pegs = []
                    staticImg = createStaticImage(pegs)
                    selectedMovingPeg = None
                    selectedControlPoint = None
                    selectedPeg = None
                    pathPoints.clear()
                # save level
                if event.key == pygame.K_s:
                    if len(pegs) == 0 or len(pegs) < 30:
                        print(
                            "WARN: Level must have at least 30 pegs before it is saved...")
                        # start the warning timer to display the message for 4 seconds
                        warningTimer.setTimer(4)
                    else:
                        saveData(pegs)
                        savedTimer.setTimer(4)
                # load level
                if event.key == pygame.K_l:
                    pegs, originPegs, orangeCount, filePath = loadLevelMenu(screen, configs["DEBUG_MODE"])
                    selectedMovingPeg = None
                    selectedControlPoint = None
                    selectedPeg = None
                    pathPoints.clear()
                    # reset the pegs
                    for peg in pegs:
                        peg.reset()
                    staticImg = createStaticImage(pegs)
                    # play random music
                    

                if event.key == pygame.K_1:
                    configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
                if event.key == pygame.K_2:
                    skipValidPegCheck = not skipValidPegCheck
                # print all the peg positions (x,y) to the terminal
                if event.key == pygame.K_p:
                    print("Pegs:")
                    pegsPos = []
                    for peg in pegs:
                        pegsPos.append((peg.pos.x, peg.pos.y))
                    print(pegsPos)
                # return when the escape key is pressed
                if event.key == pygame.K_ESCAPE:
                    editorPaused = not editorPaused
                if event.key == pygame.K_m:
                    movingPegMode = not movingPegMode
                    movingPegEditMode = False
                    movingMenuOpen = False
                    activeTool = "moving" if movingPegMode else "peg"
                    pathPoints.clear()
                    selectedMovingPeg = None
                if event.key == pygame.K_e:
                    movingPegEditMode = not movingPegEditMode
                    movingPegMode = False
                    activeTool = "path_edit" if movingPegEditMode else "select"
                    pathPoints.clear()
                    selectedControlPoint = None
                if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    if selectedMovingPeg is not None and selectedMovingPeg.movement is not None:
                        selectedMovingPeg.movement.speed += 0.5
                if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    if selectedMovingPeg is not None and selectedMovingPeg.movement is not None:
                        selectedMovingPeg.movement.speed = max(
                            MIN_MOVING_PEG_SPEED,
                            selectedMovingPeg.movement.speed - 0.5,
                        )

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not editorPaused:
                toolbar_hit = next(
                    (name for name, rect in toolbarButtons if rect.collidepoint(event.pos)),
                    None,
                )
                if toolbar_hit is not None:
                    if toolbar_hit == "Select":
                        activeTool = "select"
                        movingPegMode = False
                        movingPegEditMode = False
                        shapeMenuOpen = False
                        movingMenuOpen = False
                    elif toolbar_hit == "Peg":
                        activeTool = "peg"
                        movingPegMode = False
                        movingPegEditMode = False
                        shapeMenuOpen = False
                        movingMenuOpen = False
                    elif toolbar_hit == "Moving v":
                        activeTool = "moving"
                        movingPegMode = True
                        movingPegEditMode = False
                        shapeMenuOpen = False
                        movingMenuOpen = not movingMenuOpen
                        pathPoints.clear()
                    elif toolbar_hit == "Path":
                        activeTool = "path_edit"
                        movingPegMode = False
                        movingPegEditMode = True
                        shapeMenuOpen = False
                        movingMenuOpen = False
                    elif toolbar_hit == "Erase":
                        activeTool = "erase"
                        movingPegMode = False
                        movingPegEditMode = False
                        shapeMenuOpen = False
                        movingMenuOpen = False
                    elif toolbar_hit == "Shapes v":
                        shapeMenuOpen = not shapeMenuOpen
                        movingMenuOpen = False
                    elif toolbar_hit == "Save":
                        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_s))
                    elif toolbar_hit == "Load":
                        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_l))
                    continue

                if movingMenuOpen:
                    if movingPointMinusButton.collidepoint(event.pos):
                        movingPegPointCount = max(2, movingPegPointCount - 1)
                        pathPoints.clear()
                        continue
                    if movingPointPlusButton.collidepoint(event.pos):
                        movingPegPointCount = min(12, movingPegPointCount + 1)
                        pathPoints.clear()
                        continue
                    if movingPreviewButton.collidepoint(event.pos):
                        movingPegPreviewEnabled = not movingPegPreviewEnabled
                        continue
                    if movingScopeButton.collidepoint(event.pos):
                        movingPegPreviewScope = (
                            "all" if movingPegPreviewScope == "selected" else "selected"
                        )
                        continue
                    if movingTraversalButton.collidepoint(event.pos):
                        traversal_options = MovingPegPath.TRAVERSAL_TYPES
                        current_traversal = (
                            selectedMovingPeg.movement.traversal
                            if selectedMovingPeg is not None
                            and selectedMovingPeg.movement is not None
                            else movingPegTraversal
                        )
                        movingPegTraversal = traversal_options[
                            (traversal_options.index(current_traversal) + 1)
                            % len(traversal_options)
                        ]
                        if selectedMovingPeg is not None and selectedMovingPeg.movement is not None:
                            selectedMovingPeg.movement.set_motion_options(
                                selectedMovingPeg.movement.easing,
                                movingPegTraversal,
                            )
                            selectedMovingPeg.set_movement(selectedMovingPeg.movement)
                        continue
                    if movingEasingButton.collidepoint(event.pos):
                        easing_options = MovingPegPath.EASING_TYPES
                        current_easing = (
                            selectedMovingPeg.movement.easing
                            if selectedMovingPeg is not None
                            and selectedMovingPeg.movement is not None
                            else movingPegEasing
                        )
                        movingPegEasing = easing_options[
                            (easing_options.index(current_easing) + 1)
                            % len(easing_options)
                        ]
                        if selectedMovingPeg is not None and selectedMovingPeg.movement is not None:
                            selectedMovingPeg.movement.set_motion_options(
                                movingPegEasing,
                                selectedMovingPeg.movement.traversal,
                            )
                            selectedMovingPeg.set_movement(selectedMovingPeg.movement)
                        continue
                    if movingMenuRect.collidepoint(event.pos):
                        continue
                    movingMenuOpen = False

                if shapeMenuOpen:
                    shape_selection = next(
                        (
                            shape
                            for shape, rect in shapeMenuButtons
                            if rect.collidepoint(event.pos)
                        ),
                        None,
                    )
                    if shape_selection is not None:
                        selectedShape = shape_selection
                        activeTool = "shape"
                        movingPegMode = False
                        movingPegEditMode = False
                        shapeMenuOpen = False
                        movingMenuOpen = False
                        continue
                    if not any(rect.collidepoint(event.pos) for _, rect in shapeMenuButtons):
                        shapeMenuOpen = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if activeTool == "shape" and not editorPaused:
                    if (
                        widthBound <= event.pos[0] <= configs["WIDTH"] - widthBound
                        and heightBound <= event.pos[1] <= configs["HEIGHT"] - lowerHeightBound
                    ):
                        shapeDragStart = event.pos
                        shapeDragCurrent = event.pos
                        freehandPoints = [tuple(map(float, event.pos))]
                        shapeDragActive = True
                elif activeTool == "erase" and not editorPaused:
                    erase_x, erase_y = event.pos
                    selectedPegs = [
                        peg
                        for peg in pegs
                        if (peg.pos.x - erase_x) ** 2 + (peg.pos.y - erase_y) ** 2
                        <= peg.radius**2
                    ]
                    for selectedPeg in selectedPegs:
                        pegs.remove(selectedPeg)
                    if selectedPegs:
                        if selectedMovingPeg in selectedPegs:
                            selectedMovingPeg = None
                        if selectedPeg in selectedPegs:
                            selectedPeg = None
                        staticImg = createStaticImage(pegs)
                elif activeTool == "select" and not editorPaused:
                    mx_event, my_event = event.pos
                    selectedPeg = next(
                        (
                            peg
                            for peg in reversed(pegs)
                            if (peg.pos.x - mx_event) ** 2 + (peg.pos.y - my_event) ** 2
                            <= peg.radius**2
                        ),
                        None,
                    )
                    if selectedPeg is not None:
                        selectedMovingPeg = selectedPeg if selectedPeg.movement is not None else None
                        draggingPeg = True
                        dragLastPosition = event.pos
                elif movingPegMode and not editorPaused:
                    point = (float(event.pos[0]), float(event.pos[1]))
                    if (
                        widthBound <= point[0] <= configs["WIDTH"] - widthBound
                        and heightBound <= point[1] <= configs["HEIGHT"] - lowerHeightBound
                    ):
                        pathPoints.append(point)
                        if len(pathPoints) == movingPegPointCount:
                            try:
                                newPeg = Peg(*pathPoints[0])
                                newPeg.set_movement(
                                    MovingPegPath(
                                        pathPoints,
                                        movingPegSpeed,
                                        curve_type="catmull-rom",
                                        easing=movingPegEasing,
                                        traversal=movingPegTraversal,
                                    )
                                )
                                pegs.append(newPeg)
                                selectedMovingPeg = newPeg
                            except ValueError as error:
                                print(f"WARN: Unable to create moving peg: {error}")
                            pathPoints.clear()
                elif movingPegEditMode and not editorPaused:
                    mx_event, my_event = event.pos
                    nearest = None
                    nearest_distance = float("inf")
                    for peg in pegs:
                        if peg.movement is None:
                            continue
                        for point_index, (px, py) in enumerate(peg.movement.points):
                            distance = (px - mx_event) ** 2 + (py - my_event) ** 2
                            if distance < nearest_distance:
                                nearest = (peg, point_index)
                                nearest_distance = distance
                    if nearest is not None and nearest_distance <= (tempPeg.radius * 2) ** 2:
                        selectedMovingPeg, selectedControlPoint = nearest
            if event.type == pygame.MOUSEMOTION and shapeDragActive:
                shapeDragCurrent = event.pos
                if selectedShape == "Freehand":
                    point = (float(event.pos[0]), float(event.pos[1]))
                    if not freehandPoints or math.hypot(
                        point[0] - freehandPoints[-1][0],
                        point[1] - freehandPoints[-1][1],
                    ) >= 5:
                        freehandPoints.append(point)
            if (
                event.type == pygame.MOUSEMOTION
                and draggingPeg
                and selectedPeg is not None
                and dragLastPosition is not None
            ):
                dx = event.pos[0] - dragLastPosition[0]
                dy = event.pos[1] - dragLastPosition[1]
                if dx or dy:
                    selectedPeg.translate(dx, dy)
                    if selectedPeg.movement is None:
                        staticImg = updateStaticImage(staticImg, selectedPeg)
                    dragLastPosition = event.pos
            if (
                event.type == pygame.MOUSEMOTION
                and movingPegEditMode
                and selectedMovingPeg is not None
                and selectedControlPoint is not None
                and pygame.mouse.get_pressed()[0]
                and widthBound <= event.pos[0] <= configs["WIDTH"] - widthBound
                and heightBound <= event.pos[1] <= configs["HEIGHT"] - lowerHeightBound
            ):
                edited_points = list(selectedMovingPeg.movement.points)
                edited_points[selectedControlPoint] = (
                    float(event.pos[0]),
                    float(event.pos[1]),
                )
                try:
                    selectedMovingPeg.movement.set_points(edited_points)
                    selectedMovingPeg.set_movement(selectedMovingPeg.movement)
                except ValueError as error:
                    print(f"WARN: Unable to edit moving peg path: {error}")
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                selectedControlPoint = None
                draggingPeg = False
                dragLastPosition = None
                if shapeDragActive and shapeDragStart is not None and shapeDragCurrent is not None:
                    spacing = max(float(pegRad * 2.5), 8.0)
                    if selectedShape == "Freehand":
                        release_point = tuple(map(float, event.pos))
                        if not freehandPoints or math.hypot(
                            release_point[0] - freehandPoints[-1][0],
                            release_point[1] - freehandPoints[-1][1],
                        ) > 0:
                            freehandPoints.append(release_point)
                        points = resample_polyline(freehandPoints, spacing)
                    else:
                        points = generate_shape_points(
                            selectedShape,
                            (
                                float(shapeDragStart[0]),
                                float(shapeDragStart[1]),
                                float(shapeDragCurrent[0]),
                                float(shapeDragCurrent[1]),
                            ),
                            spacing,
                        )
                    added_count = add_static_pegs(points)
                    if added_count:
                        selectedPeg = None
                shapeDragActive = False
                shapeDragStart = None
                shapeDragCurrent = None
                freehandPoints = []

            # invalid position, play sound but only on mouse click (button down event)
            if event.type == pygame.MOUSEBUTTONDOWN and mouseOutofBounds:
                if event.button == 1 and not editorPaused:
                    if configs["SOUND_ENABLED"]:
                        playSoundPitch(invalidPegSound, 0.35)

        if movingPegPreviewEnabled and not editorPaused:
            if movingPegPreviewScope == "all":
                preview_pegs = [
                    peg for peg in pegs if peg.movement is not None
                ]
            elif selectedMovingPeg is not None and selectedMovingPeg.movement is not None:
                preview_pegs = [selectedMovingPeg]
            else:
                preview_pegs = []
            # Match run.py's clock-to-physics-time scaling for gameplay-speed preview.
            preview_delta = max(0.0, clock.get_time() / 5.0)
            for preview_peg in preview_pegs:
                preview_peg.update_movement(preview_delta)


         # get current mouse state
        mouseClicked = pygame.mouse.get_pressed()  # get the mouse click state
        mx, my = pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'
        mousePos = Vector(mx, my)


        ##### update #####
        if not editorPaused:
            # check if mouse is out of bounds
            mouseOutofBounds = False
            if mousePos.y > configs["HEIGHT"] - lowerHeightBound or mousePos.y < heightBound or mousePos.x > configs["WIDTH"] - widthBound or mousePos.x < widthBound:
                mouseOutofBounds = True

            # if mouse clicked, create a new ball at the mouse position
            if mouseClicked[0] and activeTool == "peg":
                validNewPegPos = True
                if not skipValidPegCheck:
                    # check if mouse is out of bounds
                    if mouseOutofBounds:
                        validNewPegPos = False
                    # check if mouse is touching any other already existing pegs
                    else:
                        for peg in pegs:
                            mouseBall = Ball(mousePos.x, mousePos.y)
                            mouseBall.radius = peg.radius/6
                            if isBallTouchingPeg(mouseBall, peg, 1):
                                validNewPegPos = False
                                break

                else:
                    validNewPegPos = True
                    # for peg in pegs:
                    #     if isBallTouchingPeg(mousePos.x, mousePos.y, peg.radius/6, peg.pos.x, peg.pos.y, peg.radius/6):
                    #         validNewPegPos = False
                    #         break

                # valid position, add peg
                if validNewPegPos:
                    newPeg = Peg(mousePos.x, mousePos.y)
                    pegs.append(newPeg)
                    staticImg = updateStaticImage(staticImg, newPeg)
                    # play sound
                    if configs["SOUND_ENABLED"]:
                        playSoundPitch(newPegSound, 0.35)

            # if right clicked, remove peg
            elif mouseClicked[2]:
                selectedPegs = []
                for peg in pegs:
                    mouseBall = Ball(mousePos.x, mousePos.y)
                    mouseBall.radius = peg.radius
                    if isBallTouchingPeg(mouseBall, peg, 1):
                        selectedPegs.append(peg)

                # remove any selected pegs
                for selectedPeg in selectedPegs:
                    pegs.remove(selectedPeg)

                if len(selectedPegs) > 0:
                    if selectedMovingPeg in selectedPegs:
                        selectedMovingPeg = None
                        selectedControlPoint = None
                    staticImg = createStaticImage(pegs)
                    # play sound
                    if configs["SOUND_ENABLED"]:
                        playSoundPitch(newPegSound, 0.55)

        ##### draw #####
        screen.blit(staticImg, (0, 0))
        drawMovingPegs(screen, pegs)
        if selectedPeg is not None:
            pygame.draw.circle(
                screen,
                (255, 220, 70),
                (round(selectedPeg.pos.x), round(selectedPeg.pos.y)),
                selectedPeg.radius + 3,
                2,
            )
        visible_paths = (
            [selectedMovingPeg]
            if selectedMovingPeg is not None and selectedMovingPeg.movement is not None
            else []
        )
        for path_peg in visible_paths:
            curve = path_peg.movement.sample_curve()
            pygame.draw.lines(screen, (40, 220, 255), False, curve, 2)
            for index, (point_x, point_y) in enumerate(path_peg.movement.points):
                color = (
                    (255, 220, 40)
                    if index in (0, len(path_peg.movement.points) - 1)
                    else (255, 100, 40)
                )
                pygame.draw.circle(screen, color, (round(point_x), round(point_y)), 5)
        if len(pathPoints) > 1:
            pygame.draw.lines(screen, (40, 220, 255), False, pathPoints, 2)
        for point_x, point_y in pathPoints:
            pygame.draw.circle(screen, (255, 220, 40), (round(point_x), round(point_y)), 5)
        if shapeDragActive:
            if selectedShape == "Freehand":
                preview = freehandPoints.copy()
                if shapeDragCurrent is not None:
                    preview.append(tuple(map(float, shapeDragCurrent)))
                if len(preview) > 1:
                    pygame.draw.lines(screen, (80, 220, 255), False, preview, 2)
            elif shapeDragStart is not None and shapeDragCurrent is not None:
                preview_points = generate_shape_points(
                    selectedShape,
                    (
                        float(shapeDragStart[0]),
                        float(shapeDragStart[1]),
                        float(shapeDragCurrent[0]),
                        float(shapeDragCurrent[1]),
                    ),
                    max(float(pegRad * 2.5), 8.0),
                )
                if len(preview_points) > 1:
                    pygame.draw.lines(
                        screen,
                        (80, 220, 255),
                        selectedShape != "Line",
                        preview_points,
                        2,
                    )

        # check if the mouse is in a valid position to place a peg
        # draw a sqaure bounding box to indicate the valid area
        if not editorPaused: 
            # don't draw any of this while the game is paused (its distracting)
            if mouseOutofBounds:
                # draw the bounds for the width, lower height and upper height
                pygame.draw.rect(screen, (255, 0, 0), (widthBound, heightBound, configs["WIDTH"] - widthBound*2, configs["HEIGHT"] - heightBound - lowerHeightBound), 2)

                # draw invalid transparent peg img (red peg)
                screen.blit(invalidPegImg, (mousePos.x -
                            tempPeg.posAdjust, mousePos.y - tempPeg.posAdjust))

            else:
                # draw blue transparent peg img
                screen.blit(transparentPegImg, (mousePos.x -
                            tempPeg.posAdjust, mousePos.y - tempPeg.posAdjust))

        # draw peg count text
        pegCountColor = (5, 30, 100)
        if len(pegs) >= 100:
            pegCountColor = (120, 30, 60)
        pegCount = infoFont.render(
            "Pegs : " + str(len(pegs)), False, pegCountColor)
        screen.blit(pegCount, (int(configs["WIDTH"]/2 - 45), 50))

        # draw help text
        helpText = helpFont.render(
            "Toolbar: select/move, add, moving path, erase, and shapes", False, (255, 255, 255))
        screen.blit(helpText, (int(configs["WIDTH"]-350), 10))
        helpText2 = helpFont.render("S = Save", False, (255, 255, 255))
        screen.blit(helpText2, (int(configs["WIDTH"]-150), 25))
        helpText3 = helpFont.render("L = Load", False, (255, 255, 255))
        screen.blit(helpText3, (int(configs["WIDTH"]-150), 40))
        helpText4 = helpFont.render("Drag mouse to draw shapes", False, (255, 255, 255))
        screen.blit(helpText4, (int(configs["WIDTH"]-350), 55))
        moving_mode_text = (
            f"M: create moving path ({movingPegPointCount} points) "
            "| E: edit selected path | +/-: speed"
        )
        if movingPegMode:
            moving_mode_text += f" | points: {len(pathPoints)}/{movingPegPointCount}"
        if selectedMovingPeg is not None and selectedMovingPeg.movement is not None:
            moving_mode_text += f" | speed: {selectedMovingPeg.movement.speed:g}px/step"
        if movingPegPreviewEnabled:
            moving_mode_text += (
                f" | preview: {movingPegPreviewScope}"
            )
        screen.blit(
            helpFont.render(moving_mode_text, False, (255, 255, 255)),
            (15, 10),
        )
        for label, button_rect in toolbarButtons:
            is_active = (
                (label == "Select" and activeTool == "select")
                or (label == "Peg" and activeTool == "peg")
                or (label == "Moving v" and activeTool == "moving")
                or (label == "Erase" and activeTool == "erase")
                or (label == "Path" and activeTool == "path_edit")
                or (label == "Shapes v" and activeTool == "shape")
            )
            fill_color = (50, 120, 180) if is_active else (35, 45, 65)
            pygame.draw.rect(screen, fill_color, button_rect, border_radius=5)
            pygame.draw.rect(screen, (170, 190, 220), button_rect, 1, border_radius=5)
            label_image = helpFont.render(label, False, (255, 255, 255))
            screen.blit(
                label_image,
                label_image.get_rect(center=button_rect.center),
            )
        if shapeMenuOpen:
            for shape, button_rect in shapeMenuButtons:
                pygame.draw.rect(screen, (35, 45, 65), button_rect)
                pygame.draw.rect(screen, (170, 190, 220), button_rect, 1)
                shape_image = helpFont.render(shape, False, (255, 255, 255))
                screen.blit(
                    shape_image,
                    shape_image.get_rect(center=button_rect.center),
                )
        if movingMenuOpen:
            pygame.draw.rect(screen, (25, 32, 48), movingMenuRect, border_radius=4)
            pygame.draw.rect(screen, (170, 190, 220), movingMenuRect, 1, border_radius=4)
            displayed_movement = (
                selectedMovingPeg.movement
                if selectedMovingPeg is not None
                else None
            )
            displayed_traversal = (
                displayed_movement.traversal
                if displayed_movement is not None
                else movingPegTraversal
            )
            displayed_easing = (
                displayed_movement.easing
                if displayed_movement is not None
                else movingPegEasing
            )
            for button_rect, label in (
                (movingPointMinusButton, "-"),
                (movingPointPlusButton, "+"),
                (
                    movingPreviewButton,
                    f"Live preview: {'On' if movingPegPreviewEnabled else 'Off'}",
                ),
                (
                    movingScopeButton,
                    f"Preview: {'All pegs' if movingPegPreviewScope == 'all' else 'Selected'}",
                ),
                (
                    movingTraversalButton,
                    f"Traversal: {displayed_traversal}",
                ),
                (
                    movingEasingButton,
                    f"Easing: {displayed_easing}",
                ),
            ):
                pygame.draw.rect(screen, (35, 45, 65), button_rect, border_radius=3)
                pygame.draw.rect(screen, (170, 190, 220), button_rect, 1, border_radius=3)
                label_image = helpFont.render(label, False, (255, 255, 255))
                screen.blit(label_image, label_image.get_rect(center=button_rect.center))
            point_count_label = helpFont.render(
                f"{movingPegPointCount} route points", False, (255, 255, 255)
            )
            screen.blit(point_count_label, point_count_label.get_rect(center=(250, 116)))

        # draw a circle where the ball would be
        pygame.draw.circle(screen, (255, 255, 255), [configs["WIDTH"]/2, configs["HEIGHT"]/25], 5)

        if editorPaused:
            pausedScreen, pauseSelection = getEditorPauseScreen(mx, my, mouseClicked[0], standalone)
            # blit over the scree
            screen.blit(pausedScreen, (0, 0))

            if pauseSelection == "resume":
                editorPaused = False
                time.sleep(0.25)
            elif pauseSelection == "restart":
                pegs = []
                staticImg = createStaticImage(pegs)
                selectedMovingPeg = None
                selectedControlPoint = None
                selectedPeg = None
                pathPoints.clear()
                editorPaused = False
                time.sleep(0.15)
            elif pauseSelection == "save":
                if len(pegs) < 30:
                    print(
                        "WARN: Level must have at least 30 pegs before it is saved...")
                    # start the warning timer to display the message for 4 seconds
                    warningTimer.setTimer(4)
                    time.sleep(0.15)
                else:
                    saveData(pegs)
                    editorPaused = False
                    savedTimer.setTimer(4)
            elif pauseSelection == "load":
                pegs, originPegs, orangeCount, filePath = loadLevelMenu(screen, configs["DEBUG_MODE"])
                selectedMovingPeg = None
                selectedControlPoint = None
                selectedPeg = None
                pathPoints.clear()
                # reset the pegs
                for peg in pegs:
                    peg.reset()
                staticImg = createStaticImage(pegs)
                editorPaused = False

                if configs["MUSIC_ENABLED"]:
                    # play random music
                    newSong()

                time.sleep(0.15)
            elif pauseSelection == "play":
                if len(pegs) < 30:
                    print(
                        "WARN: Level must have at least 30 pegs before it can be played...")
                    # start the warning timer to display the message for 4 seconds
                    warningTimer.setTimer(4)
                    time.sleep(0.15)
                else:
                    return "play", pegs.copy()
            elif pauseSelection == "mainMenu":
                return "mainMenu", []
            elif pauseSelection == "quit":
                return "quit", []

        # draw warning text
        warningTimer.update()
        if warningTimer.isActive and len(pegs) == 0:
            warningText = warnFont.render(
                "Level cannot be empty...", False, (200, 20, 25))
            screen.blit(warningText, (int(configs["WIDTH"]/2 - 150), configs["HEIGHT"]/2 +55))
        elif warningTimer.isActive and len(pegs) > 0 and len(pegs) < 30:
            warningText = warnFont.render(
                "Level must have at least 30 pegs...", False, (200, 20, 25))
            screen.blit(warningText, (int(configs["WIDTH"]/2 - 200), configs["HEIGHT"]/2 +55))

        # draw saved text
        savedTimer.update()
        if savedTimer.isActive:
            savedText = warnFont.render(
                "Level saved!", False, (20, 200, 25))
            screen.blit(savedText, (int(configs["WIDTH"]/2 - 100), configs["HEIGHT"]/2))

        # draw debug text
        if configs["DEBUG_MODE"]:
            if (clock.get_rawtime() < 16):  # decide whether green text or red text
                frameColor = (0, 255, 50)  # green
            else:
                frameColor = (255, 50, 0)  # red
            # print frametime
            frameTime = debugFont.render(
                str(clock.get_rawtime()) + " ms", False, (frameColor))
            screen.blit(frameTime, (5, 10))
            framesPerSec = debugFont.render(
                str(round(clock.get_fps())) + " fps", False, (255, 255, 255))
            screen.blit(framesPerSec, (5, 25))

        pygame.display.update()

        clock.tick(configs["REFRESH_RATE"])



if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((configs["WIDTH"], configs["HEIGHT"]))
    clock = pygame.time.Clock()

    pygame.display.set_icon(editorIconImg)
    
    configs["REFRESH_RATE"] = 60

    levelEditor(screen, clock, standalone=True)
