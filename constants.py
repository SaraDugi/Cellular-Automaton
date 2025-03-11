import pygame

pygame.font.init()

# ------------------------ Window Settings ------------------------
WIDTH = 800
HEIGHT = 600
CELL_SIZE = 7
FPS = 10

# ------------------------ Colors ------------------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED   = (255, 0, 0)

# ------------------------ Fonts ------------------------
FONT_TITLE = pygame.font.SysFont("Arial", 48)
FONT_MENU  = pygame.font.SysFont("Arial", 36)
FONT_INPUT = pygame.font.SysFont("Arial", 28)
INFO_FONT  = pygame.font.SysFont("Arial", 16)

# ------------------------ 2D Cellular Automaton Constants ------------------------
ROWS = HEIGHT // CELL_SIZE
COLS = WIDTH // CELL_SIZE

INITIAL_LIVE_RATIO = 0.45
INITIAL_SAND_RATIO = 0.05

BIRTH_NEIGHBORS   = {6, 7, 8}
SURVIVE_NEIGHBORS = {2, 3, 4, 5, 6, 7, 8}

EMPTY    = 0
LIVE     = 1
SAND     = 2
WOOD     = 3
FIRE     = 4
SMOKE    = 5
BALLOON  = 6
WATER    = 7

SAND_COLOR  = (194, 178, 128)
WOOD_COLOR  = (139, 69, 19)
FIRE_COLOR  = (255, 0, 0)
SMOKE_COLOR = (128, 128, 128)
BALLOON_COL = (255, 105, 180)
WATER_LEGEND = (0, 0, 255)

BASE_COLOR_MAP = {
    0: BLACK,
    1: (128, 128, 128),
    2: SAND_COLOR,
    3: FIRE_COLOR,
    4: WOOD_COLOR,
    5: (32, 32, 32),
    6: (192, 192, 192),
    7: (0, 0, 255),        
    8: (255, 105, 180)      
}

MAX_WATER_CAPACITY   = 2.0
SMOKE_LIFETIME       = 10
WOOD_BURN_CHANCE     = 1.0
FIRE_TO_SMOKE_CHANCE = 1.0