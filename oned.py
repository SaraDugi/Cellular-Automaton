import numpy as np
import pygame

def generate_rule(rule_number):
    binary_string = format(rule_number, '08b')
    rule = {}

    for i in range(8):
        key_tuple = tuple(map(int, format(i, '03b')))
        rule[key_tuple] = int(binary_string[7 - i])
    return rule


def run_automaton_1D(rule_number, width, height, cell_size):
    rows = height // cell_size
    cols = width // cell_size
    
    grid = np.zeros((rows, cols), dtype=int)
    grid[0, cols // 2] = 1  

    rule = generate_rule(rule_number)

  #neciklično :)
    for r in range(1, rows):
        for c in range(1, cols - 1):
            left  = grid[r - 1, c - 1]
            mid   = grid[r - 1, c]
            right = grid[r - 1, c + 1]
            grid[r, c] = rule.get((left, mid, right), 0)

    return grid


def draw_1D_automaton(screen, grid, cell_size, color, background):
    screen.fill(background)
    rows, cols = grid.shape

    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 1:
                x = c * cell_size
                y = r * cell_size
                pygame.draw.rect(screen, color, (x, y, cell_size, cell_size))
    pygame.display.flip()