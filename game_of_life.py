import pygame
import numpy as np
from constants import (
    WIDTH, HEIGHT, FPS, CELL_SIZE, BLACK , WHITE, GREY
)

ROWS = HEIGHT // CELL_SIZE
COLS = WIDTH // CELL_SIZE

LIVE_RATIO = 0.2 

def create_initial_grid(rows, cols, live_ratio=LIVE_RATIO):
    grid = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            if np.random.random() < live_ratio:
                grid[r, c] = 1
    return grid

def count_live_neighbors(grid, r, c):
    rows, cols = grid.shape
    count = 0

    for i in range(r - 1, r + 2):
        for j in range(c - 1, c + 2):
          
            if (i == r and j == c) or i < 0 or j < 0 or i >= rows or j >= cols:
                continue

            count += grid[i, j]
    return count

def next_generation(grid):
    """
    Izračuna naslednjo generacijo Game of Life glede na trenutno stanje 'grid'.
    - grid[r, c] = 1 -> živa celica, 0 -> mrtva.
    Pravila (Conway):
    1) Če je celica živa in ima <2 ali >3 žive sosede, umre (osamljenost ali prenaseljenost).
    2) Če je celica mrtva in ima natanko 3 žive sosede, oživi (reprodukcija).

    Vrne: new_grid (2D numpy array) z novim stanjem.
    """
    rows, cols = grid.shape
    new_grid = np.copy(grid)

    # Gremo skozi vse celice in določimo, kaj se zgodi v naslednjem koraku.
    for r in range(rows):
        for c in range(cols):
            live_neighbors = count_live_neighbors(grid, r, c)
            # Če je trenutna celica živa ...
            if grid[r, c] == 1:
                # ... in ima <2 ali >3 sosedov, umre -> 0.
                if live_neighbors < 2 or live_neighbors > 3:
                    new_grid[r, c] = 0
            else:
                # Če je trenutna celica mrtva, oživi (1), če ima natanko 3 sosedov.
                if live_neighbors == 3:
                    new_grid[r, c] = 1
    return new_grid

def draw_grid(screen, grid):
    screen.fill(BLACK)
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            if grid[r, c] == 1:
                pygame.draw.rect(screen, WHITE, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, GREY, (x, y, CELL_SIZE, CELL_SIZE), 1)
    pygame.display.flip()

def mouse_to_grid_pos(mx, my):
    c = mx // CELL_SIZE
    r = my // CELL_SIZE
    return r, c

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Conway's Game of Life - Interactive")
    clock = pygame.time.Clock()

    grid = create_initial_grid(ROWS, COLS)

    running = True  
    paused = False  

    while running:
        clock.tick(FPS)  

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    r, c = mouse_to_grid_pos(mx, my)
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        # Če je bila živa (1), postane mrtva (0) in obratno.
                        grid[r, c] = 0 if grid[r, c] == 1 else 1

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    grid = create_initial_grid(ROWS, COLS)

        if not paused:
            grid = next_generation(grid)

        draw_grid(screen, grid)