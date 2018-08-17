import pygame, sys, math
from pygame.locals import *

FPS = 30
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
IMG_WIDTH = 120
IMG_HEIGHT = 90
IMG_X = 400
IMG_Y = 300
HOOK_X = 430
HOOK_Y = 390

DEGREE_MAX = 90
DEGREE_DELTA = 5

BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)

def main():
    global display_surf
    pygame.init()
    fps_lock = pygame.time.Clock()
    display_surf = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Building')

    floor_angle = 0
    floor_angle_anticlock = True
    while True:
        checkForQuit()
        drawBackground()
        drawHook(HOOK_X, HOOK_Y)
        drawFloor(IMG_X, IMG_Y, IMG_WIDTH, IMG_HEIGHT, HOOK_X, HOOK_Y, floor_angle)
        if floor_angle_anticlock is True: 
            if floor_angle < DEGREE_MAX:
                floor_angle += DEGREE_DELTA
            else:
                floor_angle_anticlock = False
                floor_angle -= DEGREE_DELTA
        elif floor_angle_anticlock is False: 
            if floor_angle > -DEGREE_MAX:    
                floor_angle -= DEGREE_DELTA
            else:
                floor_angle_anticlock = True
                floor_angle += DEGREE_DELTA
        pygame.display.update()
        fps_lock.tick(FPS)

def drawBackground():
    ''' Draw background for main routine
    '''
    display_surf.fill(WHITE)
    
def drawHook(pos_x, pos_y):
    pygame.draw.rect(display_surf, BLACK, (pos_x, pos_y, 1, 1))
        
def drawFloor(org_x, org_y, w, h, hook_x, hook_y, a):
    floor_img = pygame.image.load("resource/floor/floor0.png")
    floor_img = pygame.transform.scale(floor_img, (w, h))
    floor_img = pygame.transform.rotate(floor_img, a)

    img_x = (org_x-hook_x)*math.cos(math.radians(a)) + (org_y-hook_y)*math.sin(math.radians(a)) + hook_x
    img_y = -(org_x-hook_x)*math.sin(math.radians(a)) + (org_y-hook_y)*math.cos(math.radians(a)) + hook_y
    
    if a >= 0:
        pos_x = img_x
        pos_y = img_y-w*math.sin(math.radians(a))
    else:
        pos_x = img_x + h*math.sin(math.radians(a))
        pos_y = img_y
    display_surf.blit(floor_img, (pos_x, pos_y))        
    
def checkForQuit():
    ''' Check for quit by system or esc button
    Throw back all button event to avoid missing in following routine
    '''
    for event in pygame.event.get(QUIT):
        terminate()
    for event in pygame.event.get(KEYUP):
        if event.key == K_ESCAPE:
            terminate()
        pygame.event.post(event) #放回所有的事件
        
def terminate():
    ''' Quit game
    '''
    pygame.quit()
    sys.exit()            
    
if __name__ == '__main__':
    main()