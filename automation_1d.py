import numpy as np
import pygame

def generate_rule(rule_number):
    """
    Converts an integer (0–255) into an 8-bit binary string,
    then creates a dictionary mapping (left, mid, right) -> new_state.
    """
    binary_string = format(rule_number, '08b')
    rule = {}
    for i in range(8):
        # i in [0..7] corresponds to a binary pattern of length 3.
        key_tuple = tuple(map(int, format(i, '03b')))  # e.g., '010' -> (0,1,0)
        # The new state is read from the binary string in reverse order
        # because index 0 of i corresponds to the rightmost bit.
        rule[key_tuple] = int(binary_string[7 - i])
    return rule

def run_automaton_1D(rule_number, width, height, cell_size):
    """
    Creates a full evolution of the 1D cellular automaton on a 2D NumPy array.
    Each row of the array is a time step; each column is a cell state.
    A single '1' is placed in the middle of the top row.
    """
    rows = height // cell_size
    cols = width // cell_size

    grid = np.zeros((rows, cols), dtype=int)
    # Place a single live cell in the middle of the first row.
    grid[0, cols // 2] = 1  

    rule = generate_rule(rule_number)

    # Fill subsequent rows based on the row above.
    for r in range(1, rows):
        for c in range(1, cols - 1):
            left  = grid[r - 1, c - 1]
            mid   = grid[r - 1, c]
            right = grid[r - 1, c + 1]
            grid[r, c] = rule.get((left, mid, right), 0)

    return grid

def draw_1D_automaton(screen, grid, cell_size, color, background):
    """
    Draws the entire 1D automaton grid to the screen.
    Each element of 'grid' is either 0 or 1.
    """
    screen.fill(background)
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 1:
                x = c * cell_size
                y = r * cell_size
                pygame.draw.rect(screen, color, (x, y, cell_size, cell_size))
    pygame.display.flip()