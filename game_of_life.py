import pygame
import numpy as np
from constants import (
    WIDTH, HEIGHT, FPS, CELL_SIZE, BLACK , WHITE, GREY
)

ROWS = HEIGHT // CELL_SIZE
COLS = WIDTH // CELL_SIZE

# Začetno razmerje živih celic (privzeto 20%).
LIVE_RATIO = 0.2 

def create_initial_grid(rows, cols, live_ratio=LIVE_RATIO):
    """
    Ustvari začetno (rows x cols) mrežo za Game of Life.
    - live_ratio: delež (0..1), ki pove, s kakšno verjetnostjo bo posamezna celica živa (1).
    - grid[r, c] = 1 pomeni živo celico, 0 pomeni mrtvo.
    
    Postopek:
    1) Ustvarimo 2D numpy array poln ničel (0).
    2) Vsako polje (r, c) izpolnimo z 1 z verjetnostjo live_ratio, sicer 0.
    """
    grid = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            if np.random.random() < live_ratio:
                grid[r, c] = 1
    return grid

def count_live_neighbors(grid, r, c):
    """
    Prešteje žive sosede (1) celice (r, c) v 8 smereh (levo, desno, gor, dol, diagonale).
    - grid: 2D numpy array
    - (r, c): indeks vrstice in stolpca

    Vrnemo število (count), ki pove, koliko sosedov je 'živih'.
    """
    rows, cols = grid.shape
    count = 0
    # Za r-1 do r+1 in c-1 do c+1 pokrijemo vse možne sosede, vključno z (r,c) samo,
    # a to preskočimo, ker se ne šteje sama sebi.
    for i in range(r - 1, r + 2):
        for j in range(c - 1, c + 2):
            # Preskočimo:
            # 1) samo celico (r,c),
            # 2) sosede, ki so izven meja (i < 0, j < 0, i >= rows, j >= cols).
            if (i == r and j == c) or i < 0 or j < 0 or i >= rows or j >= cols:
                continue
            # Če je sosed živa celica, povečamo števec.
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
    # Najprej naredimo kopijo (da ne spreminjamo 'grid' sproti).
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
    """
    Nariše celotno mrežo Game of Life na zaslon.
    - screen: Pygame-ova glavna površina, kamor rišemo
    - grid: 2D numpy array (rows x cols), kjer 1 pomeni živo celico in 0 mrtvo

    Postopek risanja:
    1) screen.fill(BLACK) -> pobarvamo celo ozadje v črno
    2) Za vsako celico (r, c):
       - izračunamo (x, y) = (c * CELL_SIZE, r * CELL_SIZE)
         ker c gre vodoravno, r navpično.
       - če je grid[r, c] == 1, narišemo bel kvadrat.
       - narišemo tudi siv okvir (GREY) debeline 1 px, da ločimo celice med sabo.
    """
    screen.fill(BLACK)
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            if grid[r, c] == 1:
                pygame.draw.rect(screen, WHITE, (x, y, CELL_SIZE, CELL_SIZE))
            # Narišemo še siv rob okrog kvadratka (lahko tudi ne, če ne želimo mreže).
            pygame.draw.rect(screen, GREY, (x, y, CELL_SIZE, CELL_SIZE), 1)
    pygame.display.flip()

def mouse_to_grid_pos(mx, my):
    """
    Pretvori miškine koordinate (mx, my) v slikovnih pikah 
    v (r, c) indeks mreže.
    
    - c = mx // CELL_SIZE (stolpec)
    - r = my // CELL_SIZE (vrstica)
    """
    c = mx // CELL_SIZE
    r = my // CELL_SIZE
    return r, c

def main():
    """
    Glavna funkcija, kjer se program začne izvajati.
    - Inicializira Pygame in okno.
    - Ustvari začetno mrežo.
    - Omogoča interaktivno uporabo:
      - Levi klik miške spreminja stanje celic (mrtva <-> živa).
      - 'SPACE' ustavi/nadaljuje simulacijo (pause).
      - 'R' resetira (ustvari novo naključno mrežo).
    - Vsak korak se prikaže na zaslon in po potrebi izvede next_generation.
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Conway's Game of Life - Interactive")
    clock = pygame.time.Clock()

    # Ustvarimo začetno mrežo (z naključno porazdelitvijo živih celic ~20%).
    grid = create_initial_grid(ROWS, COLS)

    running = True  # glavni zanki
    paused = False  # ali je simulacija zaustavljena

    while running:
        clock.tick(FPS)  # omejimo število sličic na sekundo (FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Če zapremo okno, prenehamo z glavno zanko.
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Levi klik miške - spremenimo stanje celice (r, c).
                if event.button == 1:
                    mx, my = event.pos
                    r, c = mouse_to_grid_pos(mx, my)
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        # Če je bila živa (1), postane mrtva (0) in obratno.
                        grid[r, c] = 0 if grid[r, c] == 1 else 1

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # SPACE -> pauziramo ali od-pauziramo simulacijo.
                    paused = not paused
                elif event.key == pygame.K_r:
                    # R -> reset mreže (nova naključna postavitev).
                    grid = create_initial_grid(ROWS, COLS)

        # Če nismo na pavzi, izračunamo naslednjo generacijo.
        if not paused:
            grid = next_generation(grid)

        # Vedno narišemo (tudi če je pavza, da se vidi sprememba po kliku).
        draw_grid(screen, grid)