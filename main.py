import sys
import pygame
import numpy as np
from constants import (
    WIDTH, HEIGHT, FPS,
    BLACK, WHITE, RED,
    FONT_TITLE, FONT_MENU, FONT_INPUT, CELL_SIZE
)
from oned import run_automaton_1D, draw_1D_automaton
from twod import run_simulation_2D

class GameState:
    MENU = 0
    ENTER_RULE = 1  
    SIMULATE_1D = 2
    GAME_OF_LIFE = 3  
    SIMULATE_2D = 4 

def draw_text_centered(surface, text, font, color, center_x, center_y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    rect.center = (center_x, center_y)
    surface.blit(rendered, rect)

def run_game_of_life():
    rows = HEIGHT // CELL_SIZE
    cols = WIDTH // CELL_SIZE
    LIVE_RATIO = 0.2

    grid = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            if np.random.random() < LIVE_RATIO:
                grid[r, c] = 1

    clock = pygame.time.Clock()
    paused = False
    running = True

    def count_live_neighbors(grid, r, c):
        count = 0
        for i in range(r - 1, r + 2):
            for j in range(c - 1, c + 2):
                if (i == r and j == c) or i < 0 or j < 0 or i >= rows or j >= cols:
                    continue
                count += grid[i, j]
        return count

    def next_generation(grid):
        new_grid = grid.copy()
        for r in range(rows):
            for c in range(cols):
                live_neighbors = count_live_neighbors(grid, r, c)
                if grid[r, c] == 1:
                    if live_neighbors < 2 or live_neighbors > 3:
                        new_grid[r, c] = 0
                else:
                    if live_neighbors == 3:
                        new_grid[r, c] = 1
        return new_grid

    def draw_game(screen, grid):
        screen.fill(BLACK)
        for r in range(rows):
            for c in range(cols):
                if grid[r, c] == 1:
                    x = c * CELL_SIZE
                    y = r * CELL_SIZE
                    pygame.draw.rect(screen, WHITE, (x, y, CELL_SIZE, CELL_SIZE))
        pygame.display.flip()

    def mouse_to_grid_pos(mx, my):
        return my // CELL_SIZE, mx // CELL_SIZE

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    grid = np.zeros((rows, cols), dtype=int)
                    for r in range(rows):
                        for c in range(cols):
                            if np.random.random() < LIVE_RATIO:
                                grid[r, c] = 1
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    r, c = mouse_to_grid_pos(*event.pos)
                    if 0 <= r < rows and 0 <= c < cols:
                        grid[r, c] = 0 if grid[r, c] == 1 else 1

        if not paused:
            grid = next_generation(grid)
        draw_game(pygame.display.get_surface(), grid)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Celični avtomati")
    clock = pygame.time.Clock()

    state = GameState.MENU
    running = True
    rule_input = ""
    valid_1d_grid = None

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif state == GameState.MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        state = GameState.ENTER_RULE
                        rule_input = ""
                    elif event.key == pygame.K_2:
                        state = GameState.GAME_OF_LIFE
                    elif event.key == pygame.K_3:
                        state = GameState.SIMULATE_2D
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            elif state == GameState.ENTER_RULE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        try:
                            rule_number = int(rule_input)
                            if 0 <= rule_number <= 255:
                                valid_1d_grid = run_automaton_1D(
                                    rule_number,
                                    WIDTH,
                                    HEIGHT,
                                    CELL_SIZE
                                )
                                state = GameState.SIMULATE_1D
                        except ValueError:
                            pass
                    elif event.key == pygame.K_BACKSPACE:
                        rule_input = rule_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        state = GameState.MENU
                    else:
                        if event.unicode.isdigit():
                            rule_input += event.unicode

            elif state == GameState.SIMULATE_1D:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = GameState.MENU

        if state == GameState.MENU:
            screen.fill(BLACK)
            draw_text_centered(screen, "Celični avtomati", FONT_TITLE, WHITE, WIDTH // 2, HEIGHT // 4)
            draw_text_centered(screen, "1: 1D celični avtomat (vnesi pravilo)", FONT_MENU, WHITE, WIDTH // 2, HEIGHT // 2 - 40)
            draw_text_centered(screen, "2: Game of Life", FONT_MENU, WHITE, WIDTH // 2, HEIGHT // 2)
            draw_text_centered(screen, "3: 2D celični avtomat (Wall/Sand/Fire)", FONT_MENU, WHITE, WIDTH // 2, HEIGHT // 2 + 40)
            draw_text_centered(screen, "ESC: Izhod", FONT_MENU, WHITE, WIDTH // 2, HEIGHT // 2 + 100)
            pygame.display.flip()

        elif state == GameState.ENTER_RULE:
            screen.fill(BLACK)
            draw_text_centered(screen, "Vnesite pravilo (0-255):", FONT_MENU, WHITE, WIDTH // 2, HEIGHT // 3)
            input_text = rule_input if rule_input else "_"
            draw_text_centered(screen, input_text, FONT_INPUT, RED, WIDTH // 2, HEIGHT // 2)
            pygame.display.flip()

        elif state == GameState.SIMULATE_1D:
            if valid_1d_grid is not None:
                draw_1D_automaton(screen, valid_1d_grid, CELL_SIZE, color=BLACK, background=WHITE)

        elif state == GameState.GAME_OF_LIFE:
            run_game_of_life()
            state = GameState.MENU

        elif state == GameState.SIMULATE_2D:
            run_simulation_2D()
            state = GameState.MENU

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()