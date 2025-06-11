import pygame
import math
import sys
import heapq

# Initialize Pygame
pygame.init()

# Define constants
GRID_ROWS = 6
GRID_COLS = 10
CELL_SIZE = 64
HEX_RADIUS = 40

# Set up the display
SCREEN_WIDTH = GRID_COLS * CELL_SIZE * 2
SCREEN_HEIGHT = GRID_ROWS * CELL_SIZE * 2

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

# List of all treasure coordinates
all_treasures = [(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS) if board[r][c] == '$']

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Virtual Treasure Hunt")

font = pygame.font.SysFont(None, 32)

# Valid movements (account for hex grid)
EVEN_COL_MOVES = [
    (0, -1),  # Up left
    (0, +1),  # Up right
    (-1, 0),  # Up
    (+1, 0),  # Down
    (+1, -1), # Down left
    (+1, +1)  # Down right
]

ODD_COL_MOVES = [
    (0, -1),  # Down left
    (0, +1),  # Down right
    (-1, 0),  # Up
    (+1, 0),  # Down
    (-1, -1), # Up left
    (-1, +1)  # Up right
]

def heuristic(a, b):

    # Heuristic function for A* search
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(pos):

    row, col = pos

    # choose movement sets based on even or odd column
    movements = EVEN_COL_MOVES if col % 2 == 0 else ODD_COL_MOVES
    neighbors = []

    for dr, dc in movements:

        nr, nc = row + dr, col + dc

        # Compile the list of possible nodes to visit next
        if in_bounds((nr, nc)) and is_valid((nr, nc)):

            neighbors.append((nr, nc))

    return neighbors

def in_bounds(pos):

    row, col = pos

    # Check if row and col are within bounds of grid
    return 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS

def is_valid(pos):
    
    row, col = pos

    # Check if within bounds + no obstacles
    return in_bounds(pos) and board[row][col] != 'O'

def a_star(start, goal):

    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:

        _, current = heapq.heappop(open_set)

        if current == goal:

            # Reconstruct path
            path = []

            while current in came_from:

                path.append(current)
                current = came_from[current]

            path.append(start)
            return path[::-1]

        # Neighbor exploration
        for neighbor in get_neighbors(current):

            tentative_g = g_score[current] + 1

            # Update path if improvement found
            if neighbor not in g_score or tentative_g < g_score[neighbor]:

                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))
                came_from[neighbor] = current

    return []

# Calculate the shortest path to collect all treasures
def all_treasures_path(start):

    treasures = list(all_treasures)
    path = []
    current = start

    while treasures:

        # Find nearest treasure
        treasures.sort(key=lambda t: heuristic(current, t))
        nearest = treasures.pop(0)
        partial_path = a_star(current, nearest)

        if not partial_path:

            break

        if path and partial_path[0] == path[-1]:

            path.extend(partial_path[1:])  # Avoid repeating node

        else:

            path.extend(partial_path)

        current = nearest

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

    # Draw animated path
    if path and path_index is not None:

        for i in range(min(path_index, len(path))):

            row, col = path[i]
            x, y = hex_to_pixel(col, row, HEX_RADIUS)
            pygame.draw.circle(screen, (0, 255, 0), (int(x), int(y)), 8)

# Convert axial to pixel coordinates
def hex_to_pixel(col, row, size):

    x_offset = size * 3/2 * col + 100
    y_offset = size * math.sqrt(3) * (row + 0.5 * (col % 2 == 0)) + 100
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

# Main loop
def main():
    clock = pygame.time.Clock()
    path = all_treasures_path(entry)
    path_index = 0
    animation_speed_ms = 100  # delay between steps (in milliseconds)
    last_update_time = pygame.time.get_ticks()

    while True:
        screen.fill((255, 255, 255))

        current_time = pygame.time.get_ticks()

        if current_time - last_update_time > animation_speed_ms and path_index < len(path):

            path_index += 1
            last_update_time = current_time

        draw_grid(path, path_index)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()