import pygame
import math
import sys

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

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Virtual Treasure Hunt")

# Font setup
font = pygame.font.SysFont(None, 32)

# Draw the grid
def draw_grid():

    for row in range(GRID_ROWS):

        for col in range(GRID_COLS):

            x, y = hex_to_pixel(col, row, HEX_RADIUS)

            # get color based on cell type
            cell_type = board[row][col]
            color = CELL_COLORS.get(cell_type, (255, 255, 255))

            # draw the hexagons
            pygame.draw.polygon(screen, color, hex_corners(x, y, HEX_RADIUS))
            pygame.draw.polygon(screen, (0, 0, 0), hex_corners(x, y, HEX_RADIUS), 2) # hex border
            
            if (cell_type != 'O') and (cell_type != '$'):

                # insert text labels for traps and rewards only
                label = font.render(cell_type, True, (0,0,0))
                label_rect = label.get_rect(center=(x, y))
                screen.blit(label, label_rect)

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

    while True:
        screen.fill((255, 255, 255))
        draw_grid()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()