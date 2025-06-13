import pygame
import math
import sys
import heapq

# Initialize Pygame
pygame.init()

# Define constants
GRID_ROWS = 6
GRID_COLS = 10
HEX_RADIUS = 40 # Using HEX_RADIUS directly for consistent sizing
HEX_HEIGHT = HEX_RADIUS * math.sqrt(3)
HEX_WIDTH = HEX_RADIUS * 2

# Calculate pixel dimensions for the grid area (including offsets from hex_to_pixel)
GRID_PIXEL_AREA_WIDTH = int(HEX_RADIUS * 3/2 * (GRID_COLS - 1) + HEX_RADIUS * 2 + 50) # Max X + radius + initial offset
GRID_PIXEL_AREA_HEIGHT = int(HEX_RADIUS * math.sqrt(3) * (GRID_ROWS - 1 + 0.5) + HEX_RADIUS * 2 + 50) # Max Y + radius + initial offset

INFO_PANEL_WIDTH = 350 # Width for the new information panel
SCREEN_WIDTH = GRID_PIXEL_AREA_WIDTH + INFO_PANEL_WIDTH
SCREEN_HEIGHT = max(GRID_PIXEL_AREA_HEIGHT, 600) # Ensure enough height for both grid and panel (min 600)


# Map symbols and colors
CELL_COLORS = {
    ' ': (255, 255, 255), #Empty space
    'O': (165, 165, 165), #Obstacle
    '$': (255, 213, 3), #Treasure
    # Traps (Using single color for all traps as in original code)
    '(~)': (234, 135, 237),
    '(+)': (234, 135, 237),
    '(x)': (234, 135, 237),
    '(/)': (234, 135, 237),
    # Rewards (Using single color for all rewards as in original code)
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

font = pygame.font.SysFont(None, 22) # Slightly smaller font for better fit, adjusted from 24

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
            game_log.append(f"No path found to treasure at {nearest}. Stopping.")
            break

        # Remove the first node if it's a duplicate (already in path)
        if path and partial_path and partial_path[0] == path[-1]:
            path.extend(partial_path[1:])
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

# --- NEW: Helper function to wrap text ---
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
            
            # If a single word is too long, add it as its own line (it will exceed)
            # A more advanced solution would hyphenate or truncate long words.
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

    text_start_y = 10 # Starting Y position for text
    line_height = font.get_linesize() + 2 # Get actual font line height + a small gap
    
    # Max text width inside the panel, considering 10px padding on each side
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
        text_surface = font.render(line, True, (0, 0, 0)) # Render message in black
        screen.blit(text_surface, (panel_x + 10, current_y)) # 10px padding from left of panel
        current_y += line_height # Move to the next line for the next message/wrapped part

# Main loop
def main():
    clock = pygame.time.Clock()
    
    # Initialize counters for steps and energy (still simple counts, not assignment rules yet)
    total_simple_steps_taken = 0
    total_simple_energy_used = 0 # Assuming 1 energy unit per simple step

    game_log.append("Calculating path...") # Log initial status
    path = all_treasures_path(entry)
    game_log.append(f"Path calculated with {len(path)} cells traversed.")
    # The full path string can be very long. Let's make it shorter for the GUI log if needed.
    # For now, it's included, but if it overflows, you might want to truncate it.
    game_log.append(f"Full Path Length: {len(path)} steps.") 
    
    path_index = 0
    animation_speed_ms = 100    # delay between steps (in milliseconds)
    last_update_time = pygame.time.get_ticks()

    while True:
        screen.fill((255, 255, 255)) # Fill entire screen with white background

        current_time = pygame.time.get_ticks()

        # Check if it's time for the next animation step and if there are steps left
        if current_time - last_update_time > animation_speed_ms and path_index < len(path):
            # Only log if path_index is greater than 0 (i.e., not the starting position)
            if path_index > 0:
                current_coords = path[path_index]
                row, col = current_coords
                cell_type = board[row][col]
                
                # Increment simple counters
                total_simple_steps_taken += 1
                total_simple_energy_used += 1 # Each simple step costs 1 energy unit

                # Log step details to game_log
                game_log.append(f"Move {path_index}: To ({row}, {col}) '{cell_type}' | Steps: {total_simple_steps_taken} | Energy: {total_simple_energy_used}")
            
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

        pygame.display.flip() # Update the full display surface
        clock.tick(60) # Limit frame rate to 60 FPS

if __name__ == "__main__":
    main()