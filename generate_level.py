import sys
import math
import json
import pygame
from local.vectors import Vector
from local.peg import Peg
from local.slider import Slider
from local.resources import backgroundImg, bluePegImg  # import resources

def generate_plinko_formation(rows: int, cols: int, spacing: int) -> list[Peg]:
    pegs = []
    for row in range(rows):
        for col in range(cols):
            # Offset every other row for the plinko effect
            x = col * spacing + (spacing // 2 if row % 2 else 0)
            y = row * spacing
            pegs.append(Peg(x, y))
    return pegs

def generate_square_formation(rows: int, cols: int, spacing: int, screen_width: int, screen_height: int) -> list[Peg]:
    pegs = []
    # Center the grid on screen
    grid_width = (cols - 1) * spacing
    grid_height = (rows - 1) * spacing
    offset_x = (screen_width - grid_width) // 2
    offset_y = (screen_height - grid_height) // 2
    for row in range(rows):
        for col in range(cols):
            x = col * spacing + offset_x
            y = row * spacing + offset_y
            pegs.append(Peg(x, y))
    return pegs

def generate_triangle_formation(rows: int, spacing: int, screen_width: int) -> list[Peg]:
    pegs = []
    # A triangle where first row has 1 peg, second row 2 pegs, etc.
    for row in range(rows):
        # Center the row horizontally
        row_width = row * spacing
        offset_x = screen_width / 2 - row_width / 2
        y = row * spacing + 50  # slight top offset
        for col in range(row + 1):
            x = offset_x + col * spacing
            pegs.append(Peg(x, y))
    return pegs

def generate_circle_formation(count: int, radius: int, center: Vector) -> list[Peg]:
    pegs = []
    for i in range(count):
        angle = 2 * math.pi * i / count
        x = center.x + radius * math.cos(angle)
        y = center.y + radius * math.sin(angle)
        pegs.append(Peg(x, y))
    return pegs

def init_slider(slider: Slider, min_val: int, max_val: int, init_val: int):
    slider.min = min_val
    slider.max = max_val
    slider.value = init_val
    # position knob according to value
    available_width = slider.sliderRect.width - slider.knobWidth
    slider.knobPos.x = slider.pos.x + (init_val - min_val) / (max_val - min_val) * available_width

def save_level(filename: str, formation: str, spacing: int, rows: int, cols: int, pegs: list[Peg]) -> None:
    level_data = {
        "formation": formation,
        "spacing": spacing,
        "rows": rows,
        "cols": cols,
        "pegs": [{"x": peg.pos.x, "y": peg.pos.y, "radius": peg.radius} for peg in pegs]
    }
    with open(filename, "w") as f:
        json.dump(level_data, f, indent=2)
    print(f"Level saved to {filename}")

def main():
    pygame.init()
    width, height = 1200, 900
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Level Editor")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    # Create sliders for spacing, rows, and cols
    spacing_slider = Slider(Vector(200, 810), 400, 20)
    rows_slider = Slider(Vector(200, 840), 400, 20)
    cols_slider = Slider(Vector(200, 870), 400, 20)

    # Setup slider ranges and initial values
    init_slider(spacing_slider, 50, 200, 100)
    init_slider(rows_slider, 3, 20, 10)  # For triangle and circle, rows used as count
    init_slider(cols_slider, 3, 20, 10)   # used for plinko and square

    current_formation = "plinko"  # default formation

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Handle key toggle for formations
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    current_formation = "plinko"
                elif event.key == pygame.K_s:
                    current_formation = "square"
                elif event.key == pygame.K_t:
                    current_formation = "triangle"
                elif event.key == pygame.K_c:
                    current_formation = "circle"
                # Press F5 to save the current level
                elif event.key == pygame.K_F5:
                    # Get parameters from the sliders. Round rows and cols to integers.
                    spacing = spacing_slider.value
                    rows = int(rows_slider.value)
                    cols = int(cols_slider.value)
                    if current_formation == "plinko":
                        pegs = generate_plinko_formation(rows, cols, spacing)
                    elif current_formation == "square":
                        pegs = generate_square_formation(rows, cols, spacing, width, height)
                    elif current_formation == "triangle":
                        pegs = generate_triangle_formation(rows, spacing, width)
                    elif current_formation == "circle":
                        center = Vector(width/2, height/2)
                        pegs = generate_circle_formation(rows, spacing, center)
                    else:
                        pegs = []
                    save_level("saved_level.json", current_formation, spacing, rows, cols, pegs)

        # Get current mouse position & click status
        mouse_pos = Vector(*pygame.mouse.get_pos())
        is_click = pygame.mouse.get_pressed()[0]

        # Update all sliders
        spacing_slider.update(mouse_pos, is_click)
        rows_slider.update(mouse_pos, is_click)
        cols_slider.update(mouse_pos, is_click)

        # Get parameters from the sliders. Round rows and cols to integers.
        spacing = spacing_slider.value
        rows = int(rows_slider.value)
        cols = int(cols_slider.value)

        # Generate pegs based on currently selected formation
        if current_formation == "plinko":
            pegs = generate_plinko_formation(rows, cols, spacing)
        elif current_formation == "square":
            pegs = generate_square_formation(rows, cols, spacing, width, height)
        elif current_formation == "triangle":
            pegs = generate_triangle_formation(rows, spacing, width)
        elif current_formation == "circle":
            center = Vector(width/2, height/2)
            pegs = generate_circle_formation(rows, spacing, center)
        else:
            pegs = []

        # Draw background
        screen.blit(backgroundImg, (0, 0))

        # Draw pegs using the blue peg image, centered at peg.pos
        for peg in pegs:
            screen.blit(bluePegImg, (int(peg.pos.x - peg.radius), int(peg.pos.y - peg.radius)))

        # Draw the sliders (the slider surface is drawn relative to 0,0 so blit at slider.pos)
        screen.blit(spacing_slider.getSliderSurface(), (spacing_slider.pos.x, spacing_slider.pos.y))
        screen.blit(rows_slider.getSliderSurface(), (rows_slider.pos.x, rows_slider.pos.y))
        screen.blit(cols_slider.getSliderSurface(), (cols_slider.pos.x, cols_slider.pos.y))

        # Render parameter text labels and current formation
        spacing_text = font.render(f"Spacing: {spacing}", True, (255, 255, 255))
        rows_text = font.render(f"Rows: {rows}", True, (255, 255, 255))
        cols_text = font.render(f"Cols: {cols}", True, (255, 255, 255))
        formation_text = font.render(f"Formation: {current_formation.title()}", True, (255, 255, 255))
        save_info_text = font.render("Press F5 to save current level", True, (255, 255, 255))
        screen.blit(spacing_text, (50, 810))
        screen.blit(rows_text, (50, 840))
        screen.blit(cols_text, (50, 870))
        screen.blit(formation_text, (50, 780))
        screen.blit(save_info_text, (50, 750))

        pygame.display.flip()
        clock.tick(165)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()