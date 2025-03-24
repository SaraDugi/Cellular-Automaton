import numpy as np
import pygame

def generate_rule(rule_number):
    """
    Ta funkcija generira "pravilo" za 1D celični avtomat iz podanega števila (0-255).
    
    Razlaga:
    ----------
    - 'rule_number' je celo število med 0 in 255, ki ga zapišemo v 8-bitni (binarni) obliki.
    - primer: če je rule_number = 30, se v binarni obliki to zapiše kot '00011110'.
    - V 1D avtomatih obstaja 8 možnih kombinacij sosednjih celic (levi, srednji, desni).
      Te kombinacije so predstavljene kot 3-bitno število (od 111 = 7 do 000 = 0).
      Vsaki kombinaciji dodelimo izhod (0 ali 1) glede na pozicijo v binarnem nizu 'rule_number'.

    Izvedba:
    ----------
    - Najprej pretvorimo 'rule_number' v 8-bitni binarni niz (binary_string).
    - Nato gremo skozi vseh 8 kombinacij (i = 0..7). 
      Vsak 'i' zapišemo kot 3-bitni niz (npr. i=5 -> '101'), 
      pretvorimo v tuple (1,0,1) in to nastavimo kot ključ.
    - Preberemo ustrezno vrednost (0 ali 1) iz 'binary_string' in shranimo v slovar 'rule'.
      'rule[key_tuple]' = 1 ali 0.

    Vrnemo: slovar (dict), kjer je ključ 3-terica (left, mid, right), vrednost pa 0/1.
    """
    # V 8-bitni obliki: npr. 30 -> '00011110'
    binary_string = format(rule_number, '08b')
    rule = {}

    for i in range(8):
        # 'i' pretvorimo v 3-bitni niz, npr. i=5 -> '101'
        key_tuple = tuple(map(int, format(i, '03b')))
        # ker je binarni niz obrnjen (največja kombinacija 111 je na začetku),
        # pa želimo 111 prebrati z indexom 0, 110 z indexom 1 ipd., 
        # zato uporabljamo 'binary_string[7 - i]'.
        rule[key_tuple] = int(binary_string[7 - i])
    return rule


def run_automaton_1D(rule_number, width, height, cell_size):
    """
    Izvede osnovno simulacijo 1D celičnega avtomata s podanim 'rule_number'.
    
    Parametri:
    ----------
    - rule_number: 0..255, določa, kako se izračunava nova generacija.
    - width, height: dimenzije zaslona/okna v slikovnih pikah.
    - cell_size: velikost celice (v slikovnih pikah) po vodoravni in navpični smeri.

    Postopek:
    ----------
    1) Določimo, koliko vrstic (rows) in stolpcev (cols) bo v mreži:
         rows = height // cell_size
         cols = width // cell_size
    2) Ustvarimo 2D numpy polje (grid) z vrednostmi 0 (mrtvo/prazno).
    3) V prvi vrstici (r=0) postavimo celico v sredini kot 1 (živo), 
       da dobimo 'začetni vzorec'.
    4) Pridobimo 'rule' s pomočjo funkcije generate_rule(rule_number), 
       ki vrne slovar za 8 možnih kombinacij.
    5) Gremo po vrsticah od r=1 do r=(rows-1) in za vsako celico c (razen na robovih)
       preberemo sosednje celice (left, mid, right) iz prejšnje vrstice (r-1).
       - Ključ = (left, mid, right)
       - Nova vrednost = rule[key], kjer je key 3-terica (0 ali 1).
    6) Vrnemo 2D array, ki ima v vsaki vrstici rezultat 1D avtomata za ta 'korak'.

    Vrne:
    ----------
    grid: 2D numpy array, kjer je vsaka vrstica ena generacija 1D avtomata.
    """
    rows = height // cell_size
    cols = width // cell_size

    # Ustvarimo mrežo rows x cols, kjer vse vrednosti zaenkrat nastavimo na 0.
    grid = np.zeros((rows, cols), dtype=int)

    # V prvi vrstici (r=0) damo '1' na sredino, da dobimo zagon.
    # Torej, pribl. pol stolpcev od leve
    grid[0, cols // 2] = 1  

    # Ustvarimo pravilo, ki bo slovar z možnimi kombinacijami, npr. (1,1,1)->0, (1,1,0)->1 itd.
    rule = generate_rule(rule_number)

    # Izračunamo vsako naslednjo vrstico na osnovi prejšnje (od r=1 naprej).
    for r in range(1, rows):
        for c in range(1, cols - 1):
            # Preberemo sosednje vrednosti iz vrstice r-1
            left  = grid[r - 1, c - 1]
            mid   = grid[r - 1, c]
            right = grid[r - 1, c + 1]
            # Določimo novo vrednost glede na rule
            grid[r, c] = rule.get((left, mid, right), 0)

    return grid


def draw_1D_automaton(screen, grid, cell_size, color, background):
    """
    Nariše rezultat 1D avtomata (grid) na zaslon (screen) s Pygame-om.
    
    Parametri:
    ----------
    - screen: glavna površina (pygame.Surface), na katero rišemo.
    - grid: 2D numpy array (rows x cols). Vsaka vrstica = ena generacija.
      grid[r, c] == 1 -> živa (pobarvamo), 0 -> prazna (ozadje).
    - cell_size: velikost celice (v px), določa kako velike kvadrate rišemo.
    - color: barva za žive celice (npr. BLACK).
    - background: barva ozadja (npr. WHITE).

    Logika risanja:
    ---------------
    1) Najprej pobarvamo celoten zaslon z background barvo.
    2) Gremo skozi vsako vrstico r in stolpec c v grid-u. 
       Če je grid[r, c] == 1, narišemo pravokotnik:
         x = c * cell_size  (vodoravni položaj)
         y = r * cell_size  (navpični položaj)
       Razlog, zakaj x = c in y = r, je ta, da (c) predstavlja stolpec (vodoravno),
       (r) pa vrstico (navpično). V Pygame-u je x os leva -> desna, y os pa zgoraj -> dol.
    3) Po koncu risanja (for zank) naredimo pygame.display.flip() za posodobitev okna.

    S tem v vsaki vrstici zapored rišemo nastalo konfiguracijo. Tako dobimo tipičen
    'trikotni' vzorec, kakršen je značilen za 1D celične avtomate (npr. Rule 30, Rule 110 itd.).
    """
    # Najprej počistimo ekran v barvo 'background'.
    screen.fill(background)
    rows, cols = grid.shape

    # Pregledamo vsako vrstico in stolpec
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 1:
                # Če je celica 1, jo pobarvamo z 'color'
                x = c * cell_size
                y = r * cell_size
                pygame.draw.rect(screen, color, (x, y, cell_size, cell_size))
    pygame.display.flip()