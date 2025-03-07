import sys
import pygame
import numpy as np
import random        
from constants import *

# ------------------------ Pomožne matrike ------------------------
water_amount = np.zeros((ROWS, COLS), dtype=float)
smoke_timer  = np.zeros((ROWS, COLS), dtype=int)

# ------------------------ Pygame inicializacija ------------------------
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("2D Celicni Avtomat: B678/S2345678 + Sand/Wood/Fire/Smoke/Water/Balloon")
clock = pygame.time.Clock()

info_font = pygame.font.SysFont("Arial", 16)
selected_state = BALLOON

# ------------------------ Funkcije za CA ------------------------

def create_initial_grid(rows, cols, live_ratio, sand_ratio):
    """
    Ustvari začetno mrežo za 'jamaste' strukture in dodani pesek:
      - S probability 'live_ratio' => LIVE
      - S probability 'sand_ratio' => SAND
      - Ostalo => EMPTY
    Druge elemente (WOOD, FIRE, WATER, SMOKE, BALLOON) ne postavljamo naključno,
    ampak jih lahko dodamo ročno med simulacijo.
    """
    grid = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            rnd = random.random()
            if rnd < live_ratio:
                grid[r, c] = LIVE
            elif rnd < live_ratio + sand_ratio:
                grid[r, c] = SAND
            else:
                grid[r, c] = EMPTY
    return grid

def count_live_neighbors(grid, r, c):
    """
    Prešteje 'žive' sosede (LIVE = 1) celice (r, c) v Moorovi okolici (8 sosed).
    Pesek, les, ogenj, dim, voda, balon se NE štejejo kot 'živi' za B678/S2345678.
    """
    rows, cols = grid.shape
    alive_count = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            rr = r + dr
            cc = c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                if grid[rr, cc] == LIVE:
                    alive_count += 1
    return alive_count

def update_live_empty(old_grid, new_grid, r, c):
    """
    B678/S2345678 za stanja LIVE (1) in EMPTY (0).
    """
    cell_state = old_grid[r, c]
    alive_neighbors = count_live_neighbors(old_grid, r, c)

    if cell_state == LIVE:
        # Preživi, če je alive_neighbors v SURVIVE_NEIGHBORS
        if alive_neighbors in SURVIVE_NEIGHBORS:
            new_grid[r, c] = LIVE
        else:
            new_grid[r, c] = EMPTY
    elif cell_state == EMPTY:
        # Rodi se, če je alive_neighbors v BIRTH_NEIGHBORS
        if alive_neighbors in BIRTH_NEIGHBORS:
            new_grid[r, c] = LIVE
        else:
            new_grid[r, c] = EMPTY

def update_sand(old_grid, new_grid, r, c):
    """
    Osnovna logika padanja peska:
     - Najprej poskusimo dol, če je prazno (EMPTY) ali voda (WATER) z malo vode,
       se lahko 'zasidra' spodaj.
     - Sicer poskusimo diagonalno levo/desno.
    """
    rows, cols = old_grid.shape
    below = r + 1
    if below < rows:
        below_state = old_grid[below, c]
        if below_state == EMPTY or below_state == WATER:
            new_grid[below, c] = SAND
            new_grid[r, c] = EMPTY
        else:
            move_candidates = []
            if c - 1 >= 0:
                if old_grid[below, c-1] in (EMPTY, WATER):
                    move_candidates.append((below, c-1))
            if c + 1 < cols:
                if old_grid[below, c+1] in (EMPTY, WATER):
                    move_candidates.append((below, c+1))
            if move_candidates:
                nr, nc = random.choice(move_candidates)
                new_grid[nr, nc] = SAND
                new_grid[r, c] = EMPTY
            else:
                new_grid[r, c] = SAND
    else:
        new_grid[r, c] = SAND

def update_wood(old_grid, new_grid, r, c):
    """
    Les (WOOD) pada navzdol, če je spodaj prazno ali voda.
    Če je v soseščini ogenj, obstaja verjetnost, da se vname.
    """
    rows, cols = old_grid.shape
    below = r + 1
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                if old_grid[rr, cc] == FIRE:
                    if random.random() < WOOD_BURN_CHANCE:
                        new_grid[r, c] = FIRE
                        return
    if below < rows:
        below_state = old_grid[below, c]
        if below_state == EMPTY or below_state == WATER:
            new_grid[below, c] = WOOD
            new_grid[r, c] = EMPTY
        else:
            new_grid[r, c] = WOOD
    else:
        new_grid[r, c] = WOOD

def update_fire(old_grid, new_grid, r, c):
    """
    Ogenj (FIRE) se premika naključno navzdol. Če "pristane" na gorljivem elementu (WOOD),
    ga spremeni v ogenj in se sam spremeni v dim (SMOKE) – oz. z verjetnostjo.
    Sicer se spremeni v dim, ko se premakne na prazno ali drugo celico.
    """
    rows, cols = old_grid.shape
    candidates = []
    for dc in [-1, 0, 1]:
        nr, nc = r + 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    random.shuffle(candidates)
    moved = False
    for (nr, nc) in candidates:
        target_state = old_grid[nr, nc]
        if target_state == WOOD:
            new_grid[nr, nc] = FIRE
            if random.random() < FIRE_TO_SMOKE_CHANCE:
                new_grid[r, c] = SMOKE
                smoke_timer[r, c] = SMOKE_LIFETIME
            else:
                new_grid[r, c] = EMPTY
            moved = True
            break
        elif target_state in (EMPTY, WATER, SAND, LIVE, SMOKE, BALLOON):
            new_grid[nr, nc] = FIRE
            if random.random() < FIRE_TO_SMOKE_CHANCE:
                new_grid[r, c] = SMOKE
                smoke_timer[r, c] = SMOKE_LIFETIME
            else:
                new_grid[r, c] = EMPTY
            moved = True
            break
    if not moved:
        new_grid[r, c] = FIRE

def update_smoke(old_grid, new_grid, r, c):
    """
    Dim (SMOKE) se premika navzgor (naključno med zgoraj levo, zgoraj, zgoraj desno).
    Ima omejeno življenjsko dobo. Ko se čas izteče, postane EMPTY.
    """
    rows, cols = old_grid.shape
    if smoke_timer[r, c] <= 0:
        new_grid[r, c] = EMPTY
        return

    candidates = []
    for dc in [-1, 0, 1]:
        nr, nc = r - 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    random.shuffle(candidates)
    moved = False
    for (nr, nc) in candidates:
        if old_grid[nr, nc] == EMPTY:
            new_grid[nr, nc] = SMOKE
            smoke_timer[nr, nc] = smoke_timer[r, c]
            new_grid[r, c] = EMPTY
            smoke_timer[r, c] = 0
            moved = True
            break
    if not moved:
        side_candidates = []
        for dc in [-1, 1]:
            nc = c + dc
            if 0 <= nc < cols:
                side_candidates.append((r, nc))
        random.shuffle(side_candidates)
        for (nr, nc) in side_candidates:
            if old_grid[nr, nc] == EMPTY:
                new_grid[nr, nc] = SMOKE
                smoke_timer[nr, nc] = smoke_timer[r, c]
                new_grid[r, c] = EMPTY
                smoke_timer[r, c] = 0
                moved = True
                break
    if not moved:
        new_grid[r, c] = SMOKE
    smoke_timer[r, c] -= 1
    if smoke_timer[r, c] <= 0:
        new_grid[r, c] = EMPTY

def update_balloon(old_grid, new_grid, r, c):
    """
    Balon (BALLOON) se premika navzgor (naključno med levo, sredi in desno).
    Če naleti na kakršenkoli element, "poči" (postane EMPTY).
    """
    rows, cols = old_grid.shape
    candidates = []
    for dc in [-1, 0, 1]:
        nr, nc = r - 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    random.shuffle(candidates)
    moved = False
    for (nr, nc) in candidates:
        if old_grid[nr, nc] == EMPTY:
            new_grid[nr, nc] = BALLOON
            new_grid[r, c] = EMPTY
            moved = True
            break
        else:
            new_grid[r, c] = EMPTY
            moved = True
            break
    if not moved:
        new_grid[r, c] = EMPTY

def spread_water_once(r, c, new_grid):
    """
    Preprost model pretakanja vode znotraj 8-sosedske okolice.
    """
    rows, cols = new_grid.shape
    current_amount = water_amount[r, c]
    if current_amount <= 0:
        return
    directions = [
        (1, 0),   # dol
        (1, -1),  # diagonalno dol-levo
        (1, 1),   # diagonalno dol-desno
        (0, -1),  # levo
        (0, 1),   # desno
        (-1, 0),  # gor
    ]
    for (dr, dc) in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            neighbor_state = new_grid[nr, nc]
            if neighbor_state in [EMPTY, WATER, LIVE, SAND]:
                if neighbor_state != WATER:
                    new_grid[nr, nc] = WATER
                neighbor_amt = water_amount[nr, nc]
                capacity_left = MAX_WATER_CAPACITY - neighbor_amt
                if capacity_left > 0:
                    flow = min(current_amount * 0.5, capacity_left)
                    water_amount[r, c]    -= flow
                    water_amount[nr, nc] += flow
                    current_amount -= flow
                    if current_amount <= 0:
                        break

def update_water(old_grid, new_grid, r, c):
    """
    Voda ostane WATER, količina pa se premika.
    """
    new_grid[r, c] = WATER

# ------------------------ Glavna funkcija za eno generacijo ------------------------

def next_generation(grid):
    """
    Izračuna naslednjo generacijo 2D mreže z več prehodi:
      1) LIVE/EMPTY (B678/S2345678)
      2) FIRE in SMOKE (zgoraj navzdol)
      3) BALLOON (zgoraj navzdol)
      4) SAND in WOOD (spodaj navzdol)
      5) WATER (pretakanje)
    Vrne novo mrežo in posodobi water_amount, smoke_timer.
    """
    rows, cols = grid.shape
    new_grid = np.copy(grid)

    # 1) LIVE / EMPTY
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] in (LIVE, EMPTY):
                update_live_empty(grid, new_grid, r, c)

    # 2) FIRE in SMOKE
    for r in range(rows):
        for c in range(cols):
            state = grid[r, c]
            if state == FIRE:
                update_fire(grid, new_grid, r, c)
            elif state == SMOKE:
                if new_grid[r, c] == SMOKE:
                    update_smoke(grid, new_grid, r, c)

    # 3) BALLOON
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == BALLOON:
                if new_grid[r, c] == BALLOON:
                    update_balloon(grid, new_grid, r, c)

    # 4) SAND in WOOD (od spodaj navzdol)
    for r in range(rows - 1, -1, -1):
        for c in range(cols):
            state = grid[r, c]
            if state == SAND:
                if new_grid[r, c] == SAND:
                    update_sand(grid, new_grid, r, c)
            elif state == WOOD:
                if new_grid[r, c] == WOOD:
                    update_wood(grid, new_grid, r, c)

    # 5) WATER
    idx_list = list(range(rows * cols))
    random.shuffle(idx_list)
    for idx in idx_list:
        r = idx // cols
        c = idx % cols
        if grid[r, c] == WATER or water_amount[r, c] > 0:
            spread_water_once(r, c, new_grid)
    for r in range(rows):
        for c in range(cols):
            if water_amount[r, c] > 0.01:
                if new_grid[r, c] not in (FIRE, WOOD, SMOKE, BALLOON):
                    new_grid[r, c] = WATER
            else:
                if new_grid[r, c] == WATER:
                    new_grid[r, c] = EMPTY

    return new_grid

# ------------------------ Risanje ------------------------

def get_water_color(amount):
    """
    Glede na količino vode vrne ustrezno modro barvo.
    """
    alpha = min(amount / MAX_WATER_CAPACITY, 1.0)
    r1, g1, b1 = (150, 150, 255)
    r2, g2, b2 = (0, 0, 150)
    r = int(r1 + (r2 - r1) * alpha)
    g = int(g1 + (g2 - g1) * alpha)
    b = int(b1 + (b2 - b1) * alpha)
    return (r, g, b)

def draw_grid(screen, grid):
    """
    Nariše trenutno mrežo na zaslon.
    """
    screen.fill(BLACK)
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            st = grid[r, c]
            if st == WATER:
                amt = water_amount[r, c]
                if amt > 0.01:
                    color = get_water_color(amt)
                else:
                    color = BLACK
            else:
                color = BASE_COLOR_MAP[st]
            if st != EMPTY or (st == WATER and water_amount[r, c] > 0):
                x = c * CELL_SIZE
                y = r * CELL_SIZE
                pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))

def draw_info(screen, generation, selected_state):
    """
    Nariše informativni del: trenutno generacijo, izbrani element in legendo.
    """
    info_surface = pygame.Surface((WIDTH, 50))
    info_surface.set_alpha(200)
    info_surface.fill((50, 50, 50))
    
    gen_text = info_font.render(f"Generacija: {generation}", True, WHITE)
    screen.blit(info_surface, (0, 0))
    screen.blit(gen_text, (10, 5))
    
    state_names = {
        EMPTY: "EMPTY",
        LIVE: "LIVE",
        SAND: "SAND",
        WOOD: "WOOD",
        FIRE: "FIRE",
        SMOKE: "SMOKE",
        BALLOON: "BALLOON",
        WATER: "WATER"
    }
    sel_text = info_font.render(f"Izbrano: {state_names[selected_state]}", True, WHITE)
    screen.blit(sel_text, (10, 25))
    
    legend = [
        ("LIVE", WHITE),
        ("SAND", SAND_COLOR),
        ("WOOD", WOOD_COLOR),
        ("FIRE", FIRE_COLOR),
        ("SMOKE", SMOKE_COLOR),
        ("BALLOON", BALLOON_COL),
        ("WATER", WATER_LEGEND)
    ]
    x_offset = 200
    for name, color in legend:
        pygame.draw.rect(screen, color, (x_offset, 10, 15, 15))
        legend_text = info_font.render(name, True, WHITE)
        screen.blit(legend_text, (x_offset + 20, 8))
        x_offset += 100

    pygame.display.update()

def mouse_to_grid_pos(mx, my):
    """Pretvori koordinate miške v indekse mreže."""
    c = mx // CELL_SIZE
    r = my // CELL_SIZE
    return r, c

# ------------------------ Glavna simulacija ------------------------

def run_simulation_2D():
    global selected_state
    grid = create_initial_grid(ROWS, COLS, INITIAL_LIVE_RATIO, INITIAL_SAND_RATIO)
    generation = 0
    running = True
    paused = False

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return  # Return control to caller
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False  # Exit simulation loop
                    return
                elif event.key == pygame.K_0:
                    selected_state = EMPTY
                elif event.key == pygame.K_1:
                    selected_state = WOOD
                elif event.key == pygame.K_2:
                    selected_state = FIRE
                elif event.key == pygame.K_3:
                    selected_state = SAND
                elif event.key == pygame.K_4:
                    selected_state = SMOKE
                elif event.key == pygame.K_5:
                    selected_state = LIVE
                elif event.key == pygame.K_6:
                    selected_state = BALLOON
                elif event.key == pygame.K_7:
                    selected_state = WATER
                elif paused:
                    paused = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    r, c = mouse_to_grid_pos(mx, my)
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        grid[r, c] = selected_state
                        if selected_state == WATER:
                            water_amount[r, c] = MAX_WATER_CAPACITY
                    if paused:
                        paused = False

        draw_grid(screen, grid)
        draw_info(screen, generation, selected_state)

        new_grid = next_generation(grid)

        if np.array_equal(new_grid, grid):
            if not paused:
                print(f"Stable state reached at generation {generation}. Pausing simulation...")
            paused = True
        else:
            paused = False

        if not paused:
            generation += 1
            grid = new_grid

    return