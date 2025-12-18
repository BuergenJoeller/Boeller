import sys
import json
import math
import random
from collections import deque

class Point:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"({self.x},{self.y})"


class GameState:
    def __init__(self):
        self.raw_walls = []
        self.raw_floors = []
        self.my_position = None
        self.current_gems = []


class Bot:
    # Aktionen
    ACTION_UP = 0
    ACTION_RIGHT = 1
    ACTION_DOWN = 2
    ACTION_LEFT = 3
    ACTION_NONE = 4

    # Tiles
    TILE_FLOOR = 0
    TILE_WALL = 1
    TILE_UNKNOWN = -1

    # Gedächtnis
    known_world = {}
    last_seen_map = {}
    known_gems = set()
    current_tick = 0
    last_move = ACTION_NONE

    # Aktives Ziel (Gem)
    current_target = None

    # =========================
    # Main Loop
    # =========================
    @staticmethod
    def main():
        json_buffer = []
        open_braces = 0

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            json_buffer.append(line)
            for c in line:
                if c == '{':
                    open_braces += 1
                elif c == '}':
                    open_braces -= 1

            if open_braces == 0 and json_buffer:
                Bot.process_game_tick("".join(json_buffer))
                json_buffer = []

    @staticmethod
    def process_game_tick(json_str):
        Bot.current_tick += 1
        state = Bot.parse_game_state(json_str)
        Bot.update_memory(state)

        action = Bot.berechne_naechsten_schritt(state)
        if action == Bot.ACTION_NONE:
            action = Bot.fallback_move(state)

        Bot.last_move = action

        if action == Bot.ACTION_UP:
            print("N")
        elif action == Bot.ACTION_RIGHT:
            print("E")
        elif action == Bot.ACTION_DOWN:
            print("S")
        elif action == Bot.ACTION_LEFT:
            print("W")
        else:
            print("N")

        sys.stdout.flush()

    # =========================
    # Memory Update
    # =========================
    @staticmethod
    def update_memory(state):
        for g in state.current_gems:
            Bot.known_gems.add(g)

        # Gem eingesammelt
        if state.my_position in Bot.known_gems:
            Bot.known_gems.remove(state.my_position)
            if Bot.current_target == state.my_position:
                Bot.current_target = None

        for p in state.raw_floors:
            Bot.known_world[p] = Bot.TILE_FLOOR
            Bot.last_seen_map[p] = Bot.current_tick

        for p in state.raw_walls:
            Bot.known_world[p] = Bot.TILE_WALL
            Bot.last_seen_map[p] = Bot.current_tick

        if state.my_position:
            Bot.known_world[state.my_position] = Bot.TILE_FLOOR
            Bot.last_seen_map[state.my_position] = Bot.current_tick

    # =========================
    # TODO 1: Nächstes Gem
    # =========================
    @staticmethod
    def find_closest_gem(start, gems):
        if not gems:
            return None

        closest = None
        best_dist = math.inf

        for g in gems:
            d = abs(g.x - start.x) + abs(g.y - start.y)
            if d < best_dist:
                best_dist = d
                closest = g

        return closest

    # =========================
    # TODO 2 & 3: Entscheidung
    # =========================
    @staticmethod
    def berechne_naechsten_schritt(state):
        start = state.my_position
        if not start:
            return Bot.ACTION_NONE

        # 1. Falls kein Ziel existiert, wähle eines
        if Bot.current_target is None and Bot.known_gems:
            Bot.current_target = Bot.find_closest_gem(start, Bot.known_gems)

        # 2. Falls ein Ziel existiert: kompromisslos verfolgen
        if Bot.current_target:
            action = Bot.bfs_suche(start, Bot.current_target, explore_mode=False)
            if action != Bot.ACTION_NONE:
                return action
            else:
                # Ziel aktuell nicht erreichbar
                Bot.current_target = None

        # 3. Nur wenn kein Gem existiert: Exploration
        return Bot.bfs_suche(start, None, explore_mode=True)

    # =========================
    # BFS
    # =========================
    @staticmethod
    def bfs_suche(start, fixed_target, explore_mode):
        queue = deque([start])
        parents = {start: None}
        visited = {start}
        found = None

        while queue:
            current = queue.popleft()

            if explore_mode:
                if Bot.known_world.get(current) == Bot.TILE_FLOOR:
                    last_seen = Bot.last_seen_map.get(current, 0)
                    if Bot.current_tick - last_seen > 30 or Bot.is_frontier(current):
                        found = current
                        break
            else:
                if fixed_target and current == fixed_target:
                    found = current
                    break

            for dx, dy in [(0,-1),(1,0),(0,1),(-1,0)]:
                n = Point(current.x + dx, current.y + dy)
                if n not in visited and Bot.known_world.get(n) == Bot.TILE_FLOOR:
                    visited.add(n)
                    parents[n] = current
                    queue.append(n)

        if found:
            curr = found
            while parents[curr] and parents[curr] != start:
                curr = parents[curr]
            return Bot.ermittle_richtung(start, curr)

        return Bot.ACTION_NONE

    # =========================
    # Hilfsfunktionen
    # =========================
    @staticmethod
    def is_frontier(p):
        for dx, dy in [(0,-1),(1,0),(0,1),(-1,0)]:
            if Point(p.x + dx, p.y + dy) not in Bot.known_world:
                return True
        return False

    @staticmethod
    def fallback_move(state):
        for action in [Bot.last_move, Bot.ACTION_UP, Bot.ACTION_RIGHT, Bot.ACTION_DOWN, Bot.ACTION_LEFT]:
            if Bot.is_valid_move(state.my_position, action):
                return action
        return Bot.ACTION_NONE

    @staticmethod
    def is_valid_move(pos, action):
        dx, dy = 0, 0
        if action == Bot.ACTION_UP:
            dy = -1
        elif action == Bot.ACTION_RIGHT:
            dx = 1
        elif action == Bot.ACTION_DOWN:
            dy = 1
        elif action == Bot.ACTION_LEFT:
            dx = -1

        n = Point(pos.x + dx, pos.y + dy)
        return Bot.known_world.get(n) != Bot.TILE_WALL

    @staticmethod
    def ermittle_richtung(start, to):
        if to.y < start.y:
            return Bot.ACTION_UP
        if to.x > start.x:
            return Bot.ACTION_RIGHT
        if to.y > start.y:
            return Bot.ACTION_DOWN
        if to.x < start.x:
            return Bot.ACTION_LEFT
        return Bot.ACTION_NONE

    # =========================
    # JSON Parsing
    # =========================
    @staticmethod
    def parse_game_state(json_str):
        state = GameState()
        data = json.loads(json_str)

        bot_data = data.get("bot") or data.get("agent")
        if bot_data:
            state.my_position = Point(bot_data[0], bot_data[1])

        if "wall" in data:
            state.raw_walls = [Point(x,y) for x,y in data["wall"]]
        if "floor" in data:
            state.raw_floors = [Point(x,y) for x,y in data["floor"]]

        gems = data.get("gems") or data.get("visible_gems")
        if gems:
            if isinstance(gems[0], list):
                state.current_gems = [Point(x,y) for x,y in gems]
            else:
                state.current_gems = [Point(gems[0], gems[1])]

        return state


if __name__ == "__main__":
    Bot.main()
