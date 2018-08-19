#coding:utf-8
#copyright: fiorezhang@sina.com

import sys
import math
import numpy as np
import random
import time
import pygame
from pygame.locals import *

#全局
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 15
MUSIC = True

#参数设定
BASIC_SPEED = WINDOW_WIDTH//400

CLOUD_WIDTH = 100
CLOUD_HEIGHT = 75
CLOUD_SPEED = BASIC_SPEED
CLOUD_CNT = 5

RULER_WIDTH = 120
RULER_HEIGHT = 300
RULER_X = WINDOW_WIDTH-RULER_WIDTH
RULER_Y = WINDOW_HEIGHT-RULER_HEIGHT

LIFT_WIDTH = 600
LIFT_HEIGHT = 200
LIFT_X = 0
LIFT_Y = 0

BASE_WIDTH = 145
BASE_HEIGHT = 100
BASE_X = 77
BASE_Y = WINDOW_HEIGHT-BASE_HEIGHT

RACK_WIDTH = 40
RACK_HEIGHT = 75
RACK_CNT = (WINDOW_HEIGHT-BASE_HEIGHT-LIFT_HEIGHT)//RACK_HEIGHT + 1
RACK_X = 133
RACK_Y = LIFT_HEIGHT

HOOK_WIDTH = 40
HOOK_HEIGHT = 50
HOOK_X_L = 300
HOOK_X_R = 500
HOOK_Y = 100
HOOK_SPEED = BASIC_SPEED

#====颜色
BLACK           = (  0,   0,   0)
WHITE           = (255, 255, 255)
GREY            = (185, 185, 185)
LIGHTGREY       = (225, 225, 225)
GREEN           = (  0, 155,   0)
LIGHTGREEN      = ( 40, 195,  40)
YELLOW          = (155, 155,   0)
LIGHTYELLOW     = (195, 195,  40)
BLUE            = (  0,   0, 155)
LIGHTBLUE       = ( 40,  40, 195)
RED             = (155,   0,   0)
LIGHTRED        = (195,  40,  40)
COLOR_BG_START  = ( 80, 100, 150)
COLOR_BG_OVER   = BLACK
COLOR_BG        = WHITE

STATE = {
    "HANG":   0, 
    "DROP":   1, 
    "LVUP":   2,
    "FAIL":   3, 
}


#====程序主体架构
def main():
    ''' Initialization. 
    Fps and main surface is globalized, for all scenes. 
    Game start with a start screen, then loop in main routine and end screen(show a score)
    '''
    global fps_lock, display_surf

    pygame.init()
    pygame.mixer.init()
    fps_lock = pygame.time.Clock()
    display_surf = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Ladder')

    #showStartScreen()
    while True:
        score = runGame()
        showGameOverScreen(score)
        
#====主要函数
def showStartScreen():
    ''' Start screen. 
    Play start music. Show title and button prompt. Show more items for good look. 
    '''
    if MUSIC == True:
        pygame.mixer.music.load("resource/sound/random.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1, 0.0)
    while True:
        checkForQuit()
        drawBackgroundStart()    
        drawImageStart()
        drawTitleStart()
        drawPromptStart()
        pygame.display.update()
        fps_lock.tick(FPS)
        if checkForSpaceDown() == True:
            pygame.mixer.music.fadeout(1000)
            break

def showGameOverScreen(score):
    ''' Game over screen. 
    Play music and taunt. Show score and button prompt. 
    '''
    if MUSIC == True:
        pygame.mixer.music.load("resource/sound/random.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1, 0.0)    
    while True:
        checkForQuit()
        drawBackgroundOver()    
        drawScoreOver(score)
        drawPromptOver()
        pygame.display.update()
        fps_lock.tick(FPS)
        time.sleep(1) #避免过快跳过游戏结束界面开始下一局
        if checkForSpaceDown() == True:
            if MUSIC == True:
                pygame.mixer.music.stop()
            break
    
def runGame():
    #本地变量，各种标记，缓存
    gameOver = False
    move = True
    state = STATE["HANG"]
    
    #本地变量，初始化各个元素
    clouds = initialCloud()
    crane = initialCrane()
    score = initialScore()    
    
    #MUSIC
    if MUSIC == True:
        pygame.mixer.music.load("resource/sound/ringsignal_gravitationalconstant.mp3")
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1, 0.0)
    sound_main_01 = pygame.mixer.Sound("resource/sound/notification_msg_01.wav")
    sound_main_02 = pygame.mixer.Sound("resource/sound/notification_msg_02.wav")
    sound_main_03 = pygame.mixer.Sound("resource/sound/notification_msg_03.wav")
    sound_main_04 = pygame.mixer.Sound("resource/sound/notification_msg_04.wav")
    sound_main_05 = pygame.mixer.Sound("resource/sound/notification_msg_05.wav")
    
    while gameOver == False:
        #检测退出事件
        checkForQuit()

        #TODO
        if checkForSpaceDown() == True:
            if MUSIC == True:
                pygame.mixer.music.stop()
            gameOver = True
        #TODO

        #更新各个元素
        clouds = updateCloud(clouds, move)
        crane = updateCrane(crane, move, state)
        score = updateScore(score, move)
        
        #绘图步骤 --------
        drawBackground()
        drawCloud(clouds)
        drawCrane(crane)
        drawScore(score)

        pygame.display.update()
        fps_lock.tick(FPS)
    print("return: %d" % score)
    if MUSIC == True:
        pygame.mixer.music.stop()
    return score              

def drawBackground():
    ''' Draw background for main routine
    '''
    display_surf.fill(COLOR_BG)

            
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
    
def clearKeyEvent():
    ''' Clear existing button event
    Used like before ladder raise. Ensure no residual button state interference the logics. 
    '''
    pygame.event.get([KEYDOWN, KEYUP])
    
def checkForSpaceDown():
    ''' Check for space button down, ignore and clear other button event
    '''
    for event in pygame.event.get(KEYDOWN):
        if event.key == K_SPACE:
            return True
    return False

def checkForSpaceUp():
    ''' Check for space button up, ignore and clear other button event
    '''
    for event in pygame.event.get(KEYUP):
        if event.key == K_SPACE:
            return True
    return False    
    
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
    
def drawBackgroundStart():
    ''' Draw background for start screen. 
    '''
    display_surf.fill(COLOR_BG_START)
    
def initialCloud():
    clouds = []
    for i in range(CLOUD_CNT):
        cloud_img = pygame.image.load("resource/cloud/cloud"+str(np.random.randint(8))+".png")
        cloud_img = pygame.transform.scale(cloud_img, (CLOUD_WIDTH, CLOUD_HEIGHT))
        cloud_pos = [np.random.randint(0, high=WINDOW_WIDTH-CLOUD_WIDTH), np.random.randint(0, high=WINDOW_HEIGHT-CLOUD_HEIGHT)]
        cloud = [cloud_img, cloud_pos]
        clouds.append(cloud) 
    return clouds
    
def updateCloud(clouds, move):
    for i, cloud in enumerate(clouds):
        cloud_img, cloud_pos = cloud[0], cloud[1]
        cloud_pos[0] += np.random.randint(CLOUD_SPEED) #随机移动水平速度
        if cloud_pos[0] > WINDOW_WIDTH:
            cloud_img = pygame.image.load("resource/cloud/cloud"+str(np.random.randint(8))+".png")
            cloud_img = pygame.transform.scale(cloud_img, (CLOUD_WIDTH, CLOUD_HEIGHT))
            cloud_pos = [-CLOUD_WIDTH, np.random.randint(0, high=WINDOW_HEIGHT-CLOUD_HEIGHT)]
        if move == True:
            cloud_pos[1] += BASIC_SPEED # 固定移动垂直速度，当视觉整体上移的时候
            if cloud_pos[1] > WINDOW_HEIGHT:
                cloud_img = pygame.image.load("resource/cloud/cloud"+str(np.random.randint(8))+".png")
                cloud_img = pygame.transform.scale(cloud_img, (CLOUD_WIDTH, CLOUD_HEIGHT))
                cloud_pos = [np.random.randint(0, high=WINDOW_HEIGHT-CLOUD_HEIGHT), -CLOUD_HEIGHT]
        cloud = [cloud_img, cloud_pos]
        clouds[i] = cloud
    return clouds
    
def drawCloud(clouds):
    ''' Draw clouds
    '''
    for cloud in clouds:
        cloud_img, cloud_pos = cloud[0], cloud[1]
        display_surf.blit(cloud_img, (cloud_pos[0], cloud_pos[1]))
    
def initialCrane():
    #架子
    racks = []
    for i in range(RACK_CNT):
        rack_y = RACK_Y + RACK_HEIGHT*i
        racks.append(rack_y)
    #底座
    base_y = BASE_Y
    #钩子
    hook_x = HOOK_X_L
    crane = [racks, base_y, hook_x]
    return crane

hook_move_r = True    
def updateCrane(crane, move, state):
    racks, base_y, hook_x = crane[0], crane[1], crane[2]
    #架子
    if racks[0] >= RACK_Y and racks[0] < RACK_Y+BASIC_SPEED: #第一节已经要挪出去了，需要在前面新增加一节
        rack_y_new = RACK_Y - RACK_HEIGHT
        racks.insert(0, rack_y_new)
    if racks[-1] >= WINDOW_HEIGHT:
        racks.pop(-1)
    if move == True:
        for i, rack_y in enumerate(racks):
            rack_y += BASIC_SPEED
            racks[i] = rack_y
    #底座
    if move == True:
        base_y += BASIC_SPEED
    #钩子
    global hook_move_r
    #TODO: only in free state
    if hook_move_r == True:
        if hook_x < HOOK_X_R:
            hook_x += HOOK_SPEED
        else:
            hook_move_r = False
    else:
        if hook_x > HOOK_X_L:
            hook_x -= HOOK_SPEED
        else:
            hook_move_r = True
    
    crane = [racks, base_y, hook_x]
    return crane
    
def drawCrane(crane):
    racks, base_y, hook_x = crane[0], crane[1], crane[2]
    #画架子
    for rack_y in racks:
        rack_img = pygame.image.load("resource/crane/rack.png")
        rack_img = pygame.transform.scale(rack_img, (RACK_WIDTH, RACK_HEIGHT))
        display_surf.blit(rack_img, (RACK_X, rack_y))
    #画上部支架
    lift_img = pygame.image.load("resource/crane/lift.png")      
    lift_img = pygame.transform.scale(lift_img, (LIFT_WIDTH, LIFT_HEIGHT))      
    display_surf.blit(lift_img, (LIFT_X, LIFT_Y))
    #画底座
    if base_y <= WINDOW_HEIGHT:
        base_img = pygame.image.load("resource/crane/base.png")      
        base_img = pygame.transform.scale(base_img, (BASE_WIDTH, BASE_HEIGHT))      
        display_surf.blit(base_img, (BASE_X, base_y))   
    #画钩子
    hook_img = pygame.image.load("resource/crane/hook.png")      
    hook_img = pygame.transform.scale(hook_img, (HOOK_WIDTH, HOOK_HEIGHT))      
    display_surf.blit(hook_img, (hook_x, HOOK_Y))
    
def initialScore():    
    return 0

def updateScore(score, move):
    if move == True:
        score += 1
    return score
    
def drawScore(score):
    ruler_img = pygame.image.load("resource/ruler/ruler.png")
    ruler_img = pygame.transform.scale(ruler_img, (RULER_WIDTH, RULER_HEIGHT))
    display_surf.blit(ruler_img, (RULER_X, RULER_Y))
    
    score_font = pygame.font.Font('freesansbold.ttf', 20)
    textSurfaceObj = score_font.render(str(score)+"m", True, BLACK, WHITE)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.topleft = (RULER_X, RULER_Y+10)
    display_surf.blit(textSurfaceObj, textRectObj)
    pass
    
def drawImageStart():
    ''' Draw start screen image
    '''
    img = pygame.image.load("resource/crane/start.jpg")
    img = pygame.transform.scale(img, (WINDOW_WIDTH, WINDOW_HEIGHT))
    display_surf.blit(img, (0, 0))            

def drawTitleStart():
    ''' Draw title for start screen. 
    '''
    title_font = pygame.font.Font('freesansbold.ttf', 100)
    textSurfaceObj = title_font.render("BUILDING", True, WHITE, COLOR_BG_START)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.topleft = (0, 0)
    display_surf.blit(textSurfaceObj, textRectObj)

def drawPromptStart():
    ''' Draw button prompt to start main routine for start screen. 
    '''
    prompt_font = pygame.font.Font('freesansbold.ttf', 20)
    textSurfaceObj = prompt_font.render("Press space key to continue!", True, WHITE, BLACK)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT-40)
    display_surf.blit(textSurfaceObj, textRectObj)

def drawBackgroundOver():
    ''' Draw background for game over screen. 
    '''
    display_surf.fill(COLOR_BG_OVER)
    
def drawScoreOver(score):
    ''' Draw 'GAME OVER' and score for game over screen. 
    '''
    gameover_font = pygame.font.Font('freesansbold.ttf', 100)
    textSurfaceObj = gameover_font.render("GAME OVER", True, LIGHTRED, COLOR_BG_OVER)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//3)
    display_surf.blit(textSurfaceObj, textRectObj)
    
    score_font = pygame.font.Font('freesansbold.ttf', 80)
    textSurfaceObj = score_font.render("SCORE: "+str(score), True, LIGHTBLUE, COLOR_BG_OVER)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT*2//3)
    display_surf.blit(textSurfaceObj, textRectObj)

def drawPromptOver():
    ''' Draw button prompt to back to main routine for game over screen. 
    '''
    prompt_font = pygame.font.Font('freesansbold.ttf', 20)
    textSurfaceObj = prompt_font.render("Press space key to continue!", True, WHITE, COLOR_BG_OVER)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT - 40)
    display_surf.blit(textSurfaceObj, textRectObj)
        
if __name__ == '__main__':
    main()