import sys
import pygame
from constants import (
    WIDTH, HEIGHT, FPS,
    BLACK, WHITE, RED,
    FONT_TITLE, FONT_MENU, FONT_INPUT, CELL_SIZE
)
from oned import run_automaton_1D, draw_1D_automaton
from twod import run_simulation_2D

class GameState:
    MENU        = 0
    ENTER_RULE  = 1
    SIMULATE_1D = 2
    SIMULATE_2D = 3

def draw_text_centered(surface, text, font, color, center_x, center_y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    rect.center = (center_x, center_y)
    surface.blit(rendered, rect)

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

            elif state == GameState.SIMULATE_2D:
                run_simulation_2D()
                running = False

        if state == GameState.MENU:
            screen.fill(BLACK)
            draw_text_centered(screen, "Celični avtomati", FONT_TITLE, WHITE, WIDTH // 2, HEIGHT // 3)
            draw_text_centered(screen, "Pritisnite 1 za 1D, 2 za 2D, ESC za izhod.",
                               FONT_MENU, WHITE, WIDTH // 2, HEIGHT // 2)
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

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()