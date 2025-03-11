import sys
import pygame
import numpy as np
import random
from constants import (
    WIDTH, HEIGHT, CELL_SIZE, FPS,
    BLACK, WHITE,
    SAND_COLOR, FIRE_COLOR, WOOD_COLOR,
    ROWS, COLS,
    INITIAL_LIVE_RATIO,
    INITIAL_SAND_RATIO,
    FIRE_TO_SMOKE_CHANCE,
    SMOKE_LIFETIME
)

BASE_COLOR_MAP = {
    0: BLACK,
    1: (128, 128, 128),
    2: SAND_COLOR,
    3: FIRE_COLOR,
    4: WOOD_COLOR,
    5: (32, 32, 32),
    6: (192, 192, 192),
    7: (0, 0, 255) 
}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Cellular Automata: Wall/Sand/Fire/Wood/Smoke/Water")
clock = pygame.time.Clock()
info_font = pygame.font.SysFont("Arial", 16)
menu_font = pygame.font.SysFont("Arial", 18, bold=True)
smoke_timer = np.zeros((ROWS, COLS), dtype=int)
water_levels = np.zeros((ROWS, COLS), dtype=float)
selected_state = 3  

def create_initial_grid(rows, cols, wall_ratio, sand_ratio):
    """
    Creates the initial grid.
      - With probability 'wall_ratio' the cell becomes a WALL (state 1).
      - With probability 'sand_ratio' the cell becomes SAND (state 2).
      - Else the cell is EMPTY (state 0).
    (Wood and water are not generated randomly; you can paint them.)
    """
    grid = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            rnd = random.random()
            if rnd < wall_ratio:
                grid[r, c] = 1  
            elif rnd < wall_ratio + sand_ratio:
                grid[r, c] = 2  
            else:
                grid[r, c] = 0  
    return grid

def update_sand(old_grid, new_grid, r, c):
    rows, cols = old_grid.shape
    below = r + 1
    if below < rows and old_grid[below, c] == 0:
        new_grid[below, c] = 2
        new_grid[r, c] = 0
    else:
        candidates = []
        if below < rows:
            if c - 1 >= 0 and old_grid[below, c-1] == 0:
                candidates.append((below, c-1))
            if c + 1 < cols and old_grid[below, c+1] == 0:
                candidates.append((below, c+1))
        if candidates:
            nr, nc = random.choice(candidates)
            new_grid[nr, nc] = 2
            new_grid[r, c] = 0
        else:
            new_grid[r, c] = 2

def update_fire(old_grid, new_grid, r, c):
    rows, cols = old_grid.shape
    candidates = []
    for dc in [-1, 0, 1]:
        nr, nc = r + 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    random.shuffle(candidates)
    moved = False
    for (nr, nc) in candidates:
        target = old_grid[nr, nc]
        if target in (0, 2, 4):
            if target == 4:
                new_grid[nr, nc] = 5  
            else:
                new_grid[nr, nc] = 6 
            smoke_timer[nr, nc] = SMOKE_LIFETIME
            new_grid[r, c] = 0
            moved = True
            break
    if not moved:
        new_grid[r, c] = 3

def update_wood(old_grid, new_grid, r, c):
    rows, cols = old_grid.shape
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            rr = r + dr
            cc = c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                if old_grid[rr, cc] == 3:
                    new_grid[r, c] = 3
                    return
    below = r + 1
    if below < rows and old_grid[below, c] == 0:
        new_grid[below, c] = 4
        new_grid[r, c] = 0
    else:
        new_grid[r, c] = 4

def update_smoke(old_grid, new_grid, r, c):
    rows, cols = old_grid.shape
    current_lifetime = smoke_timer[r, c]
    if current_lifetime <= 0:
        new_grid[r, c] = 0
        return
    new_lifetime = current_lifetime - 1
    upward_candidates = []
    for dc in [-1, 0, 1]:
        nr, nc = r - 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if old_grid[nr, nc] == 0:
                upward_candidates.append((nr, nc))
    if upward_candidates:
        nr, nc = random.choice(upward_candidates)
        new_grid[nr, nc] = old_grid[r, c]
        smoke_timer[nr, nc] = new_lifetime
        new_grid[r, c] = 0
    else:
        side_candidates = []
        for dc in [-1, 1]:
            nr, nc = r, c + dc
            if 0 <= nc < cols and old_grid[r, nc] == 0:
                side_candidates.append((r, nc))
        if side_candidates:
            nr, nc = random.choice(side_candidates)
            new_grid[nr, nc] = old_grid[r, c]
            smoke_timer[nr, nc] = new_lifetime
            new_grid[r, c] = 0
        else:
            new_grid[r, c] = old_grid[r, c]
            smoke_timer[r, c] = new_lifetime

def update_water(old_grid, new_grid, r, c):
    """
    Update water (state 7). Water flows:
      - Down if possible.
      - Otherwise, splits left and right.
      - If overfull (>1.0), excess flows upward.
    Water levels are stored in the global 'water_levels' array.
    """
    amount = water_levels[r, c]
    if amount <= 0:
        return
    if r + 1 < ROWS:
        if old_grid[r+1, c] == 7:
            capacity = max(0, 1.0 - water_levels[r+1, c])
        elif old_grid[r+1, c] == 0:
            capacity = 1.0
        else:
            capacity = 0
        flow = min(amount, capacity)
        if flow > 0:
            water_levels[r+1, c] += flow
            water_levels[r, c] -= flow
            new_grid[r+1, c] = 7
            new_grid[r, c] = 7 if water_levels[r, c] > 0 else 0
            return

    for dc in [-1, 1]:
        nc = c + dc
        if 0 <= nc < COLS:
            if old_grid[r, nc] in (0, 7):
                if old_grid[r, nc] == 7:
                    capacity = max(0, 1.0 - water_levels[r, nc])
                else:
                    capacity = 1.0
                share = min(amount, 0.25, capacity)
                if share > 0:
                    water_levels[r, nc] += share
                    water_levels[r, c] -= share
                    new_grid[r, nc] = 7
                    new_grid[r, c] = 7 if water_levels[r, c] > 0 else 0

    if water_levels[r, c] > 1.0 and r - 1 >= 0:
        if old_grid[r-1, c] in (0, 7):
            if old_grid[r-1, c] == 7:
                capacity = max(0, 1.0 - water_levels[r-1, c])
            else:
                capacity = 1.0
            flow = min(water_levels[r, c] - 1.0, capacity)
            if flow > 0:
                water_levels[r-1, c] += flow
                water_levels[r, c] -= flow
                new_grid[r-1, c] = 7
                new_grid[r, c] = 7 if water_levels[r, c] > 0 else 0

def draw_grid(screen, grid):
    screen.fill(BLACK)
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            state = grid[r, c]
            if state == 7:
                amt = water_levels[r, c]
                amt = min(amt, 2.0)
                t = amt / 2.0 
                r_val = int(173 * (1-t) + 0 * t)
                g_val = int(216 * (1-t) + 0 * t)
                b_val = int(230 * (1-t) + 139 * t)
                color = (r_val, g_val, b_val)
            else:
                color = BASE_COLOR_MAP[state]
            if state != 0:
                x = c * CELL_SIZE
                y = r * CELL_SIZE
                pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
    pygame.display.flip()

def draw_info(screen, generation, selected_state):
    info_surface = pygame.Surface((WIDTH, 50))
    info_surface.set_alpha(200)
    info_surface.fill((50, 50, 50))
    screen.blit(info_surface, (0, 0))
    gen_text = info_font.render(f"Generation: {generation}", True, WHITE)
    screen.blit(gen_text, (10, 5))
    state_names = {2: "SAND", 3: "FIRE", 4: "WOOD", 7: "WATER"}
    sel_text = info_font.render(f"Selected: {state_names.get(selected_state, '')}", True, WHITE)
    screen.blit(sel_text, (10, 25))

    menu_text_lines = [
        "2  ->  FIRE",
        "3  ->  SAND",
        "4  ->  WOOD",
        "5  ->  WATER"
    ]
    box_width = 200
    box_height = 90
    box_x = WIDTH - box_width - 10
    box_y = 10
    menu_bg = pygame.Surface((box_width, box_height))
    menu_bg.set_alpha(220)
    menu_bg.fill((30, 30, 30))
    screen.blit(menu_bg, (box_x, box_y))
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2)
    for i, line in enumerate(menu_text_lines):
        text_surface = menu_font.render(line, True, WHITE)
        text_x = box_x + 10
        text_y = box_y + 5 + i * 22
        screen.blit(text_surface, (text_x, text_y))
    pygame.display.update()

def mouse_to_grid_pos(mx, my):
    c = mx // CELL_SIZE
    r = my // CELL_SIZE
    return r, c

def next_generation(grid):
    rows, cols = grid.shape
    new_grid = np.copy(grid)
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 3:
                update_fire(grid, new_grid, r, c)
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] in (5, 6):
                update_smoke(grid, new_grid, r, c)
    for r in range(rows-1, -1, -1):
        for c in range(cols):
            if grid[r, c] == 2:
                update_sand(grid, new_grid, r, c)
    for r in range(rows-1, -1, -1):
        for c in range(cols):
            if grid[r, c] == 4:
                update_wood(grid, new_grid, r, c)
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 7:
                update_water(grid, new_grid, r, c)
    return new_grid

def run_simulation_2D():
    global selected_state
    grid = create_initial_grid(ROWS, COLS, INITIAL_LIVE_RATIO, INITIAL_SAND_RATIO)
    static_walls = (grid == 1)
    generation = 0
    running = True
    paused = False

    selected_state = 3  

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    return
                elif event.key == pygame.K_2:
                    selected_state = 3  
                elif event.key == pygame.K_3:
                    selected_state = 2  
                elif event.key == pygame.K_4:
                    selected_state = 4  
                elif event.key == pygame.K_5:
                    selected_state = 7  
                elif paused:
                    paused = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    r, c = mouse_to_grid_pos(mx, my)
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        grid[r, c] = selected_state
                        if selected_state == 7:
                            water_levels[r, c] = 1.0 
                    if paused:
                        paused = False

        draw_grid(screen, grid)
        draw_info(screen, generation, selected_state)
        new_grid = next_generation(grid)
        new_grid[static_walls] = 1
        if np.array_equal(new_grid, grid):
            if not paused:
                print(f"Stable state reached at generation {generation}. Pausing simulation...")
            paused = True
        else:
            paused = False
        if not paused:
            generation += 1
            grid = new_grid