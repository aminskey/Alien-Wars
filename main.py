import pygame, cv2
import numpy as np

from pygame.locals import *
from random import randint, shuffle
from os import listdir
from math import cos, sin, atan, degrees, radians

gameTitle = "Alien Wars"

pygame.init()
screen = pygame.display.set_mode((900, 600), SCALED | FULLSCREEN)
pygame.display.set_caption(gameTitle)

clock = pygame.time.Clock()
FPS = 60

playerGroup = pygame.sprite.Group()
cloudsGroup1 = pygame.sprite.Group()
cloudsGroup2 = pygame.sprite.Group()
allClouds = pygame.sprite.Group()
textGroup = pygame.sprite.Group()
fireGroup = pygame.sprite.Group()
healthBarGroup = pygame.sprite.Group()
sporeGroup = pygame.sprite.Group()


allSprites = pygame.sprite.Group()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

class Cloud(pygame.sprite.Sprite):
    def __init__(self, type="cloud", image=None):
        super().__init__()
        if image != None:
            self.image = pygame.image.load(f"levels/bgObjects/{image}.png")
        else:
            objects = listdir(f"levels/bgObjects/{type}")
            self.image = pygame.image.load(f"levels/bgObjects/{type}/{objects[randint(0, len(objects) - 1)]}")
        self.rect = self.image.get_rect()

        self.rect.midbottom = (randint(0, screen.get_width()), randint(-screen.get_height(), 0))
    def update(self, speed=2):
        self.rect.y += speed
        if self.rect.midtop[1] > screen.get_height():
            self.rect.y = -self.image.get_height()
            self.rect.x = randint(0, screen.get_width())


class Ship(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()
        self.image = pygame.image.load(f"player/{name}.png")
        self.rect = self.image.get_rect()
        self.speed = 5

        self.cooldown = 5
        self.health = 100
        self.lives = 3

    def rectifyPos(self):
        if self.rect.midright[0] > screen.get_width() - 10:
            self.rect.x -= self.speed * 2
        if self.rect.midleft[0] < 10:
            self.rect.x += self.speed * 2

        if self.rect.midtop[1] < 0:
            self.rect.y += self.speed * 2
        if self.rect.midbottom[1] > screen.get_height() - 10:
            self.rect.y -= self.speed * 2
    def fire(self):
        #pygame.mixer.Sound('SFX/Laser.wav').play()
        tmp = Lazer(mount_point=self.rect.midtop, sizeFactor=5, speed=15)
        tmp.sender = self
        tmp.oppGroup = sporeGroup
        fireGroup.add(tmp)
        allSprites.add(tmp)

    def move(self, key_read, ver_keys=[K_LEFT, K_RIGHT], hor_keys=[K_UP, K_DOWN]):
        if key_read[ver_keys[0]]:
            self.rect.x -= self.speed
        if key_read[ver_keys[1]]:
            self.rect.x += self.speed
        if key_read[hor_keys[0]]:
            self.rect.y -= self.speed
        if key_read[hor_keys[1]]:
            self.rect.y += self.speed

    def printLifeCount(self, window=screen):
        im_res = (self.image.get_width() // 1.2, self.image.get_height() // 1.2)
        image = pygame.transform.scale(self.image, im_res)
        for i in range(self.lives):
            window.blit(image,
                        (window.get_width() - (i + 1) * image.get_width(), window.get_height() - image.get_height()))
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[K_SPACE]:
            if self.cooldown <= 0:
                self.fire()
                self.cooldown = 5
        if self.cooldown > 0:
            self.cooldown -= 1

        if pygame.sprite.spritecollideany(self, sporeGroup):
            self.health = 0
            pygame.sprite.spritecollideany(self, sporeGroup).health = 0

        if self.health <= 0:
            tmp = Explosion(explosion, 2, 1, self.rect.center)
            playerGroup.add(tmp)

            self.lives -= 1
            if self.lives > 0:
                self.health = 100
            self.kill()

        self.move(keys)
        self.rectifyPos()

class Level():
    def __init__(self, scrollStrip, speed=5, cloudType="cloud-1", cloudDensity=15):
        bg = pygame.image.load(scrollStrip)
        wh_ratio = bg.get_height() // bg.get_width()

        self.image = pygame.transform.scale(bg, (screen.get_width(), screen.get_height() * wh_ratio))
        self.rect = self.image.get_rect()

        self.rect.midbottom = screen.get_rect().midbottom
        self.speed = speed
        self.cloudDensity = cloudDensity
        self.cloudType = cloudType

    def scroll(self):
        self.rect.y += self.speed
        if self.rect.topleft[1] > -25:
            self.rect.midbottom = screen.get_rect().midbottom

    def update(self):
        self.scroll()

class Text(pygame.sprite.Sprite):
    def __init__(self, msg, script, textColor, pos=(0, 0)):
        super().__init__()
        self.image = script.render(msg, None, textColor)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.alphaValue=255
        self.deltaA=-20
    def blink(self):
        self.alphaValue += self.deltaA
        if not isInBounds(self.alphaValue, 255, 0):
            self.deltaA *= -1
        self.image.set_alpha(self.alphaValue)
class Lazer(pygame.sprite.Sprite):
    def __init__(self, l_type="standard", damage=10, mount_point=(0,0), speed=10, angle=90, sizeFactor=1):
        super().__init__()
        laser = pygame.image.load(f"lazers/{l_type}.png")
        self.copy = pygame.transform.scale(laser, (laser.get_width()//sizeFactor, laser.get_height()//sizeFactor))
        self.image = pygame.transform.rotate(self.copy, angle)

        self.corrVec = pygame.math.Vector2(self.copy.get_width()//2, 0).rotate(angle)

        self.sizeFactor = sizeFactor
        self.rect = self.image.get_rect()
        self.rect.center = mount_point + self.corrVec
        self.speed = speed
        #x_vec = speed * cos(radians(angle))
        #y_vec = -speed * sin(radians(angle))
        self.vel = pygame.math.Vector2(self.speed, 0).rotate(-angle)
        self.sender = None
        self.oppGroup = None
        self.damage = damage

    def update(self):
        self.rect.center += self.vel

        if not isInBounds(self.rect.x, screen.get_width(), 0) or not isInBounds(self.rect.y, screen.get_height(), 0):
            self.kill()

        if pygame.sprite.spritecollideany(self, self.oppGroup):
            sprite = pygame.sprite.spritecollideany(self, self.oppGroup)
            if hasattr(sprite, "health"):
                sprite.health -= self.damage
            exp = Explosion(explosion, 2/(self.sizeFactor), 3, self.rect.center)
            fireGroup.add(exp)
            self.kill()


class dummySprite(pygame.sprite.Sprite):
    def __init__(self, color=GREEN):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.rect = self.image.get_rect()
        self.x_speed = 5
        self.y_speed = 5
        self.image.fill(color)
    def update(self):
        if not isInBounds(self.rect.y, screen.get_height(), 0, self.image.get_height()//2):
            self.y_speed *= -1
        if not isInBounds(self.rect.x, screen.get_width(), 0, self.image.get_width()//2):
            self.x_speed *= -1

        self.rect.x += self.x_speed
        self.rect.y += self.y_speed

class Gun(pygame.sprite.Sprite):
    def __init__(self, target, mountPoint=(0, 0), sizeFactor=1, staticAngle=90):
        super().__init__()
        self.mountpoint = mountPoint
        self.target = target
        self.sizeFactor = sizeFactor
        self.lazType = "standard"

        buffImage = pygame.image.load("turrets/gun.png")
        baseImage = pygame.image.load("turrets/turret_frame.png")

        self.image = resizeImage(buffImage, sizeFactor)
        self.turret_frame = resizeImage(baseImage, sizeFactor)

        self.image_cp = self.image.copy()
        self.rect = self.image.get_rect()
        self.frame_rect = self.turret_frame.get_rect()
        self.frame_rect.center = self.mountpoint

        self.x_dist = 0
        self.y_dist = 0
        self.angle = staticAngle
        self.correctionVector = None
        self.angleCheck = 0

        self.sender = None
        self.oppGroup = None


        self.maxCool = 10
        self.cooldown = self.maxCool
        if self.target is None:
            self.rotate()

    def get_angle(self):
        self.x_dist = self.rect.centerx - self.target.rect.centerx
        self.y_dist = self.rect.centery - self.target.rect.centery

        if self.x_dist > 0:
            self.angleCheck = 180
        else:
            self.angleCheck = 0
        if not isInBounds(self.x_dist, 1, -1) and not isInBounds(self.y_dist, 1, -1):
            self.angle = -degrees(atan(self.y_dist/self.x_dist)) + self.angleCheck

    def fire(self, offset=pygame.math.Vector2(0, 0)):
        tmp = Lazer(self.lazType, 5, speed=10, angle=self.angle, sizeFactor=3)
        tmp.rect.center = self.rect.center + offset
        tmp.sender = self.sender
        tmp.oppGroup = self.oppGroup
        fireGroup.add(tmp)

    def rotate(self):
        self.image = pygame.transform.rotate(self.image_cp, self.angle)
        self.rect = self.image.get_rect()
        self.correctionVector = pygame.math.Vector2(self.image_cp.get_width()//3, 0).rotate(-self.angle)

        self.rect.center = self.mountpoint + self.correctionVector

    def update(self, fireOffset=pygame.math.Vector2(0, 0)):
        if self.target is not None:
            self.get_angle()
            self.rotate()

        if self.cooldown <= 0:
            self.fire(fireOffset)
            self.cooldown = self.maxCool
        else:
            self.cooldown -= 1


class HealthBar(pygame.sprite.Sprite):
    def __init__(self, sprite, stdLength=screen.get_width()//3, window=screen):
        super().__init__()
        self.sprite = sprite

        self.standard_length = stdLength
        self.image = pygame.Surface((self.standard_length, window.get_height()//20))
        self.image.fill(GREEN)

        self.copy = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.bottomleft = window.get_rect().bottomleft

    def update(self):
        if self.sprite.health > 0:
            health_pct = (self.sprite.health/100)
        else:
            health_pct = 0
        self.image = pygame.transform.scale(self.copy, (health_pct * self.standard_length, self.copy.get_height()))
        if isInBounds(self.sprite.health, 100, 65):
            self.image.fill(GREEN)
        elif isInBounds(self.sprite.health, 65, 45):
            self.image.fill(YELLOW)
        elif isInBounds(self.sprite.health, 45, 0):
            self.image.fill(RED)


class Spore_Generic(pygame.sprite.Sprite):
    def __init__(self, target, tagNumber, weaponType, sizeFactor=1):
        super().__init__()
        buffImg = pygame.image.load(f"enemies/Spore-{tagNumber}.png")
        self.image = resizeImage(buffImg, sizeFactor)
        self.rect = self.image.get_rect()
        self.target = target
        self.sizeFactor = sizeFactor

        self.health = 50
        self.weaponType = weaponType
        self.speed = 5
        self.direction = 1
    def update(self):
        if not isInBounds(self.rect.centery, self.image.get_height() + screen.get_height(), -self.image.get_height(), self.image.get_height()//2):
            self.kill()
        if self.health <= 0:
            tmp = Explosion(explosion, 1/self.sizeFactor, pos=self.rect.center)
            sporeGroup.add(tmp)
            self.kill()
class Spore_3(Spore_Generic):
    def __init__(self, target):
        super().__init__(target, 3, "bomb")
        self.x_dist = 0
        self.y_dist = 0
        self.angle = 0
        self.angleCheck = 0
        self.coolDown = 0
        self.maxCool = 100
        self.speed = 1

        self.random_val = (randint(1, 10))/50
    def get_dist(self):
        self.x_dist = self.target.rect.centerx - self.rect.centerx
        self.y_dist = self.target.rect.centery - self.rect.centery
    def get_angle(self):
        if self.x_dist < 0:
            self.angleCheck = 180
        else:
            self.angleCheck = 0

        if not isInBounds(self.x_dist, 1, -1) and not isInBounds(self.y_dist, 1, -1):
            self.angle = -degrees(atan(self.y_dist/self.x_dist)) + self.angleCheck
    def fire(self):
        tmp = Lazer(self.weaponType, 20, self.rect.midbottom, 2, self.angle, 2)
        tmp.sender = self
        tmp.oppGroup = playerGroup

        fireGroup.add(tmp)
        allSprites.add(tmp)
    def update(self):
        self.get_dist()
        self.get_angle()
        if self.coolDown < 0 and self.y_dist > 0:
            self.fire()
            self.coolDown = self.maxCool
        else:
            self.coolDown -= 1
        self.rect.centerx += 5*sin(self.rect.centery * self.random_val)

        self.rect.centery += self.speed*self.direction
        super().update()
class Spore_4(Spore_Generic):
    def __init__(self, direction=1, speed=5, gunAngle=-90):
        super().__init__(None, 4, "standard", 0.5)
        if direction < 0:
            self.image = pygame.transform.rotate(self.image, 180)
        self.direction = direction
        self.gunAngle = gunAngle
        self.speed = speed
        self.turrets = []
        self.generateBarracks()
        self.oppGroup = playerGroup

        for turret in self.turrets:
            turret.oppGroup = self.oppGroup
            turret.sender = self

            turret.maxCool = randint(30, 60)

            self.image.blit(turret.turret_frame, turret.frame_rect)
            self.image.blit(turret.image, turret.rect)
    def fire(self):
        for gun in self.turrets:
            gun.update(fireOffset=pygame.math.Vector2(self.rect.topleft[0], self.rect.topleft[1]))

    def update(self):
        self.fire()
        self.rect.x += self.speed * self.direction
        super().update()

    def generateBarracks(self, num=10):
        bigBound = num-1 if self.direction > 0 else num
        smallBound = 0 if self.direction > 0 else 1
        for i in range(num):
            if isInBounds(i, bigBound, smallBound):
                tmp = Gun(None, ((i * self.image.get_width()/(num)), self.rect.centery), 0.75, staticAngle=self.gunAngle)
                self.turrets.append(tmp)

class Explosion(pygame.sprite.Sprite):
    def __init__(self, seq, size=1, speed=1, pos=(0, 0), loop=False):
        super().__init__()
        self.seq = []
        for img in seq:
            w, h = img.get_size()
            tmp = pygame.transform.scale(img, (w*size, h*size)).convert_alpha()
            tmp.set_colorkey(WHITE)
            self.seq.append(tmp)

        self.image = self.seq[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.anim_index = 0
        self.speed = speed
        self.loop = loop
    def update(self):
        self.anim_index += self.speed
        if self.anim_index >= len(self.seq) - 1:
            if self.loop:
                self.anim_index = 0
            else:
                self.kill()
        else:
            self.image = self.seq[int(self.anim_index)]
def resizeImage(img, sizeFactor=2):
    return pygame.transform.scale(img, (img.get_width()//sizeFactor, img.get_height()//sizeFactor))

def isInBounds(x, big, small, offset=0):
    return ((x + offset) < big) and ((x - offset) > small)
def drawScanlines(thickness, alpha, window):
    for i in range(window.get_height()):
        if i % (thickness * 4) == 0:
            tmp = pygame.Surface((window.get_width(), thickness))
            tmp.fill((0, 0, 0))
            tmp.set_alpha(alpha)

            window.blit(tmp, (0, i))

def meanValue(list):
    return sum(list)/len(list)

def readVideo(file, window=0, resizeFactor=1, threshold=-1, colorKey=WHITE, MaxFrames=-1):
    video = cv2.VideoCapture(file)
    w, h = video.read()[1].shape[1::-1]
    resize =  window.get_size() if type(window) == "pygame.surface.Surface" else (w//resizeFactor, h//resizeFactor)
    seq = []

    frameCount = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break

        if threshold > 0:

            '''
            for i in range(frame.shape[0]):
                for j in range(frame.shape[1]):
                    frame[i, j] = [meanValue(frame[0, i, j]), meanValue(frame[0, i, j]), meanValue(frame[0, i, j])]
            '''
            copy = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            newImg = np.zeros_like(copy)
            newImg[copy > threshold] = copy[copy > threshold]
            frame = cv2.cvtColor(newImg, cv2.COLOR_GRAY2BGR)


        tmp = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR").convert_alpha()
        tmp = pygame.transform.scale(tmp, resize)
        tmp.set_colorkey(colorKey)
        seq.append(tmp)
        frameCount += 1

        if MaxFrames > 0:
            if frameCount > MaxFrames:
                break

    return seq

lev = Level("levels/debri-field.png", 2, "meteor", 6)
earth = Level("levels/earth.png", 2, "cloud", 12)
explosion = readVideo("misc/explosion.gif")
vhs_filter = readVideo("misc/VHS-Layer.gif")
menu_vid = readVideo("video/earth.mp4", screen, MaxFrames=630)


def healthTest(num, max=3):
    if num > 0:
        num -= 1
    else:
        num = max
    return num


def sporeTest():
    spore = Spore_4()
    spore.rect.center = screen.get_rect().center

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                for sprite in fireGroup:
                    sprite.kill()
                startScreen()
                exit()

        spore.update()
        fireGroup.update()

        screen.fill(BLACK)
        fireGroup.draw(screen)
        screen.blit(spore.image, spore.rect)

        pygame.display.update()
        clock.tick(30)



def turretTest():
    dummy = dummySprite()
    allSprites.add(dummy)
    #spore = Spore_3(dummy)
    #spore.rect.center = screen.get_rect().center
    gun = Gun(dummy, screen.get_rect().center, 0.15, staticAngle=-90)
    gun.oppGroup = allSprites

    dummy.rect.topleft = (screen.get_width() - 30, 30)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                for sprite in fireGroup:
                    sprite.kill()
                startScreen()
                exit()

        dummy.update()
        #spore.update()
        gun.update()
        fireGroup.update()

        screen.fill(BLACK)
        fireGroup.draw(screen)
        screen.blit(gun.turret_frame, gun.frame_rect)
        screen.blit(gun.image, gun.rect)
        #screen.blit(spore.image, spore.rect)
        screen.blit(dummy.image, dummy.rect)

        pygame.display.update()
        clock.tick(30)

def fireTest():
    angle = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    tmp = Lazer(mount_point=screen.get_rect().center, speed=20, angle=angle)
                    fireGroup.add(tmp)
                    break
                if event.key == pygame.K_LEFT:
                    angle += 10
                    break
                if event.key == pygame.K_RIGHT:
                    angle -= 10
                    break


        fireGroup.update()

        screen.fill((0, 0, 0))
        fireGroup.draw(screen)

        pygame.display.update()
        clock.tick(30)



def startScreen():
    favicon = pygame.image.load("misc/earth-planet.png")
    favicon = pygame.transform.scale_by(favicon, screen.get_width()/favicon.get_width())
    f_rect = favicon.get_rect()
    f_rect.center = screen.get_rect().midright

    titleFont = pygame.font.Font("fonts/planet_joust_ownjx.otf", 75)
    subFont = pygame.font.Font("fonts/windows_command_prompt.ttf", 50)

    words = gameTitle.split(" ")
    for i in range(len(words)):
        title = Text(words[i], titleFont, WHITE)
        if i == 0:
            title.rect.topleft = (50, 50)
        else:
            title.rect.topleft = textGroup.sprites()[-1].rect.bottomleft
        textGroup.add(title)


    start = Text("Start", subFont, GREEN)
    menu = Text("Menu", subFont, GREEN)
    indev = Text("Indev", subFont, GREEN)
    quit = Text("Quit", subFont, GREEN)

    cursor = Text("#", subFont, GREEN)
    cursor.image.fill(GREEN)
    cursor.image = pygame.transform.scale_by(cursor.image, 0.85)
    textGroup.add(cursor)

    moveEffect = pygame.mixer.Sound("SFX/cursor.wav")

    alphaVal = 50

    shadow = pygame.Surface(screen.get_size())
    shadow.fill(BLACK)
    shadow.set_alpha(alphaVal)

    frameIndex = 0

    options = [start, menu, indev, quit]
    opIndex = 0
    i = 0
    selectMode = False
    acc = 4
    speed = 0

    for option in options:
        option.rect.midleft = (50, screen.get_height()//2 + (option.image.get_height() * i + 5))
        i += 1
        textGroup.add(option)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYUP:
                moveEffect.stop()
            if event.type == pygame.KEYDOWN:
                moveEffect.play()
                if event.key == pygame.K_DOWN:
                    if opIndex < len(options) - 1:
                        opIndex += 1
                    else:
                        opIndex = 0
                    break
                if event.key == pygame.K_UP:
                    if opIndex > 0:
                        opIndex -= 1
                    else:
                        opIndex = len(options) - 1
                    break
                if event.key == pygame.K_RETURN:
                    if not selectMode:
                        selectMode = True
                    break

        if frameIndex >= len(menu_vid) - 1:
            frameIndex = 0
        frameIndex += 1

        if selectMode:
            i=len(textGroup.sprites())
            for sprite in textGroup.sprites():
                if sprite.rect.midright[0] > -20:
                    sprite.rect.x -= speed * (i+1)
                else:
                    sprite.kill()
                i -= 1
            if speed < 20:
                speed += acc
            alphaVal += speed
            shadow.set_alpha(alphaVal)

            if (len(textGroup.sprites())) <= 0:
                if options[opIndex] == start:
                    main(earth, Ship("cobra"))
                    startScreen()
                    exit()
                elif options[opIndex] == quit:
                    pygame.quit()
                    exit()
                elif options[opIndex] == indev:
                    turretTest()
                    startScreen()
                    exit()
                else:
                    startScreen()
                    exit()


        cursor.rect.midright = options[opIndex].rect.midleft
        cursor.blink()

        #screen.blit(favicon, f_rect)
        screen.blit(menu_vid[int(frameIndex)], (0, 0))
        screen.blit(shadow, (0, 0))

        textGroup.draw(screen)
        drawScanlines(2, 150, screen)

        pygame.display.update()
        clock.tick(30)

def calc_Accel(start_point, end_point, start_speed, end_speed):
    return (end_speed**2 - start_speed**2)/(2*(end_point - start_point))


def main(level, ship):
    ship.rect.center = screen.get_rect().center
    playerGroup.add(ship)
    allSprites.add(ship)

    healthBar = HealthBar(ship)
    healthBarGroup.add(healthBar)

    font = pygame.font.Font("fonts/planet_joust_ownjx.otf", 50)
    subtitle = pygame.font.Font("fonts/ChargeVector.ttf", 20)
    subtitle.set_italic(True)

    g_over = Text("Game Over", font, WHITE)
    g_over.rect.midleft = screen.get_rect().midright
    sideMsg = Text("Press any key to Continue", subtitle, WHITE)
    sideMsg.rect.midtop = screen.get_rect().midbottom

    gameOver = False
    titleSpeed = 10
    subSpeed = 5

    titleAcc = calc_Accel(screen.get_width(), (screen.get_width() - g_over.image.get_width())//2, titleSpeed, 0)
    subAcc = calc_Accel(sideMsg.rect.midtop[1], g_over.rect.midbottom[1], subSpeed, 0)
    alphaVal = 0

    for i in range(level.cloudDensity):
        tmp = Cloud(level.cloudType)
        if not pygame.sprite.spritecollideany(tmp, allClouds):
            if i % 2 == 0:
                tmp.image.set_alpha(200)
                cloudsGroup2.add(tmp)
            else:
                cloudsGroup1.add(tmp)
            allClouds.add(tmp)

    shade_layer = pygame.Surface(screen.get_size())
    shade_layer.fill(BLACK)
    shade_layer.set_alpha(50)

    level.image.set_alpha(150)

    count = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if gameOver:
                    for sprite in allSprites.sprites():
                        sprite.kill()
                    for sprite in allClouds.sprites():
                        sprite.kill()
                    level.rect.midbottom = screen.get_rect().midbottom
                    startScreen()
                    exit()

        if count % (FPS * 5) == 0:
            y = randint(0, screen.get_height() * 5 // 6)
            list = [1, -1]
            direction = list[randint(0, 1)]
            angle = 90 if y > ship.rect.y else -90
            spore = Spore_4(direction, 2, angle)
            if direction > 0:
                spore.rect.topright = (screen.get_rect().midleft[0], y)
            else:
                spore.rect.topleft = (screen.get_rect().midright[0], y)

            sporeGroup.add(spore)
            allSprites.add(spore)

        if count % (FPS * 15) == 0:
            spore = Spore_3(ship)
            spore.rect.midtop = screen.get_rect().midbottom
            spore.direction = -1

            sporeGroup.add(spore)
            allSprites.add(spore)

        if len(playerGroup.sprites()) <= 0:
            if ship.lives > 0:
                ship.rect.midbottom = screen.get_rect().midbottom
                playerGroup.add(ship)
                allSprites.add(ship)
            else:
                gameOver = True

        level.update()
        playerGroup.update()
        sporeGroup.update()
        fireGroup.update()
        allClouds.update(speed=3)
        healthBarGroup.update()

        screen.fill(BLACK)
        screen.blit(level.image, level.rect)

        cloudsGroup2.draw(screen)
        fireGroup.draw(screen)
        playerGroup.draw(screen)
        sporeGroup.draw(screen)
        cloudsGroup1.draw(screen)
        healthBarGroup.draw(screen)
        ship.printLifeCount()

        if gameOver:
            if subSpeed > 0:
                sideMsg.rect.centery -= subSpeed
                subSpeed -= subAcc
            if titleSpeed > 0:
                g_over.rect.centerx -= titleSpeed
                titleSpeed -= titleAcc
            if alphaVal < 255:
                alphaVal += (titleAcc/titleSpeed) * 255

            shade_layer.set_alpha(alphaVal)

            screen.blit(shade_layer, (0, 0))
            screen.blit(g_over.image, g_over.rect)
            screen.blit(sideMsg.image, sideMsg.rect)

        drawScanlines(2, 50, screen)

        pygame.display.update()
        clock.tick(FPS)
        count += 1

startScreen()