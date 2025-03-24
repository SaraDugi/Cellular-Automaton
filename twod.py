import pygame
import numpy as np
import random

# Uvozimo nabor konstant iz "constants.py". Ta datoteka ponavadi vsebuje 
# vnaprej določene vrednosti, da jih lahko enostavno spreminjamo na enem mestu.
from constants import (
    WIDTH, HEIGHT, CELL_SIZE, FPS,     # Širina, višina okna, velikost celice, sličice na sekundo
    BLACK, WHITE,                      # Osnovni barvi (črna, bela)
    ROWS, COLS,                        # Število vrstic in stolpcev v mreži
    INITIAL_LIVE_RATIO,                # Začetno razmerje (verjetnost), s katero ustvarjamo 'zid' ali kaj podobnega
    INITIAL_SAND_RATIO,                # Začetno razmerje za 'pesek'
    SMOKE_LIFETIME,                    # Koliko korakov živi dim (koliko ciklov)
    BASE_COLOR_MAP                     # Slovar/Map, ki pove, kakšna barva ustreza kateremu stanju
)


pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Nastavimo napis/ime okna, ki se pokaže na vrhu (npr. v naslovni vrstici).
pygame.display.set_caption("2D Cellular Automata: Wall/Sand/Fire/Wood/Smoke/Water/Balloon")

# Ustvarimo objekt 'clock' za nadzor hitrosti glavne zanke (FPS - frames per second).
clock = pygame.time.Clock()

# Dve pisavi za prikazovanje besedila na zaslonu:
info_font = pygame.font.SysFont("Arial", 16)           # Manjša, za osnovne informacije (generacija itd.)
menu_font = pygame.font.SysFont("Arial", 18, bold=True) # Meni z odebeljeno pisavo

# Matrika (2D numpy array) 'smoke_timer' hrani za vsako celico, koliko 'življenja' 
# dima je še preostalo, če je tam dim (state=5 ali 6). Če pride do 0, dim izgine.
smoke_timer = np.zeros((ROWS, COLS), dtype=int)

# Matrika 'water_levels' za vsako celico hrani količino vode (float),
# da lahko simuliramo delno zapolnitev (npr. 0.5 pomeni pol celice vode).
water_levels = np.zeros((ROWS, COLS), dtype=float)

# 'selected_state' predstavlja, kateri material/stanje trenutno postavljamo 
# z levičnim klikom miške. Privzeto vrednost nastavimo na 3 (ogenj).
selected_state = 3

def create_initial_grid(rows, cols, wall_ratio, sand_ratio):
    """
    Ustvari začetno mrežo velikosti rows x cols.
    V vsaki celici, glede na naključje in razmerja (wall_ratio, sand_ratio), 
    nastavimo določeno stanje (zid ali pesek).
    - row_ratio: delež (verjetnost), da bo celica zid (state=1).
    - sand_ratio: delež (verjetnost), da bo celica pesek (state=2),
      glede na tiste celice, ki niso bile že zid.
    Vse ostale celice, ki ne padejo v te dve kategoriji, bodo prazne (0).
    """
    grid = np.zeros((rows, cols), dtype=int)  # Najprej ustvarimo vse s stanjem 0 (prazno)
    for r in range(rows):
        for c in range(cols):
            rnd = random.random()  # Naključno število med 0 in 1
            if rnd < wall_ratio:
                grid[r, c] = 1  # Zid (Wall)
            elif rnd < wall_ratio + sand_ratio:
                grid[r, c] = 2  # Pesek (Sand)
            else:
                grid[r, c] = 0  # Prazno
    return grid

def update_sand(old_grid, new_grid, r, c):
    """
    Posodobi gibanje peska (state=2) v celici (r, c).
    Pesek se poskuša spustiti navzdol ali diagonalno, če je spodaj prosto (prazno) ali voda.
    - old_grid: prejšnje stanje mreže (za branje)
    - new_grid: novo stanje mreže (za pisanje sprememb)
    - r, c: trenutna pozicija peska.
    """
    rows, cols = old_grid.shape
    below = r + 1  # indeks vrstice neposredno spodaj
    
    # Najprej preverimo, ali je spodaj znotraj meja in ali je tam prazno (0) ali voda (7).
    # Če je, naj pesek "pade" tja.
    if below < rows and (old_grid[below, c] == 0 or old_grid[below, c] == 7):
        new_grid[below, c] = 2  # Spodnjo celico naredimo pesek
        new_grid[r, c] = 0      # Trenutna celica postane prazna
        if old_grid[below, c] == 7:
            # Če je tam voda, jo "izpodrinemo". Količino vode nastavimo na 0.
            water_levels[below, c] = 0
    else:
        # Če pesek ne more padati naravnost navzdol, poskuša diagonalno (spodaj levo/spodaj desno).
        candidates = []
        if below < rows:
            # Spodaj levo
            if c - 1 >= 0 and old_grid[below, c-1] == 0:
                candidates.append((below, c-1))
            # Spodaj desno
            if c + 1 < cols and old_grid[below, c+1] == 0:
                candidates.append((below, c+1))
        # Če obstaja vsaj en diagonalni kandidat, izberemo naključnega in ga tja premaknemo.
        if candidates:
            nr, nc = random.choice(candidates)
            new_grid[nr, nc] = 2
            new_grid[r, c] = 0
        else:
            # Drugače pesek ostane, kjer je.
            new_grid[r, c] = 2

def update_fire(old_grid, new_grid, r, c):
    """
    Posodobi stanje ognja (state=3).
    Ogenj se navadno širi navzdol oz. diagonalno navzdol na celice,
    ki so lahko: prazne (0), pesek (2), ali les (4).
    
    Če najde les (4), ga spremeni v "ognjeni les" (5) ali "dim" (6) – 
    kar je v tej implementaciji malo pomešano, a ideja je, da se les vname in ustvari dim.
    Dimu nastavimo preostali "lifetime" v matriki 'smoke_timer'.
    """
    rows, cols = old_grid.shape
    
    # Ustvarimo seznam kandidatov (celice neposredno pod ognjem: r+1, c-1; r+1, c; r+1, c+1).
    candidates = []
    for dc in [-1, 0, 1]:
        nr, nc = r + 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    
    # Premešamo, da ogenj ne gre vedno v isto smer.
    random.shuffle(candidates)
    
    moved = False  # Pove, ali je ogenj uspel "preskočiti".
    for (nr, nc) in candidates:
        target = old_grid[nr, nc]
        # Če je tarča prazna (0), pesek (2) ali les (4), ogenj preskoči.
        if target in (0, 2, 4):
            if target == 4:
                new_grid[nr, nc] = 5  # Les -> 5 (lahko interpretiramo kot "ognjeni les" ali "dim+les")
            else:
                new_grid[nr, nc] = 6  # Drugače -> 6 (dim)
            smoke_timer[nr, nc] = SMOKE_LIFETIME  # Nastavimo, koliko korakov bo dim ostal
            new_grid[r, c] = 0  # Trenutno mesto ognja postane prazno (ker se je ogenj premaknil naprej)
            moved = True
            break
    
    if not moved:
        # Če ogenj ni našel primerne celice za preskok, ostane na istem mestu (3).
        new_grid[r, c] = 3

def update_wood(old_grid, new_grid, r, c):
    """
    Posodobi stanje lesa (state=4).
    - Les lahko zgori, če je v neposredni bližini ogenj (3).
    - Če je spodaj voda (7), se lahko 'zmoči' (glede na logiko), tukaj ostaja state=4.
    - Prav tako lahko "pade" navzdol, če je spodnja celica prazna (to je prikazano kot, da je les mobilen).
    """
    rows, cols = old_grid.shape
    
    # Če je spodaj voda, lahko les reagira (npr. ostane enak, ker je zmočen, a ne zgori).
    # Tu samo nastavimo new_grid[r, c] = 4 in se vrnemo.
    if r + 1 < rows and old_grid[r+1, c] == 7:
        new_grid[r, c] = 4
        return
    
    # Preverimo 8 sosedov (okoli lesene celice). Če najdemo ogenj (3), 
    # naj les takoj preide v stanje ogenj (3).
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue  # Ne gledamo samega sebe
            rr = r + dr
            cc = c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                if old_grid[rr, cc] == 3:
                    new_grid[r, c] = 3  # Les zagori
                    return
    
    # Če ni ognja v bližini, preverimo, ali je spodnja celica prazna (0) — les pade navzdol.
    below = r + 1
    if below < rows and old_grid[below, c] == 0:
        new_grid[below, c] = 4
        new_grid[r, c] = 0
    else:
        # Sicer ostane les tak, kot je.
        new_grid[r, c] = 4

def update_smoke(old_grid, new_grid, r, c):
    """
    Posodobi stanje dima (state=5 ali 6).
    Dim se navadno dviga navzgor (če je možno), sicer poskuša levo-desno. 
    Če mu 'lifetime' (smoke_timer[r, c]) poteče, dim izgine (celica postane 0).
    """
    rows, cols = old_grid.shape
    
    # Pridobimo preostali čas 'življenja' za dim v tej celici.
    current_lifetime = smoke_timer[r, c]
    
    if current_lifetime <= 0:
        # Če je lifetime 0 (ali manj), dim se razkadi, postane prazno.
        new_grid[r, c] = 0
        return
    
    # Zmanjšamo lifetime za 1.
    new_lifetime = current_lifetime - 1
    
    # Najprej poskusimo navzgor (r-1, c-1), (r-1, c), (r-1, c+1), če je prazno.
    upward_candidates = []
    for dc in [-1, 0, 1]:
        nr, nc = r - 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            # Če je ta celica prazna (0), dim lahko tja preskoči.
            if old_grid[nr, nc] == 0:
                upward_candidates.append((nr, nc))
    
    if upward_candidates:
        # Če je vsaj ena prazna celica zgoraj, izberemo eno naključno in se premaknemo tja.
        nr, nc = random.choice(upward_candidates)
        new_grid[nr, nc] = old_grid[r, c]    # Tam postavimo dim
        smoke_timer[nr, nc] = new_lifetime   # Nastavimo novi lifetime
        new_grid[r, c] = 0                   # Trenutna postane prazna
    else:
        # Če ne moremo navzgor, poskusimo levo ali desno v isti vrstici, če je tam prazno.
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
            # Če ne more navzgor, ne more levo ali desno, ostane na mestu in 
            # samo znižamo lifetime.
            new_grid[r, c] = old_grid[r, c]
            smoke_timer[r, c] = new_lifetime

def update_water(old_grid, new_grid, r, c):
    """
    Posodobi stanje vode (state=7). Glavni cilj je simulirati pretakanje vode (float 'amount'),
    ki se lahko razliva navzdol, levo, desno, in v posebnih primerih tudi navzgor (če ima 'pritisk').

    Zakaj vse to?
    -----------------------------------------
    1. Voda se v naravi premika tja, kjer je prosti prostor (prazno) ali kjer je 
       delno napolnjena voda, ki jo lahko dopolni. 
       Zato gledamo tja (r+1, c) - spodaj, da se voda razlije navzdol.
    2. Če se ne more povsem navzdol, preizkusimo levo in desno (r, c +/- 1).
       V naravi se voda rada razliva vstran, če je spodaj blokirano.
    3. Če je v celici več vode, kot je “1.0” (to interpretiramo kot celica je polna 
       in ima "višek/pritisk"), se lahko prelije tudi navzgor (r-1). 
       To je manj “realno” v enostavni simulaciji, a omogoča simulacije 
       hidrostatičnega pritiska in dvigovanja vode, če je prostor zgoraj manj poln.
    
    Parametri:
    - old_grid: staro stanje mreže (iz katere prebiramo, kje je voda in koliko jo je).
    - new_grid: novo stanje mreže (kamor pišemo spremembe).
    - (r, c): vrstica, stolpec v mreži za to celico, ki je označena kot voda (7).

    Za vsako celico vode najprej pridobimo 'amount' = water_levels[r, c]. 
    Če je ta <= 0, pomeni, da v resnici tam vode ni, samo state je narobe nastavljen – takrat 
    takoj 'return', ker ni ničesar za premik.

    Nato sistematično preverjamo navzdol, nato vstran, in nazadnje navzgor. 
    Kadarkoli najdemo priložnost za “tok” (flow > 0), izvedemo prenos:
      - water_levels[r, c] -= flow
      - water_levels[ciljna_celica] += flow
      - new_grid[...] = 7, ipd.
    """
    
    amount = water_levels[r, c]  # Koliko vode je v tej celici
    
    # Če ni nič vode, ne rabimo nič delati.
    if amount <= 0:
        return
    
    # 1) Poglejmo, če lahko teče navzdol (r+1, c).
    if r + 1 < ROWS:
        if old_grid[r+1, c] == 7:
            # Če je spodnja celica tudi voda, preverimo, koliko jo je tam.
            capacity = max(0, 1.0 - water_levels[r+1, c])
        elif old_grid[r+1, c] == 0:
            # Če je prazno, lahko tja 'spravimo' 1.0 enoto vode.
            capacity = 1.0
        else:
            capacity = 0
        
        # flow je, koliko vode se bo dejansko prelilo.
        flow = min(amount, capacity)
        if flow > 0:
            water_levels[r+1, c] += flow
            water_levels[r, c] -= flow
            new_grid[r+1, c] = 7
            # Če je v izvorni celici še voda, ostanemo pri stanju 7, 
            # sicer ga nastavimo na 0 (prazno).
            new_grid[r, c] = 7 if water_levels[r, c] > 0 else 0
            return  # ker smo vodni tok že izvedli
    
    # 2) Če ne moremo navzdol, poskusimo levo in desno, da se razlije voda.
    for dc in [-1, 1]:
        nc = c + dc
        if 0 <= nc < COLS:
            if old_grid[r, nc] in (0, 7):
                # capacity ocenimo glede na to, koliko vode je že tam.
                if old_grid[r, nc] == 7:
                    capacity = max(0, 1.0 - water_levels[r, nc])
                else:
                    capacity = 1.0
                # Pretok omejimo na 0.25 enote, da se razlivanje ne zgodi v celoti naenkrat.
                share = min(amount, 0.25, capacity)
                if share > 0:
                    water_levels[r, nc] += share
                    water_levels[r, c] -= share
                    new_grid[r, nc] = 7
                    new_grid[r, c] = 7 if water_levels[r, c] > 0 else 0
    
    # 3) Če imamo še vedno več kot 1.0 vode, obstaja pritisk navzgor, 
    #    zato del vode lahko steče gor.
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

def update_balloon(old_grid, new_grid, r, c):
    """
    Posodobi stanje balona (state=8).
    Ideja: balon se želi dvigniti navzgor (r-1), če je tam prazno (0). 
    Včasih preverimo tudi levo/desno zgoraj. 
    Če je vse zapolnjeno, ga lahko 'raznese' (tukaj ga nastavimo na 0).
    """
    rows, cols = old_grid.shape
    candidates = []
    # Pregledamo tri možne pozicije nad balonom: (r-1, c-1), (r-1, c), (r-1, c+1).
    for dc in [-1, 0, 1]:
        nr, nc = r - 1, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            candidates.append((nr, nc))
    
    # Premešamo, da je malce naključno.
    random.shuffle(candidates)
    
    for (nr, nc) in candidates:
        # Če je nova pozicija (nr, nc) prazna, se balon premakne tja.
        if old_grid[nr, nc] == 0:
            new_grid[nr, nc] = 8
            new_grid[r, c] = 0
            return
        else:
            # Če ni prazno, tu interpretiramo, da se balon 'razpoči'.
            new_grid[r, c] = 0
            return
    
    # Če ni uspelo nobenemu od kandidatov, balon ostane na istem mestu.
    new_grid[r, c] = 8

def draw_grid(screen, grid):
    """
    Nariše vso mrežo na zaslon.
    - screen: Pygame površina, kjer rišemo.
    - grid: numpy 2D polje stanj, npr. grid[r, c] = 7 pomeni voda v vrstici r, stolpcu c.
    """
    screen.fill(BLACK)  # Najprej počistimo zaslon s črno barvo
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            state = grid[r, c]
            if state == 7:
                # Če je celica voda (7), izračunamo barvo glede na 'amount' vode (water_levels[r, c]).
                amt = water_levels[r, c]
                amt = min(amt, 2.0)  # Omejimo, da ne gredo barvne vrednosti predaleč.
                t = amt / 2.0
                # Linearna interpolacija barve med svetlo modro in temnejšo modro (ali modro-zelene odtenke).
                r_val = int(173 * (1 - t) + 0 * t)
                g_val = int(216 * (1 - t) + 0 * t)
                b_val = int(230 * (1 - t) + 139 * t)
                color = (r_val, g_val, b_val)
            else:
                # Za druga stanja uporabimo barvo iz slovarja 'BASE_COLOR_MAP'.
                color = BASE_COLOR_MAP[state]
            
            # Praznih (0) ne rišemo, ker je ozadje že črno, 
            # čeprav bi lahko narisali črn kvadrat — enako je.
            if state != 0:
                # Pretvorimo (r, c) v (x, y), kjer x je stolpec*c, y je vrstica*r
                x = c * CELL_SIZE
                y = r * CELL_SIZE
                pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
    
    pygame.display.flip()  # Osvežimo zaslon, da se narišejo vse spremembe

def draw_info(screen, generation, selected_state):
    """
    Prikaže informacijsko vrstico na vrhu (število generacij, izbrano stanje)
    in 'meni' na desni, ki prikazuje tipke za izbiro stanja.
    """
    # Ustvarimo polprozorno površino (50 px visoko), da pokrije vrh okna.
    info_surface = pygame.Surface((WIDTH, 50))
    info_surface.set_alpha(200)  # Nastavimo prosojnost
    info_surface.fill((50, 50, 50))  # Temna siva barva
    screen.blit(info_surface, (0, 0)) # 'Nalepimo' površino na vrh okna (koordinate (0,0))
    
    # Prikaz "Generation: X"
    gen_text = info_font.render(f"Generation: {generation}", True, WHITE)
    screen.blit(gen_text, (10, 5))
    
    # Imena stanj, da uporabniku pokažemo, kaj ima izbrano.
    state_names = {2: "SAND", 3: "FIRE", 4: "WOOD", 7: "WATER", 8: "BALLOON"}
    sel_text = info_font.render(f"Selected: {state_names.get(selected_state, '')}", True, WHITE)
    screen.blit(sel_text, (10, 25))
    
    # Desni meni, ki prikazuje ukaze tipk 1-5.
    menu_text_lines = [
        "1  ->  FIRE",
        "2  ->  SAND",
        "3  ->  WOOD",
        "4  ->  WATER",
        "5  ->  BALLOON"
    ]
    
    # Definiramo velikost pravokotnika, v katerem bo prikazan 'meni'.
    box_width = 200
    box_height = 110
    box_x = WIDTH - box_width - 10
    box_y = 10
    
    menu_bg = pygame.Surface((box_width, box_height))
    menu_bg.set_alpha(220)     # Delno prozorna podlaga
    menu_bg.fill((30, 30, 30)) # Temno siva podlaga
    screen.blit(menu_bg, (box_x, box_y))
    
    # Obroba okrog menija (bela črta).
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2)
    
    # Narišemo vsako vrstico menija:
    for i, line in enumerate(menu_text_lines):
        text_surface = menu_font.render(line, True, WHITE)
        text_x = box_x + 10
        text_y = box_y + 5 + i * 22
        screen.blit(text_surface, (text_x, text_y))
    
    pygame.display.update()  # Posodobimo del zaslona, kjer so info element

def mouse_to_grid_pos(mx, my):
    """
    Pretvori koordinati miške (mx, my) iz slikovnih pik v (r, c) indeksa mreže.
    - mx // CELL_SIZE daje stolpec (c),
    - my // CELL_SIZE daje vrstico (r).
    Vendar pozor: tu se odločimo, da bo r = my // CELL_SIZE in c = mx // CELL_SIZE, 
    da ohranjamo logiko (r -> vertikala, c -> horizontala).
    """
    c = mx // CELL_SIZE
    r = my // CELL_SIZE
    return r, c

def next_generation(grid):
    """
    Izvede en cikel (generacijo) simulacije. 
    Gremo čez vsako stanje (ogenj, dim, pesek, les, voda, balon) 
    v ustreznem vrstnem redu, da posnemamo naravne zakonitosti.
    Vrne 'new_grid' kot novo stanje po tej generaciji.
    """
    rows, cols = grid.shape
    new_grid = np.copy(grid)  # Naredimo kopijo, da ne spreminjamo sproti originala.

    # 1) Ogenj (3) obdelamo najprej (od zgoraj navzdol).
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 3:
                update_fire(grid, new_grid, r, c)

    # 2) Dim (5 ali 6) obdelamo potem (tudi od zgoraj navzdol).
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] in (5, 6):
                update_smoke(grid, new_grid, r, c)

    # 3) Pesek (2) obdelamo od spodaj navzgor, ker "pada".
    for r in range(rows-1, -1, -1):
        for c in range(cols):
            if grid[r, c] == 2:
                update_sand(grid, new_grid, r, c)

    # 4) Les (4) prav tako obdelamo od spodaj navzgor, ker lahko pade dol.
    for r in range(rows-1, -1, -1):
        for c in range(cols):
            if grid[r, c] == 4:
                update_wood(grid, new_grid, r, c)

    # 5) Voda (7) obdelamo od zgoraj navzdol (logika pretakanja).
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 7:
                update_water(grid, new_grid, r, c)

    # 6) Balon (8) obdelamo od zgoraj navzdol, ker se dviga gor.
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 8:
                update_balloon(grid, new_grid, r, c)

    return new_grid

# V kodi je še enkrat definirana enaka funkcija 'update_balloon',
# kar prepiše prejšnjo (enaka vsebina). Če jo odstranimo, vseeno deluje.
def update_balloon(old_grid, new_grid, r, c):
    """
    Druga, enaka definicija update_balloon (podvojenost).
    Ta prepiše prvo, zato se dejansko uporablja ta koda.
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

def run_simulation_2D():
    """
    Glavna funkcija za zagon 2D simulacije (Wall/Sand/Fire/Wood/Smoke/Water/Balloon).
    Tu se ustvari začetna mreža, nato v while-zanki obdelujemo dogodke 
    (miška, tipke) in za vsak korak prikažemo ter posodobimo svet.
    """
    global selected_state  # Omogoča, da spreminjamo to spremenljivko znotraj funkcije
    
    # Ustvarimo začetno mrežo z naključnim razporedom zidov in peska.
    grid = create_initial_grid(ROWS, COLS, INITIAL_LIVE_RATIO, INITIAL_SAND_RATIO)
    
    # Shrani pozicije, kjer so zidovi (state=1) – te želimo ohraniti nespremenljive.
    static_walls = (grid == 1)
    
    generation = 0  # števec generacij (korakov simulacije)
    running = True  # boolean, ki upravlja glavno zanko
    paused = False  # ali je simulacija ustavljena
    
    # Privzeto izbrano orodje je FIRE (3)
    selected_state = 3

    while running:
        # Poskrbimo, da se zanka izvaja največ 'FPS' krat na sekundo.
        clock.tick(FPS)

        # Obdelava dogodkov (tipke, miška itd.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Če uporabnik zapre okno, ustavimo zanko.
                running = False
                return
            
            elif event.type == pygame.KEYDOWN:
                # Pritisnjena je bila tipka.
                if event.key == pygame.K_ESCAPE:
                    # ESC -> izhod iz simulacije, vrnemo se npr. v meni ali zapremo.
                    running = False
                    return
                elif event.key == pygame.K_1:
                    selected_state = 3  # FIRE
                elif event.key == pygame.K_2:
                    selected_state = 2  # SAND
                elif event.key == pygame.K_3:
                    selected_state = 4  # WOOD
                elif event.key == pygame.K_4:
                    selected_state = 7  # WATER
                elif event.key == pygame.K_5:
                    selected_state = 8  # BALLOON
                elif paused:
                    # Če je bilo simuliranje zaustavljeno in pritisnemo neko tipko, 
                    # spet sprožimo (od-pavziramo).
                    paused = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Levi klik miške -> postavimo material v mrežo na mesto klika.
                if event.button == 1:  # 1 = levi gumb
                    mx, my = event.pos  # Koordinati miške v slikovnih pikah
                    r, c = mouse_to_grid_pos(mx, my)  # Indeksi mreže
                    
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        # Nastavimo izbran state v mrežo
                        grid[r, c] = selected_state
                        # Če je to voda (7), nastavimo količino vode na 1.0
                        if selected_state == 7:
                            water_levels[r, c] = 1.0
                    # Če smo bili na "pause", ga izklopimo, da se simulacija nadaljuje.
                    if paused:
                        paused = False
        
        # Narišemo trenutno stanje mreže in informacijsko vrstico (generacija, izbrano orodje).
        draw_grid(screen, grid)
        draw_info(screen, generation, selected_state)
        
        # Izračunamo naslednje stanje simulacije.
        new_grid = next_generation(grid)
        
        # 'static_walls' so celice, kjer je grid == 1. 
        # Tem celicam v new_grid ponovno nastavimo 1, 
        # da jih ne prepiše npr. v ogenj ali kaj drugega.
        new_grid[static_walls] = 1
        
        # Če je mreža po naslednji generaciji enaka prejšnji, pomeni, 
        # da je simulacija v stabilnem stanju (nič se ne spreminja).
        if np.array_equal(new_grid, grid):
            if not paused:
                print(f"Stable state reached at generation {generation}. Pausing simulation...")
            paused = True
        else:
            paused = False
        
        # Če nismo na pavzi, povečamo števec generacije in zamenjamo mrežo z novo.
        if not paused:
            generation += 1
            grid = new_grid