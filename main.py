#!/usr/bin/env python3
"""Dragon Fruit Terminal Pet — an animated ASCII pet that lives in your terminal."""

import time, sys, random, threading

try:
    import tty, termios
    _UNIX = True
except ImportError:
    _UNIX = False

# ── ANSI helpers ──────────────────────────────────────────────────────────────
R     = '\033[0m'
BOLD  = '\033[1m'
DIM   = '\033[2m'
PINK  = '\033[38;5;213m'
DPINK = '\033[38;5;198m'
GREEN = '\033[38;5;82m'
YEL   = '\033[93m'
CYN   = '\033[96m'
RED   = '\033[91m'
GRY   = '\033[90m'
WHT   = '\033[97m'
SEP   = DPINK + '━' * 38 + R


def _clr():
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()


# ── Mood definitions: (above_symbol, eyes, mouth_char) ───────────────────────
_MOOD_DEF = {
    'excited': ('★ ★ ★', '^‿^', '~'),
    'happy':   ('♦ ♦ ♦', '^‿^', '_'),
    'neutral': ('· · ·', '•‿•', '_'),
    'sad':     ('· · ·', '>_<', '_'),
    'hungry':  ('~ ~ ~', 'O~O', '~'),
    'sleepy':  ('z z z', '-_-', '_'),
    'sick':    ('x x x', 'x_x', 'x'),
}
_MOOD_CLR = {
    'excited': YEL, 'happy': GREEN, 'neutral': WHT,
    'sad': RED,     'hungry': YEL,  'sleepy': CYN, 'sick': RED,
}

# Two spike frames that alternate to simulate gentle movement
_SPIKES = [
    GREEN + ' /\\/\\/\\ ' + R,
    GREEN + ' \\/\\/\\/ ' + R,
]

_IDLE_MSGS = [
    "Psst… I'm right here! 👀",
    "Did you know dragon fruits have zero fat? 🍈",
    "I like you. Just saying. 💕",
    "It's quiet in here…",
    "I heard a sound! Was that you?",
    "Waiting patiently… ⏳",
    "Dragons dream of electric mangoes. 🥭",
]


def _art(mood: str, blink: bool, frame: int) -> list[str]:
    sym, eyes, m = _MOOD_DEF.get(mood, _MOOD_DEF['neutral'])
    if blink:
        eyes = '---'
    mc = _MOOD_CLR.get(mood, WHT)
    return [
        f'  {mc}{sym}{R}',
        _SPIKES[frame & 1],
        f'{PINK}(  {WHT}{eyes}{PINK}  ){R}',
        f'{PINK}(  {WHT}~{m}~{PINK}  ){R}',
        f'{PINK} \\____/ {R}',
    ]


def _bar(label: str, val: float) -> str:
    W = 12
    c = GREEN if val > 60 else (YEL if val > 30 else RED)
    n = round(val / 100 * W)
    b = c + '█' * n + GRY + '░' * (W - n) + R
    return f'  {YEL}{label:<10}{R}  {b}  {c}{val:3.0f}%{R}'


# ── Pet ───────────────────────────────────────────────────────────────────────
class Pet:
    def __init__(self, name: str = 'Pitaya'):
        self.name      = name
        self.hunger    = 80.0   # 100 = full,   0 = starving
        self.happiness = 80.0   # 100 = elated,  0 = miserable
        self.energy    = 80.0   # 100 = rested,  0 = exhausted
        self.msg       = f"Hi! I'm {name}! 🐉  Press f / p / s / h to interact."
        self._b        = False
        self._bt       = 0.0
        self._bcd      = random.uniform(3, 7)
        self._frame    = 0
        self._ft       = 0.0
        self._idle_t   = 0.0

    def tick(self, dt: float):
        m           = dt / 60.0
        self.hunger    = max(0.0, self.hunger    - m * 8)
        self.happiness = max(0.0, self.happiness - m * 5)
        self.energy    = max(0.0, self.energy    - m * 3)
        if self.hunger < 20:
            self.happiness = max(0.0, self.happiness - m * 8)

        # blink
        self._bt += dt
        if self._b:
            if self._bt >= 0.15:
                self._b, self._bt = False, 0.0
                self._bcd = random.uniform(3, 7)
        elif self._bt >= self._bcd:
            self._b, self._bt = True, 0.0

        # spike wiggle
        self._ft += dt
        if self._ft >= 0.9:
            self._frame = 1 - self._frame
            self._ft    = 0.0

        # idle comment every ~30 s
        self._idle_t += dt
        if self._idle_t >= 30:
            self._idle_t = 0.0
            self.msg     = random.choice(_IDLE_MSGS)

    def mood(self) -> str:
        if self.hunger < 10:     return 'sick'
        if self.hunger < 25:     return 'hungry'
        if self.energy < 15:     return 'sleepy'
        if self.happiness > 80:  return 'excited'
        if self.happiness > 55:  return 'happy'
        if self.happiness < 25:  return 'sad'
        return 'neutral'

    def feed(self):
        self.hunger    = min(100.0, self.hunger    + 35)
        self.happiness = min(100.0, self.happiness + 8)
        self.msg       = 'Yummy! Thanks for the food! 🍓'
        self._idle_t   = 0.0

    def play(self):
        if self.energy < 15:
            self.msg = "Too tired to play right now… 😴"
            return
        self.happiness = min(100.0, self.happiness + 28)
        self.energy    = max(0.0,   self.energy    - 20)
        self.hunger    = max(0.0,   self.hunger    - 12)
        self.msg       = 'Wheee! That was so fun! ✨'
        self._idle_t   = 0.0

    def sleep(self):
        self.energy    = min(100.0, self.energy    + 45)
        self.happiness = min(100.0, self.happiness + 5)
        self.msg       = 'Zzz… *yawns* Feeling refreshed! 💤'
        self._idle_t   = 0.0

    def hug(self):
        self.happiness = min(100.0, self.happiness + 20)
        self.msg       = 'Aww, I love hugs! 💖'
        self._idle_t   = 0.0


# ── Render ────────────────────────────────────────────────────────────────────
def render(pet: Pet):
    _clr()
    mood = pet.mood()
    mc   = _MOOD_CLR.get(mood, WHT)

    print(SEP)
    print(f'  {BOLD}{PINK}🐉  DRAGON FRUIT PET{R}')
    print(f'  {CYN}{BOLD}{pet.name}{R}  ·  {mc}{mood.upper()}{R}')
    print(SEP)
    print()
    for line in _art(mood, pet._b, pet._frame):
        print('        ' + line)
    print()
    print(SEP)
    print(_bar('Hunger',    pet.hunger))
    print(_bar('Happiness', pet.happiness))
    print(_bar('Energy',    pet.energy))
    print(SEP)
    print(f'  {DIM}{pet.msg}{R}')
    print(SEP)
    print(f'  {GREEN}[f]{R}eed  {GREEN}[p]{R}lay  {GREEN}[s]{R}leep  {GREEN}[h]{R}ug  {GREEN}[q]{R}uit')
    print(SEP)
    sys.stdout.flush()


# ── Keyboard input (raw, non-blocking via thread) ─────────────────────────────
def _get_key() -> str:
    if _UNIX:
        fd  = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    import msvcrt
    return msvcrt.getch().decode('utf-8', errors='ignore')


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    pet  = Pet()
    _q: list[str] = []
    lock = threading.Lock()
    stop = threading.Event()

    def _reader():
        while not stop.is_set():
            try:
                k = _get_key()
                with lock:
                    _q.append(k)
                if k.lower() == 'q':
                    break
            except Exception:
                break

    threading.Thread(target=_reader, daemon=True).start()

    last = time.time()
    render(pet)

    try:
        while True:
            time.sleep(0.1)
            now = time.time()
            pet.tick(now - last)
            last = now

            with lock:
                keys = _q[:]
                _q.clear()

            for k in keys:
                k = k.lower()
                if k == 'q':
                    stop.set()
                    _clr()
                    print(f'\n{PINK}Goodbye! {pet.name} will miss you! 💖{R}\n')
                    return
                elif k == 'f': pet.feed()
                elif k == 'p': pet.play()
                elif k == 's': pet.sleep()
                elif k == 'h': pet.hug()

            render(pet)

    except KeyboardInterrupt:
        stop.set()
        _clr()
        print(f'\n{PINK}Goodbye! {pet.name} will miss you! 💖{R}\n')


if __name__ == '__main__':
    main()
