import pygame
import numpy as np
import random
# Uvozimo potrebne konstante iz modula constants, kjer so definirane dimenzije zaslona, hitrost osveževanja (FPS),
# barve, velikost celice, začetni deleži živih celic (stena, pesek) in še dodatni parametri (npr. življenjska doba dima).
from constants import (
    WIDTH, HEIGHT, CELL_SIZE, FPS,
    BLACK, WHITE,
    ROWS, COLS,
    INITIAL_LIVE_RATIO,
    INITIAL_SAND_RATIO,
    SMOKE_LIFETIME,
    BASE_COLOR_MAP
)

# Inicializacija pygame in nastavitev osnovnih parametrov okna
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Cellular Automata: Wall/Sand/Fire/Wood/Smoke/Water/Balloon")
clock = pygame.time.Clock()

# Nastavimo pisave za prikaz informacij in menijev
info_font = pygame.font.SysFont("Arial", 16)
menu_font = pygame.font.SysFont("Arial", 18, bold=True)

# Ustvarimo dve matriki, ki se uporabljata za spremljanje dodatnih lastnosti celic:
# smoke_timer: spremlja koliko časa naj dim (smoke) ostane na določenem mestu
smoke_timer = np.zeros((ROWS, COLS), dtype=int)
# water_levels: spremlja količino vode v posamezni celici (uporabljeno za dinamično barvanje)
water_levels = np.zeros((ROWS, COLS), dtype=float)

# Izbrana celica (state) se privzeto nastavi na 3, kar predstavlja FIRE (ogenj)
selected_state = 3  

# Funkcija za ustvarjanje začetne mreže, kjer so celice naključno nastavljene kot stene, pesek ali prazno
def create_initial_grid(rows, cols, wall_ratio, sand_ratio):
    """
    Ustvari začetno 2D mrežo (grid) z naključno porazdeljenimi stenami in peskom.
    - Vrednost 1 predstavlja steno, 2 predstavlja pesek, 0 pa pomeni prazno celico.
    Razlog: Naključna inicializacija omogoča dinamičen začetek simulacije.
    
    Args:
        rows (int): število vrstic v mreži
        cols (int): število stolpcev v mreži
        wall_ratio (float): delež celic, ki bodo stene (vrednost 1)
        sand_ratio (float): delež celic, ki bodo pesek (vrednost 2)
        
    Returns:
        numpy.ndarray: inicializirana mreža s stanji celic
    """
    # Ustvarimo mrežo, kjer so vse celice privzeto prazne (vrednost 0)
    grid = np.zeros((rows, cols), dtype=int)
    # Gremo čez vsako celico in določimo stanje glede na naključno vrednost
    for r in range(rows):
        for c in range(cols):
            rnd = random.random()  # naključno število med 0 in 1
            # Če je naključna vrednost manjša od wall_ratio, postavimo steno
            if rnd < wall_ratio:
                grid[r, c] = 1 
            # Če je naključna vrednost med wall_ratio in wall_ratio + sand_ratio, postavimo pesek
            elif rnd < wall_ratio + sand_ratio:
                grid[r, c] = 2  
            # V nasprotnem primeru celica ostane prazna (0)
            else:
                grid[r, c] = 0 
    return grid

# Funkcija za posodobitev stanja peska v simulaciji
def update_sand(old_grid, new_grid, r, c):
    """
    Posodobi položaj celice, ki vsebuje pesek (vrednost 2).
    Pravila za premikanje peska:
      - Pesek se premika navzdol, če je celica pod njim prazna (0) ali vsebuje vodo (7).
      - Če ni mogoče premikanje naravnost navzdol, preveri diagonalne celice (spodaj levo/desno).
      - Če najde prosto diagonalno celico, se pesek naključno premakne tja.
      - Če ni proste poti, pesek ostane na istem mestu.
      
    Args:
        old_grid (numpy.ndarray): trenutno stanje mreže pred posodobitvijo
        new_grid (numpy.ndarray): nova mreža, kjer se shranjujejo spremembe
        r, c (int): indeks trenutne celice s peskom
    """
    rows, cols = old_grid.shape
    below = r + 1  # Indeks celice neposredno pod trenutno celico
    # Če je celica pod peskom prazna ali vsebuje vodo (označeno kot 7), pesek pade navzdol
    if below < rows and (old_grid[below, c] == 0 or old_grid[below, c] == 7):
        new_grid[below, c] = 2  # Pesek se premakne navzdol
        new_grid[r, c] = 0      # Trenutna celica postane prazna
        # Če je bila celica pod peskom voda, resetiramo nivo vode (ker pesek potisne vodo)
        if old_grid[below, c] == 7:
            water_levels[below, c] = 0
    else:
        # Če ni mogoče premikanje navzdol, preverimo diagonalne smeri (spodaj levo in spodaj desno)
        candidates = []
        if below < rows:
            if c - 1 >= 0 and old_grid[below, c-1] == 0:
                candidates.append((below, c-1))
            if c + 1 < cols and old_grid[below, c+1] == 0:
                candidates.append((below, c+1))
        # Če je na voljo vsaj ena prosta diagonalna celica, izberemo naključno in pesek se premakne tja
        if candidates:
            nr, nc = random.choice(candidates)
            new_grid[nr, nc] = 2
            new_grid[r, c] = 0
        else:
            # Če ni proste poti, pesek ostane na istem mestu
            new_grid[r, c] = 2

# Funkcija za posodobitev ognja v simulaciji
def update_fire(old_grid, new_grid, r, c):
    """
    Posodobi celico z ognjem (vrednost 3) glede na okolico.
    Pravila:
      - Ogenj se premika navzdol (in diagonalno navzdol) ter išče celice, ki so prazne (0), vsebujejo pesek (2) ali les (4).
      - Če naleti na les, ga spremeni v dim (vrednost 5), sicer v ogenj (vrednost 6).
      - Pri premiku nastavi čas življenjske dobe dima (SMOKE_LIFETIME).
      - Če se ogenj ne more premakniti, ostane na mestu.
      
    Args:
        old_grid (numpy.ndarray): trenutna mreža pred posodobitvijo
        new_grid (numpy.ndarray): mreža, kjer se shranjujejo spremembe
        r, c (int): indeksi celice z ognjem
    """
    rows, cols = old_grid.shape
    candidates = []
    # Generiramo potencialne ciljne celice: ena vrstica spodaj in stolpci: levo, sredina, desno
    for dc in [-1, 0, 1]:
        nr, nc = r + 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    random.shuffle(candidates)  # Naključno premešamo možnosti, da simuliramo naključnost v širjenju ognja
    moved = False
    for (nr, nc) in candidates:
        target = old_grid[nr, nc]
        # Ogenj lahko preide v celico, če je ta prazna (0), vsebuje pesek (2) ali les (4)
        if target in (0, 2, 4):
            # Če ciljno celico predstavlja les, se ta spremeni v dim (vrednost 5)
            if target == 4:
                new_grid[nr, nc] = 5 
            else:
                # V drugih primerih se celica spremeni v ogenj (vrednost 6)
                new_grid[nr, nc] = 6  
            # Nastavimo čas življenjske dobe dima v ciljni celici
            smoke_timer[nr, nc] = SMOKE_LIFETIME
            new_grid[r, c] = 0  # Prejšnja celica postane prazna
            moved = True
            break
    if not moved:
        # Če se ognja ni premaknil, ostane na istem mestu (vrednost 3)
        new_grid[r, c] = 3

# Funkcija za posodobitev lesa v simulaciji
def update_wood(old_grid, new_grid, r, c):
    """
    Posodobi celico z lesom (vrednost 4).
    Pravila:
      - Če je neposredno pod lesom voda (7), les ostane nespremenjen.
      - Če kateri izmed sosednjih (vse smeri) celic vsebuje ogenj (3), se les spremeni v ogenj.
      - Če spodnja celica (pod lesom) je prazna, se les premakne navzdol (simulira gravitacijo).
      - V nasprotnem primeru les ostane na mestu.
      
    Args:
        old_grid (numpy.ndarray): trenutna mreža pred posodobitvijo
        new_grid (numpy.ndarray): mreža, kjer se shranjujejo spremembe
        r, c (int): indeksi celice z lesom
    """
    rows, cols = old_grid.shape
    # Preverimo, če je pod lesom voda – v tem primeru se les ne spremeni
    if r + 1 < rows and old_grid[r+1, c] == 7:
        new_grid[r, c] = 4
        return
    # Preverimo vse sosednje celice: če kateri izmed njih vsebuje ogenj (3), les se spremeni v ogenj
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue  # preskočimo samo trenutno celico
            rr = r + dr
            cc = c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                if old_grid[rr, cc] == 3:
                    new_grid[r, c] = 3
                    return
    # Če ni ognja, poskušamo premakniti les navzdol, če je spodnja celica prazna
    below = r + 1
    if below < rows and old_grid[below, c] == 0:
        new_grid[below, c] = 4
        new_grid[r, c] = 0
    else:
        # Če ni mogoče premikanje, les ostane na istem mestu
        new_grid[r, c] = 4

# Funkcija za posodobitev dima v simulaciji
def update_smoke(old_grid, new_grid, r, c):
    """
    Posodobi celico z dimom (vrednosti 5 in 6, ki predstavljata prehodna stanja dima).
    Pravila:
      - Če čas življenjske dobe dima (smoke_timer) doseže 0, se celica izklopi (postane prazna).
      - Dim se poskuša premakniti navzgor, če je to mogoče (simulira naravni vzpon dima).
      - Če ni mogoče premikanje navzgor, se poskusi premakniti bočno (levo/desno).
      - Če se dim premakne, se zmanjša njegov timer.
      
    Args:
        old_grid (numpy.ndarray): trenutna mreža pred posodobitvijo
        new_grid (numpy.ndarray): mreža, kjer se shranjujejo spremembe
        r, c (int): indeksi celice z dimom
    """
    rows, cols = old_grid.shape
    current_lifetime = smoke_timer[r, c]
    # Če je življenjska doba dima potekla, izklopimo celico
    if current_lifetime <= 0:
        new_grid[r, c] = 0
        return
    new_lifetime = current_lifetime - 1  # Zmanjšamo timer
    upward_candidates = []
    # Preverimo celice nad trenutno (vse tri možnosti: levo, sredina, desno)
    for dc in [-1, 0, 1]:
        nr, nc = r - 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if old_grid[nr, nc] == 0:
                upward_candidates.append((nr, nc))
    if upward_candidates:
        # Če je mogoče premikanje navzgor, izberemo naključno celico in premaknemo dim tja
        nr, nc = random.choice(upward_candidates)
        new_grid[nr, nc] = old_grid[r, c]
        smoke_timer[nr, nc] = new_lifetime
        new_grid[r, c] = 0
    else:
        # Če premikanje navzgor ni mogoče, preverimo stranske celice (levo in desno)
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
            # Če se dim ne more premakniti, ostane na istem mestu z zmanjšanim timerjem
            new_grid[r, c] = old_grid[r, c]
            smoke_timer[r, c] = new_lifetime

# Funkcija za posodobitev vode v simulaciji
def update_water(old_grid, new_grid, r, c):
    """
    Posodobi celico z vodo (vrednost 7) glede na tekoče količine vode in okoliške pogoje.
    Pravila za vodo:
      - Voda teče navzdol, če je pod celico dovolj prostora (prazna celica ali celica z vodo, kjer je še kapaciteta).
      - Količina vode v celici je shranjena v matrici water_levels, kjer je maksimalna kapaciteta 1.0.
      - Če voda ne more teči navzdol, se poskuša razporediti horizontalno (delitev vode med sosednje celice).
      - Če v celici ostane presežek vode (več kot 1.0), se poskuša premakniti navzgor.
      
    Args:
        old_grid (numpy.ndarray): trenutna mreža pred posodobitvijo
        new_grid (numpy.ndarray): mreža, kjer se shranjujejo spremembe
        r, c (int): indeksi celice z vodo
        
    Pomembno: 
        ko količina vode preseže 1.0, se v funkciji update_water sproži logika, ki poskuša presežek vode premakniti navzgor
    """
    amount = water_levels[r, c]  # Trenutna količina vode v celici
    if amount <= 0:
        return  # Če ni vode, nič ne naredimo
    # Preverimo, ali lahko voda teče navzdol
    if r + 1 < ROWS:
        # Če je spodnja celica že voda, izračunamo koliko vode še lahko sprejme (kapaciteta)
        if old_grid[r+1, c] == 7:
            capacity = max(0, 1.0 - water_levels[r+1, c])
        # Če je spodnja celica prazna, ima polno kapaciteto (1.0)
        elif old_grid[r+1, c] == 0:
            capacity = 1.0
        else:
            capacity = 0  # Drugi materiali preprečujejo pretok vode
        flow = min(amount, capacity)  # Količina vode, ki lahko teče navzdol
        if flow > 0:
            water_levels[r+1, c] += flow
            water_levels[r, c] -= flow
            new_grid[r+1, c] = 7  # Spodnja celica postane voda
            new_grid[r, c] = 7 if water_levels[r, c] > 0 else 0
            return
    # Če premikanje navzdol ni možno, poskušamo razporediti vodo horizontalno (levo in desno)
    for dc in [-1, 1]:
        nc = c + dc
        if 0 <= nc < COLS:
            if old_grid[r, nc] in (0, 7):
                if old_grid[r, nc] == 7:
                    capacity = max(0, 1.0 - water_levels[r, nc])
                else:
                    capacity = 1.0
                share = min(amount, 0.25, capacity)  # Omejimo količino, ki se lahko premakne horizontalno
                if share > 0:
                    water_levels[r, nc] += share
                    water_levels[r, c] -= share
                    new_grid[r, nc] = 7
                    new_grid[r, c] = 7 if water_levels[r, c] > 0 else 0
    # Če v celici ostane presežek vode (več kot 1.0), se poskuša premakniti navzgor
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

# Funkcija za posodobitev balona v simulaciji
def update_balloon(old_grid, new_grid, r, c):
    """
    Posodobi celico z balonom (vrednost 8).
    Pravila:
      - Balon se premika navzgor, saj je lahek.
      - Preveri celice nad trenutno pozicijo (levo, sredina, desno).
      - Če je katera izmed teh celic prazna, se balon premakne vanjo.
      - Če ni proste celice, se balon 'izprazni' (izbriše).
      
    Args:
        old_grid (numpy.ndarray): trenutna mreža pred posodobitvijo
        new_grid (numpy.ndarray): mreža, kjer se shranjujejo spremembe
        r, c (int): indeksi celice z balonom
    """
    rows, cols = old_grid.shape
    candidates = []
    # Generiramo kandidatske celice nad trenutnim položajem
    for dc in [-1, 0, 1]:
        nr, nc = r - 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    random.shuffle(candidates)  # Naključno premešamo možnosti
    for (nr, nc) in candidates:
        # Če je ciljno mesto prazno, premaknemo balon tja
        if old_grid[nr, nc] == 0:
            new_grid[nr, nc] = 8
            new_grid[r, c] = 0
            return
        else:
            # Če ni proste celice, balon "poteče" in se izbriše
            new_grid[r, c] = 0
            return
    # Če nobena poteza ni možna, balon ostane na istem mestu
    new_grid[r, c] = 8

# Opomba: Funkcija update_balloon je definirana dvakrat (tu je ponovitev).
# V simulacijah se običajno zagotovi samo ena definicija, vendar jo ohranjamo, ker je del danega primera.

# Funkcija za risanje mreže na zaslon
def draw_grid(screen, grid):
    """
    Nariše trenutno stanje mreže na zaslon z uporabo pygame.
    Pravila risanja:
      - Prazne celice se ne rišejo (ostanejo črne oz. barve ozadja).
      - Za celice, ki niso prazne, se nariše pravokotnik s pripadajočo barvo.
      - Poseben način barvanja se uporabi za vodo (celice s stanjem 7), kjer barva odseva količino vode.
      
    Args:
        screen (pygame.Surface): zaslon, na katerega risemo
        grid (numpy.ndarray): trenutna mreža s stanji celic
    """
    screen.fill(BLACK)  # Čistimo zaslon z ozadjem (črna barva)
    rows, cols = grid.shape
    # Gremo čez vsako celico in rišemo glede na njeno stanje
    for r in range(rows):
        for c in range(cols):
            state = grid[r, c]
            # Posebna obravnava za vodo: dinamično prilagajanje barve glede na količino vode
            if state == 7:
                amt = water_levels[r, c]
                amt = min(amt, 2.0)  # Omejimo maksimalno količino za barvno lestvico
                t = amt / 2.0  # Faktor za interpolacijo barve
                # Linearna interpolacija med dvema barvama (tu primer: med svetlo modro in toplo barvo)
                r_val = int(173 * (1-t) + 0 * t)
                g_val = int(216 * (1-t) + 0 * t)
                b_val = int(230 * (1-t) + 139 * t)
                color = (r_val, g_val, b_val)
            else:
                # Uporabimo preddefinirano barvno karto (BASE_COLOR_MAP) za ostala stanja
                color = BASE_COLOR_MAP[state]
            # Če celica ni prazna, narišemo pravokotnik, ki predstavlja stanje celice
            if state != 0:
                x = c * CELL_SIZE
                y = r * CELL_SIZE
                pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
    pygame.display.flip()  # Posodobimo zaslon, da se prikažejo spremembe

# Funkcija za risanje informacij in menija na zaslon
def draw_info(screen, generation, selected_state):
    """
    Nariše informacijski pas na vrhu zaslona, ki prikazuje:
      - Trenutno generacijo simulacije
      - Trenutno izbrano stanje (npr. ognj, pesek, les, voda, balon)
      - Meni s kratkimi navodili za izbiro stanj
      
    Args:
        screen (pygame.Surface): zaslon, na katerega risemo
        generation (int): trenutna generacija simulacije
        selected_state (int): trenutno izbrano stanje, ki ga uporabnik lahko vnaša
    """
    # Ustvarimo polprosojno površino za informacijski pas
    info_surface = pygame.Surface((WIDTH, 50))
    info_surface.set_alpha(200)
    info_surface.fill((50, 50, 50))
    screen.blit(info_surface, (0, 0))
    
    # Prikaz trenutne generacije simulacije
    gen_text = info_font.render(f"Generation: {generation}", True, WHITE)
    screen.blit(gen_text, (10, 5))
    
    # Določimo imena stanj, ki jih lahko uporabnik izbere
    state_names = {2: "SAND", 3: "FIRE", 4: "WOOD", 7: "WATER", 8: "BALLOON"}
    sel_text = info_font.render(f"Selected: {state_names.get(selected_state, '')}", True, WHITE)
    screen.blit(sel_text, (10, 25))
    
    # Meni z navodili za izbiro stanj; uporabnik pritisne tipke 1-5 za izbiro
    menu_text_lines = [
        "1  ->  FIRE",
        "2  ->  SAND",
        "3  ->  WOOD",
        "4  ->  WATER",
        "5  ->  BALLOON"
    ]
    box_width = 200
    box_height = 110
    box_x = WIDTH - box_width - 10
    box_y = 10
    # Ustvarimo ozadje za meni z rahlo prosojnostjo
    menu_bg = pygame.Surface((box_width, box_height))
    menu_bg.set_alpha(220)
    menu_bg.fill((30, 30, 30))
    screen.blit(menu_bg, (box_x, box_y))
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2)
    # Izpišemo vsako vrstico menija na zaslon
    for i, line in enumerate(menu_text_lines):
        text_surface = menu_font.render(line, True, WHITE)
        text_x = box_x + 10
        text_y = box_y + 5 + i * 22
        screen.blit(text_surface, (text_x, text_y))
    pygame.display.update()

# Funkcija za pretvorbo pozicije miške v indeks celice v mreži
def mouse_to_grid_pos(mx, my):
    """
    Pretvori koordinate miške (v pikslah) v indekse celice glede na velikost celice.
    
    Args:
        mx (int): x-koordinata miške
        my (int): y-koordinata miške
        
    Returns:
        tuple: (r, c) indeks vrstice in stolpca v mreži
    """
    c = mx // CELL_SIZE
    r = my // CELL_SIZE
    return r, c

# Funkcija za izračun naslednje generacije simulacije z uporabo vseh pravil
def next_generation(grid):
    """
    Ustvari novo generacijo mreže tako, da uporabi pravila za vse različne tipe celic.
    Postopek:
      1. Najprej posodobi ogenj.
      2. Nato posodobi dim.
      3. Sledi posodobitev peska (od spodaj navzgor, da se simulira gravitacija).
      4. Posodobi les.
      5. Posodobi vodo.
      6. Na koncu posodobi balon.
      
    Args:
        grid (numpy.ndarray): trenutna mreža s stanji celic
        
    Returns:
        numpy.ndarray: nova mreža po uporabljenih pravilih
    """
    rows, cols = grid.shape
    new_grid = np.copy(grid)
    # Posodobi ogenj: iteriramo po vseh celicah in če je celica z ognjem, jo posodobimo
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 3:
                update_fire(grid, new_grid, r, c)
    # Posodobi dim: celice s stanjem 5 in 6 (prehodni stanja dima)
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] in (5, 6):
                update_smoke(grid, new_grid, r, c)
    # Posodobi pesek: iteriramo od spodaj navzgor, da omogočimo gravitacijski učinek
    for r in range(rows-1, -1, -1):
        for c in range(cols):
            if grid[r, c] == 2:
                update_sand(grid, new_grid, r, c)
    # Posodobi les: prav tako iteriramo od spodaj navzgor
    for r in range(rows-1, -1, -1):
        for c in range(cols):
            if grid[r, c] == 4:
                update_wood(grid, new_grid, r, c)
    # Posodobi vodo: iteriramo po vseh celicah, kjer je voda
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 7:
                update_water(grid, new_grid, r, c)
    # Posodobi balon: iteriramo po vseh celicah, kjer je balon
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 8:
                update_balloon(grid, new_grid, r, c)
    return new_grid

# Ponovna definicija funkcije za posodobitev balona (enaka kot prej, zato je dejansko podvojena)
def update_balloon(old_grid, new_grid, r, c):
    """
    Ponovna definicija funkcije za posodobitev balona (vrednost 8).
    Funkcija deluje identično kot prej opisana funkcija update_balloon.
    
    Args:
        old_grid (numpy.ndarray): trenutna mreža pred posodobitvijo
        new_grid (numpy.ndarray): mreža, kjer se shranjujejo spremembe
        r, c (int): indeksi celice z balonom
    """
    rows, cols = old_grid.shape
    candidates = []
    for dc in [-1, 0, 1]:
        nr, nc = r - 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    random.shuffle(candidates)
    for (nr, nc) in candidates:
        if old_grid[nr, nc] == 0:
            new_grid[nr, nc] = 8
            new_grid[r, c] = 0
            return
        else:
            new_grid[r, c] = 0
            return
    new_grid[r, c] = 8

# Glavna funkcija, ki izvaja 2D simulacijo
def run_simulation_2D():
    """
    Izvede glavno zanko 2D simulacije celičnih avtomatov.
    Postopek:
      - Inicializira mrežo z naključno postavljenimi stenami in peskom.
      - Shranjuje statične stene (celice, kjer je vrednost 1), ki se ne spreminjajo med simulacijo.
      - Spremlja generacijo simulacije.
      - V zanki spremlja vhod uporabnika (tipkovnica in miška) za prekinitev, izbiro stanja ali risanje celic.
      - Vsaki iteraciji posodobi mrežo z uporabo pravil iz next_generation.
      - Če mreža doseže stabilno stanje (brez sprememb), simulacija se začasno ustavi.
    """
    global selected_state
    # Ustvarimo začetno mrežo s stenami in peskom glede na začetne deleže
    grid = create_initial_grid(ROWS, COLS, INITIAL_LIVE_RATIO, INITIAL_SAND_RATIO)
    # Shranimo statične stene, da jih kasneje ne spreminjamo (ostanejo vedno stene)
    static_walls = (grid == 1)
    generation = 0
    running = True
    paused = False
    selected_state = 3  # Privzeta izbira: FIRE (ogenj)

    # Glavna zanka simulacije
    while running:
        clock.tick(FPS)  # Omejimo hitrost osveževanja simulacije
        for event in pygame.event.get():
            # Če uporabnik zapre okno, končamo simulacijo
            if event.type == pygame.QUIT:
                running = False
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    return
                # Spreminjanje izbranega stanja na podlagi tipk (1: oganj, 2: pesek, 3: les, 4: voda, 5: balon)
                elif event.key == pygame.K_1:
                    selected_state = 3
                elif event.key == pygame.K_2:
                    selected_state = 2 
                elif event.key == pygame.K_3:
                    selected_state = 4 
                elif event.key == pygame.K_4:
                    selected_state = 7  
                elif event.key == pygame.K_5:
                    selected_state = 8  
                # Če je simulacija začasno ustavljena, tipka lahko nadaljuje gibanje
                elif paused:
                    paused = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Ob kliku z levim gumbom spremenimo stanje izbrane celice glede na trenutno izbrano stanje
                if event.button == 1:
                    mx, my = event.pos
                    r, c = mouse_to_grid_pos(mx, my)
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        grid[r, c] = selected_state
                        # Če je izbrana voda, nastavimo začetno količino vode na 1.0
                        if selected_state == 7:
                            water_levels[r, c] = 1.0
                    if paused:
                        paused = False

        # Narišemo trenutno stanje mreže in informacijski pas
        draw_grid(screen, grid)
        draw_info(screen, generation, selected_state)
        # Izračunamo naslednjo generacijo z uporabo pravil simulacije
        new_grid = next_generation(grid)
        # Zagotovimo, da statične stene ostanejo nespremenjene (vedno vrednost 1)
        new_grid[static_walls] = 1
        # Preverimo, če je mreža stabilna (ni sprememb med generacijami)
        if np.array_equal(new_grid, grid):
            if not paused:
                print(f"Stable state reached at generation {generation}. Pausing simulation...")
            paused = True
        else:
            paused = False
        # Če simulacija ni ustavljena, preštejemo generacijo in posodobimo mrežo
        if not paused:
            generation += 1
            grid = new_grid