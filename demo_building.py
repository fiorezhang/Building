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
CLOUD_SPEED = BASIC_SPEED * 2
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
FLOOR_DROP_SPEED = BASIC_SPEED * 5
FLOOR_ROTATE_MARGIN = 30
FLOOR_ROTATE_MAX = 45
FLOOR_ROTATE_SPEED = 1

BOOM_WIDTH = 300
BOOM_HEIGHT = 300
BOOM_X = 200
BOOM_Y = 300
BOOM_CIRCLE = FPS

SCORE_HEIGHT_BASE = 0
SCORE_BIAS_BASE = 100

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
COLOR_BG        = (200, 255, 255)

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
    pygame.display.set_caption('Building for Lucas')

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
    ''' Main routine
    Initialization. State machine. Update. Drawing. 
    '''
    #本地变量，各种标记，缓存
    state = STATE["HANG"]
    over_cnt = 0
    
    #本地变量，初始化各个元素
    clouds = initialCloud()
    crane = initialCrane()
    floors = initialFloor()
    score = initialScore()    
    boom = initialBoom()
    
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
    
    while True:
        #检测退出事件
        checkForQuit()

        #TODO
        #状态机，hang检测按键，drop检测纵坐标，land检测刚好对齐，或者摇晃角度，lvup检测纵坐标，fail检测掉落一层或者角度超最大
        if state == STATE["HANG"]: #检测按键
            if checkForSpaceDown() == True:
                state = STATE["DROP"]
                sound_main_02.play()
        elif state == STATE["DROP"]: #检测掉落快的纵坐标，如果落在最上面一块范围内，进入land状态，否则标记fail
            floor_drop_pos = floors[-1][1]
            floor_edge_pos = floors[-2][1]
            if floor_drop_pos[1] >= FLOOR_EDGE_HEIGHT-FLOOR_HEIGHT: 
                if floor_drop_pos[0] > floor_edge_pos[0]-FLOOR_WIDTH and floor_drop_pos[0] < floor_edge_pos[0]+FLOOR_WIDTH: 
                    floor_drop_pos[1] = FLOOR_EDGE_HEIGHT-FLOOR_HEIGHT
                    floors[-1][1] = floor_drop_pos
                    state = STATE["LAND"]
                else:
                    state = STATE["FAIL"]
        elif state == STATE["LAND"]: #正好对齐时提示，扣分超过预设值，结束；下落块的旋转角度超过上限，标记结束；其它情况认为正常，回正后进入lvup状态
            floor_land_pos = floors[-1][1]
            floor_edge_pos = floors[-2][1]
            if floor_land_pos[0] == floor_edge_pos[0]: #刚好对准！！
                #state = STATE["LVUP"]
                sound_main_03.play()
            if score[1] <= 0:
                state = STATE["OVER"]
                sound_main_04.play()
            elif floor_land_pos[4] >= FLOOR_ROTATE_MARGIN or floor_land_pos[4] <= -FLOOR_ROTATE_MARGIN: 
                state = STATE["FAIL"]
            elif floor_land_pos[4] == 0: #下落的floor回正了
                state = STATE["LVUP"]
                sound_main_01.play()
        elif state == STATE["LVUP"]: #检测最上层的纵坐标，到达指定位置时，回到hang状态
            floor_land_pos = floors[-1][1]
            if floor_land_pos[1] >= FLOOR_EDGE_HEIGHT: 
                floor_drop_pos[1] = FLOOR_EDGE_HEIGHT
                floors[-1][1] = floor_drop_pos
                state = STATE["HANG"]
                clearKeyEvent()
        elif state == STATE["FAIL"]: #当已经旋转超出上限的块继续旋转超过最大值，或者掉落的块掉了超过一层，标记结束
            floor_land_pos = floors[-1][1]
            if floor_land_pos[4] >= FLOOR_ROTATE_MAX or floor_land_pos[4] <= -FLOOR_ROTATE_MAX:
                state = STATE["OVER"]
                sound_main_04.play()
            elif floor_land_pos[1] >= FLOOR_EDGE_HEIGHT: 
                state = STATE["OVER"]
                sound_main_04.play()
        elif state == STATE["OVER"]: #结束状态维持一小段时间，用来画boom贴图
            over_cnt += 1
            if over_cnt >= BOOM_CIRCLE:
                break
            

        #更新各个元素
        clouds = updateCloud(clouds, state)
        crane = updateCrane(crane, state)
        floors = updateFloor(floors, crane, state)
        boom = updateBoom(boom, floors, state)
        score = updateScore(score, state)
        
        #绘图步骤 --------
        drawBackground()
        drawCloud(clouds)
        drawCrane(crane)
        drawFloor(floors)
        drawBoom(boom)
        drawScore(score)

        pygame.display.update()
        fps_lock.tick(FPS)
    print("return: %d" % score[0])
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
    ''' Initialize clouds, choose texture randomly
    '''
    clouds = []
    for i in range(CLOUD_CNT):
        cloud_img = pygame.image.load("resource/cloud/cloud"+str(np.random.randint(8))+".png")
        cloud_img = pygame.transform.scale(cloud_img, (CLOUD_WIDTH, CLOUD_HEIGHT))
        cloud_pos = [np.random.randint(0, high=WINDOW_WIDTH-CLOUD_WIDTH), np.random.randint(0, high=WINDOW_HEIGHT-CLOUD_HEIGHT)]
        cloud = [cloud_img, cloud_pos]
        clouds.append(cloud) 
    return clouds
    
def updateCloud(clouds, state):
    ''' Update clouds. choose different place when move out of screen. 
    '''
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
    ''' Initialize parts for crane
    '''
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
    ''' Update parts for crane. 
    Add racks from the top, and remove from the bottom
    Move base out of screen ater start several floors
    Move hooks left and right. The coordination will pass to the hanging floor
    '''
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
    ''' Draw parts of crane
    '''
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
        floor_img = pygame.image.load("resource/floor/floor"+str(np.random.randint(8))+".png")
        floor_img = pygame.transform.scale(floor_img, (FLOOR_WIDTH, FLOOR_HEIGHT))
        pos_x, pos_y = FLOOR_X, FLOOR_Y-FLOOR_HEIGHT*i
        floor_pos = [pos_x, pos_y, pos_x, pos_y, 0] #[左上横坐标，左上纵坐标，锚点横坐标，锚点纵坐标，逆时针旋转角度
        floor = [floor_img, floor_pos]
        floors.append(floor)
    return floors

def updateFloor(floors, crane, state):
    ''' Update floors, especially the top one
    if state is HANG:
        hanging floor follow the hook, and rotate a proper angle for fun
    if state is DROP:
        droping floor drop in DROP_SPEED
    if state is LAND:
        find biggest bias in each floor, and make sure the gravity center of floors above is in the same direction, then all the floors above should rotate around current floor corner
        rotate the floors, to desired angle - bigger when the average gravity center bias bigger
    if state is LVUP:
        move all floors down, remove the bottom one when out of screen. 
        move properly the floors horizontally, to align the bottom floor to the center
    if state is FAIL:
        continue rotate the top floor if angle already over the margin
        continue drop the top floor if out of the next floor
    '''
    if state == STATE["HANG"]:
        hook_x = crane[2]
        floor_top_pos = floors[-1][1]
        if floor_top_pos[1] > HOOK_Y+HOOK_HEIGHT: 
            floor_hang_img = pygame.image.load("resource/floor/floor"+str(np.random.randint(8))+".png")
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
        if True: #看所有画出来的层的重心，代码不好理解就去看else部分，只判断最上面一层
            floor_delta_num = 0 #这一段是找出和上一层偏移最大且上面所有层的重心在同侧的那一层
            floor_delta_found = False
            floor_deltas = []
            for i, floor in enumerate(floors[:-1]):
                floor_deltas.append(abs(floors[i][1][0] - floors[i+1][1][0]))
            floor_deltas = sorted(floor_deltas, reverse=True)
            floor_bias = 0
            for floor_delta in floor_deltas:
                if floor_delta_found == True:
                    break
                for i, _ in enumerate(floors[:-1]):
                    if floor_delta_found == True:
                        break
                    if abs(floors[i][1][0] - floors[i+1][1][0]) == floor_delta:
                        floor_bias_all = 0
                        floor_bias_cnt = 0
                        for j, _ in enumerate(floors[i+1:]):
                            floor_bias_all += floors[i][1][0] - floors[i+1+j][1][0]
                            floor_bias_cnt += 1
                        if (floors[i][1][0]-floors[i+1][1][0]) * floor_bias_all > 0: #正数说明偏移和重心同侧
                            floor_delta_found = True
                            floor_delta_num = i
                            floor_bias = floor_bias_all // floor_bias_cnt
                            break
            if floor_delta_found == True:
                angle_target = FLOOR_ROTATE_MARGIN * floor_bias // (FLOOR_WIDTH//2)
                angle = floors[-1][1][4]
                if floors[floor_delta_num][1][0] >= floors[floor_delta_num+1][1][0]:
                    hk_x, hk_y = floors[floor_delta_num][1][0], floors[floor_delta_num][1][1]
                    if angle < angle_target:
                        angle += FLOOR_ROTATE_SPEED
                    else:
                        print("Bias: %d" % floor_bias)
                        angle = 0
                elif floors[floor_delta_num][1][0] < floors[floor_delta_num+1][1][0]:
                    hk_x, hk_y = floors[floor_delta_num][1][0]+FLOOR_WIDTH, floors[floor_delta_num][1][1]
                    if angle > angle_target:
                        angle -= FLOOR_ROTATE_SPEED
                    else:
                        print("Bias: %d" % floor_bias)
                        angle = 0      
                for i, _ in enumerate(floors[floor_delta_num+1:]):
                    floors[floor_delta_num+1+i][1][2], floors[floor_delta_num+1+i][1][3], floors[floor_delta_num+1+i][1][4] = hk_x, hk_y, angle
        else:
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
        if True:
            floor_bot_pos = floors[-FLOOR_CNT][1]
            floor_land_pos = floors[-1][1]
            pos_x_delta = 0
            if FLOOR_X != floor_bot_pos[0]: #让整个楼水平方向平移，让新的底楼居中，那么每一帧移动的距离要算出来
                pos_x_delta = (FLOOR_X-floor_bot_pos[0]) * BASIC_SPEED // (FLOOR_EDGE_HEIGHT-floor_land_pos[1])
                if pos_x_delta < 0:
                    pos_x_delta += 1
                if FLOOR_EDGE_HEIGHT - floor_land_pos[1] <= BASIC_SPEED:
                    pos_x_delta = FLOOR_X-floor_bot_pos[0]            
        else:
            floor_land_pos = floors[-1][1]
            pos_x_delta = 0
            if FLOOR_X != floor_land_pos[0]: #让整个楼水平方向平移，让新的顶楼居中，那么每一帧移动的距离要算出来
                pos_x_delta = (FLOOR_X-floor_land_pos[0]) * BASIC_SPEED // (FLOOR_EDGE_HEIGHT-floor_land_pos[1])
                if pos_x_delta < 0:
                    pos_x_delta += 1
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
        if floor_drop_pos[4] >= FLOOR_ROTATE_MARGIN:
            floor_drop_pos[4] += FLOOR_ROTATE_SPEED
            floors[-1][1] = floor_drop_pos
        elif floor_drop_pos[4] <= -FLOOR_ROTATE_MARGIN:
            floor_drop_pos[4] -= FLOOR_ROTATE_SPEED
            floors[-1][1] = floor_drop_pos
        elif floor_drop_pos[1] >= FLOOR_EDGE_HEIGHT-FLOOR_HEIGHT: #说明没有碰到最上一层，而是继续往下掉，那么掉一层就报错，在主循环检测
            floor_drop_pos[1] += FLOOR_DROP_SPEED
            floor_drop_pos[4] = 0
            floors[-1][1] = floor_drop_pos
    if state == STATE["OVER"]:
        pass
    return floors

def drawFloor(floors):
    ''' Draw floors
    '''
    for floor in floors:
        floor_img, floor_pos = floor[0], floor[1]
        drawRect(floor_img, FLOOR_WIDTH, FLOOR_HEIGHT, floor_pos[0], floor_pos[1], floor_pos[2], floor_pos[3], floor_pos[4])

def drawRect(img, w, h, org_x, org_y, hk_x, hk_y, a):
    ''' Draw cell which rotate around a dedicated hook point
    '''
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

def initialBoom():
    ''' Initialize boom. Nothing to do as it's only show when game over
    '''
    return None
    
def updateBoom(boom, floors, state):
    ''' Return a coordination when game over, following the last position of the dropping/landing floor
    '''
    if state == STATE["OVER"]:
        boom = [floors[-1][1][0], floors[-1][1][1]]
        boom[0] -= (BOOM_WIDTH-FLOOR_WIDTH)//2
        boom[1] -= (BOOM_HEIGHT-FLOOR_HEIGHT)//2
        return boom
    else:
        return None

def drawBoom(boom):
    ''' Draw boom
    '''
    if boom != None:
        boom_img = pygame.image.load("resource/boom/boom.png")
        boom_img = pygame.transform.scale(boom_img, (BOOM_WIDTH, BOOM_HEIGHT))
        display_surf.blit(boom_img, (boom[0], boom[1]))

def initialScore():    
    ''' Initialize score
    First score is the height. Second is the existing score. 
    '''
    return [SCORE_HEIGHT_BASE, SCORE_BIAS_BASE]

def updateScore(score, state):
    ''' Update score
    When LVUP, the height increase. When LAND - actually floor rotating, longer when bias bigger - the score decrease. 
    So to get a better height, need reduce the bias each time
    '''
    if state == STATE["LVUP"]:
        score[0] += BASIC_SPEED
    if state == STATE["LAND"]:
        score[1] -= 1 
    return score
    
def drawScore(score):
    ''' Draw score - [0] height [1] bias score
    '''
    ruler_img = pygame.image.load("resource/ruler/ruler.png")
    ruler_img = pygame.transform.scale(ruler_img, (RULER_WIDTH, RULER_HEIGHT))
    display_surf.blit(ruler_img, (RULER_X, RULER_Y))
    
    score_font = pygame.font.Font('freesansbold.ttf', 20)
    textSurfaceObj = score_font.render(str(score[0])+" in", True, BLACK, WHITE)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.topleft = (RULER_X, RULER_Y+10)
    display_surf.blit(textSurfaceObj, textRectObj)

    score_font = pygame.font.Font('freesansbold.ttf', 20)
    textSurfaceObj = score_font.render(str(score[1])+" pt", True, BLACK, WHITE)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.topleft = (RULER_X, RULER_Y+30)
    display_surf.blit(textSurfaceObj, textRectObj)
    
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
    textSurfaceObj = score_font.render("SCORE: "+str(score[0]), True, LIGHTBLUE, COLOR_BG_OVER)
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
        
#入口
if __name__ == '__main__':
    main()
