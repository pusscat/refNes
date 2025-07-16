import sys
import pygame
from pygame.locals import *
from random import randint

pygame.init()
window = pygame.display.set_mode([256, 240])
surface = pygame.PixelArray(window)

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
    surface[randint(0,255), randint(0,239)] = pygame.Color(randint(0,255), randint(0,255), randint(0,255))
    pygame.display.update()
