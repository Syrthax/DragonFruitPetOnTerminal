#!/usr/bin/env python3
"""Dragon Fruit Terminal Pet — adaptive curses TUI, designed to live in a corner pane."""

import curses, time, random

# ── Mood table: (top_symbol, 3-char eyes, mouth char) ─────────────────────────
MOODS = {
    'excited': ('* * *', '^v^', '~'),
    'happy':   ('o o o', '^u^', '_'),
    'neutral': ('. . .', 'o.o', '_'),
    'sad':     ('. . .', '>_<', '_'),
    'hungry':  ('~ ~ ~', 'O~O', '~'),
    'sleepy':  ('z z z', '-_-', '_'),
    'sick':    ('x x x', 'x_x', 'x'),
}

SPIKES = ['/\\/\\/\\', '\\/\\/\\/']   # alternate every 0.9 s

IDLE_MSGS = [
    "Psst... still here!",
    "Zero fat. Just saying.",
    "I like you.",
    "So quiet...",
    "Waiting for you.",
    "Dream of mangoes...",
    "Feed me? Please?",
]

# ── curses colour pair IDs ────────────────────────────────────────────────────
P_SEP, P_TITLE, P_NAME               = 1, 2, 3
P_EX, P_HP, P_NT, P_SD               = 4, 5, 6, 7
P_HU, P_SL, P_SK                     = 8, 9, 10
P_GREEN, P_PINK                      = 11, 12
P_BG, P_BY, P_BR, P_EMPTY           = 13, 14, 15, 16
P_MSG, P_KEY, P_STAT                 = 17, 18, 19

MOOD_PAIR = {
    'excited': P_EX, 'happy': P_HP, 'neutral': P_NT,
    'sad': P_SD,     'hungry': P_HU, 'sleepy': P_SL, 'sick': P_SK,
}


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    bg = -1
    curses.init_pair(P_SEP,   197, bg)
    curses.init_pair(P_TITLE, 213, bg)
    curses.init_pair(P_NAME,   51, bg)
    curses.init_pair(P_EX,   226, bg)
    curses.init_pair(P_HP,    82, bg)
    curses.init_pair(P_NT,    15, bg)
    curses.init_pair(P_SD,   196, bg)
    curses.init_pair(P_HU,   226, bg)
    curses.init_pair(P_SL,    51, bg)
    curses.init_pair(P_SK,   196, bg)
    curses.init_pair(P_GREEN,  82, bg)
    curses.init_pair(P_PINK,  213, bg)
    curses.init_pair(P_BG,    82, bg)
    curses.init_pair(P_BY,   226, bg)
    curses.init_pair(P_BR,   196, bg)
    curses.init_pair(P_EMPTY, 240, bg)
    curses.init_pair(P_MSG,  240, bg)
    curses.init_pair(P_KEY,   82, bg)
    curses.init_pair(P_STAT, 226, bg)


# ── Pet ───────────────────────────────────────────────────────────────────────
class Pet:
    def __init__(self, name='Pitaya'):
        self.name   = name
        self.hunger = self.happiness = self.energy = 80.0
        self.msg    = f"Hi! I'm {name}!"
        self._b     = False
        self._bt    = 0.0
        self._bcd   = random.uniform(3, 7)
        self._frame = 0
        self._ft    = 0.0
        self._idle  = 0.0

    def tick(self, dt):
        m = dt / 60.0
        self.hunger    = max(0.0, self.hunger    - m * 8)
        self.happiness = max(0.0, self.happiness - m * 5)
        self.energy    = max(0.0, self.energy    - m * 3)
        if self.hunger < 20:
            self.happiness = max(0.0, self.happiness - m * 8)

        self._bt += dt
        if self._b:
            if self._bt >= 0.15:
                self._b, self._bt, self._bcd = False, 0.0, random.uniform(3, 7)
        elif self._bt >= self._bcd:
            self._b, self._bt = True, 0.0

        self._ft += dt
        if self._ft >= 0.9:
            self._frame, self._ft = 1 - self._frame, 0.0

        self._idle += dt
        if self._idle >= 30:
            self._idle, self.msg = 0.0, random.choice(IDLE_MSGS)

    def mood(self):
        if self.hunger    < 10: return 'sick'
        if self.hunger    < 25: return 'hungry'
        if self.energy    < 15: return 'sleepy'
        if self.happiness > 80: return 'excited'
        if self.happiness > 55: return 'happy'
        if self.happiness < 25: return 'sad'
        return 'neutral'

    def feed(self):
        self.hunger    = min(100.0, self.hunger    + 35)
        self.happiness = min(100.0, self.happiness + 8)
        self.msg = 'Yummy! Thanks!';  self._idle = 0.0

    def play(self):
        if self.energy < 15:
            self.msg = "Too tired..."; return
        self.happiness = min(100.0, self.happiness + 28)
        self.energy    = max(0.0,   self.energy    - 20)
        self.hunger    = max(0.0,   self.hunger    - 12)
        self.msg = 'Wheee! So fun!';  self._idle = 0.0

    def sleep(self):
        self.energy    = min(100.0, self.energy    + 45)
        self.happiness = min(100.0, self.happiness + 5)
        self.msg = 'Zzz... refreshed!';  self._idle = 0.0

    def hug(self):
        self.happiness = min(100.0, self.happiness + 20)
        self.msg = 'Aww, I love hugs!';  self._idle = 0.0


# ── Rendering ─────────────────────────────────────────────────────────────────
def put(win, y, x, text, attr=0):
    rows, cols = win.getmaxyx()
    if y < 0 or y >= rows - 1 or x >= cols or not text:
        return
    if x < 0:
        text, x = text[-x:], 0
    try:
        win.addstr(y, x, text[:cols - x - 1], attr)
    except curses.error:
        pass


def draw(win, pet):
    win.erase()
    rows, cols = win.getmaxyx()

    # Adapt UI width to whatever pane we're in (corner pane or full terminal)
    W = min(34, cols - 2)
    if W < 22 or rows < 18:
        put(win, 0, 0, "Too small!")
        win.refresh()
        return

    mood = pet.mood()
    mc   = MOOD_PAIR.get(mood, P_NT)
    x0   = (cols - W) // 2
    SEP  = '-' * W
    A    = curses.A_BOLD

    # Stat bar width fits exactly: 2 + 10(label) + 1 + BAR + 1 + 4(pct) = W
    BAR = max(4, min(12, W - 18))
    pct_x = x0 + 14 + BAR   # column where "XX%" starts

    # Compact controls fit in one line for any W >= 22
    ctrl = '[f] [p] [s] [h] [q]'

    total_h = 19   # fixed row count
    y = max(0, (rows - total_h) // 2)

    # ── header ───────────────────────────────────────────────────────────────
    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1

    title = 'DRAGON FRUIT PET'
    put(win, y, x0 + max(0, (W - len(title)) // 2), title,
        curses.color_pair(P_TITLE) | A);              y += 1

    nm = f'{pet.name}  *  {mood.upper()}'
    nx = x0 + max(0, (W - len(nm)) // 2)
    put(win, y, nx,                    pet.name,       curses.color_pair(P_NAME) | A)
    put(win, y, nx + len(pet.name),    '  *  ')
    put(win, y, nx + len(pet.name) + 5, mood.upper(),  curses.color_pair(mc) | A)
    y += 1

    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1

    # ── art ──────────────────────────────────────────────────────────────────
    sym, eyes, m = MOODS.get(mood, MOODS['neutral'])
    if pet._b: eyes = '---'
    spike = SPIKES[pet._frame & 1]

    art = [
        (f'  {sym}  ',    curses.color_pair(mc)),
        (f' {spike} ',    curses.color_pair(P_GREEN)),
        (f'(  {eyes}  )', curses.color_pair(P_PINK)),
        (f'(  ~{m}~  )',  curses.color_pair(P_PINK)),
        (' \\____/ ',     curses.color_pair(P_PINK)),
    ]
    ax = x0 + max(0, (W - 9) // 2)
    for text, attr in art:
        put(win, y, ax, text, attr);  y += 1
    y += 1   # blank line after art

    # ── stats ─────────────────────────────────────────────────────────────────
    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1
    for label, val in [('Hunger', pet.hunger), ('Happiness', pet.happiness),
                       ('Energy', pet.energy)]:
        bc = P_BG if val > 60 else (P_BY if val > 30 else P_BR)
        n  = round(val / 100 * BAR)
        put(win, y, x0 + 2,      f'{label:<10}',   curses.color_pair(P_STAT))
        put(win, y, x0 + 13,     '#' * n,           curses.color_pair(bc) | A)
        put(win, y, x0 + 13 + n, '-' * (BAR - n),  curses.color_pair(P_EMPTY))
        put(win, y, pct_x,       f'{val:3.0f}%',   curses.color_pair(bc))
        y += 1

    # ── message ───────────────────────────────────────────────────────────────
    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1
    put(win, y, x0 + 2, pet.msg[:W - 4], curses.color_pair(P_MSG));  y += 1

    # ── controls ─────────────────────────────────────────────────────────────
    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1
    cx = x0 + max(0, (W - len(ctrl)) // 2)
    for k in ('f', 'p', 's', 'h', 'q'):
        put(win, y, cx, f'[{k}]', curses.color_pair(P_KEY))
        cx += 4
    y += 1
    put(win, y, x0, SEP, curses.color_pair(P_SEP))

    win.refresh()


# ── Main ──────────────────────────────────────────────────────────────────────
def _run(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(80)

    pet  = Pet()
    last = time.time()

    while True:
        key = stdscr.getch()
        if   key in (ord('q'), ord('Q')): break
        elif key == ord('f'): pet.feed()
        elif key == ord('p'): pet.play()
        elif key == ord('s'): pet.sleep()
        elif key == ord('h'): pet.hug()

        now = time.time()
        pet.tick(now - last)
        last = now
        draw(stdscr, pet)


if __name__ == '__main__':
    try:
        curses.wrapper(_run)
    except KeyboardInterrupt:
        pass
    print('\nGoodbye! Pitaya will miss you!\n')
