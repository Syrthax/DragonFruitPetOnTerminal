#!/usr/bin/env python3
"""Dragon Fruit Terminal Pet — curses TUI for precise, aligned rendering."""

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

# Two spike frames that alternate every 0.9 s
SPIKES = ['/\\/\\/\\', '\\/\\/\\/']

IDLE_MSGS = [
    "Psst... I'm right here!",
    "Dragon fruits have zero fat.",
    "I like you. Just saying.",
    "It's quiet in here...",
    "Waiting patiently...",
    "Dragons dream of mangoes.",
    "Feed me? Please?",
]

# ── curses colour pair IDs ────────────────────────────────────────────────────
P_SEP, P_TITLE, P_NAME   = 1, 2, 3
P_MC_EX, P_MC_HP, P_MC_N = 4, 5, 6    # excited / happy / neutral mood colours
P_MC_SD, P_MC_HU, P_MC_SL, P_MC_SK = 7, 8, 9, 10
P_GREEN, P_PINK          = 11, 12
P_BAR_G, P_BAR_Y, P_BAR_R, P_EMPTY = 13, 14, 15, 16
P_MSG, P_KEY, P_STAT     = 17, 18, 19

MOOD_PAIR = {
    'excited': P_MC_EX, 'happy': P_MC_HP, 'neutral': P_MC_N,
    'sad': P_MC_SD,     'hungry': P_MC_HU, 'sleepy': P_MC_SL, 'sick': P_MC_SK,
}


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    bg = -1
    curses.init_pair(P_SEP,    197, bg)   # deep pink  — separators
    curses.init_pair(P_TITLE,  213, bg)   # pink       — title
    curses.init_pair(P_NAME,    51, bg)   # cyan       — name
    curses.init_pair(P_MC_EX,  226, bg)   # yellow     — excited
    curses.init_pair(P_MC_HP,   82, bg)   # green      — happy
    curses.init_pair(P_MC_N,    15, bg)   # white      — neutral
    curses.init_pair(P_MC_SD,  196, bg)   # red        — sad
    curses.init_pair(P_MC_HU,  226, bg)   # yellow     — hungry
    curses.init_pair(P_MC_SL,   51, bg)   # cyan       — sleepy
    curses.init_pair(P_MC_SK,  196, bg)   # red        — sick
    curses.init_pair(P_GREEN,   82, bg)   # green      — spikes
    curses.init_pair(P_PINK,   213, bg)   # pink       — body
    curses.init_pair(P_BAR_G,   82, bg)   # green      — bar high
    curses.init_pair(P_BAR_Y,  226, bg)   # yellow     — bar mid
    curses.init_pair(P_BAR_R,  196, bg)   # red        — bar low
    curses.init_pair(P_EMPTY,  240, bg)   # gray       — bar empty
    curses.init_pair(P_MSG,    240, bg)   # dim gray   — message
    curses.init_pair(P_KEY,     82, bg)   # green      — key hints
    curses.init_pair(P_STAT,   226, bg)   # yellow     — stat labels


# ── Pet ───────────────────────────────────────────────────────────────────────
class Pet:
    def __init__(self, name='Pitaya'):
        self.name   = name
        self.hunger = self.happiness = self.energy = 80.0
        self.msg    = f"Hi! I'm {name}!  Press f / p / s / h to interact."
        self._b     = False        # blinking flag
        self._bt    = 0.0          # blink timer
        self._bcd   = random.uniform(3, 7)
        self._frame = 0            # spike frame (0 or 1)
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
        self.msg = 'Yummy! Thanks for the food!';  self._idle = 0.0

    def play(self):
        if self.energy < 15:
            self.msg = "Too tired to play right now..."; return
        self.happiness = min(100.0, self.happiness + 28)
        self.energy    = max(0.0,   self.energy    - 20)
        self.hunger    = max(0.0,   self.hunger    - 12)
        self.msg = 'Wheee! So much fun!';  self._idle = 0.0

    def sleep(self):
        self.energy    = min(100.0, self.energy    + 45)
        self.happiness = min(100.0, self.happiness + 5)
        self.msg = 'Zzz... Feeling refreshed!';  self._idle = 0.0

    def hug(self):
        self.happiness = min(100.0, self.happiness + 20)
        self.msg = 'Aww, I love hugs!';  self._idle = 0.0


# ── Rendering ─────────────────────────────────────────────────────────────────
W = 34   # fixed UI width — all ASCII, every char is 1 column


def put(win, y, x, text, attr=0):
    """Safe addstr that clips to terminal bounds."""
    rows, cols = win.getmaxyx()
    if y < 0 or y >= rows - 1 or x >= cols or not text:
        return
    if x < 0:
        text, x = text[-x:], 0
    avail = cols - x - 1
    if avail <= 0:
        return
    try:
        win.addstr(y, x, text[:avail], attr)
    except curses.error:
        pass


def draw(win, pet):
    win.erase()
    rows, cols = win.getmaxyx()

    if cols < W + 2 or rows < 20:
        put(win, 0, 0, "Terminal too small! Resize to at least 36x20.")
        win.refresh()
        return

    mood = pet.mood()
    mc   = MOOD_PAIR.get(mood, P_MC_N)
    x0   = (cols - W) // 2
    SEP  = '-' * W
    A    = curses.A_BOLD

    y = (rows - 19) // 2   # vertically centre the 19-row UI
    y = max(0, y)

    # ── header ──────────────────────────────────────────────────────────────
    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1

    title = 'DRAGON FRUIT PET'
    put(win, y, x0 + (W - len(title)) // 2, title,
        curses.color_pair(P_TITLE) | A);              y += 1

    nm  = pet.name + '  *  ' + mood.upper()
    nx  = x0 + (W - len(nm)) // 2
    put(win, y, nx,                    pet.name,      curses.color_pair(P_NAME) | A)
    put(win, y, nx + len(pet.name),    '  *  ')
    put(win, y, nx + len(pet.name) + 5, mood.upper(), curses.color_pair(mc) | A)
    y += 1

    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1

    # ── ASCII art ───────────────────────────────────────────────────────────
    sym, eyes, m = MOODS.get(mood, MOODS['neutral'])
    if pet._b:
        eyes = '---'
    spike = SPIKES[pet._frame & 1]

    #  art lines and their colours  (all exactly 9 visible chars)
    art = [
        (f'  {sym}  ',    curses.color_pair(mc)),
        (f' {spike} ',    curses.color_pair(P_GREEN)),
        (f'(  {eyes}  )', curses.color_pair(P_PINK)),
        (f'(  ~{m}~  )',  curses.color_pair(P_PINK)),
        (' \\____/ ',     curses.color_pair(P_PINK)),
    ]
    ax = x0 + (W - 9) // 2
    for text, attr in art:
        put(win, y, ax, text, attr);  y += 1
    y += 1

    # ── stats ────────────────────────────────────────────────────────────────
    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1
    BAR = 12
    for label, val in [('Hunger', pet.hunger), ('Happiness', pet.happiness),
                       ('Energy', pet.energy)]:
        bc = P_BAR_G if val > 60 else (P_BAR_Y if val > 30 else P_BAR_R)
        n  = round(val / 100 * BAR)
        put(win, y, x0 + 2,       f'{label:<10}',   curses.color_pair(P_STAT))
        put(win, y, x0 + 13,      '#' * n,           curses.color_pair(bc) | A)
        put(win, y, x0 + 13 + n,  '-' * (BAR - n),  curses.color_pair(P_EMPTY))
        put(win, y, x0 + 26,      f'{val:3.0f}%',   curses.color_pair(bc))
        y += 1

    # ── message ──────────────────────────────────────────────────────────────
    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1
    put(win, y, x0 + 2, pet.msg[:W - 4], curses.color_pair(P_MSG));  y += 1

    # ── controls ─────────────────────────────────────────────────────────────
    put(win, y, x0, SEP, curses.color_pair(P_SEP));  y += 1
    keys = [('f','eed'), ('p','lay'), ('s','leep'), ('h','ug'), ('q','uit')]
    total = sum(3 + len(l) for _, l in keys) + len(keys) - 1
    cx = x0 + (W - total) // 2
    for k, label in keys:
        put(win, y, cx, f'[{k}]', curses.color_pair(P_KEY))
        put(win, y, cx + 3, label)
        cx += 3 + len(label) + 1
    y += 1
    put(win, y, x0, SEP, curses.color_pair(P_SEP))

    win.refresh()


# ── Main loop ─────────────────────────────────────────────────────────────────
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
