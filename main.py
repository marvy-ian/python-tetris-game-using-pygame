import pygame
import random
import sys
import math
import array

COLS, ROWS = 10, 20
CELL = 32
SIDEBAR = 200
WIDTH  = COLS * CELL + SIDEBAR
HEIGHT = ROWS * CELL

FPS = 60

BLACK      = (10,  10,  10)
DARK_GREY  = (30,  30,  35)
GREY       = (60,  60,  65)
WHITE      = (240, 240, 240)
PANEL_BG   = (20,  20,  28)

PIECE_COLORS = {
    "I": (0,   220, 220),
    "O": (220, 220,   0),
    "T": (180,  40, 220),
    "S": ( 40, 220,  80),
    "Z": (220,  40,  40),
    "J": ( 40,  80, 220),
    "L": (220, 140,  20),
}

SHAPES = {
    "I": [[(0,0),(0,1),(0,2),(0,3)],
          [(0,0),(1,0),(2,0),(3,0)]],
    "O": [[(0,0),(0,1),(1,0),(1,1)]],
    "T": [[(0,0),(0,1),(0,2),(1,1)],
          [(0,0),(1,0),(2,0),(1,1)],
          [(1,0),(1,1),(1,2),(0,1)],
          [(0,1),(1,1),(2,1),(1,0)]],
    "S": [[(0,1),(0,2),(1,0),(1,1)],
          [(0,0),(1,0),(1,1),(2,1)]],
    "Z": [[(0,0),(0,1),(1,1),(1,2)],
          [(0,1),(1,0),(1,1),(2,0)]],
    "J": [[(0,0),(1,0),(1,1),(1,2)],
          [(0,0),(0,1),(1,0),(2,0)],
          [(0,0),(0,1),(0,2),(1,2)],
          [(0,1),(1,1),(2,0),(2,1)]],
    "L": [[(0,2),(1,0),(1,1),(1,2)],
          [(0,0),(1,0),(2,0),(2,1)],
          [(0,0),(0,1),(0,2),(1,0)],
          [(0,0),(0,1),(1,1),(2,1)]],
}

SCORE_TABLE = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}


# ---------------------------------------------------------------------------
# Sound synthesis — all effects are generated in code (sine/square waves
# with a short decay envelope), so no external audio files are needed.
# ---------------------------------------------------------------------------
SAMPLE_RATE = 44100

def _tone(freq, duration_ms, volume=0.5, wave="sine", decay=True, harmonics=None):
    """Build a short synthesized tone and return it as a pygame Sound."""
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    buf = array.array("h")
    two_pi_f = 2 * math.pi * freq
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        if wave == "square":
            s = 1.0 if math.sin(two_pi_f * t) >= 0 else -1.0
        elif wave == "noise":
            s = random.uniform(-1, 1)
        else:  # sine, optionally with extra harmonics for a richer "chip" tone
            s = math.sin(two_pi_f * t)
            if harmonics:
                for mult, amp in harmonics:
                    s += amp * math.sin(two_pi_f * mult * t)
                s /= (1 + sum(a for _, a in harmonics))

        if decay:
            s *= (1 - i / n_samples) ** 1.5

        sample = int(max(-1.0, min(1.0, s)) * volume * 32767)
        buf.append(sample)   # left
        buf.append(sample)   # right
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _sequence(notes, volume=0.5, wave="sine", gap_ms=0):
    """Concatenate several (freq, duration_ms) notes into one Sound."""
    buf = array.array("h")
    for freq, duration_ms in notes:
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        two_pi_f = 2 * math.pi * freq
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            s = 1.0 if wave == "square" and math.sin(two_pi_f * t) >= 0 else \
                -1.0 if wave == "square" else math.sin(two_pi_f * t)
            s *= (1 - i / n_samples) ** 1.2
            sample = int(max(-1.0, min(1.0, s)) * volume * 32767)
            buf.append(sample)
            buf.append(sample)
        if gap_ms:
            buf.extend([0] * int(SAMPLE_RATE * gap_ms / 1000) * 2)
    return pygame.mixer.Sound(buffer=buf.tobytes())


class Sounds:
    """Loads/generates and plays every sound effect. Fails silently if the
    machine has no audio device, so the game still runs without sound."""

    def __init__(self):
        self.enabled = False
        self.effects = {}
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
            self.effects = {
                "move":      _tone(220, 35,  volume=0.20, wave="square"),
                "rotate":    _tone(330, 45,  volume=0.25, wave="square"),
                "soft_drop": _tone(150, 30,  volume=0.15, wave="square"),
                "hard_drop": _tone(90,  90,  volume=0.35, wave="noise"),
                "lock":      _tone(180, 60,  volume=0.30, wave="square"),
                "hold":      _tone(440, 80,  volume=0.25, wave="sine",
                                    harmonics=[(2, 0.3)]),
                "line":      _sequence([(523, 60), (659, 60), (784, 90)],
                                        volume=0.35, wave="square"),
                "tetris":    _sequence([(523, 55), (659, 55), (784, 55),
                                         (1047, 130)],
                                        volume=0.4, wave="square"),
                "levelup":   _sequence([(392, 70), (523, 70), (659, 110)],
                                        volume=0.35, wave="sine"),
                "gameover":  _sequence([(392, 120), (330, 120), (262, 220)],
                                        volume=0.35, wave="square"),
            }
            self.enabled = True
        except pygame.error:
            # No audio device available (e.g. headless environment) — the
            # game continues to run perfectly fine without sound.
            self.enabled = False

    def play(self, name):
        if self.enabled and name in self.effects:
            self.effects[name].play()


class Piece:
    def __init__(self, kind=None):
        self.kind = kind or random.choice(list(SHAPES.keys()))
        self.rot  = 0
        self.row  = 0
        self.col  = COLS // 2 - 2

    def cells(self, row=None, col=None, rot=None):
        r = self.row if row is None else row
        c = self.col if col is None else col
        t = self.rot if rot is None else rot
        offsets = SHAPES[self.kind][t % len(SHAPES[self.kind])]
        return [(r + dr, c + dc) for dr, dc in offsets]

    def color(self):
        return PIECE_COLORS[self.kind]

class Board:
    def __init__(self, sounds=None):
        self.grid   = [[None] * COLS for _ in range(ROWS)]
        self.piece  = Piece()
        self.next   = Piece()
        self.held   = None
        self.can_hold = True
        self.score  = 0
        self.level  = 1
        self.lines  = 0
        self.over   = False
        self.sounds = sounds

    def _play(self, name):
        if self.sounds:
            self.sounds.play(name)

    def drop_interval(self):
        return max(80, 800 - (self.level - 1) * 60)

    def valid(self, cells):
        for r, c in cells:
            if c < 0 or c >= COLS or r >= ROWS:
                return False
            if r >= 0 and self.grid[r][c]:
                return False
        return True

    def lock(self):
        for r, c in self.piece.cells():
            if r < 0:
                self.over = True
                self._play("gameover")
                return
            self.grid[r][c] = self.piece.color()
        self._play("lock")
        self._clear_lines()
        self.piece    = self.next
        self.next     = Piece()
        self.can_hold = True
        if not self.valid(self.piece.cells()):
            self.over = True
            self._play("gameover")

    def _clear_lines(self):
        full = [r for r in range(ROWS) if all(self.grid[r])]
        for r in full:
            del self.grid[r]
            self.grid.insert(0, [None] * COLS)
        n = len(full)
        if n == 4:
            self._play("tetris")
        elif n > 0:
            self._play("line")

        prev_level = self.level
        self.score += SCORE_TABLE.get(n, 0) * self.level
        self.lines += n
        self.level  = self.lines // 10 + 1
        if self.level > prev_level:
            self._play("levelup")

    def move(self, dr, dc):
        cells = self.piece.cells(self.piece.row + dr, self.piece.col + dc)
        if self.valid(cells):
            self.piece.row += dr
            self.piece.col += dc
            return True
        return False

    def rotate(self, direction=1):
        new_rot = (self.piece.rot + direction) % len(SHAPES[self.piece.kind])
        for kick in [0, 1, -1, 2, -2]:
            cells = self.piece.cells(self.piece.row, self.piece.col + kick, new_rot)
            if self.valid(cells):
                self.piece.rot = new_rot
                self.piece.col += kick
                self._play("rotate")
                return

    def hard_drop(self):
        while self.move(1, 0):
            self.score += 2
        self._play("hard_drop")
        self.lock()

    def hold(self):
        if not self.can_hold:
            return
        if self.held:
            self.piece, self.held = self.held, self.piece
            self.piece.row = 0
            self.piece.col = COLS // 2 - 2
            self.piece.rot = 0
        else:
            self.held = self.piece
            self.piece = self.next
            self.next  = Piece()
        self.can_hold = False
        self._play("hold")

    def ghost_row(self):
        r = self.piece.row
        while self.valid(self.piece.cells(r + 1, self.piece.col)):
            r += 1
        return r

def draw_cell(surf, row, col, color, alpha=255, offset_x=0, offset_y=0, size=CELL):
    x = offset_x + col * size
    y = offset_y + row * size
    rect = pygame.Rect(x + 1, y + 1, size - 2, size - 2)
    if alpha < 255:
        s = pygame.Surface((size - 2, size - 2), pygame.SRCALPHA)
        s.fill((*color, alpha))
        surf.blit(s, (x + 1, y + 1))
    else:
        pygame.draw.rect(surf, color, rect, border_radius=3)
        pygame.draw.rect(surf, tuple(min(255, v + 60) for v in color),
                         pygame.Rect(x+2, y+2, size//3, 3), border_radius=2)

def draw_grid(surf, board):
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(surf, DARK_GREY,
                             pygame.Rect(c*CELL+1, r*CELL+1, CELL-2, CELL-2),
                             border_radius=2)

    for r in range(ROWS):
        for c in range(COLS):
            if board.grid[r][c]:
                draw_cell(surf, r, c, board.grid[r][c])

    ghost_r = board.ghost_row()
    for r, c in board.piece.cells(ghost_r, board.piece.col):
        if 0 <= r < ROWS:
            draw_cell(surf, r, c, board.piece.color(), alpha=55)

    for r, c in board.piece.cells():
        if 0 <= r < ROWS:
            draw_cell(surf, r, c, board.piece.color())

def draw_mini_piece(surf, piece, title, ox, oy, font):
    label = font.render(title, True, GREY)
    surf.blit(label, (ox, oy))
    if piece is None:
        return
    size = 24
    cells = SHAPES[piece.kind][0]
    min_r = min(r for r, c in cells)
    min_c = min(c for r, c in cells)
    for dr, dc in cells:
        x = ox + (dc - min_c) * size
        y = oy + 22 + (dr - min_r) * size
        rect = pygame.Rect(x+1, y+1, size-2, size-2)
        pygame.draw.rect(surf, piece.color(), rect, border_radius=3)

def draw_sidebar(surf, board, fonts, sound_on):
    ox = COLS * CELL
    pygame.draw.rect(surf, PANEL_BG, pygame.Rect(ox, 0, SIDEBAR, HEIGHT))

    big, med, sm = fonts

    surf.blit(sm.render("SCORE", True, GREY),  (ox+14, 14))
    surf.blit(med.render(str(board.score), True, WHITE), (ox+14, 34))

    surf.blit(sm.render("LEVEL", True, GREY),  (ox+14, 80))
    surf.blit(med.render(str(board.level), True, WHITE), (ox+14, 100))

    surf.blit(sm.render("LINES", True, GREY),  (ox+14, 146))
    surf.blit(med.render(str(board.lines), True, WHITE), (ox+14, 166))

    draw_mini_piece(surf, board.next, "NEXT", ox+14, 218, sm)
    draw_mini_piece(surf, board.held, "HOLD", ox+14, 330, sm)

    hints = ["← →  move", "↑  rotate CW", "Z  rotate CCW", "↓  soft drop",
             "Space  drop", "C  hold", "M  mute sound", "P  pause", "R  restart"]
    surf.blit(sm.render("CONTROLS", True, GREY), (ox+14, 420))
    for i, h in enumerate(hints):
        surf.blit(sm.render(h, True, (100,100,110)), (ox+14, 442 + i*18))

    status = "SOUND: ON" if sound_on else "SOUND: OFF"
    surf.blit(sm.render(status, True, GREY), (ox+14, HEIGHT-24))

def draw_overlay(surf, text, sub, fonts):
    big, med, sm = fonts
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surf.blit(overlay, (0, 0))
    t = big.render(text, True, WHITE)
    surf.blit(t, t.get_rect(center=(COLS*CELL//2, HEIGHT//2 - 30)))
    s = sm.render(sub, True, GREY)
    surf.blit(s, s.get_rect(center=(COLS*CELL//2, HEIGHT//2 + 20)))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tetris")
    clock  = pygame.time.Clock()

    fonts = (
        pygame.font.SysFont("segoeui", 42, bold=True),
        pygame.font.SysFont("segoeui", 28, bold=True),
        pygame.font.SysFont("segoeui", 15),
    )

    sounds  = Sounds()
    board   = Board(sounds)
    paused  = False
    last_drop = pygame.time.get_ticks()
    das_timer = 0
    das_dir   = 0
    DAS_DELAY = 160
    DAS_RATE  = 40

    while True:
        now = pygame.time.get_ticks()
        dt  = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board = Board(sounds)
                    last_drop = now
                    paused = False
                    continue

                if event.key == pygame.K_m:
                    sounds.enabled = not sounds.enabled if sounds.effects else False

                if board.over:
                    continue

                if event.key == pygame.K_p:
                    paused = not paused

                if paused:
                    continue

                if event.key == pygame.K_LEFT:
                    if board.move(0, -1):
                        sounds.play("move")
                    das_dir = -1; das_timer = now
                if event.key == pygame.K_RIGHT:
                    if board.move(0,  1):
                        sounds.play("move")
                    das_dir =  1; das_timer = now
                if event.key == pygame.K_UP:
                    board.rotate(1)
                if event.key == pygame.K_z:
                    board.rotate(-1)
                if event.key == pygame.K_DOWN:
                    if board.move(1, 0):
                        board.score += 1
                        sounds.play("soft_drop")
                if event.key == pygame.K_SPACE:
                    board.hard_drop(); last_drop = now
                if event.key == pygame.K_c:
                    board.hold()

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    das_dir = 0

        if not board.over and not paused:
            if das_dir and now - das_timer > DAS_DELAY:
                if (now - das_timer - DAS_DELAY) % DAS_RATE < dt:
                    if board.move(0, das_dir):
                        sounds.play("move")

            if now - last_drop >= board.drop_interval():
                if not board.move(1, 0):
                    board.lock()
                last_drop = now

        screen.fill(BLACK)

        pygame.draw.rect(screen, GREY,
                         pygame.Rect(0, 0, COLS*CELL, HEIGHT), 1)

        draw_grid(screen, board)
        draw_sidebar(screen, board, fonts, sounds.enabled)

        if paused and not board.over:
            draw_overlay(screen, "PAUSED", "Press P to resume", fonts)
        if board.over:
            draw_overlay(screen, "GAME OVER",
                         f"Score: {board.score}   Press R to restart", fonts)

        pygame.display.flip()

if __name__ == "__main__":
    main()