import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]


class Gem:
   
    def __init__(self, color, target_row, col):
        self.color = color
        self.target_row = target_row
        self.col = col
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class BombGem(Gem):

    def __init__(self, color, target_row, col, direction):
        super().__init__(color, target_row, col)
        self.direction = direction


class Board:

    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.combo_count = 0
        self.reset()

    def reset(self):
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        self.combo_count = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = gem.target_y  
                self.grid[r][c] = gem

        self.resolve_matches()

    def is_animating(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True
        return False

    def swap_gems(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2

        g1, g2 = self.grid[r1][c1], self.grid[r2][c2]
        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE

        if self.grid[r2][c2]:
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_matches(self):
        matched = set()

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 2):
                if (
                    self._matchable(self.grid[r][c])
                    and self._matchable(self.grid[r][c + 1])
                    and self._matchable(self.grid[r][c + 2])
                    and self.grid[r][c].color == self.grid[r][c + 1].color == self.grid[r][c + 2].color
                ):
                    matched.update([(r, c), (r, c + 1), (r, c + 2)])

        for r in range(GRID_SIZE - 2):
            for c in range(GRID_SIZE):
                if (
                    self._matchable(self.grid[r][c])
                    and self._matchable(self.grid[r + 1][c])
                    and self._matchable(self.grid[r + 2][c])
                    and self.grid[r][c].color == self.grid[r + 1][c].color == self.grid[r + 2][c].color
                ):
                    matched.update([(r, c), (r + 1, c), (r + 2, c)])

        return matched

    def _matchable(self, gem):
        return gem is not None and not isinstance(gem, BombGem)

    def find_four_match(self, matches, swap_positions):
        matched = set(matches)

        for r in range(GRID_SIZE):
            for start in range(GRID_SIZE - 3):
                positions = [(r, start + offset) for offset in range(4)]
                if self._is_exact_four(positions, matched) and any(
                    position in positions for position in swap_positions
                ):
                    return positions, "horizontal"

        for c in range(GRID_SIZE):
            for start in range(GRID_SIZE - 3):
                positions = [(start + offset, c) for offset in range(4)]
                if self._is_exact_four(positions, matched) and any(
                    position in positions for position in swap_positions
                ):
                    return positions, "vertical"

        return None

    def _is_exact_four(self, positions, matched):
        if not set(positions).issubset(matched):
            return False

        gems = [self.grid[r][c] for r, c in positions]
        if not all(self._matchable(gem) for gem in gems):
            return False
        if len({gem.color for gem in gems}) != 1:
            return False

        start_row, start_col = positions[0]
        end_row, end_col = positions[-1]
        color = gems[0].color

        if start_row == end_row:
            if start_col > 0 and self._matchable(self.grid[start_row][start_col - 1]) \
                    and self.grid[start_row][start_col - 1].color == color:
                return False
            if end_col + 1 < GRID_SIZE and self._matchable(self.grid[end_row][end_col + 1]) \
                    and self.grid[end_row][end_col + 1].color == color:
                return False
        else:
            if start_row > 0 and self._matchable(self.grid[start_row - 1][start_col]) \
                    and self.grid[start_row - 1][start_col].color == color:
                return False
            if end_row + 1 < GRID_SIZE and self._matchable(self.grid[end_row + 1][end_col]) \
                    and self.grid[end_row + 1][end_col].color == color:
                return False

        return True

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            for r in range(empty_slots):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem

    def resolve_matches(self, score_matches=False, bomb_info=None, initial_clear=None):
        total_cleared = 0
        pending_clear = set(initial_clear or ())
        while True:
            matches = pending_clear or self.find_matches()
            pending_clear = set()
            if not matches:
                break
            self.combo_count += 1
            total_cleared += len(matches)
            if score_matches:
                self.score += len(matches) * 10 * self.combo_count
            clear_positions = set(matches)
            if bomb_info:
                bomb_position, direction = bomb_info
                if bomb_position in matches:
                    r, c = bomb_position
                    gem = self.grid[r][c]
                    if self._matchable(gem):
                        bomb = BombGem(gem.color, r, c, direction)
                        bomb.current_y = gem.current_y
                        bomb.target_y = gem.target_y
                        self.grid[r][c] = bomb
                        clear_positions.remove(bomb_position)
                bomb_info = None
            for r, c in clear_positions:
                self.grid[r][c] = None
            self.drop_and_refill()
        self.combo_count = 0
        return total_cleared

    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False

        self.swap_gems(pos1, pos2)
        swapped_bomb = None
        for position in (pos1, pos2):
            if isinstance(self.grid[position[0]][position[1]], BombGem):
                swapped_bomb = self.grid[position[0]][position[1]]
                break

        if swapped_bomb:
            row, col = pos1 if self.grid[pos1[0]][pos1[1]] is swapped_bomb else pos2
            if swapped_bomb.direction == "horizontal":
                initial_clear = {(row, c) for c in range(GRID_SIZE)}
            else:
                initial_clear = {(r, col) for r in range(GRID_SIZE)}
            self.moves_remaining -= 1
            self.combo_count = 0
            self.resolve_matches(score_matches=True, initial_clear=initial_clear)
            return True

        matches = self.find_matches()

        if not matches:
            self.swap_gems(pos1, pos2)
            return False

        self.moves_remaining -= 1
        self.combo_count = 0
        bomb_match = self.find_four_match(matches, (pos1, pos2))
        bomb_info = None
        if bomb_match:
            positions, direction = bomb_match
            bomb_position = pos1 if pos1 in positions else pos2
            bomb_info = (bomb_position, direction)
        self.resolve_matches(score_matches=True, bomb_info=bomb_info)
        return True

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

    def render(self, surface):
        board_rect = pygame.Rect(
            self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
        )
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)

                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(
                        surface, (255, 255, 255), tile_rect, width=1, border_radius=10
                    )
                    if isinstance(gem, BombGem):
                        center = tile_rect.center
                        pygame.draw.circle(surface, (255, 255, 255), center, 18, width=3)
                        if gem.direction == "horizontal":
                            pygame.draw.line(
                                surface, (255, 255, 255),
                                (center[0] - 12, center[1]),
                                (center[0] + 12, center[1]), width=3
                            )
                        else:
                            pygame.draw.line(
                                surface, (255, 255, 255),
                                (center[0], center[1] - 12),
                                (center[0], center[1] + 12), width=3
                            )

                if self.selected == (r, c):
                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE
                    sel_rect = pygame.Rect(sel_x + 2, sel_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(
                        surface, (255, 255, 255), sel_rect, width=4, border_radius=10
                    )
