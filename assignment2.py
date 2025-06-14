import pygame
import math
import sys
import heapq

class State:
    def __init__(self, pos, g_cost, gravity, speed, treasures, path, last_dir=None, traps_and_rewards=None):
        self.pos = pos
        self.g_cost = g_cost
        self.gravity = gravity
        self.speed = speed
        self.treasures = treasures  # set of remaining treasures
        self.path = path
        self.last_dir = last_dir
        self.traps_and_rewards = traps_and_rewards # set of unused traps/rewards

    def __lt__(self, other):
        return self.g_cost < other.g_cost

# Initialize Pygame
pygame.init()

# Define constants
GRID_ROWS = 6
GRID_COLS = 10
HEX_RADIUS = 40
HEX_HEIGHT = HEX_RADIUS * math.sqrt(3)
HEX_WIDTH = HEX_RADIUS * 2

# Calculate pixel dimensions for the grid area
GRID_PIXEL_AREA_WIDTH = int(HEX_RADIUS * 3/2 * (GRID_COLS - 1) + HEX_RADIUS * 2 + 50)
GRID_PIXEL_AREA_HEIGHT = int(HEX_RADIUS * math.sqrt(3) * (GRID_ROWS - 1 + 0.5) + HEX_RADIUS * 2 + 50)

INFO_PANEL_WIDTH = 350
SCREEN_WIDTH = GRID_PIXEL_AREA_WIDTH + INFO_PANEL_WIDTH
SCREEN_HEIGHT = max(GRID_PIXEL_AREA_HEIGHT, 600)


# Map symbols and colors
CELL_COLORS = {
    ' ': (255, 255, 255), #Empty space
    'O': (165, 165, 165), #Obstacle
    '$': (255, 213, 3), #Treasure
    # Traps
    '(~)': (234, 135, 237),
    '(+)': (234, 135, 237),
    '(x)': (234, 135, 237),
    '(/)': (234, 135, 237),
    # Rewards
    '[+]': (18, 196, 149),
    '[x]': (18, 196, 149)
}

# Define board variables
board = [
    [' ', ' ', ' ', ' ', '[+]', ' ', ' ', ' ', ' ', ' '],
    [' ', '(+)', ' ', '(/)', '$', ' ', '(x)', ' ', 'O', ' '],
    [' ', ' ', 'O', ' ', 'O', ' ', ' ', '[x]', '(~)', ' '],
    ['O', '[+]', ' ', 'O', ' ', '(x)', 'O', '$', ' ', '$'],
    [' ', ' ', '(+)', '$', 'O', ' ', 'O', 'O', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', '[x]', ' ', ' ', ' ', ' ']
]

entry = (0, 0) # Player starting point
player_pos = entry # Keep track of current player position

traps_and_rewards = ['(~)', '(+)', '(x)', '(/)', '[+]', '[x]']

# List of all treasure coordinates
all_treasures = [(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS) if board[r][c] == '$']
all_effects = [(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS) if board[r][c] in traps_and_rewards]

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Virtual Treasure Hunt")

font = pygame.font.SysFont(None, 22)

# Global list to store messages for the GUI log
game_log = []

# Valid movements (account for hex grid)
EVEN_COL_MOVES = [
    (0, -1),    # Up left
    (0, +1),    # Up right
    (-1, 0),    # Up
    (+1, 0),    # Down
    (+1, -1),   # Down left
    (+1, +1)    # Down right
]

ODD_COL_MOVES = [
    (0, -1),    # Down left
    (0, +1),    # Down right
    (-1, 0),    # Up
    (+1, 0),    # Down
    (-1, -1),   # Up left
    (-1, +1)    # Up right
]

# Apply transformations on moves landing in Trap 3
TRAP_3_MOVES = {
    # Trap 3 is in even column, so only use moves from odd columns
    (+1, 0): (+2, -1),
    (-1, 0): (-2, -1),
    (+1, +1): (+2, +1),
    (+1, -1): (-2, +1),
    (0, +1): (0, +2),
    (0, -1): (0, -2)
}

def heuristic(a, b):
    # Heuristic function for A* search
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(pos):
    row, col = pos
    # Select movement set based on column type
    moves = EVEN_COL_MOVES if col % 2 == 0 else ODD_COL_MOVES
    results = []

    for dr, dc in moves:
        nr, nc = row + dr, col + dc
        if in_bounds((nr, nc)) and is_valid((nr, nc)):
            # Return list of neighbors and the moves to reach them
            results.append(((nr, nc), (dc, dr))) 

    return results

def in_bounds(pos):
    row, col = pos
    # Check if row and col are within bounds of grid
    return 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS

def is_valid(pos):
    row, col = pos
    # Check if within bounds + no obstacles
    return in_bounds(pos) and board[row][col] != 'O'

def a_star(start, goal, treasures):
    open_set = []
    start_state = State(start, 0, 1.0, 1.0, treasures.copy(), [start], None, all_effects.copy())
    heapq.heappush(open_set, (0, start_state))
    visited = set()

    while open_set:
        _, state = heapq.heappop(open_set)
        r, c = state.pos

        if state.pos == goal:
            return state.path, state.g_cost

        state_id = (state.pos, tuple(sorted(state.treasures)), round(state.gravity, 2), round(state.speed, 2), tuple(sorted(state.traps_and_rewards)))
        if state_id in visited:
            continue
        visited.add(state_id)

        for neighbor, direction in get_neighbors(state.pos):
            nr, nc = neighbor
            node = board[nr][nc]

            # Avoid Trap 4 if treasures remain
            if node == '(/)' and len(state.treasures) > 0:
                continue

            # Clone state attributes
            gravity = state.gravity
            speed = state.speed
            treasures = state.treasures.copy()
            new_path = state.path + [neighbor]
            cost = state.g_cost + gravity / speed
            last_dir = direction
            traps_and_rewards = state.traps_and_rewards.copy()

            # Trap & reward effects
            if node == '(~)' and neighbor in traps_and_rewards: # Trap 1: double gravity
                gravity *= 2
                traps_and_rewards.remove(neighbor)

            elif node == '(+)' and neighbor in traps_and_rewards: # Trap 2: half speed
                speed /= 2
                traps_and_rewards.remove(neighbor)

            elif node == '(x)' and last_dir in TRAP_3_MOVES:  # Trap 3: forced teleport
                
                new_move = TRAP_3_MOVES[last_dir]
                nc += new_move[0]
                nr += new_move[1]
                
                if not in_bounds((nr, nc)) or not is_valid((nr, nc)):
                    continue  # skip invalid teleport
                neighbor = (nr, nc)
                new_path.append((nr, nc))

            elif node == '[+]' and neighbor in traps_and_rewards: # Reward 1: half gravity
                gravity /= 2
                traps_and_rewards.remove(neighbor)

            elif node == '[x]' and neighbor in traps_and_rewards: # Reward 2: double speed
                speed *= 2
                traps_and_rewards.remove(neighbor)

            elif node == '$' and neighbor in treasures:
                # remove collected treasures
                treasures.remove(neighbor)

            new_state = State(neighbor, cost, gravity, speed, treasures, new_path, last_dir, traps_and_rewards)
            priority = cost + heuristic(neighbor, goal)
            heapq.heappush(open_set, (priority, new_state))

    return [], float('inf')

# Calculate the shortest path to collect all treasures
def all_treasures_path(start):
    treasures = set(all_treasures)
    path = []
    current = start

    while treasures:
        # Find the nearest treasure
        best = None
        best_energy = float('inf')

        for t in treasures:
            partial_path, energy = a_star(current, t, treasures)
            if partial_path and energy < best_energy:
                best = (partial_path, t)
                best_energy = energy

        if not best:
            break

        partial_path, t = best
        # Remove the first node if it's a duplicate (already in path)
        if path and partial_path[0] == path[-1]:
            path.extend(partial_path[1:])
        else:
            path.extend(partial_path)

        current = t
        treasures.remove(t)

    return path

# Draw the grid
def draw_grid(path=[], path_index=None):
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x, y = hex_to_pixel(col, row, HEX_RADIUS)
            
            # get color based on cell type
            cell_type = board[row][col]
            color = CELL_COLORS.get(cell_type, (255, 255, 255))

            # draw the hexagons
            pygame.draw.polygon(screen, color, hex_corners(x, y, HEX_RADIUS))
            pygame.draw.polygon(screen, (0, 0, 0), hex_corners(x, y, HEX_RADIUS), 2) # hex border
            
            if (cell_type not in ['O', '$', ' ']):
                # insert text labels for traps and rewards only
                label = font.render(cell_type, True, (0,0,0))
                label_rect = label.get_rect(center=(x, y))
                screen.blit(label, label_rect)

    # Draw animated path (green dots)
    if path and path_index is not None:
        for i in range(min(path_index, len(path))):
            row, col = path[i]
            x, y = hex_to_pixel(col, row, HEX_RADIUS)
            pygame.draw.circle(screen, (0, 255, 0), (int(x), int(y)), 8)

# Convert axial to pixel coordinates
def hex_to_pixel(col, row, size):
    x_offset = size * 3/2 * col + 50 # Small offset from left edge
    y_offset = size * math.sqrt(3) * (row + 0.5 * (col % 2 == 0)) + 50 # Small offset from top edge
    return (x_offset, y_offset)

# Calculate hexagon points for drawing
def hex_corners(x, y, size):
    corners = []
    for i in range(6):
        angle = math.radians(60 * i)
        cx = x + size * math.cos(angle)
        cy = y + size * math.sin(angle)
        corners.append((cx, cy))
    return corners

# Helper function to wrap text
def wrap_text(text, font, max_width):
    words = text.split(' ')
    wrapped_lines = []
    current_line = []
    
    for word in words:
        # Test if adding the next word exceeds max_width
        test_line = " ".join(current_line + [word])
        text_width, _ = font.size(test_line)
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            # If current_line is not empty, add it to wrapped_lines
            if current_line:
                wrapped_lines.append(" ".join(current_line))
            # Start a new line with the current word
            current_line = [word]
            
            # If a single word is too long, add it as its own line
            if font.size(word)[0] > max_width and not wrapped_lines and not current_line: # Edge case: very first word is too long
                wrapped_lines.append(word)
                current_line = [] # Reset for next words
            elif font.size(word)[0] > max_width and current_line == [word]: # if a single word that starts a new line is too long
                 wrapped_lines.append(word) # Add it and move on
                 current_line = []

    if current_line:
        wrapped_lines.append(" ".join(current_line))
    
    return wrapped_lines

# Modified function to draw the information panel / log
def draw_info_panel(screen, log_messages, panel_x, panel_width, panel_height):
    # Draw background for the panel
    pygame.draw.rect(screen, (230, 230, 230), (panel_x, 0, panel_width, panel_height))
    # Draw a separator line
    pygame.draw.line(screen, (100, 100, 100), (panel_x, 0), (panel_x, panel_height), 2)

    text_start_y = 10
    line_height = font.get_linesize() + 2
    
    # Max text width inside the panel
    max_text_width = panel_width - 20 

    current_y = text_start_y
    
    # Build a list of all lines to display, including wrapped ones
    all_display_lines = []
    for msg in log_messages:
        # Wrap each message before adding its lines to the display list
        wrapped_parts = wrap_text(msg, font, max_text_width)
        all_display_lines.extend(wrapped_parts)
    
    # Calculate how many total lines (after wrapping) can fit in the panel
    max_lines_to_display = int(panel_height / line_height) - 1 # Leave some padding

    # Display only the most recent messages that fit
    if len(all_display_lines) > max_lines_to_display:
        all_display_lines = all_display_lines[-max_lines_to_display:]

    for line in all_display_lines:
        text_surface = font.render(line, True, (0, 0, 0))
        screen.blit(text_surface, (panel_x + 10, current_y))
        current_y += line_height # Move to the next line for the next message/wrapped part

# Main loop
def main():
    clock = pygame.time.Clock()
    
    # Initialize counters for steps and energy
    total_simple_steps_taken = 0
    total_simple_energy_used = 0 # Assuming 1 energy unit per simple step

    game_log.append("Calculating path...") # Log initial status
    path = all_treasures_path(entry)
    game_log.append(f"Path calculated with {len(path)} cells traversed.")
    game_log.append(f"Full Path Length: {len(path)} steps.") 
    
    path_index = 0
    animation_speed_ms = 100 # delay between steps
    last_update_time = pygame.time.get_ticks()

    # Keep track of gravity and speed for the log
    current_gravity = 1.0
    current_speed = 1.0

    while True:
        screen.fill((255, 255, 255))

        current_time = pygame.time.get_ticks()

        # Check if it's time for the next animation step and if there are steps left
        if current_time - last_update_time > animation_speed_ms and path_index < len(path):
            if path_index > 0:
                current_coords = path[path_index]
                row, col = current_coords
                cell_type = board[row][col]
                
                # Increment simple counters
                total_simple_steps_taken += 1 / current_speed # Speed affects steps per move
                total_simple_energy_used += 1 * (current_gravity / current_speed) # energy dependent on gravity and speed

                # Log step details to game_log
                game_log.append(f"Move {path_index}: To ({row}, {col}) '{cell_type}' | Steps: {total_simple_steps_taken} | Energy: {total_simple_energy_used}")

                # Perform checks to keep log in sync with algorithm
                if cell_type == '(~)' and board[row][col] in traps_and_rewards:
                    current_gravity *= 2
                    traps_and_rewards.remove(board[row][col])

                elif cell_type == '(+)' and board[row][col] in traps_and_rewards:
                    current_speed /= 2
                    traps_and_rewards.remove(board[row][col])

                elif cell_type == '(x)' and board[row][col] in traps_and_rewards:
                    total_simple_steps_taken += 1
                    total_simple_energy_used += 1

                elif cell_type == '[+]' and board[row][col] in traps_and_rewards:
                    current_gravity /= 2
                    traps_and_rewards.remove(board[row][col])

                elif cell_type == '[x]' and board[row][col] in traps_and_rewards:
                    current_speed *= 2
                    traps_and_rewards.remove(board[row][col])

            path_index += 1
            last_update_time = current_time
        
        # Log when animation is complete
        if path_index >= len(path) and "Animation Complete!" not in game_log:
            game_log.append("Animation Complete!")
            game_log.append(f"Final simple steps taken: {total_simple_steps_taken}")
            game_log.append(f"Final simple energy used: {total_simple_energy_used}")


        # Draw the grid
        draw_grid(path, path_index)
        
        # Draw the info panel on the right side of the grid
        draw_info_panel(screen, game_log, GRID_PIXEL_AREA_WIDTH, INFO_PANEL_WIDTH, SCREEN_HEIGHT)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()