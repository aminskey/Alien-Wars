import pygame

from pygame.locals import *
from random import randint

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

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

class Cloud(pygame.sprite.Sprite):
    def __init__(self, type="cloud-1"):
        super().__init__()
        self.image = pygame.image.load(f"levels/clouds/{type}.png")
        self.rect = self.image.get_rect()

        self.rect.midbottom = (randint(0, screen.get_width()), randint(-screen.get_height(), 0))
    def update(self, speed=2):
        self.rect.y += speed
        if self.rect.midtop[1] > screen.get_height():
            self.rect.y = -self.image.get_height()


class Player(pygame.sprite.Sprite):
    def __init__(self, name="bullseye"):
        super().__init__()
        self.image = pygame.image.load(f"player/{name}.png")
        self.rect = self.image.get_rect()
        self.speed = 5

    def rectifyPos(self):
        if self.rect.midright[0] > screen.get_width() - 10:
            self.rect.x -= self.speed * 2
        if self.rect.midleft[0] < 10:
            self.rect.x += self.speed * 2

        if self.rect.midtop[1] < 0:
            self.rect.y += self.speed * 2
        if self.rect.midbottom[1] > screen.get_height() - 10:
            self.rect.y -= self.speed * 2

    def move(self, key_read, ver_keys=[K_LEFT, K_RIGHT], hor_keys=[K_UP, K_DOWN]):
        if key_read[ver_keys[0]]:
            self.rect.x -= self.speed
        if key_read[ver_keys[1]]:
            self.rect.x += self.speed
        if key_read[hor_keys[0]]:
            self.rect.y -= self.speed
        if key_read[hor_keys[1]]:
            self.rect.y += self.speed
    def update(self):
        keys = pygame.key.get_pressed()
        self.move(keys)
        self.rectifyPos()

class Level():
    def __init__(self, scrollStrip, speed=5):
        bg = pygame.image.load(scrollStrip)
        wh_ratio = bg.get_height() // bg.get_width()

        self.image = pygame.transform.scale(bg, (screen.get_width(), screen.get_height() * wh_ratio))
        self.rect = self.image.get_rect()

        self.rect.midbottom = screen.get_rect().midbottom
        self.speed = speed


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


earth = Level("levels/earth.png", 2)

def isInBounds(x, offset, big, small):
    return ((x + offset) < big) and ((x - offset) > small)
def drawScanlines(thickness, alpha, window):
    for i in range(window.get_height()):
        if i % (thickness * 4) == 0:
            tmp = pygame.Surface((window.get_width(), thickness))
            tmp.fill((0, 0, 0))
            tmp.set_alpha(alpha)

            window.blit(tmp, (0, i))

def startScreen():
    favicon = pygame.image.load("misc/earth-planet.png")
    f_rect = favicon.get_rect()
    f_rect.center = (screen.get_width()//2, screen.get_height() * 2//3)

    titleFont = pygame.font.Font("fonts/planet_joust_ownjx.otf", 75)
    subFont = pygame.font.Font("fonts/ChargeVector.ttf", 50)

    title = Text(gameTitle, titleFont, WHITE, (screen.get_width()//2, screen.get_height()//4))
    textGroup.add(title)

    start = Text("Start", subFont, WHITE)
    menu = Text("Menu", subFont, WHITE)
    quit = Text("Quit", subFont, WHITE)

    cursor = Text(">", subFont, GREEN)
    textGroup.add(cursor)

    shadow = pygame.Surface(screen.get_size())
    shadow.fill(BLACK)
    shadow.set_alpha(150)

    options = [start, menu, quit]
    opIndex = 0
    i = 0
    for option in options:
        option.rect.center = (screen.get_width()//2, screen.get_height()//2 + (option.image.get_height() * i + 5))
        i += 1
        textGroup.add(option)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
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
                    if options[opIndex] == start:
                        main(earth, Player("cobra"))
                        break
                    if options[opIndex] == quit:
                        pygame.quit()
                        exit()

        cursor.rect.midright = options[opIndex].rect.midleft

        screen.fill(BLACK)
        screen.blit(favicon, f_rect)
        screen.blit(shadow, (0, 0))

        textGroup.draw(screen)
        drawScanlines(2, 150, screen)

        pygame.display.update()
        clock.tick(30)

def main(level, player):
    player.rect.center = screen.get_rect().center
    playerGroup.add(player)

    for i in range(10):
        tmp = Cloud()
        if not pygame.sprite.spritecollideany(tmp, allClouds):
            if i % 2 == 0:
                tmp.image.set_alpha(200)
                cloudsGroup2.add(tmp)
            else:
                cloudsGroup1.add(tmp)
            allClouds.add(tmp)

    shade_layer = pygame.Surface(screen.get_size())
    shade_layer.fill((0, 0, 0))

    level.image.set_alpha(150)
    shade_layer.set_alpha(50)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        level.update()
        playerGroup.update()
        allClouds.update(speed=3)

        screen.blit(level.image, level.rect)
        screen.blit(shade_layer, (0, 0))

        cloudsGroup2.draw(screen)
        playerGroup.draw(screen)
        cloudsGroup1.draw(screen)

        drawScanlines(2, 50, screen)

        pygame.display.update()
        clock.tick(FPS)

startScreen()