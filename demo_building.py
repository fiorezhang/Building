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
HOOK_X_L = 280
HOOK_X_R = 520
HOOK_Y = 100
HOOK_SPEED = BASIC_SPEED

FLOOR_WIDTH = 100
FLOOR_HEIGHT = 75
FLOOR_CNT = 4
FLOOR_EDGE_HEIGHT = WINDOW_HEIGHT - FLOOR_HEIGHT*FLOOR_CNT
FLOOR_X = (HOOK_X_L + HOOK_X_R)//2 - (FLOOR_WIDTH-HOOK_WIDTH)//2
FLOOR_Y = WINDOW_HEIGHT-FLOOR_HEIGHT
FLOOR_DROP_SPEED = BASIC_SPEED * 4
FLOOR_ROTATE_MARGIN = 30
FLOOR_ROTATE_MAX = 45
FLOOR_ROTATE_SPEED = 1

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
    "LAND":   2,
    "LVUP":   3,
    "FAIL":   4, 
    "OVER":   5,
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

    showStartScreen()
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
    state = STATE["HANG"]
    
    #本地变量，初始化各个元素
    clouds = initialCloud()
    crane = initialCrane()
    floors = initialFloor()
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
    
    clearKeyEvent()
    
    while state != STATE["OVER"]:
        #检测退出事件
        checkForQuit()

        #TODO
        #状态机，hang检测按键，drop检测纵坐标，land检测刚好对齐，或者摇晃角度，lvup检测纵坐标，fail检测掉落一层或者角度超最大
        if state == STATE["HANG"]:
            if checkForSpaceDown() == True:
                state = STATE["DROP"]
                sound_main_02.play()
        elif state == STATE["DROP"]:
            floor_drop_pos = floors[-1][1]
            floor_edge_pos = floors[-2][1]
            if floor_drop_pos[1] >= FLOOR_EDGE_HEIGHT-FLOOR_HEIGHT: 
                if floor_drop_pos[0] > floor_edge_pos[0]-FLOOR_WIDTH and floor_drop_pos[0] < floor_edge_pos[0]+FLOOR_WIDTH: 
                    floor_drop_pos[1] = FLOOR_EDGE_HEIGHT-FLOOR_HEIGHT
                    floors[-1][1] = floor_drop_pos
                    state = STATE["LAND"]
                else:
                    state = STATE["FAIL"]
        elif state == STATE["LAND"]:
            floor_land_pos = floors[-1][1]
            floor_edge_pos = floors[-2][1]
            if floor_land_pos[0] == floor_edge_pos[0]: #刚好对准！！
                state = STATE["LVUP"]
                sound_main_03.play()
            elif floor_land_pos[4] >= FLOOR_ROTATE_MARGIN or floor_land_pos[4] <= -FLOOR_ROTATE_MARGIN: 
                state = STATE["FAIL"]
            elif floor_land_pos[4] == 0: #下落的floor回正了
                state = STATE["LVUP"]
                sound_main_01.play()
        elif state == STATE["LVUP"]:
            floor_land_pos = floors[-1][1]
            if floor_land_pos[1] >= FLOOR_EDGE_HEIGHT: 
                floor_drop_pos[1] = FLOOR_EDGE_HEIGHT
                floors[-1][1] = floor_drop_pos
                state = STATE["HANG"]
                clearKeyEvent()
        elif state == STATE["FAIL"]:
            floor_land_pos = floors[-1][1]
            if floor_land_pos[1] >= FLOOR_EDGE_HEIGHT: 
                state = STATE["OVER"]
                sound_main_04.play()
            elif floor_land_pos[4] >= FLOOR_ROTATE_MAX or floor_land_pos[4] <= -FLOOR_ROTATE_MAX:
                state = STATE["OVER"]
                sound_main_04.play()

        #更新各个元素
        clouds = updateCloud(clouds, state)
        crane = updateCrane(crane, state)
        floors = updateFloor(floors, crane, state)
        score = updateScore(score, state)
        
        #绘图步骤 --------
        drawBackground()
        drawCloud(clouds)
        drawCrane(crane)
        drawFloor(floors)
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
    
def updateCloud(clouds, state):
    for i, cloud in enumerate(clouds):
        cloud_img, cloud_pos = cloud[0], cloud[1]
        cloud_pos[0] += np.random.randint(CLOUD_SPEED) #随机移动水平速度
        if cloud_pos[0] > WINDOW_WIDTH:
            cloud_img = pygame.image.load("resource/cloud/cloud"+str(np.random.randint(8))+".png")
            cloud_img = pygame.transform.scale(cloud_img, (CLOUD_WIDTH, CLOUD_HEIGHT))
            cloud_pos = [-CLOUD_WIDTH, np.random.randint(0, high=WINDOW_HEIGHT-CLOUD_HEIGHT)]
        if state == STATE["LVUP"]:
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
def updateCrane(crane, state):
    racks, base_y, hook_x = crane[0], crane[1], crane[2]
    #架子
    if racks[0] >= RACK_Y and racks[0] < RACK_Y+BASIC_SPEED: #第一节已经要挪出去了，需要在前面新增加一节
        rack_y_new = RACK_Y - RACK_HEIGHT
        racks.insert(0, rack_y_new)
    if racks[-1] >= WINDOW_HEIGHT:
        racks.pop(-1)
    if state == STATE["LVUP"]:
        for i, rack_y in enumerate(racks):
            rack_y += BASIC_SPEED
            racks[i] = rack_y
    #底座
    if state == STATE["LVUP"]:
        base_y += BASIC_SPEED
    #钩子
    global hook_move_r
    if state != STATE["OVER"]: 
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
    
def initialFloor():
    ''' Initialize list of floors, including the random images and initial position
    position has below information: topleft coordination, hook point coordination, rotate angle, 
    with additional information as width and height, the rect can be fixed
    '''
    floors = []
    for i in range(FLOOR_CNT): 
        floor_img = pygame.image.load("resource/floor/floor"+str(np.random.randint(16))+".png")
        floor_img = pygame.transform.scale(floor_img, (FLOOR_WIDTH, FLOOR_HEIGHT))
        pos_x, pos_y = FLOOR_X, FLOOR_Y-FLOOR_HEIGHT*i
        floor_pos = [pos_x, pos_y, pos_x, pos_y, 0] #[左上横坐标，左上纵坐标，锚点横坐标，锚点纵坐标，逆时针旋转角度
        floor = [floor_img, floor_pos]
        floors.append(floor)
    return floors

def updateFloor(floors, crane, state):
    if state == STATE["HANG"]:
        hook_x = crane[2]
        floor_top_pos = floors[-1][1]
        if floor_top_pos[1] > HOOK_Y+HOOK_HEIGHT: 
            floor_hang_img = pygame.image.load("resource/floor/floor"+str(np.random.randint(16))+".png")
            floor_hang_img = pygame.transform.scale(floor_hang_img, (FLOOR_WIDTH, FLOOR_HEIGHT))
            angle = FLOOR_ROTATE_MARGIN * 2 * (hook_x-(HOOK_X_L+HOOK_X_R)//2) // (HOOK_X_R-HOOK_X_L) #最多旋转+-margin度
            floor_hang_pos = [hook_x-(FLOOR_WIDTH-HOOK_WIDTH)//2, HOOK_Y+HOOK_HEIGHT, hook_x+HOOK_WIDTH//2, HOOK_Y+HOOK_HEIGHT, angle]
            floor_hang = [floor_hang_img, floor_hang_pos]
            floors.append(floor_hang)        
        angle = FLOOR_ROTATE_MARGIN * 2 * (hook_x-(HOOK_X_L+HOOK_X_R)//2) // (HOOK_X_R-HOOK_X_L) #最多旋转+-margin度
        floor_hang_pos = [hook_x-(FLOOR_WIDTH-HOOK_WIDTH)//2, HOOK_Y+HOOK_HEIGHT, hook_x+HOOK_WIDTH//2, HOOK_Y+HOOK_HEIGHT, angle]
        floors[-1][1] = floor_hang_pos
    if state == STATE["DROP"]:
        floor_hang_pos = floors[-1][1]
        floor_hang_pos[1] += FLOOR_DROP_SPEED
        floor_hang_pos[4] = 0
        floors[-1][1] = floor_hang_pos
    if state == STATE["LAND"]:
        floor_land_pos = floors[-1][1]
        floor_edge_pos = floors[-2][1]
        angle_target = FLOOR_ROTATE_MARGIN * (floor_edge_pos[0]-floor_land_pos[0]) // (FLOOR_WIDTH//2)
        angle = floor_land_pos[4]
        if floor_land_pos[0] <= floor_edge_pos[0]:
            hk_x, hk_y = floor_edge_pos[0], floor_edge_pos[1]
            if angle < angle_target:
                angle += FLOOR_ROTATE_SPEED
            else:
                angle = 0
        elif floor_land_pos[0] > floor_edge_pos[0]:
            hk_x, hk_y = floor_edge_pos[0]+FLOOR_WIDTH, floor_edge_pos[1]
            if angle > angle_target:
                angle -= FLOOR_ROTATE_SPEED
            else:
                angle = 0
        floor_land_pos[2], floor_land_pos[3], floor_land_pos[4] = hk_x, hk_y, angle
        floors[-1][1] = floor_land_pos
    if state == STATE["LVUP"]:
        floor_land_pos = floors[-1][1]
        pos_x_delta = 0
        if FLOOR_X != floor_land_pos[0]: #让整个楼水平方向平移，让新的顶楼居中，那么每一帧移动的距离要算出来
            pos_x_delta = (FLOOR_X-floor_land_pos[0]) * BASIC_SPEED // (FLOOR_EDGE_HEIGHT-floor_land_pos[1])
            if FLOOR_EDGE_HEIGHT - floor_land_pos[1] <= BASIC_SPEED:
                pos_x_delta = FLOOR_X-floor_land_pos[0]
        for i, floor in enumerate(floors):
            floor_pos = floor[1]
            floor_pos[0] += pos_x_delta
            floor_pos[1] += BASIC_SPEED
            floor[1] = floor_pos
            floors[i] = floor
        floor_bot_pos = floors[0][1]
        if floor_bot_pos[1] >= WINDOW_HEIGHT: 
            floors.pop(0)
    if state == STATE["FAIL"]:
        floor_drop_pos = floors[-1][1]
        if floor_drop_pos[4] > FLOOR_ROTATE_MARGIN:
            floor_drop_pos[4] += FLOOR_ROTATE_SPEED
            floors[-1][1] = floor_drop_pos
        elif floor_drop_pos[4] < -FLOOR_ROTATE_MARGIN:
            floor_drop_pos[4] -= FLOOR_ROTATE_SPEED
            floors[-1][1] = floor_drop_pos
        elif floor_drop_pos[1] >= FLOOR_EDGE_HEIGHT-FLOOR_HEIGHT: #说明没有碰到最上一层，而是继续往下掉，那么掉一层就报错，在主循环检测
            floor_drop_pos[1] += FLOOR_DROP_SPEED
            floor_drop_pos[4] = 0
            floors[-1][1] = floor_drop_pos
    return floors

def drawFloor(floors):
    for floor in floors:
        floor_img, floor_pos = floor[0], floor[1]
        drawRect(floor_img, FLOOR_WIDTH, FLOOR_HEIGHT, floor_pos[0], floor_pos[1], floor_pos[2], floor_pos[3], floor_pos[4])

def drawRect(img, w, h, org_x, org_y, hk_x, hk_y, a):
    #img = pygame.image.load("resource/floor/floor0.png")
    img = pygame.transform.scale(img, (w, h))
    img = pygame.transform.rotate(img, a)

    img_x = (org_x-hk_x)*math.cos(math.radians(a)) + (org_y-hk_y)*math.sin(math.radians(a)) + hk_x
    img_y = -(org_x-hk_x)*math.sin(math.radians(a)) + (org_y-hk_y)*math.cos(math.radians(a)) + hk_y
    
    if a >= 0:
        pos_x = img_x
        pos_y = img_y-w*math.sin(math.radians(a))
    else:
        pos_x = img_x + h*math.sin(math.radians(a))
        pos_y = img_y
    display_surf.blit(img, (pos_x, pos_y))        

def initialScore():    
    return 0

def updateScore(score, state):
    if state == STATE["LVUP"]:
        score += BASIC_SPEED
    return score
    
def drawScore(score):
    ruler_img = pygame.image.load("resource/ruler/ruler.png")
    ruler_img = pygame.transform.scale(ruler_img, (RULER_WIDTH, RULER_HEIGHT))
    display_surf.blit(ruler_img, (RULER_X, RULER_Y))
    
    score_font = pygame.font.Font('freesansbold.ttf', 20)
    textSurfaceObj = score_font.render(str(score)+" in", True, BLACK, WHITE)
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
