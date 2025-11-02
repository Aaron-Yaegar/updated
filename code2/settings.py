import pygame 
from os.path import join 
from os import walk

WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720 
TILE_SIZE = 64

# Game States
MENU = 0
GAME_ACTIVE = 1
GAME_OVER = 2

# Menu Colors
MENU_BG_COLOR = (20, 20, 30)
BUTTON_COLOR = 'cyan'
